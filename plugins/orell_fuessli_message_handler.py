from datetime import datetime

from lxml import etree

import categories
from message_handler import MessageHandler
from utils import get_tree


class OrellFuessliMessageHandler(MessageHandler):
    def get_type(self):
        return categories.LITERATURE

    def get_query_params(self):
        return {
            self.SUBJECT: "Ihre OrellFüssli-Rechnung",
            self.SENDER: "kundenservice@orellfuessli.ch",
        }

    def handle_html(self, html_str: str):
        tree: etree.ElementBase = get_tree(html_str)
        el: etree.Element = tree.xpath("//body/table/tr/td/div/p[3]")[0]
        """
        ['anbei senden wir Ihnen als Anhang Ihre',
         'Rechnung-Nr. 0000000000 vom 00.00.0000.', <---
         'Kundennummer: 0000000000']
        """
        purchase_date: str = el.xpath(".//text()")[1].split()[-1]
        self.purchase_date = datetime.strptime(purchase_date, "%d.%m.%Y.")

        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)

        el: etree.Element = tree.xpath("//body/table/tr/td/div/p[4]")[0]
        # [' Zahlbetrag: 9,00 CHF']
        _, amount, self.my_currency = el.xpath(".//text()")[0].split()
        self.amount = float(amount.replace(",", "."))
