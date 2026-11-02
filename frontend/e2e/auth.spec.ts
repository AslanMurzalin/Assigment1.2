import { test, expect } from '@playwright/test';
import { setupMockApi } from './helpers/mockApi';

test.describe('Authentication E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await setupMockApi(page);
  });

  test('displays login screen with branding', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Link Saver' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
    await expect(page.locator('#login-email')).toBeVisible();
    await expect(page.locator('#login-password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible();
  });

  test('shows validation error on empty submit', async ({ page }) => {
    await page.goto('/');
    // Remove HTML5 required to test custom client JS validation
    await page.$eval('#login-email', (el: HTMLInputElement) => el.removeAttribute('required'));
    await page.$eval('#login-password', (el: HTMLInputElement) => el.removeAttribute('required'));
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByRole('alert')).toContainText(/Please fill in both email and password/i);
  });

  test('shows error on invalid credentials', async ({ page }) => {
    await page.goto('/');
    await page.fill('#login-email', 'tester@linksaver.io');
    await page.fill('#login-password', 'wrongpassword');
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByRole('alert')).toContainText(/Invalid email or password/i);
  });

  test('switches to register form and back', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Create account' }).click();

    await expect(page.getByRole('heading', { name: 'Create an account' })).toBeVisible();
    await expect(page.locator('#reg-email')).toBeVisible();
    await expect(page.locator('#reg-password')).toBeVisible();
    await expect(page.locator('#reg-confirm-password')).toBeVisible();

    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  });

  test('registers a new account and redirects to dashboard', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Create account' }).click();

    await page.fill('#reg-email', 'newuser@linksaver.io');
    await page.fill('#reg-password', 'ValidPassword123!');
    await page.fill('#reg-confirm-password', 'ValidPassword123!');
    await page.getByRole('button', { name: 'Sign Up' }).click();

    // Authenticated dashboard layout
    await expect(page.getByText('Save a new link')).toBeVisible();
    await expect(page.getByTestId('user-email')).toHaveText('newuser@linksaver.io');
  });

  test('logs in successfully and logs out', async ({ page }) => {
    await page.goto('/');
    await page.fill('#login-email', 'tester@linksaver.io');
    await page.fill('#login-password', 'SecretPass123!');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Dashboard loaded
    await expect(page.getByText('Save a new link')).toBeVisible();
    await expect(page.getByTestId('user-email')).toHaveText('tester@linksaver.io');

    // Logout
    await page.getByRole('button', { name: /logout/i }).click();
    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  });
});
