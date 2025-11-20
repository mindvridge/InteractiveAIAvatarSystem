/**
 * Zustand 상태 관리 스토어
 * 애플리케이션의 전역 상태 관리
 */

import { create } from 'zustand';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AppState {
  // WebSocket 연결 상태
  isConnected: boolean;
  setConnected: (connected: boolean) => void;

  // 처리 상태
  isProcessing: boolean;
  processingStage: 'idle' | 'stt' | 'llm' | 'tts' | 'lipsync';
  setProcessing: (processing: boolean, stage?: 'idle' | 'stt' | 'llm' | 'tts' | 'lipsync') => void;

  // 대화 메시지
  messages: Message[];
  addMessage: (message: Message) => void;
  clearMessages: () => void;

  // 현재 응답 텍스트
  currentTranscription: string;
  setCurrentTranscription: (text: string) => void;

  currentResponse: string;
  setCurrentResponse: (text: string) => void;

  // 오디오 응답
  audioUrl: string | null;
  setAudioUrl: (url: string | null) => void;

  // 비디오 응답
  videoUrl: string | null;
  setVideoUrl: (url: string | null) => void;

  // 에러
  error: string | null;
  setError: (error: string | null) => void;

  // 음성 녹음 상태
  isRecording: boolean;
  setRecording: (recording: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // WebSocket 연결 상태
  isConnected: false,
  setConnected: (connected) => set({ isConnected: connected }),

  // 처리 상태
  isProcessing: false,
  processingStage: 'idle',
  setProcessing: (processing, stage = 'idle') =>
    set({ isProcessing: processing, processingStage: stage }),

  // 대화 메시지
  messages: [],
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  clearMessages: () => set({ messages: [] }),

  // 현재 텍스트
  currentTranscription: '',
  setCurrentTranscription: (text) => set({ currentTranscription: text }),

  currentResponse: '',
  setCurrentResponse: (text) => set({ currentResponse: text }),

  // 오디오 URL
  audioUrl: null,
  setAudioUrl: (url) => set({ audioUrl: url }),

  // 비디오 URL
  videoUrl: null,
  setVideoUrl: (url) => set({ videoUrl: url }),

  // 에러
  error: null,
  setError: (error) => set({ error }),

  // 녹음 상태
  isRecording: false,
  setRecording: (recording) => set({ isRecording: recording }),
}));
