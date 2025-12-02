from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ParseableFileType(str, Enum):
    """Enum for files that can be parsed"""

    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    TXT = "txt"
    HTML = "html"
    PDF = "pdf"
    CSV = "csv"


class ParsedPage(BaseModel):
    """
    Model for RAG Parsed Page, standardised format for parsed product
    """

    text: str
    metadata: Dict[str, Any]


class ParseConfig(BaseModel):
    """
    Model for RAG Parse Configuration
    Attributes:
        file_type (ParesableFileType):
            string of file extension to be parse/parsed
        bucket (str): name of bucket to get file
        bot (str): bot id
        file_key: name of file to process
    """

    type: ParseableFileType
    bucket: str
    bot: str
    file_key: str
    chunk_size: Optional[int] = None
