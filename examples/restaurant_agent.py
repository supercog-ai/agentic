import os
from openai import OpenAI

def rank_restaurants_with_llm(places_api_data, user_preferences):
    """
    Uses an LLM to rank restaurants based on user preferences and data from the Google Places API.

    Args:
        places_api_data (list): A list of dictionaries containing restaurant information from the Places API.  
            Data format: {
                "name": string,
                "id": string,
                "displayName": {
                    object (LocalizedText)
                },
                "types": [
                    string
                ],
                "primaryType": string,
                "primaryTypeDisplayName": {
                    object (LocalizedText)
                },
                "nationalPhoneNumber": string,
                "internationalPhoneNumber": string,
                "formattedAddress": string,
                "shortFormattedAddress": string,
                "postalAddress": {
                    object (PostalAddress)
                },
                "addressComponents": [
                    {
                    object (AddressComponent)
                    }
                ],
                "plusCode": {
                    object (PlusCode)
                },
                "location": {
                    object (LatLng)
                },
                "viewport": {
                    object (Viewport)
                },
                "rating": number,
                "googleMapsUri": string,
                "websiteUri": string,
                "reviews": [
                    {
                    object (Review)
                    }
                ],
                "regularOpeningHours": {
                    object (OpeningHours)
                },
                "timeZone": {
                    object (TimeZone)
                },
                "photos": [
                    {
                    object (Photo)
                    }
                ],
                "adrFormatAddress": string,
                "businessStatus": enum (BusinessStatus),
                "priceLevel": enum (PriceLevel),
                "attributions": [
                    {
                    object (Attribution)
                    }
                ],
                "iconMaskBaseUri": string,
                "iconBackgroundColor": string,
                "currentOpeningHours": {
                    object (OpeningHours)
                },
                "currentSecondaryOpeningHours": [
                    {
                    object (OpeningHours)
                    }
                ],
                "regularSecondaryOpeningHours": [
                    {
                    object (OpeningHours)
                    }
                ],
                "editorialSummary": {
                    object (LocalizedText)
                },
                "paymentOptions": {
                    object (PaymentOptions)
                },
                "parkingOptions": {
                    object (ParkingOptions)
                },
                "subDestinations": [
                    {
                    object (SubDestination)
                    }
                ],
                "fuelOptions": {
                    object (FuelOptions)
                },
                "evChargeOptions": {
                    object (EVChargeOptions)
                },
                "generativeSummary": {
                    object (GenerativeSummary)
                },
                "containingPlaces": [
                    {
                    object (ContainingPlace)
                    }
                ],
                "addressDescriptor": {
                    object (AddressDescriptor)
                },
                "googleMapsLinks": {
                    object (GoogleMapsLinks)
                },
                "priceRange": {
                    object (PriceRange)
                },
                "reviewSummary": {
                    object (ReviewSummary)
                },
                "evChargeAmenitySummary": {
                    object (EvChargeAmenitySummary)
                },
                "neighborhoodSummary": {
                    object (NeighborhoodSummary)
                },
                "utcOffsetMinutes": integer,
                "userRatingCount": integer,
                "takeout": boolean,
                "delivery": boolean,
                "dineIn": boolean,
                "curbsidePickup": boolean,
                "reservable": boolean,
                "servesBreakfast": boolean,
                "servesLunch": boolean,
                "servesDinner": boolean,
                "servesBeer": boolean,
                "servesWine": boolean,
                "servesBrunch": boolean,
                "servesVegetarianFood": boolean,
                "outdoorSeating": boolean,
                "liveMusic": boolean,
                "menuForChildren": boolean,
                "servesCocktails": boolean,
                "servesDessert": boolean,
                "servesCoffee": boolean,
                "goodForChildren": boolean,
                "allowsDogs": boolean,
                "restroom": boolean,
                "goodForGroups": boolean,
                "goodForWatchingSports": boolean,
                "accessibilityOptions": {
                    object (AccessibilityOptions)
                },
                "pureServiceAreaBusiness": boolean
                }
        user_preferences (dict): A dictionary containing user preferences.
            Example: {"cuisine": "Italian", "budget": "$$", "time_of_day": "dinner"}

    Returns:
        str: A formatted ranking report of restaurants.
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
    prompt = f"""You are a restaurant recommendation assistant. Based on the following user preferences:
"""

    for key in user_preferences:
        prompt += f'{key}: {user_preferences[key]}\n'

    prompt += f"""
Rank the following restaurants and provide a detailed report:\n
{formatted_string}

Include the ranking, reasoning for each choice, and any additional suggestions.
"""
        
    try:
        # Call the OpenAI API to generate the ranking report
        api_key=os.environ["OPENAI_API_KEY"]
        client = OpenAI()
        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt
        )

        return response.output_text

    except Exception as e:
        return f"Error generating ranking report: {e}"

# Example usage
if __name__ == "__main__":
    # Sample data
    places_api_data = {
        "places": [
            {
                "displayName": "Pasta Paradise",
                "id": "1",
                "rating": 4.5,
                "userRatingCount": 120,
                "priceLevel": "$$",
                "primaryType": "Italian Restaurant",
                "types": ["Italian", "Casual Dining"],
                "reviews": [
                    "Amazing pasta dishes and great ambiance!",
                    "Friendly staff and delicious food.",
                    "Best Italian restaurant in town!",
                    "Good value for money.",
                    "Highly recommend the lasagna."
                ]
            },
            {
                "displayName": "Pizza Haven",
                "id": "2",
                "rating": 4.2,
                "userRatingCount": 85,
                "priceLevel": "$",
                "primaryType": "Pizza Place",
                "types": ["Pizza", "Fast Food"],
                "reviews": [
                    "Great variety of pizzas and quick service.",
                    "Affordable and tasty!",
                    "Perfect for a casual meal.",
                    "The crust is amazing!",
                    "Good spot for a quick bite."
                ]
            },
            {
                "displayName": "Trattoria Bella",
                "id": "3",
                "rating": 4.8,
                "userRatingCount": 200,
                "priceLevel": "$$$",
                "primaryType": "Fine Dining",
                "types": ["Italian", "Fine Dining"],
                "reviews": [
                    "Exceptional service and exquisite dishes.",
                    "Perfect for a romantic dinner.",
                    "The wine selection is fantastic!",
                    "Authentic Italian cuisine at its best.",
                    "A bit pricey but worth every penny."
                ]
            }
        ]
    }

    # Sample user preferences
    preferences = {"cuisine": "Italian", "budget": "$$", "time_of_day": "dinner"}

    # Generate and print the ranking report
    report = rank_restaurants_with_llm(places_api_data, preferences)
    print(report)
