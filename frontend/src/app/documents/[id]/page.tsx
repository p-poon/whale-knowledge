'use client';

import { useParams, useRouter } from 'next/navigation';
import DocumentViewer from '@/components/DocumentViewer';

export default function DocumentViewPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = parseInt(params.id as string);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <DocumentViewer
          documentId={documentId}
          onClose={() => router.back()}
        />
      </div>
    </div>
  );
}
