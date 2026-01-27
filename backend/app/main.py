# Entry point cho Backend (FastAPI/Flask)
from pydantic import BaseModel
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

