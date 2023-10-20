#!/usr/bin/env python

import email
import os.path
import random
import sys
from email import message_from_file, policy
from email.message import EmailMessage, Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from faker import Faker

_fake = Faker()


def fake_header(header_name):
    if header_name.lower() in [
        "from",
        "to",
        "cc",
        "bcc",
        "delivered-to",
        "x-original-to",
        "return-path",
        "reply-to",
        "sender",
        "errors-to",
        "disposition-notification-to",
        "x-original-sender",
    ]:
        return _fake.email()
    elif header_name.lower() == "date":
        return _fake.date_time_this_decade().strftime("%a, %d %b %Y %H:%M:%S %z")
    elif header_name.lower() == "subject":
        return _fake.sentence()
    elif header_name.lower() in ["message-id", "origin-messageid"]:
        return f"<{_fake.uuid4()}@{_fake.free_email_domain()}>"
    elif header_name.lower() == "user-agent" or header_name.lower() == "x-mailer":
        return _fake.user_agent()
    elif header_name.lower() == "organization":
        return _fake.company()
    elif (
        header_name.lower() == "mime-version.txt"
        or header_name.lower() == "content-transfer-encoding"
    ):
        return "1.0"
    else:
        # Generate some plausible _fake data for other headers. You can extend this part as you wish.
        return f"{_fake.word()}_{_fake.word()}_{_fake.word()}"


def anonymize_part(part):
    if part.is_multipart():
        new_part = MIMEMultipart()
        for subpart in part.get_payload():
            new_subpart = anonymize_part(subpart)
            new_part.attach(new_subpart)
    else:
        payload = part.get_payload(decode=True)
        if isinstance(payload, bytes):
            payload = payload.decode(errors="replace")
        new_part = MIMEText(payload, part.get_content_subtype())

    for header, value in part.items():
        new_part[header] = fake_header(header)

    return new_part


def anonymize_eml_file(filename):
    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        original_msg = message_from_file(f)

    new_msg = MIMEMultipart()

    for header, value in original_msg.items():
        new_msg[header] = fake_header(header)

    if original_msg.is_multipart():
        for part in original_msg.walk():
            if part.is_multipart():
                continue
            new_part = anonymize_part(part)
            new_msg.attach(new_part)
    else:
        payload = original_msg.get_payload(decode=True)
        if isinstance(payload, bytes):
            payload = payload.decode(errors="replace")
        new_msg.set_payload(payload)

    with open(f"{filename}_anonymized.eml", "w") as f:
        f.write(new_msg.as_string())


def main():
    anonymize_eml_file(sys.argv[1])


if __name__ == "__main__":
    main()
