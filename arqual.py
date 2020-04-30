#!/usr/bin/env python3

'''
/*
Copyright (C) 2020 Tiago Epifânio
Licensed under Creative Commons: By Attribution 3.0 License
http://creativecommons.org/licenses/by/3.0/

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

from datetime import datetime
from datetime import date
from datetime import timedelta

import getopt
import requests
import urllib.parse
import sys

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

VERSION_TEXT = 'ArQual 0.2.0\nNotice: All data is scraped from https://qualar.apambiente.pt'
URL_ALERTAS = 'https://sniambgeoogc.apambiente.pt/getogc/rest/services/Visualizador/QAR/MapServer/9/query?f=json&spatialRel=esriSpatialRelIntersects&orderByFields=estacao_nome,data,poluente_abv'
URL_POLUENTES = 'https://sniambgeoogc.apambiente.pt/getogc/rest/services/Visualizador/QAR/MapServer/0/query?f=json&spatialRel=esriSpatialRelIntersects&orderByFields=data,estacao_nome,poluente_abv'
URL_GLOBAL = 'https://sniambgeoogc.apambiente.pt/getogc/rest/services/Visualizador/QAR/MapServer/1/query?f=json&spatialRel=esriSpatialRelIntersects'

PRINT_RED_ON_BLACK = "\033[1;31;48m"
PRINT_COLOR_RESET = "\033[0;0m"

def build_url(base_url, where, out_fields = "*", order_by = "", return_geometry = "false"):
    encoded_where = urllib.parse.quote(where)
    url = "%s&outFields=%s&orderByFields=%s&returnGeometry=%s&where=%s" % (base_url, out_fields, order_by, return_geometry, encoded_where)
    return url

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
    formatted = "%s - %s (%s) - %s" % (attributes["poluente_abv"], attributes["avg_display"], attributes["poluente_agr"], attributes["indice_nome"])
    if (attributes["hora_display"] != "N.h"):
        formatted += " (%s)" % attributes["hora_display"]
    if (attributes["alerta"] == 1):
        formatted +=  PRINT_RED_ON_BLACK + " ALERTA!" + PRINT_COLOR_RESET

    return formatted

def format_station(station):
    attr = station["attributes"]
    return "%s, %s (%s)" % (attr["concelho_nome"], attr["estacao_nome"], attr["estacao_id"])

def format_alert(station):
    attributes = station["attributes"]
    formatted = "%s - %s - %s - %s" % (format_short_date(attributes["data"]), attributes["poluente_abv"],attributes["avg_display"], attributes["indice_nome"])
    if (attributes["hora_display"] != "N.h"):
        formatted += " (%s)" % attributes["hora_display"]

    return formatted

def get_indexes(station_id, date = "", date_min = "", date_max = "", pollutant = ""):
    if not date and not date_min and not date_max:
        today = datetime.today().strftime("%Y-%m-%d")
        yesterday = format_short_date(datetime.today() - timedelta(days=1))
        get_indexes(station_id, yesterday, None, None, pollutant)
        get_indexes(station_id, today, None, None, pollutant)
        return

    where = add_parameter("", "data", date, "=")
    where = add_parameter(where, "data", date_min, ">=")
    where = add_parameter(where, "data", date_max, "<=")
    where = add_parameter(where, "estacao_id", station_id)
    where = add_parameter(where, "poluente_abv", pollutant)

    url = build_url(URL_POLUENTES, where)
    http_response = requests.get(url)

    if http_response.status_code != 200:
        return

    response = http_response.json()

    if ("error" in response):
        return

    if "features" not in response or len(response["features"]) == 0:
        print("No data found.")
        return

    previous_date = ""
    previous_station = ""

    for feature in response["features"]:
        response_date = feature["attributes"]["data"]
        response_station = feature["attributes"]["estacao_id"]
        if (response_date != previous_date or response_station != previous_station):
            previous_date = response_date
            previous_station = response_station
            formatted_date = format_short_date(response_date)
            title = "\n%s - %s" % (feature["attributes"]["estacao_nome"], formatted_date)
            print(title)
            print("-" * len(title))

        print(format_index_values(feature["attributes"]))

def get_stations(date = ""):
    if not date:
        date = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    where = add_parameter("", "data", date)
    url = build_url(URL_GLOBAL, where, "concelho_nome,estacao_id,estacao_nome", "concelho_nome,estacao_nome")
    http_response = requests.get(url)

    if http_response.status_code != 200:
        return

    response = http_response.json()

    if ("error" in response):
        return

    formatted_stations = "\n".join(map(format_station, response["features"]))
    print(formatted_stations)

def get_alerts(station = "", date = "", date_min = "", date_max = "", pollutant = ""):
    if not station and not pollutant and not date and not date_min and not date_max:
        print("Please specify one of following: station, date or pollutant")
        exit(1)

    where = add_parameter("", "data", date, "=")
    where = add_parameter(where, "data", date_min, ">=")
    where = add_parameter(where, "data", date_max, "<=")
    where = add_parameter(where, "estacao_id", station)
    where = add_parameter(where, "poluente_abv", pollutant)

    url = build_url(URL_ALERTAS, where, "*", "data")
    http_response = requests.get(url)

    if http_response.status_code != 200:
        return

    response = http_response.json()

    if ("error" in response):
        return

    if (len(response["features"]) == 0):
        print("No data found.")
        return

    previous_station = ""

    for feature in response["features"]:
        response_station = feature["attributes"]["estacao_id"]
        if (response_station != previous_station):
            previous_station = response_station
            attr = feature["attributes"]
            title = "\n%s (%s) - %s" % (attr["estacao_nome"], attr["estacao_id"], format_short_date(attr["data"]))
            print(title)
            print("-" * len(title))

        print(format_alert(feature))

def main(argv):
    inputfile = ''
    outputfile = ''

    if len(argv) == 0 or argv[0] not in ['stations', 'indexes', 'alerts' ,'-h', '--help', '-v', '--version', '-p', '--pollutant']:
        print(HELP)
        sys.exit(1)

    if  argv[0].lower() in ['--version', '-v']:
        print(VERSION_TEXT)
        sys.exit(0)
    elif  argv[0].lower() in ['-h', '--help']:
        print(HELP)
        sys.exit(0)
    elif  argv[0].lower() == 'stations':
        date = ''

        try:
            opts, args = getopt.getopt(argv[1:],"d:",["date="])
        except getopt.GetoptError:
            print(HELP)
            sys.exit(1)

        for opt, arg in opts:
            if opt in ("-d", "--date"):
                date = arg

        get_stations(date)
    elif argv[0].lower() == 'indexes':
        date = ''
        date_min = ''
        date_max = ''
        station = ''
        pollutant = ''

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

        get_indexes(station, date, date_min, date_max, pollutant)
    elif argv[0].lower() == 'alerts':
        date = ''
        date_min = ''
        date_max = ''
        station = ''
        pollutant = ''

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

        get_alerts(station, date, date_min, date_max, pollutant)

if __name__ == "__main__":
    main(sys.argv[1:])
