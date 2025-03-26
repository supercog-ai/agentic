# WeatherTool

The `WeatherTool` provides comprehensive weather information using the [Open-Meteo API](https://api.open-meteo.com). This tool allows your agents to retrieve current weather conditions, forecasts, historical weather data, and historical averages for any location.

## Features

- Get current weather conditions
- Retrieve weather forecasts (hourly or daily)
- Access historical weather data
- Calculate historical averages for specific date ranges

## Methods

### get_current_weather

```python
get_current_weather(longitude: str, latitude: str, temperature_unit: str)
```

Retrieves the current weather conditions for a specified location.

**Parameters:**

- `longitude (str)`: Location longitude (between -180 and 180)
- `latitude (str)`: Location latitude (between -90 and 90)
- `temperature_unit (str)`: 'celsius' or 'fahrenheit' (default: 'fahrenheit')

**Returns:**
A detailed string containing current weather information, including:

- Temperature
- Feels like temperature
- Wind speed and direction
- Precipitation
- Cloud cover
- Humidity
- Visibility
- UV index

### get_forecast_weather

```python
get_forecast_weather(longitude: str, latitude: str, forecast_type: str, start_date: str, end_date: str, temperature_unit: str)
```

Retrieves forecast weather data for a specific location and time range.

**Parameters:**

- `longitude (str)`: Location longitude
- `latitude (str)`: Location latitude
- `forecast_type (str)`: 'hourly' (7 days) or 'daily' (16 days)
- `start_date (Optional[str])`: Start date in YYYY-MM-DD format
- `end_date (Optional[str])`: End date in YYYY-MM-DD format
- `temperature_unit (str)`: 'celsius' or 'fahrenheit' (default: 'fahrenheit')

**Returns:**
A formatted string containing detailed forecast data for each day or hour in the requested period.

### get_historical_weather

```python
get_historical_weather(longitude: str, latitude: str, start_date: str, end_date: str, temperature_unit: str, api_key: str)
```

Retrieves historical weather data for a specific location and date range.

**Parameters:**

- `longitude (str)`: Location longitude
- `latitude (str)`: Location latitude
- `start_date (str)`: Start date in YYYY-MM-DD format
- `end_date (str)`: End date in YYYY-MM-DD format
- `temperature_unit (str)`: 'celsius' or 'fahrenheit' (default: 'fahrenheit')
- `api_key (Optional[str])`: API key for Open-Meteo Archive API

**Returns:**
A formatted string containing historical weather data for each day in the requested period.

### get_historical_averages

```python
get_historical_averages(longitude: str, latitude: str, target_start_date: str, target_end_date: str, temperature_unit: str, averaging_method: str, max_range_days: int, api_key: str)
```

Calculates 5-year historical weather averages for a specific date range.

**Parameters:**

- `longitude (str)`: Location longitude
- `latitude (str)`: Location latitude
- `target_start_date (str)`: Start date in MM-DD format
- `target_end_date (str)`: End date in MM-DD format
- `temperature_unit (str)`: 'celsius' or 'fahrenheit' (default: 'fahrenheit')
- `averaging_method (str)`: 'mean' or 'median' for calculating averages
- `max_range_days (int)`: Maximum allowed range in days (default: 14)
- `api_key (Optional[str])`: API key for Open-Meteo Archive API

**Returns:**
A formatted string containing averaged weather data for the specified date range based on historical patterns.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools.weather_tool import WeatherTool

# Create an agent with weather capabilities
weather_agent = Agent(
    name="Weather Assistant",
    instructions="You provide detailed weather information when asked.",
    tools=[WeatherTool()]
)

# Use the agent
response = weather_agent << "What's the current weather in San Francisco?"
print(response)
```
