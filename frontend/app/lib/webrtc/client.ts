/**
 * WebRTC 클라이언트
 * P2P 실시간 통신 구현 - Phase 3
 */

export interface WebRTCConfig {
  iceServers?: RTCIceServer[];
  signalingUrl?: string;
}

export type ConnectionStateHandler = (state: RTCPeerConnectionState) => void;
export type TrackHandler = (event: RTCTrackEvent) => void;
export type DataChannelHandler = (channel: RTCDataChannel) => void;

export class WebRTCClient {
  private peerConnection: RTCPeerConnection | null = null;
  private signalingSocket: WebSocket | null = null;
  private dataChannel: RTCDataChannel | null = null;
  private config: WebRTCConfig;

  // 이벤트 핸들러
  private onConnectionStateChange: ConnectionStateHandler | null = null;
  private onTrack: TrackHandler | null = null;
  private onDataChannel: DataChannelHandler | null = null;

  // 로컬 스트림
  private localStream: MediaStream | null = null;

  constructor(config: WebRTCConfig = {}) {
    this.config = {
      iceServers: config.iceServers || [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' },
      ],
      signalingUrl: config.signalingUrl || 'ws://localhost:8000/webrtc',
    };
  }

  /**
   * WebRTC 연결 초기화
   */
  async initialize(): Promise<void> {
    try {
      // RTCPeerConnection 생성
      this.peerConnection = new RTCPeerConnection({
        iceServers: this.config.iceServers,
      });

      // 이벤트 리스너 등록
      this.setupPeerConnectionListeners();

      // Signaling 소켓 연결
      await this.connectSignaling();

      console.log('✅ WebRTC initialized');
    } catch (error) {
      console.error('Failed to initialize WebRTC:', error);
      throw error;
    }
  }

  /**
   * RTCPeerConnection 이벤트 리스너 설정
   */
  private setupPeerConnectionListeners(): void {
    if (!this.peerConnection) return;

    // 연결 상태 변경
    this.peerConnection.onconnectionstatechange = () => {
      if (!this.peerConnection) return;
      console.log('Connection state:', this.peerConnection.connectionState);

      if (this.onConnectionStateChange) {
        this.onConnectionStateChange(this.peerConnection.connectionState);
      }
    };

    // ICE 후보자 발견
    this.peerConnection.onicecandidate = (event) => {
      if (event.candidate && this.signalingSocket) {
        this.signalingSocket.send(
          JSON.stringify({
            type: 'ice_candidate',
            candidate: event.candidate,
          })
        );
        console.log('🧊 ICE candidate sent');
      }
    };

    // 트랙 수신 (원격 스트림)
    this.peerConnection.ontrack = (event) => {
      console.log('📺 Track received:', event.track.kind);

      if (this.onTrack) {
        this.onTrack(event);
      }
    };

    // 데이터 채널 수신
    this.peerConnection.ondatachannel = (event) => {
      console.log('📡 Data channel received');
      this.dataChannel = event.channel;
      this.setupDataChannelListeners();

      if (this.onDataChannel) {
        this.onDataChannel(event.channel);
      }
    };
  }

  /**
   * Signaling 서버 연결
   */
  private async connectSignaling(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.config.signalingUrl) {
        reject(new Error('Signaling URL not configured'));
        return;
      }

      this.signalingSocket = new WebSocket(this.config.signalingUrl);

      this.signalingSocket.onopen = () => {
        console.log('✅ Signaling connected');
        resolve();
      };

      this.signalingSocket.onerror = (error) => {
        console.error('Signaling error:', error);
        reject(error);
      };

      this.signalingSocket.onmessage = async (event) => {
        await this.handleSignalingMessage(JSON.parse(event.data));
      };

      this.signalingSocket.onclose = () => {
        console.log('Signaling disconnected');
      };
    });
  }

  /**
   * Signaling 메시지 처리
   */
  private async handleSignalingMessage(message: any): Promise<void> {
    if (!this.peerConnection) return;

    switch (message.type) {
      case 'answer':
        // SDP Answer 수신
        await this.peerConnection.setRemoteDescription(
          new RTCSessionDescription(message.answer)
        );
        console.log('📥 Answer received and set');
        break;

      case 'ice_candidate':
        // ICE 후보자 수신
        if (message.candidate) {
          await this.peerConnection.addIceCandidate(
            new RTCIceCandidate(message.candidate)
          );
          console.log('🧊 ICE candidate added');
        }
        break;

      default:
        console.log('Unknown signaling message:', message.type);
    }
  }

  /**
   * 로컬 미디어 스트림 시작
   */
  async startLocalMedia(constraints: MediaStreamConstraints = {}): Promise<MediaStream> {
    try {
      const defaultConstraints: MediaStreamConstraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        },
        video: false,
        ...constraints,
      };

      this.localStream = await navigator.mediaDevices.getUserMedia(defaultConstraints);

      // 로컬 스트림을 peer connection에 추가
      if (this.peerConnection) {
        this.localStream.getTracks().forEach((track) => {
          if (this.peerConnection && this.localStream) {
            this.peerConnection.addTrack(track, this.localStream);
          }
        });
      }

      console.log('🎤 Local media started');
      return this.localStream;
    } catch (error) {
      console.error('Failed to start local media:', error);
      throw error;
    }
  }

  /**
   * Offer 생성 및 전송
   */
  async createOffer(): Promise<void> {
    if (!this.peerConnection || !this.signalingSocket) {
      throw new Error('WebRTC not initialized');
    }

    try {
      // Data channel 생성 (옵션)
      this.dataChannel = this.peerConnection.createDataChannel('data');
      this.setupDataChannelListeners();

      // Offer 생성
      const offer = await this.peerConnection.createOffer();
      await this.peerConnection.setLocalDescription(offer);

      // Signaling 서버로 Offer 전송
      this.signalingSocket.send(
        JSON.stringify({
          type: 'offer',
          offer: this.peerConnection.localDescription,
        })
      );

      console.log('📤 Offer created and sent');
    } catch (error) {
      console.error('Failed to create offer:', error);
      throw error;
    }
  }

  /**
   * Data channel 리스너 설정
   */
  private setupDataChannelListeners(): void {
    if (!this.dataChannel) return;

    this.dataChannel.onopen = () => {
      console.log('📡 Data channel opened');
    };

    this.dataChannel.onclose = () => {
      console.log('📡 Data channel closed');
    };

    this.dataChannel.onmessage = (event) => {
      console.log('📨 Data received:', event.data);
    };
  }

  /**
   * Data channel로 데이터 전송
   */
  sendData(data: string | ArrayBuffer): void {
    if (this.dataChannel && this.dataChannel.readyState === 'open') {
      this.dataChannel.send(data);
      console.log('📤 Data sent');
    } else {
      console.warn('Data channel not ready');
    }
  }

  /**
   * 연결 상태 변경 핸들러 등록
   */
  setOnConnectionStateChange(handler: ConnectionStateHandler): void {
    this.onConnectionStateChange = handler;
  }

  /**
   * 트랙 수신 핸들러 등록
   */
  setOnTrack(handler: TrackHandler): void {
    this.onTrack = handler;
  }

  /**
   * Data channel 핸들러 등록
   */
  setOnDataChannel(handler: DataChannelHandler): void {
    this.onDataChannel = handler;
  }

  /**
   * 현재 연결 상태
   */
  getConnectionState(): RTCPeerConnectionState | null {
    return this.peerConnection?.connectionState || null;
  }

  /**
   * 연결 종료
   */
  close(): void {
    // Local stream 정리
    if (this.localStream) {
      this.localStream.getTracks().forEach((track) => track.stop());
      this.localStream = null;
    }

    // Data channel 종료
    if (this.dataChannel) {
      this.dataChannel.close();
      this.dataChannel = null;
    }

    // Peer connection 종료
    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }

    // Signaling 소켓 종료
    if (this.signalingSocket) {
      this.signalingSocket.close();
      this.signalingSocket = null;
    }

    console.log('🔌 WebRTC connection closed');
  }
}
