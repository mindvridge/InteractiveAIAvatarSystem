/**
 * 아바타 디스플레이 컴포넌트
 * AI 아바타 비디오 또는 이미지 표시
 */

'use client';

import { useEffect, useRef } from 'react';
import { useAppStore } from '@/app/lib/store';

export default function AvatarDisplay() {
  const audioRef = useRef<HTMLAudioElement>(null);
  const { audioUrl, currentResponse, isProcessing, processingStage } = useAppStore();

  // 오디오 URL이 업데이트되면 자동 재생
  useEffect(() => {
    if (audioUrl && audioRef.current) {
      audioRef.current.src = audioUrl;
      audioRef.current.play().catch((error) => {
        console.error('Failed to play audio:', error);
      });
    }
  }, [audioUrl]);

  return (
    <div className="flex flex-col items-center gap-6">
      {/* 아바타 비디오/이미지 영역 */}
      <div className="relative w-80 h-80 bg-gradient-to-br from-purple-500 to-blue-500 rounded-2xl shadow-2xl overflow-hidden">
        {/* 플레이스홀더 아바타 */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-white text-8xl">🤖</div>
        </div>

        {/* 로딩 오버레이 */}
        {isProcessing && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="text-white text-center">
              <div className="animate-spin text-4xl mb-2">⚙️</div>
              <p className="text-sm">
                {processingStage === 'stt' && '음성 인식 중...'}
                {processingStage === 'llm' && '응답 생성 중...'}
                {processingStage === 'tts' && '음성 합성 중...'}
              </p>
            </div>
          </div>
        )}

        {/* 말하는 중 표시 */}
        {audioUrl && audioRef.current && !audioRef.current.paused && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4">
            <div className="flex items-center justify-center gap-2">
              <span className="text-white text-sm">말하는 중</span>
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 현재 응답 텍스트 */}
      {currentResponse && (
        <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-4">
          <p className="text-gray-800 text-center">{currentResponse}</p>
        </div>
      )}

      {/* 숨겨진 오디오 플레이어 */}
      <audio ref={audioRef} className="hidden" />
    </div>
  );
}
