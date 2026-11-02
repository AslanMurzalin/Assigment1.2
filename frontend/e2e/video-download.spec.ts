import { test, expect } from '@playwright/test';
import { setupMockApi, loginAsAuthenticatedUser } from './helpers/mockApi';

test.describe('Video Streaming Download E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAuthenticatedUser(page);
    await setupMockApi(page);
    await page.goto('/');
  });

  test('YouTube link card displays 720p stream download button', async ({ page }) => {
    const youtubeCard = page.locator('div.group', { hasText: 'Rick Astley' });
    await expect(youtubeCard.getByRole('button', { name: /download \(720p stream\)/i })).toBeVisible();
  });

  test('initiates video download and displays visual progress bar and completion', async ({ page }) => {
    const youtubeCard = page.locator('div.group', { hasText: 'Rick Astley' });
    const downloadBtn = youtubeCard.getByRole('button', { name: /download \(720p stream\)/i });

    await downloadBtn.click();

    // Verify progress bar / completion
    await expect(
      youtubeCard.getByText(/Streaming 720p\.\.\.|Download Complete! File Saved\./i)
    ).toBeVisible();

    // Verify completed status badge
    await expect(youtubeCard.getByText('Download Complete! File Saved.')).toBeVisible({
      timeout: 10000,
    });
  });
});
