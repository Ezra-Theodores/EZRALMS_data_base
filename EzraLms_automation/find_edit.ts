const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  await page.goto('https://students.ezralms.com/login');
  await page.getByRole('textbox', { name: 'Username or Email' }).fill('EzraT');
  await page.getByRole('button', { name: 'Continue' }).click();
  await page.getByRole('textbox', { name: '-Digit PIN' }).fill('223183');
  await page.getByRole('button', { name: 'Sign In', exact: true }).click();
  await page.waitForURL('**/tutor-dashboard', { timeout: 10000 });
  await page.getByRole('link', { name: 'Classes', exact: true }).click();
  await page.waitForTimeout(2000);
  await page.getByRole('textbox', { name: 'Search classes...' }).fill('G8 NATIONAL PLUS');
  await page.waitForTimeout(2000);
  await page.getByText('G8 NATIONAL PLUS').click();
  await page.waitForTimeout(2000);
  
  // Click on G8-01.1 to open it
  await page.getByRole('button', { name: 'View G8-01.1 Integers, Powers and Roots' }).click();
  await page.waitForTimeout(2000);
  
  // Take screenshot to see the page
  await page.screenshot({ path: 'C:/Users/Admin/Repo/EzraLms_automation/G8-01.1-open.png', fullPage: true });
  
  // Look for edit button - try clicking the subject matter card first
  const editBtn = page.locator('button, a').filter({ hasText: /edit/i }).first();
  const count = await editBtn.count();
  console.log('Edit buttons found:', count);
  
  // Get all interactive elements
  const allText = await page.locator('button, a, [role="button"]').allTextContents();
  console.log('Buttons/links on page:', allText.slice(0, 30));
  
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });