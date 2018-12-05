import pprint as pp
import unittest
import mittagv2.uksh_parser
import mittagv2.model as model

class TestUkshParser(unittest.TestCase):

    def test_parse_pdf_mfc(self):
        fp = open("tests/resources/Speiseplan Cafeteria MFC KW 49.pdf", "rb")
        parser = mittagv2.uksh_parser.MfcParser(1, fp)
        res = parser.parse()
        #pp.pprint(res)
        self.assertEqual(len(res.days[0].menus), 3)
        self.assertEqual(len(res.days[3].menus), 2)
        self.assertEqual(model.find_menu_by_type(res.days[0], "Menü 1")[0].name, "Kohlroulade")
        self.assertEqual(model.find_menu_by_type(res.days[4], "Menü 1")[0].name, "Schnitzel vom Schwein")
        self.assertEqual(model.find_menu_by_type(res.days[4], "Menü 1")[0].description[0:12], "in Kartoffel")
        self.assertEqual(model.find_menu_by_type(res.days[3], "Menü 2")[0].description[0:13], "mit Foccacina")
        self.assertAlmostEqual(model.find_menu_by_type(res.days[1], "Menü 2")[0].reduced_price, 3.25)
        self.assertAlmostEqual(model.find_menu_by_type(res.days[1], "Menü 2")[0].normal_price, 4.06)
        self.assertAlmostEqual(model.find_menu_by_type(res.days[1], "Zusatzgericht")[0].normal_price, 5.25)

    def test_parse_pdf_uksh(self):
        fp = open("tests/resources/Speiseplan Bistro KW 50.pdf", "rb")
        parser = mittagv2.uksh_parser.BistroParser(1, fp)
        res = parser.parse()
        #pp.pprint(res)
        self.assertEqual(len(res.days[0].menus), 4)
        self.assertEqual(len(res.days[3].menus), 3)
        self.assertEqual(model.find_menu_by_type(res.days[0], "Wok Station")[0].name, "Farfalle mit Gemüsestreifen")
        self.assertEqual(model.find_menu_by_type(res.days[4], "Vegetarisch")[0].name, "Kaiserschmarrn")
        self.assertEqual(model.find_menu_by_type(res.days[4], "Gericht II")[0].description[0:10], "Rahmgemüse")
        self.assertEqual(model.find_menu_by_type(res.days[3], "Gericht III")[0].description[0:21], "mit Schupfnudelpfanne")
        self.assertAlmostEqual(model.find_menu_by_type(res.days[1], "Wok Station")[0].reduced_price, 4.20)
        self.assertAlmostEqual(model.find_menu_by_type(res.days[1], "Vegetarisch")[0].normal_price, 4.06)
        self.assertAlmostEqual(model.find_menu_by_type(res.days[1], "Gericht III")[0].normal_price, 5.50)