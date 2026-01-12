from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


class Message(BaseModel):
    message: str


@app.get('/')
def health_check():
    return {"message": 'server is healthy'}


@app.post('/receive')
def receive_message(msg: Message):
    return {"status": "received", "your_message": msg.message}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, reload= True)