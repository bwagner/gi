from datetime import datetime

from lxml import etree

import categories
from message_handler import MessageHandler
from utils import get_tree


class MicasaMessageHandler(MessageHandler):
    def get_type(self):
        return categories.SUPPLIES

    def get_query_params(self):
        return {
            self.SUBJECT: "Bestellbestätigung für Bestellung",
            self.SENDER: "migros.service@mgb.ch",
        }

    def handle_html(self, html_str: str):
        tree: etree.ElementBase = get_tree(html_str)
        self.my_currency, amount = (
            tree.xpath("//tr[6]/td/table/tr/td[3]")[0].text.strip().split()
        )
        self.amount = float(amount)
        self.purchase_date = self.date_of_curr_msg

        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)
