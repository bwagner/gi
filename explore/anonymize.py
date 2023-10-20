#!/usr/bin/env python

import email
import os.path
import random
import sys
from email import message_from_file, policy
from email.message import EmailMessage, Message
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
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
    print(f"Anonymizing part: {part.get_content_type()}")

    if part.is_multipart():
        new_part = MIMEMultipart()
        for subpart in part.get_payload():
            new_subpart = anonymize_part(subpart)
            new_part.attach(new_subpart)
    else:
        payload = part.get_payload(decode=True)
        if part.get_content_type() == "text/html":
            new_part = MIMEText(payload.decode("utf-8"), part.get_content_subtype())
        elif part.get_content_type().startswith("image/"):
            new_part = MIMEImage(payload, part.get_content_subtype())
        elif part.get_content_type().startswith("application/"):
            new_part = MIMEApplication(payload, part.get_content_subtype())
        else:
            new_part = MIMEText(payload.decode("utf-8"), part.get_content_subtype())

    for header, value in part.items():
        new_part[header] = fake_header(header)

    print(
        f"Anonymized part: {new_part.as_string()[:50]}..."
    )  # Print the first 50 characters
    return new_part


def anonymize_eml_file(filename):
    with open(filename, "r") as f:
        original_msg = message_from_file(f)

    new_msg = anonymize_part(original_msg)

    print("Complete new message:")
    print(new_msg.as_string()[:100])  # Print the first 100 characters

    filename, ext = os.path.splitext(filename)
    with open(f"{filename}_anon.eml", "w") as f:
        f.write(new_msg.as_string())


def main():
    anonymize_eml_file(sys.argv[1])


if __name__ == "__main__":
    main()
