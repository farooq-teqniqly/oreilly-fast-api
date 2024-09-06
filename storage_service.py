from azure.storage.blob.aio import BlobServiceClient

class StorageService:
    def __init__(self, connection_string: str):
        self._connection_string = connection_string

    async def upload_json(self):
        blob_client = BlobServiceClient.from_connection_string(self._connection_string)

        async with blob_client:
            