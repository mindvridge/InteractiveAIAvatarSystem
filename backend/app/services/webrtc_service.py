"""
WebRTC Signaling 서비스
실시간 P2P 통신을 위한 시그널링 서버
"""

from typing import Dict, Optional, Set
import asyncio
import logging
import json
from dataclasses import dataclass, asdict
from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class ICECandidate:
    """ICE 후보자 정보"""
    candidate: str
    sdpMid: Optional[str] = None
    sdpMLineIndex: Optional[int] = None


@dataclass
class SessionDescription:
    """SDP (Session Description Protocol) 정보"""
    type: str  # "offer" or "answer"
    sdp: str


class WebRTCSignalingService:
    """
    WebRTC Signaling 서비스
    클라이언트 간 연결 설정을 중재
    """

    def __init__(self):
        self.peers: Dict[str, WebSocket] = {}  # peer_id -> websocket
        self.ice_candidates: Dict[str, list] = {}  # peer_id -> [candidates]
        self.sessions: Dict[str, SessionDescription] = {}  # peer_id -> SDP
        self.connections: Set[str] = set()  # 활성 연결 추적

    async def register_peer(self, peer_id: str, websocket: WebSocket) -> bool:
        """
        피어 등록

        Args:
            peer_id: 피어 식별자
            websocket: WebSocket 연결

        Returns:
            등록 성공 여부
        """
        if peer_id in self.peers:
            logger.warning(f"Peer {peer_id} already registered")
            return False

        self.peers[peer_id] = websocket
        self.ice_candidates[peer_id] = []
        self.connections.add(peer_id)

        logger.info(f"✅ Peer registered: {peer_id}")
        return True

    async def unregister_peer(self, peer_id: str):
        """
        피어 등록 해제

        Args:
            peer_id: 피어 식별자
        """
        if peer_id in self.peers:
            del self.peers[peer_id]

        if peer_id in self.ice_candidates:
            del self.ice_candidates[peer_id]

        if peer_id in self.sessions:
            del self.sessions[peer_id]

        self.connections.discard(peer_id)

        logger.info(f"🔌 Peer unregistered: {peer_id}")

    async def handle_offer(
        self,
        peer_id: str,
        offer: SessionDescription
    ) -> Optional[SessionDescription]:
        """
        Offer 처리 및 Answer 생성

        Args:
            peer_id: 피어 식별자
            offer: SDP Offer

        Returns:
            SDP Answer (서버에서 생성)
        """
        if peer_id not in self.peers:
            logger.error(f"Peer {peer_id} not found")
            return None

        # Offer 저장
        self.sessions[peer_id] = offer
        logger.info(f"📥 Received offer from {peer_id}")

        # Answer 생성 (간단한 예시 - 실제로는 aiortc 사용)
        answer = SessionDescription(
            type="answer",
            sdp=offer.sdp  # 실제로는 서버 SDP 생성 필요
        )

        logger.info(f"📤 Sending answer to {peer_id}")
        return answer

    async def handle_answer(self, peer_id: str, answer: SessionDescription):
        """
        Answer 처리

        Args:
            peer_id: 피어 식별자
            answer: SDP Answer
        """
        if peer_id not in self.peers:
            logger.error(f"Peer {peer_id} not found")
            return

        self.sessions[peer_id] = answer
        logger.info(f"📥 Received answer from {peer_id}")

    async def add_ice_candidate(
        self,
        peer_id: str,
        candidate: ICECandidate
    ):
        """
        ICE 후보자 추가

        Args:
            peer_id: 피어 식별자
            candidate: ICE 후보자 정보
        """
        if peer_id not in self.ice_candidates:
            self.ice_candidates[peer_id] = []

        self.ice_candidates[peer_id].append(candidate)
        logger.info(f"🧊 ICE candidate added for {peer_id}")

    async def get_ice_candidates(self, peer_id: str) -> list:
        """
        피어의 ICE 후보자 목록 반환

        Args:
            peer_id: 피어 식별자

        Returns:
            ICE 후보자 리스트
        """
        return self.ice_candidates.get(peer_id, [])

    def get_active_peers(self) -> Set[str]:
        """
        활성 피어 목록 반환

        Returns:
            활성 피어 ID 세트
        """
        return self.connections.copy()

    async def broadcast_to_peer(
        self,
        peer_id: str,
        message: dict
    ):
        """
        특정 피어에게 메시지 전송

        Args:
            peer_id: 피어 식별자
            message: 전송할 메시지
        """
        if peer_id not in self.peers:
            logger.warning(f"Peer {peer_id} not found for broadcast")
            return

        try:
            websocket = self.peers[peer_id]
            await websocket.send_json(message)
            logger.debug(f"📤 Message sent to {peer_id}: {message['type']}")
        except Exception as e:
            logger.error(f"❌ Failed to send message to {peer_id}: {e}")


class StreamingChunkProcessor:
    """
    청크 단위 스트리밍 처리기
    실시간 오디오/비디오 청크 처리
    """

    def __init__(self, chunk_size: int = 4096):
        """
        Args:
            chunk_size: 청크 크기 (바이트)
        """
        self.chunk_size = chunk_size
        self.active_streams: Dict[str, asyncio.Queue] = {}

    async def create_stream(self, stream_id: str) -> asyncio.Queue:
        """
        스트림 생성

        Args:
            stream_id: 스트림 식별자

        Returns:
            스트림 큐
        """
        if stream_id in self.active_streams:
            logger.warning(f"Stream {stream_id} already exists")
            return self.active_streams[stream_id]

        queue = asyncio.Queue()
        self.active_streams[stream_id] = queue
        logger.info(f"📺 Stream created: {stream_id}")
        return queue

    async def add_chunk(self, stream_id: str, chunk: bytes):
        """
        스트림에 청크 추가

        Args:
            stream_id: 스트림 식별자
            chunk: 데이터 청크
        """
        if stream_id not in self.active_streams:
            await self.create_stream(stream_id)

        await self.active_streams[stream_id].put(chunk)
        logger.debug(f"➕ Chunk added to stream {stream_id}: {len(chunk)} bytes")

    async def get_chunk(self, stream_id: str, timeout: float = 1.0) -> Optional[bytes]:
        """
        스트림에서 청크 가져오기

        Args:
            stream_id: 스트림 식별자
            timeout: 타임아웃 (초)

        Returns:
            데이터 청크 또는 None
        """
        if stream_id not in self.active_streams:
            return None

        try:
            chunk = await asyncio.wait_for(
                self.active_streams[stream_id].get(),
                timeout=timeout
            )
            return chunk
        except asyncio.TimeoutError:
            return None

    async def close_stream(self, stream_id: str):
        """
        스트림 종료

        Args:
            stream_id: 스트림 식별자
        """
        if stream_id in self.active_streams:
            # 남은 데이터 정리
            while not self.active_streams[stream_id].empty():
                try:
                    self.active_streams[stream_id].get_nowait()
                except asyncio.QueueEmpty:
                    break

            del self.active_streams[stream_id]
            logger.info(f"🔌 Stream closed: {stream_id}")

    def get_active_streams(self) -> Set[str]:
        """
        활성 스트림 목록 반환

        Returns:
            활성 스트림 ID 세트
        """
        return set(self.active_streams.keys())


# 싱글톤 인스턴스
signaling_service = WebRTCSignalingService()
chunk_processor = StreamingChunkProcessor()
