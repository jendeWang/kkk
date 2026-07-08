// 智慧农业IoT平台 UI自动化测试脚本
// 使用系统Chrome通过Playwright驱动
import { chromium } from 'playwright';
import fs from 'fs';

const BASE = 'http://localhost:3000';
const results = []; // 测试结果汇总
const bugs = [];     // bug汇总

function log(msg) {
  console.log(`[${new Date().toISOString().slice(11, 23)}] ${msg}`);
}

function addResult(page, item, status, detail) {
  results.push({ page, item, status, detail });
  console.log(`  [${status}] ${item}: ${detail}`);
}

function addBug(page, severity, description, detail = '') {
  bugs.push({ page, severity, description, detail });
  console.log(`  ⚠️ BUG(${severity}): ${description} ${detail}`);
}

// 收集当前页面的关键信息（替代snapshot）
async function snapshot(page, label) {
  const info = await page.evaluate(() => {
    const bodyText = document.body ? document.body.innerText.slice(0, 2000) : '(无body)';
    // 错误提示
    const errMsg = [];
    document.querySelectorAll('.el-message--error, .el-notification__title, .el-message-box__message').forEach(el => {
      const t = el.innerText && el.innerText.trim();
      if (t) errMsg.push(t);
    });
    // 空状态/空数据
    const emptyTexts = [];
    document.querySelectorAll('.el-table__empty-text, .el-empty__description, .el-empty p').forEach(el => {
      const t = el.innerText && el.innerText.trim();
      if (t) emptyTexts.push(t);
    });
    // 表格行数
    const tableRows = document.querySelectorAll('.el-table__body-wrapper tr.el-table__row').length;
    // 卡片统计
    const statCards = [];
    document.querySelectorAll('.stats-card').forEach(c => {
      const v = c.querySelector('.stats-value');
      const l = c.querySelector('.stats-label');
      if (v && l) statCards.push(`${l.innerText}:${v.innerText}`);
    });
    // 按钮文案
    const buttons = [];
    document.querySelectorAll('.el-button').forEach(b => {
      const t = b.innerText && b.innerText.trim();
      if (t && !buttons.includes(t)) buttons.push(t);
    });
    // 页面标题
    const cardTitle = document.querySelector('.el-card__header span, .el-card__header .card-header span');
    // 是否在登录页
    const isLogin = !!document.querySelector('.login-box, .login-container');
    return {
      url: location.href,
      title: document.title,
      cardTitle: cardTitle ? cardTitle.innerText.trim() : null,
      bodyTextHead: bodyText.slice(0, 300),
      errorMessages: errMsg,
      emptyTexts,
      tableRows,
      statCards,
      buttons: buttons.slice(0, 30),
      isLogin,
      bodyLen: document.body ? document.body.innerText.length : 0,
    };
  });
  console.log(`\n========== ${label} 快照 ==========`);
  console.log(`URL: ${info.url}`);
  console.log(`页面标题: ${info.title}`);
  if (info.cardTitle) console.log(`卡片标题: ${info.cardTitle}`);
  console.log(`body文本长度: ${info.bodyLen}`);
  if (info.tableRows > 0) console.log(`表格数据行数: ${info.tableRows}`);
  if (info.statCards.length) console.log(`统计卡片: ${info.statCards.join(' | ')}`);
  if (info.buttons.length) console.log(`按钮: ${info.buttons.join(', ')}`);
  if (info.errorMessages.length) console.log(`错误提示: ${info.errorMessages.join(' | ')}`);
  if (info.emptyTexts.length) console.log(`空状态文案: ${info.emptyTexts.join(' | ')}`);
  if (info.bodyTextHead) console.log(`页面文本前300字: ${info.bodyTextHead.replace(/\n/g, ' ')}`);
  return info;
}

// 收集弹窗内信息
async function snapshotDialog(page) {
  const info = await page.evaluate(() => {
    const dialog = document.querySelector('.el-dialog, .el-drawer');
    if (!dialog) return { found: false };
    const title = dialog.querySelector('.el-dialog__title, .el-drawer__title');
    const inputs = [];
    dialog.querySelectorAll('.el-form-item').forEach(item => {
      const label = item.querySelector('.el-form-item__label');
      const labelText = label ? label.innerText.trim() : '(无标签)';
      const inputEl = item.querySelector('input, textarea');
      const placeholder = inputEl ? inputEl.placeholder : '';
      inputs.push({ label: labelText, placeholder, type: inputEl ? inputEl.type : '' });
    });
    const selects = [];
    dialog.querySelectorAll('.el-select').forEach(sel => {
      const label = sel.closest('.el-form-item')?.querySelector('.el-form-item__label');
      const placeholder = sel.querySelector('.el-select__placeholder, .el-select__selected-item, input');
      selects.push({
        label: label ? label.innerText.trim() : '(无标签)',
        placeholder: placeholder ? placeholder.innerText || placeholder.placeholder : '',
      });
    });
    const switches = [];
    dialog.querySelectorAll('.el-switch').forEach(sw => {
      const label = sw.closest('.el-form-item')?.querySelector('.el-form-item__label');
      switches.push(label ? label.innerText.trim() : 'switch');
    });
    const btns = [];
    dialog.querySelectorAll('.el-button').forEach(b => {
      const t = b.innerText && b.innerText.trim();
      if (t) btns.push(t);
    });
    return {
      found: true,
      title: title ? title.innerText.trim() : '(无标题)',
      inputs,
      selects,
      switches,
      buttons: btns,
    };
  });
  console.log(`  弹窗: ${info.found ? '已打开' : '未打开'}`);
  if (info.found) {
    console.log(`  弹窗标题: ${info.title}`);
    if (info.inputs.length) console.log(`  表单项: ${info.inputs.map(i => `${i.label}[${i.placeholder||i.type}]`).join(', ')}`);
    if (info.selects.length) console.log(`  下拉框: ${info.selects.map(s => `${s.label}[${s.placeholder||''}]`).join(', ')}`);
    if (info.switches.length) console.log(`  开关: ${info.switches.join(', ')}`);
    if (info.buttons.length) console.log(`  弹窗按钮: ${info.buttons.join(', ')}`);
  }
  return info;
}

// 展开下拉框并收集选项
async function expandSelectAndCollectOptions(page, selectIndex, label) {
  try {
    // 点击指定下拉框触发器
    const triggers = await page.locator('.el-dialog .el-select, .el-drawer .el-select, .el-select').all();
    if (selectIndex >= triggers.length) {
      return { ok: false, reason: `下拉框索引${selectIndex}超出范围(共${triggers.length}个)` };
    }
    await triggers[selectIndex].click();
    await page.waitForTimeout(500);
    const options = await page.evaluate(() => {
      const opts = [];
      document.querySelectorAll('.el-select__popper .el-select-dropdown__item').forEach(item => {
        const t = item.innerText && item.innerText.trim();
        if (t && !opts.includes(t)) opts.push(t);
      });
      return opts;
    });
    // 关闭下拉
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
    return { ok: true, options };
  } catch (e) {
    return { ok: false, reason: e.message };
  }
}

// 关闭弹窗
async function closeDialog(page) {
  try {
    // 点取消按钮优先
    const cancelBtn = page.locator('.el-dialog__footer .el-button:has-text("取消"), .el-dialog .el-button:has-text("取消")').first();
    if (await cancelBtn.count()) {
      await cancelBtn.click();
    } else {
      await page.locator('.el-dialog__headerbtn').first().click();
    }
    await page.waitForTimeout(500);
  } catch (e) {
    try { await page.keyboard.press('Escape'); } catch(_) {}
  }
}

// 收集控制台错误
async function run() {
  const browser = await chromium.launch({
    headless: true,
    channel: 'chrome',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text().slice(0, 200));
  });
  page.on('pageerror', err => pageErrors.push(err.message.slice(0, 200)));

  // ===== 登录 =====
  console.log('\n################## 登录 ##################');
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1000);
  try {
    await page.fill('input[placeholder="请输入用户名"], input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"], button:has-text("登录")');
    await page.waitForTimeout(2500);
    if (page.url().includes('/login')) {
      addBug('登录', '严重', '登录失败，仍停留在登录页');
      console.log('登录失败，当前URL:', page.url());
      await browser.close();
      return;
    }
    addResult('登录', '登录', '通过', `登录成功，跳转到 ${page.url()}`);
  } catch (e) {
    addBug('登录', '严重', '登录异常', e.message);
    await browser.close();
    return;
  }

  // ===== 1. 设备管理页面 =====
  console.log('\n################## 1. 设备管理页面 (/devices) ##################');
  await page.goto(`${BASE}/devices`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(2000);
  consoleErrors.length = 0; pageErrors.length = 0;
  let snap = await snapshot(page, '设备管理-初始');
  if (snap.isLogin) { addBug('设备管理', '严重', '页面跳回登录页'); await relogin(page); }
  if (snap.bodyLen < 100) addBug('设备管理', '严重', '页面近乎空白', `body文本长度仅${snap.bodyLen}`);
  if (snap.tableRows === 0 && snap.emptyTexts.length === 0) addBug('设备管理', '中等', '设备列表为空且无空状态提示');

  // 点击新增设备
  console.log('\n--- 测试: 点击"新增设备"按钮 ---');
  try {
    const addBtn = page.locator('.el-button:has-text("新增设备")').first();
    if (await addBtn.count()) {
      await addBtn.click();
      await page.waitForTimeout(1500);
      const dlg = await snapshotDialog(page);
      if (!dlg.found) {
        addBug('设备管理', '严重', '点击"新增设备"后弹窗未打开');
      } else {
        addResult('设备管理', '新增设备弹窗', '通过', `标题=${dlg.title}, 表单项${dlg.inputs.length}个`);
        if (dlg.inputs.length === 0) addBug('设备管理', '中等', '新增设备弹窗内无表单项');
        // 检查产品选择下拉框
        if (dlg.selects.length >= 1) {
          console.log('\n--- 测试: 展开产品选择下拉框 ---');
          const r1 = await expandSelectAndCollectOptions(page, 0, '产品');
          if (r1.ok) {
            console.log(`  产品下拉选项: ${r1.options.join(', ') || '(空)'}`);
            addResult('设备管理', '产品下拉框', r1.options.length ? '通过' : '问题', `选项: ${r1.options.join(', ') || '无选项'}`);
            if (!r1.options.length) addBug('设备管理', '中等', '产品下拉框无选项(可能未创建产品或接口失败)');
          } else {
            addBug('设备管理', '中等', '产品下拉框展开失败', r1.reason);
          }
        } else {
          addBug('设备管理', '中等', '新增设备弹窗缺少产品选择下拉框');
        }
        // 检查设备分组下拉框(第二个select)
        if (dlg.selects.length >= 2) {
          console.log('\n--- 测试: 展开设备分组下拉框 ---');
          const r2 = await expandSelectAndCollectOptions(page, 1, '分组');
          if (r2.ok) {
            console.log(`  分组下拉选项: ${r2.options.join(', ') || '(空)'}`);
            addResult('设备管理', '设备分组下拉框', '通过', `选项: ${r2.options.join(', ') || '无'}`);
          }
        }
        await closeDialog(page);
      }
    } else {
      addBug('设备管理', '严重', '未找到"新增设备"按钮');
    }
  } catch (e) {
    addBug('设备管理', '严重', '测试新增设备异常', e.message);
    await closeDialog(page);
  }

  // 搜索功能
  console.log('\n--- 测试: 搜索功能 ---');
  try {
    const searchInput = page.locator('.search-bar input').first();
    if (await searchInput.count()) {
      await searchInput.fill('测试设备');
      await page.locator('.el-button:has-text("搜索")').first().click();
      await page.waitForTimeout(1500);
      addResult('设备管理', '搜索功能', '通过', '搜索已执行');
      // 重置
      const resetBtn = page.locator('.el-button:has-text("重置")').first();
      if (await resetBtn.count()) { await resetBtn.click(); await page.waitForTimeout(1000); }
    } else {
      addBug('设备管理', '中等', '未找到搜索输入框');
    }
  } catch (e) {
    addBug('设备管理', '中等', '搜索功能异常', e.message);
  }

  // 筛选下拉框
  console.log('\n--- 测试: 状态筛选下拉框 ---');
  try {
    const filterSelect = page.locator('.search-bar .el-select').first();
    if (await filterSelect.count()) {
      await filterSelect.click();
      await page.waitForTimeout(500);
      const opts = await page.evaluate(() => {
        const o = [];
        document.querySelectorAll('.el-select__popper .el-select-dropdown__item').forEach(i => { const t=i.innerText.trim(); if(t) o.push(t); });
        return o;
      });
      console.log(`  状态筛选选项: ${opts.join(', ') || '(空)'}`);
      const expected = ['在线','离线','异常'];
      const missing = expected.filter(e => !opts.some(o => o.includes(e)));
      if (missing.length) addBug('设备管理', '低', '状态筛选下拉框缺少选项', `缺少:${missing.join(',')}`);
      else addResult('设备管理', '状态筛选下拉框', '通过', `选项: ${opts.join(',')}`);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
    }
  } catch (e) {
    addBug('设备管理', '中等', '状态筛选测试异常', e.message);
  }

  // ===== 2. 告警事件页面 =====
  console.log('\n################## 2. 告警事件页面 (/alerts) ##################');
  await page.goto(`${BASE}/alerts`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(2000);
  consoleErrors.length = 0; pageErrors.length = 0;
  snap = await snapshot(page, '告警事件-初始');
  if (snap.isLogin) { addBug('告警事件', '严重', '页面跳回登录页'); await relogin(page); }
  if (snap.bodyLen < 100) addBug('告警事件', '严重', '页面近乎空白');
  if (snap.tableRows === 0 && snap.emptyTexts.length === 0) addBug('告警事件', '中等', '告警列表为空且无空状态提示');

  // 筛选下拉框
  console.log('\n--- 测试: 告警筛选下拉框 ---');
  try {
    const selects = page.locator('.el-card .el-select, .search-bar .el-select');
    const count = await selects.count();
    console.log(`  页面下拉框数量: ${count}`);
    if (count > 0) {
      await selects.first().click();
      await page.waitForTimeout(500);
      const opts = await page.evaluate(() => {
        const o = [];
        document.querySelectorAll('.el-select__popper .el-select-dropdown__item').forEach(i => { const t=i.innerText.trim(); if(t) o.push(t); });
        return o;
      });
      console.log(`  第一个筛选选项: ${opts.join(', ') || '(空)'}`);
      addResult('告警事件', '筛选下拉框', '通过', `选项: ${opts.join(',') || '无'}`);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
    } else {
      addBug('告警事件', '中等', '告警页面无筛选下拉框');
    }
  } catch (e) {
    addBug('告警事件', '中等', '筛选测试异常', e.message);
  }

  // 尝试点击确认/处理按钮
  console.log('\n--- 测试: 确认/处理告警按钮 ---');
  try {
    const confirmBtn = page.locator('.el-button:has-text("确认"), .el-button:has-text("处理"), .el-button:has-text("认领")').first();
    if (await confirmBtn.count()) {
      await confirmBtn.click();
      await page.waitForTimeout(1500);
      // 检查是否有确认对话框
      const mb = page.locator('.el-message-box, .el-dialog').first();
      if (await mb.count()) {
        const mbTitle = await mb.locator('.el-message-box__title, .el-dialog__title').first().innerText().catch(()=> '');
        console.log(`  弹出确认框: ${mbTitle}`);
        addResult('告警事件', '确认告警', '通过', `弹出确认框: ${mbTitle}`);
        // 取消
        const cancel = mb.locator('.el-button:has-text("取消")').first();
        if (await cancel.count()) await cancel.click();
        else await page.keyboard.press('Escape');
        await page.waitForTimeout(500);
      } else {
        addResult('告警事件', '确认告警', '通过', '点击后无弹窗(可能直接处理或无告警数据)');
      }
    } else {
      addResult('告警事件', '确认告警', '提示', '当前列表无"确认/处理"按钮(可能无待处理告警)');
    }
  } catch (e) {
    addBug('告警事件', '中等', '确认告警测试异常', e.message);
  }

  // 告警规则页面
  console.log('\n--- 测试: 告警规则页面 (/alert-rules) ---');
  await page.goto(`${BASE}/alert-rules`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(2000);
  const rulesSnap = await snapshot(page, '告警规则');
  if (rulesSnap.bodyLen < 100) addBug('告警规则', '严重', '告警规则页面近乎空白');
  if (rulesSnap.isLogin) { addBug('告警规则', '严重', '页面跳回登录页'); }

  // ===== 3. 场景联动页面 =====
  console.log('\n################## 3. 场景联动页面 (/scenes) ##################');
  await page.goto(`${BASE}/scenes`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(2000);
  consoleErrors.length = 0; pageErrors.length = 0;
  snap = await snapshot(page, '场景联动-初始');
  if (snap.isLogin) { addBug('场景联动', '严重', '页面跳回登录页'); await relogin(page); }
  if (snap.bodyLen < 100) addBug('场景联动', '严重', '页面近乎空白');
  if (snap.tableRows === 0 && snap.emptyTexts.length === 0) addBug('场景联动', '中等', '场景列表为空且无空状态提示');

  // 创建场景
  console.log('\n--- 测试: 点击"创建场景"按钮 ---');
  try {
    const createBtn = page.locator('.el-button:has-text("创建场景"), .el-button:has-text("新增场景"), .el-button:has-text("新建")').first();
    if (await createBtn.count()) {
      await createBtn.click();
      await page.waitForTimeout(1500);
      const dlg = await snapshotDialog(page);
      if (!dlg.found) {
        addBug('场景联动', '严重', '点击"创建场景"后弹窗未打开');
      } else {
        addResult('场景联动', '创建场景弹窗', '通过', `标题=${dlg.title}, 表单项${dlg.inputs.length}个`);
        if (dlg.inputs.length === 0) addBug('场景联动', '中等', '创建场景弹窗内无表单项');
        // 触发类型下拉框
        if (dlg.selects.length >= 1) {
          console.log('\n--- 测试: 触发类型下拉框 ---');
          const r1 = await expandSelectAndCollectOptions(page, 0, '触发类型');
          if (r1.ok) {
            console.log(`  触发类型选项: ${r1.options.join(', ') || '(空)'}`);
            addResult('场景联动', '触发类型下拉框', r1.options.length ? '通过' : '问题', `选项: ${r1.options.join(',') || '无'}`);
            if (!r1.options.length) addBug('场景联动', '中等', '触发类型下拉框无选项');
          }
        } else {
          addBug('场景联动', '中等', '创建场景弹窗缺少触发类型下拉框');
        }
        // 设备选择下拉框
        if (dlg.selects.length >= 2) {
          console.log('\n--- 测试: 设备选择下拉框 ---');
          const r2 = await expandSelectAndCollectOptions(page, 1, '设备');
          if (r2.ok) {
            console.log(`  设备选项: ${r2.options.join(', ') || '(空)'}`);
            addResult('场景联动', '设备选择下拉框', '通过', `选项: ${r2.options.join(',') || '无'}`);
          }
        }
        // 动作类型下拉框
        if (dlg.selects.length >= 3) {
          console.log('\n--- 测试: 动作类型下拉框 ---');
          const r3 = await expandSelectAndCollectOptions(page, 2, '动作类型');
          if (r3.ok) {
            console.log(`  动作类型选项: ${r3.options.join(', ') || '(空)'}`);
            addResult('场景联动', '动作类型下拉框', '通过', `选项: ${r3.options.join(',') || '无'}`);
          }
        }
        await closeDialog(page);
      }
    } else {
      addBug('场景联动', '严重', '未找到"创建场景"按钮');
    }
  } catch (e) {
    addBug('场景联动', '严重', '测试创建场景异常', e.message);
    await closeDialog(page);
  }

  // ===== 4. 系统管理-用户页面 =====
  console.log('\n################## 4. 系统管理-用户页面 (/users) ##################');
  await page.goto(`${BASE}/users`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(2000);
  consoleErrors.length = 0; pageErrors.length = 0;
  snap = await snapshot(page, '用户管理-初始');
  if (snap.isLogin) { addBug('用户管理', '严重', '页面跳回登录页'); await relogin(page); }
  if (snap.bodyLen < 100) addBug('用户管理', '严重', '页面近乎空白');
  if (snap.tableRows === 0 && snap.emptyTexts.length === 0) addBug('用户管理', '中等', '用户列表为空且无空状态提示');

  // 新增用户
  console.log('\n--- 测试: 点击"新增用户"按钮 ---');
  try {
    const addBtn = page.locator('.el-button:has-text("新增用户")').first();
    if (await addBtn.count()) {
      await addBtn.click();
      await page.waitForTimeout(1500);
      const dlg = await snapshotDialog(page);
      if (!dlg.found) {
        addBug('用户管理', '严重', '点击"新增用户"后弹窗未打开');
      } else {
        addResult('用户管理', '新增用户弹窗', '通过', `标题=${dlg.title}, 表单项${dlg.inputs.length}个`);
        // 角色选择下拉框
        if (dlg.selects.length >= 1) {
          console.log('\n--- 测试: 角色选择下拉框 ---');
          const r1 = await expandSelectAndCollectOptions(page, 0, '角色');
          if (r1.ok) {
            console.log(`  角色选项: ${r1.options.join(', ') || '(空)'}`);
            const expected = ['管理员','操作员','查看员'];
            const allPresent = expected.every(e => r1.options.some(o => o.includes(e)));
            addResult('用户管理', '角色下拉框', allPresent ? '通过' : '问题', `选项: ${r1.options.join(',')}`);
            if (!allPresent) addBug('用户管理', '中等', '角色下拉框缺少预期选项', `期望含:${expected.join('/')}, 实际:${r1.options.join(',')}`);
            if (!r1.options.length) addBug('用户管理', '严重', '角色下拉框无选项');
          } else {
            addBug('用户管理', '中等', '角色下拉框展开失败', r1.reason);
          }
        } else {
          addBug('用户管理', '中等', '新增用户弹窗缺少角色选择下拉框');
        }
        await closeDialog(page);
      }
    } else {
      addBug('用户管理', '严重', '未找到"新增用户"按钮');
    }
  } catch (e) {
    addBug('用户管理', '严重', '测试新增用户异常', e.message);
    await closeDialog(page);
  }

  // 编辑用户
  console.log('\n--- 测试: 点击"编辑"按钮 ---');
  try {
    const editBtn = page.locator('.el-button:has-text("编辑")').first();
    if (await editBtn.count()) {
      await editBtn.click();
      await page.waitForTimeout(1500);
      const dlg = await snapshotDialog(page);
      if (!dlg.found) {
        addBug('用户管理', '严重', '点击"编辑"后弹窗未打开');
      } else {
        addResult('用户管理', '编辑用户弹窗', '通过', `标题=${dlg.title}, 表单项${dlg.inputs.length}个`);
        if (dlg.title && !dlg.title.includes('编辑')) addBug('用户管理', '低', '编辑弹窗标题非"编辑用户"', `实际:${dlg.title}`);
        await closeDialog(page);
      }
    } else {
      addResult('用户管理', '编辑用户', '提示', '列表无"编辑"按钮(可能无用户数据)');
    }
  } catch (e) {
    addBug('用户管理', '中等', '测试编辑用户异常', e.message);
    await closeDialog(page);
  }

  // ===== 输出汇总 =====
  console.log('\n\n########################################################');
  console.log('################## UI测试结果汇总 ##################');
  console.log('########################################################\n');
  console.log(`共执行 ${results.length} 项检查，发现 ${bugs.length} 个Bug\n`);
  console.log('--- 检查项明细 ---');
  results.forEach((r, i) => {
    console.log(`${i+1}. [${r.page}] ${r.item} -> ${r.status}: ${r.detail}`);
  });
  if (bugs.length) {
    console.log('\n--- 发现的Bug ---');
    bugs.forEach((b, i) => {
      console.log(`${i+1}. [${b.page}][${b.severity}] ${b.description} ${b.detail ? '('+b.detail+')' : ''}`);
    });
  } else {
    console.log('\n--- 未发现明显Bug ---');
  }

  // 写入报告文件
  const report = {
    testTime: new Date().toISOString(),
    summary: { totalChecks: results.length, totalBugs: bugs.length },
    results,
    bugs,
  };
  fs.writeFileSync('/workspace/ui_test/test_report.json', JSON.stringify(report, null, 2), 'utf-8');
  console.log('\n报告已写入: /workspace/ui_test/test_report.json');

  // 截图存档
  try {
    await page.goto(`${BASE}/devices`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1500);
    await page.screenshot({ path: '/workspace/ui_test/screenshot_devices.png', fullPage: true });
  } catch (e) {}

  await browser.close();
}

async function relogin(page) {
  try {
    await page.goto(`${BASE}/login`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);
    await page.fill('input[type="text"], input[placeholder="请输入用户名"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"], button:has-text("登录")');
    await page.waitForTimeout(2500);
    console.log('  (已重新登录)');
  } catch (e) {
    console.log('  重新登录失败:', e.message);
  }
}

run().catch(e => { console.error('测试执行失败:', e); process.exit(1); });
