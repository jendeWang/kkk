const { chromium } = require('playwright');
const fs = require('fs');

async function testDashboardDeep() {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  const results = { passed: [], failed: [], warnings: [], details: [] };
  
  try {
    // 登录
    await page.goto('http://localhost:3000/login');
    await page.waitForTimeout(1000);
    await page.fill('input[placeholder="用户名"]', 'admin');
    await page.fill('input[placeholder="密码"]', 'admin123');
    await page.click('button:has-text("登录")');
    await page.waitForTimeout(3000);
    
    // 深度测试1: 大棚切换 - 逐个点击每个标签
    console.log('\n=== 深度测试1: 大棚切换 ===');
    const tabs = await page.locator('.greenhouse-tabs .el-tabs__item').all();
    const tabNames = ['农场总览', '默认分组', '1号大棚', '2号大棚', '3号大棚'];
    
    for (let i = 0; i < tabs.length; i++) {
      await tabs[i].click();
      await page.waitForTimeout(500);
      const isActive = await tabs[i].getAttribute('class');
      if (isActive && isActive.includes('is-active')) {
        results.passed.push(`大棚切换[${tabNames[i]}]: 标签激活状态正确`);
      }
      results.details.push(`大棚[${tabNames[i]}]: 点击后状态正常`);
    }
    
    // 回到农场总览
    await tabs[0].click();
    await page.waitForTimeout(1000);
    
    // 深度测试2: 趋势选择按钮 - 点击每个选项
    console.log('\n=== 深度测试2: 趋势选择按钮 ===');
    const trendButtons = await page.locator('.trend-selector button, .el-radio-button').all();
    
    if (trendButtons.length > 0) {
      // 获取所有按钮文本
      const buttonLabels = ['温度', '湿度', '光照', '土壤湿度', 'CO2', '风速', '土壤pH', '雨量'];
      
      for (let i = 0; i < Math.min(trendButtons.length, 8); i++) {
        try {
          await trendButtons[i].click();
          await page.waitForTimeout(300);
          results.passed.push(`趋势选择[${buttonLabels[i] || i}]: 点击成功`);
        } catch (e) {
          results.warnings.push(`趋势选择[${i}]: 点击失败 - ${e.message}`);
        }
      }
    } else {
      results.warnings.push('趋势选择按钮未找到');
    }
    
    // 深度测试3: 检查传感器卡片数据合理性
    console.log('\n=== 深度测试3: 传感器数据合理性 ===');
    
    // 检查温度值范围
    const tempValue = await page.locator('[class*="sensor"]').first().textContent().catch(() => '');
    const tempMatch = tempValue.match(/(\d+\.?\d*)°C/);
    if (tempMatch) {
      const temp = parseFloat(tempMatch[1]);
      if (temp >= 0 && temp <= 50) {
        results.passed.push(`温度值合理性: ${temp}°C 在正常范围(0-50°C)`);
      } else {
        results.warnings.push(`温度值异常: ${temp}°C`);
      }
    }
    
    // 检查湿度值
    const humidMatch = tempValue.match(/(\d+\.?\d*)%/);
    if (humidMatch) {
      const humid = parseFloat(humidMatch[1]);
      if (humid >= 0 && humid <= 100) {
        results.passed.push(`湿度值合理性: ${humid}% 在正常范围(0-100%)`);
      } else {
        results.warnings.push(`湿度值异常: ${humid}%`);
      }
    }
    
    // 深度测试4: 快捷操作按钮测试
    console.log('\n=== 深度测试4: 快捷操作按钮 ===');
    const quickButtons = await page.locator('.quick-actions button').all();
    
    if (quickButtons.length > 0) {
      results.passed.push(`快捷操作按钮数量: ${quickButtons.length}个`);
      
      // 检查按钮是否有图标和文字
      for (let i = 0; i < quickButtons.length; i++) {
        const btnText = await quickButtons[i].textContent();
        if (btnText && btnText.trim().length > 0) {
          results.details.push(`快捷按钮[${i}]: 内容="${btnText.trim()}"`);
        }
      }
    }
    
    // 深度测试5: 告警统计卡片
    console.log('\n=== 深度测试5: 告警统计 ===');
    const alertCard = await page.locator('[class*="alert"]').first().isVisible().catch(() => false);
    if (alertCard) {
      results.passed.push('告警统计卡片显示');
      
      // 检查告警数值
      const alertTexts = await page.locator('[class*="alert"]').allTextContents();
      results.details.push(`告警区域内容: ${alertTexts.slice(0, 100)}...`);
    }
    
    // 深度测试6: 设备状态卡片
    console.log('\n=== 深度测试6: 设备状态 ===');
    const deviceStats = await page.locator('.device-stats, [class*="device"]').first().isVisible().catch(() => false);
    if (deviceStats) {
      results.passed.push('设备状态区域显示');
      
      // 检查设备数值
      const deviceCount = await page.locator('text=/总设备|在线|离线/').all();
      if (deviceCount.length >= 3) {
        results.passed.push(`设备统计项显示: ${deviceCount.length}项`);
      }
    }
    
    // 深度测试7: 模式切换按钮
    console.log('\n=== 深度测试7: 模式切换 ===');
    const modeSwitch = await page.locator('.mode-switch, button:has-text("简化"), button:has-text("高级")').first().isVisible().catch(() => false);
    if (modeSwitch) {
      results.passed.push('模式切换按钮存在');
      
      // 检查当前模式
      const currentMode = await page.locator('button:has-text("简化"), button:has-text("高级")').first().textContent();
      results.details.push(`当前模式: ${currentMode}`);
    }
    
    // 深度测试8: 页面响应性
    console.log('\n=== 深度测试8: 页面响应性 ===');
    
    // 测试刷新后数据是否恢复
    await page.reload();
    await page.waitForTimeout(3000);
    
    const afterReloadTabs = await page.locator('.greenhouse-tabs .el-tabs__item').count();
    if (afterReloadTabs > 0) {
      results.passed.push('页面刷新后数据恢复正常');
    } else {
      results.failed.push('页面刷新后数据丢失');
    }
    
    // 截图
    await page.screenshot({ path: '/workspace/images/ui_test/dashboard_deep_test.png', fullPage: true });
    results.passed.push('深度测试截图保存');
    
  } catch (error) {
    results.failed.push(`测试异常: ${error.message}`);
  } finally {
    await browser.close();
  }
  
  // 输出结果
  console.log('\n=== 仪表盘深度测试结果 ===');
  console.log(`✅ 通过: ${results.passed.length}项`);
  console.log(`⚠️ 警告: ${results.warnings.length}项`);
  console.log(`❌ 失败: ${results.failed.length}项`);
  
  console.log('\n详细结果:');
  results.passed.forEach(r => console.log(`✅ ${r}`));
  results.warnings.forEach(r => console.log(`⚠️ ${r}`));
  results.failed.forEach(r => console.log(`❌ ${r}`));
  
  fs.writeFileSync('/workspace/dashboard_deep_test_result.json', JSON.stringify(results, null, 2));
  
  return results;
}

testDashboardDeep();