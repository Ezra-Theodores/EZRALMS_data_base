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
  
  // First click on the G8-01.1 topic area to expand it
  const topicArea = page.locator('text=G8-01.1 Integers');
  await topicArea.click({ timeout: 5000 }).catch(async () => {
    // Try clicking the parent card
    const card = page.locator('.bg-white', { has: page.locator('text=G8-01.1') }).first();
    await card.click().catch(e => console.log('Card click failed:', e.message));
  });
  
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'C:/Users/Admin/Repo/EzraLms_automation/after-click-g8-01.1.png', fullPage: true });
  
  // Get current URL
  console.log('URL after click:', page.url());
  
  // Look for edit/edit icon  
  const html = await page.content();
  const fs = require('fs');
  fs.writeFileSync('C:/Users/Admin/Repo/EzraLms_automation/after-click-g8-01.1.html', html);
  
  // Check for any menu buttons (three dots / kebab menu)
  const kebabMenus = await page.locator('[aria-label*="menu"], [aria-label*="edit"], [class*="menu"]').allTextContents();
  console.log('Menu/edit buttons:', kebabMenus);
  
  // Try right-clicking on the G8-01.1 subject matter card
  const card = page.locator('[class*="card"]').filter({ hasText: 'G8-01.1' }).first();
  const cardCount = await card.count();
  console.log('G8-01.1 card found:', cardCount);
  if (cardCount > 0) {
    await card.click({ button: 'right' });
    await page.waitForTimeout(1000);
    const contextText = await page.locator('[role="menu"], [class*="context"]').innerText().catch(() => '');
    console.log('Context menu:', contextText);
  }
  
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });