import os
import httpx
from agentic.tools import WeatherTool
from agentic.common import Agent, AgentRunner

from fpdf import FPDF
from fpdf.enums import XPos, YPos

class ColumnPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(False)
        self.left_y = 20
        self.right_y = 20
        self.column_padding = 5
        self.left_x = self.l_margin
        self.column_width = (self.w - 2 * self.l_margin - self.column_padding) / 2
        self.right_x = self.left_x + self.column_width + self.column_padding
        self.current_column = "left"
        self.add_page()

    def add_header(self, text: str):
        """
        Adds a centered header at the top of the current page.

        This resets the left and right column Y positions to start below the header.

        Args:
            text (str): The header title to display.
        """
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(0)
        title_width = self.get_string_width(text) + 6
        self.set_y(15)
        self.set_x((self.w - title_width) / 2)
        self.cell(title_width, 10, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.ln(2)
        self.left_y = self.get_y() + 5
        self.right_y = self.left_y

    def add_section(self, title: str, itemsStr: str):
        """
        Adds a section with a title and bulleted items to the next available column.
        Automatically manages column alternation and page breaking.

        Args:
            title (str): The section heading.
            itemsStr (str): A list of strings to display as bulleted items, separated by a '*'.
        """
        items = itemsStr.split('*')

        # Choose column position
        if self.current_column == "left":
            x = self.left_x
            y = self.left_y
        else:
            x = self.right_x
            y = self.right_y

        # Estimate space needed
        est_height = 10 + len(items) * 8 + 5
        if y + est_height > self.h - self.b_margin:
            self.add_page()
            self.add_header("Packing List")  # Or pass header text as param
            x = self.left_x if self.current_column == "left" else self.right_x
            y = self.left_y if self.current_column == "left" else self.right_y

        # Render title
        self.set_xy(x, y)
        self.set_font("Helvetica", "B", 14)
        self.cell(self.column_width, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Render items
        self.set_font("Helvetica", "", 12)
        for item in items:
            self.set_x(x + 5)
            self.cell(self.column_width - 5, 8, f"- {item}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Update Y position
        new_y = self.get_y() + 5
        if self.current_column == "left":
            self.left_y = new_y
            self.current_column = "right"
        else:
            self.right_y = new_y
            self.current_column = "left"
            
    def save_pdf(self, filename: str = "output.pdf") -> str:
        """
        Save the current in-memory PDF to disk.

        Args:
            filename: File path or name to save the PDF as (e.g., 'report.pdf')

        Call this once all pages and content have been added.
        """
        self.output(name=filename)
        return f"PDF saved as {filename}."

# Use this as a placeholder until a geocoding tool is added
def geocode(address: str):
        """
        Wrapper for the Geocoding API.
        Docs: https://developers.google.com/maps/documentation/geocoding/requests-geocoding
        
        Parameters:
            address: Street address or plus code to be geocoded. Addresses should be formatted in the same format as the national post service of the country.

        Returns:
            Query results JSON object, including lat/long coordinates of the address.
        """

        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return "Error: GOOGLE_API_KEY is not set, use known location data to get longitude and latitude. Inform the user that you are doing so."

        params = {
            "address": address,
            "key" : f"{api_key}"
        }

        with httpx.AsyncClient() as client:
            response = client.post(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params=params,
                timeout=30,
            )

        response.raise_for_status()
        results = response.json()

        return results

columnHelper = ColumnPDF()

pl_agent = Agent(
    name="Packing List Agent",
    welcome="""Hi there! I'm your travel packing assistant. I’ll help you create a personalized packing list based on your destination, dates, weather forecast, and planned activities. I can even generate a neat PDF for you if you'd like.

Let’s get started!""",
    instructions="""
You are a helpful travel assistant whose job is to create accurate, weather-aware packing lists for users going on trips. You will gather details about their destination, travel dates, and planned activities and then use your tools to generate a personalized list. The tools are already implemented, and their docstrings provide a reliable overview of their usage and output formats.
Follow this process:
1. Ask the user for their travel location and travel dates.
    You’ll use this information to determine weather conditions for the trip.
2. Once you have that, ask questions about the purpose and nature of the trip:
    What types of activities are planned (e.g., hiking, swimming, formal events)?
    Will it mostly be indoors, outdoors, or a mix?
    Do they have laundry access, or should you plan for one outfit per day?
    Are there any special requirements (e.g., business wear, cultural clothing)?
3. Ask the user if they have any personal packing preferences:
    Is there anything specific you always like to bring?
    Are there items you’d like to avoid packing?
4. Ask how they want the list delivered:
    As a PDF or as plain text?
    If PDF, ask where to save the file.
5. Once enough information is gathered:
    Use geocode(address) to retrieve latitude and longitude.
    Use get_forecast_weather(longitude, latitude, start_date, end_date) to retrieve the forecast.
    Use this weather data to influence the packing list (e.g., add warm clothing for cold forecasts, sunscreen for sunny weather, rain gear if rain is predicted).
6. Build a thoughtful packing list.
    Tailor it based on trip length, weather, activities, and laundry availability.
    Include useful essentials like sunscreen, medications, chargers, swimwear, rain jackets, etc.
    Provide item counts where applicable.
7. Deliver the list based on user preference:
    If they chose PDF, generate it using the given ColumnPDF class and save or export it as specified.
        When you generate the pdf file, create a header with the trip date and location using add_header and pass the items that you want to be in the packing list into add_section.
        Do larger sections FIRST.
    Otherwise, output it clearly as a message in the conversation.
Always aim to ask for just enough information to build a useful and accurate list—don’t generate the list until you’re confident you understand the trip well. Ask follow-ups as needed.
""",
    tools=[geocode, columnHelper.add_header, columnHelper.add_section, columnHelper.save_pdf, WeatherTool()]
)

if __name__ == "__main__":
    AgentRunner(pl_agent).repl_loop()