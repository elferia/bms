from io import BytesIO
from logging import getLogger
from typing import Optional, Tuple
import webbrowser

from prompt_toolkit import prompt
import requests


_logger = getLogger(__package__)
session = requests.Session()


def download_url(url: str) -> Optional[Tuple[str, BytesIO]]:
    response = session.head(url)
    content_type = response.headers.get('Content-Type', 'text/html')
    content_type = content_type.split(';', 1)[0].casefold()
    if content_type == 'text/html':
        yn = prompt(
            'Song URL is for website. Open in browser? [y/n]: ',
            default='y')
        if yn == 'y':
            webbrowser.open_new_tab(url)
    else:
        _logger.debug('%s Content-Type: %s', url, content_type)
        response = session.get(url, stream=True)
        file = BytesIO()
        for b in response.iter_content(None):
            file.write(b)
        file.seek(0)
        return content_type, file
