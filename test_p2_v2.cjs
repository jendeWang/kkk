const { chromium } = require('playwright');
const fs = require('fs');

async function testP2FeaturesV2() {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  const results = { passed: [], failed: [], warnings: [], details: {} };

  async function login() {
    await page.goto('http://localhost:3000/login');
    await page.waitForTimeout(2000);
    await page.fill('input[placeholder="用户名"]', 'admin');
    await page.fill('input[placeholder="密码"]', 'admin123');
    await page.click('button:has-text("登录")');
    await page.waitForTimeout(3000);
    const s = await page.locator('text=简化').first().isVisible().catch(() => false);
    if (s) { await page.locator('text=简化').first().click(); await page.waitForTimeout(1000); }
  }

  async function openSelectAndGetOptions(locator) {
    await locator.click();
    await page.waitForTimeout(800);
    const opts = await page.locator('.el-select-dropdown__item').allTextContents();
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
    return opts;
  }

  try {
    await login();

    // ===================== 产品管理 =====================
    console.log('\n===== 产品管理 =====');
    await page.goto('http://localhost:3000/products');
    await page.waitForTimeout(4000);

    const productRows = await page.locator('.el-table__row').count();
    if (productRows > 0) {
      results.passed.push('产品-列表(' + productRows + '条)');
      const names = await page.locator('.el-table__row .cell').first().textContent().catch(() => '');
      results.details['first_product'] = names;
    }
    await page.screenshot({ path: '/workspace/images/ui_test/p2_products_list.png' });

    // 物模型详情
    const detailBtn = page.locator('button:has-text("物模型"), button:has-text("详情")').first();
    if (await detailBtn.isVisible()) {
      await detailBtn.click(); await page.waitForTimeout(1500);
      const dlg = page.locator('.el-dialog:visible').first();
      if (await dlg.isVisible()) {
        results.passed.push('产品-物模型详情弹窗显示');
        const tabs = await page.locator('.el-dialog:visible .el-tabs__item').allTextContents();
        results.details['product_model_tabs'] = tabs;
        for (const t of tabs) {
          const tabEl = page.locator('.el-dialog:visible .el-tabs__item:has-text("' + t + '")').first();
          if (await tabEl.isVisible()) {
            await tabEl.click(); await page.waitForTimeout(300);
            results.passed.push('产品-物模型"' + t + '"标签页切换');
          }
        }
        await page.locator('.el-dialog__close').first().click(); await page.waitForTimeout(500);
      }
    }

    // 新增产品弹窗
    const addBtn = page.locator('button:has-text("新增"), button:has-text("添加")').first();
    if (await addBtn.isVisible()) {
      await addBtn.click(); await page.waitForTimeout(1000);
      const dlg = page.locator('.el-dialog:visible').first();
      if (await dlg.isVisible()) {
        results.passed.push('产品-新增弹窗显示');
        await page.screenshot({ path: '/workspace/images/ui_test/p2_add_product.png' });
        const inputs = await page.locator('.el-dialog:visible input').count();
        const selects = await page.locator('.el-dialog:visible .el-select').count();
        if (inputs >= 3) results.passed.push('产品-新增表单(' + inputs + '输入+' + selects + '下拉)');
        await page.locator('.el-dialog__close').first().click(); await page.waitForTimeout(500);
      }
    }

    // ===================== 遥测数据 =====================
    console.log('\n===== 遥测数据 =====');
    await page.goto('http://localhost:3000/telemetry');
    await page.waitForTimeout(4000);

    const tmTitle = await page.locator('h3, h2').first().textContent().catch(() => '');
    if (tmTitle.includes('遥测') || tmTitle.includes('数据')) {
      results.passed.push('遥测-页面标题正确');
    }

    // 设备选择
    const devSelect = page.locator('.el-select').first();
    if (await devSelect.isVisible()) {
      const devOpts = await openSelectAndGetOptions(devSelect);
      if (devOpts.length > 0) {
        results.passed.push('遥测-设备选项(' + devOpts.length + '个): ' + devOpts.slice(0, 5).join(', '));
      }
    }

    // 属性选择
    const propSelect = page.locator('.el-select').nth(1);
    if (await propSelect.isVisible()) {
      const propOpts = await openSelectAndGetOptions(propSelect);
      if (propOpts.length > 0) {
        results.passed.push('遥测-属性选项(' + propOpts.length + '个): ' + propOpts.slice(0, 5).join(', '));
      }
    }

    // 时间范围选择
    const timePicker = page.locator('.el-date-picker, [class*="time"]').first();
    if (await timePicker.isVisible()) {
      results.passed.push('遥测-时间范围选择器存在');
    }

    // 数据展示
    const dataRows = await page.locator('.el-table__row').count();
    if (dataRows > 0) {
      results.passed.push('遥测-数据列表(' + dataRows + '条)');
    } else {
      results.warnings.push('遥测-无数据');
    }

    // 导出功能
    const exportBtn = page.locator('button:has-text("导出"), button:has-text("下载")').first();
    if (await exportBtn.isVisible()) {
      results.passed.push('遥测-导出按钮存在');
    }

    await page.screenshot({ path: '/workspace/images/ui_test/p2_telemetry.png' });

    // ===================== 命令下发 =====================
    console.log('\n===== 命令下发 =====');
    await page.goto('http://localhost:3000/commands');
    await page.waitForTimeout(4000);

    const cmdTitle = await page.locator('h3, h2').first().textContent().catch(() => '');
    if (cmdTitle.includes('命令') || cmdTitle.includes('下发')) {
      results.passed.push('命令-页面标题正确');
    }

    const cmdDevSelect = page.locator('.el-select').first();
    if (await cmdDevSelect.isVisible()) {
      const opts = await openSelectAndGetOptions(cmdDevSelect);
      if (opts.length > 0) {
        results.passed.push('命令-设备选项(' + opts.length + '个)');
      }
    }

    const svcSelect = page.locator('.el-select').nth(1);
    if (await svcSelect.isVisible()) {
      const opts = await openSelectAndGetOptions(svcSelect);
      if (opts.length > 0) {
        results.passed.push('命令-服务选项(' + opts.length + '个): ' + opts.join(', '));
      }
    }

    // 参数输入
    const params = await page.locator('.el-form-item').count();
    if (params > 0) {
      results.passed.push('命令-参数表单(' + params + '项)');
    }

    // 下发按钮
    const sendBtn = page.locator('button:has-text("下发"), button:has-text("发送")').first();
    if (await sendBtn.isVisible()) {
      results.passed.push('命令-下发按钮存在');
    }

    // 命令历史
    const historyTab = page.locator('.el-tabs__item:has-text("历史")').first();
    if (await historyTab.isVisible()) {
      await historyTab.click(); await page.waitForTimeout(1000);
      const histRows = await page.locator('.el-table__row').count();
      results.passed.push('命令-历史记录(' + histRows + '条)');
    }

    await page.screenshot({ path: '/workspace/images/ui_test/p2_commands.png' });

    // ===================== 用户管理 =====================
    console.log('\n===== 用户管理 =====');
    await page.goto('http://localhost:3000/users');
    await page.waitForTimeout(4000);

    const userRows = await page.locator('.el-table__row').count();
    if (userRows > 0) {
      results.passed.push('用户-列表(' + userRows + '条)');
    }

    const addUserBtn = page.locator('button:has-text("新增"), button:has-text("添加")').first();
    if (await addUserBtn.isVisible()) {
      await addUserBtn.click(); await page.waitForTimeout(1000);
      const dlg = page.locator('.el-dialog:visible').first();
      if (await dlg.isVisible()) {
        results.passed.push('用户-新增弹窗显示');
        await page.screenshot({ path: '/workspace/images/ui_test/p2_add_user.png' });
        
        // 角色下拉
        const roleSel = page.locator('.el-dialog:visible .el-select').first();
        if (await roleSel.isVisible()) {
          const opts = await openSelectAndGetOptions(roleSel);
          results.details['user_role_opts'] = opts;
          const expectedRoles = ['管理员', '操作员', '查看员'];
          const hasAllRoles = expectedRoles.every(r => opts.includes(r));
          if (hasAllRoles) {
            results.passed.push('用户-角色选项完整(' + opts.join(', ') + ')');
          } else {
            results.failed.push('用户-角色选项不完整: ' + opts.join(', ') + '(预期: ' + expectedRoles.join(', ') + ')');
          }
        }
        
        await page.locator('.el-dialog__close').first().click(); await page.waitForTimeout(500);
      }
    }

    // 禁用/启用开关
    const userSwitch = page.locator('.el-switch').first();
    if (await userSwitch.isVisible().catch(() => false)) {
      results.passed.push('用户-禁用/启用开关存在');
    }

    await page.screenshot({ path: '/workspace/images/ui_test/p2_users.png' });

    // ===================== 个人中心 =====================
    console.log('\n===== 个人中心 =====');
    await page.goto('http://localhost:3000/profile');
    await page.waitForTimeout(4000);

    const profTitle = await page.locator('h3, h2').first().textContent().catch(() => '');
    if (profTitle.includes('个人') || profTitle.includes('用户')) {
      results.passed.push('个人-页面标题正确');
    }

    const infoItems = await page.locator('.el-form-item, [class*="info"]').count();
    if (infoItems > 0) {
      results.passed.push('个人-信息展示(' + infoItems + '项)');
    }

    const editBtn = page.locator('button:has-text("修改"), button:has-text("编辑")').first();
    if (await editBtn.isVisible()) {
      await editBtn.click(); await page.waitForTimeout(1000);
      const form = page.locator('.el-form').first();
      if (await form.isVisible()) {
        results.passed.push('个人-修改信息表单显示');
        await page.screenshot({ path: '/workspace/images/ui_test/p2_profile_edit.png' });
      }
    }

    const pwdBtn = page.locator('button:has-text("密码"), button:has-text("修改密码")').first();
    if (await pwdBtn.isVisible()) {
      await pwdBtn.click(); await page.waitForTimeout(1000);
      const dlg = page.locator('.el-dialog:visible').first();
      if (await dlg.isVisible()) {
        results.passed.push('个人-修改密码弹窗显示');
        const pwdInputs = await page.locator('.el-dialog:visible input[type="password"]').count();
        if (pwdInputs >= 3) {
          results.passed.push('个人-修改密码表单(旧密码+新密码+确认)');
        } else {
          results.warnings.push('个人-密码输入框数量: ' + pwdInputs);
        }
        await page.locator('.el-dialog__close').first().click(); await page.waitForTimeout(500);
      }
    }

    await page.screenshot({ path: '/workspace/images/ui_test/p2_profile.png' });

    // ===================== 数据大屏 =====================
    console.log('\n===== 数据大屏 =====');
    await page.goto('http://localhost:3000/dashboard-screen');
    await page.waitForTimeout(4000);

    const screenTitle = await page.locator('h3, h2').first().textContent().catch(() => '');
    if (screenTitle.includes('大屏') || screenTitle.includes('可视化')) {
      results.passed.push('大屏-页面标题正确');
    }

    const charts = await page.locator('.chart-container, [class*="chart"], canvas').count();
    if (charts > 0) {
      results.passed.push('大屏-图表/画布(' + charts + '个)');
    }

    const fullBtn = page.locator('button:has-text("全屏")').first();
    if (await fullBtn.isVisible()) {
      results.passed.push('大屏-全屏按钮存在');
    }

    await page.screenshot({ path: '/workspace/images/ui_test/p2_screen.png' });

  } catch (error) {
    results.failed.push('测试异常: ' + error.message);
  } finally {
    await browser.close();
  }

  console.log('\n========== P2测试汇总 ==========');
  console.log('✅ 通过: ' + results.passed.length + '项');
  console.log('⚠️ 警告: ' + results.warnings.length + '项');
  console.log('❌ 失败: ' + results.failed.length + '项');
  results.passed.forEach(r => console.log('✅ ' + r));
  results.warnings.forEach(r => console.log('⚠️ ' + r));
  results.failed.forEach(r => console.log('❌ ' + r));
  fs.writeFileSync('/workspace/p2_test_result.json', JSON.stringify(results, null, 2));
  return results;
}

testP2FeaturesV2();