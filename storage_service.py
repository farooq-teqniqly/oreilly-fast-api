from azure.storage.blob.aio import BlobServiceClient
from pydantic import BaseModel, ValidationError


class StorageServiceError(Exception):
    pass


class StorageServiceArgumentError(StorageServiceError):
    pass


class StorageServiceValidationError(StorageServiceError):
    pass


class BlobUploadContext(BaseModel):
    content: str
    blob_name: str
    container_name: str

class ErrorMessages:
    MISSING_CONNECTION_STRING="Specify a connection string"
    MISSING_CONTAINER_NAME="Specify a container name"
    VALIDATION_ERROR="{class_name} validation failure"

class StorageService:
    def __init__(self, connection_string: str):
        if connection_string is None:
            raise StorageServiceArgumentError(ErrorMessages.MISSING_CONNECTION_STRING)

        self._connection_string = connection_string
        self._blob_service_client = None

    async def __aenter__(self):
        self._blob_service_client = BlobServiceClient.from_connection_string(
            self._connection_string)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._blob_service_client.close()

    async def upload_string(self, context: BlobUploadContext):
        try:
            context.model_validate(context)
        except ValidationError as e:
            raise StorageServiceValidationError(
                ErrorMessages.VALIDATION_ERROR.format(
                    class_name=BlobUploadContext)) from e

        container_client = self._blob_service_client.get_container_client(
            context.container_name)

        if not await container_client.exists():
            await container_client.create_container()

        blob_client = container_client.get_blob_client(context.blob_name)
        upload_result = await blob_client.upload_blob(context.content, overwrite=True)

        return upload_result

    async def list_blobs(self, container_name: str):
        if container_name is None:
            raise StorageServiceArgumentError(
                ErrorMessages.MISSING_CONTAINER_NAME)

        container_client = self._blob_service_client.get_container_client(
            container_name)

        async for blob in container_client.list_blobs():
            yield blob
