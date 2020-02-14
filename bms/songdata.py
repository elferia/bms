from os.path import join as joinpath
import sqlite3
from urllib.parse import quote as urlquote, urlencode, urlunparse


def connect(beatoraja_path: str) -> None:
    global cursor
    path = joinpath(beatoraja_path, 'songdata.db')
    path = urlquote(path)
    qs = urlencode(dict(mode='ro'))
    uri = urlunparse(('file', '', path, '', qs, ''))
    conn = sqlite3.connect(uri, uri=True)
    cursor = conn.cursor()


def exists(md5: str) -> bool:
    cursor.execute('select * from song where md5=:md5', dict(md5=md5))
    return cursor.fetchone() is not None
