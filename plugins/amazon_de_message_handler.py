import locale
import re
from datetime import datetime

from lxml import etree

import categories
from message_handler import MessageHandler
from utils import get_tree, temporary_locale


class AmazonDeMessageHandler(MessageHandler):
    def get_type(self):
        return categories.LITERATURE

    def get_query_params(self):
        return {
            self.SUBJECT: "Ihre Amazon.de Bestellung von",
            self.SENDER: "bestellbestaetigung@amazon.de",
        }

    def handle_html(self, html_str: str):
        tree: etree.ElementBase = get_tree(html_str)
        date_str = re.findall(
            r"\d+\. [A-Za-z]+ \d{4}",
            tree.xpath(
                "//body/table/tbody/tr/td/table/tbody/tr[4]/td/table/tbody/tr[2]/td/span"
            )[0].text,
        )[0]
        amount_str = tree.xpath(
            "//body/table/tbody/tr/td/table/tbody/tr[4]/td/table/tbody/tr[3]/"
            "td/table[2]/tbody/tr[4]/td[2]/strong"
        )[0].text
        self.my_currency, amount = amount_str.split()
        with temporary_locale("de_DE"):
            self.purchase_date = datetime.strptime(date_str, "%d. %B %Y")
            self.amount = locale.atof(amount)
        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)
