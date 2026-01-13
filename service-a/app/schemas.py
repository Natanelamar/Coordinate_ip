from pydantic import BaseModel

class IpAddress(BaseModel):
    ip_address: str


class Coordinate(BaseModel):
    lat: float
    lon: float
