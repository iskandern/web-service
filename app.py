from flask import Flask, render_template, request
from catboost import CatBoostClassifier
import shap
import metar
import requests
import re
import datetime
import os.path
import pandas as pd

url = 'https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=%ICAO%' \
      '&data=metar&year1=%year1%&month1=%month1%&day1=%day1%&year2=%year2%&month2=%month2%&day2=%day2%&' \
      'tz=Etc%2FUTC&format=onlycomma&latlon=no&missing=M&trace=T&direct=no&report_type=2'
main_metar_features_list = ['ltg', 'vv', 'CB_amount', 'cloud', 'intens', 'BR', 'SH', 'SN', 'RA', \
                            'FZ', 'FG', 'BL', 'TS', 'DZ', 'HZ', 'PL', 'UP', 'SQ', 'FU', 'GS', 'BC', \
                            'MI', 'VA', 'wnd_spd', 'gust', 'vis', 'temp']

url_dict = {}
FILES_PATH = 'C:\\Users\\isk\\Documents\\cache\\'

def replacement(match):
    try:
        return url_dict[match.group(1)]
    except KeyError:
        return match.group(0)


pattern = re.compile(r'\%(\w+)\%')

app = Flask(__name__)


def downloadFile(ICAO, date):
    flight_date = datetime.datetime.strptime(date, '%Y-%m-%d')
    one_day = datetime.timedelta(days=1)
    start = flight_date - one_day
    end = flight_date + one_day

    url_dict['ICAO'] = ICAO
    url_dict['year1'] = str(start.year)
    url_dict['year2'] = str(end.year)
    url_dict['month1'] = str(start.month)
    url_dict['month2'] = str(end.month)
    url_dict['day1'] = str(start.day)
    url_dict['day2'] = str(end.day)

    file_name = FILES_PATH + url_dict['year1'] + '_' + url_dict['month1'] + '_' + url_dict[
        'day1'] + \
                '_' + url_dict['ICAO'] + '.csv'

    if os.path.isfile(file_name):
        return file_name

    query_url = pattern.sub(replacement, url)
    # print(query_url)

    try:
        page = requests.get(query_url)
    except:
        print('error')
        return 0

    f = open(file_name, 'w', encoding='utf-8')
    f.write(page.text)
    f.close()
    return file_name


def getFeatures(file_names_list, datetime_list, ICAO, airline):
    dep = pd.read_csv(file_names_list[0])
    arr = pd.read_csv(file_names_list[1])

    # print(dep.head())
    # print(arr.head())

    max_atmap = 0
    airport = ''
    airport_datetime = ''
    metar_feat_dict = {}
    features_dict = {}
    for airport_type in ['dep', 'arr']:
        if airport_type == 'dep':
            airport = dep
            airport_datetime = datetime_list[0]
        if airport_type == 'arr':
            airport = arr
            airport_datetime = datetime_list[1]

        time_dif_min = datetime.timedelta(days=1)
        metar_index = -1
        for i in range(len(airport)):
            date_time = airport['valid'][i]
            item_datetime = datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M')
            time_diff = abs(item_datetime - airport_datetime)
            if time_dif_min > time_diff:
                time_dif_min = time_diff
                metar_index = i

        if metar_index == -1:
            print('incorrect datetime input')
            break

        metar_string = 'METAR ' + airport['metar'][metar_index] + '='
        # print(metar)
        metar_feat_dict = metar.getFeaturesFromMETAR(metar_string)
        if metar_feat_dict in range(0, 14):
            print('incorrect metar data')
            break

        max_atmap = max(max_atmap, sum(metar.getATMAPScore(metar_feat_dict)))
        for item in main_metar_features_list:
            features_dict[airport_type + '_' + item] = metar_feat_dict[item]

    origin_datetime = datetime_list[0]
    features_dict['atmap'] = max_atmap
    features_dict['day'] = (origin_datetime - datetime.datetime(year=origin_datetime.year, month=1, day=1)).days
    features_dict['airline'] = airline
    features_dict['dep_airport'] = ICAO[0]
    features_dict['arr_airport'] = ICAO[1]
    features_dict['result_type'] = ''
    features_dict['weather_delay'] = ''
    if origin_datetime.month in [1, 2, 12]:
        features_dict['season'] = 0
    if origin_datetime.month in [3, 4, 5]:
        features_dict['season'] = 1
    if origin_datetime.month in [6, 7, 8]:
        features_dict['season'] = 2
    if origin_datetime.month in [9, 10, 11]:
        features_dict['season'] = 3
    return features_dict


@app.route('/')
def main():
    return render_template('mainPage.html')


@app.route('/form', methods=["GET"])
def form():
    dep_icao = request.args.get('dep_icao_name')
    dep_date = request.args.get('dep_date_name')
    dep_time = request.args.get('dep_time_name')
    arr_icao = request.args.get('arr_icao_name')
    arr_date = request.args.get('arr_date_name')
    arr_time = request.args.get('arr_time_name')
    airline = request.args.get('airline_name')

    ICAO = [dep_icao, arr_icao]
    date = [dep_date, arr_date]
    time = [dep_time, arr_time]
    file_names_list = ['', '']
    for i in [0, 1]:
        file_names_list[i] = downloadFile(ICAO[i], date[i])
        if file_names_list[i] == 0:
            print('download error')
            return 0

    datetime_list = ['', '']
    datetime_list[0] = datetime.datetime.strptime(dep_date + ' ' + dep_time, '%Y-%m-%d %H:%M')
    datetime_list[1] = datetime.datetime.strptime(arr_date + ' ' + arr_time, '%Y-%m-%d %H:%M')
    features_dict = getFeatures(file_names_list, datetime_list, ICAO, airline)

    all_observation = pd.DataFrame(features_dict, index=[0])
    observation = all_observation.drop(['day', 'result_type', 'weather_delay', 'atmap'], axis=1)
    observation = observation.reindex(columns=metar.columns_order)

    model = CatBoostClassifier()
    model.load_model(FILES_PATH + 'model')
    prediction = model.predict(observation)[0, 0]
    prediction_prob = model.predict_proba(observation)[0]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values([observation.iloc[0]])
    list2, list1 = zip(*sorted(zip(shap_values[prediction][0, :], metar.columns_order), reverse=True))

    first_n_items = 5
    count = 0
    contents_prefix = '<dt class="name">'
    contents_postfix = '</dt>'
    data_description_prefix = '<dd class="description">'
    data_description_postfix = '</dd>'
    data_prefix = '<p>'
    data_postfix = '</p>'

    result_string = contents_prefix
    if prediction == 0:
        result_string += 'Not expected cancellation or delay'
    if prediction == 1:
        result_string += 'Expected cancellation'
    if prediction == 2:
        result_string += 'Expected delay'
    result_string += contents_postfix

    result_string += contents_prefix
    result_string += 'Prediction probability: ' + str(prediction_prob[prediction])
    result_string += contents_postfix

    result_string += contents_prefix
    result_string += 'ATMAP score: ' + str(all_observation['atmap'][0])
    result_string += contents_postfix

    result_string += contents_prefix
    result_string += 'Weather features importance:'
    result_string += contents_postfix

    result_string += data_description_prefix
    for i in range(len(list1)):
        str_to_print = metar.getStrToPrint(list1[i], list2[i])
        if not str_to_print == '':
            count += 1
            result_string += data_prefix
            result_string += str_to_print
            result_string += data_postfix
        if count == first_n_items:
            break
    result_string += data_description_postfix

    return render_template('form.html', output=result_string)


if __name__ == '__main__':
    app.run()
