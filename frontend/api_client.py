import requests
import streamlit as st
from dotenv import load_dotenv
import os
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

def create_new_session_api(user_id: str):
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/sessions/{user_id}")
        if response.status_code == 200:
            return response.json()["data"] # Trả về session object từ Backend
        else:
            st.error(f"Lỗi Backend: {response.text}")
            return None
    except Exception as e:
        st.error(f"Không thể kết nối đến Backend: {e}")
        return None

@st.cache_data(ttl=300) # Lưu kết quả trong 5 phút
def get_user_sessions_api(user_id: str, limit: int = 10):
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/users/{user_id}/sessions", params={"limit": limit})
        if response.status_code == 200:
            return response.json()["data"] # Trả về danh sách session từ Backend
        else:
            st.error(f"Lỗi Backend: {response.text}")
            return []
    except Exception as e:
        st.error(f"Không thể kết nối đến Backend: {e}")
        return []
    
@st.cache_data(ttl=300) # Lưu kết quả trong 5 phút
def get_chat_history_api(session_id: str, limit: int = 20):
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/chat_history/{session_id}", params={"limit": limit})
        if response.status_code == 200:
            return response.json()["data"] # Trả về lịch sử chat từ Backend
        else:
            st.error(f"Lỗi Backend: {response.text}")
            return []
    except Exception as e:
        st.error(f"Không thể kết nối đến Backend: {e}")
        return []
    
def get_chat_completion_api(user_id: str, session_id: str, user_message: str):
    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "query": user_message
    }
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/chat/completions", json=payload)
        if response.status_code == 200:
            return response.json()["response"] # Trả về phản hồi từ Backend
        else:
            st.error(f"Lỗi Backend: {response.text}")
            return "Xin lỗi, đã có lỗi xảy ra."
    except Exception as e:
        st.error(f"Không thể kết nối đến Backend: {e}")
        return "Xin lỗi, không thể kết nối đến dịch vụ."
    
def get_chat_summary_api(session_id: str):
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/chat_summary/{session_id}")
        if response.status_code == 200:
            return response.json()["data"] # Trả về bản tóm tắt từ Backend
        else:
            st.error(f"Lỗi Backend: {response.text}")
            return None
    except Exception as e:
        st.error(f"Không thể kết nối đến Backend: {e}")
        return None