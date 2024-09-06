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

class AdoService:
    def __init__(self, config: AdoServiceConfiguration):
        try:
            AdoServiceConfiguration.model_validate(config)
        except ValidationError as e:
            raise AdoServiceValidationException("AdoServiceConfiguration validation failed") from e

        self._base_address = config.base_address
        self._org_name = config.org_name
        self._auth = aiohttp.BasicAuth("", config.personal_access_token)
        
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
    
    async def get_pull_requests(self, project_name: str, repository_name: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self._base_address}/{self._org_name}/{project_name}/_apis/git/repositories/{repository_name}/pullrequests?api-version=7.1-preview.1&$top=1000&searchCriteria.status=All&searchCriteria.minTime=2024-03-01T00:00:00Z&searchCriteria.maxTime=2024-09-0410T00:00:00Z", 
                auth=self._auth) as response:
                
                if response.status == 203:
                    raise AdoServiceInvalidPATException("Personal Access Token might be incorrect.")
                
                if response.status == 404:
                    raise AdoServiceInvalidUrlException("ADO REST API url might be incorrect.")
                
                return await response.json()