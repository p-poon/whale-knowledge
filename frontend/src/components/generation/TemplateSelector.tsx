'use client';

import { useState, useEffect } from 'react';
import { ContentType, ContentTemplate, listTemplates } from '@/lib/api';
import { Loader2, FileText } from 'lucide-react';

interface TemplateSelectorProps {
  contentType: ContentType;
  selectedTemplateId?: number;
  onTemplateSelect: (templateId?: number) => void;
}

export default function TemplateSelector({
  contentType,
  selectedTemplateId,
  onTemplateSelect,
}: TemplateSelectorProps) {
  const [templates, setTemplates] = useState<ContentTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadTemplates = async () => {
      setIsLoading(true);
      try {
        const response = await listTemplates(contentType);
        setTemplates(response.templates);

        // Auto-select default template
        const defaultTemplate = response.templates.find((t) => t.is_default);
        if (defaultTemplate && !selectedTemplateId) {
          onTemplateSelect(defaultTemplate.id);
        }
      } catch (error) {
        console.error('Failed to load templates:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadTemplates();
  }, [contentType]);

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-400" />
        <p className="text-gray-600">Loading templates...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Choose a Template</h2>
        <p className="text-gray-600">Select a template or use the default structure</p>
      </div>

      <div className="space-y-4">
        {templates.map((template) => (
          <button
            key={template.id}
            onClick={() => onTemplateSelect(template.id)}
            className={`w-full p-6 rounded-lg border-2 text-left transition-all ${
              selectedTemplateId === template.id
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-200 hover:border-blue-300'
            }`}
          >
            <div className="flex items-start gap-4">
              <FileText className={`w-6 h-6 flex-shrink-0 ${
                selectedTemplateId === template.id ? 'text-blue-600' : 'text-gray-400'
              }`} />

              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-gray-900">{template.name}</h3>
                  {template.is_default && (
                    <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                      Default
                    </span>
                  )}
                </div>

                {template.description && (
                  <p className="mt-1 text-sm text-gray-600">{template.description}</p>
                )}

                <div className="mt-3 flex flex-wrap gap-2">
                  {template.template_structure.sections.map((section, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                    >
                      {section.name}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-sm text-gray-700">
          💡 Templates provide a structured approach to content generation. You can also create
          custom templates in the settings (coming soon).
        </p>
      </div>
    </div>
  );
}
