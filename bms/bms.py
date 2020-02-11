from configparser import ConfigParser
from glob import escape as glob_escape, iglob
from io import TextIOWrapper
import logging
from mimetypes import guess_type as guess_mimetype
from operator import attrgetter
from os import listdir, makedirs, rmdir
import os
import os.path
from os.path import basename
import shutil
from tempfile import mkdtemp
from typing import Iterable, Iterator
from zipfile import ZipFile, is_zipfile

import click
import pkg_resources
from prompt_toolkit import prompt

from bms import difficulty_table
from bms.parse import BMS, parse as parse_bms
from bms.search import MochaSearchEngine


_logger = logging.getLogger(__package__)
_logger.addHandler(logging.StreamHandler())

_debug = _logger.debug


@click.group()
@click.option('--resource', 'resource_path')
@click.option('-v', '--verbose', 'verbosity', count=True)
@click.pass_context
def bms(ctx: click.Context, resource_path: str, verbosity: int) -> None:
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

    user_config = ConfigParser()
    user_config.read('bms.ini')
    ctx.obj = user_config


pass_config = click.make_pass_decorator(ConfigParser)


@bms.command()
@click.argument('word')
def download(word: str) -> None:
    _debug('searching with word "%s"', word)
    results = tuple(MochaSearchEngine.search(word))
    if len(results) == 0:
        return
    index = 0
    if len(results) > 1:
        for i, bms in enumerate(results):
            click.echo(f'"{bms.text}" [{i}]')
        index = int(prompt('choose index: ', default='0'))
    else:
        click.echo(f'"{results[0].text}"')
    _debug('selected: %i', index)
    result = results[index]
    _debug('detailed page uri: %s', result.detail_uri)
    result.download()


@bms.command()
@click.option('-d', 'destdir')
@click.argument('path')
@pass_config
def install(config: ConfigParser, path: str, destdir: str) -> None:
    destpath = os.path.expanduser(config['bms']['path'])
    if destdir:
        destpath = os.path.join(destpath, destdir)
    makedirs(destpath, exist_ok=True)

    mime, _ = guess_mimetype(path)
    if mime == 'application/zip':
        if not is_zipfile(path):
            raise NotImplementedError
        tempdir = mkdtemp(dir=destpath)
        try:
            with ZipFile(path) as z:
                z.extractall(tempdir)
            contents = listdir(tempdir)
            if len(contents) == 1:
                content_path = os.path.join(tempdir, contents[0])
                shutil.move(content_path, destpath)
                rmdir(tempdir)
            else:
                filename = basename(path)
                filename_base = filename.rsplit('.', 1)[0]
                newpath = os.path.join(destpath, filename_base)
                os.replace(tempdir, newpath)
        except:
            shutil.rmtree(tempdir)
            raise
    else:
        raise NotImplementedError


@bms.command()
@click.argument('path')
@pass_config
def amplify(config: ConfigParser, path: str) -> None:
    expanded_path = os.path.expanduser(path)
    _amplify(config, expanded_path)


def _amplify(config: ConfigParser, path: str) -> None:
    bms_objs = tuple(_get_bms_objs(path))
    _debug('BMSes: %s', bms_objs)
    canonical_title = _get_longest_suffix(map(attrgetter('title'), bms_objs))
    canonical_title = prompt('title: ', default=canonical_title)
    _debug('title: %s', canonical_title)
    dt_iter = difficulty_table.load(config['beatoraja'])
    hash_set = frozenset(map(attrgetter('md5'), bms_objs))
    for dtable in dt_iter:
        _debug('difficulty table name: %s', dtable.name)
        entries = dtable.search(canonical_title)
        for entry in entries:
            _debug('bms found. md5=%s', entry.md5)
            if entry.md5 in hash_set:
                pass
            else:
                pass


def _get_bms_objs(path: str) -> Iterator[BMS]:
    escaped_path = glob_escape(path)
    pattern = os.path.join(escaped_path, '*.bm[sel]')
    for bms_filepath in iglob(pattern):
        with open(bms_filepath) as bms_file:
            yield parse_bms(bms_file)


def _get_longest_suffix(words: Iterable[str]) -> str:
    words_tuple = tuple(words)
    if len(words_tuple) == 0:
        return ''

    suffix_length = 0
    for chars in zip(*words_tuple):
        if len(set(chars)) != 1:
            break
        suffix_length += 1
    return words_tuple[0][:suffix_length]
