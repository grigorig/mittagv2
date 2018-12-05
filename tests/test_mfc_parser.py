import pprint as pp
import unittest
import mittagv2.mfc_parser
import mittagv2.model as model

class TestMfcParser(unittest.TestCase):

    def test_parse_pdf(self):
        fp = open("tests/resources/Speiseplan Cafeteria MFC KW 49.pdf", "rb")
        parser = mittagv2.mfc_parser.MfcParser(1, fp)
        res = parser.parse()
        #pp.pprint(res)
        self.assertEqual(model.find_menu_by_type(res.days[0], "Menü 1")[0].name, "Kohlroulade")
        self.assertEqual(model.find_menu_by_type(res.days[4], "Menü 1")[0].name, "Schnitzel vom Schwein")
        self.assertEqual(model.find_menu_by_type(res.days[4], "Menü 1")[0].description[0:12], "in Kartoffel")
        self.assertEqual(model.find_menu_by_type(res.days[3], "Menü 2")[0].description[0:13], "mit Foccacina")
        self.assertAlmostEqual(model.find_menu_by_type(res.days[1], "Menü 2")[0].reduced_price, 3.25)
        self.assertAlmostEqual(model.find_menu_by_type(res.days[1], "Menü 2")[0].normal_price, 4.06)
        self.assertAlmostEqual(model.find_menu_by_type(res.days[1], "Zusatzgericht")[0].normal_price, 5.25)
