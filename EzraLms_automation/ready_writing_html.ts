import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('https://students.ezralms.com/class/SNk7dy7ONmkXV6JwUHVw');
  await page.getByRole('textbox', { name: 'e.g. Introduction to Fractions' }).click();
  await page.getByRole('textbox', { name: 'e.g. Introduction to Fractions' }).fill('');
  await page.getByRole('textbox', { name: 'e.g. Introduction to Fractions' }).press('CapsLock');
  await page.getByRole('textbox', { name: 'e.g. Introduction to Fractions' }).fill('G04-01.2 ');
  await page.getByRole('textbox', { name: 'e.g. Introduction to Fractions' }).press('CapsLock');
  await page.getByRole('textbox', { name: 'e.g. Introduction to Fractions' }).fill('G04-01.2 Integer Operation');
  await page.getByRole('textbox', { name: 'Brief description…' }).click();
  await page.getByRole('textbox', { name: 'Brief description…' }).fill('Operasi bilangan bulat');
  await page.getByRole('button', { name: 'Create & Open Editor' }).click();
  await page.getByRole('textbox', { name: '<html>\\n <body>\\n <h1>Hello' }).click();
});