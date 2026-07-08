// 深度UI测试脚本 - 物模型编辑器 & 模板市场
// 使用 Playwright 模拟浏览器MCP工具操作
const { chromium } = require('playwright');
const fs = require('fs');

const BASE = 'http://localhost:3000';
const IMG_DIR = '/workspace/images/ui_test';
fs.mkdirSync(IMG_DIR, { recursive: true });

// 收集所有发现的问题
const findings = [];
const consoleErrors = [];
const pageErrors = [];

function logFind(category, severity, msg, detail) {
  const entry = { category, severity, msg, detail: detail || '' };
  findings.push(entry);
  const tag = severity === 'CRITICAL' ? '❌' : severity === 'WARN' ? '⚠️' : '✅';
  console.log(`[${category}] ${tag} ${severity}: ${msg}${detail ? ' | ' + detail : ''}`);
}

async function snap(page, name) {
  const path = `${IMG_DIR}/${name}.png`;
  await page.screenshot({ path, fullPage: false });
  console.log(`  📸 截图: ${path}`);
}

// 打印页面上可见的关键文本（模拟 snapshot 获取元素）
async function dumpText(page, label) {
  console.log(`\n===== ${label} 页面关键文本 =====`);
  try {
    const texts = await page.evaluate(() => {
      const els = document.querySelectorAll('h1,h2,h3,h4,.el-card,.el-button,.el-select,.el-tabs__item,.el-table,.el-empty,.el-tag,.el-form-item__label,.el-dialog__title,.el-dialog__body');
      return Array.from(els).slice(0, 80).map(e => ({
        tag: e.tagName + (e.className ? '.' + String(e.className).slice(0, 40) : ''),
        text: (e.innerText || '').trim().slice(0, 120).replace(/\n/g, ' ')
      })).filter(x => x.text);
    });
    texts.forEach(t => console.log(`  [${t.tag}] ${t.text}`));
    return texts;
  } catch (e) {
    console.log('  (无法获取文本: ' + e.message + ')');
    return [];
  }
}

async function listSelectOptions(page, selectorLabel, name) {
  console.log(`\n  --- 检查下拉框选项: ${selectorLabel} ---`);
  try {
    const options = await page.evaluate(() => {
      const items = document.querySelectorAll('.el-select-dropdown__item');
      return Array.from(items).map(i => (i.innerText || '').trim());
    });
    console.log(`  ${name} 选项: ${JSON.stringify(options)}`);
    return options;
  } catch (e) {
    console.log(`  (获取选项失败: ${e.message})`);
    return [];
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // 捕获控制台错误
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const txt = msg.text();
      consoleErrors.push(txt);
    }
  });
  page.on('pageerror', err => {
    pageErrors.push(err.message);
  });

  console.log('========== 第0步: 登录 ==========');
  try {
    await page.goto(`${BASE}/login`, { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1500);
    await snap(page, '01-login');

    // 输入用户名密码
    const userInput = page.locator('input[type="text"], input[placeholder*="用户"], input[name="username"]').first();
    const passInput = page.locator('input[type="password"]').first();
    await userInput.fill('admin');
    await passInput.fill('admin123');
    console.log('  输入 admin/admin123 完成');
    await snap(page, '02-login-filled');

    // 点击登录
    const loginBtn = page.locator('button:has-text("登录"), button:has-text("登 录"), button[type="submit"]').first();
    await loginBtn.click();
    await page.waitForTimeout(2500);
    await snap(page, '03-after-login');

    const url = page.url();
    console.log(`  登录后URL: ${url}`);
    if (url.includes('login')) {
      logFind('登录', 'CRITICAL', '登录失败，仍在登录页', `URL: ${url}`);
    } else {
      logFind('登录', 'PASS', '登录成功', `URL: ${url}`);
    }
  } catch (e) {
    logFind('登录', 'CRITICAL', '登录流程异常', e.message);
  }

  console.log('\n========== 第0.5步: 切换到高级模式 ==========');
  try {
    await page.waitForTimeout(500);
    // 查找"简化"文字并点击切换
    const simpleToggle = page.locator('text=简化').first();
    const toggleVisible = await simpleToggle.isVisible().catch(() => false);
    if (toggleVisible) {
      await simpleToggle.click();
      await page.waitForTimeout(1500);
      await snap(page, '04-advanced-mode');
      const advVisible = await page.locator('text=高级').first().isVisible().catch(() => false);
      logFind('模式切换', 'PASS', '点击"简化"切换模式完成', `高级可见: ${advVisible}`);
    } else {
      // 可能已经是高级模式
      const advExists = await page.locator('text=高级').first().isVisible().catch(() => false);
      logFind('模式切换', 'WARN', '未找到"简化"切换按钮', `可能已是高级模式: ${advExists}`);
    }
  } catch (e) {
    logFind('模式切换', 'WARN', '切换高级模式异常', e.message);
  }

  // ============================================================
  // 测试页面1: 物模型编辑器
  // ============================================================
  console.log('\n========== 测试页面1: 物模型编辑器 ==========');
  try {
    await page.goto(`${BASE}/thing-model`, { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(2500);
    await snap(page, '05-thing-model');
    await dumpText(page, '物模型编辑器');

    // 检查页面是否空白
    const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 500));
    if (bodyText.length < 20) {
      logFind('物模型-加载', 'CRITICAL', '页面空白，无内容显示');
    } else {
      logFind('物模型-加载', 'PASS', '页面已加载内容', `内容长度: ${bodyText.length}`);
    }
  } catch (e) {
    logFind('物模型-加载', 'CRITICAL', '导航到物模型编辑器失败', e.message);
  }

  // 检查产品选择下拉框
  console.log('\n---------- 1.1 检查产品选择下拉框 ----------');
  let productOptions = [];
  try {
    const productSelect = page.locator('.el-select').first();
    const psVisible = await productSelect.isVisible().catch(() => false);
    if (psVisible) {
      await productSelect.click();
      await page.waitForTimeout(800);
      await snap(page, '06-product-dropdown');
      productOptions = await listSelectOptions(page, '产品下拉', '产品');
      await page.waitForTimeout(300);
      if (productOptions.length === 0) {
        logFind('物模型-产品下拉', 'CRITICAL', '产品下拉框无选项', '');
      } else if (productOptions.length < 4) {
        logFind('物模型-产品下拉', 'WARN', `产品数量不足，仅${productOptions.length}个`, JSON.stringify(productOptions));
      } else {
        logFind('物模型-产品下拉', 'PASS', `产品下拉有${productOptions.length}个选项`, JSON.stringify(productOptions));
      }
    } else {
      logFind('物模型-产品下拉', 'CRITICAL', '未找到产品选择下拉框');
    }
  } catch (e) {
    logFind('物模型-产品下拉', 'WARN', '检查产品下拉异常', e.message);
  }

  // 选择第一个产品
  console.log('\n---------- 1.2 选择产品并加载数据 ----------');
  try {
    if (productOptions.length > 0) {
      // 点击第一个选项
      const firstOpt = page.locator('.el-select-dropdown__item').first();
      await firstOpt.click();
      await page.waitForTimeout(2000);
      await snap(page, '07-product-selected');
      await dumpText(page, '选择产品后');

      // 检查属性/服务/事件标签页
      const tabs = await page.locator('.el-tabs__item').allTextContents();
      console.log(`  标签页: ${JSON.stringify(tabs)}`);
      const hasProps = tabs.some(t => t.includes('属性'));
      const hasSvc = tabs.some(t => t.includes('服务'));
      const hasEvt = tabs.some(t => t.includes('事件'));
      logFind('物模型-标签页', hasProps && hasSvc && hasEvt ? 'PASS' : 'WARN', '标签页检查', `属性:${hasProps} 服务:${hasSvc} 事件:${hasEvt}`);

      // 检查属性列表是否显示
      const tableRows = await page.locator('.el-table__row').count();
      const emptyText = await page.locator('.el-empty__description').first().textContent().catch(() => '');
      if (tableRows > 0) {
        logFind('物模型-属性列表', 'PASS', `属性列表显示${tableRows}条数据`);
      } else if (emptyText) {
        logFind('物模型-属性列表', 'WARN', '属性列表为空', emptyText);
      } else {
        logFind('物模型-属性列表', 'WARN', '未检测到属性数据行');
      }
    } else {
      logFind('物模型-选择产品', 'WARN', '无产品可选，跳过');
    }
  } catch (e) {
    logFind('物模型-选择产品', 'WARN', '选择产品异常', e.message);
  }

  // 检查"属性"标签页 - 新增属性弹窗
  console.log('\n---------- 1.3 检查新增属性弹窗 ----------');
  try {
    // 关闭可能打开的下拉
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(500);
    // 点击属性标签页确保在属性
    const propTab = page.locator('.el-tabs__item:has-text("属性")').first();
    if (await propTab.isVisible().catch(() => false)) {
      await propTab.click();
      await page.waitForTimeout(800);
    }

    const addBtn = page.locator('button:has-text("新增属性"), button:has-text("添加属性"), button:has-text("新增"), button:has-text("添加")').first();
    const addVisible = await addBtn.isVisible().catch(() => false);
    if (addVisible) {
      await addBtn.click();
      await page.waitForTimeout(1500);
      await snap(page, '08-add-property-dialog');
      await dumpText(page, '新增属性弹窗');

      const dialogVisible = await page.locator('.el-dialog').first().isVisible().catch(() => false);
      if (!dialogVisible) {
        logFind('物模型-新增属性弹窗', 'CRITICAL', '点击新增属性后未弹出对话框');
      } else {
        logFind('物模型-新增属性弹窗', 'PASS', '新增属性弹窗已显示');

        // 检查数据类型下拉框选项
        const dataTypeSel = page.locator('.el-dialog .el-select').nth(0);
        if (await dataTypeSel.isVisible().catch(() => false)) {
          await dataTypeSel.click();
          await page.waitForTimeout(600);
          const dtOpts = await listSelectOptions(page, '数据类型', '数据类型');
          const expectedTypes = ['float', 'int', 'bool', 'string'];
          const found = expectedTypes.filter(t => dtOpts.some(o => o.toLowerCase().includes(t)));
          logFind('物模型-数据类型下拉', found.length >= 3 ? 'PASS' : 'WARN',
            `数据类型选项: ${found.length}/${expectedTypes.length}匹配`, JSON.stringify(dtOpts));
          await page.keyboard.press('Escape').catch(() => {});
          await page.waitForTimeout(300);
        }

        // 检查访问类型下拉框选项
        const accessSel = page.locator('.el-dialog .el-select').nth(1);
        if (await accessSel.isVisible().catch(() => false)) {
          await accessSel.click();
          await page.waitForTimeout(600);
          const acOpts = await listSelectOptions(page, '访问类型', '访问类型');
          const hasRW = acOpts.some(o => o.includes('读写') || o.includes('rw'));
          const hasRO = acOpts.some(o => o.includes('只读') || o.includes('read'));
          logFind('物模型-访问类型下拉', hasRW && hasRO ? 'PASS' : 'WARN',
            '访问类型选项检查', JSON.stringify(acOpts));
          await page.keyboard.press('Escape').catch(() => {});
          await page.waitForTimeout(300);
        }

        // 关闭弹窗
        const cancelBtn = page.locator('.el-dialog button:has-text("取消"), .el-dialog button:has-text("关闭"), .el-dialog__headerbtn').first();
        if (await cancelBtn.isVisible().catch(() => false)) {
          await cancelBtn.click();
          await page.waitForTimeout(800);
          const stillVisible = await page.locator('.el-dialog').first().isVisible().catch(() => false);
          logFind('物模型-关闭弹窗', !stillVisible ? 'PASS' : 'WARN', '关闭弹窗', stillVisible ? '弹窗仍可见' : '已关闭');
        }
      }
    } else {
      logFind('物模型-新增属性', 'CRITICAL', '未找到"新增属性"按钮');
    }
  } catch (e) {
    logFind('物模型-新增属性', 'WARN', '检查新增属性弹窗异常', e.message);
  }

  // 检查"服务"标签页
  console.log('\n---------- 1.4 检查服务标签页 ----------');
  try {
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(500);
    const svcTab = page.locator('.el-tabs__item:has-text("服务")').first();
    if (await svcTab.isVisible().catch(() => false)) {
      await svcTab.click();
      await page.waitForTimeout(1500);
      await snap(page, '09-services-tab');
      await dumpText(page, '服务标签页');

      const svcRows = await page.locator('.el-table__row').count();
      logFind('物模型-服务列表', 'PASS', `服务标签页加载，${svcRows}条数据`);

      // 新增服务按钮
      const addSvcBtn = page.locator('button:has-text("新增服务"), button:has-text("添加服务"), button:has-text("新增")').first();
      if (await addSvcBtn.isVisible().catch(() => false)) {
        await addSvcBtn.click();
        await page.waitForTimeout(1500);
        await snap(page, '10-add-service-dialog');
        const dlgVis = await page.locator('.el-dialog').first().isVisible().catch(() => false);
        logFind('物模型-新增服务弹窗', dlgVis ? 'PASS' : 'CRITICAL', dlgVis ? '新增服务弹窗已显示' : '未弹出服务弹窗');
        await page.keyboard.press('Escape').catch(() => {});
        await page.waitForTimeout(800);
        const closeBtn = page.locator('.el-dialog__headerbtn, .el-dialog button:has-text("取消")').first();
        if (await closeBtn.isVisible().catch(() => false)) { await closeBtn.click(); await page.waitForTimeout(500); }
      } else {
        logFind('物模型-新增服务', 'WARN', '未找到"新增服务"按钮');
      }
    } else {
      logFind('物模型-服务标签页', 'CRITICAL', '未找到"服务"标签页');
    }
  } catch (e) {
    logFind('物模型-服务标签页', 'WARN', '检查服务标签页异常', e.message);
  }

  // 检查"事件"标签页
  console.log('\n---------- 1.5 检查事件标签页 ----------');
  try {
    const evtTab = page.locator('.el-tabs__item:has-text("事件")').first();
    if (await evtTab.isVisible().catch(() => false)) {
      await evtTab.click();
      await page.waitForTimeout(1500);
      await snap(page, '11-events-tab');
      await dumpText(page, '事件标签页');

      const evtRows = await page.locator('.el-table__row').count();
      logFind('物模型-事件列表', 'PASS', `事件标签页加载，${evtRows}条数据`);

      const addEvtBtn = page.locator('button:has-text("新增事件"), button:has-text("添加事件"), button:has-text("新增")').first();
      if (await addEvtBtn.isVisible().catch(() => false)) {
        await addEvtBtn.click();
        await page.waitForTimeout(1500);
        await snap(page, '12-add-event-dialog');
        const dlgVis = await page.locator('.el-dialog').first().isVisible().catch(() => false);
        logFind('物模型-新增事件弹窗', dlgVis ? 'PASS' : 'CRITICAL', dlgVis ? '新增事件弹窗已显示' : '未弹出事件弹窗');
        await page.keyboard.press('Escape').catch(() => {});
        await page.waitForTimeout(500);
        const closeBtn = page.locator('.el-dialog__headerbtn, .el-dialog button:has-text("取消")').first();
        if (await closeBtn.isVisible().catch(() => false)) { await closeBtn.click(); await page.waitForTimeout(500); }
      } else {
        logFind('物模型-新增事件', 'WARN', '未找到"新增事件"按钮');
      }
    } else {
      logFind('物模型-事件标签页', 'CRITICAL', '未找到"事件"标签页');
    }
  } catch (e) {
    logFind('物模型-事件标签页', 'WARN', '检查事件标签页异常', e.message);
  }

  // 测试快捷添加功能
  console.log('\n---------- 1.6 测试快捷添加温度功能 ----------');
  try {
    // 切回属性标签页
    const propTab = page.locator('.el-tabs__item:has-text("属性")').first();
    if (await propTab.isVisible().catch(() => false)) {
      await propTab.click();
      await page.waitForTimeout(1000);
    }
    // 查找温度快捷添加按钮
    const tempBtn = page.locator('button:has-text("温度"), .quick-add:has-text("温度"), [class*="quick"] button:has-text("温度")').first();
    const tempVisible = await tempBtn.isVisible().catch(() => false);
    if (tempVisible) {
      const beforeRows = await page.locator('.el-table__row').count();
      await tempBtn.click();
      await page.waitForTimeout(2000);
      await snap(page, '13-quick-add-temp');
      const afterRows = await page.locator('.el-table__row').count();
      if (afterRows > beforeRows) {
        logFind('物模型-快捷添加温度', 'PASS', `温度属性已添加，行数${beforeRows}->${afterRows}`);
      } else {
        // 可能弹出确认或对话框
        const dlgVis = await page.locator('.el-message, .el-notification, .el-dialog').first().isVisible().catch(() => false);
        logFind('物模型-快捷添加温度', 'WARN', `点击后行数未增加(${beforeRows}==${afterRows})`, dlgVis ? '有提示弹出' : '无提示');
      }
    } else {
      logFind('物模型-快捷添加温度', 'WARN', '未找到温度快捷添加按钮');
    }
  } catch (e) {
    logFind('物模型-快捷添加温度', 'WARN', '快捷添加温度异常', e.message);
  }

  // 测试删除功能
  console.log('\n---------- 1.7 测试删除属性功能 ----------');
  try {
    const deleteBtn = page.locator('.el-table button:has-text("删除"), .el-table [class*="delete"], .el-table .el-button--danger').first();
    const delVisible = await deleteBtn.isVisible().catch(() => false);
    if (delVisible) {
      await deleteBtn.click();
      await page.waitForTimeout(1000);
      await snap(page, '14-delete-confirm');
      const confirmBox = await page.locator('.el-message-box, .el-popconfirm, .el-dialog:has-text("确认"), .el-dialog:has-text("确定")').first().isVisible().catch(() => false);
      logFind('物模型-删除确认', confirmBox ? 'PASS' : 'WARN', confirmBox ? '删除确认对话框已弹出' : '未弹出确认对话框');
      // 取消删除避免影响后续
      const cancel = page.locator('.el-message-box button:has-text("取消"), .el-popconfirm button:has-text("取消"), .el-dialog button:has-text("取消")').first();
      if (await cancel.isVisible().catch(() => false)) {
        await cancel.click();
        await page.waitForTimeout(500);
      } else {
        await page.keyboard.press('Escape').catch(() => {});
      }
    } else {
      logFind('物模型-删除功能', 'WARN', '未找到删除按钮（可能无数据行）');
    }
  } catch (e) {
    logFind('物模型-删除功能', 'WARN', '测试删除功能异常', e.message);
  }

  // 控制台错误检查（物模型）
  console.log('\n---------- 1.8 物模型控制台错误检查 ----------');
  const tmConsoleErrs = consoleErrors.filter(e => !consoleErrors.indexOf(e) < 0).slice(-20);
  if (consoleErrors.length > 0) {
    logFind('物模型-控制台', 'WARN', `发现${consoleErrors.length}条控制台错误`, consoleErrors.slice(-5).join(' | ').slice(0, 300));
  } else {
    logFind('物模型-控制台', 'PASS', '无控制台错误');
  }
  if (pageErrors.length > 0) {
    logFind('物模型-页面错误', 'CRITICAL', `发现${pageErrors.length}条页面JS错误`, pageErrors.slice(-3).join(' | ').slice(0, 300));
  }

  // ============================================================
  // 测试页面2: 模板市场
  // ============================================================
  console.log('\n========== 测试页面2: 模板市场 ==========');
  // 清空之前的控制台错误计数，单独记录模板市场
  const tmErrCount = consoleErrors.length;
  const tmPageErrCount = pageErrors.length;

  try {
    await page.goto(`${BASE}/template-market`, { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(2500);
    await snap(page, '15-template-market');
    await dumpText(page, '模板市场');

    const bodyText2 = await page.evaluate(() => document.body.innerText.slice(0, 500));
    if (bodyText2.length < 20) {
      logFind('模板市场-加载', 'CRITICAL', '页面空白，无内容显示');
    } else {
      logFind('模板市场-加载', 'PASS', '页面已加载内容', `内容长度: ${bodyText2.length}`);
    }

    // 检查模板卡片
    const cards = await page.locator('.el-card').count();
    console.log(`  模板卡片数量: ${cards}`);
    if (cards === 0) {
      logFind('模板市场-卡片', 'CRITICAL', '未找到任何模板卡片');
    } else if (cards < 4) {
      logFind('模板市场-卡片', 'WARN', `模板卡片数量不足，仅${cards}个`, `预期4个`);
    } else {
      logFind('模板市场-卡片', 'PASS', `找到${cards}个模板卡片`);
    }

    // 检查卡片内容文本
    const cardTexts = await page.locator('.el-card').allTextContents();
    const hasGreenhouse = cardTexts.some(t => t.includes('大棚'));
    const hasBreeding = cardTexts.some(t => t.includes('养殖') || t.includes('畜牧'));
    logFind('模板市场-卡片内容', hasGreenhouse && hasBreeding ? 'PASS' : 'WARN',
      '模板类型检查', `大棚:${hasGreenhouse} 养殖:${hasBreeding}`);
  } catch (e) {
    logFind('模板市场-加载', 'CRITICAL', '导航到模板市场失败', e.message);
  }

  // 测试分类筛选下拉框
  console.log('\n---------- 2.1 测试分类筛选下拉框 ----------');
  let categoryOptions = [];
  try {
    // 查找分类筛选下拉
    const categorySelect = page.locator('.el-select').first();
    if (await categorySelect.isVisible().catch(() => false)) {
      await categorySelect.click();
      await page.waitForTimeout(800);
      await snap(page, '16-category-filter');
      categoryOptions = await listSelectOptions(page, '分类筛选', '分类');
      await page.waitForTimeout(300);

      const hasAgri = categoryOptions.some(o => o.includes('农业'));
      const hasLivestock = categoryOptions.some(o => o.includes('畜牧') || o.includes('养殖'));
      logFind('模板市场-分类筛选', hasAgri && hasLivestock ? 'PASS' : 'WARN',
        '分类选项检查', JSON.stringify(categoryOptions));

      // 选择"农业"筛选
      const agriOpt = page.locator('.el-select-dropdown__item:has-text("农业")').first();
      if (await agriOpt.isVisible().catch(() => false)) {
        await agriOpt.click();
        await page.waitForTimeout(1500);
        await snap(page, '17-after-agri-filter');
        const filteredCards = await page.locator('.el-card').count();
        logFind('模板市场-农业筛选', 'PASS', `筛选后显示${filteredCards}个卡片`);
      }
    } else {
      logFind('模板市场-分类筛选', 'WARN', '未找到分类筛选下拉框');
    }
  } catch (e) {
    logFind('模板市场-分类筛选', 'WARN', '测试分类筛选异常', e.message);
  }

  // 测试级别筛选下拉框
  console.log('\n---------- 2.2 测试级别筛选下拉框 ----------');
  try {
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(500);
    const levelSelect = page.locator('.el-select').nth(1);
    if (await levelSelect.isVisible().catch(() => false)) {
      await levelSelect.click();
      await page.waitForTimeout(800);
      await snap(page, '18-level-filter');
      const levelOpts = await listSelectOptions(page, '级别筛选', '级别');
      await page.waitForTimeout(300);

      const hasBeginner = levelOpts.some(o => o.includes('入门'));
      const hasRecommended = levelOpts.some(o => o.includes('推荐'));
      const hasProfessional = levelOpts.some(o => o.includes('专业'));
      logFind('模板市场-级别筛选', hasBeginner && hasRecommended && hasProfessional ? 'PASS' : 'WARN',
        '级别选项检查', JSON.stringify(levelOpts));

      // 选择"推荐"筛选
      const recOpt = page.locator('.el-select-dropdown__item:has-text("推荐")').first();
      if (await recOpt.isVisible().catch(() => false)) {
        await recOpt.click();
        await page.waitForTimeout(1500);
        await snap(page, '19-after-level-filter');
        const filteredCards2 = await page.locator('.el-card').count();
        logFind('模板市场-推荐筛选', 'PASS', `级别筛选后显示${filteredCards2}个卡片`);
      }
    } else {
      logFind('模板市场-级别筛选', 'WARN', '未找到级别筛选下拉框');
    }
  } catch (e) {
    logFind('模板市场-级别筛选', 'WARN', '测试级别筛选异常', e.message);
  }

  // 测试模板详情预览
  console.log('\n---------- 2.3 测试模板详情预览 ----------');
  try {
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(500);
    // 重新导航到模板市场重置筛选
    await page.goto(`${BASE}/template-market`, { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(2000);

    const previewBtn = page.locator('button:has-text("预览"), button:has-text("预览物模型"), [class*="preview"], button:has-text("查看")').first();
    if (await previewBtn.isVisible().catch(() => false)) {
      await previewBtn.click();
      await page.waitForTimeout(2000);
      await snap(page, '20-template-preview');
      await dumpText(page, '模板预览弹窗');

      const dlgVis = await page.locator('.el-dialog').first().isVisible().catch(() => false);
      if (dlgVis) {
        // 检查预览内容是否包含物模型信息
        const dlgText = await page.locator('.el-dialog').first().textContent().catch(() => '');
        const hasProps = dlgText.includes('属性') || dlgText.includes('property');
        const hasSvc = dlgText.includes('服务') || dlgText.includes('service');
        const hasEvt = dlgText.includes('事件') || dlgText.includes('event');
        logFind('模板市场-预览', 'PASS', '预览弹窗已显示', `属性:${hasProps} 服务:${hasSvc} 事件:${hasEvt}`);

        // 关闭弹窗
        const closeBtn = page.locator('.el-dialog__headerbtn').first();
        if (await closeBtn.isVisible().catch(() => false)) {
          await closeBtn.click();
          await page.waitForTimeout(800);
        }
      } else {
        logFind('模板市场-预览', 'CRITICAL', '点击预览后未弹出对话框');
      }
    } else {
      logFind('模板市场-预览', 'WARN', '未找到"预览物模型"按钮');
    }
  } catch (e) {
    logFind('模板市场-预览', 'WARN', '测试模板预览异常', e.message);
  }

  // 测试"使用模板"按钮
  console.log('\n---------- 2.4 测试"使用模板"按钮 ----------');
  try {
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(500);
    const useBtn = page.locator('button:has-text("使用模板"), button:has-text("使用"), button:has-text("创建"), button:has-text("应用")').first();
    if (await useBtn.isVisible().catch(() => false)) {
      const urlBefore = page.url();
      await useBtn.click();
      await page.waitForTimeout(3000);
      await snap(page, '21-after-use-template');
      const urlAfter = page.url();
      console.log(`  使用模板前URL: ${urlBefore}`);
      console.log(`  使用模板后URL: ${urlAfter}`);

      // 检查是否跳转到产品管理
      if (urlAfter.includes('product') || urlAfter !== urlBefore) {
        logFind('模板市场-使用模板', 'PASS', '使用模板后页面跳转', urlAfter);
      } else {
        // 可能弹出了成功提示
        const msg = await page.locator('.el-message--success, .el-notification').first().isVisible().catch(() => false);
        if (msg) {
          logFind('模板市场-使用模板', 'PASS', '使用模板成功（有成功提示）');
        } else {
          logFind('模板市场-使用模板', 'WARN', '点击使用模板后无明显跳转或提示', `URL: ${urlAfter}`);
        }
      }
    } else {
      logFind('模板市场-使用模板', 'WARN', '未找到"使用模板"按钮');
    }
  } catch (e) {
    logFind('模板市场-使用模板', 'WARN', '测试使用模板异常', e.message);
  }

  // 控制台错误检查（模板市场）
  console.log('\n---------- 2.5 模板市场控制台错误检查 ----------');
  const newConsoleErrs = consoleErrors.slice(tmErrCount);
  const newPageErrs = pageErrors.slice(tmPageErrCount);
  if (newConsoleErrs.length > 0) {
    logFind('模板市场-控制台', 'WARN', `发现${newConsoleErrs.length}条控制台错误`, newConsoleErrs.slice(-5).join(' | ').slice(0, 300));
  } else {
    logFind('模板市场-控制台', 'PASS', '无控制台错误');
  }
  if (newPageErrs.length > 0) {
    logFind('模板市场-页面错误', 'CRITICAL', `发现${newPageErrs.length}条页面JS错误`, newPageErrs.slice(-3).join(' | ').slice(0, 300));
  }

  await browser.close();

  // 输出汇总
  console.log('\n\n========================================');
  console.log('========== 测试结果汇总 ==========');
  console.log('========================================');
  const pass = findings.filter(f => f.severity === 'PASS').length;
  const warn = findings.filter(f => f.severity === 'WARN').length;
  const crit = findings.filter(f => f.severity === 'CRITICAL').length;
  console.log(`\n通过: ${pass} | 警告: ${warn} | 严重: ${crit} | 总计: ${findings.length}\n`);

  console.log('--- CRITICAL 问题 ---');
  findings.filter(f => f.severity === 'CRITICAL').forEach((f, i) => {
    console.log(`  [C${i + 1}] ${f.category}: ${f.msg}${f.detail ? ' | ' + f.detail : ''}`);
  });
  console.log('\n--- WARN 问题 ---');
  findings.filter(f => f.severity === 'WARN').forEach((f, i) => {
    console.log(`  [W${i + 1}] ${f.category}: ${f.msg}${f.detail ? ' | ' + f.detail : ''}`);
  });
  console.log('\n--- PASS 项目 ---');
  findings.filter(f => f.severity === 'PASS').forEach((f, i) => {
    console.log(`  [P${i + 1}] ${f.category}: ${f.msg}`);
  });

  // 写入JSON结果
  fs.writeFileSync('/workspace/ui_test_result.json', JSON.stringify({
    summary: { pass, warn, critical: crit, total: findings.length },
    findings,
    consoleErrors: consoleErrors.slice(-30),
    pageErrors: pageErrors.slice(-10)
  }, null, 2));
  console.log('\n结果已保存到 /workspace/ui_test_result.json');
})();
