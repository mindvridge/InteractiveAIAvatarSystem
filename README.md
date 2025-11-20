# Interactive AI Avatar System

실시간 대화형 AI 아바타 시스템 - HeyGen과 유사한 프로토타입

## 📋 프로젝트 개요

사용자가 음성이나 텍스트로 대화하면, AI 아바타가 실시간으로 립싱크와 함께 응답하는 시스템입니다.

### 주요 기능

- 🎤 **음성 입력**: 실시간 음성 녹음 및 STT (Speech-to-Text)
- 💬 **텍스트 채팅**: 텍스트 기반 대화 지원
- 🤖 **AI 대화**: Ollama 또는 OpenAI를 사용한 지능형 응답
- 🔊 **음성 합성**: TTS (Text-to-Speech)를 통한 자연스러운 음성 출력
- 📡 **실시간 통신**: WebSocket 기반 양방향 통신

### 기술 스택

**Backend:**
- FastAPI (Python 3.10+)
- WebSocket (실시간 통신)
- OpenAI Whisper (STT)
- Coqui TTS (음성 합성)
- Ollama / OpenAI API (LLM)

**Frontend:**
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- Zustand (상태 관리)
- WebRTC API

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.10 이상
- Node.js 20 이상
- Docker & Docker Compose (선택사항)
- FFmpeg (오디오 처리)

### 설치 방법

#### 방법 1: Docker Compose (권장)

1. **프로젝트 클론**
```bash
git clone <repository-url>
cd InteractiveAIAvatarSystem
```

2. **환경 변수 설정**
```bash
# Backend 환경 변수
cp backend/.env.example backend/.env

# Frontend 환경 변수
cp frontend/.env.example frontend/.env
```

3. **Docker Compose로 실행**
```bash
docker-compose up --build
```

4. **접속**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

#### 방법 2: 로컬 실행

**Backend 설정:**

1. **가상환경 생성 및 활성화**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

2. **의존성 설치**
```bash
pip install -r requirements.txt
```

3. **환경 변수 설정**
```bash
cp .env.example .env
# .env 파일을 열어 필요한 설정을 수정하세요
```

4. **서버 실행**
```bash
# 개발 모드
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는
python -m app.main
```

**Frontend 설정:**

1. **의존성 설치**
```bash
cd frontend
npm install
```

2. **환경 변수 설정**
```bash
cp .env.example .env.local
```

3. **개발 서버 실행**
```bash
npm run dev
```

4. **브라우저에서 접속**
```
http://localhost:3000
```

## ⚙️ 환경 설정

### Backend 환경 변수 (backend/.env)

```env
# 서버 설정
HOST=0.0.0.0
PORT=8000
DEBUG=true

# LLM 선택
USE_OPENAI_LLM=false  # true: OpenAI, false: Ollama

# OpenAI API (USE_OPENAI_LLM=true인 경우)
OPENAI_API_KEY=your-api-key-here

# Ollama 설정 (USE_OPENAI_LLM=false인 경우)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# AI 모델 설정
WHISPER_MODEL=base  # tiny, base, small, medium, large
TTS_MODEL=tts_models/ko/cv/vits

# 성능 설정
DEVICE=cpu  # cpu 또는 cuda (GPU)
```

### Frontend 환경 변수 (frontend/.env.local)

```env
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## 🔧 Ollama 설정 (로컬 LLM 사용 시)

Ollama를 사용하여 로컬에서 LLM을 실행하려면:

1. **Ollama 설치**
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: https://ollama.com/download
```

2. **모델 다운로드**
```bash
ollama pull llama2
# 또는 한국어 성능이 더 좋은 모델
ollama pull llama2-korean
```

3. **Ollama 서버 실행**
```bash
ollama serve
```

4. **Backend .env 설정 확인**
```env
USE_OPENAI_LLM=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

## 📖 사용 방법

1. **서버 연결 확인**
   - 페이지 상단에 "서버 연결됨" 표시 확인

2. **음성 대화**
   - 🎤 마이크 버튼 클릭하여 녹음 시작
   - 말한 후 다시 버튼 클릭하여 녹음 중지
   - AI가 자동으로 응답

3. **텍스트 대화**
   - 오른쪽 채팅창에 메시지 입력
   - 전송 버튼 클릭 또는 Enter 키

4. **처리 과정**
   - 🎤 **STT**: 음성을 텍스트로 변환
   - 🤖 **LLM**: AI가 응답 생성
   - 🔊 **TTS**: 텍스트를 음성으로 변환
   - 🎬 **Lipsync**: 립싱크 비디오 생성 (Phase 2)
   - 아바타가 립싱크와 함께 응답 표시

## 🏗️ 프로젝트 구조

```
InteractiveAIAvatarSystem/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 애플리케이션
│   │   ├── websocket/           # WebSocket 핸들러
│   │   │   └── handler.py
│   │   ├── services/            # AI 서비스
│   │   │   ├── config.py        # 설정 관리
│   │   │   ├── stt_service.py   # STT (Whisper)
│   │   │   ├── tts_service.py   # TTS (Coqui)
│   │   │   ├── llm_service.py   # LLM (Ollama/OpenAI)
│   │   │   └── wav2lip_service.py   # Wav2Lip (립싱크) - Phase 2
│   │   ├── utils/               # 유틸리티
│   │   │   └── video_utils.py   # 비디오 스트리밍
│   │   └── models/              # 데이터 모델
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # 메인 페이지
│   │   ├── components/          # React 컴포넌트
│   │   │   ├── AvatarDisplay/
│   │   │   ├── AudioRecorder/
│   │   │   └── ChatInterface/
│   │   └── lib/                 # 유틸리티
│   │       ├── websocket/       # WebSocket 클라이언트
│   │       ├── store.ts         # 상태 관리
│   │       └── audio-recorder.ts
│   ├── package.json
│   └── Dockerfile
├── models/                      # AI 모델 저장
├── docker-compose.yml
└── README.md
```

## 🐛 문제 해결

### 서버 연결 안됨

1. Backend 서버가 실행 중인지 확인
```bash
curl http://localhost:8000/health
```

2. CORS 설정 확인 (backend/.env)
```env
ALLOWED_ORIGINS=http://localhost:3000
```

### 마이크 권한 오류

- 브라우저에서 마이크 권한 허용
- HTTPS 또는 localhost에서만 마이크 접근 가능

### Whisper 모델 로딩 실패

- 인터넷 연결 확인 (최초 실행 시 모델 다운로드)
- 더 작은 모델 사용: `WHISPER_MODEL=tiny`

### TTS 오류

- Mock 서비스로 대체 가능 (자동 폴백)
- Coqui TTS 설치 확인:
```bash
pip install TTS
```

### Ollama 연결 실패

1. Ollama 서버 실행 확인
```bash
ollama list
```

2. 모델 다운로드 확인
```bash
ollama pull llama2
```

3. OpenAI API로 전환 (대안)
```env
USE_OPENAI_LLM=true
OPENAI_API_KEY=your-key
```

## 📈 성능 최적화

### CPU 사용 시

```env
WHISPER_MODEL=tiny      # 가장 빠른 STT 모델
DEVICE=cpu
```

### GPU 사용 시

```env
WHISPER_MODEL=small     # 더 정확한 모델
DEVICE=cuda
```

PyTorch CUDA 설치 필요:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 🚧 개발 로드맵

### Phase 1: 기본 음성 대화 시스템 ✅
- [x] FastAPI 서버 및 WebSocket
- [x] Whisper STT 통합
- [x] Ollama/OpenAI LLM 연동
- [x] Coqui TTS 통합
- [x] Frontend 기본 UI

### Phase 2: 립싱크 아바타 ✅
- [x] Wav2Lip 서비스 통합
- [x] Mock 서비스 폴백
- [x] 정적 아바타 이미지 → 립싱크 비디오
- [x] 비디오 스트리밍 파이프라인
- [x] Frontend 비디오 플레이어
- [x] 오디오-비디오 동기화

### Phase 3: 실시간 최적화 (예정)
- [ ] WebRTC 전환
- [ ] 청크 단위 실시간 처리
- [ ] 레이턴시 최적화 (< 2초 목표)
- [ ] 다중 아바타 지원

**📚 Phase 2 상세 가이드**: [PHASE2_GUIDE.md](PHASE2_GUIDE.md) 참조

## 🤝 기여

Pull Request를 환영합니다!

## 📝 라이선스

MIT License

## 📧 문의

이슈나 질문이 있으시면 GitHub Issues를 이용해주세요.

---

**Made with ❤️ for Interactive AI Avatar System**
