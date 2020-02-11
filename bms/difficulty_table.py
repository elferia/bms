from __future__ import annotations
from dataclasses import dataclass, fields as datafields
from glob import escape as escape_glob, iglob
import gzip
from itertools import chain
import json
from operator import attrgetter, itemgetter
from os.path import expanduser as expanduserpath, join as joinpath
from typing import Any, Dict, IO, Iterator, List, Mapping


class FromMappingMixin:
    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]):
        field_names = map(attrgetter('name'), datafields(cls))
        return cls(*(data[field_name] for field_name in field_names))


@dataclass
class DTableEntry(FromMappingMixin):
    md5: str
    title: str


@dataclass
class DifficultyTable(FromMappingMixin):
    name: str
    folder: List[Dict[str, Any]]

    @classmethod
    def load(cls, f: IO) -> DifficultyTable:
        data = json.load(f)  # type: Mapping[str, Any]
        return cls.from_mapping(data)

    def search(self, head: str) -> Iterator[DTableEntry]:
        for song in chain.from_iterable(map(itemgetter('songs'), self.folder)):
            if song['title'].startswith(head):
                yield DTableEntry.from_mapping(song)


def load(config: Mapping[str, Any]) -> Iterator[DifficultyTable]:
    beatoraja_path = config['path']
    beatoraja_path = expanduserpath(beatoraja_path)
    pattern = joinpath(escape_glob(beatoraja_path), 'table', '*.bmt')
    for path in iglob(pattern):
        with gzip.open(path, 'r') as f:
            yield DifficultyTable.load(f)
