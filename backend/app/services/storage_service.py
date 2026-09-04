import logging
from io import BytesIO

from minio import Minio

from app.core.config import settings

logger = logging.getLogger(__name__)

client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)


def ensure_bucket() -> None:
    """Create the bucket if it does not already exist."""
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)
        logger.info("Created MinIO bucket: %s", settings.MINIO_BUCKET)


def upload_file(file_data: bytes, storage_key: str, content_type: str) -> None:
    """Upload raw bytes to MinIO under the given storage_key."""
    ensure_bucket()
    client.put_object(
        settings.MINIO_BUCKET,
        storage_key,
        BytesIO(file_data),
        length=len(file_data),
        content_type=content_type,
    )
    logger.debug("Uploaded %d bytes to MinIO key: %s", len(file_data), storage_key)


def get_file(storage_key: str):
    """Return a streaming MinIO response object for the given key."""
    ensure_bucket()
    return client.get_object(
        settings.MINIO_BUCKET,
        storage_key,
    )


def download_file_bytes(storage_key: str) -> bytes:
    """Download a file from MinIO and return its content as bytes.

    Used by the Celery pipeline to fetch documents for processing.
    """
    ensure_bucket()
    response = client.get_object(settings.MINIO_BUCKET, storage_key)
    try:
        data = response.read()
        logger.debug(
            "Downloaded %d bytes from MinIO key: %s", len(data), storage_key
        )
        return data
    finally:
        response.close()
        response.release_conn()