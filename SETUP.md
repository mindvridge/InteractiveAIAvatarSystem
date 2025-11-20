# 빠른 설정 가이드

## 1분 안에 시작하기

### Backend 실행

```bash
cd backend

# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env

# 서버 실행
uvicorn app.main:app --reload
```

Backend가 http://localhost:8000 에서 실행됩니다.

### Frontend 실행

새 터미널에서:

```bash
cd frontend

# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env.local

# 개발 서버 실행
npm run dev
```

Frontend가 http://localhost:3000 에서 실행됩니다.

## Mock 모드로 빠르게 테스트

AI 모델 없이 Mock 서비스로 테스트할 수 있습니다:

1. Backend를 그냥 실행 (모델이 없으면 자동으로 Mock 모드)
2. Frontend 접속
3. 마이크 버튼이나 채팅으로 테스트

## Ollama 설치 (선택사항)

로컬 LLM을 사용하려면:

```bash
# Ollama 설치
curl -fsSL https://ollama.com/install.sh | sh

# 모델 다운로드
ollama pull llama2

# Ollama 서버 실행 (자동으로 백그라운드 실행됨)
ollama serve
```

Backend `.env` 파일:
```env
USE_OPENAI_LLM=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

## Docker Compose (가장 쉬운 방법)

```bash
# 환경 변수 설정
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Docker Compose로 실행
docker-compose up --build
```

## 문제 해결

### "ModuleNotFoundError: No module named 'app'"

```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:${PWD}"
python -m app.main
```

### Frontend에서 "서버 연결 안됨"

1. Backend가 실행 중인지 확인: http://localhost:8000/health
2. `.env.local`의 `NEXT_PUBLIC_WS_URL` 확인
3. CORS 설정 확인 (backend/.env의 ALLOWED_ORIGINS)

### 마이크 권한 오류

- 브라우저 설정에서 마이크 권한 허용
- HTTPS 또는 localhost에서만 작동

## 다음 단계

1. ✅ Phase 1: 기본 음성 대화 시스템 (완료)
2. 🚧 Phase 2: Wav2Lip 립싱크 통합 (예정)
3. 🚧 Phase 3: WebRTC 실시간 최적화 (예정)

자세한 내용은 [README.md](README.md)를 참조하세요.
