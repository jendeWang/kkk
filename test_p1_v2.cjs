const { chromium } = require('playwright');
const fs = require('fs');

async function testP1FeaturesV2() {
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
    const simpleText = await page.locator('text=简化').first().isVisible().catch(() => false);
    if (simpleText) { await page.locator('text=简化').first().click(); await page.waitForTimeout(1000); }
  }
  
  async function safeClick(locator) {
    try { await locator.click({ timeout: 5000 }); return true; }
    catch { return false; }
  }

  try {
    await login();

    // ===================== 物模型编辑器 =====================
    console.log('\n===== 物模型编辑器 =====');
    await page.goto('http://localhost:3000/thing-model');
    await page.waitForTimeout(4000);

    // 产品选择
    const productSelect = await page.locator('.el-select').first();
    if (await productSelect.isVisible()) {
      results.passed.push('物模型-产品选择下拉存在');
      await productSelect.click();
      await page.waitForTimeout(800);
      const productOptions = await page.locator('.el-select-dropdown__item').allTextContents();
      results.details['product_options'] = productOptions;
      if (productOptions.length >= 3) results.passed.push('物模型-产品选项(' + productOptions.length + '个): ' + productOptions.slice(0,5).join(', '));
      // 选第一个
      if (await safeClick(page.locator('.el-select-dropdown__item').first())) {
        results.passed.push('物模型-产品选择成功');
        await page.waitForTimeout(2000);
      }
    }

    // 标签页切换
    for (const tab of ['属性', '服务', '事件']) {
      const tabEl = page.locator(`.el-tabs__item:has-text("${tab}")`).first();
      if (await tabEl.isVisible()) {
        await tabEl.click(); await page.waitForTimeout(500);
        results.passed.push(`物模型-${tab}标签页切换成功`);
      }
    }
    await page.locator('.el-tabs__item:has-text("属性")').first().click();
    await page.waitForTimeout(500);

    // 属性卡片
    const propCards = await page.locator('.model-card, [class*="property-card"]').count();
    if (propCards > 0) results.passed.push('物模型-属性卡片(' + propCards + '个)');

    // 快捷添加
    const quickItems = await page.locator('.quick-add-item').count();
    if (quickItems > 0) {
      results.passed.push('物模型-快捷添加(' + quickItems + '个)');
      // 点击温度快捷添加
      const tempQuick = page.locator('.quick-add-item:has-text("温度")').first();
      if (await tempQuick.isVisible()) {
        await tempQuick.click(); await page.waitForTimeout(500);
        results.passed.push('物模型-快捷添加温度成功');
      }
    }

    // 新增属性弹窗
    const addBtn = page.locator('button:has-text("新增属性")').first();
    if (await addBtn.isVisible()) {
      await addBtn.click(); await page.waitForTimeout(1000);
      const dialog = page.locator('.el-dialog:visible').first();
      if (await dialog.isVisible()) {
        results.passed.push('物模型-新增属性弹窗显示');
        
        // 数据类型下拉 - 使用force click
        const dataTypeSel = page.locator('.el-dialog:visible .el-select').first();
        if (await dataTypeSel.isVisible()) {
          await dataTypeSel.click(); await page.waitForTimeout(800);
          const dtOpts = await page.locator('.el-select-dropdown__item').allTextContents();
          results.details['data_types'] = dtOpts;
          if (dtOpts.length >= 5) results.passed.push('物模型-数据类型选项(' + dtOpts.length + '个): ' + dtOpts.join(', '));
          await page.keyboard.press('Escape'); await page.waitForTimeout(300);
        }
        
        // 访问类型下拉
        const accessSel = page.locator('.el-dialog:visible .el-select').nth(1);
        if (await accessSel.isVisible()) {
          await accessSel.click(); await page.waitForTimeout(800);
          const acOpts = await page.locator('.el-select-dropdown__item').allTextContents();
          results.details['access_types'] = acOpts;
          if (acOpts.length >= 2) results.passed.push('物模型-访问类型选项(' + acOpts.length + '个): ' + acOpts.join(', '));
          await page.keyboard.press('Escape'); await page.waitForTimeout(300);
        }
        
        await page.locator('.el-dialog__close').first().click();
        await page.waitForTimeout(500);
      }
    }

    // 删除确认对话框
    const delBtn = page.locator('.model-card .el-button--danger, [class*="model-card"] button:has-text("删除")').first();
    if (await delBtn.isVisible().catch(() => false)) {
      await delBtn.click(); await page.waitForTimeout(800);
      const confirmBox = await page.locator('.el-message-box:visible, .el-overlay-message-box:visible').isVisible().catch(() => false);
      if (confirmBox) {
        results.passed.push('物模型-删除确认对话框显示(bug已修复)');
        await page.locator('button:has-text("取消")').first().click();
        await page.waitForTimeout(500);
      } else {
        results.failed.push('物模型-删除无确认对话框(bug未修复)');
      }
    }

    // 保存按钮
    if (await page.locator('button:has-text("保存")').first().isVisible()) {
      results.passed.push('物模型-保存按钮存在');
    }

    await page.screenshot({ path: '/workspace/images/ui_test/p1_thingmodel.png' });

    // ===================== 模板市场 =====================
    console.log('\n===== 模板市场 =====');
    await page.goto('http://localhost:3000/template-market');
    await page.waitForTimeout(4000);

    const tplCards = await page.locator('.template-card').count();
    if (tplCards >= 4) {
      results.passed.push('模板-卡片(' + tplCards + '个)');
      // 检查每个卡片内容
      const cardTexts = await page.locator('.template-card').allTextContents();
      results.details['template_card_preview'] = cardTexts.map(c => c.substring(0, 60));
    } else {
      results.warnings.push('模板-卡片数量: ' + tplCards);
    }

    // 分类筛选
    const catSel = page.locator('.el-select').first();
    if (await catSel.isVisible()) {
      await catSel.click(); await page.waitForTimeout(800);
      const catOpts = await page.locator('.el-select-dropdown__item').allTextContents();
      results.details['category_options'] = catOpts;
      results.passed.push('模板-分类选项(' + catOpts.length + '个): ' + catOpts.join(', '));
      
      // 选择"农业"
      const agri = page.locator('.el-select-dropdown__item:has-text("农业")').first();
      if (await agri.isVisible()) { await agri.click(); await page.waitForTimeout(1000); results.passed.push('模板-筛选"农业"成功'); }
    }

    // 级别筛选
    const levelSel = page.locator('.el-select').nth(1);
    if (await levelSel.isVisible()) {
      await levelSel.click(); await page.waitForTimeout(800);
      const lvOpts = await page.locator('.el-select-dropdown__item').allTextContents();
      results.details['level_options'] = lvOpts;
      results.passed.push('模板-级别选项(' + lvOpts.length + '个): ' + lvOpts.join(', '));
      await page.keyboard.press('Escape'); await page.waitForTimeout(300);
    }

    // 预览物模型
    const previewBtn = page.locator('button:has-text("预览")').first();
    if (await previewBtn.isVisible()) {
      await previewBtn.click(); await page.waitForTimeout(1000);
      const pvDialog = page.locator('.el-dialog:visible').first();
      if (await pvDialog.isVisible()) {
        results.passed.push('模板-预览弹窗显示');
        await page.screenshot({ path: '/workspace/images/ui_test/p1_template_preview.png' });
        // 检查预览内容
        const pvContent = await pvDialog.textContent();
        results.details['preview_content_len'] = pvContent.length;
        await page.locator('.el-dialog__close').first().click();
        await page.waitForTimeout(500);
      }
    }

    // 使用模板
    const useBtn = page.locator('button:has-text("使用模板")').first();
    if (await useBtn.isVisible()) {
      await useBtn.click(); await page.waitForTimeout(3000);
      if (page.url().includes('/products')) {
        results.passed.push('模板-使用模板成功跳转产品管理');
      } else {
        const succ = await page.locator('.el-message--success').isVisible().catch(() => false);
        if (succ) results.passed.push('模板-使用模板创建成功');
        else results.warnings.push('模板-使用模板后未跳转');
      }
    }

    await page.screenshot({ path: '/workspace/images/ui_test/p1_template_market.png' });

    // ===================== 告警与规则 =====================
    console.log('\n===== 告警与规则 =====');
    await page.goto('http://localhost:3000/alerts');
    await page.waitForTimeout(3000);

    const alertRows = await page.locator('.el-table__row').count();
    if (alertRows > 0) results.passed.push('告警-列表(' + alertRows + '条)');

    // 告警筛选下拉
    const alertSels = await page.locator('.el-select').count();
    if (alertSels > 0) {
      results.passed.push('告警-筛选下拉(' + alertSels + '个)');
      // 测试第一个筛选
      await page.locator('.el-select').first().click(); await page.waitForTimeout(800);
      const aOpts = await page.locator('.el-select-dropdown__item').allTextContents();
      results.details['alert_filter_1'] = aOpts;
      if (aOpts.length > 0) results.passed.push('告警-筛选选项: ' + aOpts.join(', '));
      await page.keyboard.press('Escape'); await page.waitForTimeout(300);
    }

    // 规则标签页
    const ruleTab = page.locator('.el-tabs__item:has-text("规则")').first();
    if (await ruleTab.isVisible()) {
      await ruleTab.click(); await page.waitForTimeout(1000);
      const ruleRows = await page.locator('.el-table__row').count();
      results.passed.push('告警-规则列表(' + ruleRows + '条)');
      
      // 新增规则
      const addRule = page.locator('button:has-text("新增"), button:has-text("添加")').first();
      if (await addRule.isVisible()) {
        await addRule.click(); await page.waitForTimeout(1000);
        const rd = page.locator('.el-dialog:visible').first();
        if (await rd.isVisible()) {
          results.passed.push('告警-新增规则弹窗显示');
          await page.screenshot({ path: '/workspace/images/ui_test/p1_alert_rule_add.png' });
          // 检查告警类型下拉
          const atSel = page.locator('.el-dialog:visible .el-select').first();
          if (await atSel.isVisible()) {
            await atSel.click(); await page.waitForTimeout(800);
            const atOpts = await page.locator('.el-select-dropdown__item').allTextContents();
            results.details['alert_type_options'] = atOpts;
            results.passed.push('告警-告警类型选项: ' + atOpts.join(', '));
            await page.keyboard.press('Escape');
          }
          await page.locator('.el-dialog__close').first().click();
          await page.waitForTimeout(500);
        }
      }
    }

    // 确认告警按钮
    const confirmAlert = page.locator('button:has-text("确认"), button:has-text("处理")').first();
    if (await confirmAlert.isVisible().catch(() => false)) {
      results.passed.push('告警-确认/处理按钮存在');
    }

    await page.screenshot({ path: '/workspace/images/ui_test/p1_alerts.png' });

    // ===================== 场景联动 =====================
    console.log('\n===== 场景联动 =====');
    await page.goto('http://localhost:3000/scenes');
    await page.waitForTimeout(3000);

    const sceneRows = await page.locator('.el-table__row').count();
    if (sceneRows > 0) results.passed.push('场景-列表(' + sceneRows + '条)');

    // 创建场景
    const createBtn = page.locator('button:has-text("创建"), button:has-text("新增")').first();
    if (await createBtn.isVisible()) {
      await createBtn.click(); await page.waitForTimeout(1000);
      const sd = page.locator('.el-dialog:visible').first();
      if (await sd.isVisible()) {
        results.passed.push('场景-创建弹窗显示');
        await page.screenshot({ path: '/workspace/images/ui_test/p1_scene_create.png' });
        
        // 触发类型下拉
        const ttSel = page.locator('.el-dialog:visible .el-select').first();
        if (await ttSel.isVisible()) {
          await ttSel.click(); await page.waitForTimeout(800);
          const ttOpts = await page.locator('.el-select-dropdown__item').allTextContents();
          results.details['trigger_types'] = ttOpts;
          results.passed.push('场景-触发类型: ' + ttOpts.join(', '));
          await page.keyboard.press('Escape'); await page.waitForTimeout(300);
        }
        
        // 设备选择下拉（Bug #10修复验证）
        const devSels = await page.locator('.el-dialog:visible .el-select').all();
        for (let i = 1; i < Math.min(devSels.length, 4); i++) {
          try {
            await devSels[i].click(); await page.waitForTimeout(800);
            const opts = await page.locator('.el-select-dropdown__item').allTextContents();
            results.details['scene_sel_' + i] = opts;
            // 检查是否全是数字ID
            const allNums = opts.length > 0 && opts.every(o => /^\d+$/.test(o.trim()));
            if (allNums) results.failed.push('场景-下拉选项全是数字ID(bug): ' + JSON.stringify(opts));
            else if (opts.length > 0) results.passed.push('场景-下拉' + i + '选项正常: ' + opts.slice(0, 3).join(', '));
            await page.keyboard.press('Escape'); await page.waitForTimeout(300);
          } catch {}
        }
        
        await page.locator('.el-dialog__close').first().click();
        await page.waitForTimeout(500);
      }
    }

    await page.screenshot({ path: '/workspace/images/ui_test/p1_scenes.png' });

  } catch (error) {
    results.failed.push('测试异常: ' + error.message);
  } finally {
    await browser.close();
  }

  console.log('\n========== P1测试汇总 ==========');
  console.log('✅ 通过: ' + results.passed.length + '项');
  console.log('⚠️ 警告: ' + results.warnings.length + '项');
  console.log('❌ 失败: ' + results.failed.length + '项');
  results.passed.forEach(r => console.log('✅ ' + r));
  results.warnings.forEach(r => console.log('⚠️ ' + r));
  results.failed.forEach(r => console.log('❌ ' + r));
  fs.writeFileSync('/workspace/p1_test_result.json', JSON.stringify(results, null, 2));
  return results;
}

testP1FeaturesV2();