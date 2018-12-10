import re
from abc import ABC, abstractmethod
import pdfminer.settings
pdfminer.settings.STRICT = False
import pdfminer.high_level
import pdfminer.layout
import pdfminer.pdfparser
import pdfminer.pdfdocument
import pdfminer.pdfinterp
import pdfminer.pdfdevice
import pdfminer.pdfpage
import pdfminer.converter
import mittagv2.model as model

class PdfTableParser(ABC):
    """Base class for UKSH table PDFs"""

    def __init__(self, week_number, fp):
        """Instantiate parser with given file-like object"""
        self.fp = fp
        days = [
            model.DailyMenu(0, []),
            model.DailyMenu(1, []),
            model.DailyMenu(2, []),
            model.DailyMenu(3, []),
            model.DailyMenu(4, []),
        ]
        self.model = model.WeeklyMenu(week_number, days, None)

    def parse_textline(self, menu, text):
        """Parse a line of description text"""
        price_match = re.search(r"""€\s*([0-9,]+)\s*/\s*€\s*([0-9,]+)""", text)
        kcal_match = re.search(r"""kcal\s*([0-9]+)""", text)
        if price_match:
            menu.reduced_price = float(price_match.group(1).replace(",", "."))
            menu.normal_price = float(price_match.group(2).replace(",", "."))
        elif kcal_match:
            menu.calories = int(kcal_match.group(1))
        else:
            menu.description += text.strip() + "\n"

    def parse(self):
        """Parse and fill model data"""
        resource_manager = pdfminer.pdfinterp.PDFResourceManager()
        params = pdfminer.layout.LAParams()
        params.char_margin = 0.5
        params.line_margin = 0.25
        pdf_device = pdfminer.converter.PDFPageAggregator(resource_manager, laparams=params)
        pdf_interpreter = pdfminer.pdfinterp.PDFPageInterpreter(resource_manager, pdf_device)
        for page in pdfminer.pdfpage.PDFPage.get_pages(self.fp):
            pdf_interpreter.process_page(page)
            layout = pdf_device.get_result()
            for element in layout:
                if not isinstance(element, pdfminer.layout.LTTextBoxHorizontal):
                    continue
                self.collect_base(element)
        self.clean_model()
        return self.model
    
    @abstractmethod
    def collect_base(self, element):
        """Collect element into model"""
        pass

    def clean_model(self):
        """Apply various cleanups to gathered data"""
        for day in self.model.days:
            for menu in day.menus:
                menu.description = menu.description.strip()

class MfcParser(PdfTableParser):
    """Parser for MFC Cafeteria PDFs with nutrition information"""

    def __init__(self, week_number, fp):
        PdfTableParser.__init__(self, week_number, fp)

    def collect_base(self, element):
        """Collect elements into model"""
        # outside of table
        if element.x0 < 122.88 or element.x1 > 773.09 or element.y0 < 127.64 or element.y1 > 449.56:
            return
        # Menu 1
        if element.x1 < 329.03:
            self.collect_type("Menü 1", element)
        # Menu 2
        elif element.x1 < 524.05:
            self.collect_type("Menü 2", element)
        # Zusatzgericht
        else:
            self.collect_type("Zusatzgericht", element)

    def collect_type(self, menu_type, element):
        """Collect element by menu type"""
        if element.y1 < 192.71:
            self.collect_day(4, menu_type, element)
        elif element.y1 < 256.91:
            self.collect_day(3, menu_type, element)
        elif element.y1 < 321.13:
            self.collect_day(2, menu_type, element)
        elif element.y1 < 385.36:
            self.collect_day(1, menu_type, element)
        else:
            self.collect_day(0, menu_type, element)
    
    def collect_day(self, day_number, menu_type, element):
        """Collect element by day"""
        day = self.model.days[day_number]
        try:
            menus = model.find_menu_by_type(day, menu_type)
            if len(menus) > 1:
                raise ValueError("duplicate menu_type")
            self.parse_textline(menus[0], element.get_text())
        except NameError:
            menu = model.Menu(menu_type=menu_type,
                name=element.get_text().strip(), description="",
                student_price=None, reduced_price=None, normal_price=None,
                calories=0, vegetarian=None)
            day.menus.append(menu)


class BistroParser(PdfTableParser):
    """Parser for UKSH Bistro PDFs with nutrition information"""

    def __init__(self, week_number, fp):
        PdfTableParser.__init__(self, week_number, fp)

    def collect_base(self, element):
        """Collect elements into model"""
        # outside of table
        if element.x0 < 122.88 or element.x1 > 773.09 or element.y0 < 92.957 or element.y1 > 497.83:
            return
        # Wok Station
        if element.x1 < 284.85:
            self.collect_type("Wok Station", False, element)
        # Vegetarisch
        elif element.x0 > 284.85 and element.x1 < 447.0:
            self.collect_type("Vegetarisch", True, element)
        # Gericht II
        elif element.x0 > 447.0 and element.x1 < 609.15:
            self.collect_type("Gericht II", False, element)
        # Gericht III
        elif element.x0 > 609.15:
            self.collect_type("Gericht III", False, element)

    def collect_type(self, menu_type, vegetarian, element):
        """Collect element by menu type"""
        if element.y1 < 150.79:
            # sunday, ignored
            pass
        elif element.y1 < 208.64:
            # saturday, ignored
            pass
        elif element.y1 < 266.47:
            self.collect_day(4, menu_type, vegetarian, element)
        elif element.y1 < 324.32:
            self.collect_day(3, menu_type, vegetarian, element)
        elif element.y1 < 382.15:
            self.collect_day(2, menu_type, vegetarian, element)
        elif element.y1 < 440.0:
            self.collect_day(1, menu_type, vegetarian, element)
        else:
            self.collect_day(0, menu_type, vegetarian, element)
    
    def collect_day(self, day_number, menu_type, vegetarian, element):
        """Collect element by day"""
        day = self.model.days[day_number]
        try:
            menus = model.find_menu_by_type(day, menu_type)
            if len(menus) > 1:
                raise ValueError("duplicate menu_type")
            self.parse_textline(menus[0], element.get_text())
        except NameError:
            menu = model.Menu(menu_type=menu_type,
                name=element.get_text().strip(), description="",
                student_price=None, reduced_price=None, normal_price=None,
                calories=0, vegetarian=vegetarian)
            day.menus.append(menu)
