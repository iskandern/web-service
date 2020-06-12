from flask import Flask, render_template, request
from metar import Metar
import requests
import re
from bs4 import BeautifulSoup


url = 'https://www.ogimet.com/display_metars2.php?lang=en&' \
      'lugar=%ICAO%&tipo=SA&ord=REV&nil=SI&fmt=html&ano=%year%&' \
      'mes=%month%&day=%day%&hora=%hour1%&anof=%year%&mesf=%month%&dayf=%day%&horaf=%hour2%&minf=%min%&send=send'

url_dict = {}


def replacement(match):
    try:
        return url_dict[match.group(1)]
    except KeyError:
        return match.group(0)


pattern = re.compile(r'\%(\w+)\%')

app = Flask(__name__)


@app.route('/')
def main():
    return render_template('mainPage.html')


@app.route('/form', methods=["GET"])
def form():
    icao = request.args.get('icao_name')
    date = request.args.get('weather_date_name')
    time = request.args.get('weather_time_name')

    year_month_day = re.split(r'-', date)
    hour_min = re.split(r':', time)

    url_dict['ICAO'] = icao
    url_dict['year'] = year_month_day[0]
    url_dict['month'] = year_month_day[1]
    url_dict['day'] = year_month_day[2]
    url_dict['hour2'] = '23'
    url_dict['hour1'] = '00'
    url_dict['min'] = '59'

    query_url = pattern.sub(replacement, url)
    page = requests.get(query_url)

    error = page.text.find('#Sorry')
    if error != -1:
        return render_template('form.html', icao=icao, date=date, metar='An error has occurred')

    soup = BeautifulSoup(page.text, 'html.parser')
    date = soup.findAll('td', text=re.compile('\d\d/\d\d/\d{4} \d\d:\d\d->'))
    # print_date = print_date[:-2]
    metar = soup.findAll('td', text=re.compile('METAR'))

    print_date = 'none'
    print_metar = 'none'
    for ind in range(len(date)):
        if re.split(r':', re.search(r'\d\d:\d\d', date[ind].text).group(0))[0] == hour_min[0]:
            print_date = date[ind].text[:-2]
            print_metar = metar[ind].text
            print_metar = Metar.Metar(print_metar).string()
            print_metar = re.sub('time: .*\n', '', print_metar).replace('\n', '<br>')
            break

    f = open('tmp.html', "w", encoding="utf-8")
    f.write(print_metar)
    f.close()

    return render_template('form.html', icao=icao, date=print_date, metar=print_metar)


if __name__ == '__main__':
    app.run()
