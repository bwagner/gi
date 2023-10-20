import re
from datetime import datetime

import categories
from message_handler import MessageHandler


class NewYorkJazzWorkshopMessageHandler(MessageHandler):
    def get_type(self):
        return categories.EDUCATION

    def get_query_params(self):
        return {
            self.SUBJECT: "Payment confirmation New York Jazz Workshop",
            self.SENDER: "quickbooks@notification.intuit.com",
        }

    def handle_html(self, html_str):
        self.my_currency = "USD"
        self.amount: float = float(re.search(r"You paid \$([\d.]+)", html_str)[1])
        date_str: str = re.search(r"on (\d\d/\d\d/\d{4})", html_str)[1]
        self.purchase_date = datetime.strptime(date_str, "%m/%d/%Y")

        date_str: str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.uuid()}")
        self.filename = f"{self.get_category_key()}_{date_str}.html"
        self.save_html(html_str, self.filename)
        # We should click on link "Manage payment"
        # on the opening page click on "View Invoice" or the Download button:
        # //*[@id="__next"]/div/div[1]/aside/div[1]/div/div[3]/div/div[2]/div[1]/svg
        # "View invoice":
        # //*[@id="__next"]/div/div[1]/aside/div[1]/div/div[3]/div/div[1]/button
