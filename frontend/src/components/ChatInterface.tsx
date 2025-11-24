'use client';

import { useState } from 'react';
import { queryKnowledgeBase, submitFeedback, type QueryResult } from '@/lib/api';
import { Send, ThumbsUp, ThumbsDown, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export default function ChatInterface() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<QueryResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [queryText, setQueryText] = useState('');
  const [processingTime, setProcessingTime] = useState(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    setResults([]);

    try {
      const response = await queryKnowledgeBase(query, 5);
      setResults(response.results);
      setQueryText(response.query);
      setProcessingTime(response.processing_time_ms);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (feedback: 'positive' | 'negative') => {
    try {
      const docIds = results.map(r => r.document_id);
      await submitFeedback(queryText, feedback, docIds);
      alert('Feedback submitted!');
    } catch (err) {
      alert('Failed to submit feedback');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow h-full flex flex-col">
      <div className="p-6 border-b">
        <h2 className="text-2xl font-bold">Query Knowledge Base</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {results.length === 0 && !loading && !error && (
          <div className="text-center text-gray-500 py-12">
            Ask a question to search the knowledge base
          </div>
        )}

        {error && (
          <div className="bg-red-100 text-red-700 p-4 rounded">{error}</div>
        )}

        {queryText && results.length > 0 && (
          <>
            <div className="bg-blue-50 p-4 rounded">
              <div className="font-medium mb-2">Query: {queryText}</div>
              <div className="text-sm text-gray-600">
                Found {results.length} results in {processingTime.toFixed(2)}ms
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => handleFeedback('positive')}
                  className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                >
                  <ThumbsUp size={16} />
                  Helpful
                </button>
                <button
                  onClick={() => handleFeedback('negative')}
                  className="flex items-center gap-1 px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
                >
                  <ThumbsDown size={16} />
                  Not Helpful
                </button>
              </div>
            </div>

            <div className="space-y-4">
              {results.map((result, idx) => (
                <div key={result.chunk_id} className="border rounded-lg p-4 hover:shadow-md transition">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="font-medium text-lg">
                        Result {idx + 1} - {result.metadata.filename}
                      </div>
                      <div className="text-sm text-gray-500 flex gap-4">
                        <span>Score: {(result.score * 100).toFixed(1)}%</span>
                        <span>Source: {result.metadata.source_type}</span>
                        {result.metadata.industry && <span>Industry: {result.metadata.industry}</span>}
                      </div>
                    </div>
                    <div className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      Chunk {result.metadata.chunk_index}
                    </div>
                  </div>

                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown>{result.content}</ReactMarkdown>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="animate-spin" size={32} />
          </div>
        )}
      </div>

      <div className="p-6 border-t">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about your documents..."
            className="flex-1 border rounded px-4 py-2"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400 flex items-center gap-2"
          >
            {loading ? (
              <Loader2 className="animate-spin" size={18} />
            ) : (
              <>
                <Send size={18} />
                Query
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
