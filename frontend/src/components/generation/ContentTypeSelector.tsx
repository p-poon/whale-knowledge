'use client';

import { ContentType } from '@/lib/api';
import { FileText, Newspaper, PenTool } from 'lucide-react';

interface ContentTypeSelectorProps {
  selectedType: ContentType;
  onSelect: (type: ContentType) => void;
}

const contentTypes = [
  {
    id: 'whitepaper' as ContentType,
    label: 'White Paper',
    description: 'Professional, comprehensive analysis with executive summary and detailed research',
    icon: FileText,
    features: ['Executive Summary', 'In-depth Analysis', 'Case Studies', 'References'],
  },
  {
    id: 'article' as ContentType,
    label: 'Article',
    description: 'Engaging, informative content with clear structure and actionable insights',
    icon: Newspaper,
    features: ['Compelling Introduction', 'Structured Content', 'Practical Applications', 'Call-to-Action'],
  },
  {
    id: 'blog' as ContentType,
    label: 'Blog Post',
    description: 'Conversational, accessible content optimized for online reading',
    icon: PenTool,
    features: ['Engaging Hook', 'Scannable Format', 'Key Takeaways', 'Reader Engagement'],
  },
];

export default function ContentTypeSelector({ selectedType, onSelect }: ContentTypeSelectorProps) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Choose Content Type</h2>
      <p className="text-gray-600 mb-8">Select the type of content you want to generate</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {contentTypes.map((type) => {
          const Icon = type.icon;
          const isSelected = selectedType === type.id;

          return (
            <button
              key={type.id}
              onClick={() => onSelect(type.id)}
              className={`p-6 rounded-lg border-2 text-left transition-all ${
                isSelected
                  ? 'border-blue-600 bg-blue-50 shadow-md'
                  : 'border-gray-200 hover:border-blue-300 hover:shadow-sm'
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <Icon
                  className={`w-8 h-8 ${isSelected ? 'text-blue-600' : 'text-gray-400'}`}
                />
                {isSelected && (
                  <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                )}
              </div>

              <h3 className="text-lg font-semibold text-gray-900 mb-2">{type.label}</h3>
              <p className="text-sm text-gray-600 mb-4">{type.description}</p>

              <div className="space-y-1">
                {type.features.map((feature) => (
                  <div key={feature} className="flex items-center text-sm text-gray-700">
                    <svg
                      className="w-4 h-4 text-green-500 mr-2"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    {feature}
                  </div>
                ))}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
