import pprint as pp
import unittest
import mittagv2.marli_parser
import mittagv2.model as model

class TestMarliParser(unittest.TestCase):

    def test_parse_html(self):
        with open("tests/resources/marli.html", "rb") as html:
            parser = mittagv2.marli_parser.MarliParser(1)
            res = parser.parse(html.read().decode("UTF-8"))
            pp.pprint(res)
            self.assertEqual(len(res.days[0].menus), 1)
            self.assertEqual(model.find_menu_by_type(res.days[0], "")[0].name, "Geräuchertet Putenbrust")
            self.assertEqual(model.find_menu_by_type(res.days[4], "")[0].name, "Kartoffelsuppe")
            self.assertEqual(model.find_menu_by_type(res.days[4], "")[0].description[0:25], "Kartoffelsuppe mit\nWiener")
