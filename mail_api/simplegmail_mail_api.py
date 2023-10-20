import os
from typing import Dict, List

from simplegmail import Gmail, label, query
from simplegmail.attachment import Attachment
from simplegmail.message import Message

from mail_api.abstract_mail_api import (
    AbstractAttachment,
    AbstractMailAPI,
    AbstractMessage,
    QueryParams,
)

SECRETS_FILE_DIR_KEY = "secrets_file_dir"


class SimpleGmailAdapter(AbstractMailAPI):
    def __init__(self, config: Dict[str, str]):
        secrets_file_dir: str = config[SECRETS_FILE_DIR_KEY]
        gmail_secrets_dir = os.path.expanduser(secrets_file_dir)
        self.gmail: Gmail = Gmail(
            os.path.join(gmail_secrets_dir, "client_secret.json"),
            os.path.join(gmail_secrets_dir, "gmail_token.json"),
        )

    def get_messages(self, the_query: QueryParams) -> List[AbstractMessage]:
        query_str = query.construct_query(the_query | {"label": label.INBOX})
        return [
            SimpleGmailMessageAdapter(m)
            for m in self.gmail.get_messages(query=query_str)
        ]


class SimpleGmailMessageAdapter(AbstractMessage):
    def __init__(self, message: Message):
        self.message = message

    def get_date(self) -> str:
        return self.message.date

    def get_html(self) -> str:
        return self.message.html

    def get_plain(self) -> str:
        return self.message.plain

    def get_attachments(self) -> List[AbstractAttachment]:
        return [SimpleGmailAttachmentAdapter(a) for a in self.message.attachments]

    def get_id(self) -> str:
        return self.message.id

    def get_sender(self) -> str:
        return self.message.sender

    def get_subject(self) -> str:
        return self.message.subject

    def mark_as_read(self) -> None:
        self.message.mark_as_read()

    def archive(self) -> None:
        self.message.archive()


class SimpleGmailAttachmentAdapter(AbstractAttachment):
    def __init__(self, attachment: Attachment):
        self.attachment = attachment

    def get_filename(self) -> str:
        return self.attachment.filename

    def set_filename(self, filename: str) -> None:
        self.attachment.filename = filename

    def save(self) -> None:
        self.attachment.save(overwrite=True)
