"""
녹화 서비스
Room 기반 세션 녹화 기능
"""

import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, List
import json

logger = logging.getLogger(__name__)


@dataclass
class RecordingMetadata:
    """녹화 메타데이터"""
    recording_id: str
    room_id: str
    room_name: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    participants: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    file_path: Optional[str] = None
    file_size_bytes: int = 0

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "recording_id": self.recording_id,
            "room_id": self.room_id,
            "room_name": self.room_name,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "participants": self.participants,
            "duration_seconds": self.duration_seconds,
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
        }


@dataclass
class RecordingSession:
    """녹화 세션"""
    recording_id: str
    room_id: str
    metadata: RecordingMetadata
    audio_chunks: List[bytes] = field(default_factory=list)
    video_chunks: List[bytes] = field(default_factory=list)
    transcript: List[dict] = field(default_factory=list)
    is_active: bool = True


class RecordingService:
    """녹화 서비스 - Room 기반 세션 녹화"""

    def __init__(self, recordings_dir: str = "recordings"):
        """
        Args:
            recordings_dir: 녹화 파일 저장 디렉토리
        """
        self.recordings_dir = Path(recordings_dir)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)

        # 활성 녹화 세션
        self.active_sessions: Dict[str, RecordingSession] = {}

        # 완료된 녹화 메타데이터
        self.completed_recordings: Dict[str, RecordingMetadata] = {}

        logger.info(f"RecordingService initialized. Recordings dir: {self.recordings_dir}")

    def start_recording(self, room_id: str, room_name: str, participants: List[str]) -> RecordingMetadata:
        """
        녹화 시작

        Args:
            room_id: Room ID
            room_name: Room 이름
            participants: 참가자 리스트

        Returns:
            RecordingMetadata: 녹화 메타데이터
        """
        # 이미 녹화 중인 경우
        if room_id in self.active_sessions:
            logger.warning(f"Recording already in progress for room {room_id}")
            return self.active_sessions[room_id].metadata

        # 녹화 ID 생성
        recording_id = f"rec_{room_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 메타데이터 생성
        metadata = RecordingMetadata(
            recording_id=recording_id,
            room_id=room_id,
            room_name=room_name,
            started_at=datetime.now(),
            participants=participants.copy(),
        )

        # 세션 생성
        session = RecordingSession(
            recording_id=recording_id,
            room_id=room_id,
            metadata=metadata,
        )

        self.active_sessions[room_id] = session

        logger.info(f"Recording started: {recording_id} for room {room_id}")
        return metadata

    async def stop_recording(self, room_id: str) -> Optional[RecordingMetadata]:
        """
        녹화 중지 및 파일 저장

        Args:
            room_id: Room ID

        Returns:
            RecordingMetadata: 완료된 녹화 메타데이터
        """
        session = self.active_sessions.get(room_id)
        if not session:
            logger.warning(f"No active recording for room {room_id}")
            return None

        # 녹화 종료 처리
        session.is_active = False
        metadata = session.metadata
        metadata.ended_at = datetime.now()
        metadata.duration_seconds = (metadata.ended_at - metadata.started_at).total_seconds()

        # 파일 저장
        try:
            file_path = await self._save_recording(session)
            metadata.file_path = str(file_path)
            metadata.file_size_bytes = file_path.stat().st_size if file_path.exists() else 0

            # 메타데이터 JSON 저장
            metadata_path = file_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)

            logger.info(f"Recording saved: {file_path} ({metadata.file_size_bytes} bytes)")
        except Exception as e:
            logger.error(f"Failed to save recording for room {room_id}: {e}")
            metadata.file_path = None

        # 완료된 녹화로 이동
        self.completed_recordings[metadata.recording_id] = metadata
        del self.active_sessions[room_id]

        logger.info(f"Recording stopped: {metadata.recording_id}")
        return metadata

    def add_audio_chunk(self, room_id: str, audio_data: bytes):
        """
        오디오 청크 추가

        Args:
            room_id: Room ID
            audio_data: 오디오 데이터
        """
        session = self.active_sessions.get(room_id)
        if session and session.is_active:
            session.audio_chunks.append(audio_data)

    def add_video_chunk(self, room_id: str, video_data: bytes):
        """
        비디오 청크 추가

        Args:
            room_id: Room ID
            video_data: 비디오 데이터
        """
        session = self.active_sessions.get(room_id)
        if session and session.is_active:
            session.video_chunks.append(video_data)

    def add_transcript_entry(self, room_id: str, user_id: str, username: str, text: str, timestamp: Optional[datetime] = None):
        """
        대화 내용 추가

        Args:
            room_id: Room ID
            user_id: 사용자 ID
            username: 사용자 이름
            text: 대화 내용
            timestamp: 타임스탬프
        """
        session = self.active_sessions.get(room_id)
        if session and session.is_active:
            entry = {
                "timestamp": (timestamp or datetime.now()).isoformat(),
                "user_id": user_id,
                "username": username,
                "text": text,
            }
            session.transcript.append(entry)

    async def _save_recording(self, session: RecordingSession) -> Path:
        """
        녹화 데이터를 파일로 저장

        Args:
            session: 녹화 세션

        Returns:
            Path: 저장된 파일 경로
        """
        # 파일명 생성
        filename = f"{session.recording_id}.txt"
        file_path = self.recordings_dir / filename

        # 대화 내용을 텍스트 파일로 저장 (간단한 구현)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Recording: {session.recording_id}\n")
            f.write(f"Room: {session.metadata.room_name} ({session.metadata.room_id})\n")
            f.write(f"Started: {session.metadata.started_at}\n")
            f.write(f"Participants: {', '.join(session.metadata.participants)}\n")
            f.write("\n" + "="*80 + "\n")
            f.write("TRANSCRIPT\n")
            f.write("="*80 + "\n\n")

            for entry in session.transcript:
                f.write(f"[{entry['timestamp']}] {entry['username']}: {entry['text']}\n")

        # 실제 프로덕션에서는 오디오/비디오를 ffmpeg로 병합할 수 있음
        # 여기서는 간단한 구현으로 대화 내용만 저장

        return file_path

    def is_recording(self, room_id: str) -> bool:
        """
        녹화 중인지 확인

        Args:
            room_id: Room ID

        Returns:
            bool: 녹화 중이면 True
        """
        return room_id in self.active_sessions

    def get_recording_metadata(self, recording_id: str) -> Optional[RecordingMetadata]:
        """
        녹화 메타데이터 조회

        Args:
            recording_id: 녹화 ID

        Returns:
            RecordingMetadata: 메타데이터
        """
        return self.completed_recordings.get(recording_id)

    def list_recordings(self, room_id: Optional[str] = None) -> List[RecordingMetadata]:
        """
        녹화 목록 조회

        Args:
            room_id: Room ID (선택사항, 지정 시 해당 Room의 녹화만)

        Returns:
            List[RecordingMetadata]: 녹화 목록
        """
        recordings = list(self.completed_recordings.values())

        if room_id:
            recordings = [r for r in recordings if r.room_id == room_id]

        # 최신순 정렬
        recordings.sort(key=lambda r: r.started_at, reverse=True)

        return recordings

    async def delete_recording(self, recording_id: str) -> bool:
        """
        녹화 삭제

        Args:
            recording_id: 녹화 ID

        Returns:
            bool: 성공 여부
        """
        metadata = self.completed_recordings.get(recording_id)
        if not metadata:
            return False

        try:
            # 파일 삭제
            if metadata.file_path:
                file_path = Path(metadata.file_path)
                if file_path.exists():
                    file_path.unlink()

                # 메타데이터 JSON도 삭제
                metadata_path = file_path.with_suffix('.json')
                if metadata_path.exists():
                    metadata_path.unlink()

            # 메타데이터 제거
            del self.completed_recordings[recording_id]

            logger.info(f"Recording deleted: {recording_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete recording {recording_id}: {e}")
            return False


# 싱글톤 인스턴스
recording_service = RecordingService()
