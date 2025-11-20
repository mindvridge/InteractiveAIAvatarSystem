/**
 * 오디오 녹음 유틸리티
 * 브라우저의 MediaRecorder API를 사용한 음성 녹음
 */

export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private stream: MediaStream | null = null;

  /**
   * 녹음 시작
   */
  async startRecording(): Promise<void> {
    try {
      // 마이크 권한 요청 및 스트림 획득
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1, // Mono
          sampleRate: 16000, // 16kHz
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // MediaRecorder 생성
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'audio/webm',
      });

      this.audioChunks = [];

      // 데이터 수집
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      // 녹음 시작
      this.mediaRecorder.start();
      console.log('🎤 Recording started');
    } catch (error) {
      console.error('Failed to start recording:', error);
      throw error;
    }
  }

  /**
   * 녹음 중지 및 오디오 Blob 반환
   */
  stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        reject(new Error('MediaRecorder not initialized'));
        return;
      }

      this.mediaRecorder.onstop = () => {
        // 오디오 청크를 하나의 Blob으로 결합
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });

        // 스트림 정리
        if (this.stream) {
          this.stream.getTracks().forEach((track) => track.stop());
          this.stream = null;
        }

        console.log('🎤 Recording stopped');
        resolve(audioBlob);
      };

      this.mediaRecorder.stop();
    });
  }

  /**
   * 녹음 중인지 확인
   */
  isRecording(): boolean {
    return this.mediaRecorder !== null && this.mediaRecorder.state === 'recording';
  }

  /**
   * 리소스 정리
   */
  cleanup() {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
    if (this.mediaRecorder) {
      this.mediaRecorder = null;
    }
    this.audioChunks = [];
  }
}

/**
 * WAV 파일로 변환
 */
export async function convertToWav(blob: Blob): Promise<Blob> {
  // 실제 프로덕션에서는 AudioContext를 사용하여 WAV로 변환해야 함
  // 현재는 간단히 원본 Blob을 반환
  // TODO: WebM을 WAV로 변환하는 로직 추가
  return blob;
}

/**
 * 오디오 재생
 */
export function playAudio(audioUrl: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const audio = new Audio(audioUrl);

    audio.onended = () => resolve();
    audio.onerror = (error) => reject(error);

    audio.play().catch(reject);
  });
}
