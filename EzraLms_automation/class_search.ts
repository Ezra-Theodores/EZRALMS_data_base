import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('https://students.ezralms.com/tutor-dashboard');
  await page.getByRole('link', { name: 'Classes', exact: true }).click();
  await page.getByRole('textbox', { name: 'Search classes...' }).click();
});