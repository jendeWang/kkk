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
      if (ph && (ph.includes('用户') || ph.includes('User'))) { await inp.fill(username); break; }
    }
    await page.locator('input[type="password"]').first().fill(password);
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(2500);
    return { page, context, loggedIn: !page.url().includes('login') };
  }

  let adminPage = null;
  let adminCtx = null;

  try {
    // Login as admin
    const admin = await loginUser('admin', 'admin123');
    log('1. Admin login', admin.loggedIn);
    if (!admin.loggedIn) { await browser.close(); return; }
    adminPage = admin.page;
    adminCtx = admin.context;

    // Navigate to alert rules
    await adminPage.goto('http://localhost:3000/alert-rules', { waitUntil: 'domcontentloaded' });
    await adminPage.waitForTimeout(2000);
    await adminPage.screenshot({ path: '/workspace/images/ui_test/p3_alertrules_01_page.png' });

    // Check page content
    const pageTitle = await adminPage.locator('h1, .page-title, .card-header span').first().textContent().catch(() => '');
    const hasAddBtn = await adminPage.locator('button:has-text("新增"), button:has-text("Add")').count() > 0;
    log('2. Alert rules page loaded', pageTitle.includes('告警') || hasAddBtn, `title: ${pageTitle}`);

    // Check existing rules
    const tableRows = await adminPage.locator('.el-table__body tr').count();
    log('3. Alert rules table', tableRows > 0, `${tableRows} rules`);

    // Check columns
    const headers = await adminPage.locator('.el-table__header th').allTextContents();
    log('4. Table headers', headers.length >= 5, `headers: [${headers.join(', ')}]`);

    // ===== Test: Add new rule dialog =====
    console.log('\n📋 新增告警规则测试');
    await adminPage.locator('button').filter({ hasText: /添加规则|Add/ }).first().click();
    await adminPage.waitForTimeout(1000);
    await adminPage.screenshot({ path: '/workspace/images/ui_test/p3_alertrules_02_add_dialog.png' });

    const dialogVisible = await adminPage.locator('.el-dialog').count() > 0;
    log('5. Add dialog opens', dialogVisible);

    if (dialogVisible) {
      // Test alert type dropdown
      await adminPage.locator('.el-dialog .el-select').first().click();
      await adminPage.waitForTimeout(600);
      const alertTypes = await adminPage.locator('.el-select-dropdown__item').allTextContents();
      log('6. Alert type options', alertTypes.length >= 3, `options: [${alertTypes.join(', ')}]`);
      await adminPage.keyboard.press('Escape');
      await adminPage.waitForTimeout(300);

      // Test property dropdown (for threshold type)
      const propSelect = adminPage.locator('.el-dialog .el-select').nth(1);
      await propSelect.click();
      await adminPage.waitForTimeout(600);
      const properties = await adminPage.locator('.el-select-dropdown__item').allTextContents();
      // Sensor labels in Chinese
      const sensorLabels = ['空气温度', '空气湿度', '土壤湿度', '光照强度', 'CO₂浓度', '土壤温度', '土壤pH值', '风速', '雨量', '氨气浓度'];
      const foundSensors = sensorLabels.filter(s => properties.some(p => p.includes(s)));
      log('7. Property sensor options', foundSensors.length >= 9, `found: [${foundSensors.join(', ')}] (${foundSensors.length}/10)`);
      await adminPage.keyboard.press('Escape');
      await adminPage.waitForTimeout(300);

      // Test operator dropdown
      const opSelect = adminPage.locator('.el-dialog .el-select').nth(2);
      await opSelect.click();
      await adminPage.waitForTimeout(600);
      const operators = await adminPage.locator('.el-select-dropdown__item').allTextContents();
      log('8. Operator options', operators.length >= 4, `options: [${operators.slice(0, 6).join(', ')}]`);
      await adminPage.keyboard.press('Escape');
      await adminPage.waitForTimeout(300);

      // Test severity radio group
      const severityRadios = await adminPage.locator('.el-dialog .el-radio').count();
      log('9. Severity radio options', severityRadios >= 4, `count: ${severityRadios}`);

      // Fill and save a rule
      await adminPage.locator('.el-dialog input[placeholder*="如"]').fill('高温测试告警');
      // Select temperature property (空气温度)
      await propSelect.click();
      await adminPage.waitForTimeout(600);
      const tempOption = adminPage.locator('.el-select-dropdown__item').filter({ hasText: /^空气温度$/ });
      if (await tempOption.count() > 0) await tempOption.click();
      else await adminPage.locator('.el-select-dropdown__item').first().click();
      await adminPage.waitForTimeout(500);

      // Select operator
      await opSelect.click();
      await adminPage.waitForTimeout(600);
      await adminPage.locator('.el-select-dropdown__item').first().click();
      await adminPage.waitForTimeout(500);

      // Set threshold
      const numInput = adminPage.locator('.el-dialog .el-input-number input');
      if (await numInput.count() > 0) {
        await numInput.fill('35');
      }

      // Select severity
      await adminPage.locator('.el-dialog .el-radio').nth(1).click();
      await adminPage.waitForTimeout(300);

      await adminPage.screenshot({ path: '/workspace/images/ui_test/p3_alertrules_03_filled.png' });

      // Save
      const saveBtn = adminPage.locator('.el-dialog__footer button:has-text("保存"), .el-dialog__footer button:has-text("Save")');
      if (await saveBtn.count() > 0) {
        await saveBtn.click();
        await adminPage.waitForTimeout(2000);
        log('10. Save rule button clicked', true);
      }

      await adminPage.screenshot({ path: '/workspace/images/ui_test/p3_alertrules_04_after_save.png' });
    }

    // ===== Test: Existing rules interaction =====
    console.log('\n⚙️ 规则操作测试');
    await adminPage.goto('http://localhost:3000/alert-rules', { waitUntil: 'domcontentloaded' });
    await adminPage.waitForTimeout(2000);

    const rowsAfterSave = await adminPage.locator('.el-table__body tr').count();
    log('11. Rules after save', rowsAfterSave > 0, `${rowsAfterSave} rules`);

    if (rowsAfterSave > 0) {
      // Test toggle switch
      const firstSwitch = adminPage.locator('.el-table__body tr').first().locator('.el-switch');
      if (await firstSwitch.count() > 0) {
        const beforeVal = await firstSwitch.isChecked();
        await firstSwitch.click();
        await adminPage.waitForTimeout(1000);
        const afterVal = await firstSwitch.isChecked();
        log('12. Toggle enable/disable', beforeVal !== afterVal, `${beforeVal} -> ${afterVal}`);
      }

      // Test edit button
      const editBtn = adminPage.locator('.el-table__body tr').first().locator('button:has-text("编辑")');
      if (await editBtn.count() > 0) {
        await editBtn.click();
        await adminPage.waitForTimeout(1000);
        const editDialog = await adminPage.locator('.el-dialog').count() > 0;
        log('13. Edit dialog opens', editDialog);
        if (editDialog) {
          await adminPage.screenshot({ path: '/workspace/images/ui_test/p3_alertrules_05_edit.png' });
          // Close dialog
          await adminPage.locator('.el-dialog__headerbtn').click();
          await adminPage.waitForTimeout(500);
        }
      }

      // Test delete button (check for confirm dialog)
      const delBtn = adminPage.locator('.el-table__body tr').first().locator('button:has-text("删除")');
      if (await delBtn.count() > 0) {
        await delBtn.click();
        await adminPage.waitForTimeout(800);
        const confirmDialog = await adminPage.locator('.el-message-box').count() > 0;
        log('14. Delete confirm dialog', confirmDialog);
        if (confirmDialog) {
          await adminPage.locator('.el-message-box__btns button:has-text("取消"), .el-message-box__btns button:has-text("Cancel")').click();
          await adminPage.waitForTimeout(500);
        }
      }
    }

    // ===== Test: Alert type variations =====
    console.log('\n🔧 告警类型测试');
    await adminPage.locator('button').filter({ hasText: /添加规则|Add/ }).first().click();
    await adminPage.waitForTimeout(1000);

    // Select device_offline type
    const typeSelect = adminPage.locator('.el-dialog .el-select').first();
    await typeSelect.click();
    await adminPage.waitForTimeout(600);
    const offlineOption = adminPage.locator('.el-select-dropdown__item').filter({ hasText: /offline|离线/ });
    if (await offlineOption.count() > 0) {
      await offlineOption.click();
      await adminPage.waitForTimeout(500);
      // Check if property and operator fields are hidden
      const propField = await adminPage.locator('.el-dialog .el-form-item:has-text("监测属性")').count();
      log('15. Device offline hides property field', propField === 0, `property fields: ${propField}`);
    }

    // Close dialog
    await adminPage.locator('.el-dialog__headerbtn').click();
    await adminPage.waitForTimeout(500);

  } catch (e) {
    console.error('Test error:', e.message);
    if (adminPage) await adminPage.screenshot({ path: '/workspace/images/ui_test/p3_alertrules_error.png' });
  }

  if (adminCtx) await adminCtx.close();

  const passed = results.filter(r => r.pass).length;
  const failed = results.filter(r => !r.pass).length;
  console.log(`\n${'='.repeat(50)}`);
  console.log(`  P3 ALERT RULES TEST SUMMARY`);
  console.log(`  Total: ${results.length} | Passed: ${passed} | Failed: ${failed}`);
  console.log(`${'='.repeat(50)}`);
  if (failed > 0) {
    results.filter(r => !r.pass).forEach(r => console.log(`  ❌ ${r.name} — ${r.detail}`));
  }

  await browser.close();
})();
