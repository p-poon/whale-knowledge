'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { listGeneratedContent, GeneratedContent, ContentType } from '@/lib/api';
import { FileText, Newspaper, PenTool, Calendar, DollarSign, Loader2, Plus } from 'lucide-react';

export default function GeneratedContentPage() {
  const [content, setContent] = useState<GeneratedContent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<ContentType | 'all'>('all');

  useEffect(() => {
    loadContent();
  }, [filter]);

  const loadContent = async () => {
    setIsLoading(true);
    try {
      const response = await listGeneratedContent(
        filter === 'all' ? undefined : filter,
        50,
        0
      );
      setContent(response.content);
    } catch (error) {
      console.error('Failed to load content:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getIcon = (type: ContentType) => {
    switch (type) {
      case 'whitepaper':
        return FileText;
      case 'article':
        return Newspaper;
      case 'blog':
        return PenTool;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Generated Content</h1>
              <p className="mt-2 text-gray-600">
                Browse and manage your AI-generated white papers, articles, and blogs
              </p>
            </div>
            <Link
              href="/generate"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
            >
              <Plus className="w-5 h-5" />
              Generate New
            </Link>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-700">Filter by type:</span>
            <div className="flex gap-2">
              {(['all', 'whitepaper', 'article', 'blog'] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => setFilter(type)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filter === type
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {type === 'all' ? 'All' : type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content Grid */}
        {isLoading ? (
          <div className="text-center py-12">
            <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600">Loading content...</p>
          </div>
        ) : content.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No content yet</h3>
            <p className="text-gray-600 mb-6">
              Start by generating your first white paper, article, or blog post
            </p>
            <Link
              href="/generate"
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
            >
              <Plus className="w-5 h-5" />
              Generate Content
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {content.map((item) => {
              const Icon = getIcon(item.content_type);
              return (
                <Link
                  key={item.id}
                  href={`/generated/${item.id}`}
                  className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow overflow-hidden"
                >
                  <div className="p-6">
                    <div className="flex items-start gap-3 mb-4">
                      <Icon className="w-6 h-6 text-blue-600 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-gray-900 line-clamp-2 mb-1">
                          {item.title}
                        </h3>
                        <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded capitalize">
                          {item.content_type}
                        </span>
                      </div>
                    </div>

                    <p className="text-sm text-gray-600 line-clamp-2 mb-4">{item.topic}</p>

                    <div className="space-y-2 text-sm text-gray-500">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        {formatDate(item.created_at)}
                      </div>

                      {item.cost_estimate && (
                        <div className="flex items-center gap-2">
                          <DollarSign className="w-4 h-4" />
                          ${item.cost_estimate.toFixed(4)}
                        </div>
                      )}

                      <div className="flex items-center gap-2">
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                          {item.llm_provider === 'anthropic' ? 'Claude' : 'GPT'}
                        </span>
                        {item.token_usage && (
                          <span className="text-xs text-gray-500">
                            {item.token_usage.total?.toLocaleString()} tokens
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
                    <span className="text-sm text-blue-600 font-medium">View Content →</span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
