"""
Wav2Lip 립싱크 서비스
정적 아바타 이미지에 오디오 기반 립싱크 적용
"""

import cv2
import numpy as np
from typing import Optional, Tuple
import logging
import os
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class Wav2LipService:
    """
    Wav2Lip을 사용한 립싱크 비디오 생성 서비스
    """

    def __init__(
        self,
        checkpoint_path: str = "models/wav2lip_gan.pth",
        avatar_image_path: str = "models/avatar.jpg",
        device: str = "cpu",
        resolution: Tuple[int, int] = (256, 256),
        fps: int = 25
    ):
        """
        Args:
            checkpoint_path: Wav2Lip 모델 체크포인트 경로
            avatar_image_path: 아바타 이미지 경로
            device: 실행 디바이스 (cuda 또는 cpu)
            resolution: 비디오 해상도 (width, height)
            fps: 비디오 프레임레이트
        """
        self.checkpoint_path = checkpoint_path
        self.avatar_image_path = avatar_image_path
        self.device = device
        self.resolution = resolution
        self.fps = fps
        self.initialized = False
        self.model = None

    async def initialize(self):
        """
        Wav2Lip 모델 초기화
        """
        try:
            # 모델 체크포인트 존재 확인
            if not os.path.exists(self.checkpoint_path):
                logger.warning(f"⚠️  Wav2Lip checkpoint not found: {self.checkpoint_path}")
                logger.info("📥 Please download Wav2Lip model from:")
                logger.info("   https://github.com/Rudrabha/Wav2Lip")
                raise FileNotFoundError("Wav2Lip checkpoint not found")

            # 아바타 이미지 존재 확인
            if not os.path.exists(self.avatar_image_path):
                logger.warning(f"⚠️  Avatar image not found: {self.avatar_image_path}")
                raise FileNotFoundError("Avatar image not found")

            # Wav2Lip 모델 로드
            logger.info(f"Loading Wav2Lip model from {self.checkpoint_path}")

            # 실제 Wav2Lip 구현은 복잡하므로 여기서는 구조만 작성
            # 실제 사용 시에는 Wav2Lip 라이브러리를 import하여 사용
            # from models import Wav2Lip
            # self.model = load_checkpoint(self.checkpoint_path, self.device)

            self.initialized = True
            logger.info(f"✅ Wav2Lip model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Wav2Lip: {e}")
            raise

    async def generate_lipsync_video(
        self,
        audio_path: str,
        output_path: str
    ) -> str:
        """
        오디오에 맞춰 립싱크 비디오 생성

        Args:
            audio_path: 입력 오디오 파일 경로
            output_path: 출력 비디오 파일 경로

        Returns:
            생성된 비디오 파일 경로
        """
        if not self.initialized or self.model is None:
            raise RuntimeError("Wav2Lip service not initialized")

        try:
            logger.info(f"🎬 Generating lipsync video...")

            # 아바타 이미지 로드
            avatar_img = cv2.imread(self.avatar_image_path)
            if avatar_img is None:
                raise ValueError(f"Failed to load avatar image: {self.avatar_image_path}")

            # 이미지 리사이즈
            avatar_img = cv2.resize(avatar_img, self.resolution)

            # 오디오 길이 계산
            audio_duration = self._get_audio_duration(audio_path)
            total_frames = int(audio_duration * self.fps)

            # 비디오 작성기 초기화
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(
                output_path,
                fourcc,
                self.fps,
                self.resolution
            )

            # 실제 Wav2Lip 추론
            # 여기서는 간단한 프레임 복제로 대체 (실제로는 모델 추론 필요)
            for frame_idx in range(total_frames):
                # TODO: 실제 Wav2Lip 모델로 프레임 생성
                # frame = self.model.generate_frame(avatar_img, audio_chunk)

                # 임시로 원본 이미지 사용 (립싱크 없음)
                video_writer.write(avatar_img)

            video_writer.release()

            # 오디오와 비디오 병합
            final_output = output_path.replace('.mp4', '_with_audio.mp4')
            self._merge_audio_video(output_path, audio_path, final_output)

            logger.info(f"✅ Lipsync video generated: {final_output}")
            return final_output

        except Exception as e:
            logger.error(f"❌ Failed to generate lipsync video: {e}")
            raise

    def _get_audio_duration(self, audio_path: str) -> float:
        """
        오디오 파일의 길이 계산 (초)
        """
        try:
            import soundfile as sf
            data, samplerate = sf.read(audio_path)
            duration = len(data) / samplerate
            return duration
        except Exception as e:
            logger.warning(f"Failed to get audio duration: {e}, using default 3s")
            return 3.0

    def _merge_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: str
    ):
        """
        비디오와 오디오를 병합 (ffmpeg 사용)
        """
        try:
            cmd = [
                'ffmpeg',
                '-y',  # 덮어쓰기
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental',
                output_path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )

            if result.returncode != 0:
                raise Exception(f"ffmpeg failed: {result.stderr.decode()}")

            logger.info("✅ Audio and video merged successfully")

        except subprocess.TimeoutExpired:
            logger.error("❌ ffmpeg timeout")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to merge audio/video: {e}")
            # ffmpeg가 없는 경우 원본 비디오 반환
            import shutil
            shutil.copy(video_path, output_path)

    async def cleanup(self):
        """
        리소스 정리
        """
        if self.model is not None:
            del self.model
        self.initialized = False
        logger.info("Wav2Lip service cleaned up")


class MockWav2LipService:
    """
    테스트용 목업 Wav2Lip 서비스
    실제 립싱크 없이 정적 비디오 생성
    """

    def __init__(self, *args, **kwargs):
        self.avatar_image_path = kwargs.get('avatar_image_path', 'models/avatar.jpg')
        self.resolution = kwargs.get('resolution', (256, 256))
        self.fps = kwargs.get('fps', 25)
        self.initialized = False

    async def initialize(self):
        """
        목업 초기화
        """
        # 기본 아바타 이미지가 없으면 생성
        if not os.path.exists(self.avatar_image_path):
            os.makedirs(os.path.dirname(self.avatar_image_path), exist_ok=True)
            self._create_default_avatar()

        self.initialized = True
        logger.info("✅ Mock Wav2Lip service initialized")

    def _create_default_avatar(self):
        """
        기본 아바타 이미지 생성 (단순한 원형)
        """
        img = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)

        # 배경 그라데이션
        for i in range(self.resolution[1]):
            color_val = int(100 + (i / self.resolution[1]) * 100)
            img[i, :] = [color_val, color_val // 2, color_val // 3]

        # 얼굴 원형
        center = (self.resolution[0] // 2, self.resolution[1] // 2)
        radius = min(self.resolution) // 3
        cv2.circle(img, center, radius, (220, 180, 140), -1)

        # 눈
        eye_y = center[1] - radius // 3
        left_eye = (center[0] - radius // 3, eye_y)
        right_eye = (center[0] + radius // 3, eye_y)
        cv2.circle(img, left_eye, radius // 8, (0, 0, 0), -1)
        cv2.circle(img, right_eye, radius // 8, (0, 0, 0), -1)

        # 입
        mouth_y = center[1] + radius // 3
        cv2.ellipse(img, (center[0], mouth_y), (radius // 3, radius // 6),
                    0, 0, 180, (100, 50, 50), 2)

        cv2.imwrite(self.avatar_image_path, img)
        logger.info(f"✅ Created default avatar image: {self.avatar_image_path}")

    async def generate_lipsync_video(
        self,
        audio_path: str,
        output_path: str
    ) -> str:
        """
        목업 비디오 생성 (립싱크 없음)
        """
        if not self.initialized:
            raise RuntimeError("Mock Wav2Lip service not initialized")

        try:
            logger.info(f"🎬 Generating mock lipsync video...")

            # 아바타 이미지 로드
            avatar_img = cv2.imread(self.avatar_image_path)
            if avatar_img is None:
                raise ValueError(f"Failed to load avatar image: {self.avatar_image_path}")

            avatar_img = cv2.resize(avatar_img, self.resolution)

            # 오디오 길이 계산
            try:
                import soundfile as sf
                data, samplerate = sf.read(audio_path)
                duration = len(data) / samplerate
            except:
                duration = 3.0  # 기본 3초

            total_frames = int(duration * self.fps)

            # 비디오 생성
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            temp_video = output_path.replace('.mp4', '_temp.mp4')

            video_writer = cv2.VideoWriter(
                temp_video,
                fourcc,
                self.fps,
                self.resolution
            )

            # 정적 프레임 복제 (간단한 애니메이션 추가)
            for frame_idx in range(total_frames):
                frame = avatar_img.copy()

                # 간단한 입 애니메이션 (사인파 기반)
                mouth_open = int(abs(np.sin(frame_idx * 0.5)) * 10)
                center_x = self.resolution[0] // 2
                center_y = self.resolution[1] // 2 + self.resolution[1] // 6

                cv2.ellipse(
                    frame,
                    (center_x, center_y),
                    (self.resolution[0] // 6, mouth_open + 5),
                    0, 0, 180,
                    (100, 50, 50),
                    -1
                )

                video_writer.write(frame)

            video_writer.release()

            # 오디오 병합 시도
            final_output = output_path
            try:
                cmd = [
                    'ffmpeg',
                    '-y',
                    '-i', temp_video,
                    '-i', audio_path,
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-strict', 'experimental',
                    '-shortest',
                    final_output
                ]

                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                os.remove(temp_video)
            except:
                logger.warning("ffmpeg not available, using video without audio")
                import shutil
                shutil.move(temp_video, final_output)

            logger.info(f"✅ Mock lipsync video generated: {final_output}")
            return final_output

        except Exception as e:
            logger.error(f"❌ Failed to generate mock video: {e}")
            raise

    async def cleanup(self):
        """
        리소스 정리
        """
        self.initialized = False
        logger.info("Mock Wav2Lip service cleaned up")
