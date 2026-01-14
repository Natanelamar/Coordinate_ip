from fastapi import APIRouter
from .schemas import CoordinateRequest
from .storage import insert_coordinate, get_all_coordinates as fetch_all_coordinates

router = APIRouter()

@router.get('/')
def health_check():
    return {"message": 'server is healthy'}

@router.post('/receive')
def receive_coordinate(request: CoordinateRequest):
    result = insert_coordinate(request.coordinate, request.ip_address)
    return result

@router.get('/all')
def fetch_all_coordinates_route():
    return fetch_all_coordinates()