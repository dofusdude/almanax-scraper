# Almanax Scraper
Cloudscraper based Almanax scraping to JSON and API creation client with Python.

## Usage
The script should be used like a CLI.
See the usage with `python3 almanax-scraper.py --help`.

## Example
Scraping a date span to JSON.
```sh
$ python3 almanax-scraper.py --scrape --start 2012-09-18 --end 2021-04-25
```

Writing scraped data to API.
```sh
$ python3 almanax-scraper.py --api
```

Scrapes and sends the next month to the API.
```sh
$ python3 almanax-scraper.py --daily
```

## License
Author: Christopher Sieh <stelzo@steado.de>

This project is licensed under the GPLv3 License.
