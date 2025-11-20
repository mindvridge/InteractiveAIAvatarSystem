"""
LLM (Large Language Model) 서비스
Ollama 또는 OpenAI API를 사용한 대화 생성
"""

import httpx
from typing import List, Dict, Optional
import logging
from openai import AsyncOpenAI

from app.models import ConversationMessage

logger = logging.getLogger(__name__)


class LLMService:
    """
    대화 생성을 위한 LLM 서비스
    """

    def __init__(
        self,
        use_openai: bool = False,
        openai_api_key: str = "",
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "llama2"
    ):
        """
        Args:
            use_openai: OpenAI API 사용 여부
            openai_api_key: OpenAI API 키
            ollama_base_url: Ollama 서버 URL
            ollama_model: Ollama 모델 이름
        """
        self.use_openai = use_openai
        self.openai_api_key = openai_api_key
        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model
        self.client: Optional[AsyncOpenAI] = None
        self.initialized = False
        self.conversation_history: List[ConversationMessage] = []

    async def initialize(self):
        """
        LLM 서비스 초기화
        """
        try:
            if self.use_openai:
                if not self.openai_api_key:
                    raise ValueError("OpenAI API key is required")
                self.client = AsyncOpenAI(api_key=self.openai_api_key)
                logger.info("✅ OpenAI LLM service initialized")
            else:
                # Ollama 연결 테스트
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.ollama_base_url}/api/tags")
                    if response.status_code == 200:
                        logger.info(f"✅ Ollama LLM service initialized ({self.ollama_model})")
                    else:
                        raise ConnectionError(f"Failed to connect to Ollama: {response.status_code}")

            self.initialized = True

        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM service: {e}")
            raise

    async def generate_response(self, user_message: str) -> str:
        """
        사용자 메시지에 대한 응답 생성

        Args:
            user_message: 사용자 입력 메시지

        Returns:
            AI의 응답 메시지
        """
        if not self.initialized:
            raise RuntimeError("LLM service not initialized")

        # 대화 히스토리에 추가
        self.conversation_history.append(
            ConversationMessage(role="user", content=user_message)
        )

        try:
            if self.use_openai:
                response = await self._generate_openai_response()
            else:
                response = await self._generate_ollama_response()

            # 응답을 히스토리에 추가
            self.conversation_history.append(
                ConversationMessage(role="assistant", content=response)
            )

            logger.info(f"🤖 LLM Response: {response}")
            return response

        except Exception as e:
            logger.error(f"❌ LLM generation error: {e}")
            raise

    async def _generate_openai_response(self) -> str:
        """
        OpenAI API를 사용한 응답 생성
        """
        if self.client is None:
            raise RuntimeError("OpenAI client not initialized")

        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in self.conversation_history
        ]

        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )

        return response.choices[0].message.content or ""

    async def _generate_ollama_response(self) -> str:
        """
        Ollama를 사용한 응답 생성
        """
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in self.conversation_history
        ]

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.ollama_base_url}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": messages,
                    "stream": False
                }
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")

            result = response.json()
            return result.get("message", {}).get("content", "")

    def clear_history(self):
        """
        대화 히스토리 초기화
        """
        self.conversation_history.clear()
        logger.info("Conversation history cleared")

    async def cleanup(self):
        """
        리소스 정리
        """
        self.clear_history()
        self.initialized = False
        logger.info("LLM service cleaned up")


class MockLLMService:
    """
    테스트용 목업 LLM 서비스
    """

    def __init__(self, *args, **kwargs):
        self.initialized = False
        self.conversation_history: List[ConversationMessage] = []

    async def initialize(self):
        self.initialized = True
        logger.info("✅ Mock LLM service initialized")

    async def generate_response(self, user_message: str) -> str:
        """
        목업 응답 반환
        """
        responses = [
            "안녕하세요! 무엇을 도와드릴까요?",
            "네, 이해했습니다. 더 궁금한 것이 있으신가요?",
            "좋은 질문이네요. 그것에 대해 설명드리겠습니다.",
            "감사합니다. 다른 질문이 있으시면 말씀해주세요."
        ]

        # 간단한 패턴 매칭
        user_lower = user_message.lower()
        if any(word in user_lower for word in ["안녕", "hello", "hi"]):
            return "안녕하세요! 반갑습니다. 무엇을 도와드릴까요?"
        elif any(word in user_lower for word in ["고마", "감사"]):
            return "천만에요! 언제든지 도와드리겠습니다."
        else:
            import random
            return random.choice(responses)

    def clear_history(self):
        self.conversation_history.clear()

    async def cleanup(self):
        self.initialized = False
