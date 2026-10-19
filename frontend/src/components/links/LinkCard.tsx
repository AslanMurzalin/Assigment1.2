import React, { useState, useEffect } from 'react';
import type { DownloadProgress, Link, UpdateLinkInput } from '../../types';
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
  onDownload: (
    id: string,
    onProgress?: (progress: DownloadProgress) => void
  ) => Promise<{ downloadUrl: string; filename: string }>;
  onSelectTag?: (tag: string) => void;
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
};

const formatRemainingTime = (seconds?: number): string => {
  if (!seconds || !isFinite(seconds) || seconds <= 0) return '';
  if (seconds < 60) return `~${Math.round(seconds)}s left`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `~${mins}m ${secs}s left`;
};

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
  const [downloadProgress, setDownloadProgress] = useState<DownloadProgress | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Warn user before page refresh/close during active download
  useEffect(() => {
    if (!isDownloading) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [isDownloading]);

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
    setDownloadProgress({ loaded: 0, percent: 5 });
    try {
      const result = await onDownload(link.id, (prog) => {
        setDownloadProgress(prog);
      });
      const a = document.createElement('a');
      a.href = result.downloadUrl;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      setDownloadSuccess(true);
      setDownloadProgress({ loaded: 100, percent: 100 });
      setTimeout(() => {
        setDownloadSuccess(false);
        setDownloadProgress(null);
      }, 3500);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Download failed.');
      setDownloadProgress(null);
    } finally {
      setIsDownloading(false);
    }
  };

  const isYouTube = link.siteType === 'youtube';

  return (
    <div className="bg-white rounded-2xl border border-stone-200 hover:border-orange-200 p-5 shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between group">
      <div>
        {/* Header / Source Badge & Actions */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            {isYouTube ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
                <Video className="w-3.5 h-3.5 text-red-600 fill-current" />
                YouTube (720p)
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-stone-100 text-stone-700 border border-stone-200">
                <Globe className="w-3.5 h-3.5 text-stone-500" />
                Generic
              </span>
            )}
            <span className="flex items-center gap-1 text-[11px] text-stone-400">
              <Calendar className="w-3 h-3" />
              {formattedDate}
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setIsEditModalOpen(true)}
              className="p-1.5 text-stone-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition"
              title="Edit notes & tags"
              aria-label="Edit notes and tags"
            >
              <Edit3 className="w-4 h-4" />
            </button>
            <button
              type="button"
              disabled={isDeleting}
              onClick={handleDelete}
              className="p-1.5 text-stone-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition disabled:opacity-50"
              title="Delete link"
              aria-label="Delete link"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Title */}
        <h3 className="font-semibold text-stone-900 text-base leading-snug mb-1 line-clamp-2">
          <a
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-orange-600 hover:underline transition"
          >
            {link.title || link.url}
          </a>
        </h3>

        {/* External URL */}
        <a
          href={link.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-orange-600 hover:text-orange-800 break-all mb-3 max-w-full font-mono text-[11px]"
        >
          <span className="truncate max-w-[280px] sm:max-w-[400px]">{link.url}</span>
          <ExternalLink className="w-3 h-3 shrink-0" />
        </a>

        {/* User Notes */}
        {link.userNotes && (
          <div className="p-3 bg-stone-50 rounded-xl border border-stone-100 text-xs text-stone-700 mb-3 flex items-start gap-2">
            <FileText className="w-3.5 h-3.5 text-stone-400 mt-0.5 shrink-0" />
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
                className="px-2 py-0.5 text-[11px] font-medium bg-stone-100 hover:bg-orange-50 text-stone-600 hover:text-orange-700 border border-stone-200 hover:border-orange-200 rounded-md transition"
              >
                #{tag}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer / Streaming Download & Filling Progress Scale (YouTube only) */}
      <div className="pt-2 border-t border-stone-100 mt-auto flex items-center justify-between">
        {isYouTube ? (
          isDownloading ? (
            <div className="w-full flex flex-col gap-1.5 p-2.5 bg-orange-50/70 border border-orange-200 rounded-xl">
              {/* Header: Status and percentage */}
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-1.5 text-orange-950 font-semibold">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-600" />
                  </span>
                  Streaming 720p...
                </span>
                <span className="text-orange-700 font-bold tabular-nums">
                  {downloadProgress?.percent ?? 5}%
                </span>
              </div>

              {/* Visual Filling Scale Bar */}
              <div className="w-full h-2 bg-orange-100 rounded-full overflow-hidden p-0.5 border border-orange-200/60 shadow-inner">
                <div
                  className="h-full bg-linear-to-r from-orange-500 to-orange-600 rounded-full transition-all duration-200 ease-out relative overflow-hidden"
                  style={{ width: `${Math.max(5, downloadProgress?.percent ?? 5)}%` }}
                >
                  <div className="absolute inset-0 bg-white/25 animate-pulse" />
                </div>
              </div>

              {/* Subtitle: Downloaded size & ETA/Speed */}
              <div className="flex items-center justify-between text-[11px] text-stone-500 tabular-nums">
                <span>
                  {downloadProgress?.loaded ? formatBytes(downloadProgress.loaded) : '0 B'}
                  {downloadProgress?.total ? ` / ${formatBytes(downloadProgress.total)}` : ''}
                </span>
                <span>
                  {downloadProgress?.estimated
                    ? formatRemainingTime(downloadProgress.estimated)
                    : downloadProgress?.speed
                    ? `${formatBytes(downloadProgress.speed)}/s`
                    : 'Receiving chunks...'}
                </span>
              </div>
            </div>
          ) : downloadSuccess ? (
            <div className="w-full py-2.5 px-3 text-xs font-semibold rounded-xl bg-emerald-600 text-white flex items-center justify-center gap-2 shadow-xs transition">
              <CheckCircle2 className="w-4 h-4" />
              <span>Download Complete! File Saved.</span>
            </div>
          ) : (
            <button
              type="button"
              onClick={handleDownload}
              className="w-full py-2 px-3 text-xs font-semibold rounded-xl flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white shadow-xs transition hover:shadow-sm active:scale-[0.99]"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download (720p Stream)</span>
            </button>
          )
        ) : (
          <div className="text-[11px] text-stone-400 italic">Saved generic URL</div>
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
