from datetime import datetime, timezone

import aiohttp
import tenacity
from aiohttp import ClientTimeout
from aiohttp.client_exceptions import (
    ClientConnectionError,
    ClientResponseError,
    ServerTimeoutError,
)
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, HttpUrl, SecretStr, ValidationError, field_validator
from tenacity import retry, stop_after_attempt, wait_exponential_jitter


class AdoServiceError(Exception):
    pass


class AdoServiceInvalidPATError(AdoServiceError):
    pass


class AdoServiceInvalidUrlError(AdoServiceError):
    pass


class AdoServiceValidationError(AdoServiceError):
    pass


class AdoServiceConfiguration(BaseModel):
    base_address: HttpUrl
    organization_name: str
    personal_access_token: SecretStr
    http_timeout: int = 60


class RepositoryContext(BaseModel):
    repository_name: str
    project_name: str

class PullRequestQueryParameters(BaseModel):
    top: int = 1000
    min_time: str
    max_time: str

    @field_validator("min_time", "max_time")
    @classmethod
    def check_iso8601_format(cls, value):
        try:
            isoparse(value)
        except ValueError as e:
            raise AdoServiceValidationError(
                ErrorMessages.DATE_FORMAT_INVALID.format(value=value)) from e
        return value

class ErrorMessages:
    VALIDATION_ERROR = "{class_name} validation failed."
    ADO_PAT_ERROR= "Personal Access Token might be incorrect."
    ADO_URL_ERROR= "ADO REST API URL might be incorrect."
    ADO_HTTP_REQUEST_FAILED="ADO REST API request failed with status: {status}"
    ADO_HTTP_CLIENT_ERROR="ADO REST API request failed due to connection issues"
    HTTP_TIMEOUT="ADO REST API request timed out"
    DATE_FORMAT_INVALID="{value} is not in ISO-8601 format"
class AdoService:
    def __init__(self, config: AdoServiceConfiguration):
        try:
            AdoServiceConfiguration.model_validate(config)
        except ValidationError as e:
            raise AdoServiceValidationError(
                ErrorMessages.VALIDATION_ERROR.format(
                    class_name="AdoServiceConfiguration")) from e

        self._base_address = config.base_address
        self._org_name = config.organization_name
        auth = aiohttp.BasicAuth("", config.personal_access_token.get_secret_value())

        self._http_session = aiohttp.ClientSession(
            auth=auth,
            timeout=ClientTimeout(config.http_timeout))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_session.close()

    async def get_projects(self):
        url = (f"{self._base_address}/"
               f"{self._org_name}/"
               f"_apis/projects?api-version=7.1-preview.1")

        return await self._make_request(url)

    async def get_pull_requests(
            self,
            context: RepositoryContext,
            query_params: PullRequestQueryParameters):
        try:
            RepositoryContext.model_validate(context)
        except ValidationError as e:
            raise AdoServiceValidationError(
                ErrorMessages.VALIDATION_ERROR.format(
                    class_name="RepositoryContext")) from e

        try:
            PullRequestQueryParameters.model_validate(query_params)
        except ValidationError as e:
            raise AdoServiceValidationError(
                ErrorMessages.VALIDATION_ERROR.format(
                    class_name="PullRequestQueryParameters")) from e

        url = (f"{self._base_address}/{self._org_name}/{context.project_name}"
               f"/_apis/git/repositories/"
               f"{context.repository_name}"
               f"/pullrequests?api-version=7.1-preview.1&"
               f"$top={query_params.top}&"
               f"searchCriteria.status=All&"
               f"searchCriteria.minTime={query_params.min_time}&"
               f"searchCriteria.maxTime={query_params.max_time}")

        return await self._make_request(url)

    @retry(stop=stop_after_attempt(3),
           wait=wait_exponential_jitter(jitter=1, initial=4, max=10),
           retry=(tenacity.retry_if_exception_type(ClientConnectionError) |
                  tenacity.retry_if_exception_type(ServerTimeoutError)))
    async def _make_request(self, url: str):
        try:
            async with self._http_session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10)) as response:

                if response.status == 203:
                    raise AdoServiceInvalidPATError(
                        ErrorMessages.ADO_PAT_ERROR)
                if response.status == 404:
                    raise AdoServiceInvalidUrlError(
                        ErrorMessages.ADO_URL_ERROR)
                if response.status != 200:
                    raise AdoServiceError(
                        ErrorMessages.ADO_HTTP_REQUEST_FAILED.format(
                            status=response.status))

                return await response.json()
        except ClientResponseError as e:
            raise AdoServiceError(
                ErrorMessages.ADO_HTTP_REQUEST_FAILED.format(
                    status=e.status)) from e
        except ClientConnectionError as e:
            raise AdoServiceError(
                ErrorMessages.ADO_HTTP_CLIENT_ERROR) from e
        except ServerTimeoutError as e:
            raise AdoServiceError(ErrorMessages.HTTP_TIMEOUT) from e
        except aiohttp.ClientError as e:
            raise AdoServiceError(
                ErrorMessages.ADO_HTTP_CLIENT_ERROR) from e

async def main():
    import os

    from dotenv import load_dotenv

    load_dotenv()

    http_timeout = os.getenv("ADO__HTTP_TIMEOUT_SECONDS")

    if http_timeout is None:
        http_timeout = 60

    ado_service_config = AdoServiceConfiguration(
        base_address=os.getenv("ADO__BASE_ADDRESS"),
        organization_name=os.getenv("ADO__ORG"),
        personal_access_token=os.getenv("ADO__PAT"),
        http_timeout=http_timeout,
    )

    repository_context = RepositoryContext(
        repository_name=os.getenv("ADO__REPO"),
        project_name=os.getenv("ADO__PROJECT"),
    )

    current_utc_time = datetime.now(timezone.utc)
    min_time = current_utc_time - relativedelta(months=6)
    max_time = current_utc_time

    pull_request_query_parameters = PullRequestQueryParameters(
        minTime=min_time.isoformat().replace("+00:00", "Z"),
        maxTime=max_time.isoformat().replace("+00:00", "Z"),
    )

    async with AdoService(ado_service_config) as ado_service:
        tasks = [
            ado_service.get_projects(),
            ado_service.get_pull_requests(
                repository_context,
                pull_request_query_parameters),
        ]

        results = await asyncio.gather(*tasks)

        for result in results:
            print(f"Task completed with result: {result}")

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
