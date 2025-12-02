from __future__ import annotations

import urllib.parse
from io import BytesIO
from typing import IO, Any, Tuple

from aibots.models import File
from atlas.asgi.exceptions import AtlasAPIException
from atlas.environ import E
from atlas.mixins import FileHelpersMixin
from atlas.schemas import Uuid
from atlas.services import DBS, DS, S
from atlas.utils import run_sync_as_async
from beanie.odm.operators.find.comparison import In
from fastapi import status

from chats.models import FileDB

__all__ = ("FilesAPIMixin",)


class FilesAPIMixin(FileHelpersMixin):
    """
    Mixin for supporting File APIs

    Attributes
        atlas (AtlasASGIConfig): Atlas API config
        environ (AppraiserEnviron): Environment variables
        db (BeanieService): MongoDB Service
        s3 (S3Service): S3 Service
        cf (CloudfrontService): Cloudfront Service
        files (DS): Files dataset
        logger (StructLogService): Atlas logger
    """

    def __init__(self):
        super().__init__()

        self.environ: E = self.atlas.environ
        self.bucket: str = self.environ.cloudfront.bucket
        self.db: DBS = self.atlas.db
        self.s3: S = self.atlas.services.get("s3")
        self.cf: S = self.atlas.services.get("cloudfront")
        # TODO: Make this generic
        self.files: DS = self.atlas.db.atlas_dataset(FileDB.Settings.name)
        self.logger = self.atlas.logger

    def atlas_get_public_url(self, file_id: Uuid, filename: str) -> str:
        """
        Convenience function for retrieving the public CDN url
        to the file

        Args:
            file_id (Uuid): File ID
            filename (str): Name of the file

        Returns:
            str: Public CDN url
        """
        # Handling files with spaces
        filename: str = urllib.parse.quote(
            filename, safe="", encoding=None, errors=None
        )
        return (
            f"{self.environ.cloudfront.pub_url}"
            + f"files/{file_id}/{filename}"
        )

    async def atlas_validate_files(self, files: list[Uuid]) -> None:
        """
        Validates if the specified files exist

        Args:
            files (list[Uuid]): List of files to be validated

        Returns:
            None

        Raises:
            AtlasAPIException: If files do not exist
        """
        # Check all files exists
        retrieved: list[FileDB] = await self.files.get_items(
            In(FileDB.id, files)
        )
        if invalid_files := set(files) - {file.id for file in retrieved}:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Files do not exist",
                details={"id": list(invalid_files)},
            )

    async def atlas_get_file(self, file_id: Uuid) -> FileDB:
        """
        Retrieves and checks if the file exists

        Args:
            file_id (Uuid): File ID

        Returns:
            FileDB: File to be retrieved
        """
        # Retrieve and validate if file exists
        file: FileDB | None = await self.files.get_item_by_id(file_id)
        if not file:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="File does not exist",
                details={"id": file_id},
            )
        return file

    async def atlas_download_file(
        self, file: Uuid | FileDB
    ) -> Tuple[FileDB, Any]:
        """
        Downloads the specified file

        Args:
            file (Uuid | FileDB): File to be downloaded

        Returns:
            Tuple[FileDB, Any]: File details and contents
        """
        if isinstance(file, str):
            file: FileDB | None = await self.atlas_get_file(file)
        content = await run_sync_as_async(
            self.s3.get_object, **{"Bucket": self.bucket, "Key": file.content}
        )
        return file, content["Body"]

    async def atlas_delete_file(
        self,
        file_id: Uuid,
    ) -> None:
        """
        Convenience function to delete a file

        Args:
            file_id (Uuid): Uuid of the file

        Returns:
            None

        Raises:
            AtlasAPIException: If errors occur during the file deletion process
        """
        file: FileDB = await self.atlas_get_file(file_id)

        # Deletes the file from S3
        await run_sync_as_async(
            self.s3.delete_object,
            **{"Bucket": self.bucket, "Key": file.content},
        )

        # Deletes the file from DB
        if not await self.files.delete_item_by_id(file.id):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error deleting file",
            )

    def atlas_create_file(
        self,
        details: dict[str, Any],
        filename: str,
        filebytes: IO,
        content_type: str,
        user: Uuid,
        uid: Uuid | None = None,
    ) -> File:
        """
        Convenience function to create a file

        Args:
            details (dict[str, Any]): File metadata details
            filename (str): Name of the file
            filebytes (IO): File IO details
            content_type (str): Contents of the File
            user (Uuid): UUID of the user
            uid (Uuid | None): UUID of the file

        Returns:
            File: Generated file
        """
        file_details: dict[str, Any] = details.get(filename, {})

        # Initialise default variables
        if uid is None:
            uid: Uuid = File.atlas_get_uuid()
        version: int | str = file_details.get("version", 1)
        metadata: dict[str, Any] = file_details.get("metadata", {})
        folder: str = file_details.get("folder", "/")

        # Create a file
        f_meta: dict[str, Any] = {
            **{
                "filename": filename,
                "checksum": self.get_checksum(filebytes),
                "content_type": content_type,
            },
            **metadata,
        }
        return File.create_schema(
            user=user,
            uid=uid,
            resource_type=FileDB.Settings.name,
            location=str(self.environ.project.pub_url)
            + f"latest/files/cdn/{uid}",
            version=version,
            **{
                "name": f_meta["filename"],
                "content": f"files/{uid}/{f_meta['filename']}",
                "folder": folder,
                "versions": [version],
                "metadata": f_meta,
            },
        )

    async def atlas_upload_file(self, file: File, filebytes: IO) -> None:
        """
        Convenience function to upload file to S3

        Args:
            file (File): Prepared file
            filebytes (IO): Raw file details

        Returns:
            None
        """
        # Upload file
        await run_sync_as_async(
            self.s3.upload_fileobj,
            **{
                "Fileobj": BytesIO(filebytes.read()),
                "Bucket": self.bucket,
                "Key": file.content,
                "ExtraArgs": {
                    "ContentType": file.metadata["content_type"],
                    "Metadata": {"checksum": file.metadata["checksum"]},
                },
            },
        )
