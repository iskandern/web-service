import math
import re


def get_cover(x):
    if x == 'CLR' or x == 'SKC':
        return 0
    if x == 'FEW':
        return 1
    if x == 'SCT':
        return 2
    if x == 'BKN':
        return 3
    if x == 'OVC' or x == '0VC':
        return 4
    if x == 'VV':
        return 5
    return -1


weather_list = ['BR', 'SH', 'SN', 'RA', 'FZ', 'FG', 'BL', 'TS', 'DZ', 'HZ',
                'PL', 'UP', 'SQ', 'FU', 'GS', 'BC', 'MI', 'VA']
columns_order = ['dep_intens', 'dep_BR', 'dep_SH', 'dep_SN', 'dep_RA', 'dep_FZ',
                 'dep_FG', 'dep_BL', 'dep_TS', 'dep_DZ', 'dep_HZ', 'dep_PL', 'dep_UP',
                 'dep_SQ', 'dep_FU', 'dep_GS', 'dep_BC', 'dep_MI', 'dep_VA', 'dep_wnd_spd',
                 'dep_gust', 'dep_vis', 'dep_temp', 'dep_vv', 'dep_CB_amount', 'dep_ltg',
                 'dep_cloud', 'dep_airport', 'season', 'airline', 'arr_intens', 'arr_BR',
                 'arr_SH', 'arr_SN', 'arr_RA', 'arr_FZ', 'arr_FG', 'arr_BL', 'arr_TS', 'arr_DZ',
                 'arr_HZ', 'arr_PL', 'arr_UP', 'arr_SQ', 'arr_FU', 'arr_GS', 'arr_BC', 'arr_MI',
                 'arr_VA', 'arr_wnd_spd', 'arr_gust', 'arr_vis', 'arr_temp', 'arr_vv',
                 'arr_CB_amount', 'arr_ltg', 'arr_cloud', 'arr_airport']
feat_dict = {
    'intens': 'precipitation intensity',
    'BR': 'mist',
    'SH': 'showers',
    'RA': 'rain',
    'FZ': 'freezing',
    'FG': 'fog',
    'BL': 'blowing',
    'TS': 'thunderstorm',
    'DZ': 'drizzle',
    'HZ': 'haze',
    'PL': 'ice pellets',
    'UP': 'unknown precipitation',
    'SQ': 'squall',
    'FU': 'smoke',
    'GS': 'snow pellets',
    'BC': 'patches',
    'MI': 'shallow',
    'VA': 'volcanic ash',
    'wnd': 'wind speed',
    'gust': 'wind gusts',
    'vis': 'visibility',
    'temp': 'temperature',
    'vv': 'clouds cannot be seen because of fog or heavy precipitation',
    'CB': 'presence of cumulonimbus clouds',
    'ltg': 'lightning',
    'cloud': 'cloud coverage',
}

def getStrToPrint(feat_name, feat_val):
    if feat_name == 'airline' or feat_name == 'season':
        return ''
    splitInfo = re.split('_', feat_name)
    place = splitInfo[0]
    feat = splitInfo[1]
    if feat == 'airport':
        return ''
    if place == 'arr':
        place = 'Arrival'
    if place == 'dep':
        place = 'Departure'

    return place + ' ' + feat_dict[feat] + ': ' + str(round(feat_val, 2))

def getFeaturesFromMETAR(metar):
    data = re.search('METAR\s(\w{4})\s(\d{6})Z(.*)\s(?P<kt_part>.*KT)\s(\d\d\dV\d\d\d\s)?'
                     '(?P<sm_part>.*SM)\s(?P<prec_cld>.*?)\s(?P<temp>M?\d{1,2})/(?P<dewpt>M?\d{1,2})?'
                     '\s(.*?)(RMK\s(?P<rmk>.*))?=', metar)

    if data is None:
        print(metar)
        return 0

    metar_features_dict = {}

    # ltg
    metar_features_dict['ltg'] = 0
    if not data.group('rmk') is None:
        line = data.group('rmk')
        if re.search('LTG', line):
            metar_features_dict['ltg'] = 1

    # clouds
    if data.group('prec_cld') is None:
        print('wtf1', metar)
        return 1

    cloud_pattern = '(?P<cover>VV|CLR|SKC|SCK|NSC|NCD|BKN|SCT|FEW|[O0]VC)(?P<height>[\d]{2,3})?(?P<cloud>[A-Z][A-Z]+)?'
    cloud_info = re.findall(cloud_pattern, data.group('prec_cld'))

    weather_group = re.sub(cloud_pattern, '', data.group('prec_cld'))

    if cloud_info is None:
        print('wtf2 next', metar)
        return 2

    val = cb_val = tcu_val = -1
    min_height = height = cb_height = tcu_height = 1000

    for i_cloud in range(len(cloud_info)):
        if not cloud_info[i_cloud][2].replace(' ', '') == '':
            if cloud_info[i_cloud][2] == 'CB':
                new_cb_val = get_cover(cloud_info[i_cloud][0])
                if new_cb_val == -1:
                    print('wtf4', metar)
                    return 3
                if new_cb_val > cb_val:
                    cb_val = new_cb_val
                    if cloud_info[i_cloud][1] == '':
                        print('wtf5', metar)
                        return 4
                    cb_height = cloud_info[i_cloud][1]

            elif cloud_info[i_cloud][2] == 'TCU':
                new_tcu_val = get_cover(cloud_info[i_cloud][0])
                if new_tcu_val == -1:
                    print('wtf4', metar)
                    return 5
                if new_tcu_val > tcu_val:
                    tcu_val = new_tcu_val
                    if cloud_info[i_cloud][1] == '':
                        print('wtf5', metar)
                        return 6
                    tcu_height = cloud_info[i_cloud][1]
            else:
                print('wtf3', metar)
                return 7

        else:
            new_val = get_cover(cloud_info[i_cloud][0])
            if new_val == 0:
                val = new_val
                break
            if new_val == 5:
                val = new_val
                break
            if new_val == -1:
                print('wtf4', metar)
                next_elem = True
                break
            min_height = min(min_height, height)
            if new_val > val:
                val = new_val
                if cloud_info[i_cloud][1] == '':
                    print('wtf5', metar)
                    return 8
                #                     print('---', i, ok_flights['ORIGIN_AIRPORT'][i], ok_flights['DESTINATION_AIRPORT'][i])
                height = int(cloud_info[i_cloud][1])

    if val == -1 and cb_val == -1 and tcu_val == -1:
        print('wtf6', metar, cloud_info)
        return 9

    metar_features_dict['vv'] = 0
    metar_features_dict['CB_amount'] = 0
    metar_features_dict['cloud'] = 0
    metar_features_dict['cloud_type'] = -1
    metar_features_dict['min_height'] = -1
    metar_features_dict['CB_val'] = 0
    metar_features_dict['TCU_val'] = 0
    metar_features_dict['CB_height'] = -1
    metar_features_dict['TCU_height'] = -1

    if not val == -1:
        if val == 5:
            metar_features_dict['cloud'] = 1
            metar_features_dict['vv'] = 1
        else:
            if val == 4:
                if height < 20:
                    metar_features_dict['cloud'] = 2
                else:
                    metar_features_dict['cloud'] = 1
            metar_features_dict['min_height'] = min_height
            metar_features_dict['cloud_type'] = val

    if not cb_val == -1:
        metar_features_dict['CB_val'] = cb_val
        metar_features_dict['CB_amount'] = 1
        metar_features_dict['CB_height'] = cb_height
    if not tcu_val == -1:
        metar_features_dict['TCU_val'] = tcu_val
        metar_features_dict['TCU_height'] = tcu_height

    # weather
    intens = 0
    if re.search('\+', weather_group):
        intens = 3
    elif re.search('\-', weather_group):
        intens = 1
    metar_features_dict['intens'] = intens

    for item in weather_list:
        metar_features_dict[item] = 0

    for item in weather_list:
        if re.search(item, weather_group):
            weather_group = re.sub(item, '', weather_group)
            metar_features_dict[item] = 1
            metar_features_dict['intens'] = 2

    # kt
    kt_pattern = '(?P<dir>[\d]{3}|VRB)(?P<speed>\d\d)(G(?P<gust>\d\d))?KT'
    kt_info = re.search(kt_pattern, data.group('kt_part'))
    if kt_info is None:
        print('wtf6.5 next', metar)
        return 10
    if kt_info.group('speed') is None:
        print('wtf7', metar)
        return 11
    wnd_spd = kt_info.group('speed')
    gust = wnd_spd

    metar_features_dict['wnd_spd'] = int(wnd_spd) / 50
    metar_features_dict['gust'] = int(gust) / 70
    if not kt_info.group('gust') == None:
        gust = kt_info.group('gust')
        metar_features_dict['gust'] = int(gust) / 70

    # visibility
    vis = 10
    sm_pattern = '((?P<vis_comb>(?P<vis_int_part>\d+)\s+(?P<vis_frac_part>\d+/\d+))|(?P<vis_int>\d+)|(?P<vis_frac>\d+/\d+))SM'
    visib_str = re.search(sm_pattern, data.group('sm_part'))
    if visib_str is None:
        print('wtf8 next', metar)
        return 12
    if not visib_str.group('vis_int') is None:
        vis = int(visib_str.group('vis_int'))
    elif not visib_str.group('vis_frac') is None:
        frac = re.search('(?P<dvdr>\d+)/(?P<dvdnt>\d+)', visib_str.group('vis_frac'))
        vis = int(frac.group('dvdr')) / int(frac.group('dvdnt'))
        if int(frac.group('dvdnt')) > 8 and not int(frac.group('dvdnt')) == 16:
            print('next', metar)
    elif not visib_str.group('vis_comb') is None:
        frac = re.search('(?P<dvdr>\d+)/(?P<dvdnt>\d+)', visib_str.group('vis_frac_part'))
        if int(frac.group('dvdnt')) > 8 and not int(frac.group('dvdnt')) == 16:
            print('next', metar)
        vis = int(visib_str.group('vis_int_part')) + int(frac.group('dvdr')) / int(frac.group('dvdnt'))
    else:
        print('wtf9', metar)
        return 13

    if vis > 10:
        vis = 10
    vis0_1 = round(abs(0.23 * math.log(7.5 * (vis + 0.133))), 2)

    metar_features_dict['vis'] = vis0_1

    # temperature
    temp = int(re.search('\d+', data.group('temp')).group())
    if re.search('M', data.group('temp')):
        temp *= -1

    dew_p_diff = 1
    if not data.group('dewpt') is None:
        dew_pt = int(re.search('\d+', data.group('dewpt')).group())
        if re.search('M', data.group('dewpt')):
            dew_pt *= -1
        if abs(temp - dew_pt) < 3:
            dew_p_diff = 0

    if temp > 2:
        metar_features_dict['temp'] = 0
    elif temp > -15:
        metar_features_dict['temp'] = 1
    else:
        metar_features_dict['temp'] = 2

    metar_features_dict['dew_p_diff'] = dew_p_diff

    return metar_features_dict


def getATMAPScore(metar_features_dict):
    cld_cover = False
    if metar_features_dict['cloud_type'] in [3, 4] or metar_features_dict['vv'] == 1:
        cld_cover = True

    # Visibility & ceiling
    cld_answer = 0
    if metar_features_dict['vis'] < 0.22 or (cld_cover and metar_features_dict['min_height'] < 1):
        cld_answer = 5
    elif (0.22 <= metar_features_dict['vis'] < 0.27) or (cld_cover and 1 <= metar_features_dict['min_height'] < 3):
        cld_answer = 4
    elif (0.27 <= metar_features_dict['vis'] < 0.37) or (cld_cover and 3 <= metar_features_dict['min_height'] < 5):
        cld_answer = 2

    # Precipitations
    prec_answer = 0
    if metar_features_dict['FZ'] == 1:
        prec_answer = 3
    elif metar_features_dict['SN'] == 1 and metar_features_dict['intens'] == 0:
        prec_answer = 2
    elif metar_features_dict['SN'] == 1:
        prec_answer = 3
    #     elif metar_features_dict['SG'] == 1:
    #         prec_answer = 2
    elif metar_features_dict['RA'] == 1 and metar_features_dict['intens'] == 1:
        prec_answer = 2
    elif metar_features_dict['RA'] == 1 and metar_features_dict['intens'] == 0.5:
        prec_answer = 1
    elif metar_features_dict['UP'] == 1:
        prec_answer = 1
    elif metar_features_dict['DZ'] == 1:
        prec_answer = 1

    # Freezing contions
    fc_answer = 0
    visible_moisture = 0
    if metar_features_dict['FZ'] == 1 and metar_features_dict['RA'] == 1:
        visible_moisture = 5
    elif metar_features_dict['RA'] == 1 and metar_features_dict['intens'] == 1:
        visible_moisture = 4
    #     elif metar_features_dict['SG'] == 1:
    #         visible_moisture = 4
    elif metar_features_dict['RA'] == 1 and metar_features_dict['SN'] == 1:
        visible_moisture = 4
    elif metar_features_dict['SN'] == 1 and metar_features_dict['intens'] == 0:
        visible_moisture = 4
    elif metar_features_dict['SN'] == 1:
        visible_moisture = 5
    elif metar_features_dict['BR'] == 1:
        visible_moisture = 4
    elif metar_features_dict['RA'] == 1:
        visible_moisture = 3
    elif metar_features_dict['PL'] == 1:
        visible_moisture = 3
    #     elif metar_features_dict['GR'] == 1:
    #         visible_moisture = 3
    elif metar_features_dict['GS'] == 1:
        visible_moisture = 3
    elif metar_features_dict['UP'] == 1:
        visible_moisture = 3
    elif metar_features_dict['FG'] == 1:
        visible_moisture = 3
    elif metar_features_dict['DZ'] == 1:
        visible_moisture = 3

    if metar_features_dict['temp'] == 1 and visible_moisture == 5:
        fc_answer = 4
    elif metar_features_dict['temp'] == 2:
        fc_answer = 4
    elif metar_features_dict['temp'] == 1 and visible_moisture == 4:
        fc_answer = 3
    elif metar_features_dict['temp'] == 1 and (visible_moisture == 3 or metar_features_dict['dew_p_diff'] == 0):
        fc_answer = 1

    # Wind
    wind_answer = 0
    if 15 < metar_features_dict['wnd_spd'] * 50 <= 20:
        wind_answer = 1
    elif 20 < metar_features_dict['wnd_spd'] * 50 <= 30:
        wind_answer = 2
    elif metar_features_dict['wnd_spd'] * 50 > 30:
        wind_answer = 3

    if (metar_features_dict['gust'] * 70 - metar_features_dict['wnd_spd'] * 50) > 1:
        wind_answer += 1

    # Dangerous phenomena
    dp_val = 0
    if metar_features_dict['VA'] == 1:
        dp_val = 24
    elif metar_features_dict['SQ'] == 1:
        dp_val = 24
    elif metar_features_dict['GS'] == 1:
        dp_val = 18
    elif metar_features_dict['PL'] == 1:
        dp_val = 24
    elif metar_features_dict['TS'] == 1 and metar_features_dict['intens'] == 1:
        dp_val = 30
    elif metar_features_dict['TS'] == 1:
        dp_val = 24

    cb_val = 0
    if not metar_features_dict['CB_val'] == 0:
        if metar_features_dict['CB_height'] == 4:
            cb_val = 12
        if metar_features_dict['CB_height'] == 3:
            cb_val = 10
        if metar_features_dict['CB_height'] == 2:
            cb_val = 6
        if metar_features_dict['CB_height'] == 1:
            cb_val = 4

    tcu_val = 0
    if not metar_features_dict['TCU_val'] == 0:
        if metar_features_dict['TCU_height'] == 4:
            tcu_val = 10
        if metar_features_dict['TCU_height'] == 3:
            tcu_val = 8
        if metar_features_dict['TCU_height'] == 2:
            tcu_val = 5
        if metar_features_dict['TCU_height'] == 1:
            tcu_val = 3

    ts_hint_val = 0
    if cb_val == 12 and metar_features_dict['SH'] == 1 and metar_features_dict['intens'] == 0:
        ts_hint_val = 18
    elif (cb_val == 10 or tcu_val == 10) and metar_features_dict['SH'] == 1 and metar_features_dict['intens'] == 0:
        ts_hint_val = 12
    elif (cb_val == 6 or tcu_val == 8) and metar_features_dict['SH'] == 1 and metar_features_dict['intens'] == 0:
        ts_hint_val = 10
    elif (cb_val == 4 or tcu_val == 5) and metar_features_dict['SH'] == 1 and metar_features_dict['intens'] == 0:
        ts_hint_val = 8
    elif tcu_val == 3 and metar_features_dict['SH'] == 1 and metar_features_dict['intens'] == 0:
        ts_hint_val = 4
    elif cb_val == 12 and metar_features_dict['SH'] == 1:
        ts_hint_val = 24
    elif (cb_val == 10 or tcu_val == 10) and metar_features_dict['SH'] == 1:
        ts_hint_val = 20
    elif (cb_val == 6 or tcu_val == 8) and metar_features_dict['SH'] == 1:
        ts_hint_val = 15
    elif (cb_val == 4 or tcu_val == 5) and metar_features_dict['SH'] == 1:
        ts_hint_val = 12
    elif tcu_val == 3 and metar_features_dict['SH'] == 1:
        ts_hint_val = 6

    dp_answer = max(dp_val, cb_val, tcu_val, ts_hint_val)

    return cld_answer, prec_answer, fc_answer, wind_answer, dp_answer
