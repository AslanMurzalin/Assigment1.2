import { test, expect } from '@playwright/test';

test('has title and loads auth page', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Link Saver|Vite/i);
  await expect(page.getByRole('heading', { name: 'Link Saver' })).toBeVisible();
});
