import os
from agentic.common import Agent, AgentRunner
from agentic.tools import GooglePlacesTool, GoogleGeocodingTool
from openai import OpenAI

# Sample data
# places_api_data = {
#     "places": [
#         {
#             "displayName": "Pasta Paradise",
#             "id": "1",
#             "rating": 4.5,
#             "userRatingCount": 120,
#             "priceLevel": "$$",
#             "primaryType": "Italian Restaurant",
#             "types": ["Italian", "Casual Dining"],
#             "reviews": [
#                 "Amazing pasta dishes and great ambiance!",
#                 "Friendly staff and delicious food.",
#                 "Best Italian restaurant in town!",
#                 "Good value for money.",
#                 "Highly recommend the lasagna."
#             ]
#         },
#     ]
# }
# Sample user preferences
# preferences = {"cuisine": "Italian", "budget": "$$", "time_of_day": "dinner"}


def create_report(places_api_data, user_preferences):
    """
    Creates a formatted string of restaurant descriptions and user preferences for use in querying the LLM for a ranking report.

    Args:
        places_api_data (list): A list of dictionaries containing restaurant information from the Places API.  

        user_preferences (dict): A dictionary containing user preferences.
            Example: {"cuisine": "Italian", "budget": "$$", "time_of_day": "dinner"}

    Returns:
        result: A formatted description of restaurants.
    """
    # Transform Places API data to match the expected format
    formatted_string = ''
    for index in range(len(places_api_data['places'])):
        restaurant = places_api_data["places"][index]
        formatted_string += f'Restaurant {index + 1}: {restaurant['displayName']}'
        formatted_string += f'\nUser rating (out of 5): {restaurant["rating"]} from {restaurant['userRatingCount']} reviews'
        formatted_string += f'\nPrice level: {restaurant["priceLevel"]}'
        formatted_string += f'\nDescription: {restaurant['primaryType']}, '
        for type in restaurant["types"]:
            formatted_string += f'{type}, '
        formatted_string += f'\nTop five reviews: \n'
        for review in restaurant['reviews']:
            formatted_string += f'\t{review}\n'
        formatted_string +=  '\n'

    # Construct the prompt for the LLM
    result = f"""You are a restaurant recommendation assistant. Based on the following user preferences: """

    for key in user_preferences:
        prompt += f'{key}: {user_preferences[key]}\n'

    result += f"""
Rank the following restaurants and provide a detailed report:\n
{formatted_string}

Include the ranking, reasoning for each choice, and any additional suggestions.
"""

    return result


restaurant_agent = Agent(
        name="Restaurant Agent",
        welcome="""I am the Restaurant Recommendation Agent.
Provide your location, the max distance you're willing to travel, time you're planning on eating, food type, and any other preferences and I'll rank relevant restaurants in your area.
""",
        instructions="""You provide restaurant recommendations based on location and user preferences.
The user will input a location, a max distance, a time for eating, what type of food they want to eat, and any other preferences.
You must call the GoogleGeocodingTool to get the longitude and latitude of the location, and then use the GooglePlacesTool to find nearby restaurants.
When you are done with this, generate a ranking according to the user's preferences.
If you get a tool error, stop.
""",
        tools=[GooglePlacesTool(), GoogleGeocodingTool(), create_report],
)

if __name__ == "__main__":
    AgentRunner(restaurant_agent).repl_loop()
    
# Data format: {
#     "name": string,
#     "id": string,
#     "displayName": {
#         object (LocalizedText)
#     },
#     "types": [
#         string
#     ],
#     "primaryType": string,
#     "primaryTypeDisplayName": {
#         object (LocalizedText)
#     },
#     "nationalPhoneNumber": string,
#     "internationalPhoneNumber": string,
#     "formattedAddress": string,
#     "shortFormattedAddress": string,
#     "postalAddress": {
#         object (PostalAddress)
#     },
#     "addressComponents": [
#         {
#         object (AddressComponent)
#         }
#     ],
#     "plusCode": {
#         object (PlusCode)
#     },
#     "location": {
#         object (LatLng)
#     },
#     "viewport": {
#         object (Viewport)
#     },
#     "rating": number,
#     "googleMapsUri": string,
#     "websiteUri": string,
#     "reviews": [
#         {
#         object (Review)
#         }
#     ],
#     "regularOpeningHours": {
#         object (OpeningHours)
#     },
#     "timeZone": {
#         object (TimeZone)
#     },
#     "photos": [
#         {
#         object (Photo)
#         }
#     ],
#     "adrFormatAddress": string,
#     "businessStatus": enum (BusinessStatus),
#     "priceLevel": enum (PriceLevel),
#     "attributions": [
#         {
#         object (Attribution)
#         }
#     ],
#     "iconMaskBaseUri": string,
#     "iconBackgroundColor": string,
#     "currentOpeningHours": {
#         object (OpeningHours)
#     },
#     "currentSecondaryOpeningHours": [
#         {
#         object (OpeningHours)
#         }
#     ],
#     "regularSecondaryOpeningHours": [
#         {
#         object (OpeningHours)
#         }
#     ],
#     "editorialSummary": {
#         object (LocalizedText)
#     },
#     "paymentOptions": {
#         object (PaymentOptions)
#     },
#     "parkingOptions": {
#         object (ParkingOptions)
#     },
#     "subDestinations": [
#         {
#         object (SubDestination)
#         }
#     ],
#     "fuelOptions": {
#         object (FuelOptions)
#     },
#     "evChargeOptions": {
#         object (EVChargeOptions)
#     },
#     "generativeSummary": {
#         object (GenerativeSummary)
#     },
#     "containingPlaces": [
#         {
#         object (ContainingPlace)
#         }
#     ],
#     "addressDescriptor": {
#         object (AddressDescriptor)
#     },
#     "googleMapsLinks": {
#         object (GoogleMapsLinks)
#     },
#     "priceRange": {
#         object (PriceRange)
#     },
#     "reviewSummary": {
#         object (ReviewSummary)
#     },
#     "evChargeAmenitySummary": {
#         object (EvChargeAmenitySummary)
#     },
#     "neighborhoodSummary": {
#         object (NeighborhoodSummary)
#     },
#     "utcOffsetMinutes": integer,
#     "userRatingCount": integer,
#     "takeout": boolean,
#     "delivery": boolean,
#     "dineIn": boolean,
#     "curbsidePickup": boolean,
#     "reservable": boolean,
#     "servesBreakfast": boolean,
#     "servesLunch": boolean,
#     "servesDinner": boolean,
#     "servesBeer": boolean,
#     "servesWine": boolean,
#     "servesBrunch": boolean,
#     "servesVegetarianFood": boolean,
#     "outdoorSeating": boolean,
#     "liveMusic": boolean,
#     "menuForChildren": boolean,
#     "servesCocktails": boolean,
#     "servesDessert": boolean,
#     "servesCoffee": boolean,
#     "goodForChildren": boolean,
#     "allowsDogs": boolean,
#     "restroom": boolean,
#     "goodForGroups": boolean,
#     "goodForWatchingSports": boolean,
#     "accessibilityOptions": {
#         object (AccessibilityOptions)
#     },
#     "pureServiceAreaBusiness": boolean
#     }