import React, { useState } from 'react';
import type { Link, UpdateLinkInput } from '../../types';
import { EditNotesModal } from './EditNotesModal';
import {
  ExternalLink,
  Trash2,
  Edit3,
  Download,
  Video,
  Globe,
  Calendar,
  FileText,
  CheckCircle2,
} from 'lucide-react';

interface LinkCardProps {
  link: Link;
  onDelete: (id: string) => Promise<void>;
  onUpdate: (id: string, input: UpdateLinkInput) => Promise<unknown>;
  onDownload: (id: string) => Promise<{ downloadUrl: string; filename: string }>;
  onSelectTag?: (tag: string) => void;
}

export const LinkCard: React.FC<LinkCardProps> = ({
  link,
  onDelete,
  onUpdate,
  onDownload,
  onSelectTag,
}) => {
  const [isDeleting, setIsDeleting] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  const formattedDate = new Date(link.createdAt).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to delete "${link.title}"?`)) {
      setIsDeleting(true);
      try {
        await onDelete(link.id);
      } finally {
        setIsDeleting(false);
      }
    }
  };

  const handleDownload = async () => {
    setIsDownloading(true);
    setDownloadSuccess(false);
    try {
      const result = await onDownload(link.id);
      // Trigger browser download via synthetic anchor
      const a = document.createElement('a');
      a.href = result.downloadUrl;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      setDownloadSuccess(true);
      setTimeout(() => setDownloadSuccess(false), 3000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Download failed.');
    } finally {
      setIsDownloading(false);
    }
  };

  const isYouTube = link.siteType === 'youtube';

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 hover:border-slate-300 p-5 shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between group">
      <div>
        {/* Header / Source Badge & Actions */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            {isYouTube ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-red-50 text-red-700 border border-red-200/80">
                <Video className="w-3.5 h-3.5 text-red-600 fill-current" />
                YouTube (720p)
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                <Globe className="w-3.5 h-3.5 text-slate-500" />
                Generic
              </span>
            )}
            <span className="flex items-center gap-1 text-[11px] text-slate-400">
              <Calendar className="w-3 h-3" />
              {formattedDate}
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setIsEditModalOpen(true)}
              className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition"
              title="Edit notes & tags"
              aria-label="Edit notes and tags"
            >
              <Edit3 className="w-4 h-4" />
            </button>
            <button
              type="button"
              disabled={isDeleting}
              onClick={handleDelete}
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition disabled:opacity-50"
              title="Delete link"
              aria-label="Delete link"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Title */}
        <h3 className="font-semibold text-slate-900 text-base leading-snug mb-1 line-clamp-2">
          <a
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-indigo-600 hover:underline transition"
          >
            {link.title || link.url}
          </a>
        </h3>

        {/* External URL */}
        <a
          href={link.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 break-all mb-3 max-w-full"
        >
          <span className="truncate max-w-[280px] sm:max-w-[400px]">{link.url}</span>
          <ExternalLink className="w-3 h-3 shrink-0" />
        </a>

        {/* User Notes */}
        {link.userNotes && (
          <div className="p-3 bg-slate-50/80 rounded-xl border border-slate-100 text-xs text-slate-700 mb-3 flex items-start gap-2">
            <FileText className="w-3.5 h-3.5 text-slate-400 mt-0.5 shrink-0" />
            <p className="whitespace-pre-line line-clamp-3">{link.userNotes}</p>
          </div>
        )}

        {/* Tags */}
        {link.tags && link.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {link.tags.map((tag) => (
              <button
                key={tag}
                type="button"
                onClick={() => onSelectTag?.(tag)}
                className="px-2 py-0.5 text-[11px] font-medium bg-slate-100 hover:bg-indigo-50 text-slate-600 hover:text-indigo-700 border border-slate-200 hover:border-indigo-200 rounded-md transition"
              >
                #{tag}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer / Streaming Download Button (YouTube only) */}
      <div className="pt-2 border-t border-slate-100 mt-auto flex items-center justify-between">
        {isYouTube ? (
          <button
            type="button"
            onClick={handleDownload}
            disabled={isDownloading}
            className={`w-full py-2 px-3 text-xs font-semibold rounded-xl flex items-center justify-center gap-2 transition ${
              downloadSuccess
                ? 'bg-emerald-600 text-white'
                : 'bg-red-600 hover:bg-red-700 text-white shadow-xs'
            } disabled:opacity-50`}
          >
            {isDownloading ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Streaming Video...</span>
              </>
            ) : downloadSuccess ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Download Started!</span>
              </>
            ) : (
              <>
                <Download className="w-3.5 h-3.5" />
                <span>Download (720p Stream)</span>
              </>
            )}
          </button>
        ) : (
          <div className="text-[11px] text-slate-400 italic">Saved generic URL</div>
        )}
      </div>

      {/* Edit Modal */}
      <EditNotesModal
        link={link}
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSave={onUpdate}
      />
    </div>
  );
};
