import re
from datetime import datetime

from lxml import html as lx_html

import categories
from message_handler import MessageHandler


class BirdRidesMessageHandler(MessageHandler):
    def get_type(self):
        return categories.TRANSPORT

    def get_query_params(self):
        return {
            self.SUBJECT: "Your Bird Ride Receipt",
            # self.SENDER: "",
        }

    def handle_html(self, html_str: str):
        self.purchase_date = self.date_of_curr_msg

        tree: lx_html.HtmlElement = lx_html.fromstring(html_str)
        self.amount = max(
            float(re.match(r"CHF\s*([0-9.]+)", x)[1])
            for x in tree.xpath(".//span[starts-with(text(), 'CHF')]/text()")
        )

        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)
