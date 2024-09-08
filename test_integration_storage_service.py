import json
import os
import unittest

from dotenv import load_dotenv

from storage_service import BlobUploadContext, StorageService


class TestIntegrationStorageService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        load_dotenv()
        connection_string = os.getenv("AZURE_BLOB_CONNECTION_STRING")
        self._storage_service = await StorageService(connection_string).__aenter__()

    async def asyncTearDown(self):
        await self._storage_service.__aexit__(None, None, None)

    async def test_can_upload_string_and_list_blob(self):
        container_name = "itegrationtestcontainer"
        blob_name = "person"

        content = {
            "name": "Bubba",
            "age": 77,
        }

        context = BlobUploadContext(
            blob_name=blob_name,
            container_name=container_name,
        )

        upload_result = await self._storage_service.upload_string(
            json.dumps(content),
            context)

        assert upload_result is not None

if __name__ == "__main__":
    unittest.main()
