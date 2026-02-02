import streamlit as st
from api_client import create_new_session_api, get_user_sessions_api, get_chat_history_api, get_chat_completion_api, get_chat_summary_api

# --- 1. KHỞI TẠO STATE ---
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sessions" not in st.session_state:
    st.session_state.sessions = None
if "summary" not in st.session_state:
    st.session_state.summary = None
    
USER_ID = "rimine"

# Hàm helper để load dữ liệu session (Dùng nhiều lần nên tách ra)
def load_session_data(session_id):
    st.session_state.current_session_id = session_id
    st.session_state.messages = get_chat_history_api(session_id)
    st.session_state.summary = get_chat_summary_api(session_id)

# --- 2. LOGIC LOAD DỮ LIỆU BAN ĐẦU ---
if st.session_state.sessions is None:
    st.session_state.sessions = get_user_sessions_api(USER_ID, limit=10)
    if st.session_state.sessions:
        load_session_data(st.session_state.sessions[0]["session_id"])

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🤖 AI Nutri-Coach")
    
    # Hiển thị hồ sơ sức khỏe (Summary)
    if st.session_state.summary:
        with st.container(border=True):
            st.subheader("📊 Hồ sơ của bạn")
            summary_text = st.session_state.summary.get("summary_text", "Chưa có dữ liệu")
            st.caption(summary_text)
            
            with st.popover("🔍 Chi tiết chỉ số"):
                st.json(st.session_state.summary)
    
    if st.button("➕ New Chat", use_container_width=True):
        with st.spinner("Đang khởi tạo..."):
            new_session = create_new_session_api(USER_ID)
            if new_session:
                st.session_state.sessions.insert(0, new_session)
                load_session_data(new_session["session_id"])
                st.rerun()
    
    st.divider()
    st.subheader("📂 Lịch sử tư vấn")
    for sess in st.session_state.sessions:
        is_current = sess['session_id'] == st.session_state.current_session_id
        label = f"💬 {sess['session_id'][:8]}..."
        
        if st.sidebar.button(label, key=sess["session_id"], 
                             type="primary" if is_current else "secondary",
                             use_container_width=True):
            # FIX: Load cả history và summary khi đổi session
            load_session_data(sess["session_id"])
            st.rerun()

# --- 4. MAIN CHAT AREA ---
st.title("🍎 Diet & Fitness Assistant")

# Hiển thị lịch sử chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Xử lý tin nhắn mới
if prompt := st.chat_input("Hôm nay bạn đã ăn gì hoặc tập gì?"):
    # 1. Hiển thị User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Gọi API và hiển thị AI response
    with st.chat_message("assistant"):
        with st.spinner("Coach đang tính toán..."):
            response = get_chat_completion_api(USER_ID, st.session_state.current_session_id, prompt)
            st.markdown(response)
    
    # 3. Cập nhật State
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Quan trọng: Cập nhật lại Summary vì AI vừa mới học thêm thông tin mới từ tin nhắn này
    st.session_state.summary = get_chat_summary_api(st.session_state.current_session_id)
    
    st.rerun() # Chỉ rerun khi đã xử lý xong tin nhắn