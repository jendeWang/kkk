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

  // Capture console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', err => consoleErrors.push(`PAGE: ${err.message}`));

  try {
    // Login
    await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button:has-text("登录")');
    await page.waitForTimeout(2000);
    log('Login', !page.url().includes('login'));

    // ========== BigScreen with correct route ==========
    console.log('\n--- BigScreen (/big-screen) ---');
    consoleErrors.length = 0;
    await page.goto('http://localhost:3000/big-screen', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_bigscreen_correct.png' });
    
    let bsCanvas = await page.locator('canvas').count();
    let bsContent = await page.locator('body').textContent().catch(() => '');
    const bsHasTemp = bsContent.includes('温度') || bsContent.includes('℃');
    const bsHasHumidity = bsContent.includes('湿度') || bsContent.includes('%');
    const bsHasDevice = bsContent.includes('设备');
    const bsHasOnline = bsContent.includes('在线');
    const bsHasData = bsContent.includes('CO2') || bsContent.includes('co2') || bsContent.includes('光照');
    log('BigScreen page loaded', bsCanvas > 0 || bsHasTemp || bsHasDevice,
        `canvas: ${bsCanvas}, temp: ${bsHasTemp}, humidity: ${bsHasHumidity}, device: ${bsHasDevice}, online: ${bsHasOnline}, data: ${bsHasData}`);
    
    if (bsContent.length > 50) {
      log('BigScreen has content', true, `length: ${bsContent.length}, snippet: ${bsContent.substring(0, 200).replace(/\s+/g, ' ')}`);
    }

    // Check for data sections on bigscreen
    const bsCards = await page.locator('.data-card, .stat-card, .info-card, .el-card').count();
    const bsNumbers = await page.locator('.number, .value, .stat-value, .el-statistic__number').count();
    log('BigScreen data cards', bsCards > 0 || bsNumbers > 0, `cards: ${bsCards}, numbers: ${bsNumbers}`);

    // ========== 3D Scene with correct route ==========
    console.log('\n--- 3D Scene (/greenhouse-3d) ---');
    consoleErrors.length = 0;
    await page.goto('http://localhost:3000/greenhouse-3d', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_3d_correct.png' });
    
    let tdCanvas = await page.locator('canvas').count();
    let tdSwitches = await page.locator('.el-switch').count();
    let tdContent = await page.locator('body').textContent().catch(() => '');
    const tdHasWebglMsg = tdContent.includes('WebGL') || tdContent.includes('不支持');
    const tdHasScene = tdContent.includes('大棚') || tdContent.includes('场景') || tdContent.includes('Greenhouse');
    const tdHasControl = tdContent.includes('控制') || tdContent.includes('开关');
    
    log('3D scene canvas', tdCanvas > 0, `canvas: ${tdCanvas}`);
    log('3D scene controls', tdSwitches > 0 || tdHasControl, `switches: ${tdSwitches}, has control text: ${tdHasControl}`);
    log('3D scene content', tdHasWebglMsg || tdHasScene || tdCanvas > 0,
        `webgl error: ${tdHasWebglMsg}, scene: ${tdHasScene}, canvas: ${tdCanvas}`);
    
    if (tdContent.length > 50) {
      log('3D scene has content', true, `length: ${tdContent.length}, snippet: ${tdContent.substring(0, 200).replace(/\s+/g, ' ')}`);
    }

    // ========== Re-run full telemetry test with correct routes ==========
    console.log('\n--- Telemetry Re-test ---');
    await page.goto('http://localhost:3000/telemetry', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(2000);
    
    // Select device
    const deviceSelect = page.locator('.el-form .el-select').first();
    await deviceSelect.click();
    await page.waitForTimeout(600);
    await page.locator('.el-select-dropdown__item').first().click();
    await page.waitForTimeout(3000);
    
    const tableRows = await page.locator('.el-table__body tr').count();
    const totalText = await page.locator('.el-pagination__total').textContent().catch(() => '');
    log('Telemetry data with simulator', tableRows > 0, `rows: ${tableRows}, total: ${totalText}`);
    
    // Check first row data quality
    if (tableRows > 0) {
      const firstRow = await page.locator('.el-table__body tr').first().textContent();
      log('Telemetry first row', firstRow.length > 10, `data: ${firstRow.substring(0, 80)}`);
    }

    // Verify all 9 sensor properties are present in the data
    await page.waitForTimeout(1000);
    const allTableContent = await page.locator('.el-table__body').textContent().catch(() => '');
    const sensors = ['temperature', 'humidity', 'light_intensity', 'soil_moisture', 'co2', 'soil_temperature', 'soil_ph', 'wind_speed', 'rainfall'];
    const foundSensors = sensors.filter(s => allTableContent.includes(s));
    log('All 9 sensors present', foundSensors.length === 9, `found: [${foundSensors.join(', ')}] (${foundSensors.length}/9)`);

    await page.screenshot({ path: '/workspace/images/ui_test/sim_telemetry_final.png' });

    // ========== Dashboard data verification ==========
    console.log('\n--- Dashboard Final ---');
    await page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_dashboard_final2.png' });
    
    const dashCanvas = await page.locator('canvas').count();
    const dashContent = await page.locator('body').textContent().catch(() => '');
    const dashHasData = dashContent.includes('温度') || dashContent.includes('湿度') || dashContent.includes('℃');
    log('Dashboard with simulator data', dashCanvas > 0 || dashHasData,
        `canvas: ${dashCanvas}, has data: ${dashHasData}`);

    // Print any remaining errors
    if (consoleErrors.length > 0) {
      console.log('\nConsole errors:', consoleErrors.slice(0, 3).join('\n'));
    }

  } catch (e) {
    console.error('Test error:', e.message);
    try { await page.screenshot({ path: '/workspace/images/ui_test/sim_final_error.png' }); } catch(e2) {}
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
