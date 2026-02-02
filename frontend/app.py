import streamlit as st
from api_client import create_new_session_api, get_user_sessions_api, get_chat_history_api, get_chat_completion_api, get_chat_summary_api, get_unsummarized_tokens_count_api
import time

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
    # --- PHẦN HIỂN THỊ TOKEN (NEW) ---
    if st.session_state.current_session_id:
        st.divider()
        # 1. Gọi API lấy số lượng token hiện tại
        current_tokens = get_unsummarized_tokens_count_api(st.session_state.current_session_id)
        threshold = 2000 # Ngưỡng tóm tắt Minh đã đặt trong backend
        
        # 2. Tính toán tỷ lệ %
        progress = min(current_tokens / threshold, 1.0)
        
        # 3. Hiển thị UI
        st.subheader("🧠 Trí nhớ ngắn hạn")
        st.progress(progress) # Thanh màu xanh (mặc định của Streamlit)
        
        # Hiển thị số liệu chi tiết
        st.caption(f"Tokens: **{current_tokens}** / {threshold}")
        
        if progress >= 0.9:
            st.warning("⚠️ Sắp tới ngưỡng tóm tắt dữ liệu!")
        elif progress >= 1.0:
            st.success("✅ Đang tiến hành tóm tắt để tối ưu bộ nhớ...")
            
    if st.button("🔄 Làm mới hồ sơ", use_container_width=True):
        st.session_state.summary = get_chat_summary_api(st.session_state.current_session_id)
        st.rerun()
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
    
    current_tokens = get_unsummarized_tokens_count_api(st.session_state.current_session_id)
    threshold = 2000

    # Nếu token còn thấp (ví dụ < 1800), bỏ qua việc đợi vì chắc chắn chưa tóm tắt
    if current_tokens < (threshold * 0.9):
        # Cập nhật nhanh summary hiện tại (có thể AI vừa bóc tách thêm vài info nhỏ)
        st.session_state.summary = get_chat_summary_api(st.session_state.current_session_id)
    else:
        # Bước B: Nếu mấp mé hoặc vượt ngưỡng, mới tiến hành "Đợi thông minh"
        with st.sidebar:
            status_placeholder = st.empty()
            status_placeholder.warning("🔄 AI đang tối ưu bộ nhớ...")
            
            old_summary_text = st.session_state.summary.get("summary_text", "") if st.session_state.summary else ""
            
            # Polling ngắn: 3 lần, mỗi lần 2s = Max 6s
            for i in range(3):
                time.sleep(2) 
                new_summary = get_chat_summary_api(st.session_state.current_session_id)
                
                # Nếu thấy text tóm tắt đã khác trước -> Backend đã làm xong!
                if new_summary and new_summary.get("summary_text") != old_summary_text:
                    st.session_state.summary = new_summary
                    st.toast("✅ Hồ sơ đã được cập nhật!", icon="🧠")
                    break
            
            status_placeholder.empty()
            # Xóa thông báo loading
            status_placeholder.empty()
    st.rerun() # Chỉ rerun khi đã xử lý xong tin nhắn