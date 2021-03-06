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

class MarliParser:
    """Parse Marli HTML table"""

    DAY_MAP = {
        'Montag': 0,
        'Dienstag': 1,
        'Mittwoch': 2,
        'Donnerstag': 3,
        'Freitag': 4
    }

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
        name_match = re.match(r"""^\s*([\w-]+(\s+[\w-]+)??)(\s*mit|\s+in|\s+an|\s+vom|\s*\n|\s*,)""",
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
        menus = tree.xpath("/html/body/div[2]/div/main/div[2]/p[3]")
        if len(menus) != 1:
            raise ValueError("cannot find menus")
        menu = menus[0]
        for el in menu.itertext():
            self.collect_menus(el.strip())
        weekly_notice = tree.xpath("/html/body/div[2]/div/main/div[2]/p[5]")
        if len(weekly_notice) > 0:
            prefix = "Zusatzangebot:\n\n"
            self.model.notice = prefix + "\n".join(weekly_notice[0].itertext())
        self.clean_model()
        return self.model
    
    def collect_menus(self, element):
        if element in MarliParser.DAY_MAP.keys():
            self.current_day = MarliParser.DAY_MAP[element]
        elif self.current_day != None:
            day = model.find_daily_by_id(self.model, self.current_day)
            if len(day.menus) == 0:
                day.menus.append(model.Menu(menu_type="", name="",
                    description="", student_price=None, reduced_price=None,
                    normal_price=None, calories=None, vegetarian=None))
            price_match = re.search(r"""€\s*([0-9,]+)""", element)
            if price_match:
                day.menus[0].normal_price = float(price_match.group(1).replace(",", "."))
            else:
                day.menus[0].description += element + "\n"

