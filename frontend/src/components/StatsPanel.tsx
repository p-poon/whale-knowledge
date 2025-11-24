'use client';

import useSWR from 'swr';
import { getStats, type Stats } from '@/lib/api';
import { FileText, Database, CheckCircle, Loader2 } from 'lucide-react';

export default function StatsPanel() {
  const { data, error } = useSWR<Stats>('stats', getStats, {
    refreshInterval: 5000,
  });

  if (error) {
    return <div className="bg-red-100 text-red-700 p-4 rounded">Failed to load stats</div>;
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="animate-spin" size={32} />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-gray-600">Total Documents</div>
            <div className="text-3xl font-bold text-blue-600">{data.total_documents}</div>
          </div>
          <FileText size={32} className="text-blue-400" />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-gray-600">Total Chunks</div>
            <div className="text-3xl font-bold text-green-600">{data.total_chunks}</div>
          </div>
          <Database size={32} className="text-green-400" />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-gray-600">Completed</div>
            <div className="text-3xl font-bold text-purple-600">
              {data.documents_by_status?.completed || 0}
            </div>
          </div>
          <CheckCircle size={32} className="text-purple-400" />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-gray-600">Processing</div>
            <div className="text-3xl font-bold text-yellow-600">
              {data.documents_by_status?.processing || 0}
            </div>
          </div>
          <Loader2 size={32} className="text-yellow-400" />
        </div>
      </div>
    </div>
  );
}
