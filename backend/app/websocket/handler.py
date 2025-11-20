"""
WebSocket 연결 핸들러
클라이언트와의 실시간 양방향 통신 처리
"""

from fastapi import WebSocket
import json
import asyncio
import logging
from typing import Optional, Dict, Any
import base64

from app.services.stt_service import STTService, MockSTTService
from app.services.tts_service import TTSService, MockTTSService
from app.services.llm_service import LLMService, MockLLMService
from app.services.wav2lip_service import Wav2LipService, MockWav2LipService
from app.services.config import get_settings
from app.utils.video_utils import video_to_base64, cleanup_temp_files
import tempfile
import os

logger = logging.getLogger(__name__)
settings = get_settings()


class WebSocketHandler:
    """
    WebSocket 연결을 관리하고 AI 서비스를 조율하는 핸들러
    """

    def __init__(self):
        self.stt_service: Optional[STTService] = None
        self.tts_service: Optional[TTSService] = None
        self.llm_service: Optional[LLMService] = None
        self.wav2lip_service: Optional[Wav2LipService] = None
        self.active_connections: Dict[WebSocket, Dict[str, Any]] = {}
        self.temp_files: list[str] = []  # 임시 파일 추적

    async def initialize_services(self):
        """
        AI 서비스들 초기화
        """
        # STT 서비스 초기화
        try:
            self.stt_service = STTService(
                model_name=settings.WHISPER_MODEL,
                device=settings.DEVICE
            )
            await self.stt_service.initialize()
        except Exception as e:
            logger.warning(f"⚠️  Using mock STT service: {e}")
            self.stt_service = MockSTTService()
            await self.stt_service.initialize()

        # TTS 서비스 초기화
        try:
            self.tts_service = TTSService(
                model_name=settings.TTS_MODEL,
                device=settings.DEVICE
            )
            await self.tts_service.initialize()
        except Exception as e:
            logger.warning(f"⚠️  Using mock TTS service: {e}")
            self.tts_service = MockTTSService()
            await self.tts_service.initialize()

        # LLM 서비스 초기화
        try:
            self.llm_service = LLMService(
                use_openai=settings.USE_OPENAI_LLM,
                openai_api_key=settings.OPENAI_API_KEY,
                ollama_base_url=settings.OLLAMA_BASE_URL,
                ollama_model=settings.OLLAMA_MODEL
            )
            await self.llm_service.initialize()
        except Exception as e:
            logger.warning(f"⚠️  Using mock LLM service: {e}")
            self.llm_service = MockLLMService()
            await self.llm_service.initialize()

        # Wav2Lip 서비스 초기화
        try:
            self.wav2lip_service = Wav2LipService(
                checkpoint_path=settings.WAV2LIP_CHECKPOINT,
                avatar_image_path=settings.AVATAR_IMAGE_PATH,
                device=settings.DEVICE,
                resolution=settings.VIDEO_RESOLUTION,
                fps=settings.VIDEO_FPS
            )
            await self.wav2lip_service.initialize()
        except Exception as e:
            logger.warning(f"⚠️  Using mock Wav2Lip service: {e}")
            self.wav2lip_service = MockWav2LipService(
                avatar_image_path=settings.AVATAR_IMAGE_PATH,
                resolution=settings.VIDEO_RESOLUTION,
                fps=settings.VIDEO_FPS
            )
            await self.wav2lip_service.initialize()

    async def handle_connection(self, websocket: WebSocket):
        """
        WebSocket 연결 처리

        Args:
            websocket: WebSocket 연결 객체
        """
        # 연결 정보 저장
        self.active_connections[websocket] = {
            "session_id": id(websocket),
            "language": "ko"
        }

        # 연결 성공 메시지 전송
        await self.send_message(websocket, {
            "type": "connection_established",
            "data": {
                "session_id": id(websocket),
                "message": "Connected to AI Avatar System"
            }
        })

        try:
            # 메시지 수신 루프
            while True:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive()

                if "text" in data:
                    # 텍스트 메시지 처리
                    await self.handle_text_message(websocket, data["text"])
                elif "bytes" in data:
                    # 바이너리 메시지 (오디오) 처리
                    await self.handle_audio_message(websocket, data["bytes"])

        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}", exc_info=True)
            raise

    async def handle_text_message(self, websocket: WebSocket, message: str):
        """
        텍스트 메시지 처리

        Args:
            websocket: WebSocket 연결 객체
            message: 수신된 텍스트 메시지
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "text_input":
                # 텍스트 입력 처리
                await self.process_text_input(websocket, data.get("text", ""))

            elif message_type == "config":
                # 설정 업데이트
                self.active_connections[websocket].update(data.get("config", {}))
                await self.send_message(websocket, {
                    "type": "config_updated",
                    "data": {"status": "success"}
                })

            elif message_type == "ping":
                # 핑-퐁 (연결 유지)
                await self.send_message(websocket, {"type": "pong"})

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message: {message}")
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            await self.send_error(websocket, str(e))

    async def handle_audio_message(self, websocket: WebSocket, audio_data: bytes):
        """
        오디오 메시지 처리 (음성 → 텍스트 → LLM → 음성)

        Args:
            websocket: WebSocket 연결 객체
            audio_data: 오디오 바이너리 데이터
        """
        try:
            # 처리 시작 알림
            await self.send_message(websocket, {
                "type": "processing",
                "data": {"stage": "stt"}
            })

            # 1. STT: 음성 → 텍스트
            if self.stt_service is None:
                raise RuntimeError("STT service not available")

            language = self.active_connections[websocket].get("language", "ko")
            user_text = await self.stt_service.transcribe(audio_data, language)

            # 인식된 텍스트 전송
            await self.send_message(websocket, {
                "type": "transcription",
                "data": {"text": user_text}
            })

            # 2. 텍스트 입력 처리 (LLM + TTS)
            await self.process_text_input(websocket, user_text)

        except Exception as e:
            logger.error(f"Error handling audio message: {e}")
            await self.send_error(websocket, str(e))

    async def process_text_input(self, websocket: WebSocket, text: str):
        """
        텍스트 입력 처리 (LLM → TTS → Wav2Lip)

        Args:
            websocket: WebSocket 연결 객체
            text: 입력 텍스트
        """
        audio_file_path = None
        video_file_path = None

        try:
            # LLM 처리 중 알림
            await self.send_message(websocket, {
                "type": "processing",
                "data": {"stage": "llm"}
            })

            # 1. LLM: 텍스트 → 응답 생성
            if self.llm_service is None:
                raise RuntimeError("LLM service not available")

            response_text = await self.llm_service.generate_response(text)

            # 응답 텍스트 전송
            await self.send_message(websocket, {
                "type": "response_text",
                "data": {"text": response_text}
            })

            # TTS 처리 중 알림
            await self.send_message(websocket, {
                "type": "processing",
                "data": {"stage": "tts"}
            })

            # 2. TTS: 텍스트 → 음성
            if self.tts_service is None:
                raise RuntimeError("TTS service not available")

            audio_bytes = await self.tts_service.synthesize(response_text)

            # 임시 오디오 파일 저장
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.wav', delete=False) as audio_file:
                audio_file.write(audio_bytes)
                audio_file_path = audio_file.name
                self.temp_files.append(audio_file_path)

            # 오디오를 base64로 인코딩하여 전송
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

            await self.send_message(websocket, {
                "type": "audio_response",
                "data": {
                    "audio": audio_base64,
                    "format": "wav"
                }
            })

            # Wav2Lip 처리 중 알림
            await self.send_message(websocket, {
                "type": "processing",
                "data": {"stage": "lipsync"}
            })

            # 3. Wav2Lip: 오디오 + 아바타 → 립싱크 비디오
            if self.wav2lip_service is None:
                raise RuntimeError("Wav2Lip service not available")

            # 임시 출력 비디오 파일 경로
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.mp4', delete=False) as video_file:
                video_file_path = video_file.name
                self.temp_files.append(video_file_path)

            # 립싱크 비디오 생성
            final_video_path = await self.wav2lip_service.generate_lipsync_video(
                audio_file_path,
                video_file_path
            )

            # 비디오를 base64로 인코딩하여 전송
            video_base64 = video_to_base64(final_video_path)

            await self.send_message(websocket, {
                "type": "video_response",
                "data": {
                    "video": video_base64,
                    "format": "mp4"
                }
            })

            # 처리 완료
            await self.send_message(websocket, {
                "type": "processing_complete"
            })

            # 임시 파일 정리 (비동기)
            asyncio.create_task(self._cleanup_session_files())

        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            await self.send_error(websocket, str(e))
            # 에러 발생 시에도 임시 파일 정리
            asyncio.create_task(self._cleanup_session_files())

    async def _cleanup_session_files(self):
        """
        세션 임시 파일 정리 (일정 시간 후)
        """
        # 5초 대기 후 정리 (클라이언트가 다운로드할 시간 확보)
        await asyncio.sleep(5)
        if self.temp_files:
            await cleanup_temp_files(self.temp_files)
            self.temp_files.clear()

    async def send_message(self, websocket: WebSocket, message: dict):
        """
        WebSocket으로 메시지 전송

        Args:
            websocket: WebSocket 연결 객체
            message: 전송할 메시지 (딕셔너리)
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def send_error(self, websocket: WebSocket, error_message: str):
        """
        에러 메시지 전송

        Args:
            websocket: WebSocket 연결 객체
            error_message: 에러 메시지
        """
        await self.send_message(websocket, {
            "type": "error",
            "data": {"message": error_message}
        })

    async def cleanup_connection(self, websocket: WebSocket):
        """
        연결 종료 시 정리

        Args:
            websocket: WebSocket 연결 객체
        """
        if websocket in self.active_connections:
            del self.active_connections[websocket]
        logger.info(f"Connection cleaned up: {id(websocket)}")

    async def cleanup(self):
        """
        전체 서비스 정리
        """
        if self.stt_service:
            await self.stt_service.cleanup()
        if self.tts_service:
            await self.tts_service.cleanup()
        if self.llm_service:
            await self.llm_service.cleanup()
        if self.wav2lip_service:
            await self.wav2lip_service.cleanup()

        # 남은 임시 파일 정리
        if self.temp_files:
            await cleanup_temp_files(self.temp_files)
            self.temp_files.clear()
