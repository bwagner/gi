import re
from datetime import datetime

import dateparser

import categories
from message_handler import MessageHandler


class PragProgMessageHandler(MessageHandler):
    def get_type(self):
        return categories.LITERATURE

    def get_query_params(self):
        return {
            self.SUBJECT: "Invoice/Receipt for order",
            self.SENDER: "Pragmatic Bookshelf Downloads <noreply@sendowl.com>",
        }

    def handle_plain(self, plain_body: str):
        pd: str = re.search(r"Date:\s*(\d{4}\-\d\d-\d\d)", plain_body)[1]
        self.purchase_date = dateparser.parse(pd)

        self.my_currency, amount = re.search(
            r"Total:\s*([^\d]+)(\d+\.\d+)", plain_body
        ).groups()
        self.amount = float(amount)

        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.txt"
        self.save_html(plain_body, self.filename)
