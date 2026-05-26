import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('https://students.ezralms.com/class/SNk7dy7ONmkXV6JwUHVw');
  await page.getByRole('button', { name: 'Add Sub-topic' }).nth(4).click();
  await page.getByRole('button', { name: '📖 Subject Matter' }).nth(1).click();
  await page.getByRole('button', { name: '📖 Create New Subject Matter' }).click();
});