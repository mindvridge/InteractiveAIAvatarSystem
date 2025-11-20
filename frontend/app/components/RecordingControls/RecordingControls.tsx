/**
 * 녹화 컨트롤 컴포넌트
 * Room 녹화 시작/중지 및 상태 표시
 */

'use client';

import { useState } from 'react';
import { startRecording, stopRecording } from '@/app/lib/api/recording-api';

interface RecordingControlsProps {
  roomId: string;
  isRecording: boolean;
  onRecordingStateChange?: (isRecording: boolean) => void;
}

export function RecordingControls({
  roomId,
  isRecording,
  onRecordingStateChange,
}: RecordingControlsProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * 녹화 시작
   */
  const handleStartRecording = async () => {
    setIsProcessing(true);
    setError(null);

    try {
      await startRecording(roomId);
      onRecordingStateChange?.(true);
    } catch (err) {
      console.error('Failed to start recording:', err);
      setError(err instanceof Error ? err.message : 'Failed to start recording');
    } finally {
      setIsProcessing(false);
    }
  };

  /**
   * 녹화 중지
   */
  const handleStopRecording = async () => {
    setIsProcessing(true);
    setError(null);

    try {
      await stopRecording(roomId);
      onRecordingStateChange?.(false);
    } catch (err) {
      console.error('Failed to stop recording:', err);
      setError(err instanceof Error ? err.message : 'Failed to stop recording');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      {/* 녹화 버튼 */}
      <button
        onClick={isRecording ? handleStopRecording : handleStartRecording}
        disabled={isProcessing}
        className={`
          px-4 py-2 rounded-lg font-semibold transition-colors
          ${
            isRecording
              ? 'bg-red-500 hover:bg-red-600 text-white'
              : 'bg-gray-500 hover:bg-gray-600 text-white'
          }
          ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        {isProcessing ? (
          <span className="flex items-center gap-2">
            <span className="animate-spin">⏳</span>
            Processing...
          </span>
        ) : isRecording ? (
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
            Stop Recording
          </span>
        ) : (
          <span className="flex items-center gap-2">
            🔴 Start Recording
          </span>
        )}
      </button>

      {/* 에러 메시지 */}
      {error && (
        <div className="text-xs text-red-500 dark:text-red-400">
          {error}
        </div>
      )}
    </div>
  );
}
