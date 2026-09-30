import { expect, test } from "@playwright/test";

const BE = process.env.SEARCHSTUDIO_BE ?? "http://127.0.0.1:11226";

test("backend health", async ({ request }) => {
  const resp = await request.get(`${BE}/api/health`);
  expect(resp.status()).toBe(200);
  const body = await resp.json();
  expect(body.success).toBe(true);
});

test("frontend loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#root")).toBeAttached();
});
