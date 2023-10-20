from datetime import datetime

from lxml import html as lx_html

import categories
from message_handler import MessageHandler


class TierMessageHandler(MessageHandler):
    def get_type(self):
        return categories.TRANSPORT

    def get_query_params(self):
        return {
            self.SUBJECT: "Your new invoice",
            self.SENDER: "tier.app",
        }

    def handle_html(self, html_str: str):
        self.purchase_date = self.date_of_curr_msg

        tree: lx_html.Element = lx_html.fromstring(html_str)
        self.amount = float(
            str(
                tree.xpath(
                    "//table[(((count(preceding-sibling::*) + 1) = 7)"
                    "and parent::*)]//p/text()"
                )[1]
            ).strip()[3:]
        )

        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)
