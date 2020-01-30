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

import re
import mittagv2.model as model
from lxml import html

class MensaParser:
    """Parse Mensa Lübeck HTML table"""

    def __init__(self, week_number):
        days = [
            model.DailyMenu(0, []),
            model.DailyMenu(1, []),
            model.DailyMenu(2, []),
            model.DailyMenu(3, []),
            model.DailyMenu(4, []),
        ]
        self.model = model.WeeklyMenu(week_number, days, None)
        self.current_day = None

    def extract_menu_name(self, description):
        """Extract menu name from description"""
        name_match = re.match(r"""^\s*([\w-]+(\s+[\w-]+)??)(\s*mit|\s+in|\s+an|\s*\n|\s*,)""",
            description, flags=re.I|re.M)
        if not name_match:
            return " ".join(re.split(r"""\s+""", description)[:3])
        return name_match.group(1)

    def clean_model(self):
        """Apply various cleanups to gathered data"""
        for day in self.model.days:
            for menu in day.menus:
                menu.description = menu.description.strip()
                menu.name = self.extract_menu_name(menu.description)

    def parse(self, html_text):
        """Parse HTML data into menu"""
        tree = html.fromstring(html_text)
        weeks = tree.xpath(r"""//*[@id="days"]""")
        if len(weeks) < 1:
            raise ValueError("cannot find menu table identifier")
        current_week = weeks[0]
        for day_number in range(5):
            day = current_week.xpath("""//*[@id="day_{}"]/table""".format(day_number))[0]
            self.parse_day(day_number, day)
        return self.model
    
    def parse_day(self, day_number, html):
        """Parse HTML table for a given day"""
        menu_index = 1
        for row in html.getchildren():
            if row.tag != "tr":
                continue
            menu_type = "Menü {}".format(menu_index)
            valid = self.parse_row(self.model.days[day_number], menu_type, row)
            if valid:
                menu_index += 1

    def parse_attributes(self, html):
        """Parse attributes for a menu"""
        children = html.getchildren()
        if len(children) < 1 or children[0].tag != "img":
            return False
        img = children[0]
        if "alt" not in img.attrib:
            return False
        return img.attrib["alt"].startswith("veg")
    
    def parse_prices(self, prices):
        """Parse prices string into numbers"""
        match = re.search(r"""€?\s*([0-9,]+)\s*€?\s*/\s*€?\s*([0-9,]+)\s*€?\s*/\s*€?\s*([0-9,]+)\s*€?""", prices)
        if "€" in prices and match:
            return (
                float(match.group(1).replace(",", ".")),
                float(match.group(2).replace(",", ".")),
                float(match.group(3).replace(",", "."))
            )
        else:
            return None
    
    def parse_description(self, desc):
        """Parse description entry"""
        elements = [ x.strip() for x in desc.itertext("strong", "br") ]
        return " ".join(elements).strip()

    def parse_row(self, day, menu_type, html):
        """Parse a row with menu info"""
        cols = html.getchildren()
        if len(cols) != 3:
            return False
        if cols[0].tag != "td":
            return False
        description = self.parse_description(cols[0])
        if len(description) == 0:
            return False
        vegetarian = self.parse_attributes(cols[1])
        prices = self.parse_prices(cols[2].text_content().strip())
        if prices is None:
            return False
        price_student, price_reduced, price_normal = prices
        name = self.extract_menu_name(description)
        menu = model.Menu(menu_type=menu_type, name=name,
            description=description, student_price=price_student,
            reduced_price=price_reduced, normal_price=price_normal,
            calories=None, vegetarian=vegetarian)
        day.menus.append(menu)
        return True