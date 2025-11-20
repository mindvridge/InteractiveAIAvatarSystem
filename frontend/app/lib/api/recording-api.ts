/**
 * Recording API 클라이언트
 * REST API를 통한 녹화 관리
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface RecordingMetadata {
  recording_id: string;
  room_id: string;
  room_name: string;
  started_at: string;
  ended_at: string | null;
  participants: string[];
  duration_seconds: number;
  file_path: string | null;
  file_size_bytes: number;
}

export interface RecordingListResponse {
  recordings: RecordingMetadata[];
  count: number;
}

/**
 * 녹화 시작
 */
export async function startRecording(roomId: string): Promise<RecordingMetadata> {
  const response = await fetch(`${API_BASE_URL}/rooms/${roomId}/recording/start`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to start recording');
  }

  const result = await response.json();
  return result.metadata;
}

/**
 * 녹화 중지
 */
export async function stopRecording(roomId: string): Promise<RecordingMetadata | null> {
  const response = await fetch(`${API_BASE_URL}/rooms/${roomId}/recording/stop`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to stop recording');
  }

  const result = await response.json();
  return result.metadata;
}

/**
 * 녹화 목록 조회
 */
export async function getRecordings(roomId?: string): Promise<RecordingListResponse> {
  const params = new URLSearchParams();
  if (roomId) {
    params.append('room_id', roomId);
  }

  const url = `${API_BASE_URL}/recordings${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error('Failed to fetch recordings');
  }

  return response.json();
}

/**
 * 녹화 메타데이터 조회
 */
export async function getRecording(recordingId: string): Promise<RecordingMetadata> {
  const response = await fetch(`${API_BASE_URL}/recordings/${recordingId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch recording');
  }

  const result = await response.json();
  return result.metadata;
}

/**
 * 녹화 파일 다운로드
 */
export async function downloadRecording(recordingId: string): Promise<void> {
  const url = `${API_BASE_URL}/recordings/${recordingId}/download`;

  // 새 창에서 다운로드
  window.open(url, '_blank');
}

/**
 * 녹화 삭제
 */
export async function deleteRecording(recordingId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/recordings/${recordingId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete recording');
  }
}
