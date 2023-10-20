#!/usr/bin/env python

import os
import re
import socket
import subprocess
import sys
from typing import Annotated, Optional

import pyperclip

# import keyring
import typer

import __about__
import mail_api.simplegmail_mail_api
import plugins
from message_handler import MessageHandler, ParameterObject

# environment variable names:
GMAIL_SECRET_KEY = "GET_INVOICES_GMAIL_SECRET_FILE_DIR"
RECEIPTS_DIR_KEY = "GET_INVOICES_RECEIPTS_DIR"
EXPECTED_HOST_KEY = "GET_INVOICES_HOST"
POST_PROCESS_KEY = "GET_INVOICES_POST"
MAIN_CURRENCY_KEY = "GET_INVOICES_MAIN_CURRENCY"
CATEGORY_MAP_KEY = "GET_INVOICES_MAP_CATEGORY_FILE"
EML_DIR_KEY = "GET_INVOICES_EML_DIR"

MAIL_API_DEFAULT = "simplegmail"

"""
GET_INVOICES_GMAIL_SECRET_FILE_DIR (mandatory)
Indicate in which gmail secret file is stored in the environment variable
GET_INVOICES_GMAIL_SECRET_FILE_DIR, e.g. in .bashrc:
export GET_INVOICES_GMAIL_SECRET_FILE_DIR="$HOME/.gmail_secret.json"

GET_INVOICES_RECEIPTS_DIR (mandatory)
Decide where to store your receipts and put that into the designated environment variable
GET_INVOICES_RECEIPTS_DIR, e.g. in .bashrc:
export GET_INVOICES_RECEIPTS_DIR="$HOME/accounting/`date +%Y`"

GET_INVOICES_HOST (optional)
If you want to make sure you're running the script on a specific host, add the designated
environment variable GET_INVOICES_HOST, e.g. in .bashrc:
export GET_INVOICES_HOST="My Computer"
Enter as host name the name you get by running on that host:
python -c "import socket;print(socket.gethostname())"
If you don't care about the host, add command line option -s when invoking this script.

GET_INVOICES_POST (optional)
If you want some processing to be invoked add environment variable POST_PROCESS_KEY with
the name of the program. It will be invoked using subprocess.run.

GET_INVOICES_MAP_CATEGORY_FILE (optional)
If you want to map the category of the invoice to a different category than implemented,
add environment variable GET_INVOICES_MAP_CATEGORY_FILE with the full path of the file
containing the mapping. The file should be a csv file with the following structure:
MessageHandlerClass_abbreviated whitespace <category>, e.g.

NewYorkJazzWorkshop  further education
Apple  computer hardware
Iway  internet
... ...
The file can contain comments, i.e. lines starting with #. The file can be empty.
If the file is not found, the default mapping is used. If the file is found, the default
mapping is used for the MessageHandler classes not listed in the file.




When Integrating a new invoice, decide:
    Will you get the data from:
        The mail body? (e.g. PatreonMessageHandler)
        A pdf-attachment? (e.g. NzzMessageHandler)
        A pdf downloadable via link provided in the mail body? (e.g. BoltMessageHandler)

     When getting the data from a pdf, make sure that if the mail has several
     attachments, to select the correct pdf. See MusicStoreMessageHandler,
     where there are two pdfs attached, one with the invoice and one with the
     return form.
     There could be several attachments, including non-pdfs, e.g. jpgs. Since
     MusicStoreMessageHandler has been implemented, non-pdf attachments are filtered out.


pathfinding recipe:
from lxml import etree
root = etree.fromstring(html_str)
tree = etree.ElementTree(root)
el = tree.xpath("//*[contains(., '01.02.2022')]")[-1]  # last occurrence
tree.getpath(el)
-> returns xpath pointing to element el.
if tree.xpath(tree.getpath(el))[0].text returns the expected value,
  i.e. '01.02.2022', you're done.

if parsing of html as xml above fails, do the following instead:
root = etree.HTML(html_str)
tree = etree.ElementTree(root)
el = tree.xpath("//*[contains(., 'wire')]")[0]
tree.getpath(el)


TODO:
    - Tests! Mocking
        - Anonymize existing mails
        - set up a process how to integrate new kinds of invoices into the testing
          environment, e.g.
          1. save mails locally (as .eml)
          2. run them through an anonymizer.
             The anonymizer scrambles the recipient email address, recipient's name,
             (partial) credit card info, client number.
             If the mail has an attachment, the anonymizer allows to extract it,
             let the user do the anonymizing and then offers a function to recreate
             the .eml file including this attachment.
             The Mockup version then retrieves those .eml files instead of hitting
             the user's inbox.
    - note about subject: If you want exact substring, enclose in quotes
      (see ApfelkisteMessageHandler)
    - restructure, factor out things that are duplicated, better architecture
    - get rid of simplegmail and address the gmail API directly.
    - support other mailboxes besides gmail.
"""


def assert_host(hostname: str):
    actual_hostname: str
    if hostname not in (actual_hostname := socket.gethostname()):
        print(f"run this script on {hostname}. You're on {actual_hostname}")
        sys.exit(1)


def t_main(
    handlers_regex: Optional[str] = typer.Argument(None),
    skip_host_test: bool = typer.Option(
        False, "--skip-host-test", "-s", help="Skip host test."
    ),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Perform a dry run."),
    list_handlers: bool = typer.Option(
        False, "--list-handlers", "-lh", help="List available handlers."
    ),
    mail_api_choice: Annotated[
        str,
        typer.Option(
            "--mail-api",
            "-m",
            help=f"The Mail API to use.",
        ),
    ] = MAIL_API_DEFAULT,
    list_mail_apis: bool = typer.Option(
        False, "--list-mail-apis", "-lm", help="List available mail apis."
    ),
    show_version: bool = typer.Option(False, "--version", "-v", help="Show version."),
):
    if show_version:
        print(__about__.__version__)
        return

    if list_handlers:
        print(", ".join([x[1] for x in MessageHandler.get_handlers(handlers_regex)]))
        return

    if list_mail_apis:
        print(
            ", ".join(
                [
                    re.search(r"mail_api\.([^_]+).+", x.__module__)[1]
                    for x in mail_api.abstract_mail_api.AbstractMailAPI.__subclasses__()
                ]
            )
        )  # noqa PyUnresolvedReferences
        return

    if not (receipts_dir := os.getenv(RECEIPTS_DIR_KEY)):
        print(f"Environment variable {RECEIPTS_DIR_KEY} not set. Quitting.")
        return

    if not (secret_file_dir := os.getenv(GMAIL_SECRET_KEY)):
        print(f"Environment variable {GMAIL_SECRET_KEY} not set. Quitting.")
        return

    if not (main_currency := os.getenv(MAIN_CURRENCY_KEY)):
        print(f"Environment variable {MAIN_CURRENCY_KEY} not set. Quitting.")
        return

    if not skip_host_test:
        if not (exp_hn := os.getenv(EXPECTED_HOST_KEY)):
            print(f"Environment variable {EXPECTED_HOST_KEY} not set. Quitting.")
            return
        assert_host(exp_hn)

    category_map_file: str
    if category_map_file := os.getenv(CATEGORY_MAP_KEY):
        MessageHandler.set_category_map(category_map_file)
    MessageHandler.set_main_currency(main_currency)

    if mail_api_choice == "simplegmail":
        mail_api_config = {
            mail_api.mail_api_factory.PACKAGE_KEY: f"{mail_api_choice}_mail_api",  # noqa PyUnresolvedReferences
            mail_api.simplegmail_mail_api.SECRETS_FILE_DIR_KEY: secret_file_dir,  # noqa PyUnresolvedReferences
        }
    elif mail_api_choice == "eml":
        mail_api_config = {
            mail_api.mail_api_factory.PACKAGE_KEY: f"{mail_api_choice}_mail_api",  # noqa PyUnresolvedReferences
            mail_api.eml_mail_api.EMAILS_DIR_KEY: os.getenv(EML_DIR_KEY) or os.path.join(  # noqa PyUnresolvedReferences
                os.path.dirname(__file__), "tests", "emails"
            ),
        }
        print(f"{mail_api_config}")
    else:
        print(f"Unsupported mail api: {mail_api_choice}")
        return

    clipboard_list: list[str]
    if clipboard_list := MessageHandler.process(
        ParameterObject(mail_api_config, receipts_dir, dry_run),
        handlers_regex,
    ):
        pyperclip.copy(clipboard := "\n".join(clipboard_list))
        print(f"Now in clipboard:\n{clipboard}")

        if postprocess := os.getenv(POST_PROCESS_KEY):
            if dry_run:
                print(f"Dry run: Not invoking {postprocess}...")
            else:
                print(f"Invoking {postprocess}...")
                subprocess.run([postprocess])
        else:
            print("No postprocessing configured.")
            print(f"To run a particular post process, set env. var {POST_PROCESS_KEY}.")
    else:
        print("No matching messages found.")


def main():
    plugins.init()
    typer.run(t_main)


if __name__ == "__main__":
    main()
