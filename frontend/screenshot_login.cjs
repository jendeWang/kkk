const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  const page = await context.newPage();

  console.log('正在访问登录页...');

  await page.goto('http://localhost:3000/login');
  await page.waitForTimeout(2000);

  const loginFormVisible = await page.locator('.login-container, .el-card, form').count() > 0;

  if (loginFormVisible) {
    console.log('✅ 登录页加载成功');
  } else {
    console.log('❌ 登录页加载失败');
  }

  await page.screenshot({
    path: '/workspace/images/00-login.png',
    fullPage: false
  });

  console.log('✅ 登录页截图已保存: /workspace/images/00-login.png');

  await browser.close();
  console.log('截图完成');
})();