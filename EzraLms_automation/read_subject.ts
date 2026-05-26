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
  
  // Click on G8-01.1 Integers, Powers and Roots via aria-label
  await page.getByRole('button', { name: 'View G8-01.1 Integers, Powers and Roots' }).click();
  await page.waitForTimeout(3000);
  
  await page.screenshot({ path: 'C:/Users/Admin/Repo/EzraLms_automation/G8-01.1-content.png', fullPage: true });
  console.log('Screenshot saved');
  
  // Get all content from the page
  const content = await page.locator('body').innerText();
  console.log('=== PAGE CONTENT ===');
  console.log(content);
  
  // Also try to get HTML content
  const html = await page.content();
  const fs = require('fs');
  fs.writeFileSync('C:/Users/Admin/Repo/EzraLms_automation/G8-01.1.html', html);
  console.log('HTML saved to file');
  
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });