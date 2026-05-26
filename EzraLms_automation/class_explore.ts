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
  
  // Screenshot the class page with subtopics visible
  await page.screenshot({ path: 'C:/Users/Admin/Repo/EzraLms_automation/class-subtopics.png', fullPage: true });
  
  // Get all subject matter cards and look for G8-01.1
  const allButtons = await page.locator('button').allTextContents();
  console.log('All buttons:', allButtons);
  
  // Try to find edit buttons near subject matter
  const allHtml = await page.content();
  const fs = require('fs');
  fs.writeFileSync('C:/Users/Admin/Repo/EzraLms_automation/class-full.html', allHtml);
  
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });