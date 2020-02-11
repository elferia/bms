import webbrowser

from prompt_toolkit import prompt
import requests


session = requests.Session()


def download_url(url: str) -> None:
    response = session.head(url)
    content_type = response.headers.get('Content-Type', 'text/html')
    if content_type.casefold() == 'text/html':
        yn = prompt(
            'Song URL is for website. Open in browser? [y/n]: ',
            default='y')
        if yn == 'y':
            webbrowser.open_new_tab(url)
    else:
        raise NotImplementedError
