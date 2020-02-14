from configparser import ConfigParser
from glob import escape as glob_escape, iglob
from io import TextIOWrapper
import logging
from mimetypes import guess_type as guess_mimetype
from operator import attrgetter, methodcaller
from os import listdir, makedirs, rmdir
import os
import os.path
from os.path import basename, expanduser
import shutil
from tempfile import mkdtemp
from typing import BinaryIO, Iterable, Iterator
from urllib.parse import urlparse
from zipfile import ZipFile, is_zipfile

import click
import pkg_resources
from prompt_toolkit import prompt
from rarfile import RarFile, is_rarfile

from bms import difficulty_table
from bms import songdata
from bms.parse import BMS, parse as parse_bms
from bms.search import MochaSearchEngine
from bms.util import download_url


_logger = logging.getLogger(__package__)
_logger.addHandler(logging.StreamHandler())

_debug = _logger.debug


@click.group()
@click.option('--resource', 'resource_path')
@click.option('-v', '--verbose', 'verbosity', count=True)
@click.pass_context
def bms(ctx: click.Context, resource_path: str, verbosity: int) -> None:
    _logger.setLevel(logging.WARNING - (verbosity + 1) * 10)

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

    user_config = ConfigParser(converters=dict(list=methodcaller('split')))
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
    bms_objs = _get_bms_objs(path)
    title_list = list(map(attrgetter('title'), bms_objs))
    _debug('BMSes: %s', title_list)
    canonical_title = _get_longest_suffix(title_list)
    if canonical_title:
        canonical_title = prompt('title: ', default=canonical_title)
    else:
        canonical_title = prompt(
            '''failed to guess canonical title. please type yourself.
BMSs\' title are:
    ''' + '\n    '.join(title_list) +
            '''
type title: ''')
    _debug('title: %s', canonical_title)
    dt_iter = difficulty_table.load(config['beatoraja'])
    beatoraja_path = expanduser(config['beatoraja']['path'])
    songdata.connect(beatoraja_path)
    for dtable in dt_iter:
        _debug('difficulty table name: %s', dtable.name)
        entries = dtable.search(canonical_title)
        for entry in entries:
            _debug('bms found. md5=%s', entry.md5)
            if songdata.exists(entry.md5):
                _logger.info('%s is already installed', entry.title)
                continue
            if not entry.appendurl:
                continue
            url = entry.appendurl
            yn = prompt(
                f'{entry.title} found in {dtable.name}. install? ',
                default='y')
            if yn != 'y':
                continue

            d = download_url(url)
            if not d:
                continue
            content_type, f = d
            if content_type == 'application/zip':
                _extract_files(f, path)
            elif content_type == 'application/x-rar-compressed':
                _extract_rar_files(f, path)
            elif content_type == 'application/octet-stream':
                yn = prompt(f'install {url}? [y/n]: ', default='y')
                if yn == 'y':
                    _install_url(f, url, path)
            else:
                raise NotImplementedError


def _install_url(f: BinaryIO, url: str, path: str) -> None:
    p = urlparse(url)
    paths = p.path.rsplit('/', 1)
    filename = paths[1] if len(paths) > 1 else paths[0]
    filepath = os.path.join(path, filename)
    with open(filepath, 'xb') as g:
        shutil.copyfileobj(f, g)
    _logger.info('%s added', filepath)


def _extract_files(f: BinaryIO, path: str) -> None:
    if not is_zipfile(f):
        raise NotImplementedError
    with ZipFile(f) as z:
        for member in z.infolist():
            if member.is_dir():
                continue
            filename = member.filename.encode('cp437').decode('cp932')
            filename = basename(filename)
            destpath = os.path.join(path, filename)
            with z.open(member) as content, open(destpath, 'xb') as target:
                shutil.copyfileobj(content, target)
            _logger.info('%s added', destpath)


def _extract_rar_files(f: BinaryIO, path: str) -> None:
    if not is_rarfile(f):
        raise NotImplementedError
    with RarFile(f, charset='cp932') as z:
        for member in z.infolist():
            if member.isdir():
                continue
            filename = basename(member.filename)
            destpath = os.path.join(path, filename)
            with z.open(member) as content, open(destpath, 'xb') as target:
                shutil.copyfileobj(content, target)
            _logger.info('%s added', destpath)


def _get_bms_objs(path: str) -> Iterator[BMS]:
    escaped_path = glob_escape(path)
    pattern = os.path.join(escaped_path, '*.bm[sel]')
    for bms_filepath in iglob(pattern):
        with open(bms_filepath, encoding='CP932') as bms_file:
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
