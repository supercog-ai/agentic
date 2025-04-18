from typing import Any, Callable, List, Dict, Optional, Tuple

from git import Repo, GitCommandError
from httpx._types import QueryParamTypes
import httpx
import os
import base64
import pandas as pd

from agentic.common import RunContext
from agentic.events import OAuthFlowResult
from agentic.tools.oauth_tool import OAuthTool, OAuthConfig
from agentic.tools.utils.registry import tool_registry, Dependency
from agentic.utils.directory_management import get_runtime_filepath

@tool_registry.register(
    name="GithubTool",
    description="A tool for interacting with GitHub repositories.",
    dependencies=[
        Dependency(
            name="gitpython",
            version="3.1.44",
            type="pip",
        ),
    ]
)

class GithubTool(OAuthTool):
    repo_dir: str = get_runtime_filepath("git_tool")  # Local path to store the git repos

    def __init__(self, api_key: str = None, default_repo: str = None):
        oauth_config = OAuthConfig(
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            client_id_key="GITHUB_CLIENT_ID",
            client_secret_key="GITHUB_CLIENT_SECRET", 
            scopes="repo user",
            tool_name="github"
        )
        super().__init__(oauth_config)
        self.api_key = api_key
        self.default_repo = default_repo

    def required_secrets(self) -> dict[str, str]:
        return {
            "GITHUB_API_KEY": "a Github API key. Configure one at https://github.com/settings/tokens",
            "GITHUB_DEFAULT_REPO": "a default repository to use (format: owner/repo)",
        }

    def get_tools(self) -> List[Callable]:
        return [
            #self.clone_repository,
            #self.fetch_changes,
            #self.create_commit,
            #self.push_changes,
            #self.pull_changes,
            #self.list_branches,
            #self.checkout_branch,
            #self.create_branch,
            #self.delete_branch,
            #self.list_tags,
            #self.create_tag,
            #self.repository_status,
            
            self.search_repositories,
            self.create_github_issue,
            self.get_github_issues,
            self.get_github_issue_comments,
            self.create_pull_request,
            self.get_pull_requests,
            self.get_pr_reviews,
            self.get_pr_comments,
            self.add_comment_to_issue,
            self.get_repository_contents,
            self.create_repository,
            self.delete_repository,
            self.get_user_info,
            self.list_user_repositories,
            self.list_repository_pull_requests,
            self.search_in_repo,
            self.download_repo_file
        ]

    def clone_repository(self, run_context: RunContext, repo_url: str, directory_path: str) -> str:
        """
        Clone a git repository from the given URL.
        :param repo_url: str
            The URL of the repository to clone.
        :param directory_path: str
            The path to the directory where the repository should be cloned. This should always be a relative path of the form 'owner/repo'.
        :return: str
            Status message.
        """
        try:
            Repo.clone_from(repo_url, os.path.join(self.repo_dir, directory_path))
            return "Repository cloned successfully."
        except GitCommandError as e:
            return f"Error cloning repository: {str(e)}"

    def fetch_changes(self, run_context: RunContext, repo_path: str) -> str:
        """
        Fetch changes from the remote repository.
        :param repo_path: str
            Path to the local repository.
        :return: str
            Status message.
        """
        try:
            repo = Repo(os.path.join(self.repo_dir, repo_path))
            repo.git.fetch()
            return "Fetched changes successfully."
        except GitCommandError as e:
            return f"Error fetching changes: {str(e)}"

    def create_commit(self, run_context: RunContext, repo_path: str, message: str, files: Optional[List[str]] = None) -> str:
        """
        Create a commit in the local repository.
        :param repo_path: str
            Path to the local repository.
        :param message: str
            Commit message.
        :param files: Optional[List[str]]
            List of file paths to commit. Commits all changes if None.
        :return: str
            Status message.
        """
        try:
            repo = Repo(os.path.join(self.repo_dir, repo_path))
            if files:
                repo.index.add(files)
            else:
                repo.git.add(A=True)
            repo.index.commit(message)
            return "Commit created successfully."
        except GitCommandError as e:
            return f"Error creating commit: {str(e)}"

    def push_changes(self, run_context: RunContext, repo_path: str, branch: str = "master") -> str:
        """
        Push changes from the local repository to the remote repository.
        :param repo_path: str
            Path to the local repository.
        :param branch: str
            Branch to push.
        :return: str
            Status message.
        """
        try:
            repo = Repo(os.path.join(self.repo_dir, repo_path))
            origin = repo.remote(name='origin')
            origin.push(branch)
            return "Changes pushed successfully."
        except GitCommandError as e:
            return f"Error pushing changes: {str(e)}"

    def pull_changes(self, run_context: RunContext, repo_path: str, branch: str = "master") -> str:
        """
        Pull changes from the remote repository to the local repository.
        :param repo_path: str
            Path to the local repository.
        :param branch: str
            Branch to pull.
        :return: str
            Status message.
        """
        try:
            repo = Repo(os.path.join(self.repo_dir, repo_path))
            origin = repo.remote(name='origin')
            origin.pull(branch)
            return "Changes pulled successfully."
        except GitCommandError as e:
            return f"Error pulling changes: {str(e)}"

    def list_branches(self, run_context: RunContext, repo_path: str) -> List[str]:
        """
        List all branches in the local repository.

        :param repo_path: str
            Path to the local repository.
        :return: List[str]
            List of branch names or an error message in a list.
        """
        try:
            repo = Repo(os.path.join(self.repo_dir, repo_path))
            return [str(branch) for branch in repo.branches]
        except GitCommandError as e:
            return [f"Error listing branches: {str(e)}"]

    def checkout_branch(self, run_context: RunContext, repo_path: str, branch_name: str) -> str:
        """
        Checkout a branch in the local repository.
        :param repo_path: str
            Path to the local repository.
        :param branch_name: str
            Branch to checkout.
        :return: str
            Status message.
        """
        try:
            repo = Repo(os.path.join(self.repo_dir, repo_path))
            repo.git.checkout(branch_name)
            return f"Checked out branch {branch_name} successfully."
        except GitCommandError as e:
            return f"Error checking out branch {branch_name}: {str(e)}"

    def create_branch(self, run_context: RunContext, repo_path: str, branch_name: str) -> str:
        """
        Create a new branch in the local repository.
        :param repo_path: str
            Path to the local repository.
        :param branch_name: str
            Name of the new branch to create.
        :return: str
            Status message.
        """
        try:
            repo = Repo(os.path.join(self.repo_dir, repo_path))
            repo.git.branch(branch_name)
            return f"Branch {branch_name} created successfully."
        except GitCommandError as e:
            return f"Error creating branch {branch_name}: {str(e)}"

    def delete_branch(self, run_context: RunContext, repo_path: str, branch_name: str) -> str:
        """
        Delete a branch in the local repository.
        :param repo_path: str
            Path to the local repository.
        :param branch_name: str
            Name of the branch to delete.
        :return: str
            Status message.
        """
        try:
            repo = Repo(os.path.join(self.repo_dir, repo_path))
            repo.git.branch('-d', branch_name)
            return f"Branch {branch_name} deleted successfully."
        except GitCommandError as e:
            return f"Error deleting branch {branch_name}: {str(e)}"

    def list_tags(self, run_context: RunContext, repo_path: str) -> List[str]:
        """
        List all tags in the local repository.

        :param repo_path: str
            Path to the local repository.
        :return: List[str]
            List of tag names or an error message in a list.
        """
        try:
            repo = Repo(os.path.join(self.repo_dir, repo_path))
            return [str(tag) for tag in repo.tags]
        except GitCommandError as e:
            return [f"Error listing tags: {str(e)}"]  # Return the error message as a single-element list

    def create_tag(self, run_context: RunContext, repo_path: str, tag_name: str, commit: str = 'HEAD') -> str:
        """
        Create a new tag in the local repository.
        :param repo_path: str
            Path to the local repository.
        :param tag_name: str
            Name of the new tag to create.
        :param commit: str
            Commit at which to create the tag, defaults to 'HEAD'.
        :return: str
            Status message.
        """
        try:
            repo = Repo(os.path.join(self.repo_dir, repo_path))
            repo.create_tag(tag_name, ref=commit)
            return f"Tag {tag_name} created successfully at {commit}."
        except GitCommandError as e:
            return f"Error creating tag {tag_name}: {str(e)}"

    def repository_status(self, run_context: RunContext, repo_path: str) -> str:
        """
        Get the current status of the local repository.
        :param repo_path: str
            Path to the local repository.
        :return: str
            Status message.
        """
        try:
            repo = Repo(os.path.join(self.repo_dir, repo_path))
            status = repo.git.status(porcelain=True)
            if status:
                return f"Repository status:\n{status}"
            else:
                return "No changes."
        except GitCommandError as e:
            return f"Error getting repository status: {str(e)}"

    ####################################
    # Below are the GITRestAPI functions
    ####################################        

    async def test_credential(self, run_context: RunContext) -> str:
        """
        Test that the given credential secrets are valid.
        Also validates the default_repo format if provided.
        """
        try:
            api_key = run_context.get_secret("GITHUB_API_KEY", self.api_key)
            default_repo = run_context.get_secret("GITHUB_DEFAULT_REPO", self.default_repo)

            # Test API key
            url = "https://api.github.com/user"
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"token {api_key}"}
                response = await client.get(url, headers=headers)

            if response.status_code != 200:
                return f"Invalid GitHub API key. Status code: {response.status_code}"

            # Validate default_repo format if provided
            if default_repo:
                try:
                    owner, name = default_repo.split('/')
                    # Test if the repository exists
                    async with httpx.AsyncClient() as client:
                        repo_url = f"https://api.github.com/repos/{owner}/{name}"
                        headers = {"Authorization": f"token {api_key}"}
                        repo_response = await client.get(repo_url, headers=headers)
                        
                        if repo_response.status_code != 200:
                            return f"Default repository '{default_repo}' not found or not accessible"
                except ValueError:
                    return f"Invalid default repository format: {default_repo}. Expected format: owner/repo"

            print("Connection tested OK!")
            return None

        except httpx.RequestError as e:
            return f"Error testing GitHub credentials: {str(e)}"
        except Exception as e:
            return str(e)
        
        
    async def _github_request(self, method: str, endpoint: str, run_context: RunContext, data: Optional[Dict[str, Any]] = None, params: Optional[QueryParamTypes] = None) -> Dict[str, Any]:
        """
        Async helper method to make GitHub API requests.
        """
        # First try API key
        api_key = run_context.get_secret("GITHUB_API_KEY", self.api_key)
        # Then try OAuth token
        oauth_token = run_context.get_oauth_token("github")
        
        # If neither exists, start OAuth flow
        if not api_key and not oauth_token:
            auth_result = await self.authenticate(run_context)
            if isinstance(auth_result, OAuthFlowResult):
                return {'status': 'oauth_required', 'flow': auth_result}
            elif isinstance(auth_result, str) and "Failed" in auth_result:
                return {'status': 'error', 'message': auth_result}
            # We should now have a token
            oauth_token = run_context.get_oauth_token("github")
            if not oauth_token:
                return {'status': 'error', 'message': 'Failed to obtain OAuth token'}

        # Use OAuth token if available, otherwise use API key
        token = oauth_token or api_key
        
        url = f"https://api.github.com{endpoint}"
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        async with httpx.AsyncClient() as client:
            if method.upper() == 'GET':
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = await client.post(url, headers=headers, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = await client.delete(url, headers=headers, params=params)
            elif method.upper() == 'PATCH':
                response = await client.patch(url, headers=headers, json=data, params=params)
            else:
                return {'status': 'error', 'message': f"Unsupported HTTP method: {method}"}

            if response.status_code in [200, 201, 204]:
                return {'status': 'success', 'results': response.json()}
            else:
                return {'status': 'error', 'message': f"API request failed: {response.text}"}
        
    def _get_repo_info(self, run_context: RunContext, repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> Tuple[str, str]:
        """
        Helper method to get repository owner and name, flexibly using defaults when needed.
        If only one parameter is provided, the other is taken from the default repository.
        
        :param repo_owner: Optional repository owner
        :param repo_name: Optional repository name
        :returns: Tuple of (owner, name)
        :raises ValueError: If no default repository is configured when needed
        """
        default_repo = run_context.get_secret('GITHUB_DEFAULT_REPO', self.default_repo)
        
        # If both parameters provided, use them as is
        if repo_owner is not None and repo_name is not None:
            return (repo_owner, repo_name)
            
        # If we need to use any defaults, validate default_repo format first
        if (repo_owner is None or repo_name is None) and not default_repo:
            raise ValueError("Default repository must be configured when not providing both owner and name")
            
        try:
            default_owner, default_name = default_repo.split('/')
        except ValueError:
            raise ValueError(f"Invalid default repository format: {default_repo}. Expected format: owner/repo")
            
        # Mix and match between provided values and defaults
        final_owner = repo_owner if repo_owner is not None else default_owner
        final_name = repo_name if repo_name is not None else default_name
        
        return (final_owner, final_name)

    async def search_repositories(self, run_context: RunContext,
                            query: str,
                            language: Optional[str] = None,
                            sort: str = 'stars',
                            order: str = 'desc')  -> dict:
        """
        Search for GitHub repositories.
        Args:
            query: Search keywords.
            language: Filter repositories by programming language.
            sort: Criteria to sort the results ('stars', 'forks', 'updated').
            order: Order of the results ('asc', 'desc').
        Returns:
            A list of dictionaries, each representing a repository.
        """
        params = {
            'q': f"{query}+language:{language}" if language else query,
            'sort': sort,
            'order': order
        }
        return await self._github_request('GET', '/search/repositories', run_context, params=params)

    async def create_github_issue(self, run_context: RunContext, title: str, body: str, labels: List[str] = None, 
                            repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> Dict[str, Any]:
            """
            Create a new issue in a GitHub repository.
            :param title: The title of the issue
            :param body: The body text of the issue
            :param labels: A list of labels to apply to the issue
            :param repo_owner: The owner of the repository (if None, uses default_repo owner)
            :param repo_name: The name of the repository (if None, uses default_repo name)
            :return: The created issue data or an error message
            """
            owner, name = self._get_repo_info(run_context, repo_owner, repo_name)
            endpoint = f'/repos/{owner}/{name}/issues'
            data = {
                'title': title,
                'body': body,
                'labels': labels or []
            }
            return await self._github_request('POST', endpoint, run_context, data)

    
    async def get_github_issues(
            self,
            run_context: RunContext,
            state: str = 'open',
            labels: Optional[str] = None,
            assignee: Optional[str] = None,
            creator: Optional[str] = None,
            mentioned: Optional[str] = None,
            since: Optional[str] = None,
            repo_owner: Optional[str] = None,
            repo_name: Optional[str] = None
        ) -> pd.DataFrame:
        """
        Get a list of issues for a repository, excluding pull requests.
        :param state: State of issues to return. Can be either 'open', 'closed', or 'all'
        :param labels: List of comma-separated label names. Example: bug,ui,@high
        :param assignee: Username of user that is assigned to issues. Use 'none' for issues with no assigned user. Use '*' for issues with any assigned user.
        :param creator: Username of user that created the issues
        :param mentioned: Username that is mentioned in the issues
        :param since: Only issues after this date will be returned, must be in ISO-8601 format YYYY-MM-DDTHH:MM:SSZ
        :param repo_owner: Repository owner (if None, uses default_repo owner)
        :param repo_name: Repository name (if None, uses default_repo name)
        :return: List of issues
        """
        owner, name = self._get_repo_info(run_context, repo_owner, repo_name)


        params = {
            'state': state,
            'labels': labels,
            'assignee': assignee,
            'creator': creator,
            'mentioned': mentioned,
            'since': since
        }

        # remove None values from params
        params = {k: v for k, v in params.items() if v is not None}

        response = await self._github_request('GET', f'/repos/{owner}/{name}/issues', run_context, params=params)
        results = response.get('results', [])

        # Filter out pull requests
        issues_only = [issue for issue in results if not issue.get('pull_request')]

        slim_issues = [
            {
                'number': issue.get('number'),
                'title': issue.get('title'),
                'url': issue.get('html_url'),
                'state': issue.get('state'),
                'created_at': issue.get('created_at'),
                'updated_at': issue.get('updated_at'),
                'closed_at': issue.get('closed_at'),
                'labels': [label.get('name') for label in issue.get('labels', [])],
                'assignee': issue.get('assignee', {}).get('login') if issue.get('assignee') else None,
                'creator': issue.get('user', {}).get('login') if issue.get('user') else None,
                'comments': issue.get('comments'),
                'description': issue.get('body'),
            }
            for issue in issues_only
        ]
        return pd.DataFrame(slim_issues)
  
    async def get_github_issue_comments(self, run_context: RunContext, issue_number: int, repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> dict[str, Any]:
        """
        Get comments for a GitHub issue.
        :param issue_number: The number of the issue
        :param repo_owner: Repository owner (if None, uses default_repo owner)
        :param repo_name: Repository name (if None, uses default_repo name)
        :return: List of comments
        """
        owner, name = self._get_repo_info(run_context, repo_owner, repo_name)
        endpoint = f'/repos/{owner}/{name}/issues/{issue_number}/comments'
        return await self._github_request('GET', endpoint, run_context)
    
    async def close_github_issue(self, run_context: RunContext, issue_number: int, repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Close a GitHub issue.
        :param issue_number: The number of the issue
        :param repo_owner: Repository owner (if None, uses default_repo owner)
        :param repo_name: Repository name (if None, uses default_repo name)
        :return: Closed issue data
        """
        owner, name = self._get_repo_info(run_context, repo_owner, repo_name)
        endpoint = f'/repos/{owner}/{name}/issues/{issue_number}'
        data = {'state': 'closed'}
        return await self._github_request('PATCH', endpoint, run_context, data)

    async def create_pull_request(self, run_context: RunContext, title: str, body: str, head: str, base: str,
                        repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new pull request.
        :param title: Title of the pull request
        :param body: Body of the pull request
        :param head: The name of the branch where your changes are implemented
        :param base: The name of the branch you want the changes pulled into
        :param repo_owner: Repository owner (if None, uses default_repo owner)
        :param repo_name: Repository name (if None, uses default_repo name)
        :return: Created pull request data
        """
        owner, name = self._get_repo_info(run_context, repo_owner, repo_name)
        data = {
            'title': title,
            'body': body,
            'head': head,
            'base': base
        }
        return await self._github_request('POST', f'/repos/{owner}/{name}/pulls', run_context, data)

    async def get_pull_requests(self, run_context: RunContext, state: str = 'open',
                        repo_owner: Optional[str] = None, repo_name: Optional[str] = None, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of pull requests for a repository.
        :param state: State of pull requests to return. Can be either 'open', 'closed', or 'all'
        :param repo_owner: Repository owner (if None, uses default_repo owner)
        :param repo_name: Repository name (if None, uses default_repo name)
        :param since: Only pull requests updated at or after this time are returned. This is a timestamp in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ.
        :return: List of pull requests
        """
        params = {'state': state}
        if since:
            params['since'] = since
        params = {k: v for k, v in params.items() if v is not None}
        owner, name = self._get_repo_info(run_context, repo_owner, repo_name)
        return await self._github_request('GET', f'/repos/{owner}/{name}/pulls', run_context, params=params)

    async def get_pr_reviews(self, run_context: RunContext, pr_number: int, state: str = 'open',
                        repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of reviews for a pull request.
        :param pr_number: The number of the pr
        :param state: State of pull requests to return. Can be either 'open', 'closed', or 'all'
        :param repo_owner: Repository owner (if None, uses default_repo owner)
        :param repo_name: Repository name (if None, uses default_repo name)
        :return: List of PR reviews
        """
        owner, name = self._get_repo_info(run_context, repo_owner, repo_name)
        return await self._github_request('GET', f'/repos/{owner}/{name}/pulls/{pr_number}/reviews', run_context)

    async def get_pr_comments(self, run_context: RunContext, pr_number: int, state: str = 'open',
                        repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of comments in the reviews of a pull request.
        :param pr_number: The number of the pr
        :param state: State of pull requests to return. Can be either 'open', 'closed', or 'all'
        :param repo_owner: Repository owner (if None, uses default_repo owner)
        :param repo_name: Repository name (if None, uses default_repo name)
        :return: List of PR comments
        """
        owner, name = self._get_repo_info(run_context, repo_owner, repo_name)
        return await self._github_request('GET', f'/repos/{owner}/{name}/pulls/{pr_number}/comments', run_context)

    async def add_comment_to_issue(self, run_context: RunContext, issue_number: int, body: str,
                            repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a comment to an issue.
        :param issue_number: Issue number
        :param body: Comment body
        :param repo_owner: Repository owner (if None, uses default_repo owner)
        :param repo_name: Repository name (if None, uses default_repo name)
        :return: Created comment data
        """
        owner, name = self._get_repo_info(run_context, repo_owner, repo_name)
        data = {'body': body}
        return await self._github_request('POST', f'/repos/{owner}/{name}/issues/{issue_number}/comments', run_context, data)

    async def get_repository_contents(self, run_context: RunContext, path: str = '',
                            repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get contents of a repository.
        :param path: Path to the content
        :param repo_owner: Repository owner (if None, uses default_repo owner)
        :param repo_name: Repository name (if None, uses default_repo name)
        :return: List of contents
        """
        owner, name = self._get_repo_info(run_context, repo_owner, repo_name)
        return await self._github_request('GET', f'/repos/{owner}/{name}/contents/{path}', run_context)

    async def create_repository(self, run_context: RunContext, name: str, description: str = '', private: bool = False) -> Dict[str, Any]:
        """
        Create a new repository.
        :param name: The name of the repository
        :param description: A short description of the repository
        :param private: Whether the repository should be private
        :return: Created repository data
        """
        data = {
            'name': name,
            'description': description,
            'private': private
        }
        return await self._github_request('POST', '/user/repos', run_context, data)

    async def delete_repository(self, run_context: RunContext, repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a repository.
        :param repo_owner: Repository owner (if None, uses default_repo owner)
        :param repo_name: Repository name (if None, uses default_repo name)
        :return: Status of the operation
        """
        owner, name = self._get_repo_info(run_context, repo_owner, repo_name)
        return await self._github_request('DELETE', f'/repos/{owner}/{name}', run_context)

    async def get_user_info(self, run_context: RunContext, username: str = "me") -> Dict[str, Any] | OAuthFlowResult:
        """
        Get information about a GitHub user.
        
        :param username: GitHub username or "me" for authenticated user info
        :return: User information or error message
        """
        # Determine endpoint based on username
        endpoint = "/user" if username == "me" else f"/users/{username}"
            
        try:
            response = await self._github_request("GET", endpoint, run_context)
            if response.get("status") == "success":
                user_data = response["results"]
                return {
                    "login": user_data.get("login"),
                    "name": user_data.get("name"),
                    "email": user_data.get("email"),
                    "bio": user_data.get("bio"),
                    "public_repos": user_data.get("public_repos"),
                    "followers": user_data.get("followers"),
                    "following": user_data.get("following")
                }
            elif response.get("status") == "oauth_required":
                return response["flow"]
            return {"error": response.get("message", "Failed to fetch user info")}
            
        except Exception as e:
            return {"error": f"Error fetching user info: {str(e)}"}
    
    async def list_user_repositories(self, run_context: RunContext, sort: str = 'updated', direction: str = 'desc') -> pd.DataFrame:
        """
        List repositories for the authenticated user.
        :param username: The GitHub username
        :param sort: The property to sort the repositories by. Can be one of: created, updated, pushed, full_name. (Default: 'updated')
        :param direction: The direction of the sort. Can be either 'asc' or 'desc'. (Default: 'desc')
        :return: List of repositories
        """
        params = {'sort': sort, 'direction': direction}
        response = await self._github_request('GET', f'/user/repos', run_context, params=params)

        # Check for API request errors
        if isinstance(response, dict) and response.get('status') == 'error':
            return f"Error: {response.get('message', 'Failed to retrieve issues')}"
        
        if not response or not 'results' in response:
            return []

        # Select and transform key repository information
        slim_repositories = [
            {
                'name': repo.get('name', 'N/A'),
                'full_name': repo.get('full_name', 'N/A'),
                'description': repo.get('description', 'No description'),
                'language': repo.get('language', 'Not specified'),
                'stars': repo.get('stargazers_count', 0),
                'forks': repo.get('forks_count', 0),
                'is_private': repo.get('private', False),
                'created_at': repo.get('created_at', 'N/A'),
                'updated_at': repo.get('updated_at', 'N/A'),
                'url': repo.get('html_url', '')
            }
            for repo in response.get('results', [])
        ]
        
        # Convert to DataFrame for better preview
        return pd.DataFrame(slim_repositories)

    async def list_repository_pull_requests(self, run_context: RunContext, state: str = 'open', sort: str = 'created', 
                                    direction: str = 'desc',
                                    repo_owner: Optional[str] = None, 
                                    repo_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List pull requests for a specific repository.
        :param state: State of pull requests to return. Can be either 'open', 'closed', or 'all'
        :param sort: What to sort results by. Can be either 'created', 'updated', 'popularity' or 'long-running'
        :param direction: The direction of the sort. Can be either 'asc' or 'desc'
        :param repo_owner: Repository owner (if None, uses default_repo owner)
        :param repo_name: Repository name (if None, uses default_repo name)
        :return: List of pull requests
        """
        owner, name = self._get_repo_info(run_context, repo_owner, repo_name)
        endpoint = f'/repos/{owner}/{name}/pulls'
        params = f'?state={state}&sort={sort}&direction={direction}'
        return await self._github_request('GET', f'{endpoint}{params}', run_context)

    async def search_in_repo(self, run_context: RunContext, query: str, 
                    repo_owner: Optional[str] = None, 
                    repo_name: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Search for code within a specific repository.
        
        :param query: Search terms or code snippet to find
        :param repo_owner: Repository owner (if None, uses default_repo owner)
        :param repo_name: Repository name (if None, uses default_repo name)
        :return: List of dictionaries with file paths, URLs, and code snippets
        """
        owner, name = self._get_repo_info(run_context, repo_owner, repo_name)
        
        # Construct search endpoint
        endpoint = f'/search/code?q={query}+repo:{owner}/{name}'
        
        # Perform search
        response = await self._github_request('GET', endpoint, run_context)
        
        # Check if results is an error dictionary
        if isinstance(response, dict) and response.get('status') == 'error':
            return [{'error': response.get('message', 'Search failed')}]
        
        if not response or not response.get('results'):
            return []
        
        results = response.get('results', {})
        
        # Process search results
        search_results = []
        
        for item in results.get('items', []):
            try:
                # Fetch file contents
                file_path = item.get('path', 'Unknown')
                file_contents_response = await self._github_request('GET', f'/repos/{owner}/{name}/contents/{file_path}', run_context)
                file_contents_results = file_contents_response.get('results', {})

                # Decode base64 content
                if isinstance(file_contents_results, dict) and 'content' in file_contents_results:
                    decoded_content = base64.b64decode(file_contents_results['content']).decode('utf-8')
                    
                    # Find lines containing the query with their line numbers
                    matching_lines = []
                    for line_num, line in enumerate(decoded_content.split('\n'), 1):
                        if query.lower() in line.lower():
                            # Construct GitHub line-specific URL
                            line_url = f'https://github.com/{owner}/{name}/blob/main/{file_path}#L{line_num}'
                            matching_lines.append({
                                'line_number': line_num,
                                'content': line.strip(),
                                'line_url': line_url
                            })
                    
                    search_results.append({
                        'file_path': file_path,
                        'file_url': item.get('html_url', ''),
                        'repository': f'{owner}/{name}',
                        'matching_lines': matching_lines,
                    })
            except Exception as e:
                # If fetching file contents fails, still add basic info
                search_results.append({
                    'file_path': file_path,
                    'file_url': item.get('html_url', ''),
                    'repository': f'{owner}/{name}',
                    'error': str(e)
                })

        return search_results
    
    async def download_repo_file(self, run_context: RunContext, file_path: str, 
                        repo_owner: Optional[str] = None, 
                        repo_name: Optional[str] = None, 
                        branch: Optional[str] = None,
                        local_file_name: Optional[str] = None) -> str:
        """
        Async download of a file from a repository to local storage.
        
        :param file_path: Path to the file in the repository
        :param repo_owner: Repository owner (if None, uses default_repo owner)
        :param repo_name: Repository name (if None, uses default_repo name)
        :param branch: Optional branch name to download from
        :param local_file_name: Optional local filename to save the file as
        :return: Local filename of the downloaded file or an error message
        """
        try:
            # Get repository owner and name, using defaults if not provided
            owner, name = self._get_repo_info(run_context, repo_owner, repo_name)
            
            # Construct the API endpoint to get file download URL
            endpoint = f'/repos/{owner}/{name}/contents/{file_path}'
            if branch:
                endpoint += f'?ref={branch}'
            
            # Retrieve file metadata
            response = await self._github_request('GET', endpoint, run_context)
            # Check for API request errors
            if isinstance(response, dict) and response.get('status') == 'error':
                return f"Error: {response.get('message', 'Failed to retrieve file metadata')}"
            
            file_info = response.get('results', {})

            # Get the download URL
            download_url = file_info.get('download_url')
            if not download_url:
                return "Error: No download URL found for the file"
            
            # Determine local file name
            if not local_file_name:
                # Use the last component of the file path as the default file name
                local_file_name = file_path.split('/')[-1]
            # Download the file content
            async with httpx.AsyncClient() as client:
                response = await client.get(download_url)
                if response.status_code != 200:
                    return f"Error: Failed to download file. Status code: {response.status_code}"
                
                # Save file content
                try:
                    with open(local_file_name, 'wb') as f:
                        f.write(response.content)
                    return local_file_name
                except IOError as e:
                    return f"Error saving file: {str(e)}"
        
        except Exception as e:
            return f"Unexpected error during file download: {str(e)}"