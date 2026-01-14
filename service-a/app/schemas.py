from pydantic import BaseModel, IPvAnyAddress

class IpAddress(BaseModel):
    ip_address: IPvAnyAddress


class Coordinate(BaseModel):
    lat: float
    lon: float
