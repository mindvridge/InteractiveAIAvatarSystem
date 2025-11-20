/**
 * Recordings 페이지
 * 녹화된 세션 목록 및 관리
 */

'use client';

import Link from 'next/link';
import { RecordingsList } from '@/app/components/RecordingsList/RecordingsList';

export default function RecordingsPage() {
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="p-4">
        <Link
          href="/rooms"
          className="inline-flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        >
          ← Back to Rooms
        </Link>
      </div>

      <div className="max-w-6xl mx-auto">
        <RecordingsList />
      </div>
    </div>
  );
}
