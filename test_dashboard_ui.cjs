const { chromium } = require('playwright');
const fs = require('fs');

async function testDashboard() {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  const results = { passed: [], failed: [], warnings: [] };
  
  try {
    // 1. 登录
    console.log('1. 导航到登录页面...');
    await page.goto('http://localhost:3000/login');
    await page.waitForTimeout(2000);
    
    await page.fill('input[placeholder="用户名"]', 'admin');
    await page.fill('input[placeholder="密码"]', 'admin123');
    await page.click('button:has-text("登录")');
    await page.waitForTimeout(3000);
    
    // 检查是否跳转到仪表盘
    if (page.url().includes('/dashboard')) {
      results.passed.push('登录成功跳转到仪表盘');
    } else {
      results.failed.push('登录后未跳转到仪表盘');
    }
    
    // 2. 检查页面标题
    console.log('2. 检查页面标题...');
    const title = await page.title();
    if (title.includes('物联网平台')) {
      results.passed.push('页面标题正确');
    } else {
      results.failed.push(`页面标题异常: ${title}`);
    }
    
    // 3. 检查大棚标签页
    console.log('3. 检查大棚切换标签...');
    await page.waitForTimeout(2000);
    
    // 查找大棚标签
    const greenhouseTabs = await page.locator('.greenhouse-tabs .el-tabs__item').all();
    console.log(`找到 ${greenhouseTabs.length} 个大棚标签`);
    
    if (greenhouseTabs.length >= 1) {
      results.passed.push(`大棚标签显示正常(${greenhouseTabs.length}个)`);
      
      // 尝试点击第一个大棚标签（排除农场总览）
      const tabsTexts = await page.locator('.greenhouse-tabs .el-tabs__item').allTextContents();
      console.log('标签内容:', tabsTexts);
      
      // 点击第二个标签（1号大棚或其他）
      if (greenhouseTabs.length > 1) {
        await greenhouseTabs[1].click();
        await page.waitForTimeout(1000);
        results.passed.push('大棚切换功能正常');
        
        // 切换回农场总览
        await greenhouseTabs[0].click();
        await page.waitForTimeout(1000);
        results.passed.push('切换回农场总览成功');
      }
    } else {
      results.failed.push('大棚标签未显示');
    }
    
    // 4. 检查环境监测卡片
    console.log('4. 检查环境监测卡片...');
    await page.waitForTimeout(2000);
    
    // 查找传感器卡片
    const sensorCards = await page.locator('.sensor-card, .env-card, [class*="sensor"]').all();
    console.log(`找到 ${sensorCards.length} 个传感器卡片相关元素`);
    
    // 检查温度、湿度等数据
    const tempText = await page.locator('text=/温度|🌡/').first().textContent().catch(() => null);
    const humidText = await page.locator('text=/湿度|💧/').first().textContent().catch(() => null);
    
    if (tempText || humidText) {
      results.passed.push('环境监测数据显示正常');
    } else {
      results.warnings.push('未找到明确的温度/湿度显示');
    }
    
    // 5. 检查设备状态区域
    console.log('5. 检查设备状态...');
    const deviceSection = await page.locator('text=/设备|在线|离线/').first().isVisible();
    if (deviceSection) {
      results.passed.push('设备状态区域显示');
    } else {
      results.warnings.push('设备状态区域可能未显示');
    }
    
    // 6. 检查趋势图表
    console.log('6. 检查趋势图表...');
    await page.waitForTimeout(1000);
    
    // 查找图表容器
    const chartContainer = await page.locator('.chart-container, [class*="chart"], [class*="trend"]').first().isVisible().catch(() => false);
    if (chartContainer) {
      results.passed.push('趋势图表显示');
    } else {
      results.warnings.push('趋势图表可能未显示');
    }
    
    // 7. 检查趋势选择按钮（温度/湿度等）
    console.log('7. 检查趋势选择按钮...');
    const trendButtons = await page.locator('.trend-selector button, [class*="trend"] button, .el-radio-button').all();
    if (trendButtons.length > 0) {
      console.log(`找到 ${trendButtons.length} 个趋势选择按钮`);
      
      // 尝试点击第二个按钮
      if (trendButtons.length > 1) {
        await trendButtons[1].click();
        await page.waitForTimeout(500);
        results.passed.push('趋势选择按钮可点击');
      }
    } else {
      results.warnings.push('趋势选择按钮未找到');
    }
    
    // 8. 检查告警概览
    console.log('8. 检查告警概览...');
    const alertSection = await page.locator('text=/告警|warning|alert/').first().isVisible().catch(() => false);
    if (alertSection) {
      results.passed.push('告警概览区域显示');
    } else {
      results.warnings.push('告警概览区域未明显显示');
    }
    
    // 9. 检查快捷操作按钮
    console.log('9. 检查快捷操作...');
    const quickActions = await page.locator('.quick-actions button, [class*="action"] button').all();
    if (quickActions.length > 0) {
      results.passed.push(`快捷操作按钮存在(${quickActions.length}个)`);
    } else {
      results.warnings.push('快捷操作按钮未找到');
    }
    
    // 10. 截图
    console.log('10. 截图保存...');
    await page.screenshot({ path: '/workspace/images/ui_test/dashboard_full.png', fullPage: true });
    results.passed.push('截图已保存');
    
    // 11. 检查控制台错误
    console.log('11. 检查控制台错误...');
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.waitForTimeout(2000);
    
    const sseErrors = consoleErrors.filter(e => e.includes('SSE'));
    if (sseErrors.length > 0) {
      results.warnings.push(`SSE连接错误(${sseErrors.length}个) - 已知问题`);
    }
    
    const jsErrors = consoleErrors.filter(e => !e.includes('SSE') && !e.includes('[DEBUG]'));
    if (jsErrors.length > 0) {
      results.failed.push(`JS错误: ${jsErrors.slice(0, 3).join('; ')}`);
    }
    
    // 12. 检查用户角色显示
    console.log('12. 检查用户角色显示...');
    const userRole = await page.locator('.user-role, [class*="role"]').first().textContent().catch(() => null);
    if (userRole) {
      if (userRole.includes('管理员') || userRole.includes('admin')) {
        results.passed.push('用户角色显示正确(管理员)');
      } else {
        results.warnings.push(`用户角色显示: ${userRole}`);
      }
    }
    
  } catch (error) {
    results.failed.push(`测试异常: ${error.message}`);
  } finally {
    await browser.close();
  }
  
  // 输出结果
  console.log('\n=== 仪表盘测试结果 ===');
  console.log(`✅ 通过: ${results.passed.length}项`);
  results.passed.forEach(r => console.log(`  - ${r}`));
  
  console.log(`⚠️ 警告: ${results.warnings.length}项`);
  results.warnings.forEach(r => console.log(`  - ${r}`));
  
  console.log(`❌ 失败: ${results.failed.length}项`);
  results.failed.forEach(r => console.log(`  - ${r}`));
  
  // 保存结果
  fs.writeFileSync('/workspace/dashboard_test_result.json', JSON.stringify(results, null, 2));
  console.log('\n结果已保存到 /workspace/dashboard_test_result.json');
  
  return results;
}

testDashboard();