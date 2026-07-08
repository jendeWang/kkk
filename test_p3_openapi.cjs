const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/opt/google/chrome/chrome',
    args: ['--disable-web-security', '--no-sandbox']
  });

  const results = [];
  const log = (name, pass, detail = '') => {
    results.push({ name, pass, detail });
    console.log(`${pass ? '✅' : '❌'} ${name}${detail ? ' — ' + detail : ''}`);
  };

  try {
    console.log('📖 OpenAPI 文档测试');
    
    // Test Swagger UI
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    
    // Test Swagger endpoint
    await page.goto('http://localhost:8000/docs', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/p3_openapi_01.png' });
    
    const swaggerTitle = await page.locator('h1').first().textContent().catch(() => '');
    log('1. Swagger UI loads', swaggerTitle.includes('API'), `title: ${swaggerTitle}`);
    
    const apiTags = await page.locator('.opblock-tag').all();
    const tagNames = [];
    for (const tag of apiTags) {
      tagNames.push(await tag.textContent());
    }
    log('2. API tags visible', tagNames.length > 0, `tags: [${tagNames.join(', ')}]`);
    
    // Test Redoc endpoint
    await page.goto('http://localhost:8000/redoc', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/p3_openapi_02.png' });
    
    const redocTitle = await page.locator('h1').first().textContent().catch(() => '');
    log('3. Redoc UI loads', redocTitle.length > 0, `title: ${redocTitle}`);
    
    // Test OpenAPI JSON spec
    const response = await page.goto('http://localhost:8000/openapi.json', { waitUntil: 'domcontentloaded' });
    const contentType = response.headers()['content-type'] || '';
    log('4. OpenAPI JSON endpoint', contentType.includes('application/json'), `content-type: ${contentType}`);
    
    // Check API endpoints count
    const jsonContent = await page.textContent('body');
    const spec = JSON.parse(jsonContent);
    const paths = Object.keys(spec.paths || {});
    log('5. API endpoints count', paths.length > 10, `count: ${paths.length}`);
    
    // Verify key endpoints exist
    const keyPaths = ['/api/v1/devices/', '/api/v1/auth/login', '/api/v1/alert_rules/', '/api/v1/scenes/'];
    for (const path of keyPaths) {
      log(`6. ${path} exists`, paths.includes(path));
    }
    
    await context.close();
    
  } catch (e) {
    console.error('Test error:', e.message);
  }

  const passed = results.filter(r => r.pass).length;
  const failed = results.filter(r => !r.pass).length;
  console.log(`\n${'='.repeat(50)}`);
  console.log(`  P3 OPENAPI TEST SUMMARY`);
  console.log(`  Total: ${results.length} | Passed: ${passed} | Failed: ${failed}`);
  console.log(`${'='.repeat(50)}`);

  await browser.close();
})();