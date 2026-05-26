const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

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
  
  // Go to classes and open G8 NATIONAL PLUS
  await page.getByRole('link', { name: 'Classes', exact: true }).click();
  await page.waitForTimeout(2000);
  await page.getByRole('textbox', { name: 'Search classes...' }).fill('G8 NATIONAL PLUS');
  await page.waitForTimeout(2000);
  await page.getByText('G8 NATIONAL PLUS').click();
  await page.waitForTimeout(2000);
  
  console.log('BROWSER_READY');
  
  // Command loop
  const cmdFile = 'C:/Users/Admin/Repo/EZRALMS_data_base/EzraLms_automation/cmd.json';
  let lastCmd = '';
  
  while (true) {
    await page.waitForTimeout(2000);
    try {
      if (fs.existsSync(cmdFile)) {
        const cmd = JSON.parse(fs.readFileSync(cmdFile, 'utf-8'));
        if (cmd.id !== lastCmd) {
          lastCmd = cmd.id;
          console.log('CMD:' + JSON.stringify(cmd));
          try {
            if (cmd.action === 'click') {
              await page.locator(cmd.selector).click();
              await page.waitForTimeout(2000);
              const text = await page.locator('body').innerText();
              console.log('RESULT:' + text.slice(0, 500));
            } else if (cmd.action === 'hover') {
              await page.locator(cmd.selector).hover();
              await page.waitForTimeout(1500);
              const html = await page.content();
              return html;
            } else if (cmd.action === 'fill') {
              await page.locator(cmd.selector).fill(cmd.text);
              await page.waitForTimeout(2000);
              console.log('RESULT:filled');
            } else if (cmd.action === 'goto') {
              await page.goto(cmd.url);
              await page.waitForTimeout(3000);
              const text = await page.locator('body').innerText();
              console.log('RESULT:' + text.slice(0, 500));
            } else if (cmd.action === 'screenshot') {
              await page.screenshot({ path: cmd.path || 'C:/Users/Admin/Repo/EzraLms_automation/screenshot.png', fullPage: true });
              console.log('RESULT:screenshot saved');
            } else if (cmd.action === 'evaluate') {
              const result = await page.evaluate(cmd.script);
              console.log('RESULT:' + JSON.stringify(result));
            } else if (cmd.action === 'wait') {
              await page.waitForTimeout(cmd.ms || 3000);
              console.log('RESULT:waited');
            }
          } catch (e) {
            console.log('CMD_ERROR:' + e.message);
          }
          // Remove processed command
          fs.unlinkSync(cmdFile);
        }
      }
    } catch (e) {
      // ignore
    }
  }
})().catch(e => { console.error(e.message); process.exit(1); });