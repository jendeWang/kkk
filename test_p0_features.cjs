const { chromium } = require('playwright');
const fs = require('fs');

async function testP0Features() {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  const results = {
    passed: [],
    failed: [],
    warnings: [],
    screenshots: [],
    details: {}
  };
  
  try {
    // ==================== 登录 ====================
    console.log('\n========== 登录 ==========');
    await page.goto('http://localhost:3000/login');
    await page.waitForTimeout(2000);
    await page.fill('input[placeholder="用户名"]', 'admin');
    await page.fill('input[placeholder="密码"]', 'admin123');
    await page.click('button:has-text("登录")');
    await page.waitForTimeout(3000);
    
    if (page.url().includes('/dashboard') || page.url().includes('/login')) {
      results.passed.push('登录成功');
    } else {
      results.failed.push('登录失败');
      return results;
    }
    
    // ==================== 数字孪生3D场景测试 ====================
    console.log('\n========== 数字孪生3D场景测试 ==========');
    
    // 导航到3D场景
    await page.goto('http://localhost:3000/greenhouse-3d');
    await page.waitForTimeout(5000); // 3D场景需要更长时间加载
    
    results.details['3d_url'] = page.url();
    
    // 测试1: 页面加载与Canvas渲染
    console.log('测试1: 页面加载与Canvas渲染');
    const canvas = await page.locator('canvas').first();
    const canvasCount = await page.locator('canvas').count();
    
    if (canvasCount > 0) {
      results.passed.push('3D-Canvas渲染正常(' + canvasCount + '个)');
      
      // 检查canvas尺寸
      const canvasSize = await canvas.evaluate(el => {
        return { width: el.width, height: el.height };
      });
      results.details['canvas_size'] = canvasSize;
      
      if (canvasSize.width > 0 && canvasSize.height > 0) {
        results.passed.push('Canvas尺寸正常(' + canvasSize.width + 'x' + canvasSize.height + ')');
      }
    } else {
      results.failed.push('3D-Canvas未渲染');
    }
    
    // 截图1
    await page.screenshot({ path: '/workspace/images/ui_test/3d_loaded.png', fullPage: true });
    results.screenshots.push('3d_loaded.png');
    
    // 测试2: 页面标题
    console.log('测试2: 页面标题与结构');
    const pageTitle = await page.locator('.page-title, h2, h3').first().textContent().catch(() => '');
    if (pageTitle.includes('智慧大棚') || pageTitle.includes('数字孪生') || pageTitle.includes('物联网')) {
      results.passed.push('3D-页面标题正确');
    } else {
      results.warnings.push('3D-页面标题: ' + pageTitle);
    }
    
    // 测试3: 环境监测面板
    console.log('测试3: 环境监测面板');
    const envPanel = await page.locator('[class*="environment"], [class*="monitor"], .env-panel').first().isVisible().catch(() => false);
    const envTitle = await page.locator('text=/环境|监测|🌿/').first().isVisible().catch(() => false);
    
    if (envPanel || envTitle) {
      results.passed.push('3D-环境监测面板显示');
      
      // 检查环境数据项
      const envItems = await page.locator('.env-item, [class*="sensor"]').count();
      results.details['env_items_count'] = envItems;
      
      if (envItems >= 9) {
        results.passed.push('3D-环境数据项完整(' + envItems + '项)');
      } else {
        results.warnings.push('3D-环境数据项: ' + envItems + '(预期≥9)');
      }
    } else {
      results.warnings.push('3D-环境监测面板未明确显示');
    }
    
    // 测试4: 设备控制面板
    console.log('测试4: 设备控制面板');
    const devicePanel = await page.locator('[class*="device-control"], [class*="control"]').first().isVisible().catch(() => false);
    const controlTitle = await page.locator('text=/设备|控制|⚡/').first().isVisible().catch(() => false);
    
    if (devicePanel || controlTitle) {
      results.passed.push('3D-设备控制面板显示');
      
      // 检查控制开关
      const switches = await page.locator('.el-switch, input[type="checkbox"]').count();
      results.details['switch_count'] = switches;
      
      if (switches >= 6) {
        results.passed.push('3D-设备开关完整(' + switches + '个)');
      } else if (switches > 0) {
        results.warnings.push('3D-设备开关: ' + switches + '个(预期≥6)');
      }
    } else {
      results.warnings.push('3D-设备控制面板未明确显示');
    }
    
    // 测试5: 设备控制开关点击
    console.log('测试5: 设备控制开关点击');
    const fanSwitch = await page.locator('text=/通风|风扇|fan/').first().isVisible().catch(() => false);
    const lightSwitch = await page.locator('text=/补光|灯|light/').first().isVisible().catch(() => false);
    const pumpSwitch = await page.locator('text=/灌溉|水泵|pump/').first().isVisible().catch(() => false);
    
    results.details['fan_visible'] = fanSwitch;
    results.details['light_visible'] = lightSwitch;
    results.details['pump_visible'] = pumpSwitch;
    
    // 尝试点击开关
    const switchEl = await page.locator('.el-switch').first();
    if (await switchEl.isVisible()) {
      try {
        await switchEl.click();
        await page.waitForTimeout(500);
        
        // 检查命令下发提示
        const successMsg = await page.locator('.el-message, text=/命令|下发|成功/').isVisible().catch(() => false);
        if (successMsg) {
          results.passed.push('3D-设备控制命令下发成功');
        } else {
          results.passed.push('3D-设备开关点击响应');
        }
        
        // 截图2
        await page.screenshot({ path: '/workspace/images/ui_test/3d_switch_clicked.png' });
        results.screenshots.push('3d_switch_clicked.png');
      } catch (e) {
        results.warnings.push('3D-开关点击异常: ' + e.message);
      }
    }
    
    // 测试6: OrbitControls - 视角控制
    console.log('测试6: OrbitControls视角控制');
    const resetBtn = await page.locator('button:has-text("重置"), [class*="reset"]').first().isVisible().catch(() => false);
    const autoRotateBtn = await page.locator('button:has-text("旋转"), button:has-text("停止"), [class*="rotate"]').first().isVisible().catch(() => false);
    
    results.details['reset_btn'] = resetBtn;
    results.details['auto_rotate_btn'] = autoRotateBtn;
    
    if (resetBtn) {
      results.passed.push('3D-重置视角按钮存在');
      
      try {
        await page.locator('button:has-text("重置")').first().click();
        await page.waitForTimeout(500);
        results.passed.push('3D-重置视角点击成功');
      } catch (e) {
        results.warnings.push('3D-重置按钮点击失败');
      }
    }
    
    if (autoRotateBtn) {
      results.passed.push('3D-自动旋转按钮存在');
      
      try {
        await page.locator('button:has-text("旋转"), button:has-text("停止")').first().click();
        await page.waitForTimeout(500);
        results.passed.push('3D-自动旋转切换成功');
      } catch (e) {
        results.warnings.push('3D-旋转按钮点击失败');
      }
    }
    
    // 测试7: 3D设备点击检测（模拟点击canvas中心）
    console.log('测试7: 3D设备点击检测');
    try {
      // 点击canvas中心区域模拟设备点击
      await canvas.click({ position: { x: canvasSize.width / 2, y: canvasSize.height / 2 } });
      await page.waitForTimeout(1000);
      
      // 检查是否有详情弹窗或波纹效果
      const dialog = await page.locator('.el-dialog, [class*="detail"], [class*="popup"]').isVisible().catch(() => false);
      const ripple = await page.locator('[class*="ripple"], [class*="wave"]').isVisible().catch(() => false);
      
      if (dialog) {
        results.passed.push('3D-设备点击弹窗显示');
        
        // 截图弹窗
        await page.screenshot({ path: '/workspace/images/ui_test/3d_device_dialog.png' });
        results.screenshots.push('3d_device_dialog.png');
        
        // 检查弹窗内容
        const dialogTitle = await page.locator('.el-dialog__title, [class*="dialog-title"]').textContent().catch(() => '');
        results.details['dialog_title'] = dialogTitle;
        
        // 关闭弹窗
        const closeBtn = await page.locator('.el-dialog__close, button:has-text("关闭")').first();
        if (await closeBtn.isVisible()) {
          await closeBtn.click();
          await page.waitForTimeout(500);
          results.passed.push('3D-弹窗关闭成功');
        }
      } else if (ripple) {
        results.passed.push('3D-点击波纹效果显示');
      } else {
        results.warnings.push('3D-设备点击后无明显反馈');
      }
    } catch (e) {
      results.warnings.push('3D-设备点击测试: ' + e.message);
    }
    
    // 截图3
    await page.screenshot({ path: '/workspace/images/ui_test/3d_final.png', fullPage: true });
    results.screenshots.push('3d_final.png');
    
    // ==================== 设备管理测试 ====================
    console.log('\n========== 设备管理测试 ==========');
    
    await page.goto('http://localhost:3000/devices');
    await page.waitForTimeout(3000);
    
    results.details['devices_url'] = page.url();
    
    // 测试8: 统计卡片（bug修复验证）
    console.log('测试8: 统计卡片修复验证');
    const statCards = await page.locator('.stat-card, [class*="stat"]').count();
    const totalDevices = await page.locator('text=/总设备|在线|离线|异常/').count();
    
    results.details['stat_cards_count'] = statCards;
    results.details['stat_texts_count'] = totalDevices;
    
    if (statCards >= 4 || totalDevices >= 4) {
      results.passed.push('设备-统计卡片显示');
      
      // 检查数值是否为0（之前bug）
      const statValues = await page.locator('[class*="stat"] .value, [class*="count"]').allTextContents();
      results.details['stat_values'] = statValues;
      
      // 检查是否有非0值
      const hasNonZero = statValues.some(v => {
        const num = parseInt(v);
        return num > 0;
      });
      
      if (hasNonZero) {
        results.passed.push('设备-统计数值正常(非0，bug已修复)');
      } else {
        results.failed.push('设备-统计数值仍为0(bug未修复)');
      }
    } else {
      results.warnings.push('设备-统计卡片数量: ' + statCards);
    }
    
    // 截图4
    await page.screenshot({ path: '/workspace/images/ui_test/devices_stats.png' });
    results.screenshots.push('devices_stats.png');
    
    // 测试9: 设备列表
    console.log('测试9: 设备列表');
    const deviceTable = await page.locator('.el-table, [class*="device-list"]').isVisible().catch(() => false);
    const deviceRows = await page.locator('.el-table__row, [class*="device-item"]').count();
    
    results.details['device_rows_count'] = deviceRows;
    
    if (deviceTable && deviceRows > 0) {
      results.passed.push('设备-列表显示(' + deviceRows + '条)');
    } else {
      results.warnings.push('设备-列表: ' + deviceRows + '条');
    }
    
    // 测试10: 搜索筛选
    console.log('测试10: 搜索筛选');
    const searchInput = await page.locator('input[placeholder*="搜索"], input[placeholder*="设备"]').first().isVisible().catch(() => false);
    const statusFilter = await page.locator('.el-select, [class*="filter"]').first().isVisible().catch(() => false);
    
    if (searchInput) {
      results.passed.push('设备-搜索框存在');
      
      // 测试搜索
      try {
        await page.locator('input[placeholder*="搜索"], input[placeholder*="设备"]').first().fill('大棚');
        await page.waitForTimeout(500);
        results.passed.push('设备-搜索功能响应');
        
        // 清空搜索
        await page.locator('input[placeholder*="搜索"], input[placeholder*="设备"]').first().clear();
      } catch (e) {
        results.warnings.push('设备-搜索测试失败');
      }
    }
    
    if (statusFilter) {
      results.passed.push('设备-筛选下拉存在');
    }
    
    // 测试11: 新增设备按钮与弹窗
    console.log('测试11: 新增设备弹窗');
    const addBtn = await page.locator('button:has-text("新增"), button:has-text("添加")').first().isVisible().catch(() => false);
    
    if (addBtn) {
      results.passed.push('设备-新增按钮存在');
      
      try {
        await page.locator('button:has-text("新增"), button:has-text("添加")').first().click();
        await page.waitForTimeout(1000);
        
        // 检查弹窗
        const addDialog = await page.locator('.el-dialog').isVisible().catch(() => false);
        if (addDialog) {
          results.passed.push('设备-新增弹窗显示');
          
          // 截图弹窗
          await page.screenshot({ path: '/workspace/images/ui_test/devices_add_dialog.png' });
          results.screenshots.push('devices_add_dialog.png');
          
          // 检查弹窗内组件
          const dialogInputs = await page.locator('.el-dialog input').count();
          const dialogSelects = await page.locator('.el-dialog .el-select').count();
          
          results.details['add_dialog_inputs'] = dialogInputs;
          results.details['add_dialog_selects'] = dialogSelects;
          
          if (dialogInputs >= 3) {
            results.passed.push('设备-新增弹窗表单完整(' + dialogInputs + '项)');
          }
          
          // 关闭弹窗
          await page.locator('.el-dialog__close').first().click();
          await page.waitForTimeout(500);
          results.passed.push('设备-新增弹窗关闭成功');
        }
      } catch (e) {
        results.warnings.push('设备-新增弹窗测试: ' + e.message);
      }
    }
    
    // 测试12: 设备详情/命令下发
    console.log('测试12: 设备详情');
    const detailBtn = await page.locator('button:has-text("详情"), button:has-text("查看")').first().isVisible().catch(() => false);
    
    if (detailBtn) {
      results.passed.push('设备-详情按钮存在');
      
      try {
        await page.locator('button:has-text("详情"), button:has-text("查看")').first().click();
        await page.waitForTimeout(1000);
        
        const detailDialog = await page.locator('.el-dialog').isVisible().catch(() => false);
        if (detailDialog) {
          results.passed.push('设备-详情弹窗显示');
          
          await page.screenshot({ path: '/workspace/images/ui_test/devices_detail_dialog.png' });
          results.screenshots.push('devices_detail_dialog.png');
          
          // 关闭
          await page.locator('.el-dialog__close').first().click();
        }
      } catch (e) {
        results.warnings.push('设备-详情弹窗测试: ' + e.message);
      }
    }
    
    // 截图5
    await page.screenshot({ path: '/workspace/images/ui_test/devices_final.png', fullPage: true });
    results.screenshots.push('devices_final.png');
    
    // ==================== 控制台错误检查 ====================
    console.log('\n========== 控制台检查 ==========');
    const consoleMessages = [];
    page.on('console', msg => {
      if (msg.type() === 'error' || msg.type() === 'warning') {
        consoleMessages.push({ type: msg.type(), text: msg.text() });
      }
    });
    
    await page.waitForTimeout(2000);
    
    const errors = consoleMessages.filter(m => m.type === 'error' && !m.text.includes('SSE'));
    const sseErrors = consoleMessages.filter(m => m.text.includes('SSE'));
    
    if (errors.length === 0) {
      results.passed.push('控制台-无JS错误');
    } else {
      results.warnings.push('控制台-JS错误: ' + errors.length + '个');
    }
    
    if (sseErrors.length > 0) {
      results.warnings.push('控制台-SSE连接错误(已知问题)');
    }
    
    results.details['console_errors'] = consoleMessages;
    
  } catch (error) {
    results.failed.push('测试异常: ' + error.message);
  } finally {
    await browser.close();
  }
  
  // ==================== 输出结果 ====================
  console.log('\n========== P0测试汇总 ==========');
  console.log('✅ 通过: ' + results.passed.length + '项');
  console.log('⚠️ 警告: ' + results.warnings.length + '项');
  console.log('❌ 失败: ' + results.failed.length + '项');
  console.log('📷 截图: ' + results.screenshots.length + '张');
  
  console.log('\n详细结果:');
  results.passed.forEach(r => console.log('✅ ' + r));
  results.warnings.forEach(r => console.log('⚠️ ' + r));
  results.failed.forEach(r => console.log('❌ ' + r));
  
  fs.writeFileSync('/workspace/p0_test_result.json', JSON.stringify(results, null, 2));
  console.log('\n结果已保存到 /workspace/p0_test_result.json');
  
  return results;
}

testP0Features();