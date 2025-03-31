import pytest
import os
from agentic.tools import GithubTool
from agentic.tools.utils.registry import tool_registry
from agentic.common import RunContext
from agentic.agentic_secrets import agentic_secrets
import pandas as pd

TEST_REPO_OWNER = "supercog-ai"
TEST_REPO_NAME = "test-repo"
TEST_ACCOUNT_USERNAME = "supercog-test-account"
TEST_DEFAULT_REPO = f"{TEST_REPO_OWNER}/{TEST_REPO_NAME}"

# Fixture for GithubTool instance with real test token
@pytest.fixture
@pytest.mark.github_test
def github_tool():
    gh_key = agentic_secrets.get_secret("TEST_GITHUB_TOKEN")
    tool = GithubTool(api_key=gh_key, default_repo=TEST_DEFAULT_REPO)
    tool_registry.ensure_dependencies(tool, always_install=True)
    return tool

# Fixture for RunContext
@pytest.fixture
@pytest.mark.github_test
def run_context():
    context = RunContext(None)
    context.get_secret = lambda key, default=None: (
        agentic_secrets.get_secret("TEST_GITHUB_TOKEN") if key == "GITHUB_API_KEY"
        else TEST_DEFAULT_REPO if key == "GITHUB_DEFAULT_REPO"
        else default
    )
    return context

# Test initialization and configuration
@pytest.mark.github_test
def test_github_tool_init(github_tool):
    assert github_tool.api_key is not None
    assert github_tool.default_repo == TEST_DEFAULT_REPO 

# Test repository info helper
@pytest.mark.github_test
def test_get_repo_info(github_tool, run_context):
    owner, name = github_tool._get_repo_info(run_context)
    assert owner == TEST_REPO_OWNER
    assert name == TEST_REPO_NAME

# Test API endpoints with real calls
@pytest.mark.asyncio
@pytest.mark.github_test
@pytest.mark.skip(reason="User will be marked as spammy")
@pytest.mark.github_test
async def test_search_repositories(github_tool, run_context):
    result = await github_tool.search_repositories(run_context, "test", language="python")
    assert result['status'] == 'success'
    assert 'items' in result['results']

@pytest.mark.asyncio
@pytest.mark.github_test
@pytest.mark.github_test
async def test_create_get_and_close_issue(github_tool, run_context):
    # Create an issue
    create_result = await github_tool.create_github_issue(
        run_context,
        title="Test Issue from Integration Tests",
        body="This is a test issue created by automated tests",
        labels=["test"]
    )
    assert create_result['status'] == 'success'
    issue_number = create_result['results']['number']

    # Get the issue
    issues = await github_tool.get_github_issues(run_context, state='open')
    assert isinstance(issues, pd.DataFrame)
    assert not issues.empty
    
    # Add a comment
    comment_result = await github_tool.add_comment_to_issue(
        run_context,
        issue_number=issue_number,
        body="Test comment from integration tests"
    )
    assert comment_result['status'] == 'success'

    # Get comments
    comments = await github_tool.get_github_issue_comments(
        run_context,
        issue_number=issue_number
    )
    assert comments['status'] == 'success'
    assert len(comments['results']) > 0

    # Close the issue
    close_result = await github_tool.close_github_issue(
        run_context,
        issue_number=issue_number
    )
    assert close_result['status'] == 'success'

@pytest.mark.asyncio
@pytest.mark.github_test
async def test_repository_contents(github_tool, run_context):
    result = await github_tool.get_repository_contents(run_context)
    assert result['status'] == 'success'
    assert isinstance(result['results'], (list, dict))

@pytest.mark.asyncio
@pytest.mark.github_test
async def test_list_user_repositories(github_tool, run_context):
    result = await github_tool.list_user_repositories(run_context, TEST_ACCOUNT_USERNAME)
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert 'name' in result.columns

@pytest.mark.asyncio
@pytest.mark.github_test
async def test_search_in_repo(github_tool, run_context):
    result = await github_tool.search_in_repo(
        run_context,
        query="test"
    )
    assert isinstance(result, list)

@pytest.mark.asyncio
@pytest.mark.github_test
async def test_credential_validation(github_tool, run_context):
    result = await github_tool.test_credential(run_context)
    assert result is None  # Success case returns None

@pytest.mark.asyncio
@pytest.mark.github_test
@pytest.mark.skip(reason="User will be marked as spammy")
async def test_create_and_delete_repository(github_tool, run_context):
    # Create a new test repository
    repo_name = "temp-test-repo-" + os.urandom(4).hex()
    create_result = await github_tool.create_repository(
        run_context,
        name=repo_name,
        description="Temporary test repository",
        private=True
    )
    assert create_result['status'] == 'success'
    
    # Small delay to ensure GitHub has processed the creation
    import asyncio
    await asyncio.sleep(2)
    
    # Delete the test repository
    delete_result = await github_tool.delete_repository(
        run_context,
        repo_owner=TEST_ACCOUNT_USERNAME,
        repo_name=repo_name
    )
    assert delete_result['status'] == 'success'

@pytest.mark.asyncio
@pytest.mark.github_test
async def test_create_and_get_pull_request(github_tool, run_context):
    # Note: This test assumes your test repository has at least two branches
    # You might need to modify the head and base branch names
    
    create_result = await github_tool.create_pull_request(
        run_context,
        title="Test PR from Integration Tests",
        body="This is a test pull request created by automated tests",
        head="dev",
        base="main"
    )
    
    # Get pull requests
    prs = await github_tool.get_pull_requests(run_context, state='open')
    assert prs['status'] == 'success'
    assert isinstance(prs['results'], list)

@pytest.mark.asyncio
@pytest.mark.github_test
async def test_get_pr_reviews(github_tool, run_context):
    # This test assumes there is a PR with number 17 and 
    # TEST_REPO_OWNER = "supercog-ai" and TEST_REPO_NAME = "test-repo"
    reviews_result = await github_tool.get_pr_reviews(
        run_context,
        pr_number=17
    )
    
    assert reviews_result['status'] == 'success'
    assert isinstance(reviews_result['results'], list)
    assert reviews_result['results'][0]['body'] == 'THIS IS A BAD COMMIT. Do better'
    assert reviews_result['results'][1]['body'] == 'Looks good!'

@pytest.mark.asyncio
@pytest.mark.github_test
async def test_get_pr_comments(github_tool, run_context):
    # This test assumes there is a PR with number 17 and 
    # TEST_REPO_OWNER = "supercog-ai" and TEST_REPO_NAME = "test-repo"
    comments_result = await github_tool.get_pr_comments(
        run_context,
        pr_number=17
    )
    
    print(comments_result)
    assert comments_result['status'] == 'success'
    assert isinstance(comments_result['results'], list)

if __name__ == "__main__":
    pytest.main(["-v", __file__])