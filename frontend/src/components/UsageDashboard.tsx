'use client';

import React, { useState, useEffect } from 'react';
import {
  getUsageSummary,
  getCostEstimate,
  getDailyStats,
  getTopDocumentsByUsage,
  UsageStatsResponse,
  CostEstimate,
  DailyStats,
} from '@/lib/api';

interface UsageDashboardProps {
  className?: string;
}

export default function UsageDashboard({ className = '' }: UsageDashboardProps) {
  const [usageStats, setUsageStats] = useState<UsageStatsResponse | null>(null);
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [topDocuments, setTopDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<number>(30);
  const [selectedService, setSelectedService] = useState<string>('');

  useEffect(() => {
    loadData();
  }, [selectedPeriod, selectedService]);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - selectedPeriod);

      const [stats, cost, daily, docs] = await Promise.all([
        getUsageSummary(
          selectedService || undefined,
          startDate.toISOString(),
          endDate.toISOString()
        ),
        getCostEstimate(startDate.toISOString(), endDate.toISOString()),
        getDailyStats(selectedPeriod, selectedService || undefined),
        getTopDocumentsByUsage(10, selectedService || undefined, selectedPeriod),
      ]);

      setUsageStats(stats);
      setCostEstimate(cost);
      setDailyStats(daily.data);
      setTopDocuments(docs.documents);
    } catch (err) {
      console.error('Error loading usage data:', err);
      setError('Failed to load usage data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4,
    }).format(amount);
  };

  const formatNumber = (num: number | undefined) => {
    if (num === undefined || num === null) return '0';
    return new Intl.NumberFormat('en-US').format(num);
  };

  if (loading) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
          <button
            onClick={loadData}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`p-6 space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">API Usage & Costs</h2>
        <div className="flex gap-4">
          {/* Period Selector */}
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>

          {/* Service Filter */}
          <select
            value={selectedService}
            onChange={(e) => setSelectedService(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Services</option>
            <option value="jina">JINA</option>
            <option value="pinecone">Pinecone</option>
          </select>
        </div>
      </div>

      {/* Cost Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Cost */}
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-6 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm font-medium">Total Estimated Cost</p>
              <p className="text-3xl font-bold mt-2">
                {costEstimate ? formatCurrency(costEstimate.total_cost) : '$0.00'}
              </p>
            </div>
            <div className="bg-white bg-opacity-20 rounded-full p-3">
              <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd" />
              </svg>
            </div>
          </div>
        </div>

        {/* JINA Cost */}
        <div className="bg-white rounded-lg p-6 shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">JINA API Cost</p>
              <p className="text-2xl font-bold text-gray-900 mt-2">
                {costEstimate ? formatCurrency(costEstimate.jina_cost) : '$0.00'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {costEstimate ? formatNumber(costEstimate.jina_tokens_used) : '0'} tokens
              </p>
            </div>
            <div className="bg-purple-100 rounded-full p-3">
              <svg className="w-8 h-8 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </div>
          </div>
        </div>

        {/* Pinecone Cost */}
        <div className="bg-white rounded-lg p-6 shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">Pinecone Cost</p>
              <p className="text-2xl font-bold text-gray-900 mt-2">
                {costEstimate
                  ? formatCurrency(costEstimate.pinecone_read_cost + costEstimate.pinecone_write_cost)
                  : '$0.00'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {costEstimate ? formatNumber(costEstimate.pinecone_read_units) : '0'} reads /{' '}
                {costEstimate ? formatNumber(costEstimate.pinecone_write_units) : '0'} writes
              </p>
            </div>
            <div className="bg-green-100 rounded-full p-3">
              <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M3 12v3c0 1.657 3.134 3 7 3s7-1.343 7-3v-3c0 1.657-3.134 3-7 3s-7-1.343-7-3z" />
                <path d="M3 7v3c0 1.657 3.134 3 7 3s7-1.343 7-3V7c0 1.657-3.134 3-7 3S3 8.657 3 7z" />
                <path d="M17 5c0 1.657-3.134 3-7 3S3 6.657 3 5s3.134-3 7-3 7 1.343 7 3z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Usage Summary by Operation */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Usage by Operation</h3>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Service
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Operation
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Calls
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Success Rate
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Duration
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Metrics
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {usageStats?.summaries.map((summary, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          summary.service === 'jina'
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {summary.service.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {summary.operation}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
                      {formatNumber(summary.total_calls)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right">
                      <span
                        className={`${
                          ((summary.successful_calls / summary.total_calls) * 100) >= 95
                            ? 'text-green-600'
                            : 'text-yellow-600'
                        } font-medium`}
                      >
                        {((summary.successful_calls / summary.total_calls) * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
                      {summary.avg_duration_ms ? `${summary.avg_duration_ms.toFixed(0)}ms` : '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 text-right">
                      {summary.service === 'jina'
                        ? `${formatNumber(summary.total_jina_tokens)} tokens`
                        : `${formatNumber(summary.total_read_units)} R / ${formatNumber(
                            summary.total_write_units
                          )} W`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Top Documents by Usage */}
      {topDocuments.length > 0 && (
        <div className="bg-white rounded-lg shadow border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Top Documents by API Usage</h3>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {topDocuments.map((doc, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatNumber(doc.api_calls)} API calls
                      {doc.jina_tokens && ` • ${formatNumber(doc.jina_tokens)} tokens`}
                      {doc.read_units && ` • ${formatNumber(doc.read_units)} reads`}
                      {doc.write_units && ` • ${formatNumber(doc.write_units)} writes`}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-800 text-sm font-semibold">
                      {idx + 1}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm text-gray-600">Total API Calls</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {usageStats ? formatNumber(usageStats.total_api_calls) : '0'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Period</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{selectedPeriod} days</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Services</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {selectedService || 'All'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Updated</p>
            <p className="text-sm text-gray-900 mt-1">
              {new Date().toLocaleTimeString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
