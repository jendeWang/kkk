const { chromium } = require('playwright');
const fs = require('fs');

async function testP1Supplement() {
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

  try {
    await login();

    // ===== 物模型编辑器补充 =====
    console.log('\n===== 物模型编辑器补充 =====');
    await page.goto('http://localhost:3000/thing-model');
    await page.waitForTimeout(4000);
    await page.locator('.el-select').first().click(); await page.waitForTimeout(800);
    await page.locator('.el-select-dropdown__item').first().click();
    await page.waitForTimeout(2000);

    // 删除确认测试
    await page.locator('.el-tabs__item:has-text("属性")').first().click(); await page.waitForTimeout(500);
    const delBtn = page.locator('.model-card .el-button--danger').first();
    if (await delBtn.isVisible().catch(() => false)) {
      await delBtn.click(); await page.waitForTimeout(1500);
      const confirmText = await page.locator('.el-message-box__message').textContent().catch(() => '');
      if (confirmText.includes('确认删除')) {
        results.passed.push('物模型-删除确认对话框(bug已修复)');
        await page.locator('button:has-text("取消")').first().click();
        await page.waitForTimeout(500);
      } else {
        results.failed.push('物模型-删除确认框内容异常: ' + confirmText);
      }
    }

    // 新增服务弹窗
    await page.locator('.el-tabs__item:has-text("服务")').first().click(); await page.waitForTimeout(500);
    const addSvc = page.locator('button:has-text("新增服务")').first();
    if (await addSvc.isVisible()) {
      await addSvc.click(); await page.waitForTimeout(1000);
      const dlg = page.locator('.el-dialog:visible').first();
      if (await dlg.isVisible()) {
        results.passed.push('物模型-新增服务弹窗显示');
        await page.screenshot({ path: '/workspace/images/ui_test/p1_add_service.png' });
        await page.locator('.el-dialog__close').first().click(); await page.waitForTimeout(500);
      }
    }

    // 新增事件弹窗
    await page.locator('.el-tabs__item:has-text("事件")').first().click(); await page.waitForTimeout(500);
    const addEvt = page.locator('button:has-text("新增事件")').first();
    if (await addEvt.isVisible()) {
      await addEvt.click(); await page.waitForTimeout(1000);
      const dlg = page.locator('.el-dialog:visible').first();
      if (await dlg.isVisible()) {
        results.passed.push('物模型-新增事件弹窗显示');
        // 事件类型下拉
        const evtTypeSel = page.locator('.el-dialog:visible .el-select').first();
        if (await evtTypeSel.isVisible()) {
          await evtTypeSel.click(); await page.waitForTimeout(800);
          const evtOpts = await page.locator('.el-select-dropdown__item').allTextContents();
          results.details['event_type_options'] = evtOpts;
          results.passed.push('物模型-事件类型选项: ' + evtOpts.join(', '));
          await page.keyboard.press('Escape');
        }
        await page.locator('.el-dialog__close').first().click(); await page.waitForTimeout(500);
      }
    }

    // ===== 模板市场补充 =====
    console.log('\n===== 模板市场补充 =====');
    await page.goto('http://localhost:3000/template-market');
    await page.waitForTimeout(4000);

    // 逐个测试分类筛选
    const categories = ['农业', '畜牧', '全部'];
    for (const cat of categories) {
      const catSel = page.locator('.el-select').first();
      await catSel.click(); await page.waitForTimeout(800);
      const opt = page.locator('.el-select-dropdown__item:has-text("' + cat + '")').first();
      if (await opt.isVisible()) {
        await opt.click(); await page.waitForTimeout(1000);
        const count = await page.locator('.template-card').count();
        results.passed.push('模板-筛选"' + cat + '": ' + count + '个模板');
      }
    }

    // 逐个测试级别筛选
    const levels = ['入门', '推荐', '专业'];
    for (const lv of levels) {
      const lvSel = page.locator('.el-select').nth(1);
      await lvSel.click(); await page.waitForTimeout(800);
      const opt = page.locator('.el-select-dropdown__item:has-text("' + lv + '")').first();
      if (await opt.isVisible()) {
        await opt.click(); await page.waitForTimeout(1000);
        const count = await page.locator('.template-card').count();
        results.passed.push('模板-级别"' + lv + '": ' + count + '个模板');
      }
    }

    // 预览弹窗深度检查
    const pvBtn = page.locator('button:has-text("预览")').first();
    if (await pvBtn.isVisible()) {
      await pvBtn.click(); await page.waitForTimeout(1000);
      const dlg = page.locator('.el-dialog:visible').first();
      if (await dlg.isVisible()) {
        // 检查预览弹窗中的每个标签页
        const pvTabs = await page.locator('.el-dialog:visible .el-tabs__item').allTextContents();
        results.details['preview_tabs'] = pvTabs;
        for (const t of pvTabs) {
          const tabEl = page.locator('.el-dialog:visible .el-tabs__item:has-text("' + t + '")').first();
          if (await tabEl.isVisible()) {
            await tabEl.click(); await page.waitForTimeout(300);
            results.passed.push('模板-预览"' + t + '"标签页切换成功');
          }
        }
        await page.locator('.el-dialog__close').first().click(); await page.waitForTimeout(500);
      }
    }

    // ===== 告警补充 =====
    console.log('\n===== 告警补充 =====');
    await page.goto('http://localhost:3000/alerts');
    await page.waitForTimeout(3000);

    // 逐个测试筛选选项
    const sel1 = page.locator('.el-select').first();
    await sel1.click(); await page.waitForTimeout(800);
    const statusOpts = await page.locator('.el-select-dropdown__item').allTextContents();
    results.details['alert_status_opts'] = statusOpts;
    // 选择"待处理"
    const pending = page.locator('.el-select-dropdown__item:has-text("待处理")').first();
    if (await pending.isVisible()) {
      await pending.click(); await page.waitForTimeout(1000);
      const r = await page.locator('.el-table__row').count();
      results.passed.push('告警-筛选"待处理": ' + r + '条');
    }

    // 严重级别筛选
    const sel2 = page.locator('.el-select').nth(1);
    await sel2.click(); await page.waitForTimeout(800);
    const sevOpts = await page.locator('.el-select-dropdown__item').allTextContents();
    results.details['alert_severity_opts'] = sevOpts;
    const warning = page.locator('.el-select-dropdown__item:has-text("警告")').first();
    if (await warning.isVisible()) {
      await warning.click(); await page.waitForTimeout(1000);
      const r = await page.locator('.el-table__row').count();
      results.passed.push('告警-筛选"警告": ' + r + '条');
    }

    // ===== 场景联动补充 =====
    console.log('\n===== 场景联动补充 =====');
    await page.goto('http://localhost:3000/scenes');
    await page.waitForTimeout(3000);

    // 创建场景弹窗深度测试
    const createBtn = page.locator('button:has-text("创建"), button:has-text("新增")').first();
    if (await createBtn.isVisible()) {
      await createBtn.click(); await page.waitForTimeout(1000);
      const sd = page.locator('.el-dialog:visible').first();
      if (await sd.isVisible()) {
        // 所有下拉框逐一测试
        const allSels = await page.locator('.el-dialog:visible .el-select').count();
        for (let i = 0; i < allSels; i++) {
          try {
            const sel = page.locator('.el-dialog:visible .el-select').nth(i);
            await sel.click(); await page.waitForTimeout(800);
            const opts = await page.locator('.el-select-dropdown__item').allTextContents();
            results.details['scene_sel_' + i] = opts;
            
            if (opts.length > 0) {
              // 检查是否全为数字ID
              const allNums = opts.every(o => /^\d+$/.test(o.trim()));
              if (allNums) {
                results.failed.push('场景-下拉' + i + '选项全为数字ID(bug未修复)');
              } else {
                results.passed.push('场景-下拉' + i + '(' + opts.length + '项): ' + opts.slice(0, 3).join(', '));
              }
              // 尝试选择第一项
              await page.locator('.el-select-dropdown__item').first().click();
              await page.waitForTimeout(300);
            }
          } catch {}
        }
        
        await page.screenshot({ path: '/workspace/images/ui_test/p1_scene_deep.png' });
        await page.locator('.el-dialog__close').first().click(); await page.waitForTimeout(500);
      }
    }

    // 启用/禁用场景开关
    const sceneSwitch = page.locator('.el-switch').first();
    if (await sceneSwitch.isVisible().catch(() => false)) {
      results.passed.push('场景-启用/禁用开关存在');
    }

  } catch (error) {
    results.failed.push('测试异常: ' + error.message);
  } finally {
    await browser.close();
  }

  console.log('\n========== P1补充测试汇总 ==========');
  console.log('✅ 通过: ' + results.passed.length + '项');
  console.log('⚠️ 警告: ' + results.warnings.length + '项');
  console.log('❌ 失败: ' + results.failed.length + '项');
  results.passed.forEach(r => console.log('✅ ' + r));
  results.warnings.forEach(r => console.log('⚠️ ' + r));
  results.failed.forEach(r => console.log('❌ ' + r));
  fs.writeFileSync('/workspace/p1_supplement_result.json', JSON.stringify(results, null, 2));
  return results;
}

testP1Supplement();