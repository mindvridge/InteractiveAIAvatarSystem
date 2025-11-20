# Phase 3: WebRTC 실시간 최적화 가이드

Phase 3에서는 WebRTC를 사용하여 실시간 P2P 통신을 구현하고, 청크 단위 스트리밍으로 레이턴시를 최적화합니다.

## 🚀 Phase 3 기능

- ✅ WebRTC P2P 실시간 통신
- ✅ Signaling 서버 구현
- ✅ 청크 단위 스트리밍 처리
- ✅ ICE 서버 자동 구성
- ✅ 실시간 오디오/비디오 스트리밍
- ✅ 데이터 채널 지원
- ✅ 레이턴시 < 2초 목표

## 📋 Phase 3 vs Phase 1&2

### Phase 1 & 2 (WebSocket)
```
사용자 → 전체 오디오 녹음 → WebSocket 전송 → 서버 처리 → 응답 대기
레이턴시: ~5-10초
```

### Phase 3 (WebRTC)
```
사용자 → 실시간 오디오 스트림 → P2P 전송 → 청크 단위 처리 → 즉시 응답
레이턴시: < 2초 ⚡
```

## 🎯 주요 개선사항

1. **실시간 스트리밍**
   - 전체 오디오를 기다리지 않고 청크 단위로 처리
   - 사용자가 말하는 동안 동시에 처리 시작

2. **P2P 연결**
   - 서버를 거치지 않는 직접 통신
   - 네트워크 레이턴시 최소화

3. **청크 처리**
   - 4KB 단위로 오디오 전송
   - STT, LLM, TTS 파이프라인 병렬 처리

4. **연결 안정성**
   - ICE를 통한 NAT 트래버설
   - STUN/TURN 서버 지원

## 🏗️ 아키텍처

### Backend

```
FastAPI
├── /webrtc (Signaling WebSocket)
│   ├── Offer/Answer 교환
│   ├── ICE Candidate 전송
│   └── Peer 관리
└── WebRTCSignalingService
    ├── Peer 등록/해제
    ├── SDP 처리
    └── StreamingChunkProcessor
        ├── 청크 생성
        ├── 실시간 처리
        └── 청크 스트리밍
```

### Frontend

```
Next.js
└── WebRTC Client
    ├── RTCPeerConnection
    ├── Signaling WebSocket
    ├── Local Media Stream
    ├── Remote Media Stream
    └── Data Channel
```

## 🚀 빠른 시작

### 1. Backend 실행

기존 설정 그대로 사용:

```bash
cd backend
uvicorn app.main:app --reload
```

WebRTC Signaling 서버가 자동으로 활성화됩니다.

### 2. Frontend에서 WebRTC 사용

#### 방법 1: WebRTC Hook 사용

```typescript
import { useWebRTCStreaming } from '@/app/lib/webrtc/use-webrtc-streaming';

function MyComponent() {
  const {
    isConnected,
    connectionState,
    localStream,
    remoteStream,
    connect,
    disconnect,
    sendData,
  } = useWebRTCStreaming({
    signalingUrl: 'ws://localhost:8000/webrtc',
    autoConnect: false,
    enableAudio: true,
    enableVideo: false,
  });

  // 연결 시작
  const handleConnect = async () => {
    await connect();
  };

  // 데이터 전송
  const handleSend = () => {
    sendData('Hello from WebRTC!');
  };

  return (
    <div>
      <button onClick={handleConnect}>
        {isConnected ? 'Connected' : 'Connect'}
      </button>
      <p>State: {connectionState}</p>
    </div>
  );
}
```

#### 방법 2: WebRTC Client 직접 사용

```typescript
import { WebRTCClient } from '@/app/lib/webrtc/client';

const client = new WebRTCClient({
  signalingUrl: 'ws://localhost:8000/webrtc',
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
  ],
});

// 초기화
await client.initialize();

// 로컬 미디어 시작
const localStream = await client.startLocalMedia({
  audio: true,
  video: false,
});

// Offer 생성
await client.createOffer();

// 트랙 수신 핸들러
client.setOnTrack((event) => {
  const [remoteStream] = event.streams;
  // remoteStream 사용
});
```

## ⚙️ 설정

### STUN/TURN 서버 설정

프로덕션 환경에서는 자체 TURN 서버를 권장합니다:

```typescript
const client = new WebRTCClient({
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    {
      urls: 'turn:your-turn-server.com:3478',
      username: 'user',
      credential: 'pass',
    },
  ],
});
```

### 오디오 설정 최적화

```typescript
const localStream = await client.startLocalMedia({
  audio: {
    echoCancellation: true,  // 에코 제거
    noiseSuppression: true,  // 노이즈 제거
    autoGainControl: true,   // 자동 게인 조절
    sampleRate: 16000,       // 16kHz (Whisper 최적)
    channelCount: 1,         // Mono
  },
});
```

## 📊 성능 최적화

### 청크 크기 조정

```python
# backend/app/services/webrtc_service.py
chunk_processor = StreamingChunkProcessor(
    chunk_size=4096  # 4KB (기본값)
    # chunk_size=8192  # 8KB (더 큰 청크)
)
```

### 처리 파이프라인 병렬화

```
청크 1 → STT → LLM → TTS → 비디오
청크 2         → STT → LLM → TTS → 비디오
청크 3                → STT → LLM → TTS → 비디오
```

### 레이턴시 측정

```typescript
const startTime = Date.now();

client.setOnTrack((event) => {
  const latency = Date.now() - startTime;
  console.log(`Latency: ${latency}ms`);
});
```

## 🎬 사용 예시

### 실시간 음성 대화

```typescript
'use client';

import { useWebRTCStreaming } from '@/app/lib/webrtc/use-webrtc-streaming';
import { useEffect, useRef } from 'react';

export default function RealtimeChat() {
  const audioRef = useRef<HTMLAudioElement>(null);

  const {
    isConnected,
    localStream,
    remoteStream,
    connect,
    disconnect,
  } = useWebRTCStreaming({
    enableAudio: true,
    autoConnect: true,
  });

  // 원격 스트림을 오디오 엘리먼트에 연결
  useEffect(() => {
    if (remoteStream && audioRef.current) {
      audioRef.current.srcObject = remoteStream;
    }
  }, [remoteStream]);

  return (
    <div>
      <h1>Real-time Voice Chat</h1>
      <p>Status: {isConnected ? '🟢 Connected' : '🔴 Disconnected'}</p>

      <audio ref={audioRef} autoPlay />

      <button onClick={disconnect}>Disconnect</button>
    </div>
  );
}
```

## 🐛 문제 해결

### 연결이 안 될 때

1. **STUN 서버 확인**
   ```typescript
   // 콘솔에서 ICE gathering 상태 확인
   client.setOnConnectionStateChange((state) => {
     console.log('Connection state:', state);
   });
   ```

2. **방화벽/NAT 확인**
   - UDP 포트가 차단되어 있는지 확인
   - TURN 서버 사용 고려

3. **Signaling 연결 확인**
   ```bash
   # Signaling 서버 로그 확인
   # Backend 콘솔에서 "New WebRTC signaling connection" 메시지 확인
   ```

### 오디오가 들리지 않을 때

1. **브라우저 권한 확인**
   - 마이크 권한 허용 필요
   - HTTPS 또는 localhost에서만 작동

2. **스트림 연결 확인**
   ```typescript
   if (remoteStream) {
     console.log('Remote tracks:', remoteStream.getTracks());
   }
   ```

3. **오디오 엘리먼트 확인**
   ```typescript
   <audio autoPlay playsInline muted={false} />
   ```

### 레이턴시가 높을 때

1. **네트워크 확인**
   - Ping 테스트
   - 대역폭 확인

2. **청크 크기 조정**
   ```python
   # 더 작은 청크로 변경
   chunk_size=2048
   ```

3. **처리 최적화**
   - GPU 사용 (DEVICE=cuda)
   - 낮은 해상도 비디오
   - 더 빠른 AI 모델

## 📈 성능 비교

| 항목 | Phase 1&2 (WebSocket) | Phase 3 (WebRTC) |
|------|----------------------|------------------|
| 레이턴시 | ~5-10초 | < 2초 ⚡ |
| 실시간성 | 전체 오디오 대기 | 청크 단위 처리 |
| 네트워크 | 서버 경유 | P2P 직접 |
| 대역폭 | 높음 | 낮음 (최적화) |
| 확장성 | 서버 부하 | 분산 처리 |

## 🔒 보안 고려사항

1. **HTTPS 필수**
   - WebRTC는 보안 컨텍스트에서만 작동
   - 프로덕션에서는 HTTPS 사용 필수

2. **Signaling 보안**
   - 인증 추가
   - WSS (Secure WebSocket) 사용

3. **TURN 서버 보안**
   - 비밀번호 보호
   - 타임아웃 설정

## 🎯 다음 단계

Phase 3 완료 후 추가 개선 사항:

- [ ] 다중 사용자 지원
- [ ] 화면 공유
- [ ] 녹화 기능
- [ ] 품질 자동 조정 (Adaptive Bitrate)
- [ ] 통계 및 모니터링

## 💡 팁

1. **개발 환경**: localhost에서 먼저 테스트
2. **점진적 적용**: Phase 1&2와 병행 사용 가능
3. **성능 모니터링**: Chrome WebRTC Internals 사용
4. **네트워크 테스트**: 다양한 네트워크 환경에서 테스트

## 📚 참고 자료

- [WebRTC 공식 문서](https://webrtc.org/)
- [MDN WebRTC API](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)
- [Chrome WebRTC Internals](chrome://webrtc-internals/)

---

**Phase 3 체크리스트:**

- [x] WebRTC Signaling 서버
- [x] Peer Connection 구현
- [x] ICE 서버 구성
- [x] 청크 스트리밍 처리
- [x] 실시간 오디오 스트리밍
- [x] 데이터 채널
- [x] React Hook
- [x] 문서 작성

**Made with ❤️ for Interactive AI Avatar System - Phase 3**
