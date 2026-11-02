import type { Page } from '@playwright/test';

export interface MockLink {
  id: string;
  user_id: string;
  url: string;
  title: string;
  description: string;
  site_type: 'generic' | 'youtube' | 'ozon' | 'wildberries' | 'aliexpress';
  user_notes: string;
  tags: string[];
  image_url?: string;
  price?: string;
  specs?: Record<string, string>;
  created_at: string;
  updated_at?: string;
}

export const INITIAL_MOCK_LINKS: MockLink[] = [
  {
    id: 'link-1',
    user_id: 'user-123',
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    title: 'Rick Astley - Never Gonna Give You Up (Official Music Video)',
    description: 'The official music video for Rick Astley.',
    site_type: 'youtube',
    user_notes: 'Iconic 80s hit video',
    tags: ['music', 'youtube', 'classics'],
    created_at: new Date().toISOString(),
  },
  {
    id: 'link-2',
    user_id: 'user-123',
    url: 'https://www.ozon.ru/product/wireless-mouse-11223344/',
    title: 'Logitech MX Master 3S Wireless Mouse',
    description: 'Ergonomic performance wireless mouse for Mac and Windows.',
    site_type: 'ozon',
    user_notes: 'Top ergonomics for work',
    tags: ['tech', 'mouse', 'gadgets'],
    price: '9 990 ₽',
    image_url: 'https://cdn1.ozone.ru/s3/multimedia-0/wc1000/6000000000.jpg',
    specs: {
      'Brand': 'Logitech',
      'DPI': '8000',
      'Connection': 'Bluetooth / Logi Bolt',
    },
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: 'link-3',
    user_id: 'user-123',
    url: 'https://react.dev/learn',
    title: 'Quick Start – React Documentation',
    description: 'Learn modern React with official interactive guides.',
    site_type: 'generic',
    user_notes: 'React state & effect rules',
    tags: ['frontend', 'react', 'docs'],
    created_at: new Date(Date.now() - 7200000).toISOString(),
  },
];

export async function setupMockApi(page: Page, initialLinks = INITIAL_MOCK_LINKS) {
  const links = [...initialLinks];
  let currentEmail = 'tester@linksaver.io';

  // Mock /api/v1/auth/signup
  await page.route('**/api/v1/auth/signup', async (route) => {
    const postData = route.request().postDataJSON();
    if (postData?.email) {
      currentEmail = postData.email;
    }
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'user-123',
        email: currentEmail,
        created_at: new Date().toISOString(),
      }),
    });
  });

  // Mock /api/v1/auth/login
  await page.route('**/api/v1/auth/login', async (route) => {
    const postData = route.request().postDataJSON();
    if (postData?.password === 'wrongpassword') {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid email or password' }),
      });
      return;
    }
    if (postData?.email) {
      currentEmail = postData.email;
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'mock-jwt-token-abcdef123456',
        token_type: 'bearer',
      }),
    });
  });

  // Mock /api/v1/auth/me
  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'user-123',
        email: currentEmail,
        created_at: new Date().toISOString(),
      }),
    });
  });

  // Mock GET /api/v1/links
  await page.route('**/api/v1/links?*', async (route) => {
    const url = new URL(route.request().url());
    const query = url.searchParams.get('q')?.toLowerCase();
    const tag = url.searchParams.get('tag')?.toLowerCase();

    let filtered = [...links];
    if (query) {
      filtered = filtered.filter(
        (l) =>
          l.title.toLowerCase().includes(query) ||
          l.url.toLowerCase().includes(query) ||
          l.user_notes.toLowerCase().includes(query)
      );
    }
    if (tag) {
      filtered = filtered.filter((l) => l.tags.some((t) => t.toLowerCase() === tag));
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(filtered),
    });
  });

  await page.route('**/api/v1/links', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(links),
      });
      return;
    }

    if (route.request().method() === 'POST') {
      const postData = route.request().postDataJSON();
      const newLink: MockLink = {
        id: `link-${Date.now()}`,
        user_id: 'user-123',
        url: postData.url,
        title: postData.url.includes('youtube')
          ? 'Automated YouTube Video Title'
          : 'Extracted Link Title for ' + postData.url,
        description: 'Auto-extracted description for ' + postData.url,
        site_type: postData.url.includes('youtube') ? 'youtube' : 'generic',
        user_notes: postData.user_notes || '',
        tags: postData.tags || [],
        created_at: new Date().toISOString(),
      };
      links.unshift(newLink);

      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(newLink),
      });
      return;
    }

    await route.continue();
  });

  // Mock PATCH /api/v1/links/:id
  await page.route(/\/api\/v1\/links\/[^/?#]+$/, async (route) => {
    const method = route.request().method();
    const url = route.request().url();
    const id = url.substring(url.lastIndexOf('/') + 1);

    if (method === 'PATCH') {
      const postData = route.request().postDataJSON();
      const link = links.find((l) => l.id === id);
      if (link) {
        if (postData.user_notes !== undefined) link.user_notes = postData.user_notes;
        if (postData.tags !== undefined) link.tags = postData.tags;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(link),
      });
      return;
    }

    if (method === 'DELETE') {
      const idx = links.findIndex((l) => l.id === id);
      if (idx !== -1) {
        links.splice(idx, 1);
      }
      await route.fulfill({
        status: 204,
        body: '',
      });
      return;
    }

    await route.continue();
  });

  // Mock GET /api/v1/links/:id/download
  await page.route(/\/api\/v1\/links\/[^/?#]+\/download$/, async (route) => {
    // Return dummy MP4 binary chunk with headers for progress bar
    const dummyVideo = new Uint8Array(1024 * 1024); // 1 MB
    await route.fulfill({
      status: 200,
      headers: {
        'Content-Type': 'video/mp4',
        'Content-Disposition': 'attachment; filename="test_video_720p.mp4"',
        'Content-Length': dummyVideo.length.toString(),
        'X-Estimated-Content-Length': dummyVideo.length.toString(),
        'Access-Control-Expose-Headers': 'Content-Length, Content-Disposition, X-Estimated-Content-Length',
      },
      body: Buffer.from(dummyVideo),
    });
  });

  return links;
}

export async function loginAsAuthenticatedUser(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('link_saver_auth_token', 'mock-jwt-token-abcdef123456');
    localStorage.setItem(
      'link_saver_current_user',
      JSON.stringify({
        id: 'user-123',
        email: 'tester@linksaver.io',
        createdAt: new Date().toISOString(),
      })
    );
  });
}
