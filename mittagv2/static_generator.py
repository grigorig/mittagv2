import io
from html import escape
from datetime import date
import datetime
from string import Template
import requests
from mittagv2.marli_parser import MarliParser
from mittagv2.mensa_parser import MensaParser
from mittagv2.uksh_parser import BistroParser, MfcParser

class StaticSiteGenerator:
    """Generate a basic static site with current day's menu"""

    def __init__(self):
        pass
    
    def current_week(self):
        """Get current week number"""
        return date.today().isocalendar()[1]
    
    def current_day(self):
        """Return current day number, 0 = monday"""
        return date.today().isocalendar()[2] - 1

    def scrape_bistro(self, week_number=None):
        """Scrape UKSH bistro data"""
        if not week_number:
            week_number = self.current_week()
        pdf = requests.get("https://www.uksh.de/uksh_media/Speisepl%C3%A4ne/L%C3%BCbeck+_+UKSH_Bistro/Speiseplan+Bistro+KW+{}.pdf".format(week_number)).content
        menu = BistroParser(week_number, io.BytesIO(pdf)).parse()
        return menu

    def scrape_mfc(self, week_number=None):
        """Scrape MFC data"""
        if not week_number:
            week_number = self.current_week()
        pdf = requests.get("https://www.uksh.de/uksh_media/Speisepl%C3%A4ne/L%C3%BCbeck+_+MFC+Cafeteria/Speiseplan+Cafeteria+MFC+KW+{}.pdf".format(week_number)).content
        menu = MfcParser(week_number, io.BytesIO(pdf)).parse()
        return menu

    def scrape_mensa(self):
        """Scrape Mensa data"""
        week_number = self.current_week()
        html = requests.get("https://www.studentenwerk.sh/de/essen/standorte/luebeck/mensa-luebeck/speiseplan.html").content.decode("UTF-8")
        menu = MensaParser(week_number).parse(html)
        return menu
    
    def scrape_marli(self):
        """Scrape Marli data"""
        week_number = self.current_week()
        html = requests.get("https://www.marli.de/rs/gastronomie_und_begegnung/mittagsangebote/index.html").content.decode("UTF-8")
        menu = MarliParser(week_number).parse(html)
        return menu
    
    def scrape_all(self):
        """Scrape all current data"""
        day_number = self.current_day()
        bistro_menu = self.scrape_bistro()
        mfc_menu = self.scrape_mfc()
        marli_menu = self.scrape_marli()
        mensa_menu = self.scrape_mensa()
        bistro_html = self.day_to_html(bistro_menu.days[day_number])
        marli_html = self.day_to_html(marli_menu.days[day_number])
        mfc_html = self.day_to_html(mfc_menu.days[day_number])
        mensa_html = self.day_to_html(mensa_menu.days[day_number])
        with open("mittagv2/resources/static_template.html") as template_file:
            template = Template(template_file.read())
            html = template.substitute(MFC_MENUS=mfc_html, MARLI_MENUS=marli_html,
                MENSA_MENUS=mensa_html, BISTRO_MENUS=bistro_html,
                DATE_STRING=datetime.datetime.now().date().isoformat(),
                WEEK_NUMBER=self.current_week())
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