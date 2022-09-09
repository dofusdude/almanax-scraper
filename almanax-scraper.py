"""
Almanax Scraper: Multilingual scraping of the Dofus Almanax.
Copyright (C) 2022 Christopher Sieh
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import argparse
import requests
import os
import sys

almanax_api_url="https://alm.dofusdu.de/dofus"

base_url = "http://www.krosmoz.com"
date_format = '%Y-%m-%d'
almanax_start_date = datetime.strptime("2012-09-18", date_format)
iterate_link = ""
daily_json_file = "almanax-data.json"

client_secret = "secret"

_almanax = dict()

# https://stackoverflow.com/questions/4934806/how-can-i-find-scripts-directory
def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

daily_json_file_abs = get_script_path() + "/" + daily_json_file

def addLangArrIfNotExist(obj, lang):
    if lang not in obj:
        obj[lang] = []

# help looping over a range between two dates
def date_range(start, end):
    for n in range(int((end - start).days)+1):
        yield start + timedelta(n)

def scrape_all_langs(start_date=None, end_date=None, out_file_include_range=False):
    start = datetime.strptime(start_date, date_format) if start_date else almanax_start_date
    end = datetime.strptime(end_date, date_format) if end_date else datetime.today()
    for curr_date in date_range(start, end):
        curr_date = curr_date.strftime(date_format)
        print("scraping " + curr_date)
        try:
            scrape(curr_date, "en")
        except:
            print(f"day {curr_date} failed")
            continue
        scrape(curr_date, "fr")
        scrape(curr_date, "de")
        scrape(curr_date, "it")
        scrape(curr_date, "es")

    out_file = f"almanax-data-{start.strftime(date_format)}_{end.strftime(date_format)}.json" if out_file_include_range else daily_json_file
    with open(get_script_path() + "/" + out_file, 'w') as f:
        json.dump(_almanax, f, indent=4, ensure_ascii=False)


def scrape(date, lang):
    iterate_link = base_url + "/" + lang + "/almanax/" + date

    take_begin = ""
    take_end = ""
    bonus_take = ""

    if lang == "fr":
        take_begin = "Récupérer "
        take_end = " et rapporter"
        bonus_take = "Bonus : "
    if lang == "en":
        take_begin = "Find "
        take_end = " and take"
        bonus_take = "Bonus: "
    if lang == "de":
        take_begin = "Sich "
        take_end = " beschaffen"
        bonus_take = "Bonus: "
    if lang == "it":
        take_begin = "Ottieni "
        take_end = " e porta"
        bonus_take = "Bonus: "
    if lang == "es":
        take_begin = "Recolectar "
        take_end = " y llevárselo"
        bonus_take = "Bonus: "

    html = requests.get(iterate_link).content

    soup = BeautifulSoup(html, 'html.parser')

    dofus_container = soup.find(id="achievement_dofus")
    mid_container = dofus_container.find("div", {"class": "more"})

    bonus_type = str(mid_container.previousSibling).strip()[len(bonus_take):]  # take only in english

    offering = mid_container.find("p", {"class": "fleft"}).text
    offering = offering.strip()
    index_start = len(take_begin)

    index_stop = offering.index(take_end)
    offering = offering[index_start:index_stop]

    offering_count = 0

    for s in offering.split():
        if s.isdigit():
            offering_count = int(s)
            break
    offering = offering.replace(str(offering_count), '').strip()

    pic = mid_container.img['src']

    bonus = str(mid_container)
    bonus = bonus[len('<div class="more">'):bonus.index('<div class="more-infos">')].strip()
    bonus = bonus.replace('<b>', '').replace('</b>', '')
    bonus = bonus.replace('<i>', '').replace('</i>', '')
    bonus = bonus.replace('<u>', '').replace('</u>', '')

    data = {
        "date": date,
        "item_quantity": offering_count,
        "item": offering,
        "description": bonus.replace('\n', " ").replace("\r\n", " "),
        "bonus": bonus_type.replace('\n', " ").replace("\r\n", " "),
        "language": lang,
        "item_picture_url": pic
    }
    addLangArrIfNotExist(_almanax, lang)
    _almanax[lang].append(data)


def json_to_api(path):
    with open(path, 'r') as f:
        data = json.load(f)

    # insert all new entries in english
    for offering in data["en"]:
        r = requests.post(almanax_api_url, json=offering, headers={"Authorization": f"Bearer {client_secret}"})  # created 201 when all ok
        if r.status_code > 214 and r.status_code != 406:
            print(offering)
            print(r.status_code)
            print(r.json().get("errors"))
            exit(r.status_code)

        if r.status_code == 406:
            # exists but can be outdated
            # 200 == no update, 201 == created new one, expecting translations for that now
            p = requests.put(almanax_api_url, json=offering, headers={"Authorization": f"Bearer {client_secret}"})
            if p.status_code == 201:
                print("just updated an offering")

    # add the translations
    for lang, offerings in data.items():
        if lang == "en":
            continue
        for offering in offerings:
            r = requests.put(f"{almanax_api_url}/translate", json=offering, headers={"Authorization": f"Bearer {client_secret}"})

            if r.status_code > 214:
                print(offering)
                print(r.status_code)
                print(r.json().get("errors"))
                exit(r.status_code)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="scrape dofus almanax")
    group = parser.add_mutually_exclusive_group()

    group.add_argument("--scrape", action="store_true", help="scrapes a range with start and end params, else from beginning of almanax time till today")
    group.add_argument("--api", action="store_true", help="sends the generated data to the api")
    group.add_argument("--daily", action="store_true", help="scrapes next month and sends to api")
    group.add_argument("--init", action="store_true", help="loads old almanax data if it exists and posts them to the api")

    parser.add_argument("--start", help="start date", type=str)
    parser.add_argument("--end", help="end date", type=str)

    args = parser.parse_args()

    if args.init:
        dirs = os.listdir(get_script_path())
        for filename in dirs:
            if not filename.endswith(".json") or not filename.startswith("almanax-data-"):
                continue
            file_cleaned = filename.replace("almanax-data-", "").replace(".json", "")
            
            file_date_range = filename.split("_")
            if len(file_date_range) == 2:
                with open(get_script_path() + "/" + filename, 'r') as f:
                    data = json.load(f)
                json_to_api(filename)

        if os.path.exists(daily_json_file_abs):
            json_to_api(daily_json_file_abs)

    if args.daily:
        try:
            os.remove(daily_json_file_abs)
        except:
            pass

        date_start = (datetime.today() - timedelta(days=7)).strftime(date_format)
        date_start_f = datetime.strptime(date_start, date_format)
        date_in_a_month = (date_start_f + timedelta(days=38)).strftime(date_format)
        scrape_all_langs(date_start, date_in_a_month)
        json_to_api(daily_json_file_abs)

    if args.scrape:
        scrape_all_langs(args.start, args.end, True)

    if args.api:
        if os.path.exists(daily_json_file_abs):
            json_to_api(daily_json_file_abs)