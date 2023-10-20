import re
from datetime import datetime

import pdfminer.high_level

import categories
from mail_api.abstract_mail_api import AbstractAttachment
from message_handler import MessageHandler
from utils import temporary_locale


class MoisesMessageHandler(MessageHandler):
    def get_type(self):
        return categories.COMPUTER_SOFTWARE

    def get_query_params(self):
        return {
            self.SUBJECT: "Your receipt from Moises Systems, Inc.",
            self.SENDER: "Moises Systems, Inc.",
        }

    def extract_txt(self, pdffile: str):
        text = pdfminer.high_level.extract_text(pdffile)
        purchase_date = re.findall(r"([A-Za-z]+ \d+, \d{4})", text)[0]
        with temporary_locale(
            "en_US"
        ):  # required for parsing the date with English month names
            self.purchase_date = datetime.strptime(purchase_date, "%B %d, %Y")
        self.amount = float(
            re.findall(r"Amount paid.*\$(\d+\.\d+)", text, re.DOTALL)[0]
        )
        self.my_currency = "USD"

    def handle_attachment(self, attachment: AbstractAttachment):
        if re.search(r"Invoice-", attachment.get_filename()):
            return True
        pdffile: str = self.save(attachment)
        self.filename = attachment.get_filename()
        self.extract_txt(pdffile)
