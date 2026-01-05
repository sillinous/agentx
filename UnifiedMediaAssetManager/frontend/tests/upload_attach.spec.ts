import { test, expect, request } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const BACKEND = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const FRONTEND = process.env.FRONTEND_URL || 'http://127.0.0.1:3000';

test('Upload image via UI, attach and render on element page', async ({ page }) => {
  const req = await request.newContext();
  const tokenResp = await req.post(`${BACKEND}/auth/dev-token`);
  expect(tokenResp.ok()).toBeTruthy();
  const token = (await tokenResp.json()).token;
  const headers = { Authorization: `Bearer ${token}` };

  // Create universe and element via backend API
  const uniResp = await req.post(`${BACKEND}/universes`, { headers, data: { name: 'Upload Uni', description: 'test' } });
  expect(uniResp.ok()).toBeTruthy();
  const uni = await uniResp.json();

  const elResp = await req.post(`${BACKEND}/universes/${uni.id}/elements`, { headers, data: { name: 'Upload Element', element_type: 'Generic' } });
  expect(elResp.ok()).toBeTruthy();
  const el = await elResp.json();

  // Create a small PNG file from base64
  const pngBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=";
  const tmpDir = path.join(process.cwd(), 'frontend', 'tests', 'tmp');
  if (!fs.existsSync(tmpDir)) fs.mkdirSync(tmpDir, { recursive: true });
  const tmpFile = path.join(tmpDir, 'test-upload.png');
  fs.writeFileSync(tmpFile, Buffer.from(pngBase64, 'base64'));

  // Navigate to element page and upload via file input
  await page.goto(`${FRONTEND}/universes/${uni.id}/elements/${el.id}`);
  // wait for input to be present
  const fileInput = page.locator('input[type="file"]');
  await expect(fileInput).toHaveCount(1);
  await fileInput.setInputFiles(tmpFile);
  // Click the upload button
  const uploadButton = page.locator('button', { hasText: 'Upload & Attach' });
  await uploadButton.click();

  // Wait for image to appear in components
  const img = page.locator('img').first();
  await expect(img).toBeVisible({ timeout: 5000 });
  const src = await img.getAttribute('src');
  expect(src).toBeTruthy();

  // cleanup tmp file
  try { fs.unlinkSync(tmpFile); } catch {}
});
