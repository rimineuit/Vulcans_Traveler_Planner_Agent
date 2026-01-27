from langchain_deepseek import ChatDeepSeek
from typing import Any, List
class Engine:
    def __init__(self, api_key: str, model: str = "deepseek-chat", temperature: float = 0.0, max_retries: int = 2, max_tokens: int = None, timeout: int = None):
        
        self.llm = ChatDeepSeek(
                    model="deepseek-chat",
                    temperature=0,
                    max_tokens=None,
                    timeout=None,
                    max_retries=2
                    # other params...
                    )

    def ask_question(self, msg_list: List[Any]) -> str:
        response = self.llm.invoke(msg_list)
        return response.answer