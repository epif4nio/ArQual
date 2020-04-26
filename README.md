# ArQual
ArQual, air quality index measurements in Portuguese territory.

All data is scraped from the website of [APA - Associação Portuguesa do Ambiente](https://qualar.apambiente.pt/).
That site is extremely slow and this script is meant to help with that, bringing air quality measurements right into your command line.

# How to use
```
Usage: arqual COMMAND [OPTIONS]

Commands:
  stations  Get a list of air quality measurement stations
  indexes   Get air quality index for a station

Options:
  -d, --date DATE           Specify the date for the data you want (YYYY-MM-DD)
  -s, --station STATION_ID  Specify the ID of the station
  -v, --version             Get the version of the program
  -h, --help                This text that you are reading
```

# Copyright
Copyright (C) 2020 Tiago Epifânio

# License
Licensed under Creative Commons: By Attribution 3.0 License http://creativecommons.org/licenses/by/3.0/

ArQual is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.
