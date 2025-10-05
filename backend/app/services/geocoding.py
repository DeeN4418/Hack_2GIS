import logging
import os
from typing import List, Optional
import httpx
from fastapi import HTTPException

from backend.app.settings.config import API_Settings

settings = API_Settings()

# Configure logging
logger = logging.getLogger(__name__)

PLACE_TYPE_MAPPING = {
    'кафе': 'кафе',
    'кофейня': 'кофейня', 
    'ресторан': 'ресторан',
    'магазин': 'магазин',
    'цветочный магазин': 'цветы',
    'цветы': 'цветы',
    'аптека': 'аптека',
    'банк': 'банк',
    'спортзал': 'спортзал',
    'фитнес': 'фитнес клуб',
    'кинотеатр': 'кинотеатр',
    'парк': 'парк',
    'музей': 'музей',
    'театр': 'театр',
    'больница': 'больница',
    'поликлиника': 'поликлиника',
    'столовая': 'столовая',
    'пиццерия': 'пиццерия',
    'супермаркет': 'супермаркет',
    'торговый центр': 'торговый центр',
    'кофе': 'кофейня',
    'спорт': 'спортзал',
    'зал': 'спортзал'
}

def is_generic_place(location: str) -> bool:
    """
    Checks whether the location is a general concept (cafe, store, etc.)
    and not a specific address or name.
    """
    location_lower = location.lower()
    
    address_indicators = ['ул', 'улица', 'проспект', 'пр', 'дом', 'д', 'корпус', 'к', 'строение', 'с']
    if any(char.isdigit() for char in location) and any(word in location_lower for word in address_indicators):
        return False

    for place_type in PLACE_TYPE_MAPPING.keys():
        if place_type in location_lower:
            return True
    
    return False

def get_place_search_query(location: str) -> str:
    """
    Returns a search query for a general place type.
    """
    location_lower = location.lower()
    for place_type, search_query in PLACE_TYPE_MAPPING.items():
        if place_type in location_lower:
            return search_query
    return location 

async def _find_poi_nearby(location: str, near_coordinates: List[float], client: httpx.AsyncClient) -> List[float]:
    """
    Searches for a POI (Point of Interest) of a certain type near the specified coordinates.
    Returns the coordinates of the first POI found.
    """
    try:
        search_query = get_place_search_query(location)
        
        params = {
            "q": search_query,
            "key": settings.gis_key,
            "fields": "items.point,items.name",
            "point": f"{near_coordinates[0]},{near_coordinates[1]}",
            "radius": 2000,
            "sort": "distance",
            "page_size": 1
        }
        
        logger.info(f"Searching for POI: '{search_query}' near {near_coordinates}")
        
        response = await client.get(
            settings.places_api_url,
            params=params,
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()

        if data.get("meta", {}).get("code") != 200 or not data.get("result", {}).get("items"):
            error_detail = f"POI search API returned no results for: '{location}'. Response: {data}"
            logger.error(error_detail)
            raise HTTPException(status_code=404, detail=error_detail)

        item = data["result"]["items"][0] 
        
        if "point" not in item:
            error_detail = f"POI '{location}' found, but no coordinates. Full item: {item}"
            logger.error(error_detail)
            raise HTTPException(status_code=404, detail=error_detail)

        logger.info(f"Found POI: '{item.get('name', 'Unknown')}' at {[item['point']['lon'], item['point']['lat']]}")
        return [item["point"]["lon"], item["point"]["lat"]]

    except httpx.HTTPStatusError as e:
        error_detail = f"Error from 2GIS POI API for '{location}': {e.response.status_code} - {e.response.text}"
        logger.error(error_detail, exc_info=True)
        raise HTTPException(status_code=e.response.status_code, detail=error_detail)
    except Exception as e:
        error_detail = f"Internal error during POI search for '{location}': {str(e)}"
        logger.error(error_detail, exc_info=True)
        raise HTTPException(status_code=500, detail=error_detail)

async def _geocode_specific_address(location: str, client: httpx.AsyncClient, city: Optional[str] = None) -> List[float]:
    """
    eocodes a specific address or place name.
    """
    try:
        search_query = f"{city}, {location}" if city else location
        params = {
            "q": search_query, 
            "key": settings.gis_key, 
            "fields": "items.point,items.name",
            "page_size": 1
        }
        
        logger.info(f"Geocoding specific address: '{search_query}'")
        
        response = await client.get(
            settings.places_api_url,
            params=params,
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()

        if data.get("meta", {}).get("code") != 200 or not data.get("result", {}).get("items"):
            error_detail = f"Geocoding API returned no results for location: '{location}'. Response: {data}"
            logger.error(error_detail)
            raise HTTPException(status_code=404, detail=error_detail)

        item = data["result"]["items"][0]
        
        if "point" not in item:
            error_detail = f"Location '{location}' found, but no coordinates. Full item: {item}"
            logger.error(error_detail)
            raise HTTPException(status_code=404, detail=error_detail)

        logger.info(f"Geocoded '{item.get('name', location)}' to {[item['point']['lon'], item['point']['lat']]}")
        return [item["point"]["lon"], item["point"]["lat"]]

    except httpx.HTTPStatusError as e:
        error_detail = f"Error from 2GIS Geocoding API for location '{location}': {e.response.status_code} - {e.response.text}"
        logger.error(error_detail, exc_info=True)
        raise HTTPException(status_code=e.response.status_code, detail=error_detail)
    except Exception as e:
        error_detail = f"Internal error during geocoding for location '{location}': {str(e)}"
        logger.error(error_detail, exc_info=True)
        raise HTTPException(status_code=500, detail=error_detail)

async def _geocode_one_location(location: str, client: httpx.AsyncClient, city: Optional[str] = None, reference_point: Optional[List[float]] = None) -> List[float]:
    """
    Geocodes a single location by specifying the type (a specific address or a general concept).
    """

    if is_generic_place(location) and reference_point:
        logger.info(f"'{location}' identified as generic place, searching nearby POI")
        return await _find_poi_nearby(location, reference_point, client)
    else:

        logger.info(f"'{location}' identified as specific address/name")
        return await _geocode_specific_address(location, client, city)

async def geocode_locations(locations: List[str], city: Optional[str] = None) -> List[List[float]]:
    """
    Geocodes a list of locations into coordinates.
    For general concepts, it uses previous coordinates as a reference point.
    """
    async with httpx.AsyncClient() as client:
        coordinates = []
        
        for i, location in enumerate(locations):
            logger.info(f"Processing location {i+1}/{len(locations)}: '{location}'")
            
            # For the first location, we use the city as the context.
            # For subsequent locations, we use the previous coordinate as the reference point.
            reference_point = coordinates[-1] if coordinates else None
            
            try:
                coords = await _geocode_one_location(
                    location, 
                    client, 
                    city=city, 
                    reference_point=reference_point
                )
                coordinates.append(coords)
                logger.info(f"Successfully geocoded '{location}' to {coords}")
                
            except Exception as e:
                logger.error(f"Failed to geocode '{location}': {str(e)}")
                raise
        
        return coordinates