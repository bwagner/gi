import re
from datetime import datetime

import pdfminer.high_level

import categories
from mail_api.abstract_mail_api import AbstractAttachment
from message_handler import MessageHandler
from utils import temporary_locale


class MusicStoreMessageHandler(MessageHandler):
    def get_type(self):
        return categories.COMPUTER_HARDWARE

    def get_query_params(self):
        return {
            self.SUBJECT: "MUSICSTORE Your Music Store sales invoice",
            self.SENDER: "export@musicstore.com",
        }

    def extract_txt(self, pdffile: str):
        with temporary_locale("en_US"):
            text: str = pdfminer.high_level.extract_text(pdffile)
            purchase_date: str = re.search(r"\b(\d\d\.\d\d.\d\d\d\d)\b", text)[0]
            self.purchase_date = datetime.strptime(purchase_date, "%d.%m.%Y")
            self.amount = float(
                re.search(r"Total CHF inkl. MwSt\D+(\d+,\d+)", text)[1].replace(
                    ",", "."
                )
            )

    def handle_attachment(self, attachment: AbstractAttachment):
        if re.search(r"Return-Form", attachment.get_filename()):
            return True
        pdffile: str = self.save(attachment)
        self.filename = attachment.get_filename()
        self.extract_txt(pdffile)
