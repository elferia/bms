from abc import ABC, abstractmethod
from configparser import ConfigParser
from io import TextIOWrapper
import logging
from typing import Iterator

import click
import pkg_resources


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_handler = logging.StreamHandler()
_logger.addHandler(_handler)


@click.group()
@click.option('--config', 'config_path')
def bms(config_path: str) -> None:
    _handler.setLevel(logging.DEBUG)

    config = ConfigParser()
    if config_path:
        raise NotImplementedError
    else:
        with pkg_resources.resource_stream(
                __name__, 'resource.ini'
        ) as f, TextIOWrapper(f) as config_file:
            config.read_file(config_file)
    _logger.debug('Mocha base URI: %s', config['mocha']['base_uri'])


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
