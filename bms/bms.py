from configparser import ConfigParser
from glob import escape as glob_escape, iglob
from io import TextIOWrapper
import logging
from mimetypes import guess_type as guess_mimetype
from os import listdir, makedirs, rmdir
import os
import os.path
from os.path import basename
import shutil
from tempfile import mkdtemp
from zipfile import ZipFile, is_zipfile

import click
import pkg_resources
from prompt_toolkit import prompt

from bms.search import MochaSearchEngine


_logger = logging.getLogger(__package__)
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
def install(path: str, destdir: str) -> None:
    config = ConfigParser()
    config.read('bms.ini')
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
def amplify(path: str) -> None:
    expanded_path = os.path.expanduser(path)
    _amplify(expanded_path)


def _amplify(path: str) -> None:
    escaped_path = glob_escape(path)
    pattern = os.path.join(escaped_path, '*.bm[sel]')
    bms_iter = iglob(pattern)
