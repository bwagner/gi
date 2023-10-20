import re
from datetime import datetime

import dateparser

import categories
from message_handler import MessageHandler


class KoboMessageHandler(MessageHandler):
    def get_type(self):
        return categories.LITERATURE

    def get_query_params(self):
        return {
            self.SUBJECT: "Your Kobo Order Receipt",
            self.SENDER: "noreply@kobo.com",
        }

    def handle_html(self, html_str: str):
        pd: str = re.findall(r"Your order was received on (.*?)<", html_str)[0]
        self.purchase_date = dateparser.parse(pd)

        amount = re.findall(r"Grand Total:\s+CHF (\d+\.\d+)", html_str)[0]
        self.amount = float(amount)

        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)
