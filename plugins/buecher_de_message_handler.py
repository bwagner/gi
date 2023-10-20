import re
from datetime import datetime

import pdfminer.high_level

import categories
from mail_api.abstract_mail_api import AbstractAttachment
from message_handler import MessageHandler
from utils import temporary_locale


class BuecherDeMessageHandler(MessageHandler):
    def get_type(self):
        return categories.LITERATURE

    def get_query_params(self):
        return {
            self.SUBJECT: "bücher.de Rechnung",
            self.SENDER: "keine.Antwortadresse@rechnung.buecher.de",
        }

    def handle_html(self, html_str: str):
        amount = re.findall(r"Rechnungsendbetrag: EUR (.*?)</font>", html_str)[
            0
        ].replace(",", ".")
        self.my_currency = "EUR"
        self.amount = float(amount)

    def handle_attachment(self, attachment: AbstractAttachment):
        pdffile: str = self.save(attachment)
        self.filename = attachment.get_filename()
        self.extract_txt(pdffile)

    def extract_txt(self, pdffile: str):
        with temporary_locale("en_US"):
            text = pdfminer.high_level.extract_text(pdffile)
            date_str = re.search(
                r"Rechnungs-/Lieferdatum: (\d\d\.\d\d.\d{4})", text
            ).groups()[0]
            self.purchase_date = datetime.strptime(date_str, "%d.%m.%Y")
