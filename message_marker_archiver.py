import contextlib
from abc import ABC, abstractmethod

from mail_api.abstract_mail_api import AbstractMessage


def get_message_marker_archiver(dry: bool):
    return MessageMarkerArchiverDry() if dry else MessageMarkerArchiverReal()


class MessageMarkerArchiver(ABC):
    """
    Interface for marking messages as read and archiving them.
    Foundation for implementing dry run.
    """

    @abstractmethod
    def mark_and_archive(self, m: AbstractMessage) -> None:
        """Marks message as read and archives it"""
        pass


class MessageMarkerArchiverReal(MessageMarkerArchiver):
    """
    Implementation of MessageMarkerArchiver that actually marks messages as read
    and archives them.
    """

    def mark_and_archive(self, m: AbstractMessage) -> None:
        m.mark_as_read()
        # capture KeyError from simplegmail:
        with contextlib.suppress(KeyError):
            m.archive()


class MessageMarkerArchiverDry(MessageMarkerArchiver):
    """
    Implementation of MessageMarkerArchiver that does not mark messages as read
    and does not archive them.
    """

    def mark_and_archive(self, m: AbstractMessage) -> None:
        print(f"dry run: not marking as read, not archiving message: {m.get_subject()}")
