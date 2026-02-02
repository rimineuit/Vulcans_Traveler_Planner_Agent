# Sử dụng Python slim để giữ image nhẹ
FROM python:3.11-slim

# Ngăn Python tạo file .pyc và hỗ trợ log real-time
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cài đặt các dependencies cần thiết cho UI
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy mã nguồn Frontend
COPY . .

# Port mặc định của Streamlit
EXPOSE 8501

# Lệnh chạy Streamlit
# --server.address=0.0.0.0 để container có thể truy cập từ bên ngoài
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]