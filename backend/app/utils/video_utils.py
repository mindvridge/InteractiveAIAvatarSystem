"""
비디오 스트리밍 및 처리 유틸리티
"""

import base64
import os
import asyncio
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)


async def stream_video_file(video_path: str, chunk_size: int = 65536) -> AsyncGenerator[bytes, None]:
    """
    비디오 파일을 청크 단위로 스트리밍

    Args:
        video_path: 비디오 파일 경로
        chunk_size: 청크 크기 (바이트)

    Yields:
        비디오 데이터 청크
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    try:
        with open(video_path, 'rb') as video_file:
            while True:
                chunk = video_file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
                # 너무 빠른 전송 방지 (스트리밍 시뮬레이션)
                await asyncio.sleep(0.01)

        logger.info(f"✅ Video streaming completed: {video_path}")

    except Exception as e:
        logger.error(f"❌ Error streaming video: {e}")
        raise


def video_to_base64(video_path: str) -> str:
    """
    비디오 파일을 base64 문자열로 변환

    Args:
        video_path: 비디오 파일 경로

    Returns:
        base64 인코딩된 비디오 데이터
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    try:
        with open(video_path, 'rb') as video_file:
            video_bytes = video_file.read()
            video_base64 = base64.b64encode(video_bytes).decode('utf-8')
            logger.info(f"✅ Video encoded to base64: {len(video_base64)} chars")
            return video_base64

    except Exception as e:
        logger.error(f"❌ Error encoding video to base64: {e}")
        raise


def get_video_info(video_path: str) -> dict:
    """
    비디오 파일의 정보 가져오기

    Args:
        video_path: 비디오 파일 경로

    Returns:
        비디오 정보 딕셔너리
    """
    try:
        import cv2

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")

        info = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
            'size_bytes': os.path.getsize(video_path)
        }

        cap.release()
        return info

    except Exception as e:
        logger.error(f"❌ Error getting video info: {e}")
        return {}


async def cleanup_temp_files(file_paths: list[str]):
    """
    임시 파일 정리

    Args:
        file_paths: 삭제할 파일 경로 리스트
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️  Cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {e}")
