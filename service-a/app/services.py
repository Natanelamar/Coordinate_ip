import requests
from .schemas import IpAddress, Coordinate

def get_coordinate_by_ip(ip_address: IpAddress):
    try:
        response= requests.get(f"http://ip-api.com/json/{ip_address.ip_address}")
        result = response.json()
        coordinets: Coordinate = Coordinate.model_validate(result)
        coordinets.model_dump_json()
        return coordinets
    except requests.RequestException as e:
        return {"error": f"Failed to fetch coordinates: {str(e)}"}

def send_result_to_service_b(result: Coordinate):
    try:
        response = requests.post("http://localhost:8080/receive", json=result.model_dump())
        return response.json()
    except requests.RequestException as e:
        return {"error": f"Failed to send result to service-b: {str(e)}"}
     


