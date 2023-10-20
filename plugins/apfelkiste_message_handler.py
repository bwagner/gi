from lxml import etree

import categories
from mail_api.abstract_mail_api import AbstractAttachment
from message_handler import MessageHandler
from utils import get_tree


class ApfelkisteMessageHandler(MessageHandler):
    def get_type(self):
        return categories.SUPPLIES

    def get_query_params(self):
        return {
            self.SUBJECT: '"Apfelkiste.ch: Rechnung Nr."',
            self.SENDER: "info@apfelkiste.ch",
        }

    def handle_html(self, html_str: str):
        tree: etree.ElementBase = get_tree(html_str)
        self.my_currency, amount = tree.xpath("//tr[7]/td[2]/span")[0].text.split()
        self.amount = float(amount)
        self.purchase_date = self.date_of_curr_msg

    def extract_txt(self, pdffile: str):
        """
        We don't need to extract anything from the attachment, since we're getting
        the info from html.
        :param pdffile:
        """
        pass

    def handle_attachment(self, attachment: AbstractAttachment):
        pdffile: str = self.save(attachment)
        self.filename = attachment.get_filename()
        self.extract_txt(pdffile)
