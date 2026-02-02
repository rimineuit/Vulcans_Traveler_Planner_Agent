# Entry point cho Backend (FastAPI/Flask)
from pydantic import BaseModel, Field
from fastapi import FastAPI
from app.core.schema import ChatRequest
from app.core.llm_service import LLMService
from app.core.chat_orchestrator import ChatOrchestrator
from app.core.database import DatabaseManager
from fastapi.encoders import jsonable_encoder

app = FastAPI()
db_manager = DatabaseManager()
chat_orchestrator = ChatOrchestrator()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/api/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """Process chat completion requests."""
    result = await chat_orchestrator.handle_chat(request.user_id, request.session_id, request.query)
    return result

@app.get("/api/v1/users/{user_id}/sessions")
async def read_user_sessions(user_id: str, limit: int = 10):
    # logic lấy từ database...
    sessions = await db_manager.get_user_sessions(user_id, limit=limit)
    return {"status": "success", "data": sessions}

@app.post("/api/v1/sessions/{user_id}")
async def create_session(user_id: str):
    session = await db_manager.create_new_session(user_id)
    return {
        "status": "success", 
        "data": jsonable_encoder(session)
    }

@app.get("/api/v1/chat_history/{session_id}")
async def read_chat_history(session_id: str, limit: int = 20):
    # logic lấy lịch sử chat từ database...
    history = await db_manager.get_history(session_id, limit=limit)
    
    return {"status": "success", "data": history}

@app.get("/api/v1/database/health")
async def database_health_check():
    is_healthy = await db_manager.is_healthy()
    return {"status": "success", "database_healthy": is_healthy}

@app.get("/api/v1/chat_summary/{session_id}")
async def read_chat_summary(session_id: str):
    summary = await db_manager.get_summary(session_id)
    return {"status": "success", "data": summary}

# class TestChatResponse(BaseModel):
#     user_input: str
# class Movie(BaseModel):
#     """A movie with details."""
#     title: str = Field(..., description="The title of the movie")
#     year: int = Field(..., description="The year the movie was released")
#     director: str = Field(..., description="The director of the movie")
#     rating: float = Field(..., description="The movie's rating out of 10")
    
# @app.post("/api/v1/testchat/completions")
# async def test_chat_completions(TestChatResponse: TestChatResponse):
#     """Endpoint test chat completions với định dạng trả về cụ thể."""
    
#     result = await engine.get_response(TestChatResponse.user_input, structured=Movie)
    
#     return {"status": "success", "data": jsonable_encoder(result)}