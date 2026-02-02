from app.core.database import DatabaseManager
from app.core.llm_service import LLMService
from app.core.query_process import QueryProcessor
from fastapi.encoders import jsonable_encoder
from app.utils.token_counter import TokenCounter
from app.core.memory import MemoryManager
# Sau khi lưu tin nhắn Assistant xong
import asyncio

class ChatOrchestrator:
    def __init__(self):
        # Khởi tạo các "đệ tử"
        self.db = DatabaseManager()
        self.llm_service = LLMService()
        self.processor = QueryProcessor(self.llm_service)
        self.token_counter = TokenCounter()
        self.memory_manager = MemoryManager(self.db, self.llm_service)
        
    async def handle_chat(self, user_id: str, session_id: str, message: str):
            # --- BƯỚC 1: TIẾP NHẬN & LƯU TRỮ BAN ĐẦU ---
            user_content_tokens = self.token_counter.count_text_tokens(message)
            user_msg_result = await self.db.save_message(
                session_id, user_id, "user", message, 
                metadata={"content_tokens": user_content_tokens}
            )
            user_msg_id = user_msg_result.inserted_id

            # --- BƯỚC 2: CHUẨN BỊ NGỮ CẢNH (CHỈ GỌI 1 LẦN) ---
            # Dùng luôn logic "Fresh Context" của MemoryManager để đồng bộ
            summary_text = await self.db.get_summary(session_id)
            history_msgs = await self.memory_manager.get_fresh_context(session_id)
            
            # Format history một lần duy nhất để dùng cho tất cả các bước LLM
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in history_msgs])

            # --- BƯỚC 3: REWRITE (PHÂN TÍCH Ý ĐỊNH) ---
            # Bây giờ Rewrite đã có đủ "đạn" như bước Answer
            analysis = await self.processor.rewrite_step(message, history_str, summary_text)

            # --- BƯỚC 4: XỬ LÝ RẼ NHÁNH (CLARIFY HOẶC ANSWER) ---
            if analysis.is_ambiguous:
                clarify = await self.processor.clarify_step(analysis.rewritten_query)
                
                # Cập nhật metadata suy luận cho User
                await self.db.messages.update_one(
                    {"_id": user_msg_id},
                    {"$set": {
                        "metadata.is_ambiguous": True,
                        "metadata.rewritten_query": analysis.rewritten_query,
                        "metadata.is_still_unclear": clarify.is_still_unclear,
                        "metadata.clarifying_questions": clarify.questions
                    }}
                )

                if clarify.is_still_unclear:
                    questions_joined = "\n".join([f"- {q}" for q in clarify.questions])
                    assistant_content = f"Tôi chưa rõ ý bạn lắm. Bạn vui lòng cung cấp thêm thông tin nhé:\n{questions_joined}"
                    
                    # Lưu Assistant message và dọn dẹp
                    await self._finalize_chat(session_id, user_id, assistant_content, "clarify")
                    return {"type": "clarification", "data": clarify.questions, "response": assistant_content}

            # --- BƯỚC 5: TRẢ LỜI CUỐI CÙNG (NẾU ĐÃ RÕ NGHĨA) ---
            # Đánh dấu User message đã rõ nghĩa
            await self.db.messages.update_one(
                {"_id": user_msg_id},
                {"$set": {
                    "metadata.is_ambiguous": analysis.is_ambiguous,
                    "metadata.rewritten_query": analysis.rewritten_query,
                    "metadata.is_still_unclear": False
                }}
            )

            # Augment context sử dụng history_msgs đã bốc từ đầu
            full_context = await self.processor.augment_context(analysis.rewritten_query, summary_text, history_msgs)
            
            ai_response = await self.llm_service.get_response([
                {"role": "system", "content": f"Context: {full_context}"},
                {"role": "user", "content": analysis.rewritten_query}
            ])

            # Lưu câu trả lời và dọn dẹp
            await self._finalize_chat(session_id, user_id, ai_response.answer, "final_answer", ai_response)
            
            return {"type": "answer", "data": ai_response.answer, "response": ai_response.answer}

    async def _finalize_chat(self, session_id, user_id, content, msg_type, llm_meta=None):
        """Hàm phụ trợ để lưu Assistant message và trigger tóm tắt"""
        tokens = self.token_counter.count_text_tokens(content)
        metadata = {
            "type": msg_type,
            "content_tokens": tokens
        }
        if llm_meta:
            metadata["llm_usage"] = {"input": llm_meta.input_tokens, "output": llm_meta.output_tokens}

        await self.db.save_message(session_id, user_id, "assistant", content, metadata=metadata)
        
        # Luôn chạy tóm tắt ngầm dù là clarify hay trả lời thật
        asyncio.create_task(self.memory_manager.update_memory_if_needed(session_id))