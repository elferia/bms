from abc import ABC, abstractmethod
import logging
from typing import Iterator

import click


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_handler = logging.StreamHandler()
_logger.addHandler(_handler)


@click.group()
def bms() -> None:
    _handler.setLevel(logging.DEBUG)


@bms.command()
@click.argument('word')
def search(word: str) -> None:
    _logger.debug('searching with word "%s"', word)
    result = MochaSearchEngine.search(word)


class SearchResult:
    pass


class SearchEngine(ABC):
    @classmethod
    @abstractmethod
    def search(cls, word: str) -> Iterator[SearchResult]:
        pass


class MochaSearchEngine(SearchEngine):
    @classmethod
    def search(cls, word: str) -> Iterator[SearchResult]:
        _logger.debug('searching Mocha with word "%s"', word)
        raise NotImplementedError
