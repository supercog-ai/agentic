# REST API Tools

`RestApiTool`

The base tool offering REST API calling functions.

`AuthorizedRestApiTool`

This tool is an easy way to access REST APIs that require authentication. Construct the
tool passing these args:

    token_type: str, token_var: str, token_name: str

Where token_type is "bearer", "basic", "parameter", "header". The "token_var" is the
name of the stored secret that the tool will use for the actual credential.

You need to set the actual credential as a secret in your environment or using `agentic set-secret`.

Examples:

    AuthorizedeRESTAPITool("bearer", "HEROKU_API_KEY")  - Bearer token. Set "HEROKU_API_KEY" in secrets

    AuthorizedeRESTAPITool("basic", "MY_AUTH")  - Basic auth.  Set "MY_AUTH" secret to "<username>:<password>"

    AuthorizedeRESTAPITool("parameter", "TAVILY_API_KEY, "api_key") - passes TAVILY_API_KEY secret as api_key param

    AuthorizedeRESTAPITool("header", "TAVILY_API_KEY, "x-api-key") - Passes a "x-api-key" header

Once the auth is setup properly, the tool simply exposes these functions to your agent:

    get_resource
    post_resource
    put_resource
    patch_resource
    delete_resource

which it can use to make REST API calls.

