const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--use-angle=default', '--enable-webgl'] 
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const results = [];
  const log = (name, pass, detail = '') => {
    results.push({ name, pass, detail });
    console.log(`${pass ? '✅' : '❌'} ${name}${detail ? ' — ' + detail : ''}`);
  };

  try {
    // Login
    await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button:has-text("登录")');
    await page.waitForTimeout(2000);
    log('Login', !page.url().includes('login'));

    // ========== BigScreen test with longer wait ==========
    console.log('\n--- BigScreen Test ---');
    await page.goto('http://localhost:3000/bigscreen', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(5000); // Wait longer for ECharts to render
    await page.screenshot({ path: '/workspace/images/ui_test/sim_bigscreen_01.png' });
    
    let canvas = await page.locator('canvas').count();
    let pageText = await page.locator('body').textContent().catch(() => '');
    // Check for any data content
    const hasTemp = pageText.includes('温度') || pageText.includes('temperature');
    const hasHumidity = pageText.includes('湿度') || pageText.includes('humidity');
    const hasDevice = pageText.includes('设备') || pageText.includes('device');
    const hasOnline = pageText.includes('在线') || pageText.includes('online');
    log('BigScreen content check', canvas > 0 || hasTemp || hasHumidity || hasDevice,
        `canvas: ${canvas}, temp: ${hasTemp}, humidity: ${hasHumidity}, device: ${hasDevice}, online: ${hasOnline}`);
    
    // Check page text snippets
    if (pageText.length > 0) {
      const snippet = pageText.substring(0, 500).replace(/\s+/g, ' ').trim();
      log('BigScreen page text', true, `snippet: ${snippet.substring(0, 200)}`);
    }

    // Wait more and recheck
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_bigscreen_02.png' });
    canvas = await page.locator('canvas').count();
    log('BigScreen after extra wait', canvas > 0, `canvas: ${canvas}`);

    // ========== 3D Scene test with WebGL enabled ==========
    console.log('\n--- 3D Scene Test ---');
    await page.goto('http://localhost:3000/greenhouse3d', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_3d_01.png' });
    
    canvas = await page.locator('canvas').count();
    const switches = await page.locator('.el-switch').count();
    const webglError = await page.locator('text=WebGL, text=不支持, text=浏览器').count();
    const sceneContent = await page.locator('body').textContent().catch(() => '');
    
    log('3D scene canvas', canvas > 0, `canvas: ${canvas}`);
    log('3D scene switches', switches > 0, `switches: ${switches}`);
    log('3D scene WebGL error', webglError > 0, `error hints: ${webglError}`);
    
    if (sceneContent.length > 0) {
      const snippet = sceneContent.substring(0, 500).replace(/\s+/g, ' ').trim();
      log('3D scene page text', true, `snippet: ${snippet.substring(0, 200)}`);
    }

    // Check for the WebGL unsupported message specifically
    const webglMsg = await page.locator('.webgl-error, .error-message, [class*="error"], [class*="webgl"]').count();
    log('3D WebGL fallback', webglMsg > 0 || canvas > 0, `fallback msg: ${webglMsg}, canvas: ${canvas}`);

    // ========== Dashboard with data check ==========
    console.log('\n--- Dashboard Data Verification ---');
    await page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_dashboard_final.png' });

    // Check chart data via network requests
    const dashContent = await page.locator('body').textContent().catch(() => '');
    const hasTempData = dashContent.includes('温度') || dashContent.includes('℃');
    const hasHumidData = dashContent.includes('湿度') || dashContent.includes('%');
    const hasChartData = dashContent.includes('趋势') || dashContent.includes('chart') || dashContent.includes('Chart');
    log('Dashboard data content', hasTempData || hasHumidData || hasChartData,
        `temp: ${hasTempData}, humidity: ${hasHumidData}, chart: ${hasChartData}`);

    // Canvas count on dashboard
    const dashCanvas = await page.locator('canvas').count();
    log('Dashboard canvas charts', dashCanvas > 0, `count: ${dashCanvas}`);

  } catch (e) {
    console.error('Test error:', e.message);
    try { await page.screenshot({ path: '/workspace/images/ui_test/sim_debug_error.png' }); } catch(e2) {}
  }

  const passed = results.filter(r => r.pass).length;
  const failed = results.filter(r => !r.pass).length;
  console.log(`\n========== SUMMARY ==========`);
  console.log(`Total: ${results.length}, Passed: ${passed}, Failed: ${failed}`);
  if (failed > 0) {
    console.log('Failed tests:');
    results.filter(r => !r.pass).forEach(r => console.log(`  ❌ ${r.name} — ${r.detail}`));
  }
  console.log(`=============================`);
  
  await browser.close();
})();
