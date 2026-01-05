// apps/web/e2e/home.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should load successfully and display main elements', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Synapse - AI Agent Platform/); // Updated title check

    // Check for the SYNAPSE logo text in the nav bar
    await expect(page.locator('nav').getByText('SYNAPSE')).toBeVisible();

    // Check for the Control and Command mode toggle buttons
    await expect(page.getByRole('button', { name: 'Control' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Command' })).toBeVisible();

    // Click the 'Command' button to switch to command mode
    await page.getByRole('button', { name: 'Command' }).click();

    // Now, check for the presence of an input field and a submit button in 'command' mode
    await expect(page.getByPlaceholder('Command the swarm...')).toBeVisible();
    // Updated selector for the submit button
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should allow form submission and show a loading state or response', async ({ page }) => {
    await page.goto('/');

    // Ensure we are in 'command' mode by clicking the 'Command' button
    await page.getByRole('button', { name: 'Command' }).click();

    // Wait for the initial system message to be visible
    await expect(
      page.getByText('Genesis Complete. Agents are online. Waiting for command...'),
    ).toBeVisible();

    // Fill the input field
    await page
      .getByPlaceholder('Command the swarm...')
      .fill('Generate a marketing slogan for a new coffee shop.');

    // Click the submit button
    await page.locator('button[type="submit"]').click();

    // Expect a loading indicator (bouncing circles) to appear immediately after clicking submit
    await expect(page.locator('.animate-bounce').first()).toBeVisible();

    // Start waiting for the API response
    const response = await page.waitForResponse(
      (response) => response.url().includes('/api/agent') && response.request().method() === 'POST',
    );

    // Wait for the loading indicator to disappear
    await expect(page.locator('.animate-bounce').first()).toBeHidden();

    // Get all chat messages using the class name locator
    const chatMessages = page
      .locator('.flex-1.overflow-y-auto.p-4.space-y-4.scrollbar-thin.scrollbar-thumb-slate-700')
      .locator('> div');
    // Assert that there are at least 3 messages (initial system + user + error system)
    await expect(chatMessages).toHaveCount(3);

    // Get the text of the last message in the chat history
    const lastMessageText = await chatMessages.last().locator('.text-sm').textContent();

    // Assert that the last message contains the expected error message.
    // The screenshot shows "Error: fetch failed"
    expect(lastMessageText).toContain('Error: fetch failed');
  });
});
