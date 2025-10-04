import logging
import os
from typing import List, Optional
import httpx
from fastapi import HTTPException
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

API_KEY = os.getenv("2GIS_API_KEY", "95138e17-59ca-426b-9a4b-2f5a9c36695a")
PLACES_API_URL = "https://catalog.api.2gis.com/3.0/items"


def mock_llm_geocoding(text: str) -> List[str]:
    """
    Mocks an LLM's ability to extract location names from a text query.
    For this demo, it ignores the text and returns a fixed list of locations.
    """
    print(f"Mock LLM Geocoding for text: '{text}'")
    return ["2гис офис", "Москва-сити"]


async def _geocode_one_location(location: str, client: httpx.AsyncClient, city: Optional[str] = None) -> List[float]:
    """
    Geocodes a single location string to coordinates using 2GIS Places API.
    Helper for geocode_locations.
    """
    try:
        search_query = f"{city}, {location}" if city else location
        params = {"q": search_query, "key": API_KEY, "fields": "items.point"}
        
        response = await client.get(
            PLACES_API_URL,
            params=params,
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()

        if data.get("meta", {}).get("code") != 200 or not data.get("result", {}).get("items"):
            error_detail = f"Geocoding API returned success status but no valid data for location: '{location}'. Response: {data}"
            logger.error(error_detail)
            raise HTTPException(status_code=404, detail=error_detail)

        item = data["result"]["items"][0]
        
        if "point" not in item:
            error_detail = f"Location '{location}' found, but it does not have coordinate information. Full item response: {item}"
            logger.error(error_detail)
            raise HTTPException(status_code=404, detail=error_detail)

        return [item["point"]["lon"], item["point"]["lat"]]

    except httpx.HTTPStatusError as e:
        error_detail = f"Error from 2GIS Geocoding API for location '{location}': {e.response.status_code} - {e.response.text}"
        logger.error(error_detail, exc_info=True)
        raise HTTPException(status_code=e.response.status_code, detail=error_detail)
    except Exception as e:
        error_detail = f"Internal error during geocoding for location '{location}': {str(e)}"
        logger.error(error_detail, exc_info=True)
        raise HTTPException(status_code=500, detail=error_detail)


async def geocode_locations(locations: List[str], city: Optional[str] = None) -> List[List[float]]:
    """
    Geocodes a list of location strings to a list of coordinates.
    """
    async with httpx.AsyncClient() as client:
        tasks = [_geocode_one_location(loc, client, city=city) for loc in locations]
        coordinates = await asyncio.gather(*tasks)
        return coordinates
