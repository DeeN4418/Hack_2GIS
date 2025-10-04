from typing import List
from pydantic import BaseModel

class SttRouteResponse(BaseModel):
    transcript: str
    route: List[List[float]]