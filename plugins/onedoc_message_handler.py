import re
from datetime import datetime

import pdfminer.high_level

import categories
from mail_api.abstract_mail_api import AbstractAttachment
from message_handler import MessageHandler


class OneDocMessageHandler(MessageHandler):
    def get_type(self):
        return categories.HEALTH

    def get_query_params(self):
        return {
            self.SUBJECT: "Invoice - Treatment(s) with",
            self.SENDER: "OneDoc <no-reply@onedoc.ch>",
        }

    def extract_txt(self, pdffile: str):
        text: str = pdfminer.high_level.extract_text(pdffile)
        purchase_date: str = re.findall(r", the (\d\d\.\d\d\.\d{4})", text)[0]
        self.purchase_date = datetime.strptime(purchase_date, "%d.%m.%Y")
        self.my_currency, amount = re.findall(r"\b([A-Z]{3}) (\d+\.\d+)\b", text)[0]
        self.amount = float(amount)

    def handle_attachment(self, attachment: AbstractAttachment):
        if re.search(r"Insurer Copy", attachment.get_filename()):
            return True
        pdffile: str = self.save(attachment)
        self.filename = attachment.get_filename()
        self.extract_txt(pdffile)
