import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from agentic.tools.geolocation_tool import GeolocationTool

@pytest.fixture
def geolocation_tool():
    return GeolocationTool()

@pytest.mark.asyncio
async def test_get_time(geolocation_tool):
    # Test that get_time returns a valid ISO format datetime string
    result = await geolocation_tool.get_time()
    
    # Should be a string
    assert isinstance(result, str)
    
    # Should be a valid ISO format datetime
    try:
        datetime.fromisoformat(result)
    except ValueError:
        pytest.fail("Returned time is not in ISO format")

@pytest.mark.asyncio
async def test_get_timezone(geolocation_tool, mocker):
    # Mock tzlocal to return a known timezone
    mock_tz = mocker.patch('agentic.tools.geolocation_tool.tzlocal')
    mock_tz.get_localzone.return_value = 'America/New_York'
    
    result = await geolocation_tool.get_timezone()
    
    assert result == 'America/New_York'
    mock_tz.get_localzone.assert_called_once()


@pytest.mark.asyncio
async def test_get_ip_success(geolocation_tool, mocker):
    # Mock the requests
    mock_requests = mocker.patch('agentic.tools.geolocation_tool.requests')
    
    # Mock the ipify response
    ip_response = MagicMock()
    ip_response.json.return_value = {'ip': '123.45.67.89'}
    ip_response.raise_for_status.return_value = None
    mock_requests.get.return_value = ip_response
    
    # Call the method
    result = await geolocation_tool.get_ip()
    
    # Verify the result contains the IP address
    assert '123.45.67.89' in result
    
    # Verify the request was made correctly
    mock_requests.get.assert_called_once()
    assert 'ipify.org' in mock_requests.get.call_args[0][0]

@pytest.mark.asyncio
async def test_get_ip_request_error(geolocation_tool, mocker):
    # Mock the requests module and its exceptions
    mock_requests = mocker.patch('agentic.tools.geolocation_tool.requests')
    
    # Create a mock exception class that inherits from Exception
    class MockRequestException(Exception):
        pass
    
    # Set up the mock to raise our custom exception
    mock_requests.exceptions.RequestException = MockRequestException
    mock_requests.get.side_effect = MockRequestException("Network error")
    
    # Call the method and expect an exception to be caught and printed
    with patch('builtins.print') as mock_print:
        result = await geolocation_tool.get_ip()
        
        # Verify that an error message was printed
        mock_print.assert_called()
        assert "An error occurred while getting ip: Network error" in str(mock_print.call_args[0][0])

@pytest.mark.asyncio
async def test_get_location_success(geolocation_tool, mocker):
    # Mock the requests
    mock_requests = mocker.patch('agentic.tools.geolocation_tool.requests')
    
    # Mock the ipinfo response
    location_response = MagicMock()
    location_response.json.return_value = {
        'ip': '123.45.67.89',
        'city': 'Test City',
        'region': 'Test Region',
        'country': 'US',
        'loc': '40.7128,-74.0060',
        'org': 'Test ISP',
        'timezone': 'America/New_York'
    }
    location_response.raise_for_status.return_value = None
    mock_requests.get.return_value = location_response
    
    # Call the method with a test IP
    test_ip = '123.45.67.89'
    result = await geolocation_tool.get_location(test_ip)
    
    # Verify the result contains expected information
    assert 'Test City' in result
    assert 'Test Region' in result
    assert 'US' in result
    assert '40.7128,-74.0060' in result
    assert 'Test ISP' in result
    assert 'America/New_York' in result
    assert test_ip in result
    
    # Verify the request was made correctly
    mock_requests.get.assert_called_once()
    assert test_ip in mock_requests.get.call_args[0][0]
    assert 'ipinfo.io' in mock_requests.get.call_args[0][0]

@pytest.mark.asyncio
async def test_get_location_without_ip(geolocation_tool, mocker):
    # Mock the requests
    mock_requests = mocker.patch('agentic.tools.geolocation_tool.requests')
    
    # Mock the ipify response
    ip_response = MagicMock()
    ip_response.json.return_value = {'ip': '123.45.67.89'}
    ip_response.raise_for_status.return_value = None
    
    # Mock the ipinfo response
    location_response = MagicMock()
    location_response.json.return_value = {
        'ip': '123.45.67.89',
        'city': 'Test City',
        'region': 'Test Region',
        'country': 'US',
        'loc': '40.7128,-74.0060',
        'org': 'Test ISP',
        'timezone': 'America/New_York'
    }
    location_response.raise_for_status.return_value = None
    
    # Set up the mock to return different responses for different URLs
    mock_requests.get.side_effect = [ip_response, location_response]
    
    # Call the method without an IP
    result = await geolocation_tool.get_location()
    
    # Verify the result contains expected information
    assert 'Test City' in result
    assert '123.45.67.89' in result
    
    # Verify both requests were made
    assert mock_requests.get.call_count == 2
    assert 'ipify.org' in mock_requests.get.call_args_list[0][0][0]
    assert 'ipinfo.io' in mock_requests.get.call_args_list[1][0][0]

@pytest.mark.asyncio
async def test_get_tools(geolocation_tool):
    # Test that get_tools returns the expected list of callable methods
    tools = geolocation_tool.get_tools()
    
    assert len(tools) == 4
    assert geolocation_tool.get_time in tools
    assert geolocation_tool.get_timezone in tools
    assert geolocation_tool.get_ip in tools
    assert geolocation_tool.get_location in tools