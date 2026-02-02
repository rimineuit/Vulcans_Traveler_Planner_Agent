from pydantic import BaseModel, Field
from typing import List, Optional

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
    user_id: str


# Class này định nghĩa dữ liệu kiểm tra tính mơ hồ của truy vấn
class QueryCheckAmbitous(BaseModel):
    query: str


class RewriteResponse(BaseModel):
    is_ambiguous: bool = Field(description="Truy vấn có mơ hồ, thiếu thông tin hay không")
    rewritten_query: str = Field(description="Truy vấn đã được viết lại đầy đủ dựa trên ngữ cảnh")

class ClarifyResponse(BaseModel):
    is_still_unclear: bool = Field(description="Sau khi rewrite vẫn không thể hiểu ý người dùng")
    questions: List[str] = Field(default=[], description="Danh sách 1-3 câu hỏi làm rõ")
    
class CombinedResponse(BaseModel):
    # --- Thành phần cho Bước 1 (Rewrite) ---
    is_ambiguous: bool = Field(
        description="Xác định câu hỏi có bị mơ hồ, thiếu thực thể hoặc khó hiểu không."
    )
    rewritten_query: str = Field(
        description="Câu hỏi sau khi đã được viết lại rõ ràng dựa trên lịch sử hội thoại."
    )

    # --- Thành phần cho Bước 3 (Clarify) ---
    is_still_unclear: bool = Field(
        description="Dù đã viết lại, hệ thống vẫn thấy thiếu thông tin để trả lời chính xác hay không."
    )
    clarifying_questions: List[str] = Field(
        default=[],
        description="Danh sách 1-3 câu hỏi để làm rõ ý định của người dùng."
    )
    
    
    
from pydantic import BaseModel, Field
from typing import List, Optional

class UserInfo(BaseModel):
    weight: Optional[float] = Field(None, description="Cân nặng tính bằng kg")
    height: Optional[float] = Field(None, description="Chiều cao tính bằng cm")
    age: Optional[int] = Field(None, description="Tuổi của người dùng")
    gender: Optional[str] = Field(None, description="Giới tính")
    bmi: Optional[float] = Field(None, description="Chỉ số khối cơ thể (BMI)")
    name: Optional[str] = Field(None, description="Tên người dùng")

class DailyTracking(BaseModel):
    total_calories_in: int = Field(0, description="Tổng lượng calo đã nạp trong ngày")
    exercise_done: List[str] = Field(default_factory=list, description="Danh sách các bài tập đã thực hiện")

class SessionSummary(BaseModel):
    """Cấu trúc dữ liệu chính cho bản tóm tắt bộ nhớ của Fitness Bot"""
    user_info: UserInfo = Field(default_factory=UserInfo)
    goals: List[str] = Field(default_factory=list, description="Danh sách mục tiêu của người dùng")
    restrictions: List[str] = Field(default_factory=list, description="Dị ứng hoặc hạn chế về ăn uống")
    # daily_tracking: DailyTracking = Field(default_factory=DailyTracking)
    summary_text: str = Field(..., description="Đoạn văn tóm tắt diễn biến hội thoại")

    class Config:
        # Giúp chuyển đổi mượt mà khi làm việc với MongoDB (nếu cần)
        populate_by_name = True