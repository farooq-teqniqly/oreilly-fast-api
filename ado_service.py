import aiohttp

class InvalidPATException(Exception):
    pass

class InvalidUrlException(Exception):
    pass

class AdoService:
    def __init__(self, base_address: str, org_name: str, personal_access_token: str):
        self._base_address = base_address
        self._org_name = org_name        
        self._auth = aiohttp.BasicAuth("", personal_access_token)
        
    async def get_projects(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self._base_address}/{self._org_name}/_apis/projects?api-version=7.1-preview.1", 
                auth=self._auth) as response:
                
                if response.status == 203:
                    raise InvalidPATException("Personal Access Token might be incorrect.")
                
                if response.status == 404:
                    raise InvalidUrlException("ADO REST API url might be incorrect.")
                
                return await response.json()
    
    async def get_pull_requests(self, project_name: str, repository_name: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self._base_address}/{self._org_name}/{project_name}/_apis/git/repositories/{repository_name}/pullrequests?api-version=7.1-preview.1&$top=1000&searchCriteria.status=All&searchCriteria.minTime=2024-03-01T00:00:00Z&searchCriteria.maxTime=2024-09-0410T00:00:00Z", 
                auth=self._auth) as response:
                
                if response.status == 203:
                    raise InvalidPATException("Personal Access Token might be incorrect.")
                
                if response.status == 404:
                    raise InvalidUrlException("ADO REST API url might be incorrect.")
                
                return await response.json()
            
async def main():
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    ado_service = AdoService(
        os.getenv("ADO__BASE_ADDRESS"),
        os.getenv("ADO__ORG"), 
        os.getenv("ADO__PAT"))
    
    projects = await ado_service.get_projects()
    pull_requests = await ado_service.get_pull_requests(os.getenv("ADO__PROJECT"), os.getenv("ADO__REPO"))
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())