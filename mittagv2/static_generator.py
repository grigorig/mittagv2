import io
from html import escape
from datetime import date
import datetime
from string import Template
import mittagv2.scraper as scraper
import mittagv2.utils as utils

class StaticSiteGenerator:
    """Generate a basic static site with current day's menu"""

    def __init__(self):
        self.scraper = scraper.Scraper()
    
    def get_menus(self):
        """Get menu data"""
        bistro_menu, _ = self.scraper.scrape_bistro()
        mfc_menu, _ = self.scraper.scrape_mfc()
        marli_menu, _ = self.scraper.scrape_marli()
        mensa_menu, _ = self.scraper.scrape_mensa()
        return bistro_menu, mfc_menu, marli_menu, mensa_menu
    
    def scrape_all(self):
        """Scrape all current data"""
        day_number = utils.current_day()
        bistro_menu, mfc_menu, marli_menu, mensa_menu = self.get_menus()
        bistro_html = self.day_to_html(bistro_menu.days[day_number])
        marli_html = self.day_to_html(marli_menu.days[day_number])
        mfc_html = self.day_to_html(mfc_menu.days[day_number])
        mensa_html = self.day_to_html(mensa_menu.days[day_number])
        with open("mittagv2/resources/static_template.html") as template_file:
            template = Template(template_file.read())
            html = template.substitute(MFC_MENUS=mfc_html, MARLI_MENUS=marli_html,
                MENSA_MENUS=mensa_html, BISTRO_MENUS=bistro_html,
                DATE_STRING=datetime.datetime.now().date().isoformat(),
                WEEK_NUMBER=utils.current_week())
            print(html)

    def day_to_html(self, day):
        html = ""
        for menu in day.menus:
            html += self.menu_to_html(menu)
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
    generator = StaticSiteGenerator()
    generator.scrape_all()