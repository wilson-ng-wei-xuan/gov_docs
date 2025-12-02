import io
import logging
import zipfile
from pathlib import PurePosixPath

import boto3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class S3File(io.RawIOBase):
    def __init__(self, s3_object):
        self.s3_object = s3_object
        self.position = 0

    def __repr__(self):
        return "<%s s3_object=%r>" % (type(self).__name__, self.s3_object)

    @property
    def size(self):
        return self.s3_object.content_length

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            self.position = offset
        elif whence == io.SEEK_CUR:
            self.position += offset
        elif whence == io.SEEK_END:
            self.position = self.size + offset
        else:
            raise ValueError("invalid whence (%r, should be %d, %d, %d)" % (
                whence, io.SEEK_SET, io.SEEK_CUR, io.SEEK_END
            ))

        return self.position

    def seekable(self):
        return True

    def read(self, size=-1):
        if size == -1:
            # Read to the end of the file
            range_header = "bytes=%d-" % self.position
            self.seek(offset=0, whence=io.SEEK_END)
        else:
            new_position = self.position + size

            # If we're going to read beyond the end of the object, return
            # the entire object.
            if new_position >= self.size:
                return self.read()

            range_header = "bytes=%d-%d" % (self.position, new_position - 1)
            self.seek(offset=size, whence=io.SEEK_CUR)

        return self.s3_object.get(Range=range_header)["Body"].read()

    def readable(self):
        return True


def extract_s3_zip_file(src_bucket: str, src_key: str, target_folder: str, target_bucket: str = None):
    """
    Extract a s3 zip file to a folder
    """
    s3_resource = boto3.resource("s3")
    if target_bucket is None:
        target_bucket = src_bucket
    s3_object = s3_resource.Object(bucket_name=src_bucket, key=src_key)
    s3_file = S3File(s3_object)

    with zipfile.ZipFile(s3_file) as z:
        p = PurePosixPath(target_folder)
        result = []
        for filename in z.namelist():
            file_info = z.getinfo(filename)
            logger.info(file_info)
            dest_key = str(p.joinpath(filename))
            result.append(dest_key)
            s3_resource.meta.client.upload_fileobj(
                z.open(filename),
                Bucket=target_bucket,
                Key=dest_key
            )
        return result
