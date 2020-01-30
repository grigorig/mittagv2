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

import recordclass

WeeklyMenu = recordclass.recordclass("WeeklyMenu", "week_number days, notice")
DailyMenu = recordclass.recordclass("DailyMenu", "day_number menus")
Menu = recordclass.recordclass("Menu", "menu_type name description student_price reduced_price normal_price calories vegetarian")

def find_daily_by_id(weekly: WeeklyMenu, day_number: int):
    for day in weekly.days:
        if day.day_number == day_number:
            return day
    raise NameError("day {} not found".format(day_number))

def find_menu_by_name(daily: DailyMenu, name: str):
    for menu in daily:
        if menu.name is name:
            return menu
    raise NameError("menu with name '{}' not found".format(name))

def find_menu_by_type(daily: DailyMenu, menu_type: str):
    menus = []
    for menu in daily.menus:
        if menu.menu_type == menu_type:
            menus.append(menu)
    if len(menus) == 0:
        raise NameError("menu with type '{}' not found".format(menu_type))
    return menus