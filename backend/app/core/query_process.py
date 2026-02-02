from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel
from .schema import RewriteResponse, ClarifyResponse

class QueryProcessor:
    def __init__(self, llm_service):
        self.llm = llm_service

    async def rewrite_step(self, user_input: str, history_from_messages: str, history_from_short_term_memory: str) -> RewriteResponse:
            """Bước 1: Tối ưu hoá câu hỏi dựa trên Hồ sơ sức khỏe và Lịch sử"""
            prompt = f"""
            Bạn là một chuyên gia phân tích ngôn ngữ cho Trợ lý Sức khỏe và Dinh dưỡng.
            
            NGỮ CẢNH:
            - Hồ sơ sức khỏe (Summary JSON): {history_from_short_term_memory}
            - Lịch sử trò chuyện gần đây: {history_from_messages}
            - Câu hỏi mới nhất: "{user_input}"
            
            NHIỆM VỤ:
            1. Kiểm tra xem câu hỏi có chứa các từ thay thế mơ hồ (nó, cái này, món đó, bài tập này...) không.
            2. Nếu có, hãy dùng Lịch sử để xác định chính xác thực thể đó là gì.
            3. Dựa vào Hồ sơ sức khỏe để làm rõ đối tượng (Ví dụ: "Tôi nên ăn gì?" -> "Với mục tiêu giảm cân và hiện tại nặng 70kg, tôi nên ăn gì cho bữa tối?").
            4. Viết lại câu hỏi sao cho đầy đủ, chuyên nghiệp và có thể trả lời độc lập.
            
            Yêu cầu đặc biệt: Nếu người dùng hỏi về thông số (calo, BMI) mà câu hỏi chưa rõ ràng, hãy bổ sung thêm các chỉ số hiện có từ Hồ sơ vào câu hỏi viết lại.
            """
            
            result = await self.llm.get_response(
                msgs=[{"role": "system", "content": prompt}],
                structured=RewriteResponse
            )
            return result['parsed']

    async def clarify_step(self, rewritten_query: str) -> ClarifyResponse:
            """Bước 3: Đặt câu hỏi làm rõ nếu thiếu dữ liệu tính toán (BMI, TDEE, Calo)"""
            prompt = f"""
            Bạn là một Huấn luyện viên Fitness chuyên nghiệp. 
            Hãy phân tích câu hỏi đã được viết lại: "{rewritten_query}"
            
            NHIỆM VỤ:
            1. Xác định xem để trả lời câu hỏi này một cách CHÍNH XÁC, bạn có thiếu thông tin quan trọng nào không?
            - Nếu hỏi về chế độ ăn: Cần biết Cân nặng, Chiều cao, Mục tiêu (tăng/giảm cân).
            - Nếu hỏi về bài tập: Cần biết Mục tiêu, Thời gian rảnh, hoặc Thiết bị tập luyện hiện có.
            2. Nếu thiếu, hãy đặt 1-3 câu hỏi ngắn gọn, thân thiện để lấy thông tin đó. 
            3. Nếu đã đủ thông tin để tư vấn, hãy để `is_still_unclear: false`.
            
            LƯU Ý: Không hỏi lại những gì đã có trong câu hỏi. Hãy tỏ ra là một chuyên gia tận tâm.
            """
            
            result = await self.llm.get_response(
                msgs=[{"role": "system", "content": prompt}],
                structured=ClarifyResponse
            )
            return result['parsed']

    async def augment_context(self, rewritten_query: str, summary_obj: Any, recent_messages: List[Dict]) -> str:
            """Bước 2: Kết hợp Hồ sơ cấu trúc và Lịch sử hội thoại"""
            
            # summary_obj lúc này là instance của SessionSummary (Pydantic)
            # Chúng ta bóc tách các trường quan trọng để AI dễ đọc
            profile = summary_obj.user_info
            # tracking = summary_obj.daily_tracking
            
            user_context = (
                f"HỒ SƠ KHÁCH HÀNG:\n"
                f"- Chỉ số: {profile.weight}kg, {profile.height}cm, BMI: {profile.bmi}\n"
                f"- Mục tiêu: {', '.join(summary_obj.goals)}\n"
                f"- Hạn chế: {', '.join(summary_obj.restrictions)}\n"
                # f"- Hôm nay đã nạp: {tracking.total_calories_in} kcal\n"
                f"- Tóm tắt hội thoại cũ: {summary_obj.summary_text}"
            )

            augmented_history = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])
            
            full_context = (
                f"--- BỐI CẢNH HỆ THỐNG ---\n{user_context}\n\n"
                f"--- LỊCH SỬ GẦN ĐÂY ---\n{augmented_history}\n"
                f"----------------------\n"
                f"CÂU HỎI CẦN GIẢI QUYẾT: {rewritten_query}"
            )
            return full_context