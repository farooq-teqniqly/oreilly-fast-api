import aiohttp
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
        self._auth = aiohttp.BasicAuth("", config.personal_access_token.get_secret_value())
        
    async def get_projects(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self._base_address}/{self._org_name}/_apis/projects?api-version=7.1-preview.1", 
                auth=self._auth) as response:
                
                if response.status == 203:
                    raise AdoServiceInvalidPATException("Personal Access Token might be incorrect.")
                
                if response.status == 404:
                    raise AdoServiceInvalidUrlException("ADO REST API url might be incorrect.")
                
                return await response.json()
    
    async def get_pull_requests(self, context: RepositoryContext):
        try:
            RepositoryContext.model_validate(context)
        except ValidationError as e:
            raise AdoServiceValidationException("AdoServiceConfiguration validation failed") from e

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self._base_address}/{self._org_name}/{context.project_name}/_apis/git/repositories/{context.repository_name}/pullrequests?api-version=7.1-preview.1&$top=1000&searchCriteria.status=All&searchCriteria.minTime=2024-03-01T00:00:00Z&searchCriteria.maxTime=2024-09-0410T00:00:00Z",
                auth=self._auth) as response:
                
                if response.status == 203:
                    raise AdoServiceInvalidPATException("Personal Access Token might be incorrect.")
                
                if response.status == 404:
                    raise AdoServiceInvalidUrlException("ADO REST API url might be incorrect.")

                return await response.json()

async def main():
    import os
    from dotenv import load_dotenv

    load_dotenv()

    ado_service_config = AdoServiceConfiguration(
        base_address=os.getenv("ADO__BASE_ADDRESS"),
        organization_name=os.getenv("ADO__ORG"),
        personal_access_token=os.getenv("ADO__PAT"),
    )

    ado_service = AdoService(ado_service_config)

    repository_context = RepositoryContext(
        repository_name=os.getenv("ADO__REPO"),
        project_name=os.getenv("ADO__PROJECT"),
    )

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