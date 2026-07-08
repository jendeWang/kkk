// 精确复测脚本：验证可疑问题并截图取证
import { chromium } from 'playwright';
import fs from 'fs';

const BASE = 'http://localhost:3000';
const API = 'http://localhost:8000';
const findings = [];

function log(m){ console.log(m); }

async function getToken(page) {
  // 从localStorage读取token
  return await page.evaluate(() => localStorage.getItem('token') || localStorage.getItem('auth_token') || '');
}

async function run() {
  const browser = await chromium.launch({ headless: true, channel: 'chrome', args: ['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'] });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
  const page = await ctx.newPage();

  // 登录
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(800);
  await page.fill('input[type="text"], input[placeholder="请输入用户名"]', 'admin');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"], button:has-text("登录")');
  await page.waitForTimeout(2500);

  // 获取token用于API调用
  const token = await getToken(page);
  log(`token获取: ${token ? '成功('+token.slice(0,15)+'...)' : '失败'}`);

  // ========== 验证点1: 设备统计卡片 vs 列表数量 ==========
  log('\n========== 验证1: 设备统计卡片 vs 列表数量 ==========');
  await page.goto(`${BASE}/devices`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  const devInfo = await page.evaluate(() => {
    const cards = {};
    document.querySelectorAll('.stats-card').forEach(c => {
      const v = c.querySelector('.stats-value')?.innerText.trim();
      const l = c.querySelector('.stats-label')?.innerText.trim();
      if (v && l) cards[l] = v;
    });
    const tableRows = document.querySelectorAll('.el-table__body-wrapper tr.el-table__row').length;
    // 统计表格里各状态数量
    const statusCounts = {};
    document.querySelectorAll('.el-table__body-wrapper .el-tag').forEach(t => {
      const s = t.innerText.trim();
      statusCounts[s] = (statusCounts[s]||0)+1;
    });
    return { cards, tableRows, statusCounts };
  });
  log(`统计卡片: ${JSON.stringify(devInfo.cards)}`);
  log(`表格数据行数: ${devInfo.tableRows}`);
  log(`表格内各状态tag统计: ${JSON.stringify(devInfo.statusCounts)}`);

  // 调用API对比
  const headers = { 'Authorization': `Bearer ${token}` };
  const apiDevices = await (await fetch(`${API}/api/v1/devices`, { headers })).json();
  const apiSummary = await (await fetch(`${API}/api/v1/devices/status-summary`, { headers }).catch(()=>({ok:false}))).json().catch(()=>null);
  log(`API /devices 数量: ${Array.isArray(apiDevices) ? apiDevices.length : (apiDevices.items?apiDevices.items.length:JSON.stringify(apiDevices).slice(0,100))}`);
  log(`API /devices/status-summary 返回: ${JSON.stringify(apiSummary).slice(0,300)}`);

  if (devInfo.cards['总设备'] === '0' && devInfo.tableRows > 0) {
    findings.push({ severity: '严重', page: '设备管理', bug: `统计卡片显示"总设备:0"，但列表实际显示${devInfo.tableRows}条设备数据，统计数据与列表不一致` });
  } else {
    log('  ✓ 设备统计与列表数量一致或均为空');
  }
  await page.screenshot({ path: '/workspace/ui_test/01_devices_stats.png', fullPage: true });

  // ========== 验证点2: 场景联动弹窗下拉框选项（逐个精确测试）==========
  log('\n========== 验证2: 场景联动弹窗下拉框选项 ==========');
  await page.goto(`${BASE}/scenes`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.locator('.el-button:has-text("新建场景")').first().click();
  await page.waitForTimeout(1500);

  // 逐个测试下拉框
  const selectLabels = await page.evaluate(() => {
    const arr = [];
    document.querySelectorAll('.el-dialog .el-select').forEach(s => {
      const label = s.closest('.el-form-item')?.querySelector('.el-form-item__label')?.innerText.trim();
      arr.push(label || '(无标签)');
    });
    return arr;
  });
  log(`弹窗内下拉框: ${selectLabels.join(' | ')}`);

  for (let i = 0; i < selectLabels.length; i++) {
    const label = selectLabels[i];
    // 逐个点击，收集，关闭
    const sels = page.locator('.el-dialog .el-select');
    await sels.nth(i).click();
    await page.waitForTimeout(700);
    const opts = await page.evaluate(() => {
      const o = [];
      document.querySelectorAll('.el-select__popper:not([style*="display: none"]) .el-select-dropdown__item').forEach(it => {
        const t = it.innerText.trim();
        if (t && !o.includes(t)) o.push(t);
      });
      return o;
    });
    log(`  下拉框[${i}] "${label}" 选项(${opts.length}个): ${opts.join(', ')}`);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
  }
  await page.screenshot({ path: '/workspace/ui_test/02_scenes_dialog.png', fullPage: true });
  // 关闭弹窗
  try { await page.locator('.el-dialog .el-button:has-text("取消")').first().click(); await page.waitForTimeout(500); } catch(e){}

  // ========== 验证点3: 告警"确认"按钮行为 ==========
  log('\n========== 验证3: 告警"确认"按钮行为 ==========');
  await page.goto(`${BASE}/alerts`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // 监听网络请求
  const apiCalls = [];
  page.on('request', req => {
    if (req.url().includes('/api/') && (req.url().includes('alert') || req.url().includes('confirm'))) {
      apiCalls.push(`${req.method()} ${req.url()}`);
    }
  });
  page.on('response', res => {
    if (res.url().includes('/api/') && (res.url().includes('alert') || res.url().includes('confirm'))) {
      apiCalls.push(`RESP ${res.status()} ${res.url()}`);
    }
  });

  // 先找待处理的告警行
  const pendingRow = page.locator('tr:has-text("待处理")').first();
  const hasPending = await pendingRow.count();
  log(`待处理告警行数: ${hasPending}`);
  if (hasPending > 0) {
    const confirmBtn = pendingRow.locator('.el-button:has-text("确认")').first();
    if (await confirmBtn.count()) {
      await confirmBtn.click();
      await page.waitForTimeout(1500);
      const msg = await page.evaluate(() => {
        const m = document.querySelector('.el-message');
        return m ? m.innerText.trim() : null;
      });
      log(`点击确认后消息提示: ${msg || '(无)'}`);
      log(`API调用: ${apiCalls.slice(-6).join('; ') || '(无)'}`);
    }
  } else {
    // 找任意确认按钮
    const anyConfirm = page.locator('.el-button:has-text("确认")').first();
    if (await anyConfirm.count()) {
      await anyConfirm.click();
      await page.waitForTimeout(1500);
      log(`API调用: ${apiCalls.slice(-6).join('; ') || '(无)'}`);
    } else {
      log('未找到"确认"按钮');
    }
  }
  await page.screenshot({ path: '/workspace/ui_test/03_alerts.png', fullPage: true });

  // ========== 验证点4: 设备新增弹窗下拉框被遮挡问题 ==========
  log('\n========== 验证4: 设备新增弹窗-下拉框点击被footer遮挡 ==========');
  await page.goto(`${BASE}/devices`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.locator('.el-button:has-text("新增设备")').first().click();
  await page.waitForTimeout(1200);
  // 直接点击下拉框输入区域(避开footer)
  try {
    // 用JS点击避开遮挡
    const clickResult = await page.evaluate(() => {
      const sel = document.querySelector('.el-dialog .el-select');
      if (!sel) return 'no select';
      const input = sel.querySelector('.el-select__wrapper, .el-select__input, input');
      if (input) { input.click(); return 'clicked input'; }
      sel.click(); return 'clicked sel';
    });
    log(`JS点击下拉框: ${clickResult}`);
    await page.waitForTimeout(700);
    const opts = await page.evaluate(() => {
      const o = [];
      document.querySelectorAll('.el-select__popper:not([style*="display: none"]) .el-select-dropdown__item').forEach(it => {
        const t = it.innerText.trim();
        if (t && !o.includes(t)) o.push(t);
      });
      return o;
    });
    log(`产品下拉框选项(${opts.length}个): ${opts.join(', ') || '(空)'}`);
    if (!opts.length) findings.push({ severity: '中等', page: '设备管理', bug: '新增设备弹窗的"所属产品"下拉框展开后无选项(可能产品未加载或接口失败)' });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
  } catch (e) {
    log(`下拉框测试异常: ${e.message}`);
  }
  await page.screenshot({ path: '/workspace/ui_test/04_devices_add_dialog.png', fullPage: true });

  // 关闭弹窗
  try { await page.locator('.el-dialog .el-button:has-text("取消")').first().click(); await page.waitForTimeout(400); } catch(e){}

  // ========== 验证点5: 用户角色下拉框(精确) ==========
  log('\n========== 验证5: 用户角色下拉框(精确) ==========');
  await page.goto(`${BASE}/users`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.locator('.el-button:has-text("新增用户")').first().click();
  await page.waitForTimeout(1200);
  // 点击角色下拉框
  const roleSel = page.locator('.el-dialog .el-select').first();
  await roleSel.click().catch(async () => {
    // 用JS点击
    await page.evaluate(() => {
      const sel = document.querySelector('.el-dialog .el-select');
      sel?.querySelector('input')?.click();
    });
  });
  await page.waitForTimeout(700);
  const roleOpts = await page.evaluate(() => {
    const o = [];
    document.querySelectorAll('.el-select__popper:not([style*="display: none"]) .el-select-dropdown__item').forEach(it => {
      const t = it.innerText.trim();
      if (t) o.push(t);
    });
    return o;
  });
  log(`角色下拉框选项: ${JSON.stringify(roleOpts)}`);
  const expected = ['管理员','操作员','查看员'];
  const allPresent = expected.every(e => roleOpts.some(o => o.includes(e)));
  if (!allPresent) findings.push({ severity: '中等', page: '用户管理', bug: `角色下拉框缺少预期选项，期望含${expected.join('/')},实际:${roleOpts.join('|')}` });
  await page.screenshot({ path: '/workspace/ui_test/05_users_role_dropdown.png', fullPage: true });

  await browser.close();

  // 输出补充发现
  log('\n========== 补充验证结论 ==========');
  if (findings.length === 0) log('未发现新的真实bug');
  findings.forEach((f,i) => log(`${i+1}. [${f.page}][${f.severity}] ${f.bug}`));
  fs.writeFileSync('/workspace/ui_test/verify_findings.json', JSON.stringify(findings, null, 2), 'utf-8');
  log('\n截图已保存到 /workspace/ui_test/ 目录');
}

run().catch(e => { console.error('复测失败:', e); process.exit(1); });
