from fastapi import APIRouter
from .services import get_coordinate_by_ip, send_result_to_service_b
from .schemas import IpAddress, Coordinate

router = APIRouter()

@router.get('/')
def health_check():
    return {"message": 'server is healthy'}

@router.post("/ip")
def get_ip(ip_address: IpAddress):
    result: Coordinate = get_coordinate_by_ip(ip_address)
    response = send_result_to_service_b(result, ip_address)
    return response
