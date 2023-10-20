import re
from datetime import datetime

import pdfminer.high_level

import categories
from mail_api.abstract_mail_api import AbstractAttachment
from message_handler import MessageHandler
from utils import temporary_locale


class BrackMessageHandler(MessageHandler):
    def get_type(self):
        return categories.COMPUTER_HARDWARE

    def get_query_params(self):
        return {
            self.SUBJECT: "Neue Rechnung von BRACK.CH",
            self.SENDER: "webshop@mailings.brack.ch",
        }

    def extract_txt(self, pdffile: str):
        with temporary_locale(
            "de_CH"
        ):  # required for parsing the date with German month names
            text = pdfminer.high_level.extract_text(pdffile)
            purchase_date = re.findall(r"Bestellreferenz\n\n(.*)\n", text)[0]
            self.purchase_date = datetime.strptime(purchase_date, "%d. %B %Y")
            self.amount = float(re.findall(r"Betrag\n([\d.]+)\n", text)[-1])

    def handle_attachment(self, attachment: AbstractAttachment):
        pdffile: str = self.save(attachment)
        self.filename = attachment.get_filename()
        self.extract_txt(pdffile)
