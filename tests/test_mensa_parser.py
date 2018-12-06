import pprint as pp
import unittest
import mittagv2.mensa_parser
import mittagv2.model as model

class TestMensaParser(unittest.TestCase):

    def test_parse_html(self):
        with open("tests/resources/Studentenwerk SH.html", "rb") as html:
            parser = mittagv2.mensa_parser.MensaParser(1)
            res = parser.parse(html.read().decode("UTF-8"))
            #pp.pprint(res)
            self.assertEqual(len(res.days[0].menus), 5)
            self.assertEqual(len(res.days[1].menus), 4)
            self.assertEqual(res.days[3].menus[0].vegetarian, True)
            self.assertEqual(res.days[0].menus[0].vegetarian, False)
            self.assertEqual(res.days[0].menus[4].vegetarian, True)
            self.assertAlmostEqual(res.days[0].menus[0].normal_price, 4.30)
            self.assertAlmostEqual(res.days[0].menus[0].student_price, 2.25)
            self.assertAlmostEqual(res.days[0].menus[0].reduced_price, 3.45)
            self.assertEqual(res.days[0].menus[0].name, "Kaiserschmarrn")
            self.assertEqual(res.days[0].menus[1].name, "Putengeschnetzeltes Thailändischer Art")
