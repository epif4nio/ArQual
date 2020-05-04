#!/usr/bin/env python3

'''
/*
Copyright (C) 2020 Tiago Epifânio
ArQual is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/
'''

from datetime import date
from datetime import datetime
from datetime import timedelta

import getopt
import requests
import sys
import urllib.parse

HELP = '\
Usage: ./arqual.py COMMAND [OPTIONS]\n\n\
Commands:\n\
  stations  Get a list of air quality measurement stations\n\
  indexes   Get air quality index for a station\n\
  alerts    Get alerts\n\n\
Options:\n\
  -d, --date DATE           Specify the date for the data you want (YYYY-MM-DD)\n\
  -i, --datemin DATE        Specify minimum date for the data you want (YYYY-MM-DD)\n\
  -x, --datemax DATE        Specify maximum date for the data you want (YYYY-MM-DD)\n\
  -s, --station STATION_ID  Specify the ID of the station\n\
  -v, --version             Get the version of the program\n\
  -h, --help                This text that you are reading\n\n\
Example 1 - get list of stations:\n\
  ./arqual.py get_stations\n\n\
Example 2 - get air quality indexes of station 3072 for 2020-04-17:\n\
  ./arqual.py indexes -s 3072 -d 2020-04-17\n\n\
Example 3 - get air quality indexes of station 3072 between 2020-04-10 and 2020-04-20:\n\
  ./arqual.py indexes -s 3072 --datemin 2020-04-10 --datemax 2020-04-20\n\
Example 4 - get all alerts since 2019-01-01\n\
  ./arqual.py alerts --datemin 2019-01-01'

VERSION_TEXT = 'ArQual 0.2.1\nNotice: All data is scraped from https://qualar.apambiente.pt'

URL_MAP_SERVER = 'https://sniambgeoogc.apambiente.pt/getogc/rest/services/Visualizador/QAR/MapServer'

URL_ALERTS = URL_MAP_SERVER + '/9/query?f=json&spatialRel=esriSpatialRelIntersects&orderByFields=estacao_nome,data,poluente_abv'
URL_INDEXES = URL_MAP_SERVER + '/0/query?f=json&spatialRel=esriSpatialRelIntersects&orderByFields=data,estacao_nome,poluente_abv'
URL_STATIONS = URL_MAP_SERVER + '/1/query?f=json&spatialRel=esriSpatialRelIntersects'

PRINT_COLOR_RESET = "\033[0;0m"
PRINT_RED_ON_BLACK = "\033[1;31;48m"

CMD_ALERTS = 'alerts'
CMD_INDEXES = 'indexes'
CMD_STATIONS = 'stations'

ATTR_ALERT = 'alerta'
ATTR_AVG_DISPLAY = 'avg_display'
ATTR_DATE = 'data'
ATTR_INDEX_NAME = 'indice_nome'
ATTR_HOUR_DISPLAY = 'hora_display'
ATTR_MUNICIPALITY_NOME = 'concelho_nome'
ATTR_POLUTTANT_ABV = 'poluente_abv'
ATTR_POLUTTANT_AGR = 'poluente_agr'
ATTR_STATION_ID = 'estacao_id'
ATTR_STATION_NAME = 'estacao_nome'

GROUP_ATTRIBUTES = 'attributes'
GROUP_FEATURES = 'features'

def add_parameter(statement, name, value, comparison_operator = "=", logical_operator = 'and'):
    if value:
        if statement:
            statement += " %s " % logical_operator
        statement += "%s%s'%s'" % (name, comparison_operator, value)
    return statement

def format_short_date(date):
    if (isinstance(date, int)):
        return datetime.utcfromtimestamp(date / 1000).strftime("%Y-%m-%d")
    else:
        return date.strftime("%Y-%m-%d")

def format_index_values(attributes):
    formatted = "%s - %s (%s) - %s" % (attributes[ATTR_POLUTTANT_ABV], attributes[ATTR_AVG_DISPLAY], attributes[ATTR_POLUTTANT_AGR], attributes[ATTR_INDEX_NAME])

    if (attributes[ATTR_HOUR_DISPLAY] != "N.h"):
        formatted += " (%s)" % attributes[ATTR_HOUR_DISPLAY]
    if (attributes[ATTR_ALERT] == 1):
        formatted +=  PRINT_RED_ON_BLACK + " ALERT!" + PRINT_COLOR_RESET

    return formatted

def format_station(station):
    attr = station[GROUP_ATTRIBUTES]
    return "%s, %s (%s)" % (attr[ATTR_MUNICIPALITY_NOME], attr[ATTR_STATION_NAME], attr[ATTR_STATION_ID])

def format_alert(station):
    attributes = station[GROUP_ATTRIBUTES]
    formatted = "%s - %s - %s - %s" % (format_short_date(attributes[ATTR_DATE]), attributes[ATTR_POLUTTANT_ABV],attributes[ATTR_AVG_DISPLAY], attributes[ATTR_INDEX_NAME])
    if (attributes[ATTR_HOUR_DISPLAY] != "N.h"):
        formatted += " (%s)" % attributes[ATTR_HOUR_DISPLAY]

    return formatted

def build_url(base_url, where, out_fields = "*", order_by = "", return_geometry = "false"):
    encoded_where = urllib.parse.quote(where)
    url = "%s&outFields=%s&orderByFields=%s&returnGeometry=%s&where=%s" % (base_url, out_fields, order_by, return_geometry, encoded_where)
    return url

def http_get(url, where, out_fields = "*", order_by = "", return_geometry = "false"):
    full_url = build_url(url, where, out_fields, order_by, return_geometry)
    http_response = requests.get(full_url)

    if http_response.status_code != 200:
        raise Exception("Http error: " + str(http_response.status_code))

    response = http_response.json()

    if ("error" in response):
        raise Exception("Error returned from server: " + str(response))

    return response

def get_indexes(station_id, date = "", date_min = "", date_max = "", pollutant = ""):
    if not date and not date_min and not date_max:
        date = datetime.today().strftime("%Y-%m-%d")

    where = add_parameter("", ATTR_DATE, date, "=")
    where = add_parameter(where, ATTR_DATE, date_min, ">=")
    where = add_parameter(where, ATTR_DATE, date_max, "<=")
    where = add_parameter(where, ATTR_STATION_ID, station_id)
    where = add_parameter(where, ATTR_POLUTTANT_ABV, pollutant)

    response = http_get(URL_INDEXES, where)

    if GROUP_FEATURES not in response or len(response[GROUP_FEATURES]) == 0:
        raise Exception("No data found.")

    previous_date = previous_station = ""

    for feature in response[GROUP_FEATURES]:

        response_date = feature[GROUP_ATTRIBUTES][ATTR_DATE]
        response_station = feature[GROUP_ATTRIBUTES][ATTR_STATION_ID]

        if (response_date != previous_date or response_station != previous_station):
            previous_date = response_date
            previous_station = response_station
            formatted_date = format_short_date(response_date)
            title = "\n%s - %s" % (feature[GROUP_ATTRIBUTES][ATTR_STATION_NAME], formatted_date)
            print(title)
            print("-" * len(title))

        print(format_index_values(feature[GROUP_ATTRIBUTES]))

def get_stations(date = ""):
    if not date:
        date = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    where = add_parameter("", ATTR_DATE, date)

    response = http_get(URL_STATIONS, where, "*", "concelho_nome,estacao_id,estacao_nome", "concelho_nome,estacao_nome")

    formatted_stations = "\n".join(map(format_station, response[GROUP_FEATURES]))
    print(formatted_stations)

def get_alerts(station = "", date = "", date_min = "", date_max = "", pollutant = ""):
    if not station and not pollutant and not date and not date_min and not date_max:
        raise Exception("Please specify one of following: station, date or pollutant")

    where = add_parameter("", ATTR_DATE, date, "=")
    where = add_parameter(where, ATTR_DATE, date_min, ">=")
    where = add_parameter(where, ATTR_DATE, date_max, "<=")
    where = add_parameter(where, ATTR_STATION_ID, station)
    where = add_parameter(where, ATTR_POLUTTANT_ABV, pollutant)

    response = http_get(URL_ALERTS, where, "*", ATTR_DATE)

    if (len(response[GROUP_FEATURES]) == 0):
        raise Exception("No data found.")

    previous_station = ""

    for feature in response[GROUP_FEATURES]:
        response_station = feature[GROUP_ATTRIBUTES][ATTR_STATION_ID]
        if (response_station != previous_station):
            previous_station = response_station
            attr = feature[GROUP_ATTRIBUTES]
            title = "\n%s (%s) - %s" % (attr[ATTR_STATION_NAME], attr[ATTR_STATION_ID], format_short_date(attr[ATTR_DATE]))
            print(title + "\n" + "-" * len(title))
        print(format_alert(feature))

def main(argv):
    if len(argv) == 0 or argv[0] not in [CMD_STATIONS, CMD_INDEXES, CMD_ALERTS ,'-h', '--help', '-v', '--version', '-p', '--pollutant']:
        print(HELP)
        sys.exit(1)

    date = date_min = date_max = station = pollutant = ''

    if  argv[0].lower() in ['--version', '-v']:
        print(VERSION_TEXT)
        sys.exit(0)
    elif  argv[0].lower() in ['-h', '--help']:
        print(HELP)
        sys.exit(0)
    elif  argv[0].lower() == CMD_STATIONS:
        try:
            opts, args = getopt.getopt(argv[1:],"d:",["date="])
        except getopt.GetoptError:
            print(HELP)
            sys.exit(1)

        for opt, arg in opts:
            if opt in ("-d", "--date"):
                date = arg

        get_stations(date)
    elif argv[0].lower() in (CMD_INDEXES, CMD_ALERTS) :
        try:
            opts, args = getopt.getopt(argv[1:],"d:s:i:x:p:",["date=","station=","datemin=","datemax=","pollutant="])
        except getopt.GetoptError:
            print(HELP)
            sys.exit(1)
        for opt, arg in opts:
            if opt in ("-d", "--date"):
                date = arg
            elif opt in ("-i", "--datemin"):
                date_min = arg
            elif opt in ("-x", "--datemax"):
                date_max = arg
            elif opt in ("-s", "--station"):
                station = arg
            elif opt in ("-p", "--pollutant"):
                pollutant = arg

        if argv[0].lower() == CMD_INDEXES:
            get_indexes(station, date, date_min, date_max, pollutant)
        else:
            get_alerts(station, date, date_min, date_max, pollutant)

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as ex:
        print('Error: ' + str(ex))
