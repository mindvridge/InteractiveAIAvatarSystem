/**
 * Rooms 페이지
 * 다중 사용자 Room 기능
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAppStore, Room } from '@/app/lib/store';
import { RoomList } from '@/app/components/RoomList/RoomList';
import { RoomView } from '@/app/components/RoomView/RoomView';

export default function RoomsPage() {
  const { currentRoom, setCurrentRoom, setCurrentUser } = useAppStore();
  const [currentUsername, setCurrentUsername] = useState<string>('');

  /**
   * Room 참여
   */
  const handleJoinRoom = (room: Room, username: string) => {
    setCurrentRoom(room);
    setCurrentUser({ user_id: '', username });
    setCurrentUsername(username);
    console.log('Joining room:', room.room_name, 'as', username);
  };

  /**
   * Room 나가기
   */
  const handleLeaveRoom = () => {
    setCurrentRoom(null);
    setCurrentUser(null);
    setCurrentUsername('');
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      {!currentRoom && (
        <div className="p-4">
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            ← 단일 사용자 모드
          </Link>
        </div>
      )}

      {currentRoom ? (
        <RoomView
          roomId={currentRoom.room_id}
          username={currentUsername}
          onLeaveRoom={handleLeaveRoom}
        />
      ) : (
        <RoomList onJoinRoom={handleJoinRoom} />
      )}
    </div>
  );
}
