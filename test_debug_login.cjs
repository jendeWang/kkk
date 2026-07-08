const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: '/opt/google/chrome/chrome' });
  const page = await browser.newPage();
  await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/workspace/images/ui_test/debug_login.png' });

  const inputs = await page.locator('input').all();
  console.log(`Found ${inputs.length} inputs:`);
  for (let i = 0; i < inputs.length; i++) {
    const type = await inputs[i].getAttribute('type');
    const readonly = await inputs[i].getAttribute('readonly');
    const placeholder = await inputs[i].getAttribute('placeholder');
    const cls = await inputs[i].getAttribute('class');
    console.log(`  ${i}: type=${type}, readonly=${readonly}, placeholder=${placeholder}, class=${cls}`);
  }

  await browser.close();
})();
