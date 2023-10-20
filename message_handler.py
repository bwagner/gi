import os
import re
import shutil
import traceback
import uuid
from abc import ABC, abstractmethod
from collections import namedtuple
from datetime import datetime
from typing import Dict, List, Type

import dateparser
from currency_file import get_cc

from mail_api.abstract_mail_api import (
    AbstractAttachment,
    AbstractMailAPI,
    AbstractMessage,
)
from mail_api.mail_api_factory import MailApiFactory
from message_marker_archiver import MessageMarkerArchiver, get_message_marker_archiver
from utils import cd

ParameterObject = namedtuple(
    "ParameterObject", ["mail_api_config", "receipts_dir", "dry_run"]
)


class MessageHandler(ABC):
    category_map: Dict[str, str] = {}
    main_currency: str = "CHF"

    """
    Possible query params:
    https://support.google.com/mail/answer/7190?hl=en
    """
    SUBJECT = "subject"
    SENDER = "sender"

    def __init__(self):
        """
        ctor.
        """
        self.date_of_curr_msg: datetime | None = None
        self.filename: str | None = None
        self.amount = float | None
        self.purchase_date: datetime | None = None
        self.clipboard: List[str] = []
        self.dry_run: bool | None = None
        self.my_currency: str | None = None
        self.receipts_dir: str | None = None
        self.mail_api: AbstractMailAPI | None = None

    def get_category_key(self) -> str:
        return self.__class__.__name__.replace("MessageHandler", "")

    def set_params(self, po: ParameterObject):
        self.dry_run: bool = po.dry_run
        self.receipts_dir: str = po.receipts_dir
        self.my_currency: str = self.__class__.main_currency  # default
        maf = MailApiFactory(po.mail_api_config)
        self.mail_api = maf.create()

    @staticmethod
    def process(po: ParameterObject, handlers_regex: str = None) -> list[str]:
        """
        Retrieves all subclasses of MessageHandler, instantiates them and calls
        the 'process_msgs' method on each of them. Accumulates stuff that finally
        goes into the clipboard.

        Parameters:
        @secrets_file_dir(str): Directory where the gmail API secrets file is located.
        @receipts_dir(str): Directory where receipts are saved.
        @handlers_regex(str): Regex to filter for MessageHandlers.
        @dry_run(bool): When True only logs on stdout without actually doing things
        (marking message as read, archiving message, saving attachment)
        """
        marker: MessageMarkerArchiver = get_message_marker_archiver(po.dry_run)

        mhs: List[tuple[MessageHandler, str]] = [
            (x[0](), x[1]) for x in MessageHandler.get_handlers(handlers_regex)
        ]
        for mh, _ in mhs:
            mh.set_params(po)
        clipboard: List[str] = []
        mh: MessageHandler
        name: str
        for mh, name in mhs:
            try:
                if mh.process_msgs(marker):
                    clipboard.extend(mh.clipboard)
                    print(f"{name}: Appended to clipboard:")
                    print("\n".join(mh.clipboard))
                else:
                    print(f"{name}: no matching messages found.")
            except Exception:
                traceback.print_exc()
        return clipboard

    @staticmethod
    def get_handlers(
        handlers_regex: str = None,
    ) -> list[tuple[Type["MessageHandler"], str]]:
        handlers_regex = handlers_regex or r"[a-z]+"
        pat = re.compile(rf".*\.({handlers_regex}?)MessageHandler.*", re.IGNORECASE)
        return [
            (x, m[1])
            for x in MessageHandler.__subclasses__()
            if (m := re.match(pat, str(x)))
        ]

    def process_msgs(self, marker: MessageMarkerArchiver) -> int:
        """
        Template method that processes all messages.
        Hooks of the template method:
        - filter_messages
        - handle_html
        - handle_plain
        - handle_attachment
        """
        messages: List[AbstractMessage] = self.filter_messages()
        messages_in_clipboard: int = 0
        category: str = self.category_map.get(self.get_category_key(), self.get_type())
        html_handled: bool = False
        plain_handled: bool = False
        m: AbstractMessage
        for m in messages:
            if date_of_curr_msg := dateparser.parse(m.get_date()):
                pass
            elif not (
                date_of_curr_msg := datetime.strptime(
                    m.get_date(), "%a, %d %b %Y %H:%M:%S %z (%Z)"
                )
            ):
                raise ValueError(f"Could not parse date {m.get_date()}")
            self.date_of_curr_msg = date_of_curr_msg
            if m.get_html() and not self.handle_html(m.get_html()):
                html_handled = True

            if m.get_plain() and not self.handle_plain(m.get_plain()):
                plain_handled = True

            attachment_handled: bool = False
            attachment: AbstractAttachment
            for attachment in m.get_attachments():
                print(f"File: {attachment.get_filename()}")
                if not attachment.get_filename():
                    print(
                        f"  Skipping attachment with filename '{attachment.get_filename()}' in message id {m.get_id()}"
                    )
                    continue
                if not attachment.get_filename().lower().endswith(".pdf"):
                    print(f"  Skipping non-pdf attachment in message id {m.get_id()}")
                    continue
                attachment_handled = attachment_handled or not self.handle_attachment(
                    attachment
                )

            if not any([html_handled, plain_handled, attachment_handled]):
                raise ValueError(
                    f"{self.__class__.__name__}: "
                    f"None of html, plain, or attachment handled for message id {m.get_id()} "
                    f"from {m.get_sender()} with subject '{m.get_subject()}' on {m.get_date()}"
                )
            messages_in_clipboard += 1
            purchase_date: str = datetime.strftime(self.purchase_date, "%d.%m.%Y")
            if self.my_currency != self.__class__.main_currency:
                self.my_currency = self.my_currency.upper()
                self.my_currency = (
                    "USD" if self.my_currency == "$" else self.my_currency
                )
                cc, *_ = get_cc(
                    self.my_currency, self.__class__.main_currency, self.purchase_date
                )
                self.amount = cc.convert(
                    self.amount,
                    self.my_currency,
                    self.__class__.main_currency,
                    self.purchase_date,
                )
            self.clipboard.append(
                "\t".join(
                    [
                        purchase_date,
                        f"{self.amount:.2f}",
                        category,
                        "TRUE",
                        self.filename,
                    ]
                )
            )

            marker.mark_and_archive(m)

        return messages_in_clipboard

    @abstractmethod
    def get_query_params(self) -> dict[str, str]:
        pass

    @abstractmethod
    def get_type(self) -> str:
        pass

    def handle_html(self, html_str: str) -> bool:
        """
        Hook method. Deliberately not abstract:
        We don't want to impose handling html.
        We return True here to signal that there
        is no implementation of handle_html.
        Subclasses can override this method and
        must not return True. (Methods without
        an explicit return statement return None.)
        """
        return True

    def handle_plain(self, html_str: str) -> bool:
        """
        Hook method. Deliberately not abstract:
        We don't want to impose handling plain text.
        We return True here to signal that there
        is no implementation of handle_plain.
        Subclasses can override this method and
        must not return True. (Methods without
        an explicit return statement return None.)
        """
        return True

    def handle_attachment(self, attachment: AbstractAttachment) -> bool:
        """
        Hook method. Deliberately not abstract:
        We don't want to impose handling attachment.
        We return True here to signal that there
        is no implementation of handle_attachment.
        Subclasses can override this method and
        must not return True. (Methods without
        an explicit return statement return None.)
        """
        return True

    def save_html(self, html_str: str, filename: str) -> str:
        """
        Utility method to save html message.
        Returns the full path of the new file.
        """
        if self.dry_run:
            print(f"dry run, not saving html: {filename}")
        else:
            with cd(self.receipts_dir):
                with open(filename, "w") as f:
                    f.write(html_str)
        return os.path.join(self.receipts_dir, filename)

    def save(self, attachment: AbstractAttachment) -> str:
        """
        Utility method to save attachment.
        Returns the full path of the new file.
        """
        if self.dry_run:
            print(f"dry run, not saving attachment: {attachment.get_filename()}")
        else:
            with cd(self.receipts_dir):
                attachment.save()
        return os.path.join(self.receipts_dir, attachment.get_filename())

    def rename_receipt(self, f1: str, f2: str) -> str:
        """
        Utility method to rename file within receipts dir.
        Note: f1, f2 need to be just the basename! This asserted by
              chopping off any dir in their path.
        Returns the full path of the new file.
        """
        f1, f2 = (os.path.basename(x) for x in (f1, f2))
        if self.dry_run:
            print(f"dry run, not renaming receipt: {f1} -> {f2}")
        else:
            with cd(self.receipts_dir):
                shutil.move(f1, f2)
        return os.path.join(self.receipts_dir, f2)

    def filter_messages(self) -> list[AbstractMessage]:
        """
        Template method to filter message relevant for this handler.
        Hooks of the template method:
        - get_query_params

        Using pathlib.Path as context manager is deprecated.
        https://github.com/python/cpython/issues/83863,
        thus we use our own cd context manager.
        """

        messages: List[AbstractMessage] = self.mail_api.get_messages(
            self.get_query_params()
        )
        return messages

    def uuid(self) -> uuid.UUID:
        """
        Utility method for creating unique file names: If multiple invoices
        have the same purchase date, simply append the uuid to make
        them unique.
        """
        return uuid.uuid4()

    @classmethod
    def set_category_map(cls, category_map_file: str) -> None:
        cls.category_map = {}
        handlers = [x[1] for x in cls.get_handlers()]
        with open(os.path.expanduser(category_map_file)) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                cat, *categories = line.split()
                if cat not in handlers:
                    print(
                        f" Warning: handler for category '{cat}' not present. Ignored."
                    )
                else:
                    cls.category_map[cat] = " ".join(categories)

    @classmethod
    def set_main_currency(cls, main_currency: str) -> None:
        cls.main_currency = main_currency.upper()
