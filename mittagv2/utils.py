#
# Copyright 2019 Grigori Goronzy <greg@kinoho.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import os
from datetime import date, datetime
from cloudant import CouchDB

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

def couch_connect(user=None, auth=None, url=None):
    if not user:
        user = os.getenv("COUCHDB_USER", "admin")
    if not auth:
        auth = os.getenv("COUCHDB_PASSWORD", "admin")
    if not url:
        url = os.getenv("COUCHDB_URL", "http://127.0.0.1:5984")
    return CouchDB(user, auth, url=url, connect=True)

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