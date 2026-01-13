from pydantic import BaseModel

class Message(BaseModel):
    message: str

class Coordinate(BaseModel):
    lat: float
    lon: float