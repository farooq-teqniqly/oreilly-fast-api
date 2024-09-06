from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from pydantic import BaseModel, ValidationError

class StorageServiceException(Exception):
    pass

class StorageServiceArgumentException(StorageServiceException):
    pass

class StorageServiceValidationException(StorageServiceException):
    pass

class BlobUploadContext(BaseModel):
    content: str
    blob_name: str
    container_name: str

class StorageService:
    def __init__(self, connection_string: str):
        if connection_string is None:
            raise StorageServiceArgumentException("Specify a connection string")

        self._connection_string = connection_string
        self._blob_service_client = None

    async def __aenter__(self):
        self._blob_service_client = BlobServiceClient.from_connection_string(self._connection_string)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._blob_service_client.close()

    async def upload_string(self, context: BlobUploadContext):
        container_client = self._blob_service_client.get_container_client(context.container_name)

        if not await container_client.exists():
            await container_client.create_container()

        blob_client = container_client.get_blob_client(context.blob_name)
        upload_result = await blob_client.upload_blob(context.content, overwrite=True)

        return upload_result

    async def list_blobs(self, container_name: str):
        if container_name is None:
            raise StorageServiceArgumentException("Specify a container name")

        container_client = self._blob_service_client.get_container_client(container_name)

        async for blob in container_client.list_blobs():
            yield blob

async def main():
    import json
    import os
    from dotenv import load_dotenv

    load_dotenv()
    try:
        async with StorageService(os.getenv("AZURE_BLOB_CONNECTION_STRING")) as storage_service:
            container_name = "pythontest"

            dct = {
                "name": "Bubba",
                "age": 77
            }

            blob_content = json.dumps(dct)

            try:
                upload_context = BlobUploadContext(
                    content=blob_content,
                    blob_name="bubba",
                    container_name=container_name,
                )
            except ValidationError as e:
                raise StorageServiceValidationException("BlobUploadContext validation failure") from e

            upload_result = await storage_service.upload_string(upload_context)

            print(upload_result)
            blobs = storage_service.list_blobs(container_name)

            async for blob in blobs:
                print(blob)
    except Exception as e:
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())