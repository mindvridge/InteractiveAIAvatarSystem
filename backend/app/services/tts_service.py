"""
TTS (Text-to-Speech) 서비스
Coqui TTS를 사용한 음성 합성
"""

import io
import numpy as np
import soundfile as sf
from typing import Optional
import logging

try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logging.warning("TTS library not available, using mock service")

logger = logging.getLogger(__name__)


class TTSService:
    """
    텍스트를 음성으로 변환하는 서비스
    """

    def __init__(self, model_name: str = "tts_models/ko/cv/vits", device: str = "cpu"):
        """
        Args:
            model_name: TTS 모델 이름
            device: 실행 디바이스 (cuda 또는 cpu)
        """
        self.model_name = model_name
        self.device = device
        self.tts: Optional[TTS] = None
        self.initialized = False

    async def initialize(self):
        """
        TTS 모델 로드
        """
        if not TTS_AVAILABLE:
            logger.warning("⚠️  TTS library not available, skipping initialization")
            return

        try:
            logger.info(f"Loading TTS model: {self.model_name}")
            self.tts = TTS(model_name=self.model_name, progress_bar=False)
            if self.device == "cuda":
                self.tts.to(self.device)
            self.initialized = True
            logger.info(f"✅ TTS model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"❌ Failed to load TTS model: {e}")
            raise

    async def synthesize(
        self,
        text: str,
        sample_rate: int = 22050
    ) -> bytes:
        """
        텍스트를 음성으로 변환

        Args:
            text: 변환할 텍스트
            sample_rate: 오디오 샘플링 레이트

        Returns:
            WAV 형식의 오디오 바이너리 데이터
        """
        if not self.initialized or self.tts is None:
            raise RuntimeError("TTS service not initialized")

        try:
            logger.info(f"🔊 Synthesizing: {text}")

            # 텍스트를 음성으로 변환
            wav = self.tts.tts(text)

            # numpy 배열을 WAV 바이트로 변환
            wav_array = np.array(wav, dtype=np.float32)

            # BytesIO를 사용하여 WAV 파일 생성
            audio_io = io.BytesIO()
            sf.write(audio_io, wav_array, sample_rate, format='WAV')
            audio_io.seek(0)

            audio_bytes = audio_io.read()
            logger.info(f"✅ Synthesized {len(audio_bytes)} bytes")

            return audio_bytes

        except Exception as e:
            logger.error(f"❌ TTS synthesis error: {e}")
            raise

    async def cleanup(self):
        """
        리소스 정리
        """
        if self.tts is not None:
            del self.tts
        self.initialized = False
        logger.info("TTS service cleaned up")


class MockTTSService:
    """
    테스트용 목업 TTS 서비스
    """

    def __init__(self, *args, **kwargs):
        self.initialized = False

    async def initialize(self):
        self.initialized = True
        logger.info("✅ Mock TTS service initialized")

    async def synthesize(self, text: str, sample_rate: int = 22050) -> bytes:
        """
        목업 오디오 데이터 반환 (무음)
        """
        # 1초 길이의 무음 생성
        duration = 1.0
        samples = int(sample_rate * duration)
        audio_array = np.zeros(samples, dtype=np.float32)

        # WAV 형식으로 변환
        audio_io = io.BytesIO()
        sf.write(audio_io, audio_array, sample_rate, format='WAV')
        audio_io.seek(0)

        return audio_io.read()

    async def cleanup(self):
        self.initialized = False
