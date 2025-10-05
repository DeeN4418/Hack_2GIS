import os
import httpx
from typing import List
from fastapi import HTTPException
import logging
from backend.app.settings.config import API_Settings

settings = API_Settings()

# Configure logging
logger = logging.getLogger(__name__)

MAX_ROUTE_POINTS = 10

def _parse_linestring(linestring: str) -> List[List[float]]:
    """Helper to parse a 'LINESTRING(lon1 lat1, lon2 lat2, ...)' into a list of coordinates."""
    points_str = linestring.replace("LINESTRING(", "").replace(")", "")
    if not points_str:
        return []
    
    return [
        [float(coord) for coord in point.strip().split()]
        for point in points_str.split(',')
    ]

async def get_2gis_route(points: List[List[float]]) -> List[List[float]]:
    """
    Builds a route between two or more points using the 2GIS Routing API.
    """
    if len(points) > MAX_ROUTE_POINTS:
        logger.warning(f"More than {MAX_ROUTE_POINTS} points provided. Truncating to the first {MAX_ROUTE_POINTS}.")
        points = points[:MAX_ROUTE_POINTS]
        
    if len(points) < 2:
        raise ValueError("At least two points are required to build a route.")

    payload = {
        "points": [{"lon": p[0], "lat": p[1]} for p in points],
        "transport": "walking",
        "output": "detailed"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                settings.routing_api_url,
                params={"key": settings.gis_key},
                json=payload,
                timeout=10.0
            )
            response.raise_for_status() # Raise an exception for 4xx or 5xx status codes
            data = response.json()
            
            if data.get("type") == "error" or "result" not in data or not data["result"]:
                error_detail = f"2GIS Routing API returned an error: {data.get('message', 'Could not build route.')}. Full response: {data}"
                logger.error(error_detail)
                raise HTTPException(status_code=400, detail=data.get("message", "Could not build route."))

            # Extract and parse the geometry from all maneuvers
            all_coords = []
            maneuvers = data["result"][0].get("maneuvers", [])
            for maneuver in maneuvers:
                if maneuver.get("outcoming_path") and maneuver["outcoming_path"].get("geometry"):
                    for geometry_part in maneuver["outcoming_path"]["geometry"]:
                        if geometry_part.get("selection"):
                            all_coords.extend(_parse_linestring(geometry_part["selection"]))
            
            return all_coords

        except httpx.HTTPStatusError as e:
            error_detail = f"Error from 2GIS API: {e.response.status_code} - {e.response.text}"
            logger.error(error_detail, exc_info=True)
            raise HTTPException(status_code=e.response.status_code, detail=error_detail)
        except Exception as e:
            error_detail = f"Internal error processing route: {str(e)}"
            logger.error(error_detail, exc_info=True)
            raise HTTPException(status_code=500, detail=error_detail)
