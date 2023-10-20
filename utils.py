import locale
import os
from contextlib import contextmanager
from typing import Tuple

from lxml import etree
from lxml import html as lx_html


@contextmanager
def cd(new_dir: str) -> None:
    """
    Using pathlib.Path as context manager is deprecated.
    https://github.com/python/cpython/issues/83863,
    thus we use our own cd context manager.

    :param new_dir: The directory to change to.
    """
    prev_dir: str = os.getcwd()
    os.chdir(os.path.expanduser(new_dir))
    try:
        yield
    finally:
        os.chdir(prev_dir)


@contextmanager
def temporary_locale(new_locale: str) -> None:
    """
    Temporarily changes the locale.
    :param new_locale:
    """
    old_locale: Tuple[str, str] = locale.getlocale()
    try:
        locale.setlocale(locale.LC_ALL, new_locale)
        yield
    finally:
        locale.setlocale(locale.LC_ALL, old_locale)


def get_tree(html_str: str) -> etree.ElementBase:
    """
    Get tree from parsing html string.

    For some reason, parsing the html as xml works for real emails, but not for
    eml files. Parsing the html as html works for eml files, but not for real
    emails. So we try both.
    Also: We remove the xmlns attribute from the html_str, because it makes xpath expressions
    more complicated and is not present in real emails.


    :param html_str: html as string
    :return: tree
    """

    # replacing the xmlns was necessary only for Orell Fuessli so far.
    # Reason: It would make xpath expressions more complicated, e.g.
    # tree.xpath("//body/table/tr/td/div/p[3]")[0]
    # would become:
    # tree.xpath("//x:body/x:table/x:tr/x:td/x:div/x:p[3]", namespaces={"x": "http://www.w3.org/1999/xhtml"})[0]
    # and the xmlns was only there for the eml file, not for the real email.
    html_str = html_str.replace('xmlns="http://www.w3.org/1999/xhtml"', "")
    try:
        # Case 1: html is from a real email.
        # When getting the html from a real email, parsing the message body as
        # xml works. When getting the html from an eml file, it doesn't.
        root: etree.Element = etree.fromstring(html_str)
        tree: etree.ElementTree = etree.ElementTree(root)
    except etree.XMLSyntaxError:
        # Case 2: html is from an eml file.
        # When getting the html from an eml file, parsing the message body as
        # html works. When getting the html from a real email, it doesn't.
        # (see https://stackoverflow.com/a/31210728)
        tree: lx_html.HtmlElement = lx_html.fromstring(html_str)
    return tree
