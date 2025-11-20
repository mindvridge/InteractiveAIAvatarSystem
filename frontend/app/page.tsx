/**
 * 메인 페이지
 * Interactive AI Avatar System의 메인 인터페이스
 */

'use client';

import { useEffect, useRef, useCallback } from 'react';
import AvatarDisplay from './components/AvatarDisplay/AvatarDisplay';
import AudioRecorder from './components/AudioRecorder/AudioRecorder';
import ChatInterface from './components/ChatInterface/ChatInterface';
import { WebSocketClient } from './lib/websocket/client';
import { useAppStore } from './lib/store';

export default function Home() {
  const wsClientRef = useRef<WebSocketClient | null>(null);
  const {
    isConnected,
    setConnected,
    setProcessing,
    addMessage,
    setCurrentTranscription,
    setCurrentResponse,
    setAudioUrl,
    setVideoUrl,
    setError,
  } = useAppStore();

  // WebSocket 메시지 핸들러
  const handleWebSocketMessage = useCallback(
    (message: any) => {
      console.log('📨 Received:', message.type);

      switch (message.type) {
        case 'connection_established':
          console.log('✅ Connected to server');
          setConnected(true);
          break;

        case 'transcription':
          // STT 결과 (사용자 음성 인식)
          const userText = message.data.text;
          setCurrentTranscription(userText);
          addMessage({
            role: 'user',
            content: userText,
            timestamp: new Date(),
          });
          break;

        case 'response_text':
          // LLM 응답 텍스트
          const responseText = message.data.text;
          setCurrentResponse(responseText);
          addMessage({
            role: 'assistant',
            content: responseText,
            timestamp: new Date(),
          });
          break;

        case 'audio_response':
          // TTS 오디오 응답
          const audioBase64 = message.data.audio;
          const audioBlob = base64ToBlob(audioBase64, 'audio/wav');
          const audioUrl = URL.createObjectURL(audioBlob);
          setAudioUrl(audioUrl);
          break;

        case 'video_response':
          // Wav2Lip 비디오 응답
          const videoBase64 = message.data.video;
          const videoBlob = base64ToBlob(videoBase64, 'video/mp4');
          const videoUrl = URL.createObjectURL(videoBlob);
          setVideoUrl(videoUrl);
          break;

        case 'processing':
          // 처리 단계 업데이트
          const stage = message.data.stage;
          setProcessing(true, stage);
          break;

        case 'processing_complete':
          // 처리 완료
          setProcessing(false, 'idle');
          setCurrentTranscription('');
          break;

        case 'error':
          // 에러 처리
          console.error('Server error:', message.data.message);
          setError(message.data.message);
          setProcessing(false, 'idle');
          break;

        default:
          console.log('Unknown message type:', message.type);
      }
    },
    [
      setConnected,
      setProcessing,
      addMessage,
      setCurrentTranscription,
      setCurrentResponse,
      setAudioUrl,
      setVideoUrl,
      setError,
    ]
  );

  // WebSocket 연결 초기화
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    const wsClient = new WebSocketClient(wsUrl);
    wsClientRef.current = wsClient;

    // 메시지 핸들러 등록
    wsClient.addMessageHandler(handleWebSocketMessage);

    // 연결 시도
    wsClient.connect().catch((error) => {
      console.error('Failed to connect:', error);
      setError('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.');
    });

    // 정리
    return () => {
      wsClient.disconnect();
    };
  }, [handleWebSocketMessage, setError]);

  // 오디오 녹음 완료 핸들러
  const handleAudioRecorded = async (audioBlob: Blob) => {
    if (!wsClientRef.current?.isConnected()) {
      setError('서버에 연결되지 않았습니다.');
      return;
    }

    try {
      // WebSocket으로 오디오 전송
      wsClientRef.current.sendAudio(audioBlob);
    } catch (error) {
      console.error('Failed to send audio:', error);
      setError('오디오 전송에 실패했습니다.');
    }
  };

  // 텍스트 메시지 전송 핸들러
  const handleSendMessage = (message: string) => {
    if (!wsClientRef.current?.isConnected()) {
      setError('서버에 연결되지 않았습니다.');
      return;
    }

    try {
      // 사용자 메시지 추가
      addMessage({
        role: 'user',
        content: message,
        timestamp: new Date(),
      });

      // WebSocket으로 텍스트 전송
      wsClientRef.current.sendText(message);
    } catch (error) {
      console.error('Failed to send message:', error);
      setError('메시지 전송에 실패했습니다.');
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* 헤더 */}
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Interactive AI Avatar System
          </h1>
          <p className="text-gray-600">실시간 대화형 AI 아바타 프로토타입</p>

          {/* 연결 상태 표시 */}
          <div className="mt-4 flex items-center justify-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            ></div>
            <span className="text-sm text-gray-600">
              {isConnected ? '서버 연결됨' : '서버 연결 안됨'}
            </span>
          </div>
        </header>

        {/* 메인 콘텐츠 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 왼쪽: 아바타 디스플레이 및 오디오 녹음 */}
          <div className="flex flex-col items-center gap-8">
            <AvatarDisplay />
            <AudioRecorder onAudioRecorded={handleAudioRecorded} />
          </div>

          {/* 오른쪽: 채팅 인터페이스 */}
          <div className="h-[600px]">
            <ChatInterface onSendMessage={handleSendMessage} />
          </div>
        </div>

        {/* 사용 방법 안내 */}
        <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            사용 방법
          </h2>
          <ul className="space-y-2 text-gray-600">
            <li>🎤 <strong>음성 입력:</strong> 마이크 버튼을 클릭하여 녹음을 시작하고, 다시 클릭하여 중지합니다.</li>
            <li>💬 <strong>텍스트 입력:</strong> 오른쪽 채팅창에 메시지를 입력하여 대화할 수 있습니다.</li>
            <li>🤖 <strong>AI 응답:</strong> AI가 음성과 텍스트로 응답합니다.</li>
          </ul>
        </div>
      </div>
    </main>
  );
}

/**
 * Base64를 Blob으로 변환
 */
function base64ToBlob(base64: string, mimeType: string): Blob {
  const byteCharacters = atob(base64);
  const byteNumbers = new Array(byteCharacters.length);

  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }

  const byteArray = new Uint8Array(byteNumbers);
  return new Blob([byteArray], { type: mimeType });
}
