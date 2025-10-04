from typing import List

def mock_2gis_route(transcript: str) -> List[List[float]]:
    """Mocks the 2GIS routing process based on a transcript."""
    print(f"Mock 2GIS routing for transcript: '{transcript}'")
    return [
      [37.6175, 55.7504], [37.6200, 55.7510], [37.6242, 55.7527],
      [37.6290, 55.7540], [37.6338, 55.7552], [37.6392, 55.7565],
      [37.6440, 55.7578], [37.6485, 55.7591], [37.6530, 55.7602]
    ]
