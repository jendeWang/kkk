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

  // Helper: login and return { page, token }
  async function loginUser(username, password) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(800);
    const inputs = await page.locator('input[type="text"]').all();
    for (const inp of inputs) {
      const ph = await inp.getAttribute('placeholder');
      if (ph && (ph.includes('用户') || ph.includes('User') || ph.includes('name'))) {
        await inp.fill(username);
        break;
      }
    }
    await page.locator('input[type="password"]').first().fill(password);
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(2500);
    const token = await page.evaluate(() => localStorage.getItem('token')).catch(() => null);
    return { page, context, token, loggedIn: !page.url().includes('login') };
  }

  // Helper: check menu
  async function hasMenuItem(page, text) {
    const items = await page.locator('.el-menu-item, .el-sub-menu__title').allTextContents();
    return items.some(i => i.includes(text));
  }

  let adminToken = null;
  let opUser = null;
  let vwUser = null;

  try {
    // ===== Admin login =====
    console.log('\n🔧 创建测试账号');
    const admin = await loginUser('admin', 'admin123');
    log('1. Admin login', admin.loggedIn);
    if (!admin.loggedIn) {
      console.log('Admin login failed, aborting');
      await browser.close();
      return;
    }
    adminToken = admin.token;
    await admin.page.screenshot({ path: '/workspace/images/ui_test/p3_perm_admin_dash.png' });

    // Create test users via API
    const ts = Date.now();
    opUser = `op_${ts}`;
    vwUser = `vw_${ts}`;

    const opCreate = await admin.page.evaluate(async ({ token, username }) => {
      try {
        const r = await fetch('/api/v1/users/', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password: 'TestPass123!', role: 'operator', email: `${username}@test.com`, full_name: `Test ${username}` })
        });
        return { status: r.status, ok: r.ok };
      } catch (e) { return { status: 0, error: e.message }; }
    }, { token: adminToken, username: opUser });
    log('2. Create operator user', opCreate.ok || opCreate.status === 201, `status: ${opCreate.status}`);

    const vwCreate = await admin.page.evaluate(async ({ token, username }) => {
      try {
        const r = await fetch('/api/v1/users/', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password: 'TestPass123!', role: 'viewer', email: `${username}@test.com`, full_name: `Test ${username}` })
        });
        return { status: r.status, ok: r.ok };
      } catch (e) { return { status: 0, error: e.message }; }
    }, { token: adminToken, username: vwUser });
    log('3. Create viewer user', vwCreate.ok || vwCreate.status === 201, `status: ${vwCreate.status}`);

    await admin.context.close();

    // ===== Operator tests =====
    console.log('\n👤 操作员权限测试');
    const op = await loginUser(opUser, 'TestPass123!');
    log('4. Operator login', op.loggedIn);

    if (op.loggedIn) {
      await op.page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded' });
      await op.page.waitForTimeout(2000);
      await op.page.screenshot({ path: '/workspace/images/ui_test/p3_perm_01_operator.png' });

      log('5. Operator sees user menu', await hasMenuItem(op.page, '用户'));
      log('6. Operator sees device menu', await hasMenuItem(op.page, '设备'));
      log('7. Operator sees alert menu', await hasMenuItem(op.page, '告警'));
      log('8. Operator sees scene menu', await hasMenuItem(op.page, '场景'));

      // API tests
      const usersApi = await op.page.evaluate(async (token) => {
        try { const r = await fetch('/api/v1/users/', { headers: { 'Authorization': `Bearer ${token}` } }); return { status: r.status, ok: r.ok }; }
        catch (e) { return { status: 0, error: e.message }; }
      }, op.token);
      log('9. Operator API GET /users/', usersApi.ok, `status: ${usersApi.status}`);

      const createDev = await op.page.evaluate(async (token) => {
        try { const r = await fetch('/api/v1/devices/', { method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ device_name: 'op_test_dev', product_id: 1 }) }); return { status: r.status, ok: r.ok }; }
        catch (e) { return { status: 0, error: e.message }; }
      }, op.token);
      log('10. Operator API POST /devices/', createDev.ok, `status: ${createDev.status}`);

      // Operator access user management page directly
      await op.page.goto('http://localhost:3000/users', { waitUntil: 'domcontentloaded' });
      await op.page.waitForTimeout(2000);
      await op.page.screenshot({ path: '/workspace/images/ui_test/p3_perm_01_op_users.png' });
      const opOnUsers = op.page.url().includes('users');
      log('11. Operator navigates to /users', opOnUsers, `URL: ${op.page.url()}`);

      await op.context.close();
    }

    // ===== Viewer tests =====
    console.log('\n👁️ 查看员权限测试');
    const vw = await loginUser(vwUser, 'TestPass123!');
    log('12. Viewer login', vw.loggedIn);

    if (vw.loggedIn) {
      await vw.page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded' });
      await vw.page.waitForTimeout(2000);
      await vw.page.screenshot({ path: '/workspace/images/ui_test/p3_perm_02_viewer.png' });

      log('13. Viewer sees user menu', await hasMenuItem(vw.page, '用户'));
      log('14. Viewer sees device menu', await hasMenuItem(vw.page, '设备'));
      log('15. Viewer sees alert menu', await hasMenuItem(vw.page, '告警'));
      log('16. Viewer sees scene menu', await hasMenuItem(vw.page, '场景'));

      const usersApi = await vw.page.evaluate(async (token) => {
        try { const r = await fetch('/api/v1/users/', { headers: { 'Authorization': `Bearer ${token}` } }); return { status: r.status, ok: r.ok }; }
        catch (e) { return { status: 0, error: e.message }; }
      }, vw.token);
      log('17. Viewer API GET /users/', usersApi.ok, `status: ${usersApi.status}`);

      const createDev = await vw.page.evaluate(async (token) => {
        try { const r = await fetch('/api/v1/devices/', { method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ device_name: 'vw_test_dev', product_id: 1 }) }); return { status: r.status, ok: r.ok }; }
        catch (e) { return { status: 0, error: e.message }; }
      }, vw.token);
      log('18. Viewer API POST /devices/', createDev.ok, `status: ${createDev.status}`);

      // Viewer access user management page directly
      await vw.page.goto('http://localhost:3000/users', { waitUntil: 'domcontentloaded' });
      await vw.page.waitForTimeout(2000);
      await vw.page.screenshot({ path: '/workspace/images/ui_test/p3_perm_02_vw_users.png' });
      const vwOnUsers = vw.page.url().includes('users');
      log('19. Viewer navigates to /users', vwOnUsers, `URL: ${vw.page.url()}`);

      // Permission bypass: try to disable admin
      const disableAdmin = await vw.page.evaluate(async (token) => {
        try { const r = await fetch('/api/v1/users/1', { method: 'PUT', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ is_active: false }) }); return { status: r.status, ok: r.ok }; }
        catch (e) { return { status: 0, error: e.message }; }
      }, vw.token);
      log('20. Viewer disable admin user', !disableAdmin.ok, `status: ${disableAdmin.status} (should fail)`);

      // Permission bypass: try to delete device
      const delDev = await vw.page.evaluate(async (token) => {
        try { const r = await fetch('/api/v1/devices/1', { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } }); return { status: r.status, ok: r.ok }; }
        catch (e) { return { status: 0, error: e.message }; }
      }, vw.token);
      log('21. Viewer delete device', !delDev.ok, `status: ${delDev.status} (should fail)`);

      await vw.context.close();
    }

    // ===== Admin re-login for cleanup =====
    console.log('\n👑 管理员权限确认');
    const admin2 = await loginUser('admin', 'admin123');
    if (admin2.loggedIn) {
      const usersApi = await admin2.page.evaluate(async (token) => {
        try { const r = await fetch('/api/v1/users/', { headers: { 'Authorization': `Bearer ${token}` } }); return { status: r.status, ok: r.ok }; }
        catch (e) { return { status: 0, error: e.message }; }
      }, admin2.token);
      log('22. Admin API GET /users/', usersApi.ok, `status: ${usersApi.status}`);

      const createDev = await admin2.page.evaluate(async (token) => {
        try { const r = await fetch('/api/v1/devices/', { method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ device_name: 'admin_test_dev', product_id: 1 }) }); return { status: r.status, ok: r.ok }; }
        catch (e) { return { status: 0, error: e.message }; }
      }, admin2.token);
      log('23. Admin API POST /devices/', createDev.ok, `status: ${createDev.status}`);

      await admin2.context.close();
    }

  } catch (e) {
    console.error('Test error:', e.message);
  }

  const passed = results.filter(r => r.pass).length;
  const failed = results.filter(r => !r.pass).length;
  console.log(`\n${'='.repeat(50)}`);
  console.log(`  P3 PERMISSION TEST SUMMARY`);
  console.log(`  Total: ${results.length} | Passed: ${passed} | Failed: ${failed}`);
  console.log(`${'='.repeat(50)}`);
  if (failed > 0) {
    results.filter(r => !r.pass).forEach(r => console.log(`  ❌ ${r.name} — ${r.detail}`));
  }

  await browser.close();
})();
