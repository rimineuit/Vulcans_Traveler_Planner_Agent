from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
import os
import getpass
from typing import Any, List, Dict, Optional, Type
from .schema import ChatResult
from pydantic import BaseModel, Field
import asyncio


class LLMService:
    _instance = None  # Singleton instance
    def __new__(cls, model: str = "deepseek-chat", temperature: float = 1.3, max_retries: int = 2, max_tokens: int = None, timeout: int = None):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            
            load_dotenv()
            if not os.getenv("DEEPSEEK_API_KEY"):
                os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter your DeepSeek API key: ")
            if not os.getenv("LANGSMITH_API_KEY"):
                os.environ["LANGSMITH_API_KEY"] = getpass.getpass("Enter your LangSmith API key: ")
            
            if model == "deepseek-chat":
                cls._instance.llm = ChatDeepSeek(
                            model="deepseek-chat",
                            temperature=temperature,
                            max_retries=max_retries,
                            max_tokens=max_tokens,
                            timeout=timeout
                            )
        return cls._instance

    def _parse_response(self, response: AIMessage) -> ChatResult:
        """Hàm private để làm sạch dữ liệu"""
        usage = response.usage_metadata or {}
        
        return ChatResult(
            answer=response.content,
            input_tokens=usage.get('input_tokens', 0),
            output_tokens=usage.get('output_tokens', 0),
            total_tokens=usage.get('total_tokens', 0)
        )
        
    async def get_response(self, msgs: Any, structured: Optional[Type[BaseModel]] = None):
        """
        Xử lý linh hoạt cả Chat thông thường và Trích xuất dữ liệu có cấu trúc.
        """
        if structured:
            # 1. Thiết lập model để trả về cấu trúc Pydantic
            # include_raw=True cực kỳ quan trọng để lấy được metadata/tokens
            model_with_structure = self.llm.with_structured_output(structured, include_raw=True)
            
            # 2. Gọi model (msgs lúc này có thể là Prompt hoặc List messages)
            result = await model_with_structure.ainvoke(msgs)
            
            # result lúc này là dict: {'raw': AIMessage, 'parsed': BaseModel, 'parsing_error': ...}
            # Ta tận dụng hàm _parse_response để lấy token từ 'raw'
            clean_meta = self._parse_response(result['raw'])
            
            return {
                "parsed": result['parsed'],   # Object Pydantic đã parse (vd: Movie)
                "metadata": clean_meta,       # Lượng token, prompt cache...
                "error": result['parsing_error']
            }
        
        else:
            # Trường hợp chat thông thường (trả về text)
            raw_response = await self.llm.ainvoke(msgs)
            
            # Làm sạch và lấy thông tin token
            clean_response = self._parse_response(raw_response)
            
            # Trả về format đồng nhất hoặc chỉ trả về kết quả parse
            return clean_response

class Movie(BaseModel):
    """A movie with details."""
    title: str = Field(..., description="The title of the movie")
    year: int = Field(..., description="The year the movie was released")
    director: str = Field(..., description="The director of the movie")
    rating: float = Field(..., description="The movie's rating out of 10")
    
async def main():
    engine = LLMService(temperature=0.7) # Khởi tạo engine
    messages = [
        ("system", "You are a helpful assistant that translates English to Vietnamese."),
        ("human", "I love programming.")
    ]
    
    # Gọi hàm async bằng await
    result = await engine.get_response("Provide details about the movie Inception", structured=Movie)
    # print(f"Dịch: {result.answer}")
    # print(f"Sử dụng: {result.total_tokens} tokens")
    print(f"Movie Details: {result}")

if __name__ == "__main__":
    asyncio.run(main())