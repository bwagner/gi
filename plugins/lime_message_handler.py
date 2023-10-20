from datetime import datetime, timedelta
from typing import List

import dateparser
from lxml import etree

import categories
from message_handler import MessageHandler
from utils import get_tree


class LimeMessageHandler(MessageHandler):
    def __init__(self):
        super().__init__()
        self.times = None
        self.distance = None

    def get_type(self):
        return categories.TRANSPORT

    def get_query_params(self):
        return {
            self.SUBJECT: "Receipt for your Lime ride",
            self.SENDER: "no-reply@li.me",
        }

    def handle_html(self, html_str: str):
        tree: etree.ElementBase = get_tree(html_str)

        (date_str, dist_str, time_str) = [
            x.text
            for i, x in enumerate(tree.xpath("//table/tr/td/table/tr/td/div/span/span"))
            if i in [0, 2, 4]
        ]
        self.purchase_date = dateparser.parse(date_str.replace("Date of Issue: ", ""))
        self.distance = float(dist_str.replace("km distance", ""))
        times: List[datetime] = [
            self.purchase_date.replace(hour=x.hour, minute=x.minute)
            for x in [datetime.strptime(x, "%I:%M %p") for x in time_str.split(" - ")]
        ]
        if times[0] > times[1]:
            times[1] += timedelta(days=1)
        self.times = times

        amount_xpath: str = (
            "//body/center/div/table/tr/td/table/tr/td/table/tr/td/"
            "table/tr/td/table/tr/td/table/tr/td/table/tr/td/div/span"
        )
        self.amount = float([x.text for x in tree.xpath(amount_xpath)][1][3:])

        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)
