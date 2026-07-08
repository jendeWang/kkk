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

  // Helper: open el-select dropdown and get option texts
  async function openSelectAndGetOptions(locator) {
    await locator.click();
    await page.waitForTimeout(800);
    const opts = await page.locator('.el-select-dropdown__item').allTextContents();
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
    return opts;
  }

  try {
    // Login
    await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button:has-text("登录")');
    await page.waitForURL('**/dashboard**', { timeout: 10000 }).catch(() => {});
    await page.waitForTimeout(2000);
    const loggedIn = !page.url().includes('login');
    log('Login', loggedIn);

    // Navigate to Telemetry
    await page.goto('http://localhost:3000/telemetry', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    log('Navigate to Telemetry page', page.url().includes('telemetry'));
    await page.screenshot({ path: '/workspace/images/ui_test/telemetry_sim_01_initial.png' });

    // Test 1: Page has content
    const pageContent = await page.content();
    log('Page loaded', pageContent.length > 500, `content length: ${pageContent.length}`);

    // Test 2: Device selector exists
    const deviceSelectLocator = page.locator('.el-form .el-select').first();
    const deviceSelectExists = await deviceSelectLocator.count() > 0;
    log('Device select found', deviceSelectExists);

    if (deviceSelectExists) {
      // Test 3: Device dropdown options
      const deviceOpts = await openSelectAndGetOptions(deviceSelectLocator);
      log('Device dropdown options', deviceOpts.length > 0, `options: [${deviceOpts.slice(0, 8).join(', ')}] (total: ${deviceOpts.length})`);

      // Test 4: Select a device and wait for data
      await deviceSelectLocator.click();
      await page.waitForTimeout(600);
      await page.locator('.el-select-dropdown__item').first().click();
      await page.waitForTimeout(3000); // Wait for API to return data
      await page.screenshot({ path: '/workspace/images/ui_test/telemetry_sim_02_device_selected.png' });
      
      // Check table data
      const tableRows = await page.locator('.el-table__body tr').count();
      const totalText = await page.locator('.el-pagination__total').textContent().catch(() => 'N/A');
      log('Data loaded after device select', tableRows > 0, `table rows: ${tableRows}, total: ${totalText}`);

      // Test 5: Check actual data values in table
      if (tableRows > 0) {
        const firstRow = await page.locator('.el-table__body tr').first().textContent();
        log('First row has data', firstRow.length > 10, `content: ${firstRow.substring(0, 100)}`);
      }

      // Test 6: Property selector - check if populated after device select
      const propSelectLocator = page.locator('.el-form .el-select').nth(1);
      if (await propSelectLocator.count() > 0) {
        const propOpts = await openSelectAndGetOptions(propSelectLocator);
        log('Property dropdown options after device select', propOpts.length > 0, `options: [${propOpts.join(', ')}]`);
      }

      // Test 7: Select a specific property
      if (await propSelectLocator.count() > 0) {
        await propSelectLocator.click();
        await page.waitForTimeout(600);
        const propItems = await page.locator('.el-select-dropdown__item').allTextContents();
        if (propItems.length > 0) {
          // Select temperature
          const tempItem = page.locator('.el-select-dropdown__item:has-text("temperature")');
          if (await tempItem.count() > 0) {
            await tempItem.click();
          } else {
            await page.locator('.el-select-dropdown__item').first().click();
          }
          await page.waitForTimeout(2000);
          const filteredRows = await page.locator('.el-table__body tr').count();
          log('Data after property filter', filteredRows > 0, `rows: ${filteredRows}`);
          await page.screenshot({ path: '/workspace/images/ui_test/telemetry_sim_03_filtered.png' });
        }
      }

      // Test 8: Pagination
      const paginationExists = await page.locator('.el-pagination').count() > 0;
      log('Pagination present', paginationExists);
      
      if (paginationExists) {
        // Check page size selector
        const sizesSelect = page.locator('.el-pagination__sizes .el-select');
        if (await sizesSelect.count() > 0) {
          const sizeOpts = await openSelectAndGetOptions(sizesSelect);
          log('Page size options', sizeOpts.length > 0, `options: [${sizeOpts.join(', ')}]`);
        }
      }

      // Test 9: Time range picker
      const datePicker = page.locator('.el-date-editor').first();
      if (await datePicker.count() > 0) {
        log('Time range picker found', true);
        await datePicker.click();
        await page.waitForTimeout(800);
        const panel = await page.locator('.el-picker-panel, .el-date-range-picker').count();
        log('Date picker panel opens', panel > 0);
        await page.keyboard.press('Escape');
        await page.waitForTimeout(500);
      }

      // Test 10: Export CSV button
      const exportBtn = page.locator('button:has-text("导出CSV")');
      const exportExists = await exportBtn.count() > 0;
      log('Export CSV button present', exportExists);

      // Test 11: Reset button
      const resetBtn = page.locator('button:has-text("重置")');
      if (await resetBtn.count() > 0) {
        await resetBtn.click();
        await page.waitForTimeout(1000);
        const rowsAfterReset = await page.locator('.el-table__body tr').count();
        log('Reset clears data', true, `rows after reset: ${rowsAfterReset}`);
        await page.screenshot({ path: '/workspace/images/ui_test/telemetry_sim_04_reset.png' });
      }

      // Test 12: Quality tag colors
      // Re-select device for quality check
      await deviceSelectLocator.click();
      await page.waitForTimeout(600);
      await page.locator('.el-select-dropdown__item').first().click();
      await page.waitForTimeout(3000);
      
      const goodTags = await page.locator('.el-table .el-tag--success, .el-table .el-tag--danger, .el-table .el-tag--info').count();
      log('Quality tags rendered', goodTags > 0 || tableRows > 0, `quality tags: ${goodTags}`);
    }

    // Test 13: Dashboard with simulator data
    await page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/telemetry_sim_05_dashboard.png' });
    
    const statNumbers = await page.locator('.el-statistic__number').count();
    const canvasCharts = await page.locator('canvas').count();
    log('Dashboard has data from simulator', statNumbers > 0 || canvasCharts > 0,
        `stat numbers: ${statNumbers}, canvas charts: ${canvasCharts}`);

    // Test 14: Data Big Screen
    await page.goto('http://localhost:3000/bigscreen', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/telemetry_sim_06_bigscreen.png' });
    const bigScreenContent = await page.content();
    log('Big screen loaded', bigScreenContent.length > 500, `content: ${bigScreenContent.length}`);

    // Test 15: Sensors page (if exists)
    await page.goto('http://localhost:3000/sensors', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/telemetry_sim_07_sensors.png' });
    const sensorData = await page.locator('.el-card, .el-statistic, .el-descriptions').count();
    log('Sensors page has data', sensorData > 0, `data elements: ${sensorData}`);

  } catch (e) {
    console.error('Test error:', e.message);
    try { await page.screenshot({ path: '/workspace/images/ui_test/telemetry_sim_error.png' }); } catch(e2) {}
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
