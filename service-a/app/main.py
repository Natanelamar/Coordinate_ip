from fastapi import FastAPI
import requests
import uvicorn
app = FastAPI()


@app.get('/')
def health_check():
    try:
        response = requests.post(
            "http://localhost:8080/receive", 
            json={"message": "Hello from service-a"},
            proxies={"http": None, "https": None},
            timeout=5
        )
        return {"message": 'server is healthy', "service_b_response": response.json()}
    except Exception as e:
        return {"message": 'server is healthy', "service_b_error": str(e)}





if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload= True)