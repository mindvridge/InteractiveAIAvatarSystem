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
from app.services.webrtc_service import signaling_service
from app.services.room_service import room_service

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
        "version": "0.3.0",  # Phase 3
        "status": "running",
        "phase": "3",
        "features": ["WebSocket", "WebRTC", "Lipsync"],
        "services": {
            "stt": ws_handler.stt_service is not None,
            "tts": ws_handler.tts_service is not None,
            "llm": ws_handler.llm_service is not None,
            "wav2lip": ws_handler.wav2lip_service is not None,
            "webrtc": True,  # Phase 3
        }
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    헬스 체크 엔드포인트
    """
    return {"status": "healthy"}


# Room 관리 API
@app.get("/rooms")
async def get_rooms():
    """
    모든 대화방 목록 조회
    """
    return {
        "rooms": room_service.get_all_rooms(),
        "stats": room_service.get_room_stats()
    }


@app.post("/rooms")
async def create_room(room_name: str, max_users: int = 10):
    """
    새로운 대화방 생성
    """
    room = room_service.create_room(room_name, max_users)
    return {"room": room.to_dict()}


@app.get("/rooms/{room_id}")
async def get_room(room_id: str):
    """
    특정 대화방 정보 조회
    """
    room = room_service.get_room(room_id)

    if not room:
        return JSONResponse(
            status_code=404,
            content={"error": "Room not found"}
        )

    return {"room": room.to_dict()}


@app.delete("/rooms/{room_id}")
async def delete_room(room_id: str):
    """
    대화방 삭제
    """
    success = room_service.delete_room(room_id)

    if not success:
        return JSONResponse(
            status_code=404,
            content={"error": "Room not found"}
        )

    return {"message": "Room deleted successfully"}


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


@app.websocket("/webrtc")
async def webrtc_signaling_endpoint(websocket: WebSocket):
    """
    WebRTC Signaling 엔드포인트 - Phase 3

    P2P 연결 설정을 위한 시그널링 서버
    """
    await websocket.accept()
    peer_id = str(id(websocket))
    logger.info(f"🎥 New WebRTC signaling connection: {peer_id}")

    # 피어 등록
    await signaling_service.register_peer(peer_id, websocket)

    try:
        while True:
            # 시그널링 메시지 수신
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "offer":
                # SDP Offer 처리
                offer = data.get("offer")
                answer = await signaling_service.handle_offer(peer_id, offer)
                if answer:
                    await websocket.send_json({
                        "type": "answer",
                        "answer": answer
                    })

            elif message_type == "answer":
                # SDP Answer 처리
                answer = data.get("answer")
                await signaling_service.handle_answer(peer_id, answer)

            elif message_type == "ice_candidate":
                # ICE 후보자 처리
                candidate = data.get("candidate")
                await signaling_service.add_ice_candidate(peer_id, candidate)

            elif message_type == "get_peers":
                # 활성 피어 목록 요청
                peers = signaling_service.get_active_peers()
                await websocket.send_json({
                    "type": "peers",
                    "peers": list(peers)
                })

            else:
                logger.warning(f"Unknown WebRTC message type: {message_type}")

    except WebSocketDisconnect:
        logger.info(f"🎥 WebRTC signaling disconnected: {peer_id}")
    except Exception as e:
        logger.error(f"❌ WebRTC signaling error: {e}", exc_info=True)
    finally:
        await signaling_service.unregister_peer(peer_id)
        logger.info(f"🎥 WebRTC signaling closed: {peer_id}")


@app.websocket("/rooms/{room_id}/ws")
async def room_websocket_endpoint(websocket: WebSocket, room_id: str):
    """
    Room WebSocket 엔드포인트 - 다중 사용자 지원

    특정 방에 참여하여 실시간 대화
    """
    await websocket.accept()
    user_id = str(id(websocket))

    # 사용자 이름 요청
    try:
        init_data = await websocket.receive_json()
        username = init_data.get("username", f"User_{user_id[:8]}")
    except:
        username = f"User_{user_id[:8]}"

    logger.info(f"🏠 User {username} attempting to join room {room_id}")

    # 방에 참여
    success = await room_service.join_room(room_id, user_id, username, websocket)

    if not success:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "Failed to join room"}
        })
        await websocket.close()
        return

    # 참여 성공 알림
    room = room_service.get_room(room_id)
    await websocket.send_json({
        "type": "room_joined",
        "data": {"room": room.to_dict() if room else None}
    })

    try:
        # 메시지 수신 루프
        while True:
            data = await websocket.receive()

            if "text" in data:
                # 텍스트 메시지 처리
                message = await asyncio.to_thread(lambda: __import__('json').loads(data["text"]))
                message_type = message.get("type")

                if message_type == "speaking_status":
                    # 발화 상태 업데이트
                    is_speaking = message.get("is_speaking", False)
                    room_service.set_user_speaking(user_id, is_speaking)

                    # 다른 사용자들에게 브로드캐스트
                    await room_service.broadcast_to_room(
                        room_id,
                        {
                            "type": "user_speaking",
                            "data": {
                                "user_id": user_id,
                                "username": username,
                                "is_speaking": is_speaking
                            }
                        },
                        exclude_user=user_id
                    )

                elif message_type == "chat_message":
                    # 채팅 메시지 브로드캐스트
                    await room_service.broadcast_to_room(
                        room_id,
                        {
                            "type": "chat_message",
                            "data": {
                                "user_id": user_id,
                                "username": username,
                                "message": message.get("message", "")
                            }
                        }
                    )

                # 기존 WebSocket 핸들러로 처리
                elif message_type in ["text_input", "config", "ping"]:
                    # 개별 사용자 처리
                    await ws_handler.handle_text_message(websocket, data["text"])

            elif "bytes" in data:
                # 오디오 데이터는 개별 처리
                await ws_handler.handle_audio_message(websocket, data["bytes"])

    except WebSocketDisconnect:
        logger.info(f"🏠 User {username} disconnected from room {room_id}")
    except Exception as e:
        logger.error(f"❌ Room WebSocket error: {e}", exc_info=True)
    finally:
        # 방에서 나가기
        room_service.leave_room(user_id)

        # 다른 사용자들에게 알림
        await room_service.broadcast_to_room(
            room_id,
            {
                "type": "user_left",
                "data": {
                    "user_id": user_id,
                    "username": username
                }
            }
        )

        logger.info(f"🏠 User {username} left room {room_id}")


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
