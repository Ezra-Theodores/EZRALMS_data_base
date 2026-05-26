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
  console.log('Logged in');

  await page.getByRole('link', { name: 'Classes', exact: true }).click();
  await page.waitForTimeout(2000);

  // Take screenshot
  await page.screenshot({ path: 'C:/Users/Admin/Repo/EzraLms_automation/class-list.png', fullPage: true });

  // Get all visible text
  const allText = await page.locator('body').innerText();
  console.log('Page content:');
  console.log(allText);

  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });