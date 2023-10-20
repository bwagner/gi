import html
import re
from datetime import datetime

import pdfminer.high_level
import requests
from requests import Response

import categories
from message_handler import MessageHandler
from utils import cd, temporary_locale


class BoltMessageHandler(MessageHandler):
    def get_type(self):
        return categories.TRANSPORT

    def get_query_params(self):
        return {
            self.SUBJECT: "Your Bolt Scooter ride",
        }

    def handle_html(self, html_str: str):
        """neither
        root = etree.fromstring(html_str)
        tree = etree.ElementTree(root)
        (https://bugs.launchpad.net/lxml/+bug/1902364)

        nor

        root = etree.HTML(html_str)
        tree = etree.ElementTree(root)
        (https://bugs.launchpad.net/lxml/+bug/1854057)

        worked. Falling back to regex.
        """
        purchase_date: str = re.search(r"\d{4}-\d\d-\d\d", html_str)[0]
        self.purchase_date = datetime.strptime(purchase_date, "%Y-%m-%d")
        url: str = re.search(
            r"(https://doclink.live.boltsvc.net/invoice/pdf[^\"]+)", html_str
        )[0]
        url: str = html.unescape(url)
        response: Response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Could not download {url}")
        self.filename = (
            f"{self.get_category_key()}_{self.purchase_date.strftime('%Y%m%d')}_"
            f"{datetime.now().strftime('%H%M%S')}.pdf"
        )
        with cd(self.receipts_dir), open(self.filename, "wb") as f:
            f.write(response.content)
            self.extract_txt(self.filename)

    def extract_txt(self, pdffile: str):
        with temporary_locale("en_US"):
            text = pdfminer.high_level.extract_text(pdffile)
            purchase_date = re.findall(r"\n\nDate: (\d{4}-\d\d-\d\d)\n\n", text)[0]
            self.purchase_date = datetime.strptime(purchase_date, "%Y-%m-%d")
            self.amount = float(list(re.findall(r"\s\d+\.\d+\s", text))[-1])
