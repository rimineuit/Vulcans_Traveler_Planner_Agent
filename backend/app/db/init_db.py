from pymongo import MongoClient, ASCENDING, DESCENDING

def init_db():
    client = MongoClient("mongodb+srv://minh0974680144_db_user:root@cluster0.451ejek.mongodb.net/?appName=Cluster0")
    db = client["vulcan_chat_db"]
    messages_col = db["messages"]
    
    # Tạo Index kép (Compound Index)
    # Giúp tìm kiếm theo user và session cực nhanh
    messages_col.create_index([("user_id", ASCENDING), ("session_id", ASCENDING)])
    
    # Tạo Index cho thời gian để sắp xếp tin nhắn theo đúng thứ tự
    messages_col.create_index([("timestamp", ASCENDING)])
    
    print("✅ Database & Indexes initialized!")
    return messages_col

if __name__ == "__main__":
    init_db()