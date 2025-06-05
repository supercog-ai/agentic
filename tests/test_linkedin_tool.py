import pytest
from unittest.mock import Mock, patch
from agentic.tools import LinkedinDataTool
from agentic.tools.utils.registry import tool_registry
from agentic.common import ThreadContext
import pandas as pd

# Mock API responses
MOCK_PROFILE_RESPONSE = {
    "id": 11848598,
    "username": "adamselipsky",
    "firstName": "Adam",
    "lastName": "Selipsky",
    "isTopVoice": True,
    "isPremium": True,
    "profilePicture": "https://media.licdn.com/dms/image/example.jpg",
    "headline": "Former CEO at Amazon Web Services (AWS). Former President and CEO at Tableau.",
    "summary": "Adam Selipsky is the CEO of Amazon Web Services (AWS)...",
    "geo": {
        "country": "United States",
        "city": "Greater Seattle Area",
        "full": "Greater Seattle Area",
        "countryCode": "us"
    },
    "educations": [
        {
            "degree": "MBA",
            "schoolName": "Harvard Business School",
            "url": "https://www.linkedin.com/school/harvard-business-school/"
        }
    ],
    "position": [
        {
            "companyName": "Amazon Web Services (AWS)",
            "title": "CEO",
            "start": {"year": 2021, "month": 5},
            "end": {"year": 2024, "month": 6}
        }
    ]
}

MOCK_LOCATION_RESPONSE = {
    "success": True,
    "message": "",
    "data": {
        "items": [
            {
                "id": "urn:li:geo:102277331",
                "name": "San Francisco Bay Area"
            }
        ]
    }
}

MOCK_COMPANY_RESPONSE = {
    "success": True,
    "message": "",
    "data": {
        "id": "1441",
        "name": "Google",
        "universalName": "google",
        "linkedinUrl": "https://www.linkedin.com/company/google",
        "description": "A problem isn't truly solved until it's solved for all...",
        "staffCount": 303008,
        "headquarter": {
            "country": "US",
            "city": "Mountain View"
        }
    }
}

MOCK_PEOPLE_SEARCH_RESPONSE = {
    "success": True,
    "message": "",
    "data": {
        "total": 1000,
        "items": [
            {
                "fullName": "Max Lopez",
                "headline": "Software Engineer",
                "location": "San Francisco Bay Area",
                "profileURL": "https://www.linkedin.com/in/max-lopez-7605972"
            }
        ]
    }
}

@pytest.fixture
def linkedin_tool(monkeypatch):
    # Set the API key in environment before creating the tool
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    tool = LinkedinDataTool()
    tool_registry.ensure_dependencies(tool, always_install=True)
    return tool

@pytest.fixture
def thread_context():
    context = ThreadContext(None)
    return context

def test_linkedin_tool_init(linkedin_tool):
    assert linkedin_tool.get_api_key() == "test_key"
    assert linkedin_tool.BASE_URL == "https://linkedin-data-api.p.rapidapi.com"

@pytest.mark.asyncio
async def test_get_linkedin_profile_info(linkedin_tool):
    mock_response = Mock()
    mock_response.json.return_value = MOCK_PROFILE_RESPONSE
    mock_response.raise_for_status.return_value = None
    
    with patch('httpx.AsyncClient.get', return_value=mock_response):
        result = await linkedin_tool.get_linkedin_profile_info(
            "https://www.linkedin.com/in/adamselipsky/"
        )
        
        assert "Adam Selipsky" in result
        assert "Former CEO at Amazon Web Services" in result
        assert "Harvard Business School" in result
        assert "Greater Seattle Area" in result

        assert "CAREER PROGRESSION:" in result
        assert "Role: CEO" in result
        assert "Company: Amazon Web Services (AWS)" in result
        assert "Duration: 5/2021 - 6/2024" in result

@pytest.mark.asyncio
async def test_search_location(linkedin_tool):
    mock_response = Mock()
    mock_response.json.return_value = MOCK_LOCATION_RESPONSE
    mock_response.raise_for_status.return_value = None
    
    with patch('httpx.AsyncClient.get', return_value=mock_response):
        result = await linkedin_tool.search_location("San Francisco, CA")
        assert result == "102277331"

@pytest.mark.asyncio
async def test_get_company_linkedin_info(linkedin_tool):
    mock_response = Mock()
    mock_response.json.return_value = MOCK_COMPANY_RESPONSE
    mock_response.raise_for_status.return_value = None
    
    with patch('httpx.AsyncClient.get', return_value=mock_response):
        result = await linkedin_tool.get_company_linkedin_info("google")
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert "Google" in result.values

@pytest.mark.asyncio
async def test_linkedin_people_search(linkedin_tool):
    # Create two mock responses - one for location search and one for people search
    location_mock = Mock()
    location_mock.json.return_value = MOCK_LOCATION_RESPONSE
    location_mock.raise_for_status.return_value = None

    people_mock = Mock()
    people_mock.json.return_value = MOCK_PEOPLE_SEARCH_RESPONSE
    people_mock.raise_for_status.return_value = None
    
    # Use side_effect to return different responses for sequential calls
    with patch('httpx.AsyncClient.get', side_effect=[location_mock, people_mock]):
        result = await linkedin_tool.linkedin_people_search(
            name="Max",
            location="San Francisco, CA"
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "Max Lopez" in str(result)

@pytest.mark.asyncio
async def test_api_error_handling(linkedin_tool):
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("API Error")
    
    with patch('httpx.AsyncClient.get', return_value=mock_response):
        with pytest.raises(Exception):
            await linkedin_tool.get_linkedin_profile_info(
                "https://www.linkedin.com/in/nonexistent/"
            )

def test_missing_api_key():
    # Create a new instance without setting the environment variable
    tool = LinkedinDataTool()
    result = tool.get_api_key()
    assert result is None

def test_linkedin_people_search_tst(linkedin_tool):
    """Test the test/mock version of linkedin_people_search that returns hardcoded data."""
    result = linkedin_tool.linkedin_people_search_tst(name="Scott Persinger")
    
    # Verify the response contains expected data
    assert "Scott Persinger" in result
    assert "Council Bluffs, IA" in result
    assert "Chicago, IL" in result
    assert "St. Petersburg, FL" in result
    assert "San Francisco, CA" in result
    assert "CEO at Supercog AI" in result
    assert "Stripe" in result
    assert "Heroku" in result

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 