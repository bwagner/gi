#!/usr/bin/env python
from collections import defaultdict
from email import message_from_file

"""
Sensitive Information:
- Headers
    - Delivered-To                : Sensitive
    - X-Original-To               : Sensitive
    - To                          : Sensitive
    - From                        : Sensitive
    - Cc                          : Sensitive
    - Bcc                         : Sensitive
    - Received                    : Sensitive
    - X-Originating-IP            : Sensitive
    - Reply-To                    : Potentially Sensitive
    - Sender                      : Potentially Sensitive
    - X-Google-Smtp-Source        : Potentially Sensitive
    - X-Received                  : Potentially Sensitive
    - Authentication-Results      : Potentially Sensitive
    - X-Gmail-Fetch-Info          : Potentially Sensitive
    - Return-Path                 : Potentially Sensitive
    - Subject                     : Potentially Sensitive
    - Disposition-Notification-To : Potentially Sensitive
    - Errors-To                   : Potentially Sensitive
    - X-Original-Sender           : Potentially Sensitive
    - Received-SPF                : Less Sensitive
    - DKIM-Signature              : Less Sensitive
    - X-Mailin-EID                : Less Sensitive
    - Date                        : Less Sensitive
    - Message-Id                  : Less Sensitive
    - Origin-messageId            : Less Sensitive
    - X-sib-id                    : Less Sensitive
    - List-Unsubscribe-Post       : Less Sensitive
    - Feedback-ID                 : Less Sensitive
    - List-Unsubscribe            : Less Sensitive
    - In-Reply-To                 : Less Sensitive
    - References                  : Less Sensitive
    - User-Agent                  : Less Sensitive
    - X-Mailer                    : Less Sensitive
    - Organization                : Less Sensitive
    - Mime-Version                : Not Sensitive
    - Content-Type                : Not Sensitive
    - X-Antivirus                 : Not Sensitive
    - X-Antivirus-Status          : Not Sensitive
    - X-CSA-Complaints            : Not Sensitive
    - X-Spam-Status               : Not Sensitive
    - X-Spam-Level                : Not Sensitive
    - X-Spam-Checker-Version      : Not Sensitive
    - X-Spam-Relay-Countries      : Not Sensitive
    - X-Spam-DCC                  : Not Sensitive
    - X-Priority                  : Not Sensitive
    - Importance                  : Not Sensitive
    - Priority                    : Not Sensitive
    - Content-Disposition         : Not Sensitive
    - Content-Transfer-Encoding   : Not Sensitive
    - Precedence                  : Not Sensitive
    - X-Auto-Response-Suppress    : Not Sensitive
    - Auto-Submitted              : Not Sensitive



- Body
- Attachments

See:
https://chat.openai.com/share/376cf58f-bbae-42eb-8709-2713a18065f4

https://tools.ietf.org/html/rfc5322

https://developer.mozilla.org/en-US/docs/Mozilla/Thunderbird/Thunderbird_extensions/Building_a_Thunderbird_extension_3:_Modifying_an_email_prior_to_sending_or_saving#Mail_headers

https://en.wikipedia.org/wiki/List_of_email_header_fields
"""

# Read the email from a file
with open(
    "MUSICSTORE_Your_Music_Store_sales_invoice_and_shipping_information.eml", "r"
) as f:
    email_message = message_from_file(f)

# Subject
subject = email_message["Subject"]
print(f"Subject: {subject}")

# Sender
sender = email_message["From"]
print(f"Sender: {sender}")

# Recipient
recipient = email_message["To"]
print(f"Recipient: {recipient}")

# Date
date = email_message["Date"]
print(f"Date: {date}")

print("========= all headers:")
for header, value in email_message.items():
    print(f"<-{header}->: {value}")
print("=========")
headers = defaultdict(list)
for header, value in email_message.items():
    headers[header].append(value)
print("========= all headers (defaultdict):")
for header, value in headers.items():
    # print(f"<-{header}->: {value}")
    print(f"    - {header}")
print("=========")

# Body
body = ""
html_body = ""
for part in email_message.walk():
    content_type = part.get_content_type()
    content_disposition = str(part.get("Content-Disposition"))

    # Skip any text, html, or data in multipart/* parts.
    if part.is_multipart():
        continue

    if "attachment" not in content_disposition:
        # not an attachment, is it the text or HTML body?
        if content_type == "text/plain":
            body = part.get_payload(decode=True).decode()
        elif content_type == "text/html":
            html_body = part.get_payload(decode=True).decode()
        elif "image" in content_type:
            # Inline image. For now, let's just note its presence
            print(f"Inline {content_type} image found.")

        else:
            print(f"Unexpected content_type: {content_type}")

print(f"Body (plain text):\n'{body[:20]}' ...")
print(f"Body (HTML):\n'{html_body[:20]}' ...")

# Attachments
attachments = []
for part in email_message.walk():
    content_type = part.get_content_type()
    content_disposition = str(part.get("Content-Disposition"))

    if "attachment" in content_disposition:
        if filename := part.get_filename():
            attachments.append(filename)
            # Save the file
            with open(filename, "wb") as f:
                f.write(part.get_payload(decode=True))

print(f"Attachments: {attachments}")
