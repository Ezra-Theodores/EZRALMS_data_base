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
  
  // Navigate to G8-01.1 (click the topic, not the view button)
  const topic = page.locator('text=G8-01.1 Integers').first();
  await topic.click();
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'C:/Users/Admin/Repo/EzraLms_automation/lesson-page.png', fullPage: true });
  
  const html = await page.content();
  const fs = require('fs');
  fs.writeFileSync('C:/Users/Admin/Repo/EzraLms_automation/lesson-page.html', html);
  
  const bodyText = await page.locator('body').innerText();
  console.log('Lesson page text:\n', bodyText.slice(0, 3000));
  
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });