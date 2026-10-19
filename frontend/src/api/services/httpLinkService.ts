import { apiClient } from '../client';
import type {
  CreateLinkInput,
  DownloadProgress,
  FilterParams,
  ILinkService,
  Link,
  SiteType,
  UpdateLinkInput,
} from '../../types';

interface BackendLinkRead {
  id: string;
  user_id: string;
  url: string;
  title: string;
  description: string | null;
  site_type: string;
  user_notes: string | null;
  tags: string[];
  created_at: string;
  updated_at: string | null;
}

const mapLink = (l: BackendLinkRead): Link => ({
  id: l.id,
  userId: l.user_id,
  url: l.url,
  title: l.title || '',
  description: l.description || '',
  siteType: (l.site_type || 'generic') as SiteType,
  userNotes: l.user_notes || '',
  tags: Array.isArray(l.tags) ? l.tags : [],
  createdAt: l.created_at,
  updatedAt: l.updated_at || undefined,
});

export class HttpLinkService implements ILinkService {
  async getLinks(filters?: FilterParams): Promise<Link[]> {
    try {
      const params: Record<string, string> = {};
      if (filters?.q && filters.q.trim()) {
        params.q = filters.q.trim();
      }
      if (filters?.tag && filters.tag.trim()) {
        params.tag = filters.tag.trim();
      }

      const resp = await apiClient.get<BackendLinkRead[]>('/api/v1/links', { params });
      return resp.data.map(mapLink);
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || 'Failed to fetch links';
      throw new Error(msg);
    }
  }

  async getLinkById(id: string): Promise<Link> {
    try {
      const resp = await apiClient.get<BackendLinkRead>(`/api/v1/links/${id}`);
      return mapLink(resp.data);
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || 'Failed to fetch link';
      throw new Error(msg);
    }
  }

  async createLink(input: CreateLinkInput): Promise<Link> {
    try {
      const payload: Record<string, any> = {
        url: input.url.trim(),
      };
      if (input.userNotes !== undefined) {
        payload.user_notes = input.userNotes.trim();
      }
      if (input.tags !== undefined) {
        payload.tags = input.tags.map((t) => t.trim().toLowerCase()).filter(Boolean);
      }

      const resp = await apiClient.post<BackendLinkRead>('/api/v1/links', payload);
      return mapLink(resp.data);
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || 'Failed to create link';
      throw new Error(msg);
    }
  }

  async updateLink(id: string, input: UpdateLinkInput): Promise<Link> {
    try {
      const payload: Record<string, any> = {};
      if (input.userNotes !== undefined) {
        payload.user_notes = input.userNotes.trim();
      }
      if (input.tags !== undefined) {
        payload.tags = input.tags.map((t) => t.trim().toLowerCase()).filter(Boolean);
      }

      const resp = await apiClient.patch<BackendLinkRead>(`/api/v1/links/${id}`, payload);
      return mapLink(resp.data);
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || 'Failed to update link';
      throw new Error(msg);
    }
  }

  async deleteLink(id: string): Promise<void> {
    try {
      await apiClient.delete(`/api/v1/links/${id}`);
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || 'Failed to delete link';
      throw new Error(msg);
    }
  }

  async downloadVideo(
    id: string,
    onProgress?: (progress: DownloadProgress) => void
  ): Promise<{ downloadUrl: string; filename: string }> {
    try {
      const startTime = Date.now();

      const resp = await apiClient.get(`/api/v1/links/${id}/download`, {
        responseType: 'blob',
        timeout: 0, // No timeout for large video streams
        onDownloadProgress: (progressEvent) => {
          if (onProgress) {
            const loaded = progressEvent.loaded || 0;
            const total = progressEvent.total || undefined;
            let percent: number;

            if (total && total > 0) {
              percent = Math.min(99, Math.round((loaded * 100) / total));
            } else {
              // Adaptive progress estimate for 720p stream (~15MB typical size)
              const benchmark = 15 * 1024 * 1024;
              percent = Math.min(95, Math.round((loaded * 100) / benchmark));
            }

            const elapsedSec = Math.max(0.1, (Date.now() - startTime) / 1000);
            const speed = loaded / elapsedSec; // bytes per second
            const estimated =
              total && speed > 0 && total > loaded
                ? Math.round((total - loaded) / speed)
                : undefined;

            onProgress({
              loaded,
              total,
              percent,
              speed,
              estimated,
            });
          }
        },
      });

      // Check if received video stream is empty
      if (!resp.data || resp.data.size === 0) {
        throw new Error('Video stream returned 0 bytes. The video format may be unavailable or restricted.');
      }

      // Final 100% notification
      if (onProgress) {
        onProgress({
          loaded: resp.data.size,
          total: resp.data.size,
          percent: 100,
        });
      }

      // Parse filename from Content-Disposition header if available
      let filename = `video_${id}_720p.mp4`;
      const disposition = resp.headers['content-disposition'];
      if (disposition) {
        const match = disposition.match(/filename=["']?([^"']+)["']?/);
        if (match && match[1]) {
          filename = match[1];
        }
      }

      const contentType = (resp.headers['content-type'] as string) || 'video/mp4';
      const blob = new Blob([resp.data], { type: contentType });
      const downloadUrl = URL.createObjectURL(blob);

      return { downloadUrl, filename };
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || 'Failed to download video stream';
      throw new Error(msg);
    }
  }
}

export const httpLinkService = new HttpLinkService();
