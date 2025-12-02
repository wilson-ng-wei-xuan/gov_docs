from __future__ import annotations

import re
import unicodedata


def convert_string_to_url(string):
    # Normalize the string to NFKD form
    value = unicodedata.normalize("NFKD", string)
    # Encode to ASCII bytes, ignoring non-ASCII characters
    value = value.encode("ascii", "ignore").decode("ascii")
    # Remove non-word characters and convert to lowercase
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    # Replace spaces and hyphens with a single hyphen
    return re.sub(r"[-\s]+", "-", value)
