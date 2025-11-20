"""
FastAPI 메인 애플리케이션
실시간 대화형 AI 아바타 시스템의 백엔드 서버
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any
import asyncio

from app.websocket.handler import WebSocketHandler
from app.services.config import get_settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 설정 로드
settings = get_settings()

# WebSocket 핸들러 인스턴스
ws_handler = WebSocketHandler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리
    시작 시 AI 모델 로딩, 종료 시 리소스 정리
    """
    logger.info("🚀 Starting Interactive AI Avatar System...")

    # AI 서비스 초기화
    try:
        await ws_handler.initialize_services()
        logger.info("✅ All AI services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize AI services: {e}")
        logger.warning("⚠️  Running in fallback mode with mock services")

    yield

    # 종료 시 리소스 정리
    logger.info("🛑 Shutting down...")
    await ws_handler.cleanup()
    logger.info("✅ Cleanup completed")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Interactive AI Avatar System",
    description="실시간 대화형 AI 아바타 시스템 API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 설정 - 프론트엔드에서 접근 가능하도록
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, Any]:
    """
    루트 엔드포인트 - 서버 상태 확인
    """
    return {
        "message": "Interactive AI Avatar System API",
        "version": "0.2.0",  # Phase 2
        "status": "running",
        "phase": "2",
        "services": {
            "stt": ws_handler.stt_service is not None,
            "tts": ws_handler.tts_service is not None,
            "llm": ws_handler.llm_service is not None,
            "wav2lip": ws_handler.wav2lip_service is not None,  # Phase 2
        }
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    헬스 체크 엔드포인트
    """
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 엔드포인트 - 실시간 양방향 통신

    클라이언트와 서버 간 실시간 오디오 스트리밍 및 대화 처리
    """
    await websocket.accept()
    logger.info(f"🔌 New WebSocket connection from {websocket.client}")

    try:
        await ws_handler.handle_connection(websocket)
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
    finally:
        await ws_handler.cleanup_connection(websocket)
        logger.info(f"🔌 WebSocket connection closed: {websocket.client}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    전역 예외 핸들러
    """
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
