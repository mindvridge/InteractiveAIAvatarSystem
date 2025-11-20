/**
 * 녹화 목록 컴포넌트
 * 녹화된 세션 목록 표시 및 관리
 */

'use client';

import { useState, useEffect } from 'react';
import {
  getRecordings,
  downloadRecording,
  deleteRecording,
  RecordingMetadata,
} from '@/app/lib/api/recording-api';

interface RecordingsListProps {
  roomId?: string;
}

export function RecordingsList({ roomId }: RecordingsListProps) {
  const [recordings, setRecordings] = useState<RecordingMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * 녹화 목록 로드
   */
  const loadRecordings = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getRecordings(roomId);
      setRecordings(response.recordings);
    } catch (err) {
      console.error('Failed to load recordings:', err);
      setError('Failed to load recordings');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 녹화 삭제
   */
  const handleDelete = async (recordingId: string) => {
    if (!confirm('Are you sure you want to delete this recording?')) {
      return;
    }

    try {
      await deleteRecording(recordingId);
      await loadRecordings();
    } catch (err) {
      console.error('Failed to delete recording:', err);
      alert('Failed to delete recording');
    }
  };

  /**
   * 녹화 다운로드
   */
  const handleDownload = (recordingId: string) => {
    downloadRecording(recordingId);
  };

  /**
   * 초기 로드
   */
  useEffect(() => {
    loadRecordings();
  }, [roomId]);

  /**
   * 시간 포맷
   */
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  /**
   * 파일 크기 포맷
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Recordings</h2>
        <button
          onClick={loadRecordings}
          disabled={isLoading}
          className="px-4 py-2 text-sm bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50"
        >
          {isLoading ? '⏳ Loading...' : '🔄 Refresh'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Recordings List */}
      {isLoading && recordings.length === 0 ? (
        <div className="text-center py-12 text-gray-500">Loading recordings...</div>
      ) : recordings.length === 0 ? (
        <div className="text-center py-12 text-gray-500">No recordings found</div>
      ) : (
        <div className="space-y-4">
          {recordings.map((recording) => (
            <div
              key={recording.recording_id}
              className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 dark:hover:border-blue-500 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{recording.room_name}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {new Date(recording.started_at).toLocaleString()}
                  </p>

                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-600 dark:text-gray-400">
                    <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 rounded">
                      ⏱ {formatDuration(recording.duration_seconds)}
                    </span>
                    <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 rounded">
                      👥 {recording.participants.length} participants
                    </span>
                    {recording.file_size_bytes > 0 && (
                      <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
                        📁 {formatFileSize(recording.file_size_bytes)}
                      </span>
                    )}
                  </div>

                  {recording.participants.length > 0 && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      Participants: {recording.participants.join(', ')}
                    </p>
                  )}
                </div>

                <div className="flex gap-2">
                  {recording.file_path && (
                    <button
                      onClick={() => handleDownload(recording.recording_id)}
                      className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                    >
                      📥 Download
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(recording.recording_id)}
                    className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                  >
                    🗑 Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
