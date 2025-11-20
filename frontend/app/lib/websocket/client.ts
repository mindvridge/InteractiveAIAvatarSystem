/**
 * WebSocket 클라이언트
 * 백엔드와의 실시간 양방향 통신 관리
 */

export type MessageType =
  | 'connection_established'
  | 'transcription'
  | 'response_text'
  | 'audio_response'
  | 'processing'
  | 'processing_complete'
  | 'error'
  | 'pong';

export interface WebSocketMessage {
  type: MessageType;
  data?: any;
}

export type MessageHandler = (message: WebSocketMessage) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private messageHandlers: Set<MessageHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isManualClose = false;

  constructor(url: string = 'ws://localhost:8000/ws') {
    this.url = url;
  }

  /**
   * WebSocket 연결
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        this.isManualClose = false;

        this.ws.onopen = () => {
          console.log('✅ WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('🔌 WebSocket disconnected');
          if (!this.isManualClose) {
            this.attemptReconnect();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 재연결 시도
   */
  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;

    console.log(`🔄 Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  /**
   * 메시지 핸들러 등록
   */
  addMessageHandler(handler: MessageHandler) {
    this.messageHandlers.add(handler);
  }

  /**
   * 메시지 핸들러 제거
   */
  removeMessageHandler(handler: MessageHandler) {
    this.messageHandlers.delete(handler);
  }

  /**
   * 수신된 메시지 처리
   */
  private handleMessage(message: WebSocketMessage) {
    this.messageHandlers.forEach((handler) => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });
  }

  /**
   * 텍스트 메시지 전송
   */
  sendText(text: string) {
    this.send({
      type: 'text_input',
      text,
    });
  }

  /**
   * 오디오 데이터 전송
   */
  sendAudio(audioBlob: Blob) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }

    audioBlob.arrayBuffer().then((buffer) => {
      this.ws?.send(buffer);
    });
  }

  /**
   * JSON 메시지 전송
   */
  send(data: any) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }

    this.ws.send(JSON.stringify(data));
  }

  /**
   * Ping 전송 (연결 유지)
   */
  ping() {
    this.send({ type: 'ping' });
  }

  /**
   * 연결 종료
   */
  disconnect() {
    this.isManualClose = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 연결 상태 확인
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}
