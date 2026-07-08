const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: '/opt/google/chrome/chrome', args: ['--no-sandbox'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(800);
  const inputs = await page.locator('input[type="text"]').all();
  for (const inp of inputs) {
    const ph = await inp.getAttribute('placeholder');
    if (ph && ph.includes('用户')) { await inp.fill('admin'); break; }
  }
  await page.locator('input[type="password"]').first().fill('admin123');
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(2500);

  await page.goto('http://localhost:3000/alert-rules', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);

  const buttons = await page.locator('button').all();
  console.log(`Found ${buttons.length} buttons:`);
  for (let i = 0; i < buttons.length; i++) {
    const text = await buttons[i].textContent();
    const cls = await buttons[i].getAttribute('class');
    console.log(`  ${i}: "${text?.trim()}" class=${cls}`);
  }

  await page.screenshot({ path: '/workspace/images/ui_test/debug_alert_rules.png' });
  await browser.close();
})();
