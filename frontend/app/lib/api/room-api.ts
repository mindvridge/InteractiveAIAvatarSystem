/**
 * Room API 클라이언트
 * REST API를 통한 Room 관리
 */

import { Room } from '../store';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface CreateRoomRequest {
  room_name: string;
  max_users?: number;
}

export interface RoomListResponse {
  rooms: Room[];
  stats: {
    total_rooms: number;
    total_users: number;
  };
}

/**
 * Room 목록 조회
 */
export async function getRooms(): Promise<RoomListResponse> {
  const response = await fetch(`${API_BASE_URL}/rooms`);

  if (!response.ok) {
    throw new Error('Failed to fetch rooms');
  }

  return response.json();
}

/**
 * Room 생성
 */
export async function createRoom(data: CreateRoomRequest): Promise<Room> {
  const params = new URLSearchParams();
  params.append('room_name', data.room_name);
  if (data.max_users) {
    params.append('max_users', data.max_users.toString());
  }

  const response = await fetch(`${API_BASE_URL}/rooms?${params.toString()}`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('Failed to create room');
  }

  const result = await response.json();
  return result.room;
}

/**
 * Room 상세 정보 조회
 */
export async function getRoom(roomId: string): Promise<Room> {
  const response = await fetch(`${API_BASE_URL}/rooms/${roomId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch room');
  }

  const result = await response.json();
  return result.room;
}

/**
 * Room 삭제
 */
export async function deleteRoom(roomId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/rooms/${roomId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete room');
  }
}
