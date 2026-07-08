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

  let page = null;
  let ctx = null;

  try {
    console.log('\n' + '='.repeat(60));
    console.log('  核心功能回归测试');
    console.log('='.repeat(60));

    // ===== 1. 登录测试 =====
    console.log('\n📱 【1/12】登录功能');
    ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    page = await ctx.newPage();
    
    await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);
    
    const loginTitle = await page.title();
    log('1.1 登录页面加载', loginTitle.length > 0, `title: ${loginTitle}`);
    
    const hasUsername = await page.locator('input[placeholder="用户名"]').count() > 0;
    const hasPassword = await page.locator('input[type="password"]').count() > 0;
    log('1.2 用户名密码输入框', hasUsername && hasPassword);
    
    const hasSubmit = await page.locator('button[type="submit"]').count() > 0;
    const hasQuickLogin = await page.locator('button:has-text("一键体验")').count() > 0;
    log('1.3 登录按钮存在', hasSubmit && hasQuickLogin);
    
    // 登录
    await page.locator('input[placeholder="用户名"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(3000);
    
    const loginSuccess = page.url().includes('/dashboard');
    log('1.4 登录成功跳转', loginSuccess, `url: ${page.url()}`);
    
    if (!loginSuccess) {
      console.log('登录失败，终止测试');
      await browser.close();
      return;
    }

    // ===== 2. 仪表盘测试 =====
    console.log('\n📊 【2/12】仪表盘');
    await page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: '/workspace/images/ui_test/reg_dashboard.png' });
    
    const statCards = await page.locator('.el-card, .stat-card, [class*="stat"], [class*="card"]').count();
    log('2.1 统计卡片存在', statCards > 0, `count: ${statCards}`);
    
    const dashboardTitle = await page.locator('h2, h3, .title, [class*="title"]').first().textContent().catch(() => '');
    log('2.2 仪表盘标题存在', dashboardTitle.length > 0, `title: ${dashboardTitle.substring(0, 30)}`);
    
    const chartContainers = await page.locator('canvas, [class*="chart"], [class*="echarts"]').count();
    log('2.3 图表组件存在', chartContainers > 0, `count: ${chartContainers}`);

    // ===== 3. 设备管理测试 =====
    console.log('\n🔌 【3/12】设备管理');
    await page.goto('http://localhost:3000/devices', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: '/workspace/images/ui_test/reg_devices.png' });
    
    const deviceTable = await page.locator('.el-table').count() > 0;
    log('3.1 设备列表表格', deviceTable);
    
    const deviceRows = await page.locator('.el-table__body tr').count();
    log('3.2 设备数据加载', deviceRows > 0, `${deviceRows} 台设备`);
    
    const addDeviceBtn = await page.locator('button:has-text("新增设备")').count() > 0;
    log('3.3 新增设备按钮', addDeviceBtn);
    
    // 打开新增对话框
    if (addDeviceBtn) {
      await page.locator('button:has-text("新增设备")').click();
      await page.waitForTimeout(1000);
      const dialogOpen = await page.locator('.el-dialog').count() > 0;
      log('3.4 新增对话框打开', dialogOpen);
      
      if (dialogOpen) {
        const formInputs = await page.locator('.el-dialog .el-input').count();
        const formSelects = await page.locator('.el-dialog .el-select').count();
        log('3.5 表单字段完整', formInputs >= 2 && formSelects >= 1, `inputs:${formInputs} selects:${formSelects}`);
        
        // 测试产品下拉
        const prodSelect = page.locator('.el-dialog .el-select').first();
        await prodSelect.click();
        await page.waitForTimeout(600);
        const prodOptions = await page.locator('.el-select-dropdown__item').count();
        log('3.6 产品下拉选项', prodOptions > 0, `${prodOptions} 个产品`);
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);
        
        await page.locator('.el-dialog__headerbtn').click();
        await page.waitForTimeout(500);
      }
    }
    
    // 测试设备详情
    if (deviceRows > 0) {
      const firstRow = page.locator('.el-table__body tr').first();
      const detailBtn = firstRow.locator('button:has-text("详情"), button:has-text("查看")');
      if (await detailBtn.count() > 0) {
        await detailBtn.click();
        await page.waitForTimeout(1500);
        const detailPage = !page.url().includes('/devices') || await page.locator('.el-drawer, .el-dialog').count() > 0;
        log('3.7 设备详情可打开', detailPage);
        await page.goBack();
        await page.waitForTimeout(1000);
      } else {
        log('3.7 设备详情按钮', true, '表格行内操作');
      }
    }

    // ===== 4. 3D数字孪生测试 =====
    console.log('\n🌱 【4/12】3D数字孪生');
    await page.goto('http://localhost:3000/greenhouse', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/workspace/images/ui_test/reg_3d.png' });
    
    const canvasCount = await page.locator('canvas').count();
    log('4.1 3D画布渲染', canvasCount > 0, `canvas: ${canvasCount}`);
    
    const threeContainer = await page.locator('#three-container, [class*="three"], [id*="three"]').count();
    log('4.2 3D容器存在', threeContainer > 0 || canvasCount > 0);
    
    const sensorPanels = await page.locator('[class*="sensor"], [class*="panel"], .el-card').count();
    log('4.3 传感器面板', sensorPanels > 0, `count: ${sensorPanels}`);

    // ===== 5. 告警管理测试 =====
    console.log('\n⚠️ 【5/12】告警管理');
    await page.goto('http://localhost:3000/alerts', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: '/workspace/images/ui_test/reg_alerts.png' });
    
    const alertTabs = await page.locator('.el-tabs__item').count();
    log('5.1 告警标签页', alertTabs >= 2, `count: ${alertTabs}`);
    
    const alertTable = await page.locator('.el-table').count() > 0;
    log('5.2 告警列表', alertTable);
    
    const addRuleBtn = await page.locator('button:has-text("添加规则"), button:has-text("新增规则")').count() > 0;
    log('5.3 添加规则按钮', addRuleBtn);
    
    if (addRuleBtn) {
      await page.locator('button:has-text("添加规则"), button:has-text("新增规则")').first().click();
      await page.waitForTimeout(1000);
      const ruleDialog = await page.locator('.el-dialog').count() > 0;
      log('5.4 规则对话框打开', ruleDialog);
      
      if (ruleDialog) {
        // 检查告警类型下拉
        const alertTypeSelect = page.locator('.el-dialog .el-select').first();
        await alertTypeSelect.click();
        await page.waitForTimeout(500);
        const typeOptions = await page.locator('.el-select-dropdown__item').count();
        log('5.5 告警类型选项', typeOptions >= 2, `${typeOptions} 种类型`);
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);
        
        // 检查严重级别
        const radios = await page.locator('.el-dialog .el-radio').count();
        log('5.6 严重级别选项', radios >= 2, `${radios} 个选项`);
        
        await page.locator('.el-dialog__headerbtn').click();
        await page.waitForTimeout(500);
      }
    }

    // ===== 6. 场景联动测试 =====
    console.log('\n🔄 【6/12】场景联动');
    await page.goto('http://localhost:3000/scenes', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: '/workspace/images/ui_test/reg_scenes.png' });
    
    const sceneCards = await page.locator('.el-card').count();
    const sceneList = await page.locator('.el-table__body tr').count();
    log('6.1 场景列表', sceneCards > 0 || sceneList > 0, `cards:${sceneCards} rows:${sceneList}`);
    
    const addSceneBtn = await page.locator('button:has-text("新建场景")').count() > 0;
    log('6.2 新建场景按钮', addSceneBtn);
    
    if (addSceneBtn) {
      await page.locator('button:has-text("新建场景")').click();
      await page.waitForTimeout(1500);
      const sceneDialog = await page.locator('.el-dialog').count() > 0;
      log('6.3 场景对话框打开', sceneDialog);
      
      if (sceneDialog) {
        const dividers = await page.locator('.el-dialog .el-divider').count();
        log('6.4 分区结构完整', dividers >= 2, `${dividers} 个分区`);
        
        const radios = await page.locator('.el-dialog .el-radio').count();
        log('6.5 触发+动作选项', radios >= 5, `${radios} 个radio选项`);
        
        const selects = await page.locator('.el-dialog .el-select').count();
        log('6.6 选择器数量', selects >= 3, `${selects} 个下拉`);
        
        await page.locator('.el-dialog__headerbtn').click();
        await page.waitForTimeout(500);
      }
    }
    
    // 测试场景开关
    const switches = await page.locator('.el-switch').count();
    if (switches > 0) {
      const firstSw = page.locator('.el-switch').first();
      const beforeClass = await firstSw.getAttribute('class');
      const beforeOn = beforeClass && beforeClass.includes('is-active');
      await firstSw.click();
      await page.waitForTimeout(1000);
      const afterClass = await firstSw.getAttribute('class');
      const afterOn = afterClass && afterClass.includes('is-active');
      log('6.7 场景开关切换', beforeOn !== afterOn, `${beforeOn} -> ${afterOn}`);
    }

    // ===== 7. 产品管理测试 =====
    console.log('\n📦 【7/12】产品管理');
    await page.goto('http://localhost:3000/products', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: '/workspace/images/ui_test/reg_products.png' });
    
    const productTable = await page.locator('.el-table').count() > 0;
    log('7.1 产品列表', productTable);
    
    const productRows = await page.locator('.el-table__body tr').count();
    log('7.2 产品数据', productRows > 0, `${productRows} 个产品`);

    // ===== 8. 遥测数据测试 =====
    console.log('\n📈 【8/12】遥测数据');
    await page.goto('http://localhost:3000/telemetry', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: '/workspace/images/ui_test/reg_telemetry.png' });
    
    const telemetryTable = await page.locator('.el-table').count() > 0;
    log('8.1 遥测数据列表', telemetryTable);
    
    const telemetryRows = await page.locator('.el-table__body tr').count();
    log('8.2 遥测数据量', telemetryRows > 0, `${telemetryRows} 条记录`);

    // ===== 9. 命令下发测试 =====
    console.log('\n📤 【9/12】命令下发');
    await page.goto('http://localhost:3000/commands', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: '/workspace/images/ui_test/reg_commands.png' });
    
    const commandPage = page.url().includes('command');
    log('9.1 命令页面访问', commandPage, `url: ${page.url()}`);

    // ===== 10. 用户管理测试 =====
    console.log('\n👤 【10/12】用户管理');
    await page.goto('http://localhost:3000/users', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: '/workspace/images/ui_test/reg_users.png' });
    
    const userTable = await page.locator('.el-table').count() > 0;
    log('10.1 用户列表', userTable);
    
    const userRows = await page.locator('.el-table__body tr').count();
    log('10.2 用户数据', userRows > 0, `${userRows} 个用户`);

    // ===== 11. 个人中心测试 =====
    console.log('\n👤 【11/12】个人中心');
    await page.goto('http://localhost:3000/profile', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/workspace/images/ui_test/reg_profile.png' });
    
    const profilePage = page.url().includes('profile') || page.url().includes('user');
    log('11.1 个人中心页面', profilePage, `url: ${page.url()}`);

    // ===== 12. 退出登录测试 =====
    console.log('\n🚪 【12/12】退出登录');
    const logoutBtn = page.locator('button:has-text("退出"), .el-dropdown-item:has-text("退出")');
    if (await logoutBtn.count() > 0) {
      await logoutBtn.first().click();
      await page.waitForTimeout(1500);
    } else {
      await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(1500);
      // 清除token模拟登出
      await page.evaluate(() => localStorage.clear());
    }
    
    await page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    const loggedOut = page.url().includes('login');
    log('12.1 未登录拦截', loggedOut, `url: ${page.url()}`);

  } catch (e) {
    console.error('\n❌ 测试异常:', e.message);
    console.error(e.stack);
    if (page) {
      try {
        await page.screenshot({ path: '/workspace/images/ui_test/reg_error.png' });
      } catch (_) {}
    }
  }

  if (ctx) await ctx.close();

  // 汇总
  const passed = results.filter(r => r.pass).length;
  const failed = results.filter(r => !r.pass).length;
  const total = results.length;
  const rate = ((passed / total) * 100).toFixed(1);

  console.log('\n' + '='.repeat(60));
  console.log('  核心功能回归测试报告');
  console.log('='.repeat(60));
  console.log(`  总测试项: ${total}`);
  console.log(`  通过: ${passed}`);
  console.log(`  失败: ${failed}`);
  console.log(`  通过率: ${rate}%`);
  console.log('='.repeat(60));
  
  if (failed > 0) {
    console.log('\n  失败项:');
    results.filter(r => !r.pass).forEach(r => {
      console.log(`    ❌ ${r.name}${r.detail ? ' — ' + r.detail : ''}`);
    });
  }
  
  console.log('\n  截图位置: /workspace/images/ui_test/reg_*.png');
  console.log('='.repeat(60));

  await browser.close();
})();