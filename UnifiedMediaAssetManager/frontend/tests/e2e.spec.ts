import { test, expect, request } from '@playwright/test';

const BACKEND = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const FRONTEND = process.env.FRONTEND_URL || 'http://127.0.0.1:3000';

test('AI generate -> attach -> render image on element page', async ({ page }) => {
  // Acquire a dev token
  const req = await request.newContext();
  const tokenResp = await req.post(`${BACKEND}/auth/dev-token`);
  expect(tokenResp.ok()).toBeTruthy();
  const tokenBody = await tokenResp.json();
  const token = tokenBody.token;

  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  // Create a universe
  const uniResp = await req.post(`${BACKEND}/universes`, { headers, data: { name: 'E2E Universe', description: 'test' } });
  expect(uniResp.ok()).toBeTruthy();
  const uni = await uniResp.json();

  // Create an element
  const elResp = await req.post(`${BACKEND}/universes/${uni.id}/elements`, { headers, data: { name: 'E2E Element', element_type: 'Generic' } });
  expect(elResp.ok()).toBeTruthy();
  const el = await elResp.json();

  // Generate an image via AI endpoint
  const prompt = 'A minimal e2e test image';
  const genResp = await req.post(`${BACKEND}/ai/generate/image`, { headers, data: { prompt } });
  expect(genResp.ok()).toBeTruthy();
  const gen = await genResp.json();
  expect(gen.url).toBeTruthy();

  // Attach the image as ImageComponent
  const comp = {
    type: 'ImageComponent',
    data: { label: 'E2E Image', url: gen.url, prompt }
  };
  const addCompResp = await req.post(`${BACKEND}/universes/${uni.id}/elements/${el.id}/components`, { headers, data: comp });
  expect(addCompResp.ok()).toBeTruthy();

  // Now load the frontend element page and assert the image is displayed
  await page.goto(`${FRONTEND}/universes/${uni.id}/elements/${el.id}`);
  // Wait for image to appear
  const img = page.locator('img');
  await expect(img).toBeVisible();
  const src = await img.first().getAttribute('src');
  expect(src).toBeTruthy();

  // Reload the page and ensure the component persists and image still present
  await page.reload();
  const img2 = page.locator('img');
  await expect(img2.first()).toBeVisible();

  // Verify backend lists the component
  const compsResp = await req.get(`${BACKEND}/universes/${uni.id}/elements` , { headers });
  expect(compsResp.ok()).toBeTruthy();
  const elements = await compsResp.json();
  const found = elements.find((e: any) => e.id === el.id);
  expect(found).toBeTruthy();
  const imageComponents = found.components.filter((c: any) => c.type === 'ImageComponent');
  expect(imageComponents.length).toBeGreaterThanOrEqual(1);
});
