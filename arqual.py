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
Usage: arqual COMMAND [OPTIONS]\n\n\
Commands:\n\
  stations  Get a list of air quality measurement stations\n\
  indexes   Get air quality index for a station\n\n\
Options:\n\
  -d, --date DATE           Specify the date for the data you want (YYYY-MM-DD)\n\
  -s, --station STATION_ID  Specify the ID of the station\n\
  -v, --version             Get the version of the program\n\
  -h, --help                This text that you are reading'

VERSION_TEXT = 'ArQual 0.1.0\nNotice: All data is scraped from https://qualar.apambiente.pt'
URL_POLUENTES = 'https://sniambgeoogc.apambiente.pt/getogc/rest/services/Visualizador/QAR/MapServer/0/query?f=json&spatialRel=esriSpatialRelIntersects'
URL_GLOBAL = 'https://sniambgeoogc.apambiente.pt/getogc/rest/services/Visualizador/QAR/MapServer/1/query?f=json&spatialRel=esriSpatialRelIntersects'

def build_url(base_url, where, out_fields = "*", order_by = "", return_geometry = "false"):
    encoded_where = urllib.parse.quote(where)
    url = "%s&outFields=%s&orderByFields=%s&returnGeometry=%s&where=%s" % (base_url, out_fields, order_by, return_geometry, encoded_where)
    return url

def add_parameter(statement, name, value, operator = 'and'):
    if statement:
        statement += " %s " % operator
    statement += "%s='%s'" % (name, value)
    return statement

def get_indexes(estacao_id, data = ""):
    if not data:
        today = datetime.today().strftime("%Y-%m-%d")
        yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        get_indexes(estacao_id, yesterday)
        print("\n")
        get_indexes(estacao_id, today)
        return

    where = add_parameter("", "data", data)
    where = add_parameter(where, "estacao_id", estacao_id)

    url = build_url(URL_POLUENTES, where)

    http_response = requests.get(url)

    if http_response.status_code != 200:
        return

    response = http_response.json()

    if ("error" in response):
        return

    if "features" not in response or len(response["features"]) == 0:
        return

    response_date = response["features"][0]["attributes"]["data"]
    formatted_date = datetime.utcfromtimestamp(response_date / 1000).strftime('%Y-%m-%d')

    title = "%s - %s" % (response["features"][0]["attributes"]["estacao_nome"], formatted_date)
    print(title)
    print("-" * len(title))

    for feature in response["features"]:
        attributes = feature["attributes"]
        print("%s: %s (%s) - %s" % (attributes["poluente_abv"], attributes["avg_display"], attributes["poluente_agr"], attributes["indice_nome"]))

def format_station(station):
    attr = station["attributes"]
    return "%s, %s (%s)" % (attr["concelho_nome"], attr["estacao_nome"], attr["estacao_id"])

def get_stations(data = ""):
    if not data:
        data = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    where = add_parameter("", "data", data)
    url = build_url(URL_GLOBAL, where, "concelho_nome,estacao_id,estacao_nome", "concelho_nome,estacao_nome")
    http_response = requests.get(url)

    if http_response.status_code != 200:
        return

    response = http_response.json()

    if ("error" in response):
        return

    estacoes_formatted = "\n".join(map(format_station, response["features"]))
    print(estacoes_formatted)

def main(argv):
    inputfile = ''
    outputfile = ''

    if len(argv) == 0 or argv[0] not in ['stations', 'indexes', '-h', '--help', '-v', '--version']:
        print(HELP)
        sys.exit(1)

    if  argv[0].lower() in ['--version', '-v']:
        print(VERSION_TEXT)
        sys.exit(0)
    elif  argv[0].lower() in ['-h', '--help']:
        print(HELP)
        sys.exit(0)
    elif  argv[0].lower() == 'stations':
        data = ''

        try:
            opts, args = getopt.getopt(argv[1:],"d:",["date="])
        except getopt.GetoptError:
            print(HELP)
            sys.exit(1)

        for opt, arg in opts:
            if opt in ("-d", "--date"):
                data = arg

        get_stations(data)
    elif argv[0].lower() == 'indexes':
        data = ''
        estacao = ''

        try:
            opts, args = getopt.getopt(argv[1:],"d:s:",["date=","station="])
        except getopt.GetoptError:
            print(HELP)
            sys.exit(1)
        for opt, arg in opts:
            if opt in ("-d", "--date"):
                data = arg
            elif opt in ("-s", "--station"):
                estacao = arg

        if (not estacao):
            print('Error: missing argument --station\n')
            print(HELP)
            sys.exit(1)

        get_indexes(estacao, data)

if __name__ == "__main__":
    main(sys.argv[1:])
