import os
from agentic.common import Agent, AgentRunner
from agentic.tools import GooglePlacesTool, GoogleGeocodingTool

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


def create_report(places_api_data: str, user_preferences: str):
    """
    Creates a formatted string of restaurant descriptions and user preferences for use in querying the LLM for a ranking report.

    Args:
        places_api_data (list): a string containing what the places api sends back 

        user_preferences (str): a string explaining the user's preferences

    Returns:
        result: A formatted description of restaurants.
    """
    print("Called create report")
    

    # Construct the prompt for the LLM
    result = f"""You are a restaurant recommendation assistant. Based on the following user preferences: 
    {user_preferences}"""


    result += f"""
Rank the following restaurants and provide a detailed report:\n
{places_api_data}

Include the ranking, reasoning for each choice, and any additional suggestions.
"""
    return result

ranking_agent = Agent(
    name="Ranking Agent",
    instructions="Follow the given instructions",
)

restaurant_agent = Agent(
    name="Restaurant Agent",
    welcome="""I am the Restaurant Recommendation Agent.
Provide your location, the max distance you're willing to travel, time you're planning on eating, food type, and any other preferences and I'll rank relevant restaurants in your area.
""",
    instructions="""You provide restaurant recommendations based on location and user preferences.
The user will input a location, a max distance, a time for eating, what type of food they want to eat, and any other preferences.
You must call the GoogleGeocodingTool to get the longitude and latitude of the location, and then use the GooglePlacesTool to find nearby restaurants.
When you are done with this, call the ranking agent with the result of create_report and output what it says.
""",
    tools=[GooglePlacesTool(), GoogleGeocodingTool(), create_report, ranking_agent],
    memories=[
            "valid fieldmask types: places.displayName, places.formattedAddress, places.types, places.location, places.priceRange, places.rating, places.allowsDogs, places.dineIn, places.delivery, places.goodForChildren, places.goodForGroups, places.reviews, places.servesBreakfast, places.servesBrunch, places.servesLunch, places.servesDinner, places.servesVegetarianFood, places.currentOpeningHours",
            "valid includedTypes types: restaurant, cafe, bakery, bar, meal_takeaway, meal_delivery fast_food, afghani_restaurant, african_restaurant, american_restaurant, asian_restaurant, brazilian_restaurant, chinese_restaurant, dessert_restaurant, french_restaurant, greek_restaurant,indian_restaurant, indonesian_restaurant, italian_restaurant, japanese_restaurant, korean_restaurant, lebanese_restaurant, mediterranean_restaurant, mexican_restaurant, middle_eastern_restaurant, pizza_restaurant, ramen_restaurant, seafood_restaurant, spanish_restaurant, steak_house, sushi_restaurant, thai_restaurant, turkish_restaurant, vegan_restaurant, vegetarian_restaurant, vietnamese_restaurant"
        ],
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