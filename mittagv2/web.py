import os
import re
import time
from string import Template
import argparse
from html import escape
import datetime
import mittagv2.utils as utils
import cherrypy
from cloudant import CouchDB


def no_index():
    """Tool to disable slash redirect for indexes"""
    cherrypy.request.is_index = False
cherrypy.tools.no_index = cherrypy.Tool('before_handler', no_index)

def restrict_methods(methods):
    """Tool for restricting to a certain set of allowed HTTP methods"""
    if not cherrypy.request.method in methods:
        raise cherrypy.HTTPError(405)
cherrypy.tools.restrict_methods = cherrypy.Tool('before_handler', restrict_methods)

class Root:
    def __init__(self):
        self._view_template = Template(open("mittagv2/resources/dynamic_template.html").read())
        self._db = utils.couch_connect()

    @cherrypy.expose()
    @cherrypy.tools.no_index()
    @cherrypy.tools.restrict_methods(methods = ["GET", "HEAD"])
    def index(self, day=None):
        cherrypy.response.headers["Content-Type"] = "text/html; charset=UTF-8"
        try:
            return self._get_all(day)
        except cherrypy.HTTPError as ex:
            raise ex
        except:
            raise cherrypy.HTTPError(500)

    def _get_menus(self):
        menus = self._db["mv2_menus"]
        all_menus = menus.get_view_result("_design/views", "byYearWeek", key=utils.current_year_week(), limit=4).all()
        marli_menu = None
        mfc_menu = None
        bistro_menu = None
        mensa_menu = None
        for m in all_menus:
            v = m["value"]
            if v["source_name"] == "marli-sb":
                marli_menu = v["menus"]
            if v["source_name"] == "uksh-cafeteria":
                mfc_menu = v["menus"]
            if v["source_name"] == "uksh-bistro":
                bistro_menu = v["menus"]
            if v["source_name"] == "swsh-mensa":
                mensa_menu = v["menus"]
        return bistro_menu, mfc_menu, marli_menu, mensa_menu

    def _get_all(self, day=None):
        """Get all current data"""
        if day:
            day_number = int(day)
        else:
            day_number = utils.current_day()
        if day_number < 0 or day_number > 6:
            raise cherrypy.HTTPError(400, "illegal day number")
        bistro_menu, mfc_menu, marli_menu, mensa_menu = self._get_menus()
        if bistro_menu and day_number < len(bistro_menu["days"]):
            bistro_html = self._day_to_html(bistro_menu["days"][day_number], bistro_menu)
        else:
            bistro_html = "<p>Keine Daten vorhanden!</p>"
        if marli_menu and day_number < len(bistro_menu["days"]):
            marli_html = self._day_to_html(marli_menu["days"][day_number], marli_menu)
        else:
            marli_html = "<p>Keine Daten vorhanden!</p>"
        if mfc_menu and day_number < len(bistro_menu["days"]):
            mfc_html = self._day_to_html(mfc_menu["days"][day_number], mfc_menu)
        else:
            mfc_html = "<p>Keine Daten vorhanden!</p>"
        if mensa_menu and day_number < len(bistro_menu["days"]):
            mensa_html = self._day_to_html(mensa_menu["days"][day_number], mensa_menu)
        else:
            mensa_html = "<p>Keine Daten vorhanden!</p>"
        calculated_day = datetime.datetime.now().date().day - utils.current_day() + day_number
        day_names = {
            0: "Montag",
            1: "Dienstag",
            2: "Mittwoch",
            3: "Donnerstag",
            4: "Freitag",
            5: "Samstag",
            6: "Sonntag"
        }
        date_string = "{}, {}".format(day_names[day_number],
            datetime.datetime.now().date().replace(day=calculated_day).isoformat())
        with open("mittagv2/resources/dynamic_template.html") as template_file:
            template = Template(template_file.read())
            html = template.substitute(MFC_MENUS=mfc_html, MARLI_MENUS=marli_html,
                MENSA_MENUS=mensa_html, BISTRO_MENUS=bistro_html,
                DATE_STRING=date_string,
                WEEK_NUMBER=utils.current_week())
            #print(html)
            return html

    def _day_to_html(self, day, week):
        html = ""
        for menu in day["menus"]:
            html += self._menu_to_html(menu)
        if "notice" in week:
            html += "<p>{}</p>".format(escape(week["notice"]).replace("\n", "<br>"))
        return html
    
    def _menu_to_html(self, menu):
        name = menu["name"]
        print(menu)
        if "menu_type" in menu and len(menu["menu_type"]) > 0:
            name = "{}: {}".format(menu["menu_type"], menu["name"])
        html = "<p><strong>{}</strong></p>".format(escape(name))
        if "description" in menu:
            html_description = escape(menu["description"]).replace("\n", "<br>")
            html += "<p>{}</p>".format(html_description)
        attributes = []
        if "calories" in menu:
            attributes.append("{:d} kcal".format(menu["calories"]))
        if "vegetarian" in menu and menu["vegetarian"] == True:
            attributes.append("vegetarisch")
        if len(attributes) > 0:
            html += """<p style="float: right; font-size: 90%; margin-top: 0;">"""
            html += ", ".join(attributes)
            html += "</p>"
        html += """<p style="float: left; margin-top: 0;">"""
        if "student_price" in menu and menu["student_price"]:
            html += "{:.2f} € / ".format(menu["student_price"]).replace(".", ",")
        if "reduced_price" in menu and menu["reduced_price"]:
            html += "{:.2f} € / ".format(menu["reduced_price"]).replace(".", ",")
        if "normal_price" in menu and menu["normal_price"]:
            html += "{:.2f} €".format(menu["normal_price"]).replace(".", ",")
        html += "</p>"
        html += """<div style="clear: both;"></div>"""
        return html

def start_web():
    """Start web server"""
    parser = argparse.ArgumentParser(description="mittagv2")
    parser.add_argument("--debug", "-d", action="store_true", help="debug mode")
    args = parser.parse_args()

    root = Root()

    global_config = {
        'server.socket_host': "0.0.0.0",
        'server.socket_port': 1234,
        'tools.proxy.on': True,
    }

    app_config = {
        '/': {
            'tools.staticdir.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd()) + "/mittagv2/resources/web_static/",
            'tools.staticdir.dir': './',
            'tools.staticdir.index': 'index.html',
        },
    }
    
    if args.debug == False:
        cherrypy.config.update(cherrypy.config.environments["production"])

    cherrypy.config.update(global_config)
    cherrypy.quickstart(root, '/', app_config)

if __name__ == "__main__":
    start_web()