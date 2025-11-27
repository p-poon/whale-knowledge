'use client';

import { GenerationCustomization, LLMProvider } from '@/lib/api';

interface CustomizationFormProps {
  customization: GenerationCustomization;
  onCustomizationChange: (customization: GenerationCustomization) => void;
  llmProvider: LLMProvider;
  onProviderChange: (provider: LLMProvider) => void;
  llmModel: string;
  onModelChange: (model: string) => void;
}

export default function CustomizationForm({
  customization,
  onCustomizationChange,
  llmProvider,
  onProviderChange,
  llmModel,
  onModelChange,
}: CustomizationFormProps) {
  const handleChange = (field: keyof GenerationCustomization, value: any) => {
    onCustomizationChange({
      ...customization,
      [field]: value,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Customize Your Content</h2>
        <p className="text-gray-600">Fine-tune the style, tone, and structure</p>
      </div>

      {/* LLM Provider */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          AI Model Provider
        </label>
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => onProviderChange('anthropic')}
            className={`p-4 rounded-lg border-2 text-left ${
              llmProvider === 'anthropic'
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-200 hover:border-blue-300'
            }`}
          >
            <div className="font-semibold text-gray-900">Anthropic Claude</div>
            <div className="text-sm text-gray-600 mt-1">Claude 3.5 Sonnet - Best quality</div>
          </button>
          <button
            onClick={() => onProviderChange('openai')}
            className={`p-4 rounded-lg border-2 text-left ${
              llmProvider === 'openai'
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-200 hover:border-blue-300'
            }`}
          >
            <div className="font-semibold text-gray-900">OpenAI</div>
            <div className="text-sm text-gray-600 mt-1">GPT-4 Turbo - Fast & powerful</div>
          </button>
        </div>
      </div>

      {/* Style */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Writing Style
        </label>
        <select
          value={customization.style}
          onChange={(e) => handleChange('style', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="professional">Professional</option>
          <option value="formal">Formal</option>
          <option value="conversational">Conversational</option>
          <option value="technical">Technical</option>
        </select>
      </div>

      {/* Tone */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tone
        </label>
        <select
          value={customization.tone}
          onChange={(e) => handleChange('tone', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="neutral">Neutral</option>
          <option value="enthusiastic">Enthusiastic</option>
          <option value="analytical">Analytical</option>
          <option value="authoritative">Authoritative</option>
          <option value="friendly">Friendly</option>
        </select>
      </div>

      {/* Audience */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Target Audience
        </label>
        <select
          value={customization.audience}
          onChange={(e) => handleChange('audience', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="general">General Public</option>
          <option value="executives">Executives</option>
          <option value="technical">Technical Professionals</option>
          <option value="academic">Academic / Researchers</option>
        </select>
      </div>

      {/* Length */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Content Length
        </label>
        <select
          value={customization.length}
          onChange={(e) => handleChange('length', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="short">Short (~1,000 words)</option>
          <option value="medium">Medium (~2,500 words)</option>
          <option value="long">Long (~5,000 words)</option>
        </select>
      </div>

      {/* Target Word Count */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Target Word Count (Optional)
        </label>
        <input
          type="number"
          value={customization.target_word_count || ''}
          onChange={(e) => handleChange('target_word_count', e.target.value ? parseInt(e.target.value) : undefined)}
          placeholder="Leave blank for default"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Citation Style */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Citation Style
        </label>
        <select
          value={customization.citation_style}
          onChange={(e) => handleChange('citation_style', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="inline">Inline Citations</option>
          <option value="footnotes">Footnotes</option>
          <option value="references">References Section</option>
        </select>
      </div>

      {/* Additional Options */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">
          Additional Options
        </label>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={customization.include_executive_summary}
            onChange={(e) => handleChange('include_executive_summary', e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">Include Executive Summary</span>
        </label>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={customization.include_conclusion}
            onChange={(e) => handleChange('include_conclusion', e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">Include Conclusion</span>
        </label>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={customization.include_references}
            onChange={(e) => handleChange('include_references', e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">Include References</span>
        </label>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">About Customization</h4>
        <p className="text-sm text-blue-800">
          These settings help the AI understand your requirements. The more specific you are,
          the better the generated content will match your expectations.
        </p>
      </div>
    </div>
  );
}
