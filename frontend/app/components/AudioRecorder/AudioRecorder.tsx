/**
 * 오디오 녹음 컴포넌트
 * 음성 입력을 위한 녹음 버튼 제공
 */

'use client';

import { useRef } from 'react';
import { useAppStore } from '@/app/lib/store';
import { AudioRecorder as AudioRecorderUtil } from '@/app/lib/audio-recorder';

interface AudioRecorderProps {
  onAudioRecorded?: (audioBlob: Blob) => void;
}

export function AudioRecorder({ onAudioRecorded }: AudioRecorderProps) {
  const audioRecorderRef = useRef<AudioRecorderUtil | null>(null);
  const { isRecording, setRecording, isProcessing } = useAppStore();

  const handleRecordClick = async () => {
    if (isRecording) {
      // 녹음 중지
      if (audioRecorderRef.current) {
        try {
          const audioBlob = await audioRecorderRef.current.stopRecording();
          setRecording(false);
          if (onAudioRecorded) {
            onAudioRecorded(audioBlob);
          }
        } catch (error) {
          console.error('Failed to stop recording:', error);
          setRecording(false);
        }
      }
    } else {
      // 녹음 시작
      try {
        audioRecorderRef.current = new AudioRecorderUtil();
        await audioRecorderRef.current.startRecording();
        setRecording(true);
      } catch (error) {
        console.error('Failed to start recording:', error);
        alert('마이크 권한이 필요합니다.');
      }
    }
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <button
        onClick={handleRecordClick}
        disabled={isProcessing}
        className={`
          w-20 h-20 rounded-full flex items-center justify-center
          transition-all duration-200 shadow-lg
          ${
            isRecording
              ? 'bg-red-500 hover:bg-red-600 animate-pulse'
              : 'bg-blue-500 hover:bg-blue-600'
          }
          ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          text-white text-3xl
        `}
        aria-label={isRecording ? '녹음 중지' : '녹음 시작'}
      >
        {isRecording ? '⏹' : '🎤'}
      </button>

      <div className="text-center">
        <p className="text-sm font-medium">
          {isRecording ? '녹음 중... 다시 클릭하여 중지' : '클릭하여 녹음 시작'}
        </p>
        {isProcessing && (
          <p className="text-xs text-gray-500 mt-1">처리 중...</p>
        )}
      </div>
    </div>
  );
}
