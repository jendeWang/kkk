const { chromium } = require('playwright');

async function verifyDevicesStats() {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  try {
    // 登录
    await page.goto('http://localhost:3000/login');
    await page.waitForTimeout(2000);
    await page.fill('input[placeholder="用户名"]', 'admin');
    await page.fill('input[placeholder="密码"]', 'admin123');
    await page.click('button:has-text("登录")');
    await page.waitForTimeout(3000);
    
    // 导航到设备管理
    await page.goto('http://localhost:3000/devices');
    await page.waitForTimeout(5000);
    
    // 检查统计卡片数值
    console.log('=== 检查统计卡片数值 ===');
    
    // 使用正确的类名
    const statsValues = await page.locator('.stats-value').allTextContents();
    const statsLabels = await page.locator('.stats-label').allTextContents();
    
    console.log('统计数值:', statsValues);
    console.log('统计标签:', statsLabels);
    
    // 检查是否有非零值
    let hasNonZero = false;
    for (let i = 0; i < statsValues.length; i++) {
      const num = parseInt(statsValues[i]);
      console.log(`${statsLabels[i]}: ${statsValues[i]} (数值: ${num})`);
      if (num > 0) hasNonZero = true;
    }
    
    if (hasNonZero) {
      console.log('\n✅ 统计卡片数值正常（非零）');
    } else {
      console.log('\n❌ 统计卡片数值仍为零');
    }
    
    // 截图
    await page.screenshot({ path: '/workspace/images/ui_test/devices_stats_verify.png' });
    
    // 检查网络请求
    console.log('\n=== 检查API请求 ===');
    const requests = [];
    page.on('request', req => {
      if (req.url().includes('status-summary')) {
        requests.push(req.url());
      }
    });
    page.on('response', res => {
      if (res.url().includes('status-summary')) {
        console.log('API响应状态:', res.status());
      }
    });
    
    // 刷新页面触发请求
    await page.reload();
    await page.waitForTimeout(3000);
    
    const newStatsValues = await page.locator('.stats-value').allTextContents();
    console.log('刷新后统计数值:', newStatsValues);
    
  } finally {
    await browser.close();
  }
}

verifyDevicesStats();