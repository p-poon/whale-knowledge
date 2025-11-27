'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { getGeneratedContent, GeneratedContent } from '@/lib/api';
import { ArrowLeft, Calendar, DollarSign, FileText, Loader2, Download, Copy, Check } from 'lucide-react';

export default function ContentViewerPage() {
  const params = useParams();
  const router = useRouter();
  const contentId = parseInt(params.id as string);

  const [content, setContent] = useState<GeneratedContent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadContent();
  }, [contentId]);

  const loadContent = async () => {
    setIsLoading(true);
    try {
      const data = await getGeneratedContent(contentId, true);
      setContent(data);
    } catch (error) {
      console.error('Failed to load content:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyHTML = () => {
    if (content) {
      navigator.clipboard.writeText(content.content_html);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadHTML = () => {
    if (content) {
      const blob = new Blob([content.content_html], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${content.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.html`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading content...</p>
        </div>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Content Not Found</h2>
          <p className="text-gray-600 mb-6">The requested content could not be found.</p>
          <Link
            href="/generated"
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Library
          </Link>
        </div>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/generated"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Library
          </Link>

          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <span className="px-3 py-1 bg-blue-100 text-blue-700 text-sm font-medium rounded-full capitalize">
                  {content.content_type}
                </span>
                <span className="px-3 py-1 bg-purple-100 text-purple-700 text-sm font-medium rounded-full">
                  {content.llm_provider === 'anthropic' ? 'Claude' : 'GPT'} - {content.llm_model}
                </span>
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{content.title}</h1>
              <p className="text-gray-600">{content.topic}</p>
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleCopyHTML}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                {copied ? 'Copied!' : 'Copy HTML'}
              </button>
              <button
                onClick={handleDownloadHTML}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Download className="w-5 h-5" />
                Download
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow-sm p-8">
              <div
                className="prose prose-slate max-w-none"
                dangerouslySetInnerHTML={{ __html: content.content_html }}
              />
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Metadata */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Metadata</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <div className="flex items-center gap-2 text-gray-500 mb-1">
                    <Calendar className="w-4 h-4" />
                    Created
                  </div>
                  <p className="text-gray-900">{formatDate(content.created_at)}</p>
                </div>

                {content.cost_estimate && (
                  <div>
                    <div className="flex items-center gap-2 text-gray-500 mb-1">
                      <DollarSign className="w-4 h-4" />
                      Cost
                    </div>
                    <p className="text-gray-900">${content.cost_estimate.toFixed(4)}</p>
                  </div>
                )}

                {content.token_usage && (
                  <div>
                    <div className="text-gray-500 mb-1">Token Usage</div>
                    <div className="space-y-1">
                      <p className="text-gray-900">
                        Input: {content.token_usage.input?.toLocaleString() || 0}
                      </p>
                      <p className="text-gray-900">
                        Output: {content.token_usage.output?.toLocaleString() || 0}
                      </p>
                      <p className="font-medium text-gray-900">
                        Total: {content.token_usage.total?.toLocaleString() || 0}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Source Documents */}
            {content.source_documents && content.source_documents.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Source Documents</h3>
                <div className="space-y-2">
                  {content.source_documents.map((doc) => (
                    <div
                      key={doc.document_id}
                      className="p-3 bg-gray-50 rounded-lg text-sm"
                    >
                      <p className="font-medium text-gray-900 truncate">{doc.filename}</p>
                      {(doc.industry || doc.author) && (
                        <p className="text-gray-500 text-xs mt-1">
                          {[doc.industry, doc.author].filter(Boolean).join(' • ')}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Generation Parameters */}
            {content.generation_params && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Settings Used</h3>
                <div className="space-y-2 text-sm">
                  {content.generation_params.style && (
                    <div>
                      <span className="text-gray-500">Style:</span>{' '}
                      <span className="text-gray-900 capitalize">{content.generation_params.style}</span>
                    </div>
                  )}
                  {content.generation_params.tone && (
                    <div>
                      <span className="text-gray-500">Tone:</span>{' '}
                      <span className="text-gray-900 capitalize">{content.generation_params.tone}</span>
                    </div>
                  )}
                  {content.generation_params.audience && (
                    <div>
                      <span className="text-gray-500">Audience:</span>{' '}
                      <span className="text-gray-900 capitalize">{content.generation_params.audience}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
