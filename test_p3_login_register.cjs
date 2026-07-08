const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: '/opt/google/chrome/chrome' });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const results = [];
  const log = (name, pass, detail = '') => {
    results.push({ name, pass, detail });
    console.log(`${pass ? '✅' : '❌'} ${name}${detail ? ' — ' + detail : ''}`);
  };

  const consoleMessages = [];
  page.on('console', msg => {
    consoleMessages.push({ type: msg.type(), text: msg.text() });
  });

  try {
    // ===== 1. 注册页面访问 =====
    console.log('\n📋 注册页面测试');
    await page.goto('http://localhost:3000/register', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1000);
    await page.screenshot({ path: '/workspace/images/ui_test/p3_01_register_page.png' });
    
    const registerUrl = page.url();
    const hasTitle = await page.locator('h1').count() > 0;
    const textInputs = await page.locator('input[type="text"]').count();
    const pwdInputs = await page.locator('input[type="password"]').count();
    log('1. Register page accessible', registerUrl.includes('register') && hasTitle, `${textInputs} text inputs, ${pwdInputs} password inputs`);
    log('2. Register form has username field', textInputs >= 1);
    log('3. Register form has password+confirm fields', pwdInputs >= 2);

    const hasLoginLink = await page.locator('a[href="/login"]').count() > 0;
    log('4. Register has login link', hasLoginLink);

    // Helper: click register button (handles both Chinese and English)
    async function clickRegister() {
      const btn = page.locator('button[type="submit"]');
      if (await btn.count() > 0) {
        await btn.click();
      } else {
        const btn2 = page.locator('button').filter({ hasText: /Register|注册/ });
        await btn2.click();
      }
    }

    // ===== 2. 注册空字段验证 =====
    await clickRegister();
    await page.waitForTimeout(800);
    log('5. Empty form no crash', page.url().includes('register'), 'still on register page');

    // ===== 3. 注册密码不匹配 =====
    const timestamp = Date.now();
    const textInputsLocator = page.locator('input[type="text"]');
    await textInputsLocator.nth(0).fill(`testuser_${timestamp}`);
    const passwordInputs = page.locator('input[type="password"]');
    await passwordInputs.nth(0).fill('password123');
    await passwordInputs.nth(1).fill('different456');
    consoleMessages.length = 0;
    await clickRegister();
    await page.waitForTimeout(1000);
    
    const passwordMismatch = consoleMessages.some(m => m.text.includes('Passwords do not match'));
    log('6. Password mismatch error', passwordMismatch, passwordMismatch ? 'Frontend validation triggered' : 'no mismatch message');

    // ===== 4. 正常注册流程（重新加载页面确保干净状态）=====
    await page.goto('http://localhost:3000/register', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(500);
    const textInputs2 = page.locator('input[type="text"]');
    const pwdInputs2 = page.locator('input[type="password"]');
    await textInputs2.nth(0).fill(`testuser_${timestamp}`);
    if (await textInputs2.count() >= 2) await textInputs2.nth(1).fill(`test_${timestamp}@example.com`);
    if (await textInputs2.count() >= 3) await textInputs2.nth(2).fill(`Test User ${timestamp}`);
    await pwdInputs2.nth(0).fill('TestPass123!');
    await pwdInputs2.nth(1).fill('TestPass123!');
    
    consoleMessages.length = 0;
    await clickRegister();
    await page.waitForTimeout(3000);
    
    const registered = !page.url().includes('register');
    const tokenInStorage = await page.evaluate(() => localStorage.getItem('token'));
    log('7. Registration redirects after submit', registered, `URL: ${page.url()}`);
    log('8. Token stored after registration', !!tokenInStorage, `token length: ${tokenInStorage ? tokenInStorage.length : 0}`);

    // ===== 5. 登出测试 =====
    console.log('\n🚪 登出测试');
    await page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(2000);
    
    // 尝试找登出按钮，通常在顶部导航的用户名下拉菜单中
    const userMenu = page.locator('.el-dropdown, [class*="user"], [class*="avatar"]');
    if (await userMenu.count() > 0) {
      await userMenu.first().click();
      await page.waitForTimeout(800);
      const logoutInDropdown = page.locator('.el-dropdown-menu__item:has-text("退出"), .el-dropdown-menu__item:has-text("登出"), .el-dropdown-menu__item:has-text("Logout")');
      if (await logoutInDropdown.count() > 0) {
        await logoutInDropdown.first().click();
        await page.waitForTimeout(2000);
      }
    }
    
    const afterLogoutToken = await page.evaluate(() => localStorage.getItem('token'));
    const onLoginPage = page.url().includes('login');
    log('9. Logout clears token', !afterLogoutToken, `token: ${afterLogoutToken}`);
    log('10. Logout redirects to login', onLoginPage, `URL: ${page.url()}`);

    // ===== 6. 登录页面测试 =====
    console.log('\n🔐 登录页面测试');
    await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1000);
    await page.screenshot({ path: '/workspace/images/ui_test/p3_02_login_page.png' });
    
    const loginUrl = page.url();
    log('11. Login page accessible', loginUrl.includes('login'));
    log('12. Login has register link', await page.locator('a[href="/register"]').count() > 0);
    log('13. Login has demo button', await page.locator('button:has-text("一键体验")').count() > 0);

    // Helper: click login button
    async function clickLogin() {
      const btn = page.locator('button[type="submit"]');
      if (await btn.count() > 0) { await btn.click(); }
      else {
        const btn2 = page.locator('button').filter({ hasText: /登录|Login/ });
        await btn2.click();
      }
    }

    // ===== 7. 空字段登录 =====
    await clickLogin();
    await page.waitForTimeout(800);
    log('14. Empty login stays on page', page.url().includes('login'));

    // ===== 8. 错误密码登录 =====
    console.log('\n🚫 错误密码登录测试');
    const errorLoginResults = [];
    for (let i = 0; i < 3; i++) {
      await page.fill('input[type="text"]', 'admin');
      await page.fill('input[type="password"]', 'wrongpassword');
      consoleMessages.length = 0;
      await clickLogin();
      await page.waitForTimeout(1500);
      
      const hasErrorMsg = consoleMessages.some(m => m.type === 'error' || m.text.includes('失败') || m.text.includes('incorrect') || m.text.includes('Incorrect'));
      errorLoginResults.push({ attempt: i + 1, error: hasErrorMsg, url: page.url() });
    }
    log('15. Wrong password shows error', errorLoginResults.every(r => r.error), 
        `attempts: ${errorLoginResults.map(r => r.error).join(', ')}`);
    log('16. Wrong password stays on login', errorLoginResults.every(r => r.url.includes('login')));
    await page.screenshot({ path: '/workspace/images/ui_test/p3_03_login_error.png' });

    // ===== 9. 正确登录 =====
    console.log('\n✅ 正确登录测试');
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    consoleMessages.length = 0;
    await clickLogin();
    await page.waitForTimeout(3000);
    
    const loggedIn = !page.url().includes('login');
    const adminToken = await page.evaluate(() => localStorage.getItem('token'));
    log('17. Correct login redirects', loggedIn, `URL: ${page.url()}`);
    log('18. Token stored after login', !!adminToken, `token length: ${adminToken ? adminToken.length : 0}`);
    await page.screenshot({ path: '/workspace/images/ui_test/p3_04_login_success.png' });

    // ===== 10. 一键体验按钮 =====
    console.log('\n⚡ 一键体验测试');
    await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1000);
    const demoBtn = page.locator('button:has-text("一键体验")');
    if (await demoBtn.count() > 0) {
      await demoBtn.click();
      await page.waitForTimeout(3000);
      const demoLoggedIn = !page.url().includes('login');
      const demoToken = await page.evaluate(() => localStorage.getItem('token'));
      log('19. Demo login works', demoLoggedIn && !!demoToken, `URL: ${page.url()}`);
    } else {
      log('19. Demo button not found', false);
    }

    // ===== 11. 已登录用户访问登录页 =====
    await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(2000);
    const alreadyLogged = !page.url().includes('login');
    log('20. Logged-in user redirected from login', alreadyLogged, `URL: ${page.url()}`);

    // ===== 12. 未登录访问受保护页面 =====
    await page.evaluate(() => localStorage.removeItem('token'));
    await page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(2000);
    const redirectedToLogin = page.url().includes('login');
    log('21. Unauthenticated redirected to login', redirectedToLogin, `URL: ${page.url()}`);

    // ===== 13. 注册密码长度验证（后端限制6字符）=====
    console.log('\n🔒 密码强度测试');
    await page.goto('http://localhost:3000/register', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(500);
    const ts2 = Date.now();
    const txtInputs = page.locator('input[type="text"]');
    await txtInputs.nth(0).fill(`short_${ts2}`);
    const pwds = page.locator('input[type="password"]');
    await pwds.nth(0).fill('123');
    await pwds.nth(1).fill('123');
    consoleMessages.length = 0;
    await clickRegister();
    await page.waitForTimeout(2000);
    
    const shortPwdError = consoleMessages.some(m => m.text.includes('6') || m.text.includes('Password must be at least'));
    const stillOnReg = page.url().includes('register');
    log('22. Short password rejected', shortPwdError || stillOnReg, 
        shortPwdError ? 'Backend rejected' : `still on register: ${stillOnReg}`);

    // ===== 14. 注册用户名长度验证（后端限制3字符）=====
    await page.goto('http://localhost:3000/register', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(500);
    const txtInputs2 = page.locator('input[type="text"]');
    await txtInputs2.nth(0).fill('ab');
    const pwds2 = page.locator('input[type="password"]');
    await pwds2.nth(0).fill('password123');
    await pwds2.nth(1).fill('password123');
    consoleMessages.length = 0;
    await clickRegister();
    await page.waitForTimeout(2000);
    
    const shortUserError = consoleMessages.some(m => m.text.includes('3') || m.text.includes('Username must be at least'));
    const stillOnReg2 = page.url().includes('register');
    log('23. Short username rejected', shortUserError || stillOnReg2,
        shortUserError ? 'Backend rejected' : `still on register: ${stillOnReg2}`);

  } catch (e) {
    console.error('Test error:', e.message);
    try { await page.screenshot({ path: '/workspace/images/ui_test/p3_error.png' }); } catch(e2) {}
  }

  const passed = results.filter(r => r.pass).length;
  const failed = results.filter(r => !r.pass).length;
  console.log(`\n${'='.repeat(50)}`);
  console.log(`  P3 LOGIN/REGISTER TEST SUMMARY`);
  console.log(`  Total: ${results.length} | Passed: ${passed} | Failed: ${failed}`);
  console.log(`${'='.repeat(50)}`);
  if (failed > 0) {
    results.filter(r => !r.pass).forEach(r => console.log(`  ❌ ${r.name} — ${r.detail}`));
  }

  await browser.close();
})();
