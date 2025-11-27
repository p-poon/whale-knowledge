'use client';

import { useState } from 'react';
import Link from 'next/link';
import DocumentUpload from '@/components/DocumentUpload';
import DocumentList from '@/components/DocumentList';
import ChatInterface from '@/components/ChatInterface';
import EvaluationDashboard from '@/components/EvaluationDashboard';
import StatsPanel from '@/components/StatsPanel';
import { Database, MessageSquare, BarChart3, FileText, Sparkles, Library } from 'lucide-react';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'documents' | 'query' | 'evaluation'>('documents');
  const [refreshKey, setRefreshKey] = useState(0);

  const tabs = [
    { id: 'documents' as const, label: 'Documents', icon: FileText },
    { id: 'query' as const, label: 'Query', icon: MessageSquare },
    { id: 'evaluation' as const, label: 'Evaluation', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <Database size={32} className="text-blue-500" />
                <h1 className="text-3xl font-bold text-gray-900">Whale Knowledge Base</h1>
              </div>
              <p className="text-gray-600 mt-2">RAG-powered document knowledge base with MCP integration</p>
            </div>


          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Stats Panel */}
        <div className="mb-8">
          <StatsPanel />
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="flex gap-4">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Icon size={20} />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'documents' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <DocumentUpload onSuccess={() => setRefreshKey(k => k + 1)} />
            </div>
            <div className="lg:col-span-2">
              <DocumentList refreshKey={refreshKey} />
            </div>
          </div>
        )}

        {activeTab === 'query' && (
          <div className="max-w-4xl mx-auto">
            <ChatInterface />
          </div>
        )}

        {activeTab === 'evaluation' && (
          <div>
            <EvaluationDashboard />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-gray-600">
          <p>Whale Knowledge Base - Powered by FastAPI, Pinecone, and Next.js</p>
        </div>
      </footer>
    </div>
  );
}
