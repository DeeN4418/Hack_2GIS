from typing import List
import httpx
from fastapi import HTTPException
import asyncio

API_KEY = "e50d3992-8076-47d8-bc3c-9add5a142f20"
PLACES_API_URL = "https://catalog.api.2gis.com/3.0/items"


def mock_llm_geocoding(text: str) -> List[str]:
    """
    Mocks an LLM's ability to extract location names from a text query.
    For this demo, it ignores the text and returns a fixed list of locations.
    """
    print(f"Mock LLM Geocoding for text: '{text}'")
    return ["2гис офис", "Москва-сити"]


async def _geocode_one_location(location: str, client: httpx.AsyncClient) -> List[float]:
    """
    Geocodes a single location string to coordinates using 2GIS Places API.
    Helper for geocode_locations.
    """
    try:
        response = await client.get(
            PLACES_API_URL,
            params={"q": location, "key": API_KEY, "fields": "items.point", "region_id": "32"},  # Moscow region
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()

        if data.get("meta", {}).get("code") != 200 or not data.get("result", {}).get("items"):
            raise HTTPException(status_code=404, detail=f"Location not found: {location}")

        item = data["result"]["items"][0]
        return [item["point"]["lon"], item["point"]["lat"]]

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Error from 2GIS Geocoding API: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error during geocoding: {str(e)}")


async def geocode_locations(locations: List[str]) -> List[List[float]]:
    """
    Geocodes a list of location strings to a list of coordinates.
    """
    async with httpx.AsyncClient() as client:
        tasks = [_geocode_one_location(loc, client) for loc in locations]
        coordinates = await asyncio.gather(*tasks)
        return coordinates
