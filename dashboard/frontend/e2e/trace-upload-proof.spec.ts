import { expect, test } from "@playwright/test";

test("deliberate failure for trace upload verification", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("trace-upload-proof-marker", { exact: true })).toBeVisible({ timeout: 500 });
});
