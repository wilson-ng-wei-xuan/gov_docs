import pathlib
import re
from typing import Dict, List, Tuple

from email_validator import validate_email, EmailNotValidError

from app.utils.file_util import hash_by_md5


def validate_email_address(email: str, validate_domain=False) -> bool:
    """
    Validate an email address.
    """
    # pattern = r'([A-Za-z0-9]+[-.-_])*[A-Za-z0-9]+@[-A-Za-z0-9-]+(\.[-A-Z|a-z]{2,})+'
    # if re.match(pattern, email):
    #     return True
    # return False
    try:
        email = validate_email(email, check_deliverability=validate_domain).email
        return True
    except EmailNotValidError as e:
        # email is not valid, exception message is human-readable
        print(str(e))
        return False


def find_placeholders_in_text(org_str: str, pattern='{{([a-zA-Z0-9_-]+)}}') -> List[str]:
    """
    File all placeholders {{*}} in a string.
    """
    return re.findall(pattern, org_str)


def replace_all_substrings(text: str, dic: Dict[str, str]) -> str:
    """
    Replace all placeholders in the text
    Args:
        text: original text
        dic: Dictionary with key=old-substring value=new-substring
    Return:
        Updated text
    """
    for old_str, new_str in dic.items():
        text = text.replace(old_str, new_str)
    return text


def find_and_replace_placeholders(text: str, replacements: Dict[str, str]) -> str:
    """
    Replace placeholders marked within {{}}
    """
    placeholders = find_placeholders_in_text(
        text, pattern='{{([a-zA-Z0-9_-]+)}}')
    dic = {f'{{{{{k}}}}}': replacements[k] for k in placeholders}
    return replace_all_substrings(text, dic)


def replace_image_urls_with_cid_in_html(html_code: str) -> Tuple[Dict, str]:
    """
    Extract image urls in a HTML file, and replace the url with "cid: <md5 of url>".
    It works with following tags
    - <img src=""/> 
    - <td background=""/>
    - <td width="50%" style="background-image: url('https://api.capdev.link/v1/moonshot/download_file/dGhhbmcua2lldUAyMzU5bWVkaWEuY29tL2ltYWdlcy8yMDIxMTEwODAwNTIxM19pbWFnZTAwMi5qcGVn'); margin: 0px; padding: 0px; vertical-align: top; box-sizing: content-box;">
    Returns: dictionary of md5 to image urls, and the updated_html
    """
    PATTERN_URL = r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"

    PATTERN_BG_URL = f"(<(?:table|tr|td)\s[^>]*?background\s*=\s*(?:'|\"|&quot;)){PATTERN_URL}((?:'|\"|&quot;)[^>]*?>)"
    PATTERN_IMG_URL = f"(<img\s[^>]*?src\s*=\s*(?:'|\"|&quot;)){PATTERN_URL}((?:'|\"|&quot;)[^>]*?>)"
    PATTERN_BGIMG_URL = f"(background-image:\s*url\((?:&quot;|')){PATTERN_URL}((?:&quot;|')\))"

    image_urls = {}
    patterns = [PATTERN_BG_URL, PATTERN_IMG_URL, PATTERN_BGIMG_URL]
    for pattern in patterns:
        while re.search(pattern, html_code):
            m = re.search(pattern, html_code)
            url = m[2]
            image_cid = hash_by_md5(url)
            image_urls[image_cid] = url
            position = m.start()
            html_code = html_code[:position] + \
                        re.sub(pattern, f"\\1cid:{image_cid}\\3",
                               html_code[position:], count=1)

    # Remove empty string
    return image_urls, html_code


def extract_images_in_html(html_code: str):
    """
    Extract image urls and files used in a HTML file, it works with following tags
    - <img src=""/>
    - <td background=""/>
    - <td width="50%" style="background-image: url('https://api.capdev.link/v1/moonshot/download_file/dGhhbmcua2lldUAyMzU5bWVkaWEuY29tL2ltYWdlcy8yMDIxMTEwODAwNTIxM19pbWFnZTAwMi5qcGVn'); margin: 0px; padding: 0px; vertical-align: top; box-sizing: content-box;">
    - <td width="50%" style="background-image: url('/themes/Blue/images/text/1.png'); margin: 0px; padding: 0px; vertical-align: top; box-sizing: content-box;">
    Returns: list of url, list of file_path
    """
    PATTERN_URL = "(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"
    PATTERN_FILE = "(\/{0,1}(((\w)|(\.)|(\\\s))+\/)*((\w)|(\.)|(\\\s))+)"

    PATTERN_BG_URL = f"<td\s[^>]*?background\s*=\s*['\"]{PATTERN_URL}['\"][^>]*?>"
    PATTERN_BG_FILE = f"<td\s[^>]*?background\s*=\s*['\"]{PATTERN_FILE}['\"][^>]*?>"

    PATTERN_IMG_URL = f"<img\s[^>]*?src\s*=\s*['\"]{PATTERN_URL}['\"][^>]*?>"
    PATTERN_IMG_FILE = f"<img\s[^>]*?src\s*=\s*['\"]{PATTERN_FILE}['\"][^>]*?>"

    PATTERN_BGIMG_URL = f"background-image:\s*url\(['\"]{PATTERN_URL}['\"]\)"
    PATTERN_BGIMG_FILE = f"<td\s[^>]*?\s*background-image:\s*url\(['\"]{PATTERN_FILE}['\"]\)"

    result_urls = []
    patterns = [PATTERN_BG_URL, PATTERN_IMG_URL, PATTERN_BGIMG_URL]
    for pattern in patterns:
        result_urls.extend(re.findall(pattern, html_code))

    result_files = []
    patterns = [PATTERN_BG_FILE, PATTERN_IMG_FILE, PATTERN_BGIMG_FILE]
    for pattern in patterns:
        for item in re.findall(pattern, html_code):
            if len(item) > 0:
                # Only take first group in each match
                result_files.append(item[0])

    # Remove empty string
    result_urls = [item for item in result_urls if item]
    result_files = [item for item in result_files if item]
    return result_urls, result_files


if __name__ == '__main__':
    folder = pathlib.Path(__file__).resolve().parent
    file = folder.joinpath('../../docs/moonshot/edm.html')

    with open(file) as f:
        html = f.read()
    result = extract_images_in_html(html)
    print(result)

    file = folder.joinpath('../../test/thang_updated_2.html')

    with open(file) as f:
        html = f.read()
    result = replace_image_urls_with_cid_in_html(html)
    print(result[0])
    print(result[1])

    with open('temp.html', 'w') as f:
        f.write(result[1])

    # result = find_placeholders_in_text('Hello {{who}} world {{where_abc}} is good')
    # print(result)
    # result = find_placeholders_in_text('Hello is good')
    # print(result)
