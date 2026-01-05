import { test, expect } from '@playwright/test';

test('homepage has content', async ({ page }) => {
  const base = process.env.BASE_URL || 'http://localhost:3000';
  await page.goto(base);
  await expect(page.locator('body')).toBeVisible();
});
