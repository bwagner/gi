# get_invoices
get_invoices is a command line tool to get messages from your gmail account,
filter out invoices, archive them and save the receipts to a folder.
In addition, it puts the relevant invoice information into the clipboard
(thanks to [pyperclip](https://pypi.org/project/pyperclip)).
Optionally, a follow-up process is invoked.

See [main.py](main.py) for required and optional environment variables:
- `GET_INVOICES_GMAIL_SECRET_FILE_DIR` (required)
- `GET_INVOICES_RECEIPTS_DIR` (required)
- `GET_INVOICES_MAIN_CURRENCY` (required)
- `GET_INVOICES_HOST` (optional)
- `GET_INVOICES_POST` (optional)
- `GET_INVOICES_MAP_CATEGORY_FILE` (optional)
- `GET_INVOICES_EML_DIR` (optional)


## Command Line Usage
### Top Level
```console

 Usage: get_invoices [OPTIONS] [HANDLERS_REGEX]

╭─ Arguments ────────────────────────────────────────────────────────────────────────────╮
│   handlers_regex      [HANDLERS_REGEX]  [default: None]                                │
╰────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────╮
│ --skip-host-test  -s             Skip host test.                                       │
│ --dry-run         -d             Perform a dry run.                                    │
│ --list-handlers   -lh            List available handlers.                              │
│ --mail-api        -m       TEXT  The Mail API to use. [default: simplegmail]           │
│ --list-mail-apis  -lm            List available mail apis.                             │
│ --version         -v             Show version.                                         │
│ --help                           Show this message and exit.                           │
╰────────────────────────────────────────────────────────────────────────────────────────╯
```
## Install
```console
pip install https://github.com/bwagner/get_invoices.git
```
## Test
```console
git clone https://github.com/bwagner/get_invoices.git
cd get_invoices
python -m venv ~/venv/get_invoices
source ~/venv/get_invoices/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pytest
deactivate
rm -rf ~/venv/get_invoices
```
## TODO
- Tests
- weird project structure:
  there should be `__main__.py`. But I can't import from `__main__.py`,
  even if there is a `__init__.py` in the same directory.
  So `pyproject.toml` refers to `get_invoices = "main:main"` instead of
  `"__main__:main"`. Even if I add `__main__.py` and call `main.main` from there,
  the module can't be invoked with `python -m get_invoices`.
- introduce environment variable `GET_INVOICES_FORMAT` to allow specification of
  the order of the extracted data (date, amount, category, receipt_filename) and
  possibly a field separator.
- come up with architecture for follow-up process. For now, it's the clipboard and
  environment variable `GET_INVOICES_POST`.
- integration with bookkeeping/accounting software, e.g. [beancount](https://beancount.github.io/docs/importing_external_data.html)
- more todos in [main.py](main.py)
### Abstract Mail API
[`abstract_mail_api.py`](mail_api/abstract_mail_api.py) defines an abstract mail API.
The mail API should be usable by different mail APIs. The API consists of three classes:
`AbstractMailAPI`, `AbstractMessage`, and `AbstractAttachment`. `AbstractMailAPI`
offers selecting messages by date, by sender, by subject and other criteria. Its
sole method `get_messages` returns a list of `AbstractMessage` objects.
`AbstractMessage` offers methods to get various attributes like sender, the subject,
the html body, etc., and the method `get_attachments`, which returns
a list of `AbstractAttachment` objects. `AbstractAttachment` offers methods to
get and set the filename and to save the content of the attachment.
Currently, there's two implementations of the abstract mail API:
[simplegmail](mail_api/simplegmail_mail_api.py) and [eml](mail_api/eml_mail_api.py).
Next on the list is the gmail API.

## Contribute
```console
git clone https://github.com/bwagner/get_invoices.git
cd get_invoices
source ~/venv/get_invoices/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pre-commit install
```
The project uses a simple plugin architecture. The plugins are in the
[plugins](plugins) package. To add a plugin, create a new module in the
`plugins` package. Your plugin is a subclass of [MessageHandler](message_handler.py). The task of
your plugin is to detect mails that match your plugin, extract the relevant
information from the message and to save a receipt to the `receipts` directory (specified by environment
variable `GET_INVOICES_RECEIPTS_DIR`).
The plugin should extract this information:
- the amount of the invoice in the main currency (instance variable)
- the date of the invoice (instance variable)
- the category of the invoice (implemented as method `get_category`, can be overridden by the category mapping
  file specified by environment variable `GET_INVOICES_MAP_CATEGORY_FILE`)
- the filename of the receipt (instance variable)

Some invoicing parties choose to send the invoice as a pdf attachment (see [NzzMessageHandler](plugins/nzz_message_handler.py)), others add
the information in the html body of the mail (e.g. [PatreonMessageHandler](plugins/patreon_message_handler.py)) or provide a link to the invoice
([BoltMessageHandler](plugins/bolt_message_handler.py)). If the data is provided in the html body of the mail,
you can either use regexes ([KoboMessageHandler](plugins/kobo_message_handler.py)) or
a html parser ([AppleMessageHandler](plugins/apple_message_handler.py)) to extract the relevant information.
If the data is provided in a pdf, you are provided with a plain text representation of the pdf, courtesy of
[pdfminer](https://pypi.org/project/pdfminer.six/).

For now, the extracted data is accumulated in the clipboard, so that you can paste it into your accounting software.
Your accounting software or other follow-up process can optionally be specified by environment variable
`GET_INVOICES_POST`, which will be invoked after all plugins have been run on all messages.
