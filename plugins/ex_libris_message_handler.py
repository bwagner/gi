"""
# Didn't get it to work. All pages linked from the html seem to have dynamic content
# that is displayed in the browser but absent in the files retrieved via requests.

class ExLibrisMessageHandler(MessageHandler):

    def get_type(self):
        return categories.LITERATURE

    def get_query_params(self):
        return {
            self.SUBJECT: "Ihr Rechnungsbeleg",
            self.SENDER: "noreply@exlibris.ch",
        }

    def handle_html(self, html_str: str):
        # this is html_str from the mail!
        # we need to extract the invoice_html via href "Rechnung anzeigen"
        tree = lx_html.fromstring(html_str)
        invoice_link = tree.xpath('//a[contains(., "Rechnung")]')[0].attrib["href"]

        username = keyring.get_password("exlibris_user")
        password = keyring.get_password("exlibris_pw", username)

        payload = {
            "inUserName": username,
            "inUserPass": password,
        }
        with requests.Session() as s:
            p = s.post(invoice_link, data=payload)
            invoice_html_str = p.text
            itree = lx_html.fromstring(invoice_html_str)
            el = itree.xpath(
                '//a[contains(., "Rechnung")]'
            )[0]
            pdf_url = el.attrib["href"]
            # missing: download pdf
            # (optional, since we have all info in the invoice_html)

        purchase_date = tree.xpath('//p[contains(., "Rechnungsdatum")]')[0].text.split()[1]
        self.purchase_date = datetime.strptime(purchase_date, "%d.%m.%Y")
        self.amount = float(tree.xpath('//p[contains(., "Betrag")]')[0].text.split()[2])

        date_str = datetime.strftime(self.purchase_date, f"%Y%m%d_{self.next_int()}")
        self.filename = f"ExLibris_{date_str}.html"
        self.save_html(html_str, self.filename)
"""
