import { test, expect } from '@playwright/test';
import { setupMockApi, loginAsAuthenticatedUser } from './helpers/mockApi';

test.describe('Links Management & Dashboard E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAuthenticatedUser(page);
    await setupMockApi(page);
    await page.goto('/');
  });

  test('displays saved links list with badges', async ({ page }) => {
    // Check initial cards rendered
    await expect(page.getByText('Rick Astley - Never Gonna Give You Up')).toBeVisible();
    await expect(page.getByText('Logitech MX Master 3S Wireless Mouse')).toBeVisible();
    await expect(page.getByText('Quick Start – React Documentation')).toBeVisible();

    // Check badges
    await expect(page.getByText('YouTube (720p)')).toBeVisible();
    await expect(page.locator('span:text-is("Ozon")')).toBeVisible();
    await expect(page.locator('span:text-is("Generic")')).toBeVisible();

    // Check marketplace price and details
    await expect(page.getByText('9 990 ₽')).toBeVisible();
  });

  test('submits a new link with tags and notes', async ({ page }) => {
    await page.fill('#link-url', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    await page.fill('#link-notes', 'Best song of all time');

    // Add a tag
    await page.fill('#link-tags', 'greatmusic');
    await page.locator('#link-tags').press('Enter');
    await expect(page.getByText('#greatmusic')).toBeVisible();

    // Submit
    await page.getByRole('button', { name: /save link/i }).click();

    // Verify created link appears
    await expect(page.getByText('Automated YouTube Video Title')).toBeVisible();
  });

  test('filters links by search query', async ({ page }) => {
    const searchInput = page.getByRole('searchbox', { name: /search links/i });
    await searchInput.fill('Logitech');

    // Matching link visible
    await expect(page.getByText('Logitech MX Master 3S Wireless Mouse')).toBeVisible();

    // Non-matching links filtered out
    await expect(page.getByText('Rick Astley - Never Gonna Give You Up')).not.toBeVisible();
    await expect(page.getByText('Quick Start – React Documentation')).not.toBeVisible();

    // Clear search
    await page.getByRole('button', { name: /clear search text/i }).click();
    await expect(page.getByText('Rick Astley - Never Gonna Give You Up')).toBeVisible();
  });

  test('filters links by clicking a tag pill', async ({ page }) => {
    // Click on #tech tag in the top tag filter bar
    await page.getByRole('button', { name: '#tech' }).first().click();

    // Only Ozon mouse has #tech
    await expect(page.getByText('Logitech MX Master 3S Wireless Mouse')).toBeVisible();
    await expect(page.getByText('Rick Astley - Never Gonna Give You Up')).not.toBeVisible();

    // Click 'All' to reset
    await page.getByRole('button', { name: 'All', exact: true }).click();
    await expect(page.getByText('Rick Astley - Never Gonna Give You Up')).toBeVisible();
  });

  test('edits notes and tags via modal', async ({ page }) => {
    // Find the edit button for Rick Astley card
    const firstCard = page.locator('div.group', { hasText: 'Rick Astley' });
    await firstCard.getByLabel('Edit notes and tags').click();

    // Modal opens
    await expect(page.getByRole('heading', { name: 'Edit notes & tags' })).toBeVisible();

    // Modify notes
    await page.fill('#edit-notes', 'Updated favorite dance track');
    await page.getByRole('button', { name: /save changes/i }).click();

    // Verify modal closed and updated notes displayed
    await expect(page.getByRole('heading', { name: 'Edit notes & tags' })).not.toBeVisible();
    await expect(page.getByText('Updated favorite dance track')).toBeVisible();
  });

  test('deletes a link with confirmation', async ({ page }) => {
    // Auto-accept window.confirm
    page.on('dialog', (dialog) => dialog.accept());

    const reactCard = page.locator('div.group', { hasText: 'Quick Start – React Documentation' });
    await reactCard.getByLabel('Delete link').click();

    // Verify link is removed from DOM
    await expect(page.getByText('Quick Start – React Documentation')).not.toBeVisible();
  });
});
