from abc import ABC, abstractmethod
from collections import ChainMap
from configparser import ConfigParser
from dataclasses import dataclass
from io import TextIOWrapper
import logging
from types import MappingProxyType
from typing import Iterator

from bs4 import BeautifulSoup
import bs4
import click
import pkg_resources
import requests


_logger = logging.getLogger(__name__)
_logger.addHandler(logging.StreamHandler())

_debug = _logger.debug


@click.group()
@click.option('--resource', 'resource_path')
@click.option('-v', '--verbose', 'verbosity', count=True)
def bms(resource_path: str, verbosity: int) -> None:
    if verbosity > 0:
        _logger.setLevel(logging.WARNING - verbosity * 10)

    config = ConfigParser()
    if resource_path:
        raise NotImplementedError
    else:
        with pkg_resources.resource_stream(
                __name__, 'resource.ini'
        ) as f, TextIOWrapper(f) as config_file:
            config.read_file(config_file)

    MochaSearchEngine.URI = config['mocha']['uri']
    _debug('Mocha URI: %s', MochaSearchEngine.URI)


@bms.command()
@click.argument('word')
def search(word: str) -> None:
    _debug('searching with word "%s"', word)
    result = MochaSearchEngine.search(word)
    for bms in result:
        click.echo(bms.text)


@dataclass
class SearchResult:
    text: str


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
        root = BeautifulSoup(response.text, features='html.parser')
        tables = root('table', class_='ranking')
        assert len(tables) == 1, f'table must be exactly 1, got {len(tables)}'
        table = tables[0]
        rows = table(_is_data_row)
        for row in rows:
            yield SearchResult(''.join(row('td')[1].strings))


def _is_data_row(element) -> bool:
    if not isinstance(element, bs4.Tag):
        return False
    tag = element  # type: bs4.Tag
    if tag.name != 'tr':
        return False
    tr = tag
    return not tr.th
