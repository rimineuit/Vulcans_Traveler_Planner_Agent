from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
import os
import getpass
from typing import Any, List, Dict
from schema import ChatResult
import asyncio


class ChatEngine:
    def __new__(self, model: str = "deepseek-chat", temperature: float = 1.3, max_retries: int = 2, max_tokens: int = None, timeout: int = None):
        load_dotenv()
        if not os.getenv("DEEPSEEK_API_KEY"):
            os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter your DeepSeek API key: ")
        if not os.getenv("LANGSMITH_API_KEY"):
            os.environ["LANGSMITH_API_KEY"] = getpass.getpass("Enter your LangSmith API key: ")
        if model == "deepseek-chat":
            self.llm = ChatDeepSeek(
                        model="deepseek-chat",
                        temperature=temperature,
                        max_retries=max_retries,
                        max_tokens=max_tokens,
                        timeout=timeout
                        )

    def _parse_response(self, response: AIMessage) -> ChatResult:
        """Hàm private để làm sạch dữ liệu"""
        usage = response.usage_metadata or {}
        
        return ChatResult(
            answer=response.content,
            input_tokens=usage.get('input_tokens', 0),
            output_tokens=usage.get('output_tokens', 0),
            total_tokens=usage.get('total_tokens', 0)
        )
        
    async def get_response(self, msg_list: List[Any]):
        # Lấy raw response từ LLM
        raw_response = await self.llm.invoke(msg_list)
        # Trích xuất nội dung từ response
        clean_response = self._parse_response(raw_response)
        return clean_response
    
async def main():
    engine = ChatEngine(temperature=0.7) # Khởi tạo engine
    messages = [
        ("system", "You are a helpful assistant that translates English to Vietnamese."),
        ("human", "I love programming.")
    ]
    
    # Gọi hàm async bằng await
    result = await engine.get_response(messages)
    print(f"Dịch: {result.answer}")
    print(f"Sử dụng: {result.total_tokens} tokens")

if __name__ == "__main__":
    asyncio.run(main())