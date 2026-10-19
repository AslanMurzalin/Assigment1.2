import React from 'react';
import { Tag as TagIcon, X } from 'lucide-react';

interface TagFilterProps {
  availableTags: string[];
  selectedTag: string | null;
  onSelectTag: (tag: string | null) => void;
}

export const TagFilter: React.FC<TagFilterProps> = ({
  availableTags,
  selectedTag,
  onSelectTag,
}) => {
  if (availableTags.length === 0) return null;

  return (
    <div className="flex items-center gap-2 overflow-x-auto py-1 scrollbar-none">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-stone-500 uppercase tracking-wider shrink-0 pr-1">
        <TagIcon className="w-3.5 h-3.5" />
        <span>Tags:</span>
      </div>

      <button
        type="button"
        onClick={() => onSelectTag(null)}
        className={`px-3 py-1 rounded-full text-xs font-medium shrink-0 transition ${
          selectedTag === null
            ? 'bg-orange-600 text-white shadow-xs'
            : 'bg-white hover:bg-orange-50 text-stone-600 hover:text-orange-700 border border-stone-200 hover:border-orange-200'
        }`}
      >
        All
      </button>

      {availableTags.map((tag) => {
        const isSelected = selectedTag === tag;
        return (
          <button
            key={tag}
            type="button"
            onClick={() => onSelectTag(isSelected ? null : tag)}
            className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium shrink-0 transition ${
              isSelected
                ? 'bg-orange-600 text-white shadow-xs'
                : 'bg-white hover:bg-orange-50 text-stone-600 hover:text-orange-700 border border-stone-200 hover:border-orange-200'
            }`}
          >
            <span>#{tag}</span>
            {isSelected && <X className="w-3 h-3 ml-0.5" />}
          </button>
        );
      })}
    </div>
  );
};
