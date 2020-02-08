from abc import ABC, abstractmethod
from collections import ChainMap
from configparser import ConfigParser
from io import TextIOWrapper
import logging
from types import MappingProxyType
from typing import Iterator

import click
import pkg_resources
import requests


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_handler = logging.StreamHandler()
_logger.addHandler(_handler)

_debug = _logger.debug


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
    _debug('Mocha base URI: %s', config['mocha']['uri'])

    MochaSearchEngine.URI = config['mocha']['uri']


@bms.command()
@click.argument('word')
def search(word: str) -> None:
    _debug('searching with word "%s"', word)
    result = MochaSearchEngine.search(word)


class SearchResult:
    pass


class SearchEngine(ABC):
    @classmethod
    @abstractmethod
    def search(cls, word: str) -> Iterator[SearchResult]:
        pass


class MochaSearchEngine(SearchEngine):
    URI = ''

    _SORT_USER_COUNT = 2
    _ORDER_DESCEND = 0
    _URL_EXISTS = 1
    _DEFAULT_PARAMS = MappingProxyType(
        dict(
            artist='', mode='beat-7k', sort=_SORT_USER_COUNT,
            order=_ORDER_DESCEND, url=_URL_EXISTS))

    @classmethod
    def search(cls, word: str) -> Iterator[SearchResult]:
        _debug('searching Mocha with word "%s"', word)
        response = requests.get(
            cls.URI, params=ChainMap(cls._DEFAULT_PARAMS, dict(title=word)))
        _debug('Mocha result HTML: %s', response.text)
        raise NotImplementedError
