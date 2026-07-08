const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: '/opt/google/chrome/chrome', args: ['--no-sandbox'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(800);
  for (const inp of await page.locator('input[type="text"]').all()) {
    const ph = await inp.getAttribute('placeholder');
    if (ph && ph.includes('用户')) { await inp.fill('admin'); break; }
  }
  await page.locator('input[type="password"]').first().fill('admin123');
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(2500);
  await page.goto('http://localhost:3000/scenes', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
  await page.locator('button').filter({ hasText: /新建场景/ }).first().click();
  await page.waitForTimeout(1500);

  const dialogHtml = await page.locator('.el-dialog').innerHTML().catch(() => 'NO DIALOG');
  console.log('Dialog HTML (first 1500 chars):');
  console.log(dialogHtml.substring(0, 1500));
  await page.screenshot({ path: '/workspace/images/ui_test/debug_scene_dialog.png' });
  await browser.close();
})();
