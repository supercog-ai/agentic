from typing import Callable

from agentic.common import RunContext
from agentic.tools.utils.registry import tool_registry
from agentic.tools.rest_api_tool import RestApiTool

@tool_registry.register(
    name="AuthorizedRestApiTool",
    description="Extends the RestApiTool to include authorization",
    dependencies=[],
    config_requirements=[],
)

class AuthorizedRestApiTool(RestApiTool):
    token_type: str = "bearer"
    token_var: str = "bearer_token"
    token_name: str = "Bearer"

    def __init__(self, token_type: str, token_var: str, token_name: str):
        """Construct with the type of token (bearer,basic,parameter,header) and the name
        of the secret that holds the token value. For Basic auth set the token as "<user>:<password>"
        """
        super().__init__()
        self.token_type = token_type
        self.token_var = token_var
        self.token_name = token_name

    def get_tools(self) -> list[Callable]:
        return [
            self.add_request_header,
            self.get_resource,
            self.post_resource,
            self.put_resource,
            self.patch_resource,
            self.delete_resource,
            self.debug_request,
        ]

    async def get_auth_variable(self, run_context: RunContext):
        print("Auto REST API, ", self.token_type, self.token_var, self.token_name)

        self.run_context = run_context
        token = run_context.get_secret(self.token_var)
        if token is None:
            raise RuntimeError(f"Token variable {self.token_var} not found in secrets")

        print("Token: ", token)
        auth_type = "none"
        token: str | None = None
        token_name: str = ""
        username: str | None = None
        password: str | None = None
        if self.token_type == "bearer":
            auth_type = "bearer"
            token = run_context.get_secret(self.token_var)
            token_name = self.token_name or "Bearer"
        elif self.token_type == "basic":
            auth_type = "basic"
            username, password = run_context.get_secret(self.token_var).split(":")
        elif self.token_type == "parameter":
            auth_type = "parameter"
            token = run_context.get_secret(self.token_var)
            token_name = self.token_name or "api_key"

        auth_var = await super().prepare_auth_config(
            auth_type=auth_type,
            username=username,
            password=password,
            token=token,
            token_name=token_name,
        )

        if self.token_type == "header":
            super().add_request_header(
                auth_var,
                self.token_name,
                run_context.get_secret(self.token_var),
            )

        return auth_var

    async def get_resource(
        self,
        url: str,
        params: dict = {},
        run_context: RunContext = None,
    ):
        """Invoke the GET REST endpoint on the indicated URL, using authentication already configured.
        returns: the JSON response, or the response text and status code.
        """
        return await super().get_resource(
            url, params, auth_config_var=await self.get_auth_variable(run_context)
        )

    async def post_resource(
        self,
        url: str,
        content_type: str = "application/json",
        data: str = "{}",
        run_context: RunContext = None,
    ):
        """Invoke the POST REST endpoint, using authentication already configured.
        Supply a data dictionary of params (as json data). The data will be submitted
        as json or as form data (application/x-www-form-urlencoded).
        Returns the response and status code.
        """
        return await super().post_resource(
            url,
            content_type,
            data,
            auth_config_var=await self.get_auth_variable(run_context),
        )

    async def put_resource(
        self,
        url: str,
        data: str = "{}",
        run_context: RunContext = None,
    ):
        """Invoke the PUT REST endpoint.
        Supply a data dictionary of params (as json data).
        """
        return await super().put_resource(
            url, data, auth_config_var=await self.get_auth_variable(run_context)
        )

    async def patch_resource(
        self,
        url: str,
        data: str = "{}",
        run_context: RunContext = None,
    ):
        """Invoke the PATCH REST endpoint.
        Supply a data dictionary of params (as json data).
        """
        return await super().patch_resource(
            url, data, auth_config_var=await self.get_auth_variable(run_context)
        )

    async def delete_resource(
        self,
        url: str,
        run_context: RunContext = None,
    ):
        """Invoke the DELETE REST endpoint."""
        return await super().delete_resource(
            url, auth_config_var=await self.get_auth_variable(run_context)
        )
