from typing import List
from pydantic import BaseModel

class RoutePoint(BaseModel):
    coord: List[float]

class SttRouteResponse(BaseModel):
    route_type: str
    transcript: str
    route: List[RoutePoint]
    pivot_route_points: List[RoutePoint]
    
class UserLocation(BaseModel):
    lat: float
    lon: float