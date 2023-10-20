import re
from datetime import datetime

from lxml import etree

import categories
from message_handler import MessageHandler
from utils import get_tree


class SbbOnlinePurchaseMessageHandler(MessageHandler):
    def get_type(self):
        return categories.TRANSPORT

    def get_query_params(self):
        return {
            self.SUBJECT: "Your online purchase from SBB",
        }

    def handle_html(self, html_str: str):
        tree: etree.ElementBase = get_tree(html_str)
        date_str = tree.xpath(
            "//body/table/tr/td/table[6]/tr/td[2]/table/tr/th[5]/table/tr[3]/td"
        )[0].text
        self.purchase_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
        if not re.match(
            r"CHF \d+\.\d+",
            amount_str := tree.xpath(
                # purchase from 24.09.2023
                "//body/table/tr/td/table[6]/tr/td[2]/table/tr/th[3]/table/tr[11]/td"
            )[0].text,
        ):
            # purchase from 14.10.2023. Only difference in xpath: 11 became 12
            amount_str = tree.xpath(
                "//body/table/tr/td/table[6]/tr/td[2]/table/tr/th[3]/table/tr[12]/td"
            )[0].text
        self.my_currency, amount = amount_str.split()
        self.amount = float(amount)
        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)
