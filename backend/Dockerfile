# Sử dụng Python 3.11 slim để tối ưu dung lượng image
FROM python:3.11-slim

# Thiết lập các biến môi trường để Python không tạo file .pyc và log được in trực tiếp
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các gói hệ thống cần thiết (nếu có dùng thư viện C-based)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements trước để tận dụng Docker cache
COPY requirements.txt .

# Cài đặt dependencies (bao gồm tiktoken, pydantic, pymongo, fastapi...)
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Mở cổng 8000 cho FastAPI
EXPOSE 8000

# Copy script vào container
COPY entrypoint.sh .

# Cấp quyền thực thi cho script
RUN chmod +x entrypoint.sh

# Sử dụng ENTRYPOINT để chạy script
ENTRYPOINT ["./entrypoint.sh"]