from typing import TextIO
from dataclasses import dataclass


@dataclass
class BMS:
    title: str
    md5: str


def parse(bms: TextIO) -> BMS:
    title = ''
    for raw_line in bms:
        line = raw_line.lstrip().rstrip('\r\n')
        if line.startswith('#') and line[1:5 + 1].casefold() == 'title':
            parsed_line = line.split(maxsplit=1)
            if len(parsed_line) == 2:
                title = parsed_line[1]
    return BMS(title, '')
