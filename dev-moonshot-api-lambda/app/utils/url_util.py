import base64
from pathlib import Path
from urllib.parse import urlparse

import requests

from app.utils.file_util import hash_by_md5


def is_valid_url(url: str):
    """
    Validate an URL
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def get_content_as_base64(url: str) -> str:
    """
    Get the content from an URL and return its base64bit-encoded data.
    """
    return str(base64.b64encode(requests.get(url).content))


def get_url_content_type_from_header(url: str) -> str:
    """
    Get content type of an URL.
    If content type is text or html, it is not downloadable.
    Note: This method does not work for all redirected links if server does not respond to a HEAD request
    """
    response = requests.head(url, allow_redirects=True)
    header = response.headers
    content_type = header.get('content-type')
    return content_type.lower()


def is_downloadable(url: str) -> bool:
    """
    Get content type of an URL.
    If content type is text or html, it is not downloadable.
    """
    content_type = get_url_content_type_from_header(url)
    if 'text' in content_type:
        return False
    if 'html' in content_type:
        return False
    return True


def download_file_from_url(url: str, folder_path: str, file_name: str = None, file_stem: str = None) -> str:
    """
    Download file from a URL.
    If file_name is not provided, file name is assigned with the md5 hash on the URL.
    File extension is derived from content-type.
    Returns file_path of the downloaded file.
    """
    # Get content from URL
    response = requests.get(url, stream=True)
    content_type = response.headers.get('content-type').lower()
    file_ext = content_type.split('/')[-1]

    if not file_name:
        if not file_stem:
            file_stem = hash_by_md5(url)
        file_name = f'{file_stem}.{file_ext}'
    file_path = Path(folder_path).joinpath(file_name)
    file_path = str(file_path)
    with open(file_path, 'wb') as f:
        f.write(response.content)
    return file_path


if __name__ == '__main__':
    print(is_valid_url('http://www.google.com'))
    url = 'https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png'
    content_type = get_url_content_type_from_header(url)
    file_ext = content_type.split('/')[-1]
    file_stem = hash_by_md5(url)
    with open(f'{file_stem}.{file_ext}', 'wb') as f:
        f.write(requests.get(url).content)
