
import redis
from .schemas import Coordinate, IpAddress

client = redis.Redis(host='localhost', port=6379, db=0)

def insert_coordinate(coordinate: Coordinate, ip_address: IpAddress):
    try:
        ip_key = str(ip_address.ip_address)
        client.hset(ip_key, "coordinate", coordinate.model_dump_json())
        return {"message": "Coordinate inserted successfully", "ip": ip_key}
    except Exception as e:
        return {"error": str(e)}

def get_coordinate_by_ip(ip_address: IpAddress):
    try:
        ip_key = str(ip_address.ip_address)
        coordinate = client.hget(ip_key, "coordinate")
        return {"message": "Coordinate retrieved successfully", "ip": ip_key, "coordinate": coordinate}
    except Exception as e:
        return {"error": str(e)}

def get_all_coordinates():
    try:
        all_data = []
        keys = client.keys("*")
        for key in keys:
            ip_address = key.decode('utf-8')
            coordinate_json = client.hget(key, "coordinate")
            if coordinate_json:
                all_data.append({
                    "ip": ip_address,
                    "coordinate": coordinate_json.decode('utf-8')
                })
        return {"message": "All coordinates retrieved successfully", "count": len(all_data), "data": all_data}
    except Exception as e:
        return {"error": str(e)}