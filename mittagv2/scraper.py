#
# Copyright 2019 Grigori Goronzy <greg@kinoho.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import io
import requests
import schedule
import time
import threading
import traceback
import logging
import os
from cloudant import CouchDB
import mittagv2.model as model
from mittagv2.marli_parser import MarliParser
from mittagv2.mensa_parser import MensaParser
from mittagv2.uksh_parser import BistroParser, MfcParser
import mittagv2.utils as utils

class ScrapingError(Exception):
    """Scraping error with optional associated data"""
    def __init__(self, blob=None, error=None):
        self.blob = blob
        self.error = error

class Scraper:
    """Scheduled scraping and storageof scraped data"""

    MAX_RETRIES = 3 #: Maximum number of retries before giving up
    RETRY_WAIT_TIME = 3600 #: Wait time between retries in seconds

    def scrape_bistro(self, week_number=None):
        """Scrape UKSH bistro data"""
        if not week_number:
            week_number = utils.current_week()
        url = "https://www.uksh.de/uksh_media/Speisepl%C3%A4ne/L%C3%BCbeck+_+UKSH_Bistro/Speiseplan+Bistro+KW+{:02}.pdf".format(week_number)
        pdf = requests.get(url).content
        try:
            menu = BistroParser(week_number, io.BytesIO(pdf)).parse()
            return menu, pdf
        except Exception as ex:
            raise ScrapingError(blob=pdf, error=ex)

    def scrape_mfc(self, week_number=None):
        """Scrape MFC data"""
        if not week_number:
            week_number = utils.current_week()
        url = "https://www.uksh.de/uksh_media/Speisepl%C3%A4ne/L%C3%BCbeck+_+MFC+Cafeteria/Speiseplan+Cafeteria+MFC+KW+{:02}.pdf".format(week_number)
        pdf = requests.get(url).content
        try:
            menu = MfcParser(week_number, io.BytesIO(pdf)).parse()
            return menu, pdf
        except Exception as ex:
            raise ScrapingError(blob=pdf, error=ex)

    def scrape_mensa(self):
        """Scrape Mensa data"""
        week_number = utils.current_week()
        url = "https://www.studentenwerk.sh/de/essen/standorte/luebeck/mensa-luebeck/speiseplan.html"
        data = requests.get(url).content
        try:
            menu = MensaParser(week_number).parse(data.decode("UTF-8"))
            return menu, data
        except Exception as ex:
            raise ScrapingError(blob=data, error=ex)
    
    def scrape_marli(self):
        """Scrape Marli data"""
        week_number = utils.current_week()
        url = "https://www.marli.de/rs/gastronomie_und_begegnung/mittagsangebote/index.html"
        data = requests.get(url).content
        try:
            menu = MarliParser(week_number).parse(data.decode("UTF-8"))
            return menu, data
        except Exception as ex:
            raise ScrapingError(blob=data, error=ex)

    def scheduled_scraper(self):
        """Start a scheduling scraper. This schedules scraping for each Monday
        morning. It also uses a retry mechanism to guard against intermittent
        failures"""
        self.check_scraping_status()
        schedule.every().monday.at("07:00").do(self._scrape_job)
        #schedule.every(2).minutes.do(self._scrape_job)
        while True:
            schedule.run_pending()
            time.sleep(30)
    
    def check_scraping_status(self):
        """Check scraping status (and fetch if needed)"""
        pass
    
    def _scrape_job(self):
        """Start off scraping threads for all menus"""
        logging.info("starting scraping")
        scrapings = (
            (self.scrape_bistro, "uksh-bistro"),
            (self.scrape_marli, "marli-sb"),
            (self.scrape_mensa, "swsh-mensa"),
            (self.scrape_mfc, "uksh-cafeteria")
        )
        for scraper, name in scrapings:
            self._scrape_single_background(scraper, name)
    
    def _scrape_single(self, scraper, name):
        """Scrape single menu (with retrying)"""
        logging.info("scraping {}".format(name))
        for _ in range(Scraper.MAX_RETRIES):
            try:
                menu, blob = scraper()
                self._scrape_log(name, True, blob=blob)
                self._menu(name, menu)
                break
            except ScrapingError as ex:
                self._scrape_log(name, False, blob=ex.blob, error=traceback.format_exc(limit=2))
                time.sleep(Scraper.RETRY_WAIT_TIME)
            except Exception as ex:
                self._scrape_log(name, False, error=traceback.format_exc(limit=1))
                time.sleep(Scraper.RETRY_WAIT_TIME)
    
    def _scrape_single_background(self, scraper, name):
        """Scrape a single menu in background"""
        t = threading.Thread(target=lambda: self._scrape_single(scraper, name))
        t.start()
    
    def _scrape_log(self, name, success, blob=None, error=None):
        """Store scraping log - raw data and metadata from scraping"""
        document = {
            "type": "scrape_log",
            "source_name": name,
            "at": utils.timestamp_rfc3339(),
            "success": success,
        }
        if error != None:
            document["error"] = str(error)
        logging.info("scraped: {}".format(document))
        self._store_scrape_log(document, blob)

    def _menu(self, name, menu):
        """Store menu data"""
        weekly = {
            "year_week": utils.current_year_week(), 
            "days": []
        }
        document = {
            "type": "weekly_menu", 
            "at": utils.timestamp_rfc3339(),
            "source_name": name,
            "menus": weekly
        }
        if menu.notice:
            weekly["notice"] = menu.notice
        for daily in menu.days:
            day = {
                "day": daily.day_number,
                "menus": []
            }
            for m in daily.menus:
                md = {
                    "menu_type": m.menu_type,
                    "name": m.name,
                    "normal_price": m.normal_price
                }
                if m.description:
                    md["description"] = m.description
                if m.student_price:
                    md["student_price"] = m.student_price
                if m.reduced_price:
                    md["reduced_price"] = m.reduced_price
                if m.vegetarian:
                    md["vegetarian"] = m.vegetarian
                if m.calories:
                    md["calories"] = m.calories
                day["menus"].append(md)
            if len(day) > 0:
                weekly["days"].append(day)
        logging.info("menu received: {}".format(document))
        self._store_menu(document)

    def _store_scrape_log(self, document, blob=None):
        pass
    
    def _store_menu(self, document):
        pass

class CouchScraper(Scraper):
    """Scraper with CouchDB data storage"""

    def __init__(self, user=None, auth=None, url=None):
        self.db = utils.couch_connect(user, auth, url)
        self.scrapings = self.db.create_database("mv2_scrapings")
        self.menus = self.db.create_database("mv2_menus")
        utils.create_couch_views(self.menus)
        self._last_scrape = None

    def check_scraping_status(self):
        sources = {
            "swsh-mensa": self.scrape_mensa,
            "marli-sb": self.scrape_marli,
            "uksh-cafeteria": self.scrape_mfc,
            "uksh-bistro": self.scrape_bistro
        }
        for s in sources.keys():
            menu_key = "{}/{}".format(s, utils.current_year_week())
            res = self.menus.get_view_result("_design/views", "bySourceNameYearWeek", key=menu_key).all()
            if len(res) == 0:
                logging.info("{} has no menu for current week, trying to scrape".format(s))
                self._scrape_single_background(sources[s], s)


    def _store_scrape_log(self, document, blob=None):
        doc = self.scrapings.create_document(document)
        scrape_name = "{}_{}.bin".format(document["source_name"], utils.current_year_week())
        if blob != None:
            doc.put_attachment(scrape_name, "application/octet-stream", blob)
        self._last_scrape = doc
    
    def _store_menu(self, document):
        if not self._last_scrape:
            raise RuntimeError("store scrape first")
        document["scrape_id"] = self._last_scrape["_id"]
        self.menus.create_document(document)
        self._last_scrape = None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = CouchScraper()
    scraper.scheduled_scraper()