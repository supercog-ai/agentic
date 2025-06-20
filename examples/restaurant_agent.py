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
        tools=[GooglePlacesTool(), GoogleGeocodingTool()],
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