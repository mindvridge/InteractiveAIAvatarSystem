/**
 * Room 목록 컴포넌트
 * 사용 가능한 Room 목록 표시 및 생성
 */

'use client';

import { useEffect, useState } from 'react';
import { useAppStore, Room } from '@/app/lib/store';
import { getRooms, createRoom } from '@/app/lib/api/room-api';

interface RoomListProps {
  onJoinRoom: (room: Room, username: string) => void;
}

export function RoomList({ onJoinRoom }: RoomListProps) {
  const { availableRooms, setAvailableRooms } = useAppStore();
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newRoomName, setNewRoomName] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState<string | null>(null);

  /**
   * Room 목록 로드
   */
  const loadRooms = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getRooms();
      setAvailableRooms(response.rooms);
    } catch (err) {
      setError('Failed to load rooms');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Room 생성
   */
  const handleCreateRoom = async () => {
    if (!newRoomName.trim()) {
      setError('Room name is required');
      return;
    }

    setIsCreating(true);
    setError(null);

    try {
      const room = await createRoom({ room_name: newRoomName, max_users: 10 });
      setNewRoomName('');
      await loadRooms();
      console.log('✅ Room created:', room);
    } catch (err) {
      setError('Failed to create room');
      console.error(err);
    } finally {
      setIsCreating(false);
    }
  };

  /**
   * Room 참여
   */
  const handleJoinRoom = (room: Room) => {
    if (!username.trim()) {
      setError('Username is required');
      return;
    }

    onJoinRoom(room, username);
  };

  /**
   * 초기 로드
   */
  useEffect(() => {
    loadRooms();

    // 자동 새로고침 (10초마다)
    const interval = setInterval(loadRooms, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">🏠 AI Avatar Rooms</h1>

      {/* Username Input */}
      <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <label className="block text-sm font-medium mb-2">Your Name</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Enter your name..."
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Create Room */}
      <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <h2 className="text-lg font-semibold mb-3">Create New Room</h2>
        <div className="flex gap-3">
          <input
            type="text"
            value={newRoomName}
            onChange={(e) => setNewRoomName(e.target.value)}
            placeholder="Room name..."
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isCreating}
          />
          <button
            onClick={handleCreateRoom}
            disabled={isCreating || !newRoomName.trim()}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isCreating ? 'Creating...' : 'Create'}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Room List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Available Rooms</h2>
          <button
            onClick={loadRooms}
            disabled={isLoading}
            className="px-4 py-2 text-sm bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50"
          >
            {isLoading ? '⏳ Loading...' : '🔄 Refresh'}
          </button>
        </div>

        {isLoading && availableRooms.length === 0 ? (
          <div className="text-center py-12 text-gray-500">Loading rooms...</div>
        ) : availableRooms.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No rooms available. Create one!
          </div>
        ) : (
          <div className="grid gap-4">
            {availableRooms.map((room) => (
              <div
                key={room.room_id}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 dark:hover:border-blue-500 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-lg">{room.room_name}</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      👥 {room.user_count} / {room.max_users} users
                      {room.is_recording && ' • 🔴 Recording'}
                    </p>
                  </div>
                  <button
                    onClick={() => handleJoinRoom(room)}
                    disabled={!username.trim() || room.user_count >= room.max_users}
                    className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                  >
                    {room.user_count >= room.max_users ? 'Full' : 'Join'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
