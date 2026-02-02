import os
from transformers import AutoTokenizer
from typing import List, Dict, Union

class TokenCounter:
    def __init__(self, model_name_or_path: str = "deepseek-ai/DeepSeek-V3"):
        """
        Khởi tạo Tokenizer. 
        Nếu bạn đã tải các file cấu hình về máy, hãy truyền đường dẫn folder vào đây.
        """
        try:
            # trust_remote_code=True là bắt buộc với kiến trúc của DeepSeek
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name_or_path, 
                trust_remote_code=True
            )
        except Exception as e:
            print(f"❌ Lỗi khởi tạo Tokenizer: {e}")
            self.tokenizer = None

    def count_text_tokens(self, text: str) -> int:
        """Đếm số lượng token trong một đoạn văn bản."""
        if not self.tokenizer or not text:
            return 0
        return len(self.tokenizer.encode(text))

    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Đếm tổng token cho một danh sách tin nhắn chat.
        Mỗi tin nhắn thường có cấu trúc: {'role': 'user', 'content': '...'}
        """
        num_tokens = 0
        for message in messages:
            # Cộng token cho vai trò (role), nội dung (content) và các ký tự đặc biệt
            num_tokens += 4 # Khoảng bù cho metadata của mỗi tin nhắn
            for key, value in message.items():
                num_tokens += self.count_text_tokens(value)
        num_tokens += 2 # Khoảng bù cho phản hồi sắp tới của trợ lý
        return num_tokens

    def truncate_history(self, messages: List[Dict[str, str]], max_tokens: int = 4096) -> List[Dict[str, str]]:
        """
        Cắt tỉa lịch sử chat để đảm bảo không vượt quá giới hạn cho phép.
        Giữ lại các tin nhắn mới nhất và System Prompt.
        """
        if self.count_messages_tokens(messages) <= max_tokens:
            return messages

        # Luôn giữ lại tin nhắn System (thường ở vị trí 0)
        system_message = None
        if messages and messages[0]['role'] == 'system':
            system_message = messages[0]
            messages = messages[1:]

        # Xóa dần tin nhắn cũ cho đến khi đạt ngưỡng
        while self.count_messages_tokens(messages) > (max_tokens - (4 if system_message else 0)):
            if len(messages) > 1:
                messages.pop(0)
            else:
                break
        
        return [system_message] + messages if system_message else messages