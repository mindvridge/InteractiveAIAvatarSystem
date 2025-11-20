"""
Room 관리 서비스
다중 사용자 지원을 위한 Room 기반 시스템
"""

from typing import Dict, Set, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
import asyncio
import logging
import uuid
from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class User:
    """사용자 정보"""
    user_id: str
    username: str
    websocket: WebSocket
    joined_at: datetime = field(default_factory=datetime.now)
    is_speaking: bool = False


@dataclass
class Room:
    """대화방 정보"""
    room_id: str
    room_name: str
    max_users: int = 10
    created_at: datetime = field(default_factory=datetime.now)
    users: Dict[str, User] = field(default_factory=dict)
    is_recording: bool = False

    def get_user_count(self) -> int:
        """현재 사용자 수"""
        return len(self.users)

    def is_full(self) -> bool:
        """방이 가득 찼는지 확인"""
        return self.get_user_count() >= self.max_users

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (WebSocket 제외)"""
        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "max_users": self.max_users,
            "current_users": self.get_user_count(),
            "created_at": self.created_at.isoformat(),
            "is_recording": self.is_recording,
            "users": [
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "joined_at": user.joined_at.isoformat(),
                    "is_speaking": user.is_speaking,
                }
                for user in self.users.values()
            ],
        }


class RoomService:
    """
    Room 관리 서비스
    다중 사용자 대화방 관리
    """

    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.user_to_room: Dict[str, str] = {}  # user_id -> room_id

    def create_room(
        self,
        room_name: str,
        max_users: int = 10
    ) -> Room:
        """
        새로운 방 생성

        Args:
            room_name: 방 이름
            max_users: 최대 사용자 수

        Returns:
            생성된 Room 객체
        """
        room_id = str(uuid.uuid4())
        room = Room(
            room_id=room_id,
            room_name=room_name,
            max_users=max_users
        )

        self.rooms[room_id] = room
        logger.info(f"🏠 Room created: {room_name} ({room_id})")

        return room

    def get_room(self, room_id: str) -> Optional[Room]:
        """
        Room 조회

        Args:
            room_id: Room ID

        Returns:
            Room 객체 또는 None
        """
        return self.rooms.get(room_id)

    def get_all_rooms(self) -> List[dict]:
        """
        모든 방 목록 조회

        Returns:
            Room 정보 리스트
        """
        return [room.to_dict() for room in self.rooms.values()]

    def delete_room(self, room_id: str) -> bool:
        """
        방 삭제

        Args:
            room_id: Room ID

        Returns:
            삭제 성공 여부
        """
        if room_id in self.rooms:
            room = self.rooms[room_id]

            # 모든 사용자 제거
            for user_id in list(room.users.keys()):
                self.leave_room(user_id)

            del self.rooms[room_id]
            logger.info(f"🗑️  Room deleted: {room_id}")
            return True

        return False

    async def join_room(
        self,
        room_id: str,
        user_id: str,
        username: str,
        websocket: WebSocket
    ) -> bool:
        """
        방에 참여

        Args:
            room_id: Room ID
            user_id: User ID
            username: 사용자 이름
            websocket: WebSocket 연결

        Returns:
            참여 성공 여부
        """
        room = self.get_room(room_id)

        if not room:
            logger.error(f"Room not found: {room_id}")
            return False

        if room.is_full():
            logger.warning(f"Room is full: {room_id}")
            return False

        # 사용자 생성
        user = User(
            user_id=user_id,
            username=username,
            websocket=websocket
        )

        # 방에 추가
        room.users[user_id] = user
        self.user_to_room[user_id] = room_id

        logger.info(f"👤 User joined room: {username} → {room.room_name}")

        # 다른 사용자들에게 알림
        await self.broadcast_to_room(
            room_id,
            {
                "type": "user_joined",
                "data": {
                    "user_id": user_id,
                    "username": username,
                    "room": room.to_dict(),
                }
            },
            exclude_user=user_id
        )

        return True

    def leave_room(self, user_id: str) -> bool:
        """
        방에서 나가기

        Args:
            user_id: User ID

        Returns:
            나가기 성공 여부
        """
        room_id = self.user_to_room.get(user_id)

        if not room_id:
            return False

        room = self.get_room(room_id)

        if not room or user_id not in room.users:
            return False

        username = room.users[user_id].username

        # 사용자 제거
        del room.users[user_id]
        del self.user_to_room[user_id]

        logger.info(f"👋 User left room: {username}")

        # 빈 방 자동 삭제
        if room.get_user_count() == 0:
            self.delete_room(room_id)

        return True

    async def broadcast_to_room(
        self,
        room_id: str,
        message: dict,
        exclude_user: Optional[str] = None
    ):
        """
        방의 모든 사용자에게 메시지 브로드캐스트

        Args:
            room_id: Room ID
            message: 전송할 메시지
            exclude_user: 제외할 사용자 ID (선택)
        """
        room = self.get_room(room_id)

        if not room:
            return

        # 모든 사용자에게 전송
        tasks = []
        for user_id, user in room.users.items():
            if exclude_user and user_id == exclude_user:
                continue

            tasks.append(self._send_to_user(user.websocket, message))

        # 병렬 전송
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_to_user(self, websocket: WebSocket, message: dict):
        """
        특정 사용자에게 메시지 전송

        Args:
            websocket: WebSocket 연결
            message: 전송할 메시지
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def get_user_room(self, user_id: str) -> Optional[Room]:
        """
        사용자가 속한 방 조회

        Args:
            user_id: User ID

        Returns:
            Room 객체 또는 None
        """
        room_id = self.user_to_room.get(user_id)

        if room_id:
            return self.get_room(room_id)

        return None

    def set_user_speaking(self, user_id: str, is_speaking: bool):
        """
        사용자 발화 상태 설정

        Args:
            user_id: User ID
            is_speaking: 발화 중 여부
        """
        room = self.get_user_room(user_id)

        if room and user_id in room.users:
            room.users[user_id].is_speaking = is_speaking
            logger.debug(f"User speaking status: {user_id} = {is_speaking}")

    def get_room_stats(self) -> dict:
        """
        전체 통계 조회

        Returns:
            통계 정보
        """
        total_users = len(self.user_to_room)

        return {
            "total_rooms": len(self.rooms),
            "total_users": total_users,
            "rooms": self.get_all_rooms(),
        }


# 싱글톤 인스턴스
room_service = RoomService()
