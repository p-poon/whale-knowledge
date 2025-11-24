'use client';

import useSWR from 'swr';
import { getEvaluationMetrics, type EvaluationMetrics } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Loader2 } from 'lucide-react';

export default function EvaluationDashboard() {
  const { data, error } = useSWR<EvaluationMetrics>('evaluation-metrics', getEvaluationMetrics, {
    refreshInterval: 10000, // Refresh every 10 seconds
  });

  if (error) {
    return <div className="bg-red-100 text-red-700 p-4 rounded">Failed to load metrics</div>;
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="animate-spin" size={32} />
      </div>
    );
  }

  const chartData = [
    {
      name: 'Precision',
      value: data.avg_precision ? (data.avg_precision * 100) : 0,
    },
    {
      name: 'Recall',
      value: data.avg_recall ? (data.avg_recall * 100) : 0,
    },
    {
      name: 'Semantic Similarity',
      value: data.avg_semantic_similarity ? (data.avg_semantic_similarity * 100) : 0,
    },
  ];

  const feedbackData = [
    {
      name: 'Positive',
      value: data.positive_feedback_rate ? (data.positive_feedback_rate * 100) : 0,
    },
    {
      name: 'Negative',
      value: data.negative_feedback_rate ? (data.negative_feedback_rate * 100) : 0,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-6">Evaluation Metrics</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-blue-50 p-4 rounded">
            <div className="text-sm text-gray-600">Total Queries</div>
            <div className="text-3xl font-bold text-blue-600">{data.total_queries}</div>
          </div>

          <div className="bg-green-50 p-4 rounded">
            <div className="text-sm text-gray-600">Avg Precision</div>
            <div className="text-3xl font-bold text-green-600">
              {data.avg_precision ? `${(data.avg_precision * 100).toFixed(1)}%` : 'N/A'}
            </div>
          </div>

          <div className="bg-purple-50 p-4 rounded">
            <div className="text-sm text-gray-600">Avg Recall</div>
            <div className="text-3xl font-bold text-purple-600">
              {data.avg_recall ? `${(data.avg_recall * 100).toFixed(1)}%` : 'N/A'}
            </div>
          </div>
        </div>

        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4">Retrieval Quality Metrics</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(value) => `${Number(value).toFixed(1)}%`} />
              <Legend />
              <Bar dataKey="value" fill="#3b82f6" name="Score %" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {(data.positive_feedback_rate !== null || data.negative_feedback_rate !== null) && (
          <div>
            <h3 className="text-lg font-semibold mb-4">User Feedback</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={feedbackData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value) => `${Number(value).toFixed(1)}%`} />
                <Legend />
                <Bar dataKey="value" fill="#10b981" name="Feedback Rate %" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
