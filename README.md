# 🍎 AI Nutri-Coach: Chat Assistant with Session Memory

> **Vulcan Labs AI Engineer Intern - Take-Home Test Submission** > **Author:** Nguyen Le Thanh Minh (Rimine)

**AI Nutri-Coach** là một trợ lý ảo thông minh chuyên về dinh dưỡng và thể hình. Dự án tập trung giải quyết hai bài toán lớn của Chatbot LLM hiện nay: **Quản lý ngữ cảnh dài (Long-term Memory)** và **Hiểu ý định người dùng (Ambiguous Query Understanding)**.

---

## 🚀 Tính Năng Nổi Bật

* **🧠 Smart Memory Management**:
    * **Short-term**: Lưu trữ nguyên văn các đoạn hội thoại gần nhất.
    * **Long-term**: Tự động tóm tắt hội thoại khi vượt ngưỡng Token để cập nhật vào "Hồ sơ sức khỏe" (User Profile) có cấu trúc (Cân nặng, chiều cao, dị ứng, mục tiêu...).
* **🔍 Advanced Query Pipeline**:
    * **Rewrite**: Viết lại câu hỏi của người dùng để rõ nghĩa hơn dựa trên ngữ cảnh cũ.
    * **Clarify**: Tự động đặt câu hỏi ngược lại cho người dùng nếu thiếu thông tin quan trọng (VD: Cần biết cân nặng để tính Calories).
    * **Augment**: Bổ sung dữ liệu hồ sơ vào ngữ cảnh trước khi gửi cho LLM trả lời.
* **⚡ Tech Stack hiện đại**:
    * **Backend**: FastAPI (Python 3.11), Pydantic (Structured Output).
    * **AI Engine**: LangChain, DeepSeek-V3 (via API), LangSmith (Tracing).
    * **Database**: MongoDB (Motor Async Driver).
    * **Frontend**: Streamlit.
    * **DevOps**: Docker & Docker Compose.

---

## 🚀 1. Hướng dẫn Cài đặt & Khởi chạy (Quick Start)

Hệ thống được đóng gói hoàn toàn bằng Docker ("Containerized"), đảm bảo chạy ổn định trên mọi môi trường.

### Yêu cầu tiên quyết
- Docker & Docker Compose cài sẵn.
- API Key của **DeepSeek** (Model chính) và **LangSmith** (Monitoring - tuỳ chọn).

### Bước 1: Cấu hình môi trường
Tạo file `.env` tại thư mục gốc của dự án và điền các thông tin sau:

```env
# LLM Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Monitoring (Optional - LangChain)
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=[https://api.smith.langchain.com](https://api.smith.langchain.com)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT="Vulcans Chatbot"

# Database (Internal Docker Networking)
MONGO_URI=mongodb://mongodb:27017/vulcan_chat_db
MONGO_DB_NAME=vulcan_chat_db

```

### Bước 2: Khởi chạy hệ thống

Chạy lệnh sau tại thư mục gốc để build và start toàn bộ services:

```bash
docker-compose up --build
```

### Bước 3: Truy cập ứng dụng

Sau khi container khởi động thành công:

* **Giao diện Chat (Streamlit):** [http://localhost:8501](https://www.google.com/search?q=http://localhost:8501)
* **API Documentation (Swagger UI):** [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs)
* **Quản lý Database (Mongo Express):** [http://localhost:8081](https://www.google.com/search?q=http://localhost:8081)

---

## 🛠️ 2. Kiến trúc & Thiết kế hệ thống (High-Level Design)

Hệ thống được thiết kế theo mô hình **Modular Monolith**, tách biệt rõ ràng giữa Frontend, Backend và Database.

### A. Chiến lược quản lý bộ nhớ (Memory Management Strategy)

Thay vì gửi toàn bộ lịch sử chat (gây tốn token và tăng độ trễ), hệ thống sử dụng cơ chế **Summarization Trigger**:

1. **Token Counting:** Sử dụng `AutoTokenizer` (DeepSeek-V3) để đếm chính xác token của từng tin nhắn.
2. **Trigger Condition:** Khi tổng token của các tin nhắn *chưa tóm tắt* vượt ngưỡng **2000 tokens**.
3. **Summarization Process (Async):**
* Hệ thống gọi LLM để nén các tin nhắn cũ.
* Trích xuất thông tin quan trọng vào **Structured User Profile** (JSON Schema: Weight, Height, Goals, Restrictions).
* Cập nhật lại `summaries` collection và đánh dấu `is_summarized=True` cho các tin nhắn cũ.


4. **Optimization:** Sử dụng **MongoDB Partial Index** (`idx_unsummarized_messages`) để truy vấn các tin nhắn chưa tóm tắt với tốc độ O(1).

### B. Pipeline hiểu truy vấn (Query Understanding Pipeline)

Mọi câu hỏi của người dùng đều đi qua `ChatOrchestrator` với quy trình 3 bước:

1. **Rewrite (Viết lại):**
* Input: Câu hỏi hiện tại + Lịch sử hội thoại.
* Output: Câu hỏi rõ nghĩa, giải quyết các đại từ mơ hồ (vd: "nó", "cái đó").


2. **Clarify (Làm rõ - Rẽ nhánh):**
* Hệ thống kiểm tra xem đã đủ thông tin để trả lời chưa (vd: Hỏi TDEE nhưng thiếu Cân nặng/Chiều cao).
* Nếu thiếu: Trả về câu hỏi Clarifying Questions cho người dùng.
* Nếu đủ: Chuyển sang bước tiếp theo.


3. **Augment & Answer (Tăng cường ngữ cảnh & Trả lời):**
* Kết hợp: `Rewritten Query` + `Session Summary (JSON)` + `Recent Messages`.
* Gửi Prompt đã được làm giàu ngữ cảnh tới LLM để sinh câu trả lời cuối cùng.



---

## 📊 3. Định dạng dữ liệu (Structured Outputs)

Dự án áp dụng triệt để **Pydantic** để đảm bảo tính nhất quán của dữ liệu (Type Safety).

### Session Summary Schema

```json
{
  "user_info": {
    "weight": 70.5,
    "height": 175,
    "bmi": 23.0,
    "age": 25,
    "gender": "Nam"
  },
  "goals": ["Giảm mỡ", "Tăng cơ"],
  "restrictions": ["Dị ứng hải sản"],
  "summary_text": "Người dùng nam, 25 tuổi, đang muốn giảm mỡ..."
}

```

---

## 🧪 4. Kịch bản kiểm thử (Test Scenarios)

Dữ liệu mẫu nằm trong thư mục `/data` để giám khảo dễ dàng kiểm chứng các luồng xử lý chính.

### Flow 1: Kiểm thử bộ nhớ (Memory Trigger)

* **Mục tiêu:** Chứng minh khả năng tự động tóm tắt khi hội thoại dài.
* **Cách test:**
1. Copy nội dung từ `data/long_conv.jsonl`.
2. Paste liên tục vào khung chat.
3. Quan sát log backend: `🔄 Token threshold reached... Starting summarization...`.
4. Kiểm tra Sidebar trên Streamlit: Phần "Hồ sơ của bạn" sẽ tự động cập nhật thông tin mới.



### Flow 2: Xử lý truy vấn mơ hồ (Ambiguous Query)

* **Mục tiêu:** Chứng minh khả năng hiểu ngữ cảnh và viết lại câu hỏi.
* **Cách test:**
1. Nhập: *"Tôi muốn ăn ức gà cho bữa trưa."*
2. Nhập tiếp (từ `data/ambiguous.jsonl`): *"Nó bao nhiêu calo?"*
3. **Kết quả:** Bot sẽ hiểu "Nó" là "Ức gà" và trả lời chính xác lượng calo của ức gà, thay vì hỏi lại "Nó là cái gì?".



---

## 📂 5. Cấu trúc dự án

```text
.
├── backend/                # FastAPI Application
│   ├── app/
│   │   ├── core/           # Core Logic (Memory, Query Pipeline, LLM)
│   │   ├── schemas/        # Pydantic Models
│   │   ├── utils/          # Token Counter, Decorators
│   │   ├── main.py         # App Entrypoint
│   │   └── init_db.py      # Database Initialization Script
│   ├── Dockerfile
│   └── entrypoint.sh       # Startup Script (Init DB -> Start Server)
├── frontend/               # Streamlit Application
│   ├── app.py              # UI Logic
│   └── api_client.py       # API Communication Layer
├── data/                   # Test datasets (.jsonl)
├── docker-compose.yml      # Orchestration
└── requirements.txt        # Dependencies

```

---

## 📝 6. Giả định & Hạn chế (Assumptions & Limitations)

1. **Tokenizer Download:** Lần chạy đầu tiên có thể mất 1-2 phút để tải `DeepSeek-V3` tokenizer từ HuggingFace.
2. **API Rate Limit:** Tốc độ phản hồi phụ thuộc vào API của DeepSeek. Hệ thống đã implement cơ chế `Async` để không block main thread.
3. **Session Isolation:** Mỗi session hoạt động độc lập. Dữ liệu tóm tắt thuộc về session đó, chưa chia sẻ chéo giữa các session của cùng một User (có thể nâng cấp trong tương lai).

---

*Built with ❤️ using FastAPI, LangChain & Streamlit.*

```

```