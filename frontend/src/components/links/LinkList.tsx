import React from 'react';
import type { Link, UpdateLinkInput } from '../../types';
import { LinkCard } from './LinkCard';
import { BookmarkX } from 'lucide-react';

interface LinkListProps {
  links: Link[];
  isLoading: boolean;
  onDelete: (id: string) => Promise<void>;
  onUpdate: (id: string, input: UpdateLinkInput) => Promise<unknown>;
  onDownload: (id: string) => Promise<{ downloadUrl: string; filename: string }>;
  onSelectTag?: (tag: string) => void;
  onClearFilters?: () => void;
  isFiltered?: boolean;
}

export const LinkList: React.FC<LinkListProps> = ({
  links,
  isLoading,
  onDelete,
  onUpdate,
  onDownload,
  onSelectTag,
  onClearFilters,
  isFiltered,
}) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {[1, 2, 3].map((n) => (
          <div
            key={n}
            className="h-64 bg-white rounded-2xl border border-stone-200 p-5 animate-pulse flex flex-col justify-between"
          >
            <div>
              <div className="h-5 w-24 bg-stone-200 rounded-lg mb-3" />
              <div className="h-5 w-3/4 bg-stone-200 rounded-lg mb-2" />
              <div className="h-3 w-1/2 bg-stone-100 rounded-lg mb-4" />
              <div className="h-16 w-full bg-stone-100 rounded-xl mb-4" />
            </div>
            <div className="h-9 w-full bg-stone-100 rounded-xl" />
          </div>
        ))}
      </div>
    );
  }

  if (links.length === 0) {
    return (
      <div className="text-center py-16 px-4 bg-white rounded-2xl border border-stone-200 shadow-xs">
        <div className="w-12 h-12 mx-auto mb-4 bg-orange-50 text-orange-500 rounded-2xl flex items-center justify-center">
          <BookmarkX className="w-6 h-6" />
        </div>
        <h3 className="text-base font-semibold text-stone-900 mb-1">
          {isFiltered ? 'No matching links found' : 'No links saved yet'}
        </h3>
        <p className="text-sm text-stone-500 max-w-sm mx-auto mb-4">
          {isFiltered
            ? 'Try broadening your search keywords or clearing tag filters.'
            : 'Paste a YouTube video or website URL above to save your first bookmark.'}
        </p>
        {isFiltered && onClearFilters && (
          <button
            type="button"
            onClick={onClearFilters}
            className="px-4 py-2 text-xs font-semibold text-orange-700 bg-orange-50 hover:bg-orange-100 border border-orange-200 rounded-xl transition"
          >
            Clear all filters
          </button>
        )}
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-stone-700">
          Saved Links ({links.length})
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {links.map((link) => (
          <LinkCard
            key={link.id}
            link={link}
            onDelete={onDelete}
            onUpdate={onUpdate}
            onDownload={onDownload}
            onSelectTag={onSelectTag}
          />
        ))}
      </div>
    </div>
  );
};
