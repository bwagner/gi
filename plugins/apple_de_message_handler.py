import re
from datetime import datetime

import pdfminer.high_level

import categories
from mail_api.abstract_mail_api import AbstractAttachment
from message_handler import MessageHandler
from utils import temporary_locale


class AppleDeMessageHandler(MessageHandler):
    def get_type(self):
        return categories.COMPUTER_HARDWARE

    def get_query_params(self):
        return {
            self.SUBJECT: "Ihre Apple Rechnungsnummer",
            self.SENDER: "EMEA_Invoicing@email.apple.com",
        }

    def extract_txt(self, pdffile: str):
        with temporary_locale("en_US"):
            text: str = pdfminer.high_level.extract_text(pdffile)
            purchase_date: str = re.findall(r"Rechnungsdatum:\s+([\d.]+)", text)[0]
            self.purchase_date = datetime.strptime(purchase_date, "%d.%m.%Y")
            self.amount = max(
                float(x.replace(",", ".")) for x in re.findall(r"\d+,\d+", text)
            )

    def handle_attachment(self, attachment: AbstractAttachment):
        pdffile: str = self.save(attachment)
        self.filename = attachment.get_filename()
        self.extract_txt(pdffile)
