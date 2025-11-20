"""
애플리케이션 설정 관리
환경 변수를 통해 설정을 로드하고 관리
"""

from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    """

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS 설정
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # OpenAI API 설정 (선택사항)
    OPENAI_API_KEY: str = ""

    # Ollama 설정 (로컬 LLM)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"

    # AI 모델 설정
    USE_OPENAI_LLM: bool = False  # True면 OpenAI, False면 Ollama
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    TTS_MODEL: str = "tts_models/ko/cv/vits"  # 한국어 TTS 모델

    # 오디오 설정
    SAMPLE_RATE: int = 16000  # 16kHz
    AUDIO_CHANNELS: int = 1  # Mono

    # 비디오 설정 (Wav2Lip)
    VIDEO_FPS: int = 25
    VIDEO_RESOLUTION: tuple = (256, 256)  # (width, height)
    AVATAR_IMAGE_PATH: str = "models/avatar.jpg"

    # 모델 경로
    MODELS_DIR: str = "models"
    WAV2LIP_CHECKPOINT: str = "models/wav2lip_gan.pth"

    # 성능 설정
    MAX_AUDIO_CHUNK_SIZE: int = 1024 * 16  # 16KB
    DEVICE: str = "cpu"  # "cuda" 또는 "cpu"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    설정 싱글톤 인스턴스 반환
    """
    return Settings()
