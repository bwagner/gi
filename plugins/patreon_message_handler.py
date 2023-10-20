import re
from datetime import datetime

import dateparser

import categories
from message_handler import MessageHandler


class PatreonMessageHandler(MessageHandler):
    def get_type(self):
        return categories.EDUCATION

    def get_query_params(self):
        return {
            self.SUBJECT: "Your Patreon receipt is here!",
        }

    def handle_html(self, html_str: str):
        pd: str = re.search(r"Charge date: (.*)</p>", html_str).groups()[0]
        self.purchase_date = dateparser.parse(pd)

        amount: str = re.findall(r">\$([.\d]+)</span></td>", html_str)[0]
        self.my_currency = "USD"
        self.amount = float(amount)

        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)
