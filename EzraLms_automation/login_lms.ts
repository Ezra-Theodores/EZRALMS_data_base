import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('https://students.ezralms.com/login');
  await page.getByRole('textbox', { name: 'Username or Email' }).click();
  await page.getByRole('textbox', { name: 'Username or Email' }).fill('EzraT');
  await page.getByRole('button', { name: 'Continue' }).click();
  await page.getByRole('textbox', { name: '-Digit PIN' }).fill('223183');
  await page.getByRole('button', { name: 'Sign In', exact: true }).click();
});