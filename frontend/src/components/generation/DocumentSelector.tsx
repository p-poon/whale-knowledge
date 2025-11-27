'use client';

import { useState, useEffect } from 'react';
import { ContentType, SuggestedDocument, suggestDocuments, listDocuments, Document } from '@/lib/api';
import { Search, Sparkles, CheckCircle2, Circle, Loader2 } from 'lucide-react';

interface DocumentSelectorProps {
  topic: string;
  onTopicChange: (topic: string) => void;
  selectedDocuments: number[];
  onDocumentsChange: (documents: number[]) => void;
  contentType: ContentType;
}

export default function DocumentSelector({
  topic,
  onTopicChange,
  selectedDocuments,
  onDocumentsChange,
  contentType,
}: DocumentSelectorProps) {
  const [suggestedDocs, setSuggestedDocs] = useState<SuggestedDocument[]>([]);
  const [allDocuments, setAllDocuments] = useState<Document[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Load all documents
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const response = await listDocuments(1, 100);
        setAllDocuments(response.documents);
      } catch (error) {
        console.error('Failed to load documents:', error);
      } finally {
        setIsLoadingDocs(false);
      }
    };
    loadDocuments();
  }, []);

  const handleGetSuggestions = async () => {
    if (topic.length < 10) return;

    setIsLoadingSuggestions(true);
    try {
      const response = await suggestDocuments(topic, contentType, 10);
      setSuggestedDocs(response.suggested_documents);
      setShowSuggestions(true);

      // Auto-select top 5 suggested documents
      const topDocs = response.suggested_documents.slice(0, 5).map((d) => d.document_id);
      onDocumentsChange(Array.from(new Set([...selectedDocuments, ...topDocs])));
    } catch (error) {
      console.error('Failed to get suggestions:', error);
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  const toggleDocument = (docId: number) => {
    if (selectedDocuments.includes(docId)) {
      onDocumentsChange(selectedDocuments.filter((id) => id !== docId));
    } else {
      onDocumentsChange([...selectedDocuments, docId]);
    }
  };

  const getDocumentId = (doc: SuggestedDocument | Document): number => {
    return 'document_id' in doc ? doc.document_id : doc.id;
  };

  const filteredDocuments = allDocuments.filter((doc) =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const displayDocs = showSuggestions && suggestedDocs.length > 0 ? suggestedDocs : filteredDocuments;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Topic & Documents</h2>
        <p className="text-gray-600">Describe your topic and select relevant documents</p>
      </div>

      {/* Topic Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Topic *
        </label>
        <textarea
          value={topic}
          onChange={(e) => onTopicChange(e.target.value)}
          placeholder="Describe the topic for your content... (minimum 10 characters)"
          rows={4}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="mt-1 text-sm text-gray-500">
          {topic.length} / 10 characters minimum
        </p>
      </div>

      {/* AI Suggestions Button */}
      <div className="flex items-center justify-between">
        <button
          onClick={handleGetSuggestions}
          disabled={topic.length < 10 || isLoadingSuggestions}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoadingSuggestions ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Getting AI Suggestions...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              Get AI Document Suggestions
            </>
          )}
        </button>

        {suggestedDocs.length > 0 && (
          <button
            onClick={() => setShowSuggestions(!showSuggestions)}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            {showSuggestions ? 'Show All Documents' : 'Show Suggestions'}
          </button>
        )}
      </div>

      {/* Search */}
      {!showSuggestions && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search documents..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      )}

      {/* Selected Count */}
      <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <span className="text-sm font-medium text-blue-900">
          {selectedDocuments.length} document{selectedDocuments.length !== 1 ? 's' : ''} selected
        </span>
        {selectedDocuments.length > 0 && (
          <button
            onClick={() => onDocumentsChange([])}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Document List */}
      <div className="border border-gray-200 rounded-lg divide-y divide-gray-200 max-h-96 overflow-y-auto">
        {isLoadingDocs ? (
          <div className="p-8 text-center text-gray-500">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />
            Loading documents...
          </div>
        ) : displayDocs.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No documents found. Upload some documents first.
          </div>
        ) : (
          displayDocs.map((doc) => {
            const docId = getDocumentId(doc);
            const isSelected = selectedDocuments.includes(docId);
            const isSuggested = 'relevance_score' in doc;

            return (
              <button
                key={docId}
                onClick={() => toggleDocument(docId)}
                className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${
                  isSelected ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-1">
                    {isSelected ? (
                      <CheckCircle2 className="w-5 h-5 text-blue-600" />
                    ) : (
                      <Circle className="w-5 h-5 text-gray-300" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-gray-900 truncate">
                        {doc.filename}
                      </h4>
                      {isSuggested && (
                        <span className="flex items-center gap-1 px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                          <Sparkles className="w-3 h-3" />
                          {Math.round((doc as SuggestedDocument).relevance_score * 100)}% match
                        </span>
                      )}
                    </div>

                    <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
                      {doc.industry && <span>{doc.industry}</span>}
                      {doc.author && <span>{doc.author}</span>}
                      <span>{doc.chunk_count} chunks</span>
                    </div>

                    {isSuggested && (doc as SuggestedDocument).relevance_explanation && (
                      <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                        {(doc as SuggestedDocument).relevance_explanation}
                      </p>
                    )}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>

      {selectedDocuments.length === 0 && (
        <div className="text-center p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            Please select at least one document to continue
          </p>
        </div>
      )}
    </div>
  );
}
