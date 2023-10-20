from typing import Dict, List, Protocol

QueryParams = Dict[str, str]


class AbstractAttachment(Protocol):
    def get_filename(self) -> str:
        pass

    def set_filename(self, filename: str) -> None:
        pass

    def save(self) -> None:
        pass


class AbstractMessage(Protocol):
    def get_date(self) -> str:
        pass

    def get_html(self) -> str:
        pass

    def get_plain(self) -> str:
        pass

    def get_attachments(self) -> List[AbstractAttachment]:
        pass

    def get_id(self) -> str:
        pass

    def get_sender(self) -> str:
        pass

    def get_subject(self) -> str:
        pass

    def mark_as_read(self) -> None:
        pass

    def archive(self) -> None:
        pass


class AbstractMailAPI(Protocol):
    def get_messages(self, query_params: QueryParams) -> List[AbstractMessage]:
        pass
