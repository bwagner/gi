import re
from datetime import datetime

import pdfminer.high_level

import categories
from mail_api.abstract_mail_api import AbstractAttachment
from message_handler import MessageHandler


class NzzMessageHandler(MessageHandler):
    def get_type(self):
        return categories.LITERATURE

    def get_query_params(self):
        return {
            self.SUBJECT: "Ihre Abo-Erneuerung",
            self.SENDER: "service@nzz.ch",
        }

    def extract_txt(self, pdffile: str):
        text: str = pdfminer.high_level.extract_text(pdffile)
        purchase_date: str = re.search(r"\b(\d\d\.\d\d.\d\d\d\d)\b", text)[1]
        self.purchase_date = datetime.strptime(purchase_date, "%d.%m.%Y")
        self.amount = float(re.findall(r"\b(\d\d\.00)\b", text)[-1])

    def handle_attachment(self, attachment: AbstractAttachment):
        """
        First, save the attachment to a file in order to extract text from it.
        Extracting text provides the purchase date and the amount.
        Then, rename the receipt to a conforming name, including the purchase date.
        This is necessary because the original filename provided by NZZ is not
        unique: "Ihre Abo-Rechnung.pdf".

        The default handling would be simply (see e.g. MusikhugMessageHandler):
            pdffile: str = self.save(attachment)
            self.filename = attachment.filename
            self.extract_txt(pdffile)

        TODO: both the default handling and this special handling should be
            moved to the superclass MessageHandler.
            The subclasses would simply indicate whether they have
            attachments at all and whether they need special handling
            (renaming receipt) or not.

        :param attachment:
        :return:
        """
        date_str: str = datetime.strftime(self.date_of_curr_msg, "%Y%m%d%H%M%S_%f")
        self.filename = f"NZZ{date_str}.pdf"  # temporary filename
        attachment.set_filename(self.filename)
        pdffile: str = self.save(attachment)
        self.extract_txt(pdffile)
        self.filename: str = datetime.strftime(
            self.purchase_date, f"{self.get_category_key()}_%Y%m%d_{self.uuid()}.pdf"
        )
        self.rename_receipt(pdffile, self.filename)
