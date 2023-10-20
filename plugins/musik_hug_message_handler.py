import re
from datetime import datetime

import pdfminer.high_level

import categories
from mail_api.abstract_mail_api import AbstractAttachment
from message_handler import MessageHandler
from utils import temporary_locale


class MusikHugMessageHandler(MessageHandler):
    def get_type(self):
        return categories.SUPPLIES

    def get_query_params(self):
        return {
            self.SUBJECT: "Ihre Bestellung wurde versandt",
            self.SENDER: "musikhug.ch",
        }

    def extract_txt(self, pdffile: str):
        with temporary_locale("de_CH"):
            text: str = pdfminer.high_level.extract_text(pdffile)
            purchase_date: str = re.search(
                r"\b(\d+\. (?:Januar|Februar|März|April|Mai|Juni|Juli|"
                r"August|September|Oktober|November|Dezember).\d\d\d\d)\b",
                text,
            )[1]
            self.purchase_date = datetime.strptime(purchase_date, "%d. %B %Y")
            self.amount = float(re.findall(r"\b(\d+\.\d+)\b", text)[-1])

    def handle_attachment(self, attachment: AbstractAttachment):
        pdffile: str = self.save(attachment)
        self.filename = attachment.get_filename()
        self.extract_txt(pdffile)
