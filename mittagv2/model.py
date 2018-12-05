import recordclass

WeeklyMenu = recordclass.recordclass("WeeklyMenu", "week_number days")
DailyMenu = recordclass.recordclass("DailyMenu", "day_number menus")
Menu = recordclass.recordclass("Menu", "menu_type name description student_price reduced_price normal_price calories vegetarian")

def find_daily_by_id(weekly: WeeklyMenu, day_number: int):
    for day in weekly:
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