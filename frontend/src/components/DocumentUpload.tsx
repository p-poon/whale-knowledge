'use client';

import { useState } from 'react';
import { uploadPDF, scrapeURL } from '@/lib/api';
import { Upload, Link as LinkIcon, Loader2 } from 'lucide-react';

export default function DocumentUpload({ onSuccess }: { onSuccess?: () => void }) {
  const [uploadType, setUploadType] = useState<'pdf' | 'url'>('pdf');
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState('');
  const [industry, setIndustry] = useState('');
  const [author, setAuthor] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      if (uploadType === 'pdf') {
        if (!file) {
          setError('Please select a PDF file');
          setLoading(false);
          return;
        }
        const result = await uploadPDF(file, industry, author);
        setSuccess(`Successfully uploaded: ${result.filename}`);
        setFile(null);
      } else {
        if (!url) {
          setError('Please enter a URL');
          setLoading(false);
          return;
        }
        const result = await scrapeURL(url, industry, author);
        setSuccess(`Successfully scraped: ${url}`);
        setUrl('');
      }

      setIndustry('');
      setAuthor('');

      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold mb-4">Add Document</h2>

      <div className="mb-4 flex gap-2">
        <button
          onClick={() => setUploadType('pdf')}
          className={`flex items-center gap-2 px-4 py-2 rounded ${
            uploadType === 'pdf'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          <Upload size={18} />
          Upload PDF
        </button>
        <button
          onClick={() => setUploadType('url')}
          className={`flex items-center gap-2 px-4 py-2 rounded ${
            uploadType === 'url'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          <LinkIcon size={18} />
          Scrape URL
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {uploadType === 'pdf' ? (
          <div>
            <label className="block text-sm font-medium mb-2">PDF File</label>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="w-full border rounded p-2"
              disabled={loading}
            />
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium mb-2">URL</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/article"
              className="w-full border rounded p-2"
              disabled={loading}
            />
          </div>
        )}

        <div>
          <label className="block text-sm font-medium mb-2">Industry (optional)</label>
          <input
            type="text"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            placeholder="e.g., Healthcare, Finance"
            className="w-full border rounded p-2"
            disabled={loading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Author (optional)</label>
          <input
            type="text"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="e.g., John Doe"
            className="w-full border rounded p-2"
            disabled={loading}
          />
        </div>

        {error && (
          <div className="p-3 bg-red-100 text-red-700 rounded">{error}</div>
        )}

        {success && (
          <div className="p-3 bg-green-100 text-green-700 rounded">{success}</div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:bg-gray-400 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              Processing...
            </>
          ) : (
            uploadType === 'pdf' ? 'Upload PDF' : 'Scrape URL'
          )}
        </button>
      </form>
    </div>
  );
}
