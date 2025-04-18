from typing import Callable, Any, Optional, Dict, Awaitable, Union, AsyncGenerator
from io import BytesIO
from PIL import Image
import uuid
import os
import json
import pandas as pd
import math
import numpy as np
import random
import httpx
from urllib.parse import urlparse, parse_qsl, urlencode

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry
from agentic.common import RunContext

class AsyncRequestBuilder:
    def __init__(self, base_url: str, logger_func: Callable[..., Awaitable[None]]):
        parsed_url = urlparse(base_url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.base_path = parsed_url.path
        self.headers: Dict[str, str] = {}
        self.auth_params: Dict[str, str] = {}
        self.auth: Optional[httpx.BasicAuth] = None
        self.client: Optional[httpx.AsyncClient] = None
        self.logger_func = logger_func

    def with_bearer_token(self, token: str, token_name: str = "Bearer"):
        self.headers["Authorization"] = f"{token_name} {token}"
        return self

    def with_basic_auth(self, username: str, password: str):
        self.auth = httpx.BasicAuth(username, password)
        return self

    def with_header(self, key: str, value: str):
        self.headers[key] = value
        return self

    def with_auth_param(self, param_name: str, param_value: str):
        self.auth_params[param_name] = param_value
        return self

    async def create_client(self):
        if self.client is None:
            self.client = httpx.AsyncClient(headers=self.headers, auth=self.auth)

    async def close_client(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def _ensure_client(self):
        if self.client is None:
            await self.create_client()

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        await self._ensure_client()
        if self.base_url:
            parsed = urlparse(path)
            url = (
                path
                if parsed.netloc
                else self.base_url + os.path.join(self.base_path, path).rstrip("/")
            )
        else:
            url = path
        self.logger_func(f"{method.upper()} {url}")
        if self.auth:
            self.logger_func(f"Auth: {self.auth}")
        if self.headers:
            self.logger_func(f"--Headers--")
            for k, v in self.headers.items():
                self.logger_func(f"  {k}: {v}")
        print(f"Requesting {method} {url}")
        if self.auth_params:
            if "params" in kwargs:
                kwargs["params"].update(self.auth_params)
            else:
                kwargs["params"] = self.auth_params
        return await self.client.request(method, url, timeout=60.0, **kwargs)

    async def get(self, path: str, **kwargs):
        return await self._request("GET", path, **kwargs)

    async def post_json(self, path: str, json: Any = None, **kwargs):
        return await self._request("POST", path, json=json, **kwargs)

    async def put_json(self, path: str, json: Any = None, **kwargs):
        return await self._request("PUT", path, json=json, **kwargs)

    async def post_form(self, path: str, form_data: Any = None, **kwargs):
        kwargs["data"] = form_data
        kwargs.setdefault("headers", {})[
            "Content-Type"
        ] = "application/x-www-form-urlencoded"
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, data: Any = None, json: Any = None, **kwargs):
        return await self._request("PUT", path, data=data, json=json, **kwargs)

    async def patch(self, path: str, data: Any = None, json: Any = None, **kwargs):
        return await self._request("PATCH", path, data=data, json=json, **kwargs)

    async def delete(self, path: str, **kwargs):
        return await self._request("DELETE", path, **kwargs)


@tool_registry.register(
    name="RestApiTool",
    description="REST API Tool",
    dependencies=[],
    config_requirements=[],
)
class RestApiTool(BaseAgenticTool):
    def __init__(
        self,
        request_map:  dict[str, AsyncRequestBuilder] = {},
        return_dataframe: bool = False,
        run_context: Optional[RunContext] = None
    ):
        super().__init__()
        self.request_map = request_map
        self.return_dataframe = return_dataframe
        self.run_context = run_context

    def get_tools(self) -> list[Callable]:
        return [
            self.prepare_auth_config,
            self.add_request_header,
            self.get_resource,
            self.post_resource,
            self.put_resource,
            self.patch_resource,
            self.delete_resource,
            self.debug_request,
        ]

    def debug_request(self, request_name: str):
        """Returns debug information about the indicated request object."""
        request = self.request_map.get(request_name)
        if request is None:
            raise ValueError(f"Request '{request_name}' not found.")

        auth = ""
        if request.auth:
            auth = f"Auth: {request.auth}\n"

        res = f"""
        Base URL: {request.base_url}
        Headers: {request.headers}
        {auth}
        """
        return res

    async def prepare_auth_config(
        self,
        auth_type: str,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
        token_name: str = "Bearer",
        run_context: RunContext|None=None,
    ) -> AsyncGenerator[Any, Any]:
        """Constructs an auth_config object to use with later requests.
        auth_type is one of: basic, bearer, token, or parameter
        For "basic" provide the username and password.
        For "bearer" provide the token.
        You can override the default "Bearer" token name.
        For "parameter" provide the parameter value and name in token and token_name.
        Any value can refer to ENV VARS using ${KEY} syntax.
        Returns the variable name of the auth config for use in request calls.
        """
        if not run_context:
            return
        
        async def logger_func(msg: str):
            print(msg)

        request = AsyncRequestBuilder("", logger_func=logger_func)

        auth_type = auth_type.lower()

        if auth_type == "basic":
            username = run_context.get_secret(username or "")
            password = run_context.get_secret(password or "")
            request = request.with_basic_auth(username, password)
            yield run_context.log(f"Basic Auth: {username} / {password}")
        elif auth_type in ["bearer", "token"]:
            token = run_context.get_secret(token or "")
            request = request.with_bearer_token(token, token_name)
            yield run_context.log(f"[token] {token_name}: {token}")
        elif auth_type == "parameter":
            token = run_context.get_secret(token or "")
            if token:
                request = request.with_auth_param(token_name, token)
            else:
                raise ValueError(f"Token value is empty.")
            yield run_context.log(f"[param] {token_name}: {token}")
        elif auth_type == "none":
            pass
        else:
            raise ValueError(f"Unsupported auth type: {auth_type}")

        name = f"auth_{random.randint(1000,9999)}"
        self.request_map[name] = request
        yield name

    def add_request_header(self, auth_config_var: str, name: str, value: str) -> str:
        """Add a header to the auth config which was created already."""
        request = self.request_map.get(auth_config_var)
        if request is None:
            raise ValueError(f"Request '{auth_config_var}' not found.")

        request.headers[name] = value
        return "OK"

    async def get_resource(
        self,
        url: str,
        params: dict = {},
        auth_config_var: Optional[str] = "",
        run_context: RunContext|None=None,
    ):
        """Invoke the GET REST endpoint on the indicate URL. If the endpoints requires
        authentication then call 'prepare_auth_config' first and pass the config name to this function.
        returns: the JSON response, or the response text and status code.
        """
        if auth_config_var:
            request = self.request_map.get(auth_config_var)
            if request is None:
                raise ValueError(
                    f"Auth config '{auth_config_var}' not found. Must call prepare_auth_config first."
                )
        else:
            request = AsyncRequestBuilder("", logger_func=run_context.info)

        response = await request.get(url, params=params)

        return await self.process_response(response)

    async def _post_json(
        self,
        auth_config_var: str | None,
        url: str,
        params: dict | str,
        method="POST",
    ):
        if isinstance(params, str):
            params = json.loads(params)

        if not auth_config_var:
            request = AsyncRequestBuilder("", logger_func=run_context.info)
        else:
            request = self.request_map.get(auth_config_var)
            if request is None:
                raise ValueError(f"Request '{auth_config_var}' not found.")

        response = await request._request(method, url, json=params)
        return response

    async def post_resource(
        self,
        path: str,
        content_type: str = "application/json",
        data: Union[str, dict] = "{}",
        auth_config_var: Optional[str] = "",
    ):
        """Invoke the POST REST endpoint. Pass an auth config name if the request needs authentication.
        Supply data as a string or dictionary. For JSON, use a JSON-formatted string or a dictionary.
        For form data, use a dictionary or URL-encoded string.
        Returns the response and status code.
        """
        # Convert data to a dictionary if it's a string
        if isinstance(data, str):
            try:
                params = json.loads(data)
            except json.JSONDecodeError:
                # If JSON decoding fails, assume it's URL-encoded form data
                params = dict(parse_qsl(data))
        else:
            params = data

        if content_type == "application/json":
            response = await self._post_json(
                auth_config_var or "", path, params, "POST"
            )
        else:
            if auth_config_var:
                request = self.request_map.get(auth_config_var)
                if request is None:
                    raise ValueError(f"Request '{auth_config_var}' not found.")
            else:
                request = AsyncRequestBuilder("", logger_func=run_context.info)

            # Convert params to URL-encoded string if it's not already
            if isinstance(params, dict):
                form_data = urlencode(params)
            else:
                form_data = params

            response = await request.post_form(path, form_data=form_data)

        return await self.process_response(response)

    async def put_resource(
        self,
        url: str,
        data: str = "{}",
        auth_config_var: Optional[str] = "",
    ):
        """Invoke the PUT REST endpoint using the prepared request object.
        Supply a data dictionary of params (as json data).
        """
        response = await self._post_json(auth_config_var, url, data, method="PUT")

        return await self.process_response(response)

    async def patch_resource(
        self,
        url: str,
        data: str = "{}",
        auth_config_var: Optional[str] = "",
    ):
        """Invoke the PATCH REST endpoint using the prepared request object.
        Supply a data dictionary of params (as json data).
        """
        response = await self._post_json(auth_config_var, url, data, method="PATCH")

        return await self.process_response(response)

    async def delete_resource(
        self,
        url: str,
        auth_config_var: Optional[str] = "",
    ):
        """Invoke the DELETE REST endpoint using the prepared request object."""
        if auth_config_var:
            request = self.request_map.get(auth_config_var)
            if request is None:
                raise ValueError(f"Request '{auth_config_var}' not found.")
        else:
            request = AsyncRequestBuilder("", logger_func=run_context.info)

        response = await request.delete(url)
        return await self.process_response(response)

    ###################

    async def process_response(self, response: httpx.Response):
        if response.status_code >= 400:
            return {
                "status": response.status_code,
                "response": str(response),
                "text": response.text,
            }

        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return await self.process_json(response)
        elif "image" in content_type:
            return await self.process_image(response)
        elif "text/html" in content_type:
            return {"html": response.text}
        elif "text/plain" in content_type:
            return {"text": response.text}
        elif "text/csv" in content_type:
            return {"csv": response.text}
        elif "application/atom+xml" in content_type:
            return {"xml": response.text}
        else:
            return "Error: Unsupported response content type '{}'".format(content_type)

    async def process_json(self, response: httpx.Response):
        json = response.json()
        # json = self.clean_json_data(json)
        if not self.return_dataframe:
            return json
        else:
            df = pd.json_normalize(json)
            df.replace({np.nan: ""}, inplace=True)
            return df

    def clean_json_data(self, data):
        if isinstance(data, dict):
            return {k: self.clean_json_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.clean_json_data(v) for v in data]
        elif isinstance(data, float) and math.isnan(data):
            return None  # or a default value like 0
        else:
            return data

    async def process_image(self, response: httpx.Response):
        return await RestApiTool._process_image(
            response.content
        )  # Read the image data as bytes

    @staticmethod
    async def _process_image(image_data: bytes):
        """
        Image Formats Supported
        BMP
        EPS
        GIF
        ICNS
        ICO
        IM
        JPEG      .jpg
        JPEG 2000
        MSP
        PCX
        PNG       .png
        PPM
        SGI
        SPIDER
        TIFF
        WebP
        XBM
        XV
        """
        format = "PNG"
        extension = "png"

        print(f"***************> Got an image to return:")
        # Read the image data as bytes
        image = Image.open(BytesIO(image_data))

        # Convert RGBA to RGB if necessary
        if format == "JPEG":
            if image.mode == "RGBA":
                image = image.convert("RGB")

        # Create an in-memory bytes buffer to save the image
        image_buffer = BytesIO()
        image.save(image_buffer, format=format)
        image_buffer.seek(0)  # Rewind the buffer to the beginning

        # Generate a unique object name for the S3 upload
        object_name = f"images/{uuid.uuid4()}.{extension}"

        # Upload the image file to S3 and get the public URL
        public_url = upload_file_to_s3(
            image_buffer,
            public_image_bucket(),
            object_name,
            mime_type=f"image/{extension}",
        )

        # Return markdown formatted image link
        return {"thumb": f"![Generated Image]({public_url})"}
