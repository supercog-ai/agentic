import httpx
import os
import pandas as pd
from typing import Dict, Callable, ClassVar, Optional

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry

@tool_registry.register(
    name="LinkedinDataTool",
    description="A tool for interacting with LinkedIn data.",
    dependencies=[],
    config_requirements=[],
)

class LinkedinDataTool(BaseAgenticTool):
    BASE_URL: ClassVar[str] = "https://linkedin-data-api.p.rapidapi.com"

    def __init__(self):
        super().__init__()

    def get_api_key(self) -> str | None:
        """Retrieve RAPIDAPI_KEY."""
        return os.environ.get("RAPIDAPI_KEY")

    def get_headers(self) -> Dict[str, str]:
        """Generate the headers required for the API request."""
        return {
            "x-rapidapi-host": "linkedin-data-api.p.rapidapi.com",
            "x-rapidapi-key": self.get_api_key(),
        }

    def get_tools(self) -> list[Callable]:
        return [
            self.get_linkedin_profile_info,
            self.get_company_linkedin_info,
            self.linkedin_people_search,
        ]

    async def search_location(self, keyword: str) -> str:
        """Search for LinkedIn location ID by keyword.

        Args:
            keyword: Location name to search for (e.g., "California")

        Returns:
            Location ID for the first matching result
        """
        if self.get_api_key() is None:
            return "Error: no API key available for the RapidAPI LinkedIn Data API"

        params = {"keyword": keyword}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search-locations",
                headers=self.get_headers(),
                params=params,
                timeout=30,
            )

        response.raise_for_status()
        results = response.json()

        if not results.get("success") or not results.get("data", {}).get("items"):
            return "No matching locations found"

        # Extract the numeric ID from the first result's URN
        first_location = results["data"]["items"][0]
        location_urn = first_location["id"]  # e.g., "urn:li:geo:102095887"
        location_id = location_urn.split(":")[-1]  # e.g., "102095887"
        return location_id

    async def get_linkedin_profile_info(self, profile_url: str) -> str:
        """Tool that queries the LinkedIn Data API and gets back profile information.
        Args:
            profile_url: Full LinkedIn profile URL (e.g., https://www.linkedin.com/in/username/)
        """
        if self.get_api_key() is None:
            return "Error: no API key available for the RapidAPI LinkedIn Data API"

        params = {"url": profile_url}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/get-profile-data-by-url",
                headers=self.get_headers(),
                params=params,
                timeout=30,
            )

        response.raise_for_status()
        profile_data = response.json()
        
        # Create a formatted string with clear sections
        profile_text = f"""
PROFILE INFORMATION:
Name: {profile_data.get('firstName', '')} {profile_data.get('lastName', '')}
Headline: {profile_data.get('headline', '')}
Location: {profile_data.get('geo', {}).get('full', '')}
Profile URL: {profile_url}
Profile Picture: {profile_data.get('profilePicture', '')}
Background Image: {profile_data.get('backgroundImage', [{}])[0].get('url', '') if profile_data.get('backgroundImage') else ''}
Is Top Voice: {profile_data.get('isTopVoice', False)}
Is Premium: {profile_data.get('isPremium', False)}

SUMMARY:
{profile_data.get('summary', '')}

CAREER PROGRESSION:"""

        # Add career progression
        positions = profile_data.get('position', [])
        for position in positions:
            start_year = position.get('start', {}).get('year', '')
            start_month = position.get('start', {}).get('month', '')
            end_year = position.get('end', {}).get('year', '')
            end_month = position.get('end', {}).get('month', '')
            
            start_date = f"{start_month}/{start_year}" if start_month else str(start_year)
            end_date = f"{end_month}/{end_year}" if end_month and end_year else "Present"
            
            profile_text += f"""

Role: {position.get('title', '')}
Company: {position.get('companyName', '')}
Company URL: {position.get('companyURL', '')}
Company Username: {position.get('companyUsername', '')}
Company Logo: {position.get('companyLogo', '')}
Company Industry: {position.get('companyIndustry', '')}
Company Size: {position.get('companyStaffCountRange', '')}
Duration: {start_date} - {end_date}
Location: {position.get('location', '')}
Employment Type: {position.get('employmentType', '')}
Description: {position.get('description', '')}"""

        profile_text += "\n\nEDUCATION:"
        
        # Add education
        for edu in profile_data.get('educations', []):
            profile_text += f"""

School: {edu.get('schoolName', '')}
School URL: {edu.get('url', '')}
School Logo: {edu.get('logo', [{}])[0].get('url', '') if edu.get('logo') else ''}
Degree: {edu.get('degree', '')}
Field of Study: {edu.get('fieldOfStudy', '')}
Grade: {edu.get('grade', '')}
Activities: {edu.get('activities', '')}
Start Year: {edu.get('start', {}).get('year', '')}
End Year: {edu.get('end', {}).get('year', '')}"""

        profile_text += "\n\nSKILLS:"
        
        # Add skills with endorsements
        for skill in profile_data.get('skills', []):
            profile_text += f"\n- {skill.get('name', '')} (Endorsements: {skill.get('endorsementsCount', 0)})"

        # Add certifications if any
        if profile_data.get('certifications'):
            profile_text += "\n\nCERTIFICATIONS:"
            for cert in profile_data.get('certifications', []):
                profile_text += f"""
- Name: {cert.get('name', '')}
  Authority: {cert.get('authority', '')}
  Company: {cert.get('company', {}).get('name', '')}"""

        # Add honors if any
        if profile_data.get('honors'):
            profile_text += "\n\nHONORS & AWARDS:"
            for honor in profile_data.get('honors', []):
                profile_text += f"""
- Title: {honor.get('title', '')}
  Description: {honor.get('description', '')}
  Issuer: {honor.get('issuer', '')}"""

        # Add courses if any
        if profile_data.get('courses'):
            profile_text += "\n\nCOURSES:"
            for course in profile_data.get('courses', []):
                profile_text += f"\n- {course.get('name', '')}"

        # Add volunteering if any
        if profile_data.get('volunteering'):
            profile_text += "\n\nVOLUNTEERING EXPERIENCE:"
            for vol in profile_data.get('volunteering', []):
                profile_text += f"""
- Title: {vol.get('title', '')}
  Organization: {vol.get('companyName', '')}
  URL: {vol.get('companyUrl', '')}"""

        return profile_text
    

    async def get_company_linkedin_info(
        self, company_username_or_domain: str
    ) -> str | pd.DataFrame:
        """queries the LinkedIn Data API of rapidapi to get company information either by username or domain.
        Args:
            company_username_or_domain: Company username (e.g., "Google") or domain (e.g., "google.com")
        """
        if self.get_api_key() is None:
            return "Error: no API key available for the RapidAPI LinkedIn Data API"

        # Determine if input is a domain by checking for '.'
        is_domain = "." in company_username_or_domain

        # Set up the appropriate endpoint and parameters
        if is_domain:
            endpoint = f"{self.BASE_URL}/get-company-by-domain"
            params = {"domain": company_username_or_domain}
        else:
            endpoint = f"{self.BASE_URL}/get-company-details"
            params = {"username": company_username_or_domain}

        # Make the API request
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    endpoint,
                    headers=self.get_headers(),
                    params=params,
                    timeout=30,
                )
                response.raise_for_status()
                company_data = response.json()

                # Check if the API request was successful
                if not company_data.get("success"):
                    error_message = company_data.get("message", "Unknown error")
                    return f"Error: {error_message}"

                # Extract data and handle cases where data might be None
                data = company_data.get("data", {})
                if data is None:
                    return "No company data found"

                # Convert data to list format for DataFrame
                if isinstance(data, dict):
                    items = [data]  # Single company result
                elif isinstance(data, list):
                    items = data  # Multiple company results
                else:
                    items = []  # No results

                if not items:
                    return "No company information found"

                # Convert to DataFrame for consistent output format
                df = pd.DataFrame(items)
                return df

            except httpx.HTTPStatusError as e:
                return f"Error: API request failed with status code {e.response.status_code}"
            except httpx.RequestError as e:
                return f"Error: Failed to make API request - {str(e)}"
            except Exception as e:
                return f"Error: Unexpected error occurred - {str(e)}"

    async def linkedin_people_search(
        self,
        name: Optional[str] = None,
        location: Optional[str] = None,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        start: str = "0",
    ) -> list[dict]:
        """searches for LinkedIn profiles based on various criteria.
        Args:
            name: Full name or partial name to search for
            location: Either a location name (e.g., "California") or a geo ID (e.g., "102095887")
            job_title: Job title to search for
            company: Company name to search for
            start: start index (0, 10, 20, etc.)
        """
        if self.get_api_key() is None:
            return "Error: no API key RAPIDAPI_KEY available for the RapidAPI LinkedIn Data API"

        # Build search parameters
        params = {"start": start}

        # Add name-related parameters
        if name:
            if " " in name:
                first_name, last_name = name.split(" ", 1)
                params["firstName"] = first_name
                params["lastName"] = last_name
            else:
                params["keywords"] = name

        # Handle location - if it's numeric, use as is, otherwise search for location ID
        if location:
            if location.isdigit():
                params["geo"] = location
            else:
                location_id = await self.search_location(location)
                if not location_id.startswith("Error") and not location_id.startswith(
                    "No matching"
                ):
                    params["geo"] = location_id

        # Add other search parameters
        if job_title:
            params["keywordTitle"] = job_title
        if company:
            params["company"] = company

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search-people",
                headers=self.get_headers(),
                params=params,
                timeout=30,
            )

        response.raise_for_status()
        search_results = response.json()

        # Check if the search was successful and has results
        if not search_results.get("success"):
            return f"Search failed: {search_results.get('message', 'Unknown error')}"

        data = search_results.get("data", {})
        total_results = data.get("total", 0)
        items = data.get("items", [])

        if total_results == 0 or not items:
            return "No results found for your search criteria"

        # ToolFactory will automatically convert this list to a DataFrame
        return items

    def linkedin_people_search_tst(self, name: str, company: Optional[str] = "") -> str:
        return """
1. **Scott Persinger**
   - **Title:** Assistant Vice President, Information Technology
   - **Location:** Council Bluffs, IA
   - [View Profile](https://www.linkedin.com/in/scott-persinger-79569144)

2. **Scott Persinger**
   - **Title:** Associate at Skadden, Arps, Slate, Meagher & Flom LLP
   - **Location:** Chicago, IL
   - [View Profile](https://www.linkedin.com/in/scott-persinger-313166134)

3. **Scott Persinger**
   - **Title:** Engagement Manager at GlideFast Consulting
   - **Location:** St. Petersburg, FL
   - ![Profile Picture](https://media.licdn.com/dms/image/v2/D4E03AQFgPDXDb4R-pg/profile-displayphoto-shrink_100_100/profile-displayphoto-shrink_100_100/0/1722259230079?e=1744243200&v=beta&t=0u1lTxPPIoCqMr7Xg5SKwCcdiWefdb1Cxs76yz_tRYQ)
   - [View Profile](https://www.linkedin.com/in/scott-persinger-13270b4)

4. **Scott Persinger**
   - **Title:** CEO at Supercog AI, previous positions at Tatari, Stripe, Heroku, founder at CloudConnect
   - **Location:** San Francisco, CA
   - ![Profile Picture](https://media.licdn.com/dms/image/v2/C5603AQEkZLLKGXHz_g/profile-displayphoto-shrink_100_100/profile-displayphoto-shrink_100_100/0/1577142760426?e=1744243200&v=beta&t=tJq5QtTCCA11s83DVL-v9YbF1jW3VnMPytRs3YWHisU)
   - [View Profile](https://www.linkedin.com/in/scottpersinger)
"""
