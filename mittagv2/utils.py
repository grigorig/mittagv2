from datetime import date, datetime


def current_year():
    """Get current year (local timezone)"""
    return date.today().isocalendar()[0]

def current_week():
    """Get current week number (local timezone)"""
    return date.today().isocalendar()[1]

def current_year_week():
    """Get current year+week identification"""
    return "{:4d}-{:2d}".format(current_year(), current_week())

def current_day():
    """Return current week day number, 0 = monday (local timezone)"""
    return date.today().isocalendar()[2] - 1

def timestamp_rfc3339():
    """Generate RC3339 compliant UTC timestamp"""
    return datetime.utcnow().isoformat("T") + "Z"

def create_couch_views(db):
    design_doc = {
        "_id": "_design/views",
        "views": {
            "byYearWeek": {
                "map": "function (doc) {\n  if (doc.type === \"weekly_menu\" && doc.menus.year_week)\n    emit(doc.menus.year_week, doc);\n}"
            },
            "bySourceNameYearWeek": {
                "map": "function (doc) {\n  if (doc.type === \"weekly_menu\" && doc.source_name && doc.menus.year_week)\n    emit(doc.source_name+\"/\"+doc.menus.year_week, doc);\n}"
            }
        },
        "language": "javascript"
    }
    db.create_document(design_doc)