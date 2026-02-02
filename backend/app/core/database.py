import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid
from dotenv import load_dotenv
from app.utils.decorators import mongo_serialized as serialize_mongo
from app.core.schema import SessionSummary

class DatabaseManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            load_dotenv()
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            
            # Đọc cấu hình từ .env
            uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
            db_name = os.getenv("MONGO_DB_NAME", "vulcan_chat_db")
            col_messages = os.getenv("COLLECTION_MESSAGES", "messages")
            col_summaries = os.getenv("COLLECTION_SUMMARY", "summaries")
            col_sessions = os.getenv("COLLECTION_SESSIONS", "sessions")
            # Kết nối MongoDB
            cls._instance.client = AsyncIOMotorClient(uri, maxPoolSize=50)
            cls._instance.db = cls._instance.client[db_name]
            
            # Gán collections cho messages giữa user và bot, "summary" cho short memory và sessions 
            cls._instance.messages = cls._instance.db[col_messages]
            cls._instance.summaries = cls._instance.db[col_summaries]
            cls._instance.sessions = cls._instance.db[col_sessions]
        return cls._instance
    
    @serialize_mongo
    async def save_message(self, session_id, user_id, role, content, metadata=None):
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
        
        return await self.messages.insert_one(doc)

    @serialize_mongo
    async def get_history(self, session_id, limit=20, last_timestamp=None):
        """
        Lấy lịch sử chat theo session_id và giới hạn số tin 
        session_id: ID của phiên chat
        limit: Số tin nhắn tối đa cần lấy
        last_timestamp: Thời gian của tin nhắn cũ nhất hiện tại trên UI
        """
        query = {"session_id": session_id}
        
        # Nếu người dùng muốn load thêm tin nhắn CŨ HƠN
        if last_timestamp:
            query["timestamp"] = {"$lt": last_timestamp} # $lt = Less Than (nhỏ hơn/cũ hơn)
            
        cursor = self.messages.find(query)\
                         .sort("timestamp", -1)\
                         .limit(limit)
        # Đảo ngược để trả về theo thứ tự thời gian tăng dần
        results = await cursor.to_list(length=limit)
        return results[::-1]
    
    @serialize_mongo
    async def get_summary(self, session_id: str) -> SessionSummary:
        """Lấy bản tóm tắt đầy đủ (Structured Summary) của session"""
        query = {"session_id": session_id}
        summary_doc = await self.summaries.find_one(query)
        
        if summary_doc:
            # Nếu tìm thấy, chuyển đổi từ Dict trong DB sang Object Pydantic
            # Điều này giúp bạn truy cập .user_info.weight một cách dễ dàng
            return SessionSummary.model_validate(summary_doc)
        
        # Nếu chưa có summary (session mới), trả về một Object mặc định (rỗng)
        # Việc trả về Object rỗng thay vì "" giúp code không bị crash ở các bước sau
        return SessionSummary(summary_text="Chưa có lịch sử hội thoại.")
    
    @serialize_mongo
    async def update_session_summary(self, session_id: str, summary: SessionSummary, last_token_count: int = 0):
        """Cập nhật hồ sơ sức khỏe đầy đủ dựa trên Pydantic Model"""
        query = {"session_id": session_id}
        
        # Chuyển Pydantic -> Dict để lưu vào Mongo
        update_data = summary.model_dump()
        
        # Bổ sung các trường metadata hệ thống
        update_data["updated_at"] = datetime.utcnow()
        update_data["last_token_count"] = last_token_count
        
        new_data = {
            "$set": update_data
        }
        
        return await self.summaries.update_one(query, new_data, upsert=True)
    
    @serialize_mongo
    async def get_user_sessions(self, user_id, limit=10):
        """Lấy danh sách các cuộc hội thoại của user"""
        query = {"user_id": user_id}
        
        # Sắp xếp theo updated_at để cuộc chat mới nhất luôn ở trên cùng
        cursor = self.sessions.find(query)\
                                    .sort("updated_at", -1)\
                                    .limit(limit)
        
        
        return await cursor.to_list(length=limit)
    
    @serialize_mongo
    async def create_new_session(self, user_id):
        """Tạo một session mới cho user"""
        new_session_id = str(uuid.uuid4())
        session_doc = {
            "session_id": new_session_id,
            "user_id": user_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "title": "New Chat Session",
            }
        
        await self.sessions.insert_one(session_doc)
        
        # Xử lý trường hợp ObjectId không thể serialize được, chuyển thành string. MongoDB tự tạo _id cho mỗi document và chèn trực tiếp vào session_doc
        if "_id" in session_doc:
            session_doc["_id"] = str(session_doc["_id"])
        return session_doc
    
    @serialize_mongo
    async def init_indices(self):
        """Khởi tạo index một cách async (Gọi khi app startup)"""
        await self.messages.create_index([("session_id", 1), ("timestamp", 1)])
        await self.summary.create_index("session_id", unique=True)
        await self.sessions.create_index([("user_id", 1), ("updated_at", -1)])
        print("Database Indices Initialized!")
        
    async def is_healthy(self):
        """Kiểm tra kết nối DB có ổn không"""
        try:
            await self.client.admin.command('ping')
            return True
        except Exception:
            return False