from typing import Any, Dict

def parse_response(response: Any) -> Dict:
    # 1. Lấy nội dung câu trả lời
    content = response.content
    
    # 2. Khởi tạo giá trị mặc định
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    # 3. Kiểm tra và lấy thông tin token nếu có
    if hasattr(response, 'usage_metadata') and response.usage_metadata:
        input_tokens = response.usage_metadata.get('input_tokens', 0)
        output_tokens = response.usage_metadata.get('output_tokens', 0)
        total_tokens = response.usage_metadata.get('total_tokens', 0)
        
    return {
        "content": content,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens
    }