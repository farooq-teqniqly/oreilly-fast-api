import aiohttp

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
    print(projects)
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())