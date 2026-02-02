#!/bin/bash

# Dừng script nếu có lỗi xảy ra
set -e

echo "🚀 Khởi tạo Database Indexes..."
python app/init_db.py

echo "🔥 Khởi chạy FastAPI Server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000