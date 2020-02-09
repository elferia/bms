from abc import ABC, abstractmethod
from collections import ChainMap
from dataclasses import dataclass
from logging import getLogger
from types import MappingProxyType
from typing import Iterator
from urllib.parse import urljoin
import webbrowser

from bs4 import BeautifulSoup
import bs4
from prompt_toolkit import prompt
import requests


_logger = getLogger(__package__)
_debug = _logger.debug

_session = requests.Session()
_http_get = _session.get


@dataclass
class SearchResult(ABC):
    text: str
    detail_uri: str

    @abstractmethod
    def download(self) -> None:
        pass


class MochaSearchResult(SearchResult):
    def download(self) -> None:
        response = _http_get(self.detail_uri)
        root = BeautifulSoup(response.text, features='html.parser')
        tables = root('table', class_='songinfo')
        assert len(tables) == 1, f'table must be exactly 1, got {len(tables)}'
        table = tables[0]  # type: bs4.Tag
        url_rows = table(self._is_url_row)
        assert len(url_rows) == 1, (
            f'URL row must be exactly 1, got {len(url_rows)}')
        url_row = url_rows[0]  # type: bs4.Tag
        url_cell = url_row('td')[1]  # type: bs4.Tag
        url = url_cell.a['href']  # type: str

        response = _session.head(url)
        content_type = response.headers.get('Content-Type', 'text/html')
        if content_type.casefold() == self._CASEFOLDED_TEXT_HTML:
            yn = prompt(
                'Song URL is for website. Open in browser? [y/n]: ',
                default='y')
            if yn == 'y':
                webbrowser.open_new_tab(url)
        else:
            raise NotImplementedError

    _CASEFOLDED_URL = 'url'.casefold()
    _CASEFOLDED_TEXT_HTML = 'text/html'.casefold()

    @classmethod
    def _is_url_row(cls, element) -> bool:
        if not _is_tr(element):
            return False
        tr = element  # type: bs4.Tag
        cells = tr('td')
        if len(cells) == 0:
            return False
        header_column_cell = cells[0]  # type: bs4.Tag
        header_column_text = ''.join(header_column_cell.strings)
        return header_column_text.casefold() == cls._CASEFOLDED_URL


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
        response = _http_get(
            cls.URI, params=ChainMap(cls._DEFAULT_PARAMS, dict(title=word)))
        cls._logger.debug('Mocha result HTML: %s', response.text)
        root = BeautifulSoup(response.text, features='html.parser')
        tables = root('table', class_='ranking')
        assert len(tables) == 1, f'table must be exactly 1, got {len(tables)}'
        table = tables[0]  # type: bs4.Tag
        rows = table(_is_data_row)

        row: bs4.Tag
        for row in rows:
            title_cell = row('td')[1]  # type: bs4.Tag
            relative_uri = title_cell.a['href']  # type: str
            absolute_uri = urljoin(cls.URI, relative_uri)
            yield MochaSearchResult(''.join(title_cell.strings), absolute_uri)


MochaSearchEngine._logger = getLogger(MochaSearchEngine.__qualname__)


def _is_data_row(element) -> bool:
    if not _is_tr(element):
        return False
    tr = element  # type: bs4.Tag
    return not tr.th


def _is_tr(element) -> bool:
    if not isinstance(element, bs4.Tag):
        return False
    tag = element  # type: bs4.Tag
    if tag.name != 'tr':
        return False
    return True
