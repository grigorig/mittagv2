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
import sys
from html import escape
from datetime import date
import datetime
from string import Template
import mittagv2.scraper as scraper
import mittagv2.utils as utils

class StaticSiteGenerator:
    """Generate a basic static site with current day's menu"""

    def __init__(self, week_number=None, day_number=None):
        self.scraper = scraper.Scraper()
        self._week = week_number if week_number != None else utils.current_week() 
        self._day = day_number if day_number != None else utils.current_day()
    
    def get_menus(self):
        """Get menu data"""
        bistro_menu, _ = self.scraper.scrape_bistro(week_number=self._week)
        mfc_menu, _ = self.scraper.scrape_mfc(week_number=self._week)
        marli_menu, _ = self.scraper.scrape_marli()
        mensa_menu, _ = self.scraper.scrape_mensa()
        return bistro_menu, mfc_menu, marli_menu, mensa_menu
    
    def scrape_all(self):
        """Scrape all current data"""
        bistro_menu, mfc_menu, marli_menu, mensa_menu = self.get_menus()
        bistro_html = self.day_to_html(bistro_menu.days[self._day], bistro_menu)
        marli_html = self.day_to_html(marli_menu.days[self._day], marli_menu)
        mfc_html = self.day_to_html(mfc_menu.days[self._day], mfc_menu)
        mensa_html = self.day_to_html(mensa_menu.days[self._day], mensa_menu)
        with open("mittagv2/resources/static_template.html") as template_file:
            template = Template(template_file.read())
            html = template.substitute(MFC_MENUS=mfc_html, MARLI_MENUS=marli_html,
                MENSA_MENUS=mensa_html, BISTRO_MENUS=bistro_html,
                DATE_STRING=datetime.datetime.now().date().isoformat(),
                WEEK_NUMBER=self._week)
            print(html)

    def day_to_html(self, day, week):
        html = ""
        for menu in day.menus:
            html += self.menu_to_html(menu)
        if week.notice:
            html += "<p>{}</p>".format(escape(week.notice).replace("\n", "<br>"))
        return html
    
    def menu_to_html(self, menu):
        name = menu.name
        if menu.menu_type:
            name = "{}: {}".format(menu.menu_type, menu.name)
        html = "<p><strong>{}</strong></p>".format(escape(name))
        if menu.description:
            html_description = menu.description.replace("\n", "<br>")
            html += "<p>{}</p>".format(html_description)
        attributes = []
        if menu.calories:
            attributes.append("Kalorien: {:d}".format(menu.calories))
        if menu.vegetarian == True:
            attributes.append("Vegetarisch")
        if len(attributes) > 0:
            html += "<p>"
            html += ", ".join(attributes)
            html += "</p>"
        html += "<p>"
        if menu.student_price:
            html += "{:.2f} € / ".format(menu.student_price).replace(".", ",")
        if menu.reduced_price:
            html += "{:.2f} € / ".format(menu.reduced_price).replace(".", ",")
        if menu.normal_price:
            html += "{:.2f} €".format(menu.normal_price).replace(".", ",")
        html += "<br><br></p>"
        return html

if __name__ == "__main__":
    week_number = None
    day_number = None
    if len(sys.argv) > 1:
        week_number = int(sys.argv[1])
    if len(sys.argv) > 2:
        day_number = int(sys.argv[2])
    generator = StaticSiteGenerator(week_number, day_number)
    generator.scrape_all()