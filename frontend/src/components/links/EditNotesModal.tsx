import React, { useState } from 'react';
import type { Link, UpdateLinkInput } from '../../types';
import { X, Tag as TagIcon, FileText, Check } from 'lucide-react';

interface EditNotesModalProps {
  link: Link;
  isOpen: boolean;
  onClose: () => void;
  onSave: (id: string, input: UpdateLinkInput) => Promise<unknown>;
}

export const EditNotesModal: React.FC<EditNotesModalProps> = ({
  link,
  isOpen,
  onClose,
  onSave,
}) => {
  const [notes, setNotes] = useState(link.userNotes);
  const [tags, setTags] = useState<string[]>(link.tags);
  const [tagInput, setTagInput] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  if (!isOpen) return null;

  const handleAddTag = () => {
    const trimmed = tagInput.trim().toLowerCase().replace(/^[#,]/, '');
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed]);
    }
    setTagInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
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
    setIsSaving(true);
    try {
      let finalTags = [...tags];
      if (tagInput.trim()) {
        const pending = tagInput.trim().toLowerCase().replace(/^[#,]/, '');
        if (pending && !finalTags.includes(pending)) {
          finalTags.push(pending);
        }
      }
      await onSave(link.id, {
        userNotes: notes,
        tags: finalTags,
      });
      onClose();
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Edit Notes & Tags</h2>
            <p className="text-xs text-slate-500 truncate max-w-xs">{link.title}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label htmlFor="edit-notes" className="flex items-center gap-1.5 text-xs font-medium text-slate-700 mb-1.5">
              <FileText className="w-3.5 h-3.5 text-slate-400" />
              User Notes
            </label>
            <textarea
              id="edit-notes"
              rows={4}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add your notes, key insights, or thoughts on this link..."
              className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition resize-y"
            />
          </div>

          <div>
            <label htmlFor="edit-tags" className="flex items-center gap-1.5 text-xs font-medium text-slate-700 mb-1.5">
              <TagIcon className="w-3.5 h-3.5 text-slate-400" />
              Tags
            </label>
            <div className="flex gap-2">
              <input
                id="edit-tags"
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type tag and press Enter"
                className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition"
              />
              <button
                type="button"
                onClick={handleAddTag}
                className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-medium transition"
              >
                Add
              </button>
            </div>

            <div className="flex flex-wrap gap-1.5 mt-2.5 min-h-[28px]">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100"
                >
                  #{tag}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="hover:text-indigo-900"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
              {tags.length === 0 && (
                <span className="text-xs text-slate-400 italic">No tags associated</span>
              )}
            </div>
          </div>

          <div className="flex justify-end gap-2.5 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 rounded-xl transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs transition flex items-center gap-1.5 disabled:opacity-50"
            >
              {isSaving ? (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Check className="w-4 h-4" />
              )}
              <span>Save Changes</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
