import os
from pathlib import Path

def create_project_structure():
    # Định nghĩa cấu trúc thư mục
    structure = [
        "backend/app/core",
        "backend/app/schemas",
        "backend/app/db",
        "frontend",
        "data",
    ]

    # Danh sách các file cần khởi tạo nội dung cơ bản
    files = {
        "backend/app/core/memory.py": "# Xử lý tóm tắt hội thoại khi vượt ngưỡng token\n",
        "backend/app/core/query.py": "# Pipeline: Rewrite -> Augment -> Clarify\n",
        "backend/app/schemas/session.py": "# Định nghĩa Schema cho Session Summary\n",
        "backend/app/schemas/query.py": "# Định nghĩa Schema cho Query Understanding\n",
        "backend/app/main.py": "# Entry point cho Backend (FastAPI/Flask)\n",
        "backend/Dockerfile": "FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD [\"python\", \"app/main.py\"]\n",
        "backend/requirements.txt": "vllm\nfastapi\nuvicorn\npydantic\n",
        
        "frontend/app.py": "# Giao diện Streamlit/Gradio cho Demo\n",
        "frontend/Dockerfile": "FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD [\"streamlit\", \"run\", \"app.py\", \"--server.port=8501\"]\n",
        "frontend/requirements.txt": "streamlit\nrequests\n",
        
        "data/long_conv.jsonl": "{\"role\": \"user\", \"content\": \"Dữ liệu mẫu hội thoại dài...\"} #\n",
        "data/ambiguous.jsonl": "{\"original_query\": \"nó ở đâu?\"} #\n",
        
        "docker-compose.yml": "services:\n  backend:\n    build: ./backend\n    ports:\n      - \"8000:8000\"\n  frontend:\n    build: ./frontend\n    ports:\n      - \"8501:8501\"\n    depends_on:\n      - backend\n",
        ".env": "HF_TOKEN=your_huggingface_token_here\nMODEL_NAME=meta-llama/Llama-3.2-1B-Instruct\n",
        "README.md": "# AI Assistant - Vulcan Labs Take-Home Test\n\n## 1. Setup Instructions\n## 2. How to run\n## 3. High-level Design\n## 4. Assumptions & Limitations\n"
    }

    print("🚀 Đang khởi tạo cấu trúc dự án cho Vulcan Labs...")

    # Tạo thư mục
    for folder in structure:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created folder: {folder}")

    # Tạo file
    for file_path, content in files.items():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄 Created file: {file_path}")

    print("\n✅ Xong! Bạn đã có một khung dự án chuyên nghiệp. Chúc bạn làm bài test tốt!")

if __name__ == "__main__":
    create_project_structure()