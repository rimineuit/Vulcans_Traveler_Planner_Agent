# Xử lý tóm tắt hội thoại khi vượt ngưỡng token
from typing import List
from datetime import datetime
from unittest import result
from app.core.schema import SessionSummary

class MemoryManager:
    def __init__(self, db_manager, llm_service):
        self.db = db_manager
        self.llm = llm_service
        # Ngưỡng token để kích hoạt tóm tắt (ví dụ 2000 tokens)
        self.token_threshold = 2000 

    async def get_unsummarized_token_count(self, session_id: str) -> int:
        """Sử dụng MongoDB Aggregation để tính tổng token cực nhanh"""
        pipeline = [
            {"$match": {"session_id": session_id, "is_summarized": False}},
            {"$group": {
                "_id": "$session_id",
                "total_tokens": {"$sum": "$metadata.content_tokens"}
            }}
        ]
        cursor = self.db.messages.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return result[0]["total_tokens"] if result else 0

    async def update_memory_if_needed(self, session_id: str):
        # 1. Kiểm tra tổng lượng token tích lũy
        current_tokens = await self.get_unsummarized_token_count(session_id)
        
        if current_tokens < self.token_threshold:
            return # Chưa đủ "nặng" để tóm tắt

        print(f"🔄 Token threshold reached ({current_tokens}). Starting summarization...")

        # 2. Lấy toàn bộ tin nhắn chưa tóm tắt để nén
        unsummarized_msgs = await self.db.messages.find({
            "session_id": session_id,
            "is_summarized": False
        }).sort("timestamp", 1).to_list(None)

        # 3. Lấy bản tóm tắt cũ (bộ nhớ dài hạn hiện tại)
        old_summary_doc = await self.db.summaries.find_one({"session_id": session_id})
        old_summary = old_summary_doc.get("summary_text", "") if old_summary_doc else "Chưa có tóm tắt trước đó."

        # 4. Soạn thảo Prompt tóm tắt
        new_content = "\n".join([f"{m['role']}: {m['content']}" for m in unsummarized_msgs])
        
        prompt = f"""
        Nhiệm vụ: Bạn là một Chuyên gia Quản lý Dữ liệu Sức khỏe. Hãy cập nhật Hồ sơ người dùng (User Profile) dựa trên thông tin cũ và các tin nhắn mới.

        ---
        HỒ SƠ CŨ (Dạng JSON): 
        {old_summary}

        ---
        TIN NHẮN MỚI:
        {new_content}

        ---
        YÊU CẦU:
        1. Tổng hợp dữ liệu: Kết hợp hồ sơ cũ và tin nhắn mới để tạo ra một bản hồ sơ cập nhật nhất.
        2. Trích xuất thực thể quan trọng:
        - Thông số: Cân nặng (kg), Chiều cao (cm), Tuổi, Giới tính.
        - Mục tiêu: Giảm cân, tăng cơ, chạy bộ, v.v.
        - Chế độ ăn/Dị ứng: Ghét hành, dị ứng hải sản, đang ăn Keto, v.v.
        - Hoạt động hôm nay: Đã ăn bao nhiêu calo? Tập bài gì?
        3. Tính toán: Nếu có đủ cân nặng và chiều cao, hãy tính lại BMI.
        4. ĐỊNH DẠNG ĐẦU RA: Bắt buộc trả về một chuỗi JSON duy nhất, không có thêm văn bản dẫn nhập.

        Cấu trúc JSON yêu cầu:
        {{
            "user_info": {{
                "weight": float,
                "height": float,
                "age": int,
                "gender": "string",
                "bmi": float
            }},
            "goals": ["string"],
            "restrictions": ["string"],
            "daily_tracking": {{
                "total_calories_in": int,
                "exercise_done": ["string"]
            }},
            "summary_text": "Đoạn văn tóm tắt mạch hội thoại để làm ngữ cảnh cho AI (Tiếng Việt, súc tích)."
        }}
"""

        # 5. Gọi LLM và cập nhật Database
        response = await self.llm.get_response(msgs=prompt, structured=SessionSummary)

        # Cập nhật bảng summaries (Upsert)
        # Kiểm tra nếu parse thành công
        if response.get("parsed"):
            new_summary_obj = response["parsed"] # Đây là instance của SessionSummary
            
            # 6. Cập nhật vào Database sử dụng hàm đã sửa ở trên
            await self.db.update_session_summary(
                session_id=session_id,
                summary=new_summary_obj,
                last_token_count=current_tokens
            )
            
            print(f"✅ Hồ sơ sức khỏe cho session {session_id} đã được cập nhật cấu trúc JSON.")
        else:
            print(f"❌ Lỗi khi parse Summary cho session {session_id}: {response.get('error')}")

        # 6. Đánh dấu các tin nhắn đã "nhập" vào bộ nhớ
        msg_ids = [m["_id"] for m in unsummarized_msgs]
        await self.db.messages.update_many(
            {"_id": {"$in": msg_ids}},
            {"$set": {"is_summarized": True}}
        )

        print(f"✅ Memory updated based on tokens.")
        
    async def get_fresh_context(self, session_id: str, min_overlap: int = 5) -> list:
            """
            Lấy các tin nhắn mới nhất chưa tóm tắt + một ít tin nhắn cũ để làm 'mồi' ngữ cảnh.
            """
            # 1. Lấy toàn bộ tin nhắn chưa tóm tắt (Sắp xếp từ cũ đến mới)
            recent_history_msgs = await self.db.messages.find({
                "session_id": session_id,
                "is_summarized": False
            }).sort("timestamp", 1).to_list(None)

            # 2. Logic bù đắp (Padding): Nếu tin nhắn mới quá ít, bốc thêm tin cũ đã tóm tắt
            if len(recent_history_msgs) < min_overlap:
                # Lấy các tin nhắn đã tóm tắt (Sắp xếp từ mới nhất ngược về cũ)
                extra_msgs = await self.db.messages.find({
                    "session_id": session_id,
                    "is_summarized": True
                }).sort("timestamp", -1).limit(min_overlap).to_list(None)
                
                # Đảo ngược extra_msgs để đúng thứ tự thời gian và gộp vào đầu
                recent_history_msgs = extra_msgs[::-1] + recent_history_msgs

            return recent_history_msgs