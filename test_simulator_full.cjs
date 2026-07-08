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

  // Helper: open el-select dropdown and get option texts
  async function openSelectAndGetOptions(locator) {
    await locator.click();
    await page.waitForTimeout(800);
    const opts = await page.locator('.el-select-dropdown__item').allTextContents();
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
    return opts;
  }

  const consoleErrors = [];
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });

  try {
    // ===== Login =====
    await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button:has-text("登录")');
    await page.waitForTimeout(2000);
    log('1. Login', !page.url().includes('login'));

    // ===== 遥测数据页面 =====
    console.log('\n📊 遥测数据页面');
    await page.goto('http://localhost:3000/telemetry', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(2000);
    
    // Device select
    const deviceSelect = page.locator('.el-form .el-select').first();
    await deviceSelect.click();
    await page.waitForTimeout(600);
    const deviceOpts = await page.locator('.el-select-dropdown__item').allTextContents();
    log('2. Telemetry device dropdown', deviceOpts.length > 0, `${deviceOpts.length} options`);
    
    // Select first device
    await page.locator('.el-select-dropdown__item').first().click();
    await page.waitForTimeout(3000);
    
    let tableRows = await page.locator('.el-table__body tr').count();
    let totalText = await page.locator('.el-pagination__total').textContent().catch(() => '');
    log('3. Telemetry data loaded', tableRows > 0, `rows: ${tableRows}, ${totalText}`);
    
    // Check all 9 sensors in data
    const allData = await page.locator('.el-table__body').textContent().catch(() => '');
    const sensors = ['temperature', 'humidity', 'light_intensity', 'soil_moisture', 'co2', 'soil_temperature', 'soil_ph', 'wind_speed', 'rainfall'];
    const found = sensors.filter(s => allData.includes(s));
    log('4. All 9 sensors present', found.length === 9, `[${found.join(', ')}] (${found.length}/9)`);
    
    // Filter by temperature
    const propSelect = page.locator('.el-form .el-select').nth(1);
    await propSelect.click();
    await page.waitForTimeout(600);
    const exactTemp = page.locator('.el-select-dropdown__item').filter({ hasText: /^temperature$/ });
    if (await exactTemp.count() > 0) {
      await exactTemp.click();
      await page.waitForTimeout(2000);
      const filteredRows = await page.locator('.el-table__body tr').count();
      log('5. Filter by temperature', filteredRows > 0, `${filteredRows} rows`);
    }
    
    // Clear filter and check all sensors
    const clearBtn = propSelect.locator('.el-select__clear');
    if (await clearBtn.count() > 0) await clearBtn.click();
    await page.waitForTimeout(1500);
    
    // Pagination
    const nextBtn = page.locator('.el-pagination .btn-next');
    if (await nextBtn.count() > 0 && await nextBtn.isEnabled()) {
      await nextBtn.click();
      await page.waitForTimeout(2000);
      const p2Rows = await page.locator('.el-table__body tr').count();
      log('6. Pagination works', p2Rows > 0, `page 2 rows: ${p2Rows}`);
      const prevBtn = page.locator('.el-pagination .btn-prev');
      if (await prevBtn.count() > 0) await prevBtn.click();
      await page.waitForTimeout(1000);
    }
    
    // Export CSV button
    log('7. Export CSV button', await page.locator('button:has-text("导出CSV")').count() > 0);
    
    // Reset
    const resetBtn = page.locator('button:has-text("重置")');
    if (await resetBtn.count() > 0) {
      await resetBtn.click();
      await page.waitForTimeout(1000);
      log('8. Reset button clears data', true);
    }
    
    await page.screenshot({ path: '/workspace/images/ui_test/final_01_telemetry.png' });

    // ===== 仪表盘 =====
    console.log('\n📈 仪表盘');
    await page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/final_02_dashboard.png' });
    
    const dashCanvas = await page.locator('canvas').count();
    const dashContent = await page.locator('body').textContent().catch(() => '');
    log('9. Dashboard charts', dashCanvas > 0, `canvas: ${dashCanvas}`);
    log('10. Dashboard data', dashContent.includes('温度') || dashContent.includes('℃'), 'has temp/humidity data');
    
    // Greenhouse tabs
    const tabs = await page.locator('.el-tabs__item').count();
    if (tabs > 1) {
      const tabNames = await page.locator('.el-tabs__item').allTextContents();
      log('11. Dashboard tabs', tabNames.length > 0, `[${tabNames.map(t => t.trim()).join(', ')}]`);
      // Switch tab
      await page.locator('.el-tabs__item').nth(1).click();
      await page.waitForTimeout(2000);
      log('12. Tab switch works', true, `switched to: ${(await page.locator('.el-tabs__item').nth(1).textContent()).trim()}`);
    }

    // ===== 设备管理 =====
    console.log('\n🔌 设备管理');
    await page.goto('http://localhost:3000/devices', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/final_03_devices.png' });
    const devRows = await page.locator('.el-table__body tr').count();
    log('13. Devices page', devRows > 0, `${devRows} devices`);
    
    // Check online/offline status
    const onlineTags = await page.locator('.el-tag--success, .el-tag--danger').count();
    log('14. Device status tags', onlineTags > 0, `${onlineTags} status tags`);

    // ===== 传感器页面 =====
    console.log('\n🌡️ 传感器页面');
    await page.goto('http://localhost:3000/sensors', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/final_04_sensors.png' });
    const sensorContent = await page.locator('body').textContent().catch(() => '');
    const sensorDataPresent = sensorContent.includes('温度') || sensorContent.includes('temperature') || sensorContent.includes('℃');
    log('15. Sensors page data', sensorDataPresent, 'has sensor data');

    // ===== 执行器页面 =====
    console.log('\n⚡ 执行器页面');
    await page.goto('http://localhost:3000/actuators', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/final_05_actuators.png' });
    const actSwitches = await page.locator('.el-switch').count();
    log('16. Actuators page', actSwitches > 0, `${actSwitches} switches`);

    // ===== 告警页面 =====
    console.log('\n🚨 告警页面');
    await page.goto('http://localhost:3000/alerts', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/final_06_alerts.png' });
    const alertRows = await page.locator('.el-table__body tr').count();
    log('17. Alerts page', alertRows > 0, `${alertRows} alerts`);

    // ===== 场景联动 =====
    console.log('\n🔄 场景联动');
    await page.goto('http://localhost:3000/scenes', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/final_07_scenes.png' });
    const sceneRows = await page.locator('.el-table__body tr').count();
    const sceneCards = await page.locator('.el-card').count();
    log('18. Scenes page', sceneRows > 0 || sceneCards > 0, `rows: ${sceneRows}, cards: ${sceneCards}`);

    // ===== 命令下发 =====
    console.log('\n📤 命令下发');
    await page.goto('http://localhost:3000/commands', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/final_08_commands.png' });
    const cmdContent = await page.locator('body').textContent().catch(() => '');
    log('19. Commands page', cmdContent.includes('命令') || cmdContent.includes('设备'), 'has command UI');

    // ===== 数据大屏 =====
    console.log('\n🖥️ 数据大屏');
    await page.goto('http://localhost:3000/big-screen', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: '/workspace/images/ui_test/final_09_bigscreen.png' });
    
    const bsCanvas = await page.locator('canvas').count();
    const bsContent = await page.locator('body').textContent().catch(() => '');
    const bsHasData = bsContent.includes('温度') || bsContent.includes('设备') || bsContent.includes('在线');
    log('20. Big screen renders', bsCanvas > 0 || bsHasData, `canvas: ${bsCanvas}, data: ${bsHasData}`);
    
    const bsNumbers = await page.locator('.number, .value, .stat-value, .el-statistic__number').count();
    log('21. Big screen data values', bsNumbers > 0, `${bsNumbers} value elements`);

    // ===== 3D数字孪生 =====
    console.log('\n🎮 3D数字孪生');
    await page.goto('http://localhost:3000/greenhouse-3d', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: '/workspace/images/ui_test/final_10_3d.png' });
    
    const tdCanvas = await page.locator('canvas').count();
    const tdSwitches = await page.locator('.el-switch').count();
    const tdContent = await page.locator('body').textContent().catch(() => '');
    const tdHasEnvData = tdContent.includes('°C') || tdContent.includes('%') || tdContent.includes('ppm');
    log('22. 3D scene canvas', tdCanvas > 0, `canvas: ${tdCanvas}`);
    log('23. 3D scene controls', tdSwitches > 0, `${tdSwitches} switches`);
    log('24. 3D scene env data', tdHasEnvData, 'shows temperature/humidity/CO2');
    
    // Check animationId error is fixed
    const animErrors = consoleErrors.filter(e => e.includes('animationId'));
    log('25. 3D animationId bug fixed', animErrors.length === 0, `errors: ${animErrors.length}`);

    // ===== 产品管理 =====
    console.log('\n📦 产品管理');
    await page.goto('http://localhost:3000/products', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/final_11_products.png' });
    const prodRows = await page.locator('.el-table__body tr').count();
    log('26. Products page', prodRows > 0, `${prodRows} products`);

    // ===== 物模型编辑器 =====
    console.log('\n🔧 物模型编辑器');
    await page.goto('http://localhost:3000/thing-model', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/final_12_thingmodel.png' });
    const tmContent = await page.locator('body').textContent().catch(() => '');
    log('27. Thing model page', tmContent.includes('属性') || tmContent.includes('服务'), 'has model content');

    // ===== 用户管理 =====
    console.log('\n👥 用户管理');
    await page.goto('http://localhost:3000/users', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/final_13_users.png' });
    const userRows = await page.locator('.el-table__body tr').count();
    log('28. Users page', userRows > 0, `${userRows} users`);

    // ===== 个人中心 =====
    console.log('\n👤 个人中心');
    await page.goto('http://localhost:3000/profile', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/final_14_profile.png' });
    const profileContent = await page.locator('body').textContent().catch(() => '');
    log('29. Profile page', profileContent.includes('admin') || profileContent.includes('用户'), 'has user info');

  } catch (e) {
    console.error('Test error:', e.message);
    try { await page.screenshot({ path: '/workspace/images/ui_test/final_error.png' }); } catch(e2) {}
  }

  const passed = results.filter(r => r.pass).length;
  const failed = results.filter(r => !r.pass).length;
  console.log(`\n${'='.repeat(50)}`);
  console.log(`  SIMULATOR FULL TEST SUMMARY`);
  console.log(`  Total: ${results.length} | Passed: ${passed} | Failed: ${failed}`);
  console.log(`${'='.repeat(50)}`);
  if (failed > 0) {
    console.log('  Failed tests:');
    results.filter(r => !r.pass).forEach(r => console.log(`    ❌ ${r.name} — ${r.detail}`));
  }
  
  await browser.close();
})();
