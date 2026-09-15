from django.conf import settings
from azure.storage.blob import BlobServiceClient, ContentSettings
from receipts.exceptions import BlobUploadError


class BlobService:
    def __init__(self):
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        self.client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        self.container_client = self.client.get_container_client(
            self.container_name
        )

    def upload(self, file_obj, blob_name: str, content_type: str) -> str:
        try:
            file_obj.seek(0)
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.upload_blob(
                file_obj,
                overwrite=True,
                raw_response_hook=None,
                content_settings=ContentSettings(content_type=content_type)
            )
            return blob_name
        except Exception as e:
            raise BlobUploadError(f"Failed to upload blob: {str(e)}")

    def download(self, blob_name: str) -> bytes:
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            return blob_client.download_blob().readall()
        except Exception as e:
            raise BlobUploadError(f"Failed to download blob: {str(e)}")

    def delete(self, blob_name: str) -> None:
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
        except Exception as e:
            raise BlobUploadError(f"Failed to delete blob: {str(e)}")
