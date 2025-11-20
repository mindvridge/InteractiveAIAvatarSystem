/**
 * Room 뷰 컴포넌트
 * 현재 참여 중인 Room 표시
 */

'use client';

import { useEffect, useState } from 'react';
import { useAppStore } from '@/app/lib/store';
import { useRoomWebSocket } from '@/app/lib/websocket/room-websocket';
import { AudioRecorder } from '../AudioRecorder/AudioRecorder';
import { AvatarDisplay } from '../AvatarDisplay/AvatarDisplay';
import { ChatInterface } from '../ChatInterface/ChatInterface';
import { RecordingControls } from '../RecordingControls/RecordingControls';

interface RoomViewProps {
  roomId: string;
  username: string;
  onLeaveRoom: () => void;
}

export function RoomView({ roomId, username, onLeaveRoom }: RoomViewProps) {
  const { currentRoom, isRecording, setCurrentRoom } = useAppStore();
  const [isRoomRecording, setIsRoomRecording] = useState(false);

  const {
    sendSpeakingStatus,
    sendChatMessage,
    isConnected,
  } = useRoomWebSocket(roomId, username);

  /**
   * Room 녹화 상태 업데이트
   */
  const handleRecordingStateChange = (recording: boolean) => {
    setIsRoomRecording(recording);
    if (currentRoom) {
      setCurrentRoom({ ...currentRoom, is_recording: recording });
    }
  };

  /**
   * 초기 녹화 상태 설정
   */
  useEffect(() => {
    if (currentRoom) {
      setIsRoomRecording(currentRoom.is_recording);
    }
  }, [currentRoom]);

  /**
   * 녹음 상태 변경 시 발화 상태 전송
   */
  useEffect(() => {
    sendSpeakingStatus(isRecording);
  }, [isRecording, sendSpeakingStatus]);

  if (!currentRoom) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="text-4xl mb-4">⏳</div>
          <p className="text-gray-500">Connecting to room...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{currentRoom.room_name}</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
              {' • '}
              👤 {username}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Recording Controls */}
            <RecordingControls
              roomId={roomId}
              isRecording={isRoomRecording}
              onRecordingStateChange={handleRecordingStateChange}
            />

            <button
              onClick={onLeaveRoom}
              className="px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              Leave Room
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Users List */}
        <div className="w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 p-4 overflow-y-auto">
          <h2 className="font-semibold mb-4">
            Users ({currentRoom.user_count}/{currentRoom.max_users})
          </h2>
          <div className="space-y-2">
            {currentRoom.users.map((user) => (
              <div
                key={user.user_id}
                className="p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${user.is_speaking ? 'bg-green-500' : 'bg-gray-300'}`} />
                  <span className="font-medium">{user.username}</span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {new Date(user.joined_at).toLocaleTimeString()}
                </p>
              </div>
            ))}
          </div>

          {/* Recording Status */}
          {currentRoom.is_recording && (
            <div className="mt-6 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                <span className="text-sm font-semibold">Recording</span>
              </div>
            </div>
          )}
        </div>

        {/* Center: Avatar & Controls */}
        <div className="flex-1 flex flex-col">
          {/* Avatar Display */}
          <div className="flex-1 flex items-center justify-center p-8">
            <AvatarDisplay />
          </div>

          {/* Audio Recorder */}
          <div className="p-6 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
            <AudioRecorder />
          </div>
        </div>

        {/* Right: Chat */}
        <div className="w-96 border-l border-gray-200 dark:border-gray-700 flex flex-col">
          <div className="flex-1 overflow-hidden">
            <ChatInterface onSendMessage={sendChatMessage} />
          </div>
        </div>
      </div>
    </div>
  );
}
