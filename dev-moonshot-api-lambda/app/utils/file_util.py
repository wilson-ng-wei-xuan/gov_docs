import base64
import csv
import hashlib
import os
import random
from typing import Dict, List


def hash_by_md5(original: str) -> str:
    """
    Use MD5 to generate a file name from URL
    """
    hash_object = hashlib.md5(original.encode())
    md5_hash = hash_object.hexdigest()
    return md5_hash


def remove_prefix(s, prefix: str) -> str:
    """Remove a prefix from a string"""
    return s[len(prefix):] if s.startswith(prefix) else s


def b64encode_string(plain: str) -> str:
    """
    Encode a string into base64 encoded string.
    """
    return base64.b64encode(plain.encode('utf-8')).decode('utf-8')


def b64decode_string(encoded: str) -> str:
    """
    Decode a string from its base64 encoded string.
    """
    return base64.b64decode(encoded.encode('utf-8')).decode('utf-8')


def recursive_glob(root_folder, file_ends_with='', output_relative_path=True):
    """
    Return recursive list of files in root_folder
    :param root_folder: Folder to look into
    :param file_ends_with: Filter files by ending string, use '' to match all files
    :param output_relative_path: Output relative path if True, else output absolute path
    :return: List of file paths
    """
    result = [os.path.join(dirpath, f)
              for dirpath, dirnames, files in os.walk(root_folder)
              for f in files if f.endswith(file_ends_with)]
    if output_relative_path:
        result = [os.path.relpath(x, root_folder) for x in result]
    return result


def read_csv_to_dict(filename: str) -> List[Dict]:
    """
    Read an csv file with header and return a dictionary with header as the key.
    """
    try:
        with open(filename) as f:
            file_data = csv.reader(f, skipinitialspace=True)
            headers = next(file_data)
            return [dict(zip(headers, i)) for i in file_data if i]
    except Exception as ex:
        raise


def read_random_line_from_file(file_path: str) -> str:
    """
    Read a random line from a text file.
    """
    with open(file_path, "rt") as f:
        total_bytes = os.path.getsize(file_path)
        f.seek(random.randint(0, total_bytes))
        f.readline()  # read everything up until the next newline and discard the result
        return f.readline().strip()


if __name__ == '__main__':
    folder = os.path.abspath(os.path.join('..'))
    print(folder)
    result = recursive_glob(folder, '', True)
    print(result)

    x = read_csv_to_dict('test.csv')
    print(x)
