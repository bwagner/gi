import re
from datetime import datetime

import pdfminer.high_level
from lxml import etree

import categories
from mail_api.abstract_mail_api import AbstractAttachment
from message_handler import MessageHandler
from utils import get_tree, temporary_locale


class SbbEasyRideMessageHandler(MessageHandler):
    def get_type(self):
        return categories.TRANSPORT

    def get_query_params(self):
        return {
            self.SUBJECT: "EasyRide receipt",
        }

    def handle_html(self, html_str: str):
        if "You can find your detailed receipt attached to this email." in html_str:
            return True  # message from before 2023-08-30. Before then, the receipt
            # used to be in the attachment.
        tree: etree.ElementBase = get_tree(html_str)
        date_str: str = tree.xpath(
            "//body/table/tr/td/table[6]/tr/td[2]/table[2]/"
            "tr/td/table/tr/th[3]/table/tr[2]/td/span"
        )[0].text
        self.purchase_date = datetime.strptime(date_str, "%d.%m.%Y")
        amount_str: str = tree.xpath(
            "//body/table/tr/td/table[10]/tr/td[2]/table[2]/"
            "tr[2]/td/table/tr/th[5]/nobr"
        )[0].text
        self.my_currency, amount = amount_str.split()
        self.amount = float(amount)
        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)

    def extract_txt(self, pdffile: str):
        with temporary_locale("en_US"):
            text: str = pdfminer.high_level.extract_text(pdffile)

            # not working for EasyRide_2022-08-30_b7Rvu8hemOdDWAfBQA.pdf
            # (Date missing in title)
            # match = re.search("Payment receipt – (.*)", text)
            # self.purchase_date = datetime.strptime(match[1], "%d %b %Y")

            date_str: str = re.search(r"Invoicing date: (\d+ .* \d{4})", text)[1]
            self.purchase_date = datetime.strptime(date_str, "%d %b %Y")

            self.amount = max(float(x) for x in re.findall(r"CHF (\d+\.\d+)", text))

    def handle_attachment(self, attachment: AbstractAttachment):
        pdffile: str = self.save(attachment)
        self.filename = attachment.get_filename()
        self.extract_txt(pdffile)
