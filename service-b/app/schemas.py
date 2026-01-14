from pydantic import BaseModel, IPvAnyAddress

class Message(BaseModel):
    message: str

class Coordinate(BaseModel):
    lat: float
    lon: float

class IpAddress(BaseModel):
    ip_address: IPvAnyAddress

class CoordinateRequest(BaseModel):
    coordinate: Coordinate
    ip_address: IpAddress