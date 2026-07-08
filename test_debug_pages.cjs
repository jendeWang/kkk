const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--use-angle=default', '--enable-webgl'] 
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  
  // Capture console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error' || msg.type() === 'warning') {
      consoleErrors.push(`${msg.type()}: ${msg.text()}`);
    }
  });
  page.on('pageerror', err => consoleErrors.push(`PAGE ERROR: ${err.message}`));

  try {
    // Login
    await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button:has-text("登录")');
    await page.waitForTimeout(2000);

    // Test BigScreen
    console.log('=== BigScreen ===');
    consoleErrors.length = 0;
    await page.goto('http://localhost:3000/bigscreen', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(5000);
    
    console.log('URL:', page.url());
    console.log('Title:', await page.title());
    const bsHtml = await page.locator('#app').innerHTML().catch(() => 'EMPTY');
    console.log('App innerHTML length:', bsHtml.length);
    console.log('App innerHTML (first 500):', bsHtml.substring(0, 500));
    console.log('Canvas count:', await page.locator('canvas').count());
    console.log('Errors:', consoleErrors.slice(0, 5).join('\n'));

    // Test 3D
    console.log('\n=== Greenhouse3D ===');
    consoleErrors.length = 0;
    await page.goto('http://localhost:3000/greenhouse3d', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(5000);
    
    console.log('URL:', page.url());
    const tdHtml = await page.locator('#app').innerHTML().catch(() => 'EMPTY');
    console.log('App innerHTML length:', tdHtml.length);
    console.log('App innerHTML (first 500):', tdHtml.substring(0, 500));
    console.log('Canvas count:', await page.locator('canvas').count());
    console.log('Switch count:', await page.locator('.el-switch').count());
    console.log('Errors:', consoleErrors.slice(0, 5).join('\n'));

  } catch (e) {
    console.error('Error:', e.message);
  }
  
  await browser.close();
})();
