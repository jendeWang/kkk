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

  const buttons = await page.locator('button').all();
  console.log('Scene page buttons:');
  for (let i = 0; i < Math.min(buttons.length, 10); i++) {
    const text = await buttons[i].textContent();
    console.log(`  ${i}: "${text?.trim()}"`);
  }
  await browser.close();
})();
