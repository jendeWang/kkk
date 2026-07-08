const { chromium } = require('playwright');
const fs = require('fs');

async function testP1Features() {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  const results = { passed: [], failed: [], warnings: [], details: {} };

  async function login() {
    await page.goto('http://localhost:3000/login');
    await page.waitForTimeout(2000);
    await page.fill('input[placeholder="用户名"]', 'admin');
    await page.fill('input[placeholder="密码"]', 'admin123');
    await page.click('button:has-text("登录")');
    await page.waitForTimeout(3000);
    // 确保高级模式
    const simpleText = await page.locator('text=简化').first().isVisible().catch(() => false);
    if (simpleText) {
      await page.locator('text=简化').first().click();
      await page.waitForTimeout(1000);
    }
  }

  try {
    await login();

    // ===================== 物模型编辑器 =====================
    console.log('\n========== 物模型编辑器 ==========');
    await page.goto('http://localhost:3000/thing-model');
    await page.waitForTimeout(4000);

    // 测试1: 页面加载
    console.log('测试1: 页面加载');
    const tmTitle = await page.locator('h3, h2').first().textContent().catch(() => '');
    if (tmTitle.includes('物模型') || tmTitle.includes('编辑')) {
      results.passed.push('物模型-页面标题正确');
    }
    await page.screenshot({ path: '/workspace/images/ui_test/tm_loaded.png' });

    // 测试2: 产品选择下拉
    console.log('测试2: 产品选择下拉');
    const productSelect = await page.locator('.el-select').first();
    if (await productSelect.isVisible()) {
      results.passed.push('物模型-产品选择下拉存在');
      // 点击展开
      await productSelect.click();
      await page.waitForTimeout(500);
      const productOptions = await page.locator('.el-select-dropdown__item').allTextContents();
      results.details['product_options'] = productOptions;
      if (productOptions.length >= 3) {
        results.passed.push('物模型-产品选项完整(' + productOptions.length + '个)');
      }
      // 选择第一个产品
      await page.locator('.el-select-dropdown__item').first().click();
      await page.waitForTimeout(2000);
      results.passed.push('物模型-产品选择成功');
    } else {
      results.failed.push('物模型-产品选择下拉不存在');
    }

    // 测试3: 属性/服务/事件标签页
    console.log('测试3: 标签页切换');
    const tabs = ['属性', '服务', '事件'];
    for (const tab of tabs) {
      const tabEl = await page.locator(`.el-tabs__item:has-text("${tab}")`).first();
      if (await tabEl.isVisible()) {
        await tabEl.click();
        await page.waitForTimeout(500);
        results.passed.push(`物模型-${tab}标签页切换成功`);
      } else {
        results.warnings.push(`物模型-${tab}标签页未找到`);
      }
    }
    // 回到属性标签页
    await page.locator('.el-tabs__item:has-text("属性")').first().click();
    await page.waitForTimeout(500);

    // 测试4: 属性卡片列表
    console.log('测试4: 属性卡片列表');
    const modelCards = await page.locator('.model-card, [class*="property-card"], [class*="item-card"]').count();
    results.details['property_cards'] = modelCards;
    if (modelCards > 0) {
      results.passed.push('物模型-属性卡片显示(' + modelCards + '个)');
    } else {
      results.warnings.push('物模型-属性卡片数为0');
    }

    // 测试5: 快捷添加
    console.log('测试5: 快捷添加');
    const quickAddItems = await page.locator('.quick-add-item, [class*="quick-add"] [class*="item"]').count();
    results.details['quick_add_items'] = quickAddItems;
    if (quickAddItems > 0) {
      results.passed.push('物模型-快捷添加项显示(' + quickAddItems + '个)');
      // 点击第一个快捷添加（温度）
      const firstQuick = await page.locator('.quick-add-item, [class*="quick-add"] [class*="item"]').first();
      if (await firstQuick.isVisible()) {
        await firstQuick.click();
        await page.waitForTimeout(500);
        results.passed.push('物模型-快捷添加点击成功');
      }
    } else {
      results.warnings.push('物模型-快捷添加项未找到');
    }

    // 测试6: 新增属性弹窗
    console.log('测试6: 新增属性弹窗');
    const addPropBtn = await page.locator('button:has-text("新增属性"), button:has-text("添加属性")').first();
    if (await addPropBtn.isVisible()) {
      await addPropBtn.click();
      await page.waitForTimeout(1000);
      
      const addDialog = await page.locator('.el-dialog:visible').first();
      if (await addDialog.isVisible()) {
        results.passed.push('物模型-新增属性弹窗显示');
        await page.screenshot({ path: '/workspace/images/ui_test/tm_add_prop_dialog.png' });
        
        // 检查数据类型下拉
        const dataTypeSelect = await page.locator('.el-dialog:visible .el-select').first();
        if (await dataTypeSelect.isVisible()) {
          await dataTypeSelect.click();
          await page.waitForTimeout(500);
          const dataTypes = await page.locator('.el-select-dropdown__item:visible').allTextContents();
          results.details['data_type_options'] = dataTypes;
          results.passed.push('物模型-数据类型下拉(' + dataTypes.length + '个选项)');
          // 选择一个
          await page.locator('.el-select-dropdown__item').first().click();
          await page.waitForTimeout(300);
        }
        
        // 关闭弹窗
        await page.locator('.el-dialog__close').first().click();
        await page.waitForTimeout(500);
      }
    } else {
      results.warnings.push('物模型-新增属性按钮未找到');
    }

    // 测试7: 删除确认对话框
    console.log('测试7: 删除确认对话框');
    const deleteBtn = await page.locator('[class*="model-card"] button:has-text("删除"), [class*="item"] button:has-text("删除"), .el-button--danger').first();
    if (await deleteBtn.isVisible().catch(() => false)) {
      await deleteBtn.click();
      await page.waitForTimeout(500);
      
      // 检查确认对话框
      const confirmDialog = await page.locator('.el-message-box, .el-overlay:visible').isVisible().catch(() => false);
      if (confirmDialog) {
        results.passed.push('物模型-删除确认对话框显示');
        // 取消删除
        await page.locator('button:has-text("取消")').first().click();
        await page.waitForTimeout(500);
      } else {
        results.warnings.push('物模型-删除无确认对话框');
      }
    } else {
      results.warnings.push('物模型-删除按钮未找到');
    }

    // 测试8: 保存更改按钮
    console.log('测试8: 保存更改按钮');
    const saveBtn = await page.locator('button:has-text("保存")').first();
    if (await saveBtn.isVisible()) {
      results.passed.push('物模型-保存按钮存在');
    }

    // ===================== 模板市场 =====================
    console.log('\n========== 模板市场 ==========');
    await page.goto('http://localhost:3000/template-market');
    await page.waitForTimeout(4000);

    // 测试9: 页面加载与模板卡片
    console.log('测试9: 模板卡片');
    const templateCards = await page.locator('.template-card, [class*="template"]').count();
    results.details['template_cards'] = templateCards;
    if (templateCards >= 4) {
      results.passed.push('模板-卡片显示完整(' + templateCards + '个)');
    } else if (templateCards > 0) {
      results.warnings.push('模板-卡片数量: ' + templateCards + '(预期4+)');
    } else {
      results.failed.push('模板-卡片未显示');
    }
    await page.screenshot({ path: '/workspace/images/ui_test/tm_market_loaded.png' });

    // 测试10: 分类筛选下拉
    console.log('测试10: 分类筛选');
    const categorySelect = await page.locator('select, .el-select').first();
    if (await categorySelect.isVisible()) {
      await categorySelect.click();
      await page.waitForTimeout(500);
      const catOptions = await page.locator('.el-select-dropdown__item:visible').allTextContents();
      results.details['category_options'] = catOptions;
      results.passed.push('模板-分类下拉(' + catOptions.length + '个选项)');
      
      // 选择"农业"筛选
      const agriOpt = await page.locator('.el-select-dropdown__item:has-text("农业")').first();
      if (await agriOpt.isVisible()) {
        await agriOpt.click();
        await page.waitForTimeout(1000);
        results.passed.push('模板-分类筛选"农业"成功');
      }
    }

    // 测试11: 预览物模型弹窗
    console.log('测试11: 预览物模型');
    const previewBtn = await page.locator('button:has-text("预览")').first();
    if (await previewBtn.isVisible()) {
      await previewBtn.click();
      await page.waitForTimeout(1000);
      
      const previewDialog = await page.locator('.el-dialog:visible').first();
      if (await previewDialog.isVisible()) {
        results.passed.push('模板-预览弹窗显示');
        await page.screenshot({ path: '/workspace/images/ui_test/tm_market_preview.png' });
        
        // 关闭
        await page.locator('.el-dialog__close').first().click();
        await page.waitForTimeout(500);
      }
    } else {
      results.warnings.push('模板-预览按钮未找到');
    }

    // 测试12: 使用模板创建产品
    console.log('测试12: 使用模板');
    const useBtn = await page.locator('button:has-text("使用模板")').first();
    if (await useBtn.isVisible()) {
      await useBtn.click();
      await page.waitForTimeout(3000);
      
      // 检查是否跳转到产品管理
      if (page.url().includes('/products')) {
        results.passed.push('模板-使用模板成功跳转到产品管理');
      } else {
        // 检查是否有成功提示
        const successMsg = await page.locator('.el-message--success, text=/成功|创建/').isVisible().catch(() => false);
        if (successMsg) {
          results.passed.push('模板-使用模板创建成功');
        } else {
          results.warnings.push('模板-使用模板后未跳转');
        }
      }
    }

    // ===================== 告警与规则引擎 =====================
    console.log('\n========== 告警与规则引擎 ==========');
    await page.goto('http://localhost:3000/alerts');
    await page.waitForTimeout(3000);

    // 测试13: 告警列表
    console.log('测试13: 告警列表');
    const alertTable = await page.locator('.el-table').isVisible().catch(() => false);
    const alertRows = await page.locator('.el-table__row').count();
    results.details['alert_rows'] = alertRows;
    if (alertTable && alertRows > 0) {
      results.passed.push('告警-列表显示(' + alertRows + '条)');
    } else {
      results.warnings.push('告警-列表: ' + alertRows + '条');
    }
    await page.screenshot({ path: '/workspace/images/ui_test/alerts_list.png' });

    // 测试14: 告警状态筛选下拉
    console.log('测试14: 告警筛选');
    const alertFilters = await page.locator('.el-select').count();
    if (alertFilters > 0) {
      results.passed.push('告警-筛选下拉存在(' + alertFilters + '个)');
      
      // 点击第一个筛选
      await page.locator('.el-select').first().click();
      await page.waitForTimeout(500);
      const filterOptions = await page.locator('.el-select-dropdown__item:visible').allTextContents();
      results.details['alert_filter_options'] = filterOptions;
      if (filterOptions.length > 0) {
        results.passed.push('告警-筛选选项(' + filterOptions.length + '个)');
      }
      // 点空白处关闭
      await page.locator('body').click();
      await page.waitForTimeout(300);
    }

    // 测试15: 告警规则标签页
    console.log('测试15: 告警规则');
    const ruleTab = await page.locator('.el-tabs__item:has-text("规则")').first();
    if (await ruleTab.isVisible()) {
      await ruleTab.click();
      await page.waitForTimeout(1000);
      
      const ruleRows = await page.locator('.el-table__row').count();
      results.details['rule_rows'] = ruleRows;
      if (ruleRows > 0) {
        results.passed.push('告警-规则列表(' + ruleRows + '条)');
      }
      
      // 新增规则按钮
      const addRuleBtn = await page.locator('button:has-text("新增"), button:has-text("添加")').first();
      if (await addRuleBtn.isVisible()) {
        await addRuleBtn.click();
        await page.waitForTimeout(1000);
        
        const ruleDialog = await page.locator('.el-dialog:visible').first();
        if (await ruleDialog.isVisible()) {
          results.passed.push('告警-新增规则弹窗显示');
          await page.screenshot({ path: '/workspace/images/ui_test/alert_add_rule.png' });
          
          // 检查弹窗内的下拉框
          const dialogSelects = await page.locator('.el-dialog:visible .el-select').count();
          results.details['rule_dialog_selects'] = dialogSelects;
          
          // 逐一测试每个下拉框
          for (let i = 0; i < dialogSelects; i++) {
            const sel = await page.locator('.el-dialog:visible .el-select').nth(i);
            await sel.click();
            await page.waitForTimeout(500);
            const opts = await page.locator('.el-select-dropdown__item:visible').allTextContents();
            results.details['rule_select_' + i] = opts;
            await page.locator('body').click();
            await page.waitForTimeout(300);
          }
          
          // 关闭弹窗
          await page.locator('.el-dialog__close').first().click();
          await page.waitForTimeout(500);
        }
      }
    }

    // ===================== 场景联动 =====================
    console.log('\n========== 场景联动 ==========');
    await page.goto('http://localhost:3000/scenes');
    await page.waitForTimeout(3000);

    // 测试16: 场景列表
    console.log('测试16: 场景列表');
    const sceneTable = await page.locator('.el-table').isVisible().catch(() => false);
    const sceneRows = await page.locator('.el-table__row').count();
    results.details['scene_rows'] = sceneRows;
    if (sceneTable && sceneRows > 0) {
      results.passed.push('场景-列表显示(' + sceneRows + '条)');
    } else {
      results.warnings.push('场景-列表: ' + sceneRows + '条');
    }
    await page.screenshot({ path: '/workspace/images/ui_test/scenes_list.png' });

    // 测试17: 创建场景弹窗
    console.log('测试17: 创建场景弹窗');
    const createSceneBtn = await page.locator('button:has-text("创建"), button:has-text("新增")').first();
    if (await createSceneBtn.isVisible()) {
      await createSceneBtn.click();
      await page.waitForTimeout(1000);
      
      const sceneDialog = await page.locator('.el-dialog:visible').first();
      if (await sceneDialog.isVisible()) {
        results.passed.push('场景-创建弹窗显示');
        await page.screenshot({ path: '/workspace/images/ui_test/scene_create_dialog.png' });
        
        // 测试触发类型下拉
        const triggerSelect = await page.locator('.el-dialog:visible .el-select').first();
        if (await triggerSelect.isVisible()) {
          await triggerSelect.click();
          await page.waitForTimeout(500);
          const triggerOpts = await page.locator('.el-select-dropdown__item:visible').allTextContents();
          results.details['trigger_type_options'] = triggerOpts;
          results.passed.push('场景-触发类型选项(' + triggerOpts.length + '个)');
          await page.locator('body').click();
          await page.waitForTimeout(300);
        }
        
        // 测试设备选择下拉（Bug #10修复验证）
        const deviceSelects = await page.locator('.el-dialog:visible .el-select').all();
        for (let i = 1; i < Math.min(deviceSelects.length, 4); i++) {
          await deviceSelects[i].click();
          await page.waitForTimeout(500);
          const opts = await page.locator('.el-select-dropdown__item:visible').allTextContents();
          results.details['scene_select_' + i] = opts;
          
          // 检查是否显示设备名而非数字ID
          const hasOnlyNumbers = opts.every(o => /^\d+$/.test(o.trim()));
          if (hasOnlyNumbers && opts.length > 0) {
            results.failed.push('场景-下拉选项显示数字ID(bug未修复): ' + JSON.stringify(opts));
          }
          await page.locator('body').click();
          await page.waitForTimeout(300);
        }
        
        // 关闭弹窗
        await page.locator('.el-dialog__close').first().click();
        await page.waitForTimeout(500);
      }
    } else {
      results.warnings.push('场景-创建按钮未找到');
    }

    // ===================== 截图 =====================
    await page.screenshot({ path: '/workspace/images/ui_test/p1_final.png', fullPage: true });

  } catch (error) {
    results.failed.push('测试异常: ' + error.message);
  } finally {
    await browser.close();
  }

  // ===================== 输出结果 =====================
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

testP1Features();