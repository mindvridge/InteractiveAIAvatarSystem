/**
 * WebRTC 스트리밍 Hook
 * 실시간 오디오/비디오 스트리밍 관리 - Phase 3
 */

'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { WebRTCClient } from './client';

export interface UseWebRTCStreamingOptions {
  signalingUrl?: string;
  autoConnect?: boolean;
  enableAudio?: boolean;
  enableVideo?: boolean;
}

export interface WebRTCStreamingState {
  isConnected: boolean;
  connectionState: RTCPeerConnectionState | null;
  error: string | null;
  localStream: MediaStream | null;
  remoteStream: MediaStream | null;
}

export function useWebRTCStreaming(options: UseWebRTCStreamingOptions = {}) {
  const {
    signalingUrl = 'ws://localhost:8000/webrtc',
    autoConnect = false,
    enableAudio = true,
    enableVideo = false,
  } = options;

  const clientRef = useRef<WebRTCClient | null>(null);
  const [state, setState] = useState<WebRTCStreamingState>({
    isConnected: false,
    connectionState: null,
    error: null,
    localStream: null,
    remoteStream: null,
  });

  /**
   * 연결 상태 업데이트
   */
  const handleConnectionStateChange = useCallback(
    (connectionState: RTCPeerConnectionState) => {
      setState((prev) => ({
        ...prev,
        connectionState,
        isConnected: connectionState === 'connected',
      }));

      if (connectionState === 'connected') {
        console.log('✅ WebRTC connected');
      } else if (connectionState === 'failed' || connectionState === 'disconnected') {
        console.log('❌ WebRTC connection failed/disconnected');
      }
    },
    []
  );

  /**
   * 원격 트랙 수신 처리
   */
  const handleTrack = useCallback((event: RTCTrackEvent) => {
    console.log('📺 Remote track received:', event.track.kind);

    // 원격 스트림 설정
    const [remoteStream] = event.streams;
    if (remoteStream) {
      setState((prev) => ({
        ...prev,
        remoteStream,
      }));
    }
  }, []);

  /**
   * WebRTC 연결 시작
   */
  const connect = useCallback(async () => {
    try {
      setState((prev) => ({ ...prev, error: null }));

      // WebRTC 클라이언트 생성
      const client = new WebRTCClient({
        signalingUrl,
      });

      clientRef.current = client;

      // 이벤트 핸들러 등록
      client.setOnConnectionStateChange(handleConnectionStateChange);
      client.setOnTrack(handleTrack);

      // 초기화
      await client.initialize();

      // 로컬 미디어 시작
      if (enableAudio || enableVideo) {
        const localStream = await client.startLocalMedia({
          audio: enableAudio,
          video: enableVideo,
        });

        setState((prev) => ({
          ...prev,
          localStream,
        }));
      }

      // Offer 생성 및 전송
      await client.createOffer();

      console.log('✅ WebRTC connection initiated');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Failed to connect WebRTC:', error);
      setState((prev) => ({
        ...prev,
        error: errorMessage,
      }));
    }
  }, [signalingUrl, enableAudio, enableVideo, handleConnectionStateChange, handleTrack]);

  /**
   * WebRTC 연결 종료
   */
  const disconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.close();
      clientRef.current = null;
    }

    setState({
      isConnected: false,
      connectionState: null,
      error: null,
      localStream: null,
      remoteStream: null,
    });

    console.log('🔌 WebRTC disconnected');
  }, []);

  /**
   * 데이터 전송
   */
  const sendData = useCallback((data: string | ArrayBuffer) => {
    if (clientRef.current) {
      clientRef.current.sendData(data);
    } else {
      console.warn('WebRTC client not initialized');
    }
  }, []);

  /**
   * 자동 연결
   */
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // 컴포넌트 언마운트 시 정리
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    sendData,
    client: clientRef.current,
  };
}
