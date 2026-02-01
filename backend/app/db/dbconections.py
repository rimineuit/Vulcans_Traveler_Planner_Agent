
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://minh0974680144_db_user:root@cluster0.451ejek.mongodb.net/?appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# 2. Chọn Database (Nếu chưa có, MongoDB sẽ tự tạo khi có dữ liệu)
mydb = client["my_company_db"]

# 3. Chọn Collection - Tương đương với Table (Cũng sẽ tự tạo ngầm định)
mycol = mydb["customers"]

# 4. Chèn một dữ liệu mẫu để "kích hoạt" việc tạo Database & Collection
data = { "name": "Hoàng", "address": "Hà Nội" }
x = mycol.insert_one(data)

print(f"Đã tạo collection và chèn ID: {x.inserted_id}")