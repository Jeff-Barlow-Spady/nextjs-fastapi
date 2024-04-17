from fastapi import FastAPI

app = FastAPI()

@app.get("/api/python")
def hello_world():
    return {"message": "Hello World"}

@app.get("/api/python/{name}")
def get_greeting(name: str):
    return {"message": f"Hello {name}"}
    
