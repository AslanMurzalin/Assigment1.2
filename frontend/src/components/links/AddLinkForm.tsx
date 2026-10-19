import React, { useState } from 'react';
import type { CreateLinkInput } from '../../types';
import { Plus, X, Link as LinkIcon, Tag as TagIcon, FileText } from 'lucide-react';

interface AddLinkFormProps {
  onAddLink: (input: CreateLinkInput) => Promise<unknown>;
}

export const AddLinkForm: React.FC<AddLinkFormProps> = ({ onAddLink }) => {
  const [url, setUrl] = useState('');
  const [notes, setNotes] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddTag = () => {
    const trimmed = tagInput.trim().toLowerCase().replace(/^[#,]/, '');
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed]);
    }
    setTagInput('');
  };

  const handleKeyDownTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      setError('Please paste a valid URL.');
      return;
    }

    try {
      new URL(trimmedUrl);
    } catch {
      setError('Invalid URL format. Please include http:// or https://');
      return;
    }

    let finalTags = [...tags];
    if (tagInput.trim()) {
      const pendingTag = tagInput.trim().toLowerCase().replace(/^[#,]/, '');
      if (pendingTag && !finalTags.includes(pendingTag)) {
        finalTags.push(pendingTag);
      }
    }

    setIsSubmitting(true);
    try {
      await onAddLink({
        url: trimmedUrl,
        userNotes: notes.trim(),
        tags: finalTags,
      });
      setUrl('');
      setNotes('');
      setTags([]);
      setTagInput('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save link.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-stone-200 p-5 sm:p-6 shadow-xs mb-8">
      <div className="flex items-center gap-2.5 mb-4">
        <div className="p-2 bg-orange-50 text-orange-600 rounded-xl">
          <Plus className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-base sm:text-lg font-semibold text-stone-900">Save a new link</h2>
          <p className="text-xs text-stone-500">Auto-fetches page title and tags for quick retrieval</p>
        </div>
      </div>

      {error && (
        <div className="p-3 mb-4 text-xs sm:text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-xl">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} method="POST" className="space-y-4">
        <div>
          <label htmlFor="link-url" className="flex items-center gap-1.5 text-xs font-medium text-stone-700 mb-1.5">
            <LinkIcon className="w-3.5 h-3.5 text-stone-400" />
            URL to save <span className="text-rose-500">*</span>
          </label>
          <input
            id="link-url"
            name="url"
            type="url"
            required
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=... or https://example.com"
            className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-stone-300 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-600 transition"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="link-notes" className="flex items-center gap-1.5 text-xs font-medium text-stone-700 mb-1.5">
              <FileText className="w-3.5 h-3.5 text-stone-400" />
              Notes (optional)
            </label>
            <textarea
              id="link-notes"
              name="notes"
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Why you saved this, takeaways, or reminders..."
              className="w-full px-3.5 py-2 text-sm rounded-xl border border-stone-300 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-600 transition resize-y min-h-[44px]"
            />
          </div>

          <div>
            <label htmlFor="link-tags" className="flex items-center gap-1.5 text-xs font-medium text-stone-700 mb-1.5">
              <TagIcon className="w-3.5 h-3.5 text-stone-400" />
              Tags (press Enter or comma)
            </label>
            <div className="flex gap-2">
              <input
                id="link-tags"
                name="tags"
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleKeyDownTag}
                placeholder="tech, tutorial, music..."
                className="w-full px-3.5 py-2 text-sm rounded-xl border border-stone-300 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-600 transition"
              />
              <button
                type="button"
                onClick={handleAddTag}
                className="px-3.5 py-2 bg-stone-100 hover:bg-stone-200 text-stone-700 rounded-xl text-xs font-medium transition"
              >
                Add
              </button>
            </div>

            {tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-50 text-orange-700 border border-orange-200"
                  >
                    #{tag}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className="hover:text-orange-900 rounded-full"
                      aria-label={`Remove tag ${tag}`}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end pt-1">
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full sm:w-auto px-6 py-2.5 bg-orange-600 hover:bg-orange-700 text-white font-medium text-sm rounded-xl shadow-xs hover:shadow transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Extracting & Saving...</span>
              </>
            ) : (
              <>
                <Plus className="w-4 h-4" />
                <span>Save Link</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
