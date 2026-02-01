# Entry point cho Backend (FastAPI/Flask)
from fastapi import FastAPI
from core.schema import ChatRequest
from backend.app.core.chat_engine import ChatEngine
from backend.app.core.database import DatabaseManager

app = FastAPI()
db_manager = DatabaseManager()
engine = ChatEngine()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/chat/completions")
async def chat_completions(request: ChatRequest):
    """Process chat completion requests."""
    
    result = await engine.get_response(request)
    
    return result
