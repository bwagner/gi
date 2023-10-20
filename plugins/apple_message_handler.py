import re
from datetime import datetime

from lxml import etree

import categories
from message_handler import MessageHandler
from utils import get_tree


class AppleMessageHandler(MessageHandler):
    def get_type(self):
        return categories.COMPUTER_SOFTWARE

    def get_query_params(self):
        return {
            self.SUBJECT: "Your invoice from Apple.",
            self.SENDER: "no_reply@email.apple.com",
        }

    def handle_html(self, html_str: str):
        # TODO: handle_html should be pulled up to the parent,
        #       providing only hooks for getting purchase date and amount.
        #       Rest should be handled by parent class.
        tree: etree.ElementBase = get_tree(html_str)
        el: etree.Element = tree.xpath("//td[@width='90' and @align='right']")[0]
        amount: float = float(re.search(r"CHF.([\d.]+)", el.text).groups()[0])
        el: etree.Element = tree.xpath("//span[contains(., 'INVOICE DATE')]")[0]
        td: etree.Element = el.getparent()
        it: etree.ElementTextIterator = td.itertext()
        next(it)
        date_str: str = next(it)
        self.purchase_date = datetime.strptime(date_str, "%d %b %Y")

        # TODO: Saving html could be handled by parent, too: Name is
        #   prefix of this class "Apple", underscore, date, and uuid to make
        #   the name unique.
        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)

        self.amount = amount
