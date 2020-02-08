import logging

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
    _logger.debug('searching with %s', word)
