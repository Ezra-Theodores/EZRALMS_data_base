const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Login
  await page.goto('https://students.ezralms.com/login');
  await page.getByRole('textbox', { name: 'Username or Email' }).fill('EzraT');
  await page.getByRole('button', { name: 'Continue' }).click();
  await page.getByRole('textbox', { name: '-Digit PIN' }).fill('223183');
  await page.getByRole('button', { name: 'Sign In', exact: true }).click();
  await page.waitForURL('**/tutor-dashboard', { timeout: 10000 });
  console.log('Logged in, on dashboard');

  // Navigate to Classes
  await page.getByRole('link', { name: 'Classes', exact: true }).click();
  await page.waitForTimeout(2000);

  // Search for class 8 Nasional
  await page.getByRole('textbox', { name: 'Search classes...' }).fill('8 Nasional');
  await page.waitForTimeout(3000);

  // Take screenshot
  await page.screenshot({ path: 'C:/Users/Admin/Repo/EzraLms_automation/class-search.png', fullPage: true });
  console.log('Screenshot saved');

  // Get all class cards
  const cards = page.locator('.class-card, .module-card, [class*="card"]');
  const count = await cards.count();
  console.log('Class cards found:', count);

  // Print the page content for inspection
  const classNames = await page.locator('text=8').allTextContents();
  console.log('Texts containing 8:', classNames.slice(0, 20));

  await browser.close();
  console.log('Done');
})().catch(e => { console.error(e.message); process.exit(1); });