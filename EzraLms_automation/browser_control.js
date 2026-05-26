const { chromium } = require('@playwright/test');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Login & navigate
  await page.goto('https://students.ezralms.com/login');
  await page.getByRole('textbox', { name: 'Username or Email' }).fill('EzraT');
  await page.getByRole('button', { name: 'Continue' }).click();
  await page.getByRole('textbox', { name: '-Digit PIN' }).fill('223183');
  await page.getByRole('button', { name: 'Sign In', exact: true }).click();
  await page.waitForURL('**/tutor-dashboard', { timeout: 10000 });
  await page.getByRole('link', { name: 'Classes' }).click();
  await page.waitForTimeout(2000);
  await page.getByRole('textbox', { name: 'Search classes...' }).fill('G8 NATIONAL PLUS');
  await page.waitForTimeout(2000);
  await page.getByText('G8 NATIONAL PLUS').click();
  await page.waitForTimeout(3000);
  
  console.log('READY');
  
  const cmdFile = 'C:/Users/Admin/Repo/EZRALMS_data_base/EzraLms_automation/cmd.json';
  let lastCmd = '';
  
  while (true) {
    await page.waitForTimeout(1500);
    try {
      if (fs.existsSync(cmdFile)) {
        const cmd = JSON.parse(fs.readFileSync(cmdFile, 'utf-8'));
        if (cmd.id !== lastCmd) {
          lastCmd = cmd.id;
          console.log('CMD:', JSON.stringify(cmd));
          try {
            if (cmd.action === 'hover') {
              await page.hover(cmd.selector);
              await page.waitForTimeout(1500);
              console.log('HOVERED');
            } else if (cmd.action === 'screenshot') {
              await page.screenshot({ path: cmd.path, fullPage: true });
              console.log('SCREENSHOT');
            } else if (cmd.action === 'click') {
              await page.click(cmd.selector);
              await page.waitForTimeout(2000);
              console.log('CLICKED');
            }
          } catch (e) { console.log('ERR:', e.message); }
          fs.unlinkSync(cmdFile);
        }
      }
    } catch (e) {}
  }
})();