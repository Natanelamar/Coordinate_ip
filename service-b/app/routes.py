from fastapi import APIRouter
from .schemas import Coordinate

router = APIRouter()

@router.get('/')
def health_check():
    return {"message": 'server is healthy'}

@router.post('/receive')
def receive_coordinate(coordinate: Coordinate):
    return {"status": "received", "coordinate": {"lat": coordinate.lat, "lon": coordinate.lon}}
