'use client';

import { useState, useEffect } from 'react';
import { GenerationJobStatus, getJobStatus, createJobStream } from '@/lib/api';
import { Loader2, CheckCircle2, XCircle, Sparkles } from 'lucide-react';

interface GenerationProgressProps {
  jobId: string;
  onComplete: (contentId: number) => void;
}

export default function GenerationProgress({ jobId, onComplete }: GenerationProgressProps) {
  const [status, setStatus] = useState<GenerationJobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    // Try SSE streaming first
    let eventSource: EventSource | null = null;
    let pollInterval: NodeJS.Timeout | null = null;

    try {
      eventSource = createJobStream(jobId);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.done) {
            eventSource?.close();
            return;
          }

          if (data.error) {
            setError(data.error);
            eventSource?.close();
            return;
          }

          setStatus(data);

          // Check if completed
          if (data.status === 'completed' && data.result_id) {
            eventSource?.close();
            setTimeout(() => onComplete(data.result_id), 1500);
          } else if (data.status === 'failed') {
            eventSource?.close();
            setError(data.error_message || 'Generation failed');
          }
        } catch (err) {
          console.error('Failed to parse SSE data:', err);
        }
      };

      eventSource.onerror = (err) => {
        console.error('SSE error, falling back to polling:', err);
        eventSource?.close();

        // Fallback to polling
        pollInterval = setInterval(async () => {
          try {
            const jobStatus = await getJobStatus(jobId);
            setStatus(jobStatus);

            if (jobStatus.status === 'completed' && jobStatus.result_id) {
              if (pollInterval) clearInterval(pollInterval);
              setTimeout(() => onComplete(jobStatus.result_id!), 1500);
            } else if (jobStatus.status === 'failed') {
              if (pollInterval) clearInterval(pollInterval);
              setError(jobStatus.error_message || 'Generation failed');
            }
          } catch (error) {
            console.error('Failed to poll status:', error);
          }
        }, 2000);
      };
    } catch (err) {
      console.error('Failed to create SSE connection:', err);
      // Immediate fallback to polling
      pollInterval = setInterval(async () => {
        try {
          const jobStatus = await getJobStatus(jobId);
          setStatus(jobStatus);

          if (jobStatus.status === 'completed' && jobStatus.result_id) {
            if (pollInterval) clearInterval(pollInterval);
            setTimeout(() => onComplete(jobStatus.result_id!), 1500);
          } else if (jobStatus.status === 'failed') {
            if (pollInterval) clearInterval(pollInterval);
            setError(jobStatus.error_message || 'Generation failed');
          }
        } catch (error) {
          console.error('Failed to poll status:', error);
        }
      }, 2000);
    }

    // Cleanup
    return () => {
      if (eventSource) {
        eventSource.close();
      }
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [jobId, onComplete]);

  if (error) {
    return (
      <div className="text-center py-12">
        <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Generation Failed</h2>
        <p className="text-gray-600 mb-6">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="text-center py-12">
        <Loader2 className="w-16 h-16 text-blue-600 animate-spin mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Initializing...</h2>
        <p className="text-gray-600">Setting up your content generation</p>
      </div>
    );
  }

  const isComplete = status.status === 'completed';
  const progress = status.progress_percent || 0;

  return (
    <div className="space-y-8">
      <div className="text-center">
        {isComplete ? (
          <>
            <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Generation Complete!</h2>
            <p className="text-gray-600">Redirecting to your content...</p>
          </>
        ) : (
          <>
            <Sparkles className="w-16 h-16 text-blue-600 mx-auto mb-4 animate-pulse" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Generating Your Content</h2>
            <p className="text-gray-600">This usually takes 2-5 minutes</p>
          </>
        )}
      </div>

      {/* Progress Bar */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Progress</span>
          <span className="text-sm font-medium text-blue-600">{progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-600 to-purple-600 h-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Current Step */}
      {status.current_step && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm font-medium text-blue-900">{status.current_step}</p>
        </div>
      )}

      {/* Timeline */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${progress >= 10 ? 'bg-green-500' : 'bg-gray-300'}`} />
          <span className={`text-sm ${progress >= 10 ? 'text-gray-900' : 'text-gray-500'}`}>
            Gathering context from documents
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${progress >= 30 ? 'bg-green-500' : 'bg-gray-300'}`} />
          <span className={`text-sm ${progress >= 30 ? 'text-gray-900' : 'text-gray-500'}`}>
            Generating content sections
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${progress >= 90 ? 'bg-green-500' : 'bg-gray-300'}`} />
          <span className={`text-sm ${progress >= 90 ? 'text-gray-900' : 'text-gray-500'}`}>
            Formatting and finalizing
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${isComplete ? 'bg-green-500' : 'bg-gray-300'}`} />
          <span className={`text-sm ${isComplete ? 'text-gray-900' : 'text-gray-500'}`}>
            Complete
          </span>
        </div>
      </div>

      <div className="text-center text-sm text-gray-500">
        Job ID: {jobId}
      </div>
    </div>
  );
}
