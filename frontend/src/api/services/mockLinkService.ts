import type { CreateLinkInput, DownloadProgress, FilterParams, ILinkService, Link, SiteType, UpdateLinkInput } from '../../types';

const STORAGE_LINKS_KEY = 'link_saver_links';
const STORAGE_CURRENT_USER_KEY = 'link_saver_current_user';

const delay = (ms = 250) => new Promise((resolve) => setTimeout(resolve, ms));

const INITIAL_LINKS: Link[] = [
  {
    id: 'link-seed-1',
    userId: 'user-demo-1',
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    title: 'Rick Astley - Never Gonna Give You Up (Official Music Video)',
    description: 'The official video for "Never Gonna Give You Up" by Rick Astley. 720p stream ready.',
    siteType: 'youtube',
    userNotes: 'Classic 80s pop anthem. Great test for 720p video streaming.',
    tags: ['music', 'youtube', 'classics'],
    createdAt: new Date(Date.now() - 3600000 * 24 * 2).toISOString(),
  },
  {
    id: 'link-seed-2',
    userId: 'user-demo-1',
    url: 'https://react.dev/learn',
    title: 'Quick Start – React Documentation',
    description: 'Welcome to the React documentation! This page gives an introduction to 80% of React concepts.',
    siteType: 'generic',
    userNotes: 'Reference guide for modern React hooks, state, and component architecture.',
    tags: ['frontend', 'react', 'documentation'],
    createdAt: new Date(Date.now() - 3600000 * 24).toISOString(),
  },
  {
    id: 'link-seed-3',
    userId: 'user-demo-1',
    url: 'https://fastapi.tiangolo.com/tutorial/',
    title: 'FastAPI Tutorial - User Guide',
    description: 'FastAPI framework tutorial, high performance, easy to learn, fast to code, ready for production.',
    siteType: 'generic',
    userNotes: 'Study dependency injection patterns and StreamingResponse.',
    tags: ['backend', 'python', 'fastapi'],
    createdAt: new Date(Date.now() - 3600000 * 5).toISOString(),
  },
  {
    id: 'link-seed-4',
    userId: 'user-demo-1',
    url: 'https://youtu.be/M576WGiDBdQ',
    title: 'Vite 5 in 100 Seconds',
    description: 'Fast next-generation frontend tooling overview.',
    siteType: 'youtube',
    userNotes: 'Speed comparison between Vite and traditional bundlers.',
    tags: ['vite', 'youtube', 'tooling'],
    createdAt: new Date(Date.now() - 3600000 * 2).toISOString(),
  },
];

export class MockLinkService implements ILinkService {
  private getCurrentUserId(): string {
    const raw = localStorage.getItem(STORAGE_CURRENT_USER_KEY);
    if (!raw) return 'user-demo-1';
    try {
      const u = JSON.parse(raw);
      return u.id || 'user-demo-1';
    } catch {
      return 'user-demo-1';
    }
  }

  private getStoredLinks(): Link[] {
    const raw = localStorage.getItem(STORAGE_LINKS_KEY);
    if (!raw) {
      localStorage.setItem(STORAGE_LINKS_KEY, JSON.stringify(INITIAL_LINKS));
      return INITIAL_LINKS;
    }
    try {
      return JSON.parse(raw);
    } catch {
      return [];
    }
  }

  private saveStoredLinks(links: Link[]): void {
    localStorage.setItem(STORAGE_LINKS_KEY, JSON.stringify(links));
  }

  private inferSiteType(url: string): SiteType {
    try {
      const parsed = new URL(url);
      const host = parsed.hostname.toLowerCase();
      if (host.includes('youtube.com') || host.includes('youtu.be')) {
        return 'youtube';
      }
      return 'generic';
    } catch {
      if (url.includes('youtube.com') || url.includes('youtu.be')) {
        return 'youtube';
      }
      return 'generic';
    }
  }

  private mockExtractMetadata(url: string, siteType: SiteType): { title: string; description: string } {
    try {
      const parsed = new URL(url);
      const host = parsed.hostname.replace(/^www\./, '');
      if (siteType === 'youtube') {
        return {
          title: `YouTube Video: ${parsed.pathname.slice(1) || 'Stream 720p'}`,
          description: `Extracted YouTube video stream metadata from ${host}. Ready for direct 720p on-demand streaming.`,
        };
      }
      const pathSnippet = parsed.pathname.split('/').filter(Boolean).slice(-1)[0] || 'Homepage';
      return {
        title: `${pathSnippet.replace(/[-_]/g, ' ')} – ${host}`,
        description: `Auto-extracted OpenGraph summary for ${url}. Saved to Link Saver.`,
      };
    } catch {
      return {
        title: `Saved Link (${url.substring(0, 30)}...)`,
        description: 'Auto-extracted website metadata and description preview.',
      };
    }
  }

  async getLinks(filters?: FilterParams): Promise<Link[]> {
    await delay(200);
    const userId = this.getCurrentUserId();
    let links = this.getStoredLinks().filter((l) => l.userId === userId);

    if (filters?.q && filters.q.trim()) {
      const q = filters.q.trim().toLowerCase();
      links = links.filter(
        (l) =>
          l.title.toLowerCase().includes(q) ||
          l.userNotes.toLowerCase().includes(q) ||
          l.tags.some((t) => t.toLowerCase().includes(q))
      );
    }

    if (filters?.tag && filters.tag.trim()) {
      const tagQuery = filters.tag.trim().toLowerCase();
      links = links.filter((l) => l.tags.some((t) => t.toLowerCase() === tagQuery));
    }

    // Sort newest first
    return links.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }

  async getLinkById(id: string): Promise<Link> {
    await delay(150);
    const link = this.getStoredLinks().find((l) => l.id === id);
    if (!link) {
      throw new Error(`Link with ID ${id} not found`);
    }
    return link;
  }

  async createLink(input: CreateLinkInput): Promise<Link> {
    await delay(350);
    const userId = this.getCurrentUserId();
    const siteType = this.inferSiteType(input.url);
    const meta = this.mockExtractMetadata(input.url, siteType);

    const newLink: Link = {
      id: `link-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      userId,
      url: input.url.trim(),
      title: meta.title,
      description: meta.description,
      siteType,
      userNotes: (input.userNotes || '').trim(),
      tags: (input.tags || []).map((t) => t.trim().toLowerCase()).filter(Boolean),
      createdAt: new Date().toISOString(),
    };

    const all = this.getStoredLinks();
    all.unshift(newLink);
    this.saveStoredLinks(all);

    return newLink;
  }

  async updateLink(id: string, input: UpdateLinkInput): Promise<Link> {
    await delay(200);
    const all = this.getStoredLinks();
    const index = all.findIndex((l) => l.id === id);
    if (index === -1) {
      throw new Error(`Link with ID ${id} not found`);
    }

    const current = all[index];
    const updated: Link = {
      ...current,
      userNotes: input.userNotes !== undefined ? input.userNotes.trim() : current.userNotes,
      tags:
        input.tags !== undefined
          ? input.tags.map((t) => t.trim().toLowerCase()).filter(Boolean)
          : current.tags,
      updatedAt: new Date().toISOString(),
    };

    all[index] = updated;
    this.saveStoredLinks(all);
    return updated;
  }

  async deleteLink(id: string): Promise<void> {
    await delay(200);
    const all = this.getStoredLinks().filter((l) => l.id !== id);
    this.saveStoredLinks(all);
  }

  async downloadVideo(
    id: string,
    onProgress?: (progress: DownloadProgress) => void
  ): Promise<{ downloadUrl: string; filename: string }> {
    const totalBytes = 14 * 1024 * 1024;
    onProgress?.({ loaded: 1 * 1024 * 1024, total: totalBytes, percent: 10 });
    await delay(120);
    onProgress?.({ loaded: 6 * 1024 * 1024, total: totalBytes, percent: 45 });
    await delay(120);
    onProgress?.({ loaded: 11 * 1024 * 1024, total: totalBytes, percent: 80 });
    await delay(120);
    onProgress?.({ loaded: totalBytes, total: totalBytes, percent: 100 });

    const link = await this.getLinkById(id);
    if (link.siteType !== 'youtube') {
      throw new Error('Only YouTube links support direct video streaming download');
    }

    const safeFilename = `${link.title.replace(/[^a-zA-Z0-9_-]/g, '_')}_720p.mp4`;
    // Create a mock streamable blob for client-side demo
    const mockBlob = new Blob(
      [
        `Mock 720p Video Stream for: ${link.title}\nSource: ${link.url}\nTimestamp: ${new Date().toISOString()}`,
      ],
      { type: 'video/mp4' }
    );
    const downloadUrl = URL.createObjectURL(mockBlob);

    return {
      downloadUrl,
      filename: safeFilename,
    };
  }
}

export const mockLinkService = new MockLinkService();
