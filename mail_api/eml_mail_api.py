import glob
import os
import re
from email import header, message_from_file
from typing import Dict, List, Optional

from mail_api.abstract_mail_api import (
    AbstractAttachment,
    AbstractMailAPI,
    AbstractMessage,
    QueryParams,
)

EMAILS_DIR_KEY = "emails_dir"


class EMLEmailAttachment(AbstractAttachment):
    def __init__(self, part):
        self.part = part

    def save(self, overwrite: bool = True) -> None:
        # Implementation to save the attachment
        with open(self.get_filename(), "wb") as f:
            f.write(self.part.get_payload(decode=True))

    def get_filename(self) -> str:
        return self.part.get_filename()


class EMLEmailMessage(AbstractMessage):
    def __init__(self, msg, filename):
        self.msg = msg
        self.filename = filename

    def get_date(self) -> str:
        return self.msg["Date"]

    def get_html(self) -> str:
        try:
            return next(
                (
                    part.get_payload(decode=True).decode()
                    for part in self.msg.walk()
                    if part.get_content_type() == "text/html"
                ),
                "",
            )
        except UnicodeDecodeError:
            return next(
                (
                    part.get_payload(decode=True).decode("latin-1")
                    for part in self.msg.walk()
                    if part.get_content_type() == "text/html"
                ),
                "",
            )

    def get_plain(self) -> Optional[str]:
        # Iterate over each part in the email
        for part in self.msg.walk():
            # Look for the plain text part
            if part.get_content_type() == "text/plain":
                if charset := part.get_content_charset():
                    return part.get_payload(decode=True).decode(charset)
                else:
                    return part.get_payload()
        return None  # Return None if no 'text/plain' part is found

    def get_attachments(self) -> List[AbstractAttachment]:
        attachments = []
        for part in self.msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get("Content-Disposition") is None:
                continue
            attachments.append(EMLEmailAttachment(part))
        return attachments

    def get_id(self) -> str:
        return self.filename

    def get_sender(self) -> str:
        return self.msg["From"]

    def get_subject(self) -> str:
        return "".join(
            [
                s.decode(encoding)
                if encoding
                else s
                if isinstance(s, str)
                else s.decode()
                for s, encoding in header.decode_header(self.msg["Subject"])
            ]
        )

    def mark_as_read(self) -> None:
        # Implementation to mark the email as read
        pass

    def archive(self) -> None:
        # Implementation to archive the email
        pass


def regexify(query, key):
    return r".*".join(
        [re.escape(x) for x in query.get(key, "").lower().split()]
    ).replace('"', "")


class EMLMailAPI(AbstractMailAPI):
    def __init__(self, config: Dict[str, str]):
        self.directory = config[EMAILS_DIR_KEY]

    def get_messages(self, query: Dict[str, str]) -> List[AbstractMessage]:
        email_files = glob.glob(f"{self.directory}/*.eml")
        messages = []

        for email_file in email_files:
            with open(email_file, "r") as f:
                msg = message_from_file(f)
                eml_msg = EMLEmailMessage(msg, os.path.basename(email_file))

                # "poor man's gmail query":
                # gmail would find email messages with a subject query, even
                # if there are words missing in the search term. the eml
                # implementation would not find the respective mails, so we
                # interpret the search as a regex by stuffing .* between the
                # words of the query and escaping regex-meta-chars.
                subject_query = regexify(query, "subject")
                if subject_query and not re.search(
                    subject_query, eml_msg.get_subject().lower()
                ):
                    continue

                # this is a mere search, not a regex.
                sender_query = query.get("sender", "").lower()
                if sender_query and sender_query not in eml_msg.get_sender().lower():
                    continue

                messages.append(eml_msg)

        return messages
