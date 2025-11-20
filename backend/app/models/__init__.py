"""
데이터 모델 정의
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class WebSocketMessage(BaseModel):
    """
    WebSocket 메시지 기본 구조
    """
    type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: dict = {}


class AudioChunk(BaseModel):
    """
    오디오 청크 데이터
    """
    audio_data: bytes
    sample_rate: int = 16000
    channels: int = 1
    format: str = "wav"


class TextMessage(BaseModel):
    """
    텍스트 메시지
    """
    text: str
    language: str = "ko"


class ConversationMessage(BaseModel):
    """
    대화 메시지
    """
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionConfig(BaseModel):
    """
    세션 설정
    """
    use_audio: bool = True
    use_video: bool = True
    language: str = "ko"
    avatar_id: Optional[str] = None


class ErrorMessage(BaseModel):
    """
    에러 메시지
    """
    error_type: str
    message: str
    details: Optional[dict] = None
