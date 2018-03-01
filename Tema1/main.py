import sys
import urllib.request
import urllib.parse
import json
import datetime
import operator
import logging
import webbrowser

kelvin = 273.15
logging.basicConfig(filename='log.log', level=logging.DEBUG)
logging.basicConfig(filename='request.log', level=logging.DEBUG)


def get_google_place_id(city):
    logging.info('Accessing Google Geolocation API for city: %s' % city)
    params = urllib.parse.urlencode(({'address': city, 'key': 'AIzaSyD18P0LUk_mrv0uXKPGpXDjz6aK3ViS2hk'}))
    f = urllib.request.urlopen(r'https://maps.googleapis.com/maps/api/geocode/json?%s' % params)
    j = json.loads(f.read())
    logging.info(' Got id: %s for city: %s' % (j['results'][0]['place_id'], city))
    return j['results'][0]['place_id']


def get_google_info(city):
    logging.info('Accessing Google Places API for city: %s' % city)
    params = urllib.parse.urlencode(({'placeid': get_google_place_id(city),
                                      'key': 'AIzaSyD18P0LUk_mrv0uXKPGpXDjz6aK3ViS2hk'}))
    f = urllib.request.urlopen(r'https://maps.googleapis.com/maps/api/place/details/json?%s' % params)
    j = json.loads(f.read())
    logging.info("Opening browser for %s's map" % city)
    webbrowser.open(j['result']['url'])
    return j['result']['url']


def get_location_from_ip(ip):
    logging.info('Accessing Neutrino API for ip %s...' % ip)
    params = urllib.parse.urlencode(({'user-id': 'Mihaivasilache',
                                      'api-key': 'ngTmg2QEt4HVp6xDY8gU1MgJ1zgE5inmaZyyNJ8H4orOMuRQ',
                                      'ip': ip}))
    f = urllib.request.urlopen(r'https://neutrinoapi.com/ip-info?%s' % params)
    j = json.loads(f.read())
    logging.info('Got city: %s, latitude: %f, longitude: %f for ip: %s' %
                 ( j['city'], j['latitude'], j['longitude'], ip))
    return j['city'], j['latitude'], j['longitude']


def get_weather_report(lat, lng):
    logging.info('Accessing weather API for lat %f, lng %f for 5 days...' % (lat, lng))
    params = urllib.parse.urlencode(({'lat': lat, 'lon': lng, 'APPID': '61e0bae56b586e752aed5ec28bee4765'}))
    f = urllib.request.urlopen(r'https://api.openweathermap.org/data/2.5/forecast?%s' % params)
    weather_json = json.load(f)
    current_time = datetime.datetime.fromtimestamp(weather_json['list'][0]['dt']).strftime('%Y-%m-%d')
    min_temp = 0
    max_temp = 0
    forecast = dict()
    count = 0
    for i in weather_json['list']:
        if current_time != datetime.datetime.fromtimestamp(i['dt']).strftime('%Y-%m-%d'):
            print(current_time)
            print('\tMin Temp:', round(min_temp / count - kelvin))
            print('\tMax Temp:', round(max_temp / count - kelvin))
            print('\tForecast:', sorted(forecast.items(), key=operator.itemgetter(1), reverse=True)[0][0])
            current_time = datetime.datetime.fromtimestamp(i['dt']).strftime('%Y-%m-%d')
            min_temp = 0
            max_temp = 0
            forecast = dict()
            count = 0
        else:
            min_temp += i['main']['temp_min']
            max_temp += i['main']['temp_max']
            if i['weather'][0]['main'] not in forecast:
                forecast[i['weather'][0]['main']] = 1
            else:
                forecast[i['weather'][0]['main']] += 1
            count += 1


def main():
    ip = sys.argv[1]
    city, lat, lng = get_location_from_ip(ip)
    get_weather_report(lat, lng)
    get_google_info(city)


if __name__ == '__main__':
    main()
