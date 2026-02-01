from pydantic import BaseModel

# Class này định nghĩa dữ liệu sạch sẽ trả về cho Frontend
class ChatResult(BaseModel):
    answer: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    
# Class này định nghĩa dữ liệu đầu vào từ Frontend(User query + session_id)
class ChatRequest(BaseModel):
    query: str
    session_id: str


# Class này định nghĩa dữ liệu kiểm tra tính mơ hồ của truy vấn
class QueryCheckAmbitous(BaseModel):
    query: str
    