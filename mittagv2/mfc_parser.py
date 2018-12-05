import re
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

class MfcParser:
    """Parser for MFC Cafeteria PDFs with nutrition information"""

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
        self.model = model.WeeklyMenu(week_number, days)
    
    def parse(self):
        """Parse and fill model data"""
        resource_manager = pdfminer.pdfinterp.PDFResourceManager()
        params = pdfminer.layout.LAParams()
        pdf_device = pdfminer.converter.PDFPageAggregator(resource_manager, laparams=params)
        pdf_interpreter = pdfminer.pdfinterp.PDFPageInterpreter(resource_manager, pdf_device)
        for page in pdfminer.pdfpage.PDFPage.get_pages(self.fp):
            pdf_interpreter.process_page(page)
            layout = pdf_device.get_result()
            for element in layout:
                # no text
                if not isinstance(element, pdfminer.layout.LTTextBoxHorizontal):
                    continue
                # outside of table
                if element.x0 < 130.88 or element.x1 > 718.24 or element.y0 < 127.64 or element.y1 > 449.56:
                    continue
                # Menu 1
                if element.x1 < 329.03:
                    self.collect_type("Menü 1", element)
                # Menu 2
                elif element.x1 < 524.05:
                    self.collect_type("Menü 2", element)
                # Zusatzgericht
                else:
                    self.collect_type("Zusatzgericht", element)
        self.clean_model()
        return self.model

    def clean_model(self):
        """Apply various cleanups to gathered data"""
        for day in self.model.days:
            for menu in day.menus:
                menu.description = menu.description.strip()

    def collect_type(self, menu_type, element):
        """Collect element by menu type"""
        if element.y1 < 127.64:
            self.collect_day(5, menu_type, element)
        elif element.y1 < 192.71:
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
                student_price=-1.0, reduced_price=-1.0, normal_price=-1.0)
            day.menus.append(menu)

    def parse_textline(self, menu, text):
        """Parse a line of description text"""
        price_match = re.search(r"""€\s*([0-9,]+)\s*/\s*€\s*([0-9,]+)""", text)
        if price_match:
            menu.reduced_price = float(price_match.group(1).replace(",", "."))
            menu.student_price = menu.reduced_price
            menu.normal_price = float(price_match.group(2).replace(",", "."))
        else:
            menu.description += text.strip() + "\n"