# Phase 2: 립싱크 아바타 설정 가이드

Phase 2에서는 Wav2Lip 모델을 사용하여 정적 아바타 이미지에 립싱크를 적용한 비디오를 생성합니다.

## 🎬 Phase 2 기능

- ✅ 정적 아바타 이미지에서 립싱크 비디오 생성
- ✅ 오디오와 비디오 자동 동기화
- ✅ 실시간 비디오 스트리밍
- ✅ Mock 서비스로 모델 없이 테스트 가능

## 📋 사전 요구사항

### 1. FFmpeg 설치 (필수)

비디오와 오디오 병합을 위해 FFmpeg가 필요합니다.

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
- https://ffmpeg.org/download.html 에서 다운로드
- 시스템 PATH에 추가

### 2. Python 의존성 확인

```bash
cd backend
pip install opencv-python numpy scipy soundfile
```

## 🎯 빠른 시작 (Mock 모드)

Mock 서비스를 사용하면 Wav2Lip 모델 없이 바로 테스트할 수 있습니다!

1. **Backend 실행**
```bash
cd backend
uvicorn app.main:app --reload
```

Mock Wav2Lip 서비스가 자동으로 활성화됩니다.

2. **Frontend 실행**
```bash
cd frontend
npm run dev
```

3. **테스트**
- http://localhost:3000 접속
- 텍스트 또는 음성으로 대화
- 간단한 애니메이션이 적용된 비디오가 생성됩니다

Mock 모드에서는:
- 기본 아바타 이미지 자동 생성
- 간단한 입 애니메이션 적용
- 실제 립싱크 없이 비디오 생성

## 🚀 실제 Wav2Lip 모델 사용 (선택사항)

더 정확한 립싱크를 원한다면 실제 Wav2Lip 모델을 사용할 수 있습니다.

### 1. Wav2Lip 모델 다운로드

```bash
cd models

# Wav2Lip GAN 모델 다운로드 (권장)
wget "https://iiitaphyd-my.sharepoint.com/:u:/g/personal/radrabha_m_research_iiit_ac_in/Eb3LEzbfuKlJiR600lQWRxgBIY27JZg80f7V9jtMfbNDaQ?download=1" -O wav2lip_gan.pth

# 또는 GitHub에서 직접 클론
git clone https://github.com/Rudrabha/Wav2Lip.git
cp Wav2Lip/checkpoints/wav2lip_gan.pth ./
```

### 2. 아바타 이미지 준비

`models/avatar.jpg` 파일에 아바타 이미지를 배치하세요.

**권장 사항:**
- **해상도**: 256x256 이상
- **형식**: JPG 또는 PNG
- **얼굴**: 정면을 바라보는 클리어한 얼굴 사진
- **배경**: 단순한 배경 권장

**예시:**
```bash
# 샘플 이미지 다운로드
curl -o models/avatar.jpg https://example.com/your-avatar.jpg
```

### 3. Backend 환경 변수 설정

`backend/.env` 파일 수정:

```env
# Wav2Lip 모델 경로
WAV2LIP_CHECKPOINT=models/wav2lip_gan.pth
AVATAR_IMAGE_PATH=models/avatar.jpg

# 비디오 설정
VIDEO_FPS=25
VIDEO_RESOLUTION=256,256

# GPU 사용 (선택사항)
DEVICE=cuda  # GPU 사용 시
# DEVICE=cpu  # CPU만 사용 시
```

### 4. Wav2Lip 라이브러리 설치 (고급)

실제 Wav2Lip 추론을 위해서는 추가 라이브러리가 필요합니다:

```bash
cd backend

# Wav2Lip 의존성
pip install torch torchvision torchaudio
pip install face-alignment
pip install librosa
```

**참고**: Wav2Lip의 실제 구현은 복잡하므로, 현재 구조는 Mock 서비스를 기본으로 사용합니다.

## 📊 성능 최적화

### CPU 최적화

```env
DEVICE=cpu
VIDEO_RESOLUTION=256,256  # 낮은 해상도
VIDEO_FPS=15              # 낮은 프레임레이트
```

### GPU 최적화

```env
DEVICE=cuda
VIDEO_RESOLUTION=512,512  # 높은 해상도
VIDEO_FPS=30              # 높은 프레임레이트
```

## 🎨 아바타 이미지 커스터마이즈

### 방법 1: 직접 이미지 배치

```bash
cp your-avatar-image.jpg models/avatar.jpg
```

### 방법 2: 환경 변수로 경로 지정

```env
AVATAR_IMAGE_PATH=/path/to/your/avatar.jpg
```

### 방법 3: 런타임 설정 (향후 기능)

Frontend에서 아바타 선택 기능 예정

## 📝 테스트 방법

### 1. Backend 상태 확인

```bash
curl http://localhost:8000/

# 응답 예시:
{
  "message": "Interactive AI Avatar System API",
  "version": "0.1.0",
  "status": "running",
  "services": {
    "stt": true,
    "tts": true,
    "llm": true,
    "wav2lip": true  // Phase 2 추가
  }
}
```

### 2. Frontend에서 테스트

1. http://localhost:3000 접속
2. 채팅창에 메시지 입력
3. 처리 과정 확인:
   - STT (음성 입력 시)
   - LLM 응답 생성
   - TTS 음성 합성
   - **Lipsync 비디오 생성** ⬅️ Phase 2
4. 립싱크 비디오 자동 재생

## 🐛 문제 해결

### "FFmpeg not found" 오류

```bash
# FFmpeg 설치 확인
ffmpeg -version

# 없으면 설치 (위 FFmpeg 설치 섹션 참조)
```

### "Wav2Lip checkpoint not found" 경고

- Mock 서비스로 자동 전환됩니다
- 실제 모델을 사용하려면 위의 "Wav2Lip 모델 다운로드" 섹션 참조

### "Avatar image not found" 오류

Mock 서비스가 자동으로 기본 아바타 이미지를 생성합니다.

### 비디오 생성이 느림

CPU 모드에서는 비디오 생성에 시간이 걸릴 수 있습니다:

- 해상도 낮추기: `VIDEO_RESOLUTION=128,128`
- FPS 낮추기: `VIDEO_FPS=15`
- GPU 사용 (가능한 경우)

### 비디오가 재생되지 않음

브라우저 콘솔 확인:

```javascript
// Chrome DevTools > Console
// 비디오 재생 오류 확인
```

브라우저가 MP4 코덱을 지원하지 않을 수 있습니다:
- Chrome/Edge: 지원
- Firefox: 지원
- Safari: 지원

## 📚 다음 단계

Phase 2 완료 후:

- ✅ Phase 1: 기본 음성 대화 시스템
- ✅ Phase 2: 립싱크 아바타
- 🚧 **Phase 3: WebRTC 실시간 최적화** (예정)
  - 청크 단위 스트리밍
  - 레이턴시 < 2초 목표
  - 다중 아바타 지원

## 💡 팁

1. **빠른 테스트**: Mock 모드로 먼저 전체 플로우 테스트
2. **점진적 개선**: 기본 설정 → 아바타 이미지 → 실제 Wav2Lip 순으로 진행
3. **성능 모니터링**: Backend 로그에서 처리 시간 확인
4. **브라우저 캐시**: 아바타 이미지 변경 시 브라우저 캐시 비우기

## 🤝 기여

Phase 2 개선 사항:

- [ ] 실제 Wav2Lip 모델 완전 통합
- [ ] 여러 아바타 지원
- [ ] 실시간 비디오 스트리밍 최적화
- [ ] 해상도 업스케일링
- [ ] 배경 제거

Pull Request를 환영합니다!

---

**Phase 2 완료 체크리스트:**

- [x] Wav2Lip 서비스 구현
- [x] Mock 서비스 폴백
- [x] 비디오 스트리밍 파이프라인
- [x] Frontend 비디오 플레이어
- [x] 오디오-비디오 동기화
- [x] 문서 작성

**Made with ❤️ for Interactive AI Avatar System - Phase 2**
