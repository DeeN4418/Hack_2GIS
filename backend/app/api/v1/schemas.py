from typing import List
from pydantic import BaseModel

class RoutePoint(BaseModel):
    coord: List[float]

class SttRouteResponse(BaseModel):
    transcript: str
    route: List[RoutePoint]
    
class UserLocation(BaseModel):
    lat: float
    lon: float