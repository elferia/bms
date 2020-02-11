from __future__ import annotations
from dataclasses import dataclass
from glob import escape as escape_glob, iglob
import gzip
import json
from os.path import expanduser as expanduserpath, join as joinpath
from typing import Any, IO, Iterator, Mapping


@dataclass
class DTableEntry:
    md5: str


@dataclass
class DifficultyTable:
    name: str

    @classmethod
    def load(cls, f: IO) -> DifficultyTable:
        data = json.load(f)
        return cls(data['name'])

    def search(self, head: str) -> Iterator[DTableEntry]:
        raise NotImplementedError


def load(config: Mapping[str, Any]) -> Iterator[DifficultyTable]:
    beatoraja_path = config['path']
    beatoraja_path = expanduserpath(beatoraja_path)
    pattern = joinpath(escape_glob(beatoraja_path), 'table', '*.bmt')
    for path in iglob(pattern):
        with gzip.open(path, 'r') as f:
            yield DifficultyTable.load(f)
