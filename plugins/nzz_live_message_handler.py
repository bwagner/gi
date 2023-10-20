import re
from datetime import datetime

import dateparser

import categories
from message_handler import MessageHandler


class NzzLiveMessageHandler(MessageHandler):
    def __init__(self):
        super().__init__()

    def get_type(self):
        return categories.EDUCATION

    def get_query_params(self):
        return {
            self.SUBJECT: "Zahlungseingang für Ticketbuchung",
            self.SENDER: "NZZ Live <support@ticketpark.ch>",
        }

    def handle_html(self, html_str: str):
        """
        Not working:
        root = etree.HTML(html_str)
        tree = etree.ElementTree(root)
        self.purchase_date = dateparser.parse(
            tree.xpath('/html/body/table/table/tr/td[2]/table[4]/tr/td/table/tr[3]/td[2]')[0].text
        )
        resorting to regex:
        """
        self.my_currency, amount = re.findall(r"([A-Z]{3}) (\d+\.\d+\b)", html_str)[0]
        self.amount = float(amount)
        self.purchase_date = dateparser.parse(
            re.findall(r"(\d\d\. [JFMASOND][a-z]+ \d{4})", html_str)[0]
        )
        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)
