from pymongo import MongoClient, ASCENDING, DESCENDING
import os
from dotenv import load_dotenv

load_dotenv()

def init_db():
    """Khởi tạo database và các indexes chiến lược cho Fitness Chatbot"""
    
    # Lấy URI từ môi trường hoặc dùng mặc định cho local
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(uri)
    db = client["vulcan_chat_db"]
    
    # 1. Collection: MESSAGES (Lưu lịch sử chat)
    messages = db["messages"]
    # Index kép để load lịch sử chat nhanh theo thời gian
    messages.create_index([("session_id", ASCENDING), ("timestamp", ASCENDING)])
    
    # [ĂN TIỀN] Partial Index cho Memory Trigger: 
    # Chỉ index những tin nhắn chưa tóm tắt. Cực kỳ nhanh cho MemoryManager.
    messages.create_index(
        [("session_id", ASCENDING), ("is_summarized", ASCENDING)],
        partialFilterExpression={"is_summarized": False},
        name="idx_unsummarized_messages"
    )

    # 2. Collection: SESSIONS (Lưu thông tin phiên chat)
    sessions = db["sessions"]
    # Giúp hiển thị danh sách chat ở Sidebar cho User theo thứ tự mới nhất
    sessions.create_index([("user_id", ASCENDING), ("updated_at", DESCENDING)])
    # Đảm bảo session_id là duy nhất
    sessions.create_index("session_id", unique=True)

    # 3. Collection: SUMMARIES (Lưu hồ sơ sức khỏe & tóm tắt)
    summaries = db["summaries"]
    # Mỗi session chỉ có duy nhất một bản tóm tắt hồ sơ
    summaries.create_index("session_id", unique=True)

    print("🚀 [SUCCESS] Database & Strategic Indexes initialized!")
    return db

if __name__ == "__main__":
    init_db()