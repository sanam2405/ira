import logging
import structlog

from typing import Any, Iterator, override
from scrapy import logformatter
from pydantic import BaseModel
from itemadapter.adapter import AdapterInterface

log = structlog.stdlib.get_logger()


class PoliteLogFormatter(logformatter.LogFormatter):
    """A custom log formatter which does not log the dropped items. Used to avoid cluttering the logs."""

    @override
    def dropped(self, item, exception, response, spider):
        return {
            "level": logging.DEBUG,
            "msg": logformatter.DROPPEDMSG,
            "args": {
                "exception": exception,
                "item": item,
            },
        }


class PydanticAdapter(AdapterInterface):
    """An adapter which converts the Pydantic item to a dictionary. Needed to support Pydantic items in Scrapy."""

    item: BaseModel

    @classmethod
    @override
    def is_item_class(cls, item_class: type) -> bool:
        return issubclass(item_class, BaseModel)

    @override
    @classmethod
    def get_field_names_from_class(
        cls, item_class: type[BaseModel]
    ) -> list[str] | None:
        return list(item_class.model_fields.keys())

    @override
    def field_names(self) -> set[str]:
        return self.item.model_fields_set

    def asdict(self) -> dict:
        return self.item.model_dump(mode="json")

    @override
    def __getitem__(self, key: str) -> Any:
        return getattr(self.item, key)

    @override
    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self.item, key, value)

    @override
    def __delitem__(self, key: str) -> None:
        delattr(self.item, key)

    @override
    def __iter__(self) -> Iterator[str]:
        return iter(self.item.model_fields)

    @override
    def __len__(self) -> int:
        return len(self.item.model_fields)
