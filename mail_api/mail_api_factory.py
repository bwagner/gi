from typing import Dict

from mail_api.abstract_mail_api import AbstractMailAPI
from mail_api.eml_mail_api import EMLMailAPI
from mail_api.simplegmail_mail_api import SimpleGmailAdapter

PACKAGE_KEY = "package"


class MailApiFactory:
    def __init__(self, config: Dict[str, str]):
        self.config: Dict[str, str] = config

    def create(self) -> AbstractMailAPI:
        package = self.config[PACKAGE_KEY]
        if package == "simplegmail_mail_api":
            return SimpleGmailAdapter(self.config)
        elif package == "eml_mail_api":
            return EMLMailAPI(self.config)
        else:
            raise ValueError(f"unsupported Mail API: {package}")
