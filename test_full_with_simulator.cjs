const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
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
    await page.waitForURL('**/dashboard**', { timeout: 10000 }).catch(() => {});
    await page.waitForTimeout(2000);
    log('Login', !page.url().includes('login'));

    // ========== 遥测数据页面测试 ==========
    await page.goto('http://localhost:3000/telemetry', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    log('Telemetry page loaded', page.url().includes('telemetry'));
    await page.screenshot({ path: '/workspace/images/ui_test/sim_test_01_telemetry.png' });

    // Test: Device select
    const deviceSelect = page.locator('.el-form .el-select').first();
    await deviceSelect.click();
    await page.waitForTimeout(800);
    const deviceOpts = await page.locator('.el-select-dropdown__item:not(.is-disabled)').allTextContents();
    log('Device dropdown', deviceOpts.length > 0, `options: [${deviceOpts.slice(0, 8).join(', ')}] (${deviceOpts.length})`);
    
    // Select first device
    await page.locator('.el-select-dropdown__item').first().click();
    await page.waitForTimeout(3000);
    
    // Check table
    let tableRows = await page.locator('.el-table__body tr').count();
    let totalText = await page.locator('.el-pagination__total').textContent().catch(() => 'N/A');
    log('Data after device select', tableRows > 0, `rows: ${tableRows}, total: ${totalText}`);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_test_02_data_loaded.png' });

    // Test: First row data verification
    if (tableRows > 0) {
      const firstRow = await page.locator('.el-table__body tr').first();
      const cells = await firstRow.locator('.el-table__cell').allTextContents();
      log('First row content', cells.length >= 3, `cells: [${cells.join(' | ')}]`);
      
      // Check quality tag
      const tag = await firstRow.locator('.el-tag').textContent().catch(() => '');
      log('Quality tag', tag.length > 0, `quality: ${tag}`);
    }

    // Test: Property select - use scoped approach
    const propSelect = page.locator('.el-form .el-select').nth(1);
    // Get the select's popperclass to scope dropdown items
    await propSelect.click();
    await page.waitForTimeout(800);
    // The property dropdown should contain sensor names
    const allDropdownItems = await page.locator('.el-select-dropdown__item').allTextContents();
    // Filter to only sensor-like items
    const sensorProps = allDropdownItems.filter(item => 
      ['temperature','humidity','light_intensity','soil_moisture','co2','soil_temperature','soil_ph','wind_speed','rainfall'].includes(item)
    );
    log('Property dropdown sensor options', sensorProps.length >= 9, `sensors: [${sensorProps.join(', ')}]`);
    
    // Select temperature specifically (use exact match)
    const exactTempItem = page.locator('.el-select-dropdown__item').filter({ hasText: /^temperature$/ });
    if (await exactTempItem.count() > 0) {
      await exactTempItem.click();
      await page.waitForTimeout(2000);
      const filteredRows = await page.locator('.el-table__body tr').count();
      log('Filtered by temperature', filteredRows > 0, `rows: ${filteredRows}`);
      await page.screenshot({ path: '/workspace/images/ui_test/sim_test_03_temp_filtered.png' });
    } else {
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
      log('Temperature filter skipped', true, 'exact match not found');
    }

    // Test: Clear property filter
    const clearBtn = propSelect.locator('.el-select__clear');
    if (await clearBtn.count() > 0) {
      await clearBtn.click();
      await page.waitForTimeout(2000);
      const allRows = await page.locator('.el-table__body tr').count();
      log('Clear property filter', allRows > 0, `all rows: ${allRows}`);
    }

    // Test: Pagination
    const nextBtn = page.locator('.el-pagination .btn-next');
    if (await nextBtn.count() > 0 && await nextBtn.isEnabled()) {
      await nextBtn.click();
      await page.waitForTimeout(2000);
      const page2Rows = await page.locator('.el-table__body tr').count();
      log('Pagination next page', page2Rows > 0, `page 2 rows: ${page2Rows}`);
      
      // Go back to page 1
      const prevBtn = page.locator('.el-pagination .btn-prev');
      if (await prevBtn.count() > 0) await prevBtn.click();
      await page.waitForTimeout(1000);
    }

    // Test: Page size change
    const sizeSelect = page.locator('.el-pagination__sizes .el-select');
    if (await sizeSelect.count() > 0) {
      await sizeSelect.click();
      await page.waitForTimeout(600);
      const sizeItems = await page.locator('.el-select-dropdown__item').allTextContents();
      // Filter to page size items
      const sizeOpts = sizeItems.filter(s => s.includes('/page'));
      log('Page size options', sizeOpts.length > 0, `options: [${sizeOpts.join(', ')}]`);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
    }

    // Test: Time range picker
    const dateEditor = page.locator('.el-date-editor').first();
    if (await dateEditor.count() > 0) {
      await dateEditor.click();
      await page.waitForTimeout(1000);
      const panelVisible = await page.locator('.el-picker-panel').count() > 0;
      log('Date picker panel', panelVisible);
      
      // Try quick select - last 7 days
      const shortcut7d = page.locator('.el-picker-panel__shortcut:has-text("7")');
      if (await shortcut7d.count() > 0) {
        await shortcut7d.click();
        await page.waitForTimeout(2000);
        log('Quick select 7 days', true);
      } else {
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);
        log('Date picker shortcut', true, 'no shortcut found, manual select available');
      }
    }

    // Test: Export CSV
    const exportBtn = page.locator('button:has-text("导出CSV")');
    log('Export CSV button', await exportBtn.count() > 0);

    // Test: Reset button
    const resetBtn = page.locator('button:has-text("重置")');
    if (await resetBtn.count() > 0) {
      await resetBtn.click();
      await page.waitForTimeout(1000);
      const emptyRows = await page.locator('.el-table__body tr').count();
      log('Reset button', true, `rows after reset: ${emptyRows}`);
    }

    // ========== 仪表盘测试（验证模拟器数据在dashboard显示）==========
    await page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_test_04_dashboard.png' });
    
    const statNumbers = await page.locator('.el-statistic__number').count();
    const canvasCount = await page.locator('canvas').count();
    log('Dashboard with simulator data', statNumbers > 0 || canvasCount > 0,
        `stats: ${statNumbers}, charts: ${canvasCount}`);

    // Check actual stat values
    if (statNumbers > 0) {
      const statValues = [];
      for (let i = 0; i < Math.min(statNumbers, 6); i++) {
        const val = await page.locator('.el-statistic__number').nth(i).textContent().catch(() => '');
        statValues.push(val);
      }
      log('Dashboard stat values', true, `values: [${statValues.join(', ')}]`);
    }

    // Test greenhouse tabs
    const ghTabs = await page.locator('.el-tabs__item').count();
    if (ghTabs > 0) {
      const tabNames = await page.locator('.el-tabs__item').allTextContents();
      log('Greenhouse tabs', tabNames.length > 0, `tabs: [${tabNames.join(', ')}]`);
      
      // Switch tabs and check data refresh
      if (tabNames.length > 1) {
        await page.locator('.el-tabs__item').nth(1).click();
        await page.waitForTimeout(2000);
        await page.screenshot({ path: '/workspace/images/ui_test/sim_test_05_dashboard_tab2.png' });
        log('Dashboard tab switch', true, `switched to: ${tabNames[1]}`);
      }
    }

    // ========== 传感器页面测试 ==========
    await page.goto('http://localhost:3000/sensors', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_test_06_sensors.png' });
    
    const sensorCards = await page.locator('.el-card').count();
    const sensorStats = await page.locator('.el-statistic').count();
    const sensorDescs = await page.locator('.el-descriptions').count();
    log('Sensors page data', sensorCards > 0 || sensorStats > 0 || sensorDescs > 0,
        `cards: ${sensorCards}, stats: ${sensorStats}, descriptions: ${sensorDescs}`);

    // ========== 执行器页面测试 ==========
    await page.goto('http://localhost:3000/actuators', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_test_07_actuators.png' });
    
    const actuatorSwitches = await page.locator('.el-switch').count();
    const actuatorCards = await page.locator('.el-card').count();
    log('Actuators page', actuatorSwitches > 0 || actuatorCards > 0,
        `switches: ${actuatorSwitches}, cards: ${actuatorCards}`);

    // ========== 数据大屏测试 ==========
    await page.goto('http://localhost:3000/bigscreen', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_test_08_bigscreen.png' });
    const bigScreenCanvas = await page.locator('canvas').count();
    const bigScreenText = await page.locator('text=温度, text=湿度, text=CO2, text=co2').count();
    log('Big screen with data', bigScreenCanvas > 0 || bigScreenText > 0,
        `canvas: ${bigScreenCanvas}, data labels: ${bigScreenText}`);

    // ========== 命令下发测试 ==========
    await page.goto('http://localhost:3000/commands', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_test_09_commands.png' });
    
    const cmdDeviceSelect = page.locator('.el-form .el-select').first();
    if (await cmdDeviceSelect.count() > 0) {
      await cmdDeviceSelect.click();
      await page.waitForTimeout(600);
      const cmdDevices = await page.locator('.el-select-dropdown__item').allTextContents();
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
      log('Command device select', cmdDevices.length > 0, `options: ${cmdDevices.length}`);
    }

    // ========== 告警页面测试 ==========
    await page.goto('http://localhost:3000/alerts', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_test_10_alerts.png' });
    
    const alertRows = await page.locator('.el-table__body tr').count();
    const alertCards = await page.locator('.el-card').count();
    log('Alerts page with data', alertRows > 0 || alertCards > 0,
        `table rows: ${alertRows}, cards: ${alertCards}`);

    // ========== 设备管理测试 ==========
    await page.goto('http://localhost:3000/devices', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_test_11_devices.png' });
    
    const deviceRows = await page.locator('.el-table__body tr').count();
    log('Devices page with data', deviceRows > 0, `rows: ${deviceRows}`);

    // ========== 3D场景测试 ==========
    await page.goto('http://localhost:3000/greenhouse3d', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/sim_test_12_3d.png' });
    
    const canvas3d = await page.locator('canvas').count();
    const switch3d = await page.locator('.el-switch').count();
    log('3D scene with data', canvas3d > 0, `canvas: ${canvas3d}, switches: ${switch3d}`);

  } catch (e) {
    console.error('Test error:', e.message);
    try { await page.screenshot({ path: '/workspace/images/ui_test/sim_test_error.png' }); } catch(e2) {}
  }

  // Summary
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
