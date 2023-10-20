import re
from datetime import datetime

import categories
from message_handler import MessageHandler


class LehmannsMessageHandler(MessageHandler):
    def get_type(self):
        return categories.LITERATURE

    def get_query_params(self):
        return {
            self.SUBJECT: "Rechnung.*Lehmanns Media GmbH",
            self.SENDER: "info@lehmanns.de",
        }

    def handle_html(self, html_str: str):
        purchase_date, amount = re.findall(
            r"Ihre Lehmanns-Bestellung vom (\d\d\.\d\d\.\d\d\d\d) "
            r"wurde.*Rechnungsendbetrag: (\d+\.\d+) EUR",
            html_str,
        )[0]
        self.purchase_date = datetime.strptime(purchase_date, "%d.%m.%Y")

        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)

        self.my_currency = "EUR"
        self.amount = float(amount)
