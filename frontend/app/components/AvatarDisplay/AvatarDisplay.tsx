/**
 * 아바타 디스플레이 컴포넌트
 * AI 아바타 비디오 또는 이미지 표시 (Phase 2: 립싱크 비디오 지원)
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { useAppStore } from '@/app/lib/store';

export function AvatarDisplay() {
  const audioRef = useRef<HTMLAudioElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);

  const {
    audioUrl,
    videoUrl,
    currentResponse,
    isProcessing,
    processingStage,
  } = useAppStore();

  // 비디오 URL이 업데이트되면 자동 재생
  useEffect(() => {
    if (videoUrl && videoRef.current) {
      videoRef.current.src = videoUrl;
      videoRef.current.play().then(() => {
        setIsVideoPlaying(true);
      }).catch((error) => {
        console.error('Failed to play video:', error);
      });

      // 비디오 종료 이벤트
      videoRef.current.onended = () => {
        setIsVideoPlaying(false);
      };
    }
  }, [videoUrl]);

  // 오디오 URL이 업데이트되면 자동 재생 (비디오가 없을 때만)
  useEffect(() => {
    if (audioUrl && audioRef.current && !videoUrl) {
      audioRef.current.src = audioUrl;
      audioRef.current.play().catch((error) => {
        console.error('Failed to play audio:', error);
      });
    }
  }, [audioUrl, videoUrl]);

  return (
    <div className="flex flex-col items-center gap-6">
      {/* 아바타 비디오/이미지 영역 */}
      <div className="relative w-80 h-80 bg-gradient-to-br from-purple-500 to-blue-500 rounded-2xl shadow-2xl overflow-hidden">
        {/* 립싱크 비디오 */}
        {videoUrl ? (
          <video
            ref={videoRef}
            className="absolute inset-0 w-full h-full object-cover"
            playsInline
            muted={false}
          />
        ) : (
          /* 플레이스홀더 아바타 */
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-white text-8xl">🤖</div>
          </div>
        )}

        {/* 로딩 오버레이 */}
        {isProcessing && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-10">
            <div className="text-white text-center">
              <div className="animate-spin text-4xl mb-2">⚙️</div>
              <p className="text-sm">
                {processingStage === 'stt' && '음성 인식 중...'}
                {processingStage === 'llm' && '응답 생성 중...'}
                {processingStage === 'tts' && '음성 합성 중...'}
                {processingStage === 'lipsync' && '립싱크 비디오 생성 중...'}
              </p>
            </div>
          </div>
        )}

        {/* 말하는 중 표시 */}
        {(isVideoPlaying || (audioUrl && audioRef.current && !audioRef.current.paused)) && !isProcessing && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4 z-10">
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

        {/* Phase 2 뱃지 */}
        {videoUrl && (
          <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full z-10">
            Phase 2: 립싱크
          </div>
        )}
      </div>

      {/* 현재 응답 텍스트 */}
      {currentResponse && (
        <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-4">
          <p className="text-gray-800 text-center">{currentResponse}</p>
        </div>
      )}

      {/* 숨겨진 오디오 플레이어 (비디오가 없을 때 사용) */}
      <audio ref={audioRef} className="hidden" />
    </div>
  );
}
