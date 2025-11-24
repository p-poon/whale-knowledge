'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { listDocuments, deleteDocument, type Document } from '@/lib/api';
import { Trash2, FileText, Globe, FileIcon, Loader2 } from 'lucide-react';
import { format } from 'date-fns';

export default function DocumentList({ refreshKey }: { refreshKey?: number }) {
  const [page, setPage] = useState(1);
  const [industryFilter, setIndustryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const { data, error, mutate } = useSWR(
    ['documents', page, industryFilter, statusFilter, refreshKey],
    () => listDocuments(page, 20, industryFilter || undefined, statusFilter || undefined),
    { refreshInterval: 5000 } // Auto-refresh every 5 seconds
  );

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      await deleteDocument(id);
      mutate();
    } catch (err) {
      alert('Failed to delete document');
    }
  };

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'pdf':
        return <FileText size={18} className="text-red-500" />;
      case 'web':
        return <Globe size={18} className="text-blue-500" />;
      default:
        return <FileIcon size={18} className="text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      completed: 'bg-green-100 text-green-800',
      processing: 'bg-yellow-100 text-yellow-800',
      pending: 'bg-gray-100 text-gray-800',
      error: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`px-2 py-1 rounded text-xs ${colors[status] || colors.pending}`}>
        {status}
      </span>
    );
  };

  if (error) {
    return <div className="bg-red-100 text-red-700 p-4 rounded">Failed to load documents</div>;
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="animate-spin" size={32} />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <h2 className="text-2xl font-bold mb-4">Documents</h2>

        <div className="flex gap-4">
          <input
            type="text"
            placeholder="Filter by industry..."
            value={industryFilter}
            onChange={(e) => setIndustryFilter(e.target.value)}
            className="border rounded px-3 py-2 flex-1"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="pending">Pending</option>
            <option value="error">Error</option>
          </select>
        </div>
      </div>

      <div className="divide-y">
        {data.documents.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No documents found. Upload a PDF or scrape a URL to get started.
          </div>
        ) : (
          data.documents.map((doc: Document) => (
            <div key={doc.id} className="p-4 hover:bg-gray-50 flex items-center gap-4">
              <div className="flex-shrink-0">
                {getSourceIcon(doc.source_type)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-medium truncate">{doc.filename}</h3>
                  {getStatusBadge(doc.status)}
                </div>

                <div className="text-sm text-gray-500 space-y-1">
                  {doc.industry && <div>Industry: {doc.industry}</div>}
                  {doc.author && <div>Author: {doc.author}</div>}
                  <div>Chunks: {doc.chunk_count} | Created: {format(new Date(doc.created_at), 'MMM d, yyyy')}</div>
                </div>
              </div>

              <button
                onClick={() => handleDelete(doc.id)}
                className="text-red-500 hover:text-red-700 p-2"
                title="Delete document"
              >
                <Trash2 size={18} />
              </button>
            </div>
          ))
        )}
      </div>

      {data.total > 20 && (
        <div className="p-4 border-t flex items-center justify-between">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Previous
          </button>

          <span className="text-sm text-gray-600">
            Page {page} of {Math.ceil(data.total / 20)}
          </span>

          <button
            onClick={() => setPage(p => p + 1)}
            disabled={page >= Math.ceil(data.total / 20)}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
