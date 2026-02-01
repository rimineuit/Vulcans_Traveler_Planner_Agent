import os
from pymongo import MongoClient, ASCENDING
from datetime import datetime

class DatabaseManager:
    _instance = None  # Singleton instance

    def __new__(cls):
        """Đảm bảo chỉ có DUY NHẤT một kết nối được tạo ra"""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            # Khởi tạo DatabaseClient một lần duy nhất
            uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
            cls._instance.client = MongoClient(uri, maxPoolSize=5)
            cls._instance.db = cls._instance.client["vulcan_chat_db"]
            cls._instance.messages = cls._instance.db["messages"]
            cls._instance.short_term_session_summary = cls._instance.db["short_term_session_summary"]
            # Tự động đánh Index "session_id", "user_id", "timestamp" khi khởi tạo nếu chưa có
            cls._instance.messages.create_index([("session_id", ASCENDING), ("timestamp", ASCENDING), ("user_id", ASCENDING)])
        return cls._instance

    def save_message(self, session_id, user_id, role, content, metadata=None):
        """Lưu tin nhắn vào DB"""
        doc = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now(),
            "is_summarized": False
        }
        return self.messages.insert_one(doc)

    def get_history(self, session_id, limit=20):
        """Lấy lịch sử chat theo session_id và giới hạn số tin nhắn"""
        cursor = self.messages.find({"session_id": session_id})\
                             .sort("timestamp", -1)\
                             .limit(limit)
        return list(cursor)[::-1]

    def is_healthy(self):
        """Kiểm tra kết nối DB có ổn không"""
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False