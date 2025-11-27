'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ContentType, LLMProvider, GenerationCustomization, startGeneration } from '@/lib/api';
import ContentTypeSelector from '@/components/generation/ContentTypeSelector';
import DocumentSelector from '@/components/generation/DocumentSelector';
import CustomizationForm from '@/components/generation/CustomizationForm';
import TemplateSelector from '@/components/generation/TemplateSelector';
import GenerationProgress from '@/components/generation/GenerationProgress';

type WizardStep = 'content-type' | 'documents' | 'customization' | 'template' | 'review' | 'generating';

export default function GeneratePage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<WizardStep>('content-type');
  const [jobId, setJobId] = useState<string | null>(null);

  // Form state
  const [contentType, setContentType] = useState<ContentType>('whitepaper');
  const [topic, setTopic] = useState('');
  const [selectedDocuments, setSelectedDocuments] = useState<number[]>([]);
  const [llmProvider, setLLMProvider] = useState<LLMProvider>('anthropic');
  const [llmModel, setLLMModel] = useState<string>('');
  const [customization, setCustomization] = useState<GenerationCustomization>({
    style: 'professional',
    tone: 'neutral',
    audience: 'general',
    length: 'medium',
    include_executive_summary: true,
    include_conclusion: true,
    include_references: true,
  });
  const [templateId, setTemplateId] = useState<number | undefined>(undefined);

  const steps: { id: WizardStep; label: string }[] = [
    { id: 'content-type', label: 'Content Type' },
    { id: 'documents', label: 'Topic & Documents' },
    { id: 'customization', label: 'Customize' },
    { id: 'template', label: 'Template' },
    { id: 'review', label: 'Review' },
  ];

  const currentStepIndex = steps.findIndex((s) => s.id === currentStep);

  const handleNext = () => {
    const nextIndex = currentStepIndex + 1;
    if (nextIndex < steps.length) {
      setCurrentStep(steps[nextIndex].id);
    }
  };

  const handleBack = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setCurrentStep(steps[prevIndex].id);
    }
  };

  const handleGenerationComplete = (contentId: number) => {
    router.push(`/generated/${contentId}`);
  };

  const handleStartGeneration = async () => {
    try {
      const response = await startGeneration({
        topic,
        content_type: contentType,
        document_ids: selectedDocuments,
        llm_provider: llmProvider,
        llm_model: llmModel || undefined,
        customization,
        template_id: templateId,
      });

      setJobId(response.job_id);
      setCurrentStep('generating');
    } catch (error) {
      console.error('Failed to start generation:', error);
      alert('Failed to start generation. Please try again.');
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 'content-type':
        return contentType !== null;
      case 'documents':
        return topic.length >= 10 && selectedDocuments.length > 0;
      case 'customization':
      case 'template':
        return true;
      case 'review':
        return true;
      default:
        return false;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-5xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Generate Content</h1>
          <p className="mt-2 text-gray-600">
            Create AI-powered white papers, articles, and blog posts from your knowledge base
          </p>
        </div>

        {/* Progress Steps */}
        {currentStep !== 'generating' && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => (
                <div key={step.id} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                        index <= currentStepIndex
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-600'
                      }`}
                    >
                      {index + 1}
                    </div>
                    <span
                      className={`mt-2 text-sm ${
                        index <= currentStepIndex ? 'text-blue-600 font-medium' : 'text-gray-500'
                      }`}
                    >
                      {step.label}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className={`h-1 flex-1 mx-2 ${
                        index < currentStepIndex ? 'bg-blue-600' : 'bg-gray-200'
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-sm p-8">
          {currentStep === 'content-type' && (
            <ContentTypeSelector
              selectedType={contentType}
              onSelect={setContentType}
            />
          )}

          {currentStep === 'documents' && (
            <DocumentSelector
              topic={topic}
              onTopicChange={setTopic}
              selectedDocuments={selectedDocuments}
              onDocumentsChange={setSelectedDocuments}
              contentType={contentType}
            />
          )}

          {currentStep === 'customization' && (
            <CustomizationForm
              customization={customization}
              onCustomizationChange={setCustomization}
              llmProvider={llmProvider}
              onProviderChange={setLLMProvider}
              llmModel={llmModel}
              onModelChange={setLLMModel}
            />
          )}

          {currentStep === 'template' && (
            <TemplateSelector
              contentType={contentType}
              selectedTemplateId={templateId}
              onTemplateSelect={setTemplateId}
            />
          )}

          {currentStep === 'review' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900">Review & Generate</h2>

              <div className="space-y-4">
                <div className="border-b pb-4">
                  <h3 className="text-sm font-medium text-gray-500">Content Type</h3>
                  <p className="mt-1 text-lg capitalize">{contentType}</p>
                </div>

                <div className="border-b pb-4">
                  <h3 className="text-sm font-medium text-gray-500">Topic</h3>
                  <p className="mt-1 text-lg">{topic}</p>
                </div>

                <div className="border-b pb-4">
                  <h3 className="text-sm font-medium text-gray-500">Selected Documents</h3>
                  <p className="mt-1 text-lg">{selectedDocuments.length} documents</p>
                </div>

                <div className="border-b pb-4">
                  <h3 className="text-sm font-medium text-gray-500">LLM Provider</h3>
                  <p className="mt-1 text-lg capitalize">{llmProvider}</p>
                </div>

                <div className="border-b pb-4">
                  <h3 className="text-sm font-medium text-gray-500">Style & Tone</h3>
                  <p className="mt-1 text-lg">
                    {customization.style} style, {customization.tone} tone
                  </p>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  Generation typically takes 2-5 minutes depending on content length and complexity.
                  You'll be able to monitor progress in real-time.
                </p>
              </div>
            </div>
          )}

          {currentStep === 'generating' && jobId && (
            <GenerationProgress
              jobId={jobId}
              onComplete={handleGenerationComplete}
            />
          )}
        </div>

        {/* Navigation Buttons */}
        {currentStep !== 'generating' && (
          <div className="mt-6 flex justify-between">
            <button
              onClick={handleBack}
              disabled={currentStepIndex === 0}
              className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Back
            </button>

            {currentStep === 'review' ? (
              <button
                onClick={handleStartGeneration}
                disabled={!canProceed()}
                className="px-8 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Start Generation
              </button>
            ) : (
              <button
                onClick={handleNext}
                disabled={!canProceed()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
