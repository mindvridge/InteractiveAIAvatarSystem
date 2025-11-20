/**
 * Room WebSocket 클라이언트
 * 다중 사용자 Room 통신
 */

'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useAppStore, Room } from '../store';

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface RoomWebSocketMessage {
  type: string;
  data?: any;
}

export function useRoomWebSocket(roomId: string | null, username: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);

  const { setConnected, setError, setCurrentRoom, addMessage } = useAppStore();

  /**
   * 메시지 전송
   */
  const sendMessage = useCallback((message: RoomWebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected');
    }
  }, []);

  /**
   * 메시지 핸들러
   */
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: RoomWebSocketMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'room_joined':
          // Room 참여 성공
          if (message.data?.room) {
            setCurrentRoom(message.data.room as Room);
            console.log('✅ Joined room:', message.data.room);
          }
          break;

        case 'user_joined':
          // 새 사용자 참여 알림
          console.log('👤 User joined:', message.data?.username);
          addMessage({
            role: 'assistant',
            content: `${message.data?.username}님이 입장했습니다.`,
            timestamp: new Date(),
          });
          break;

        case 'user_left':
          // 사용자 퇴장 알림
          console.log('👋 User left:', message.data?.username);
          addMessage({
            role: 'assistant',
            content: `${message.data?.username}님이 퇴장했습니다.`,
            timestamp: new Date(),
          });
          break;

        case 'user_speaking':
          // 사용자 발화 상태 변경
          console.log('🎤 User speaking:', message.data?.username, message.data?.is_speaking);
          // Room 상태 업데이트 (필요시)
          break;

        case 'chat_message':
          // 채팅 메시지
          addMessage({
            role: message.data?.user_id === wsRef.current ? 'user' : 'assistant',
            content: `${message.data?.username}: ${message.data?.message}`,
            timestamp: new Date(),
          });
          break;

        case 'recording_started':
          // 녹화 시작 알림
          console.log('🔴 Recording started:', message.data?.recording_id);
          addMessage({
            role: 'assistant',
            content: '🔴 녹화가 시작되었습니다.',
            timestamp: new Date(),
          });
          break;

        case 'recording_stopped':
          // 녹화 중지 알림
          console.log('⏹ Recording stopped:', message.data?.recording_id);
          addMessage({
            role: 'assistant',
            content: '⏹ 녹화가 중지되었습니다.',
            timestamp: new Date(),
          });
          break;

        case 'error':
          // 에러 처리
          setError(message.data?.message || 'Unknown error');
          console.error('Room error:', message.data?.message);
          break;

        default:
          console.log('Unknown room message type:', message.type);
      }
    } catch (error) {
      console.error('Failed to parse room message:', error);
    }
  }, [setCurrentRoom, addMessage, setError]);

  /**
   * 연결
   */
  const connect = useCallback(() => {
    if (!roomId || !username) {
      console.warn('Room ID or username not provided');
      return;
    }

    try {
      const ws = new WebSocket(`${WS_BASE_URL}/rooms/${roomId}/ws`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ Room WebSocket connected');
        setConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;

        // 초기화 메시지 전송 (username)
        ws.send(JSON.stringify({ username }));
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        console.error('Room WebSocket error:', error);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        console.log('🔌 Room WebSocket disconnected');
        setConnected(false);
        setCurrentRoom(null);

        // 재연결 시도
        if (reconnectAttemptsRef.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
          console.log(`Reconnecting in ${delay}ms...`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        } else {
          setError('Failed to reconnect to room');
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setError('Failed to connect to room');
    }
  }, [roomId, username, setConnected, setError, setCurrentRoom, handleMessage]);

  /**
   * 연결 해제
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnected(false);
    setCurrentRoom(null);
  }, [setConnected, setCurrentRoom]);

  /**
   * 발화 상태 전송
   */
  const sendSpeakingStatus = useCallback((isSpeaking: boolean) => {
    sendMessage({
      type: 'speaking_status',
      is_speaking: isSpeaking,
    });
  }, [sendMessage]);

  /**
   * 채팅 메시지 전송
   */
  const sendChatMessage = useCallback((message: string) => {
    sendMessage({
      type: 'chat_message',
      message,
    });
  }, [sendMessage]);

  /**
   * 자동 연결/해제
   */
  useEffect(() => {
    if (roomId && username) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [roomId, username, connect, disconnect]);

  return {
    connect,
    disconnect,
    sendMessage,
    sendSpeakingStatus,
    sendChatMessage,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  };
}
