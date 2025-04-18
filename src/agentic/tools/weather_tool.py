from typing import Callable
import requests
from datetime import datetime, timedelta
import zoneinfo
import statistics

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry

@tool_registry.register(
    name="WeatherTool",
    description="A tool for getting weather information",
    dependencies=[],
    config_requirements=[],
)
class WeatherTool(BaseAgenticTool):
    """Functions for getting weather information."""

    def __init__(self):
        pass

    def get_tools(self) -> list[Callable]:
        return [
            self.get_current_weather,
            self.get_forecast_weather,
            self.get_historical_weather,
            self.get_historical_averages,
        ]

    def _get_current_datetime_with_timezone(self):
        # Get the current date and time
        current_datetime = datetime.now()

        # Get the system's timezone
        system_timezone = zoneinfo.ZoneInfo(
            zoneinfo.available_timezones().pop()
        )  # or replace with your system's timezone string

        # Attach the timezone to the datetime object
        current_datetime_with_tz = current_datetime.replace(tzinfo=system_timezone)

        # Format the output
        formatted_output = current_datetime_with_tz.strftime("%Y-%m-%d %H:%M:%S %Z")

        return formatted_output

    def get_current_weather(
        self,
        longitude: str = "-122.2730",  # Berkeley
        latitude: str = "37.8715",
        temperature_unit: str = "fahrenheit",  # 'celsius' or 'fahrenheit'
    ) -> str:
        """
        Get the current weather for the passed in region

        Args:
            longitude: str: Location longitude (should be between -180 and 180)
            latitude: str: Location latitude (should be between -90 and 90)
            temperature_unit: str: 'celsius' or 'fahrenheit' (default: 'fahrenheit')
        """
        # Open-Meteo endpoint for current weather
        url = "https://api.open-meteo.com/v1/forecast"

        # Set temperature unit symbol based on unit choice
        temp_symbol = "°F" if temperature_unit.lower() == "fahrenheit" else "°C"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "auto",
            "temperature_unit": temperature_unit.lower(),
            "current_weather": "true",
            "hourly": [
                "temperature_2m",
                "apparent_temperature",
                "precipitation",
                "rain",
                "snowfall",
                "weathercode",
                "cloudcover",
                "windspeed_10m",
                "winddirection_10m",
                "windgusts_10m",
                "relative_humidity_2m",
                "visibility",
                "uv_index",
                "is_day",
            ],
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            current_datetime = self._get_current_datetime_with_timezone()

            # Initialize return string with current time
            return_string = f"Current Weather as of: {current_datetime}\n"

            # Get current weather data
            current_weather = data.get("current_weather", {})
            hourly = data.get("hourly", {})

            # Find the current hour's index in the hourly data
            current_time = current_weather.get("time")
            if current_time and "time" in hourly:
                try:
                    current_index = hourly["time"].index(current_time)
                except ValueError:
                    current_index = 0  # Fallback to first hour if time not found
            else:
                current_index = 0

            # Add basic current weather information
            if current_weather:
                temp = current_weather.get("temperature")
                if temp is not None:
                    return_string += f"Temperature: {temp}{temp_symbol}\n"

                windspeed = current_weather.get("windspeed")
                if windspeed is not None:
                    return_string += f"Wind Speed: {windspeed}km/h\n"

                winddirection = current_weather.get("winddirection")
                if winddirection is not None:
                    return_string += f"Wind Direction: {winddirection}°\n"

                weathercode = current_weather.get("weathercode")
                if weathercode is not None:
                    return_string += f"Weather Code: {weathercode}\n"

            # Add additional current conditions from hourly data
            if hourly and current_index is not None:
                # Apparent temperature
                apparent_temp = hourly.get("apparent_temperature", [None])[
                    current_index
                ]
                if apparent_temp is not None:
                    return_string += f"Feels Like: {apparent_temp}{temp_symbol}\n"

                # Precipitation
                precip = hourly.get("precipitation", [None])[current_index]
                if precip is not None:
                    return_string += f"Precipitation: {precip}mm\n"

                # Rain
                rain = hourly.get("rain", [0])[current_index]
                if rain and rain > 0:
                    return_string += f"Rain: {rain}mm\n"

                # Snowfall
                snow = hourly.get("snowfall", [0])[current_index]
                if snow and snow > 0:
                    return_string += f"Snowfall: {snow}cm\n"

                # Cloud Cover
                cloud = hourly.get("cloudcover", [None])[current_index]
                if cloud is not None:
                    return_string += f"Cloud Cover: {cloud}%\n"

                # Wind Gusts
                gusts = hourly.get("windgusts_10m", [None])[current_index]
                if gusts is not None:
                    return_string += f"Wind Gusts: {gusts}km/h\n"

                # Humidity
                humidity = hourly.get("relative_humidity_2m", [None])[current_index]
                if humidity is not None:
                    return_string += f"Relative Humidity: {humidity}%\n"

                # Visibility
                visibility = hourly.get("visibility", [None])[current_index]
                if visibility is not None:
                    return_string += f"Visibility: {visibility}m\n"

                # UV Index
                uv = hourly.get("uv_index", [None])[current_index]
                if uv is not None:
                    return_string += f"UV Index: {uv}\n"

                # Is Day
                is_day = hourly.get("is_day", [None])[current_index]
                if is_day is not None:
                    return_string += f"Daylight: {'Yes' if is_day else 'No'}\n"

            return return_string
        else:
            return f"Failed to retrieve data: {response.status_code}\nResponse: {response.text}"

    def get_forecast_weather(
        self,
        longitude: str = "-122.2730",  # Berkeley
        latitude: str = "37.8715",
        forecast_type: str = "daily",
        start_date: str = None,  # Format: "YYYY-MM-DD"
        end_date: str = None,  # Format: "YYYY-MM-DD"
        temperature_unit: str = "fahrenheit",  # 'celsius' or 'fahrenheit'
    ) -> str:
        """
        Get the forecasted weather for the passed in region

        Args:
            longitude: str: Location longitude (should be between -180 and 180)
            latitude: str: Location latitude (should be between -90 and 90)
            forecast_type: str: can be 'hourly' (7 days) or 'daily' (16 days)
            start_date: str: Start date for forecast (YYYY-MM-DD)
            end_date: str: End date for forecast (YYYY-MM-DD)
            temperature_unit: str: 'celsius' or 'fahrenheit' (default: 'fahrenheit')
        """
        url = "https://api.open-meteo.com/v1/forecast"

        # Set temperature unit symbol based on unit choice
        temp_symbol = "°F" if temperature_unit.lower() == "fahrenheit" else "°C"

        # Base parameters
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "auto",
            "temperature_unit": temperature_unit.lower(),
        }

        # Add date parameters if provided
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Add forecast-specific parameters with verified API variables
        if forecast_type == "hourly":
            params["hourly"] = [
                "temperature_2m",
                "apparent_temperature",
                "precipitation",
                "rain",
                "snowfall",
                "weathercode",
                "cloudcover",
                "windspeed_10m",
                "winddirection_10m",
                "windgusts_10m",
                "relative_humidity_2m",
                "visibility",
                "uv_index",
                "is_day",
            ]
        elif forecast_type == "daily":
            params["daily"] = [
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "apparent_temperature_min",
                "precipitation_sum",
                "precipitation_hours",
                "precipitation_probability_max",
                "rain_sum",
                "snowfall_sum",
                "weathercode",
                "windspeed_10m_max",
                "windgusts_10m_max",
                "winddirection_10m_dominant",
                "sunrise",
                "sunset",
                "uv_index_max",
            ]

        # Print the URL and parameters for debugging
        print(f"Making request to: {url}")
        print(f"With parameters: {params}")

        response = requests.get(url, params=params)
        return_string = (
            f"Current Date and time is: {self._get_current_datetime_with_timezone()}\n"
        )

        if response.status_code == 200:
            data = response.json()

            if forecast_type == "hourly":
                hourly = data.get("hourly", {})
                if hourly:
                    times = hourly.get("time", [])
                    for i in range(len(times)):
                        return_string += f"Time: {times[i]}\n"

                        temp = hourly.get("temperature_2m", [None] * len(times))[i]
                        if temp is not None:
                            return_string += f"  Temperature: {temp}{temp_symbol}\n"

                        feels_like = hourly.get(
                            "apparent_temperature", [None] * len(times)
                        )[i]
                        if feels_like is not None:
                            return_string += (
                                f"  Feels Like: {feels_like}{temp_symbol}\n"
                            )

                        precip = hourly.get("precipitation", [None] * len(times))[i]
                        if precip is not None:
                            return_string += f"  Precipitation: {precip}mm\n"

                        rain = hourly.get("rain", [0] * len(times))[i]
                        if rain and rain > 0:
                            return_string += f"  Rain: {rain}mm\n"

                        snow = hourly.get("snowfall", [0] * len(times))[i]
                        if snow and snow > 0:
                            return_string += f"  Snowfall: {snow}cm\n"

                        weathercode = hourly.get("weathercode", [None] * len(times))[i]
                        if weathercode is not None:
                            return_string += f"  Weather Code: {weathercode}\n"

                        cloud = hourly.get("cloudcover", [None] * len(times))[i]
                        if cloud is not None:
                            return_string += f"  Cloud Cover: {cloud}%\n"

                        wind = hourly.get("windspeed_10m", [None] * len(times))[i]
                        if wind is not None:
                            return_string += f"  Wind Speed: {wind}km/h\n"

                        gusts = hourly.get("windgusts_10m", [None] * len(times))[i]
                        if gusts is not None:
                            return_string += f"  Wind Gusts: {gusts}km/h\n"

                        direction = hourly.get(
                            "winddirection_10m", [None] * len(times)
                        )[i]
                        if direction is not None:
                            return_string += f"  Wind Direction: {direction}°\n"

                        humidity = hourly.get(
                            "relative_humidity_2m", [None] * len(times)
                        )[i]
                        if humidity is not None:
                            return_string += f"  Humidity: {humidity}%\n"

                        visibility = hourly.get("visibility", [None] * len(times))[i]
                        if visibility is not None:
                            return_string += f"  Visibility: {visibility}m\n"

                        uv = hourly.get("uv_index", [None] * len(times))[i]
                        if uv is not None:
                            return_string += f"  UV Index: {uv}\n"

                        is_day = hourly.get("is_day", [None] * len(times))[i]
                        if is_day is not None:
                            return_string += (
                                f"  Daylight: {'Yes' if is_day else 'No'}\n"
                            )

                        return_string += "------------------------\n"

            elif forecast_type == "daily":
                daily = data.get("daily", {})
                if daily:
                    times = daily.get("time", [])
                    for i in range(len(times)):
                        return_string += f"Date: {times[i]}\n"

                        # Temperature range
                        temp_min = daily.get("temperature_2m_min", [None] * len(times))[
                            i
                        ]
                        temp_max = daily.get("temperature_2m_max", [None] * len(times))[
                            i
                        ]
                        if temp_min is not None and temp_max is not None:
                            return_string += f"  Temperature Range: {temp_min}{temp_symbol} to {temp_max}{temp_symbol}\n"

                        # Feels like range
                        feel_min = daily.get(
                            "apparent_temperature_min", [None] * len(times)
                        )[i]
                        feel_max = daily.get(
                            "apparent_temperature_max", [None] * len(times)
                        )[i]
                        if feel_min is not None and feel_max is not None:
                            return_string += f"  Feels Like Range: {feel_min}{temp_symbol} to {feel_max}{temp_symbol}\n"

                        # Precipitation
                        precip = daily.get("precipitation_sum", [None] * len(times))[i]
                        precip_hours = daily.get(
                            "precipitation_hours", [None] * len(times)
                        )[i]
                        if precip is not None and precip_hours is not None:
                            return_string += f"  Precipitation: {precip}mm over {precip_hours} hours\n"

                        # Precipitation probability
                        prob = daily.get(
                            "precipitation_probability_max", [None] * len(times)
                        )[i]
                        if prob is not None:
                            return_string += f"  Precipitation Probability: {prob}%\n"

                        # Rain and snow
                        rain = daily.get("rain_sum", [0] * len(times))[i]
                        if rain and rain > 0:
                            return_string += f"  Rain: {rain}mm\n"

                        snow = daily.get("snowfall_sum", [0] * len(times))[i]
                        if snow and snow > 0:
                            return_string += f"  Snowfall: {snow}cm\n"

                        # Weather code
                        weathercode = daily.get("weathercode", [None] * len(times))[i]
                        if weathercode is not None:
                            return_string += f"  Weather Code: {weathercode}\n"

                        # Wind information
                        wind = daily.get("windspeed_10m_max", [None] * len(times))[i]
                        if wind is not None:
                            return_string += f"  Max Wind Speed: {wind}km/h\n"

                        gusts = daily.get("windgusts_10m_max", [None] * len(times))[i]
                        if gusts is not None:
                            return_string += f"  Max Wind Gusts: {gusts}km/h\n"

                        direction = daily.get(
                            "winddirection_10m_dominant", [None] * len(times)
                        )[i]
                        if direction is not None:
                            return_string += (
                                f"  Dominant Wind Direction: {direction}°\n"
                            )

                        # Sun information
                        sunrise = daily.get("sunrise", [None] * len(times))[i]
                        if sunrise is not None:
                            return_string += f"  Sunrise: {sunrise}\n"

                        sunset = daily.get("sunset", [None] * len(times))[i]
                        if sunset is not None:
                            return_string += f"  Sunset: {sunset}\n"

                        # UV index
                        uv = daily.get("uv_index_max", [None] * len(times))[i]
                        if uv is not None:
                            return_string += f"  Max UV Index: {uv}\n"

                        return_string += "------------------------\n"

            if return_string:
                return return_string
            else:
                return "No forecast data found."
        else:
            return f"Failed to retrieve data: {response.status_code}\nResponse: {response.text}"

    def _get_historical_weather_data(
        self,
        longitude: str,
        latitude: str,
        start_date: str,
        end_date: str,
        temperature_unit: str = "fahrenheit",
        api_key: str = None,
    ) -> dict:
        """
        Internal function to fetch historical weather data for a specific date range.
        Returns raw data or error information.
        """
        url = "https://archive-api.open-meteo.com/v1/archive"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "auto",
            "temperature_unit": temperature_unit.lower(),
            "start_date": start_date,
            "end_date": end_date,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "temperature_2m_mean",
                "apparent_temperature_max",
                "apparent_temperature_min",
                "precipitation_sum",
                "rain_sum",
                "snowfall_sum",
                "precipitation_hours",
                "windspeed_10m_max",
                "windgusts_10m_max",
                "winddirection_10m_dominant",
                "shortwave_radiation_sum",
                "et0_fao_evapotranspiration",
            ],
        }

        if api_key:
            params["apikey"] = api_key

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return {
                    "status": "success",
                    "data": response.json(),
                    "message": "Data retrieved successfully",
                }
            else:
                return {
                    "status": "error",
                    "data": None,
                    "message": f"API request failed: {response.text}",
                }
        except Exception as e:
            return {
                "status": "error",
                "data": None,
                "message": f"Request failed: {str(e)}",
            }

    def get_historical_weather(
        self,
        longitude: str = "-122.2730",  # Berkeley
        latitude: str = "37.8715",
        start_date: str = None,  # Format: "YYYY-MM-DD"
        end_date: str = None,  # Format: "YYYY-MM-DD"
        temperature_unit: str = "fahrenheit",  # 'celsius' or 'fahrenheit'
        api_key: str = None,  # Optional API key for professional/production use
    ) -> str:
        """
        Get historical weather data for the specified location and date range
        """
        if not start_date or not end_date:
            return "Error: Both start_date and end_date are required for historical weather lookup"

        # Get data using internal function
        result = self._get_historical_weather_data(
            longitude=longitude,
            latitude=latitude,
            start_date=start_date,
            end_date=end_date,
            temperature_unit=temperature_unit,
            api_key=api_key,
        )

        if result["status"] != "success":
            return f"Failed to retrieve historical data: {result['message']}"

        data = result["data"]
        temp_symbol = "°F" if temperature_unit.lower() == "fahrenheit" else "°C"

        # Format the historical data
        return_string = f"Historical Weather Data from {start_date} to {end_date}\n"
        return_string += "=" * 50 + "\n\n"

        # Process daily data
        daily = data.get("daily", {})
        if daily:
            times = daily.get("time", [])
            for i in range(len(times)):
                date = times[i]
                return_string += f"Date: {date}\n"

                # Temperature data
                temp_min = daily.get("temperature_2m_min", [None] * len(times))[i]
                temp_max = daily.get("temperature_2m_max", [None] * len(times))[i]
                temp_mean = daily.get("temperature_2m_mean", [None] * len(times))[i]
                if all(x is not None for x in [temp_min, temp_max, temp_mean]):
                    return_string += f"  Temperature:\n"
                    return_string += f"    Min: {temp_min}{temp_symbol}\n"
                    return_string += f"    Max: {temp_max}{temp_symbol}\n"
                    return_string += f"    Mean: {temp_mean}{temp_symbol}\n"

                # Feels like temperature
                feel_min = daily.get("apparent_temperature_min", [None] * len(times))[i]
                feel_max = daily.get("apparent_temperature_max", [None] * len(times))[i]
                if feel_min is not None and feel_max is not None:
                    return_string += f"  Feels Like Range: {feel_min}{temp_symbol} to {feel_max}{temp_symbol}\n"

                # Precipitation data
                precip = daily.get("precipitation_sum", [None] * len(times))[i]
                precip_hours = daily.get("precipitation_hours", [None] * len(times))[i]
                if precip is not None:
                    return_string += f"  Precipitation: {precip}mm"
                    if precip_hours is not None:
                        return_string += f" over {precip_hours} hours"
                    return_string += "\n"

                # Rain and snow
                rain = daily.get("rain_sum", [0] * len(times))[i]
                if rain and rain > 0:
                    return_string += f"  Rain: {rain}mm\n"

                snow = daily.get("snowfall_sum", [0] * len(times))[i]
                if snow and snow > 0:
                    return_string += f"  Snowfall: {snow}cm\n"

                # Wind data
                wind_speed = daily.get("windspeed_10m_max", [None] * len(times))[i]
                wind_gusts = daily.get("windgusts_10m_max", [None] * len(times))[i]
                wind_dir = daily.get("winddirection_10m_dominant", [None] * len(times))[
                    i
                ]

                if any(x is not None for x in [wind_speed, wind_gusts, wind_dir]):
                    return_string += "  Wind:\n"
                    if wind_speed is not None:
                        return_string += f"    Max Speed: {wind_speed}km/h\n"
                    if wind_gusts is not None:
                        return_string += f"    Max Gusts: {wind_gusts}km/h\n"
                    if wind_dir is not None:
                        return_string += f"    Dominant Direction: {wind_dir}°\n"

                # Solar radiation and evapotranspiration
                radiation = daily.get("shortwave_radiation_sum", [None] * len(times))[i]
                if radiation is not None:
                    return_string += f"  Solar Radiation: {radiation}MJ/m²\n"

                evapotranspiration = daily.get(
                    "et0_fao_evapotranspiration", [None] * len(times)
                )[i]
                if evapotranspiration is not None:
                    return_string += f"  Evapotranspiration: {evapotranspiration}mm\n"

                return_string += "-" * 40 + "\n"

        return return_string

    def get_historical_averages(
        self,
        longitude: str = "-122.2730",
        latitude: str = "37.8715",
        target_start_date: str = None,  # Format: "MM-DD"
        target_end_date: str = None,  # Format: "MM-DD"
        temperature_unit: str = "fahrenheit",
        averaging_method: str = "mean",  # 'mean' or 'median'
        max_range_days: int = 14,  # Maximum allowed range in days
        api_key: str = None,
    ) -> str:
        """
        Get 5-year historical weather averages for a specific date range.

        Args:
            longitude: Location longitude
            latitude: Location latitude
            target_start_date: Start date in MM-DD format
            target_end_date: End date in MM-DD format
            temperature_unit: 'celsius' or 'fahrenheit'
            averaging_method: 'mean' or 'median' for calculating averages
            max_range_days: Maximum allowed range between dates
            api_key: Optional API key for professional/production use

        Returns:
            String containing averaged weather data and metadata
        """
        try:
            # Validate and process date inputs
            if not target_start_date or not target_end_date:
                return "Error: Both start and end dates are required (MM-DD format)"

            # Get current date
            current_date = datetime.now()

            # Parse target dates
            current_year = current_date.year
            try:
                # Parse target dates with current year to check range
                target_start = datetime.strptime(
                    f"{current_year}-{target_start_date}", "%Y-%m-%d"
                )
                target_end = datetime.strptime(
                    f"{current_year}-{target_end_date}", "%Y-%m-%d"
                )

                # Handle year wrap (e.g., Dec 25 - Jan 5)
                if target_end < target_start:
                    target_end = target_end.replace(year=target_end.year + 1)

                # Validate range
                date_range = (target_end - target_start).days
                if date_range > max_range_days:
                    return f"Error: Date range exceeds maximum of {max_range_days} days"

            except ValueError:
                return 'Error: Invalid date format. Use MM-DD format (e.g., "12-25")'

            # Determine years to analyze
            years_to_analyze = []
            start_year = current_year

            # If the date range is in the future for current year, start from last year
            if target_start > current_date:
                start_year -= 1

            # Get 5 years of data
            for year_offset in range(5):
                years_to_analyze.append(start_year - year_offset)

            # Collect historical data for each year
            all_data = []
            for year in years_to_analyze:
                start_date = target_start.replace(year=year).strftime("%Y-%m-%d")
                end_date = target_end.replace(year=year).strftime("%Y-%m-%d")

                result = self._get_historical_weather_data(
                    longitude=longitude,
                    latitude=latitude,
                    start_date=start_date,
                    end_date=end_date,
                    temperature_unit=temperature_unit,
                    api_key=api_key,
                )

                if result["status"] == "success":
                    all_data.append(result["data"])

            if not all_data:
                return "Error: No historical data could be retrieved"

            # Initialize storage for averaging
            daily_fields = [
                "temperature_2m_max",
                "temperature_2m_min",
                "temperature_2m_mean",
                "apparent_temperature_max",
                "apparent_temperature_min",
                "precipitation_sum",
                "rain_sum",
                "snowfall_sum",
                "precipitation_hours",
                "windspeed_10m_max",
                "windgusts_10m_max",
                "winddirection_10m_dominant",
            ]

            # Initialize storage for each field
            averaged_data = {field: [] for field in daily_fields}

            # Number of days in the date range
            num_days = (target_end - target_start).days + 1

            # Calculate averages for each day in the range
            for day_index in range(num_days):
                day_values = {field: [] for field in daily_fields}

                # Collect values from all years for this day
                for year_data in all_data:
                    if "daily" in year_data:
                        for field in daily_fields:
                            if field in year_data["daily"]:
                                value = year_data["daily"][field][day_index]
                                if value is not None:  # Skip None values
                                    day_values[field].append(value)

                # Calculate averages for each field
                for field in daily_fields:
                    values = day_values[field]
                    if values:
                        if averaging_method == "median":
                            avg_value = statistics.median(values)
                        else:  # default to mean
                            avg_value = statistics.mean(values)
                        averaged_data[field].append(round(avg_value, 2))
                    else:
                        averaged_data[field].append(None)

            # Format the response
            dates = [
                (target_start + timedelta(days=i)).strftime("%m-%d")
                for i in range(num_days)
            ]
            temp_symbol = "°F" if temperature_unit.lower() == "fahrenheit" else "°C"

            formatted_text = "Historical Weather Averages\n"
            formatted_text += "=" * 40 + "\n\n"
            formatted_text += f"Analysis of {len(years_to_analyze)} years: {', '.join(map(str, years_to_analyze))}\n"
            formatted_text += f"Using {averaging_method} averaging method\n\n"

            for i, date in enumerate(dates):
                formatted_text += f"Date: {date}\n"
                formatted_text += f"  Temperature Range: {averaged_data['temperature_2m_min'][i]}{temp_symbol} to {averaged_data['temperature_2m_max'][i]}{temp_symbol}\n"
                formatted_text += f"  Average Temperature: {averaged_data['temperature_2m_mean'][i]}{temp_symbol}\n"
                formatted_text += f"  Feels Like Range: {averaged_data['apparent_temperature_min'][i]}{temp_symbol} to {averaged_data['apparent_temperature_max'][i]}{temp_symbol}\n"

                if averaged_data["precipitation_sum"][i]:
                    formatted_text += f"  Precipitation: {averaged_data['precipitation_sum'][i]}mm over {averaged_data['precipitation_hours'][i]} hours\n"

                if averaged_data["rain_sum"][i]:
                    formatted_text += f"  Rain: {averaged_data['rain_sum'][i]}mm\n"

                if averaged_data["snowfall_sum"][i]:
                    formatted_text += (
                        f"  Snowfall: {averaged_data['snowfall_sum'][i]}cm\n"
                    )

                formatted_text += (
                    f"  Max Wind Speed: {averaged_data['windspeed_10m_max'][i]}km/h\n"
                )
                formatted_text += (
                    f"  Max Wind Gusts: {averaged_data['windgusts_10m_max'][i]}km/h\n"
                )
                formatted_text += "------------------------\n"

            return formatted_text

        except Exception as e:
            return f"Error calculating historical averages: {str(e)}"
