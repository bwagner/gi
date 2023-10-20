from datetime import datetime

from lxml import html as lx_html  # to avoid collision with html module

import categories
from message_handler import MessageHandler


class NamecheapHeresYourAutoRenewalMessageHandler(MessageHandler):
    def get_type(self):
        return categories.INTERNET

    def get_query_params(self):
        return {
            self.SUBJECT: "here's your auto-renewal notice",
            self.SENDER: "renewals@namecheap.com",
        }

    def handle_html(self, html_str: str):
        self.purchase_date = self.date_of_curr_msg

        tree: lx_html.Element = lx_html.fromstring(html_str)
        amount: str = tree.xpath(
            '//td[text() = "Your total renewal cost will be:"]'
            "/following-sibling::td/text()"
        )[0][1:]
        self.my_currency = "USD"
        self.amount = float(amount)

        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)
