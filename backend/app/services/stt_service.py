"""
STT (Speech-to-Text) 서비스
OpenAI Whisper를 사용한 음성 인식
"""

import whisper
import torch
import numpy as np
import io
import soundfile as sf
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class STTService:
    """
    음성을 텍스트로 변환하는 서비스
    """

    def __init__(self, model_name: str = "base", device: str = "cpu"):
        """
        Args:
            model_name: Whisper 모델 크기 (tiny, base, small, medium, large)
            device: 실행 디바이스 (cuda 또는 cpu)
        """
        self.model_name = model_name
        self.device = device
        self.model: Optional[whisper.Whisper] = None
        self.initialized = False

    async def initialize(self):
        """
        Whisper 모델 로드
        """
        try:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name, device=self.device)
            self.initialized = True
            logger.info(f"✅ Whisper model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            raise

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "ko"
    ) -> str:
        """
        오디오 데이터를 텍스트로 변환

        Args:
            audio_data: 오디오 바이너리 데이터 (WAV 형식)
            language: 언어 코드 (ko, en 등)

        Returns:
            변환된 텍스트
        """
        if not self.initialized or self.model is None:
            raise RuntimeError("STT service not initialized")

        try:
            # 바이트 데이터를 numpy 배열로 변환
            audio_io = io.BytesIO(audio_data)
            audio_array, sample_rate = sf.read(audio_io)

            # float32로 변환 및 정규화
            if audio_array.dtype != np.float32:
                audio_array = audio_array.astype(np.float32)

            # 스테레오를 모노로 변환
            if len(audio_array.shape) > 1:
                audio_array = audio_array.mean(axis=1)

            # Whisper로 음성 인식
            result = self.model.transcribe(
                audio_array,
                language=language,
                fp16=False if self.device == "cpu" else True
            )

            text = result["text"].strip()
            logger.info(f"🎤 Transcribed: {text}")

            return text

        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            raise

    async def cleanup(self):
        """
        리소스 정리
        """
        if self.model is not None:
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        self.initialized = False
        logger.info("STT service cleaned up")


class MockSTTService:
    """
    테스트용 목업 STT 서비스
    """

    def __init__(self, *args, **kwargs):
        self.initialized = False

    async def initialize(self):
        self.initialized = True
        logger.info("✅ Mock STT service initialized")

    async def transcribe(self, audio_data: bytes, language: str = "ko") -> str:
        """
        목업 응답 반환
        """
        return "안녕하세요, 테스트 음성 입력입니다."

    async def cleanup(self):
        self.initialized = False
