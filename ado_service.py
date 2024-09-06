from idlelib.window import add_windows_to_menu

import aiohttp
from aiohttp import ClientTimeout
from pydantic import BaseModel, ValidationError, HttpUrl, SecretStr

class AdoServiceException(Exception):
    pass

class AdoServiceInvalidPATException(AdoServiceException):
    pass

class AdoServiceInvalidUrlException(AdoServiceException):
    pass

class AdoServiceValidationException(AdoServiceException):
    pass

class AdoServiceConfiguration(BaseModel):
    base_address: HttpUrl
    organization_name: str
    personal_access_token: SecretStr
    http_timeout: int=60

class RepositoryContext(BaseModel):
    repository_name: str
    project_name: str

class AdoService:
    def __init__(self, config: AdoServiceConfiguration):
        try:
            AdoServiceConfiguration.model_validate(config)
        except ValidationError as e:
            raise AdoServiceValidationException("AdoServiceConfiguration validation failed") from e

        self._base_address = config.base_address
        self._org_name = config.organization_name
        auth = aiohttp.BasicAuth("", config.personal_access_token.get_secret_value())
        self._http_session = aiohttp.ClientSession(auth=auth, timeout=ClientTimeout(config.http_timeout))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_session.close()

    async def get_projects(self):
        url = f"{self._base_address}/{self._org_name}/_apis/projects?api-version=7.1-preview.1"
        return await self._make_request(url)
    
    async def get_pull_requests(self, context: RepositoryContext):
        try:
            RepositoryContext.model_validate(context)
        except ValidationError as e:
            raise AdoServiceValidationException("RepositoryContext validation failed") from e

        url = f"{self._base_address}/{self._org_name}/{context.project_name}/_apis/git/repositories/{context.repository_name}/pullrequests?api-version=7.1-preview.1&$top=1000&searchCriteria.status=All&searchCriteria.minTime=2024-03-01T00:00:00Z&searchCriteria.maxTime=2024-09-0410T00:00:00Z"
        return await self._make_request(url)

    async def _make_request(self, url: str):
        try:
            async with self._http_session.get(url) as response:
                if response.status == 203:
                    raise AdoServiceInvalidPATException("Personal Access Token might be incorrect.")
                if response.status == 404:
                    raise AdoServiceInvalidUrlException("ADO REST API URL might be incorrect.")
                if response.status != 200:
                    raise AdoServiceException(f"ADO REST API request failed with status: {response.status}")
                return await response.json()
        except aiohttp.ClientError as e:
            raise AdoServiceException(f"ADO REST API request failed") from e

async def main():
    import os
    from dotenv import load_dotenv

    load_dotenv()

    http_timeout = os.getenv("ADO__HTTP_TIMEOUT_SECONDS")

    if http_timeout is None:
        http_timeout=60

    ado_service_config = AdoServiceConfiguration(
        base_address=os.getenv("ADO__BASE_ADDRESS"),
        organization_name=os.getenv("ADO__ORG"),
        personal_access_token=os.getenv("ADO__PAT"),
        http_timeout = http_timeout,
    )

    repository_context = RepositoryContext(
        repository_name=os.getenv("ADO__REPO"),
        project_name=os.getenv("ADO__PROJECT"),
    )

    async with AdoService(ado_service_config) as ado_service:
        tasks = [
            ado_service.get_projects(),
            ado_service.get_pull_requests(repository_context),
        ]

        results = await asyncio.gather(*tasks)

        for result in results:
            print(f"Task completed with result: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())