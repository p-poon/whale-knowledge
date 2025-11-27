'use client';

import { useEffect, useState } from 'react';
import { getDocumentContent, type DocumentContent } from '@/lib/api';
import { Loader2, FileText, Globe, Calendar, User, Building2, Hash, ArrowLeft } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface DocumentViewerProps {
  documentId: number;
  onClose?: () => void;
}

export default function DocumentViewer({ documentId, onClose }: DocumentViewerProps) {
  const [content, setContent] = useState<DocumentContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadContent();
  }, [documentId]);

  const loadContent = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getDocumentContent(documentId);
      setContent(data as DocumentContent);
    } catch (err) {
      setError('Failed to load document content');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'pdf':
        return <FileText className="text-red-500" size={20} />;
      case 'web':
        return <Globe className="text-blue-500" size={20} />;
      default:
        return <FileText className="text-gray-500" size={20} />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-16">
        <Loader2 className="animate-spin" size={48} />
      </div>
    );
  }

  if (error || !content) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-lg">
        <h3 className="font-semibold mb-2">Error Loading Document</h3>
        <p>{error || 'Document not found'}</p>
        {onClose && (
          <button
            onClick={onClose}
            className="mt-4 px-4 py-2 bg-red-100 hover:bg-red-200 rounded"
          >
            Go Back
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4 flex-1">
            <div className="mt-1">
              {getSourceIcon(content.source_type)}
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold mb-2">{content.filename}</h1>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-blue-100">
                {content.source_type === 'web' && content.source_url && (
                  <div className="flex items-center gap-2">
                    <Globe size={14} />
                    <a
                      href={content.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline truncate"
                    >
                      {content.source_url}
                    </a>
                  </div>
                )}
                {content.industry && (
                  <div className="flex items-center gap-2">
                    <Building2 size={14} />
                    <span>{content.industry}</span>
                  </div>
                )}
                {content.author && (
                  <div className="flex items-center gap-2">
                    <User size={14} />
                    <span>{content.author}</span>
                  </div>
                )}
                {content.created_at && (
                  <div className="flex items-center gap-2">
                    <Calendar size={14} />
                    <span>{new Date(content.created_at).toLocaleDateString()}</span>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <Hash size={14} />
                  <span>{content.chunk_count} chunks</span>
                </div>
              </div>
            </div>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="ml-4 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg flex items-center gap-2 transition-colors"
            >
              <ArrowLeft size={16} />
              Back
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-8">
        <div className="prose prose-slate max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ node, ...props }) => <h1 className="text-3xl font-bold mt-8 mb-4 text-gray-900" {...props} />,
              h2: ({ node, ...props }) => <h2 className="text-2xl font-bold mt-6 mb-3 text-gray-800" {...props} />,
              h3: ({ node, ...props }) => <h3 className="text-xl font-semibold mt-4 mb-2 text-gray-700" {...props} />,
              h4: ({ node, ...props }) => <h4 className="text-lg font-semibold mt-3 mb-2 text-gray-700" {...props} />,
              p: ({ node, ...props }) => <p className="mb-4 text-gray-700 leading-relaxed" {...props} />,
              ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-4 space-y-1 text-gray-700" {...props} />,
              ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-4 space-y-1 text-gray-700" {...props} />,
              li: ({ node, ...props }) => <li className="ml-4" {...props} />,
              a: ({ node, ...props }) => <a className="text-blue-600 hover:underline" {...props} />,
              code: ({ node, className, children, ...props }) => {
                const isInline = !className;
                return isInline ? (
                  <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-red-600" {...props}>
                    {children}
                  </code>
                ) : (
                  <code className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono" {...props}>
                    {children}
                  </code>
                );
              },
              pre: ({ node, ...props }) => <pre className="mb-4 overflow-x-auto" {...props} />,
              blockquote: ({ node, ...props }) => (
                <blockquote className="border-l-4 border-blue-500 pl-4 italic my-4 text-gray-600" {...props} />
              ),
              table: ({ node, ...props }) => (
                <div className="overflow-x-auto mb-4">
                  <table className="min-w-full border-collapse border border-gray-300" {...props} />
                </div>
              ),
              th: ({ node, ...props }) => <th className="border border-gray-300 bg-gray-100 px-4 py-2 font-semibold text-left" {...props} />,
              td: ({ node, ...props }) => <td className="border border-gray-300 px-4 py-2" {...props} />,
            }}
          >
            {content.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
