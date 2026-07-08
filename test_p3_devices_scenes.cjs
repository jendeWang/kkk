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

  async function loginUser(username, password) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(800);
    const inputs = await page.locator('input[type="text"]').all();
    for (const inp of inputs) {
      const ph = await inp.getAttribute('placeholder');
      if (ph && ph.includes('用户')) { await inp.fill(username); break; }
    }
    await page.locator('input[type="password"]').first().fill(password);
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(2500);
    return { page, context, loggedIn: !page.url().includes('login') };
  }

  let page = null;
  let ctx = null;

  try {
    // Login
    const admin = await loginUser('admin', 'admin123');
    log('1. Admin login', admin.loggedIn);
    if (!admin.loggedIn) { await browser.close(); return; }
    page = admin.page;
    ctx = admin.context;

    // ===== 设备管理深度测试 =====
    console.log('\n🔌 设备管理深度测试');
    await page.goto('http://localhost:3000/devices', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/workspace/images/ui_test/p3_devices_01.png' });

    const devRows = await page.locator('.el-table__body tr').count();
    log('2. Device list loaded', devRows > 0, `${devRows} devices`);

    // Add device dialog
    await page.locator('button').filter({ hasText: /新增设备|Add/ }).first().click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: '/workspace/images/ui_test/p3_devices_02_add.png' });
    const addDialog = await page.locator('.el-dialog').count() > 0;
    log('3. Add device dialog', addDialog);

    if (addDialog) {
      // Check form fields
      const formInputs = await page.locator('.el-dialog input').count();
      const formSelects = await page.locator('.el-dialog .el-select').count();
      log('4. Add form fields', formInputs > 0 && formSelects > 0, `inputs: ${formInputs}, selects: ${formSelects}`);

      // Product dropdown
      const prodSelect = page.locator('.el-dialog .el-select').first();
      await prodSelect.click();
      await page.waitForTimeout(600);
      const prodOptions = await page.locator('.el-select-dropdown__item').allTextContents();
      log('5. Product dropdown', prodOptions.length > 0, `options: ${prodOptions.length}`);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);

      // Close dialog
      await page.locator('.el-dialog__headerbtn').click();
      await page.waitForTimeout(500);
    }

    // Edit first device
    if (devRows > 0) {
      const editBtn = page.locator('.el-table__body tr').first().locator('button:has-text("编辑")');
      if (await editBtn.count() > 0) {
        await editBtn.click();
        await page.waitForTimeout(1000);
        const editDialog = await page.locator('.el-dialog').count() > 0;
        log('6. Edit dialog opens', editDialog);
        if (editDialog) {
          await page.screenshot({ path: '/workspace/images/ui_test/p3_devices_03_edit.png' });
          await page.locator('.el-dialog__headerbtn').click();
          await page.waitForTimeout(500);
        }
      }

      // Delete confirm
      const delBtn = page.locator('.el-table__body tr').first().locator('button:has-text("删除")');
      if (await delBtn.count() > 0) {
        await delBtn.click();
        await page.waitForTimeout(800);
        const confirm = await page.locator('.el-message-box').count() > 0;
        log('7. Delete confirm dialog', confirm);
        if (confirm) {
          await page.locator('.el-message-box__btns button').first().click();
          await page.waitForTimeout(500);
        }
      }

      // Device status tag
      const statusTag = await page.locator('.el-table__body tr').first().locator('.el-tag').textContent().catch(() => '');
      log('8. Device status visible', statusTag.length > 0, `status: ${statusTag}`);
    }

    // ===== 场景联动深度测试 =====
    console.log('\n🔄 场景联动深度测试');
    await page.goto('http://localhost:3000/scenes', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/workspace/images/ui_test/p3_scenes_01.png' });

    const sceneCards = await page.locator('.el-card').count();
    const sceneRows = await page.locator('.el-table__body tr').count();
    log('9. Scene list loaded', sceneCards > 0 || sceneRows > 0, `cards: ${sceneCards}, rows: ${sceneRows}`);

    // Add scene dialog
    await page.locator('button').filter({ hasText: /新建场景|使用模板/ }).first().click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: '/workspace/images/ui_test/p3_scenes_02_add.png' });
    const sceneDialog = await page.locator('.el-dialog').count() > 0;
    log('10. Add scene dialog', sceneDialog);

    if (sceneDialog) {
      // Check trigger condition section (el-divider with content)
      const hasTrigger = await page.locator('.el-dialog .el-divider__text').filter({ hasText: /触发/ }).count() > 0;
      const hasAction = await page.locator('.el-dialog .el-divider__text').filter({ hasText: /执行/ }).count() > 0;
      log('11. Trigger condition section', hasTrigger);
      log('12. Execute action section', hasAction);

      // Trigger type radio options
      const triggerRadios = await page.locator('.el-dialog .el-radio').count();
      log('13. Trigger type radio options', triggerRadios >= 3, `count: ${triggerRadios}`);

      // Select threshold trigger to see sensor options
      await page.locator('.el-dialog .el-radio__input').first().click();
      await page.waitForTimeout(500);

      // Check sensor property options
      const propSelect = page.locator('.el-dialog .el-select').first();
      await propSelect.click();
      await page.waitForTimeout(600);
      const triggerOptions = await page.locator('.el-select-dropdown__item').allTextContents();
      const sensorLabels = ['空气温度', '空气湿度', '土壤湿度', '光照强度', 'CO₂浓度', '土壤温度', '土壤pH值', '风速', '雨量'];
      const foundSensors = sensorLabels.filter(s => triggerOptions.some(o => o.includes(s)));
      log('14. Trigger has sensor options', foundSensors.length >= 7, `found: [${foundSensors.join(', ')}] (${foundSensors.length}/9)`);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);

      // Action type radio
      const actionRadios = await page.locator('.el-dialog .el-radio-group').nth(1).locator('.el-radio').count();
      log('15. Action type options', actionRadios >= 2, `count: ${actionRadios}`);

      await page.locator('.el-dialog__headerbtn').click();
      await page.waitForTimeout(500);
    }

    // Toggle enable/disable on first scene
    if (sceneCards > 0 || sceneRows > 0) {
      const switches = await page.locator('.el-switch').count();
      if (switches > 0) {
        const firstSw = page.locator('.el-switch').first();
        const before = await firstSw.isChecked();
        await firstSw.click();
        await page.waitForTimeout(1000);
        const after = await firstSw.isChecked();
        log('16. Scene enable toggle', before !== after, `${before} -> ${after}`);
      }
    }

    // ===== 跨页面联动测试 =====
    console.log('\n🔗 跨页面联动测试');
    // Dashboard -> Device detail
    await page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);

    // Check if dashboard has device links
    const deviceLinks = await page.locator('a[href*="/devices"], .device-link, [class*="device"]').count();
    log('17. Dashboard has device links', deviceLinks > 0, `count: ${deviceLinks}`);

    // Alerts -> Device
    await page.goto('http://localhost:3000/alerts', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    const alertDevLinks = await page.locator('.el-table__body tr').first().locator('a, .link').count();
    log('18. Alerts have device links', alertDevLinks > 0, `count: ${alertDevLinks}`);

  } catch (e) {
    console.error('Test error:', e.message);
    if (page) await page.screenshot({ path: '/workspace/images/ui_test/p3_devices_scenes_error.png' });
  }

  if (ctx) await ctx.close();

  const passed = results.filter(r => r.pass).length;
  const failed = results.filter(r => !r.pass).length;
  console.log(`\n${'='.repeat(50)}`);
  console.log(`  P3 DEVICES & SCENES TEST SUMMARY`);
  console.log(`  Total: ${results.length} | Passed: ${passed} | Failed: ${failed}`);
  console.log(`${'='.repeat(50)}`);
  if (failed > 0) {
    results.filter(r => !r.pass).forEach(r => console.log(`  ❌ ${r.name} — ${r.detail}`));
  }

  await browser.close();
})();
