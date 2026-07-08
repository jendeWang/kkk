const { chromium } = require('playwright');

async function verifyUserRoles() {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });

  try {
    await page.goto('http://localhost:3000/login');
    await page.waitForTimeout(2000);
    await page.fill('input[placeholder="用户名"]', 'admin');
    await page.fill('input[placeholder="密码"]', 'admin123');
    await page.click('button:has-text("登录")');
    await page.waitForTimeout(3000);
    const s = await page.locator('text=简化').first().isVisible().catch(() => false);
    if (s) { await page.locator('text=简化').first().click(); await page.waitForTimeout(1000); }

    await page.goto('http://localhost:3000/users');
    await page.waitForTimeout(4000);

    const addBtn = page.locator('button:has-text("新增")').first();
    if (await addBtn.isVisible()) {
      await addBtn.click(); await page.waitForTimeout(1000);

      const roleSel = page.locator('.el-dialog:visible .el-select').first();
      if (await roleSel.isVisible()) {
        await roleSel.click(); await page.waitForTimeout(800);
        const opts = await page.locator('.el-select-dropdown__item').allTextContents();
        console.log('角色选项:', opts);

        const expected = ['管理员', '操作员', '查看员'];
        const hasAll = expected.every(r => opts.includes(r));
        if (hasAll) {
          console.log('✅ 角色选项完整:', opts.join(', '));
        } else {
          console.log('❌ 角色选项不完整');
        }

        await page.keyboard.press('Escape');
      }

      await page.locator('.el-dialog__close').first().click();
    }
  } finally {
    await browser.close();
  }
}

verifyUserRoles();