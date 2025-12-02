from __future__ import annotations

from io import StringIO
from typing import Any, Dict

from boto3 import client


class S3File:
    """
    class for wrapping boto3 S3 file getters
    """

    def __init__(self, bucket: str, file_key: str, s3_client=None) -> None:
        self.bucket = bucket
        self.file_key = file_key
        self.s3 = client("s3") if s3_client is None else s3_client

    def get_file(
        self, decode: bool = True, encoding: str = "utf-8"
    ) -> StringIO:
        """
        gets files from s3 bucket organised in "bot" folders
        Args:
            bot (str): id of the bot
            file_key (str): filename
        Returns:
            StringIO: bytes of file to use
        """
        s3_response: Dict[str, Any] = self.s3.get_object(
            Bucket=self.bucket, Key=self.file_key
        )
        if decode:
            file_data = s3_response["Body"].read().decode(encoding)
        else:
            # docx, pptx and other files do not require decoding to be parsed
            return s3_response["Body"].read()
        return StringIO(file_data)

    def get_last_modified(self) -> str:
        """
        gets the last modified datetime of a file in s3 bucket
        Returns:
            (str): string of last modified datetime
        """
        file_data = self.s3.head_object(Bucket=self.bucket, Key=self.file_key)
        return file_data["LastModified"]
