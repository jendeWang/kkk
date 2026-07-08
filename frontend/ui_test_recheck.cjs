// 精确复测脚本 - 验证疑似误报的问题
const { chromium } = require('playwright');
const fs = require('fs');

const BASE = 'http://localhost:3000';
const IMG_DIR = '/workspace/images/ui_test';
fs.mkdirSync(IMG_DIR, { recursive: true });

const findings = [];
function log(cat, sev, msg, detail) {
  findings.push({ cat, sev, msg, detail: detail || '' });
  const tag = sev === 'CRITICAL' ? '❌' : sev === 'WARN' ? '⚠️' : '✅';
  console.log(`[${cat}] ${tag} ${sev}: ${msg}${detail ? ' | ' + detail : ''}`);
}
async function snap(page, name) {
  await page.screenshot({ path: `${IMG_DIR}/${name}.png`, fullPage: false });
  console.log(`  📸 ${name}`);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // 登录
  console.log('===== 登录 =====');
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(1500);
  await page.locator('input[type="text"], input[placeholder*="用户"]').first().fill('admin');
  await page.locator('input[type="password"]').first().fill('admin123');
  await page.locator('button:has-text("登录"), button[type="submit"]').first().click();
  await page.waitForTimeout(2500);
  // 切换高级模式
  const simple = page.locator('text=简化').first();
  if (await simple.isVisible().catch(() => false)) { await simple.click(); await page.waitForTimeout(1500); }
  console.log('登录完成, URL:', page.url());

  // ============ 物模型编辑器精确复测 ============
  console.log('\n===== 物模型编辑器精确复测 =====');
  await page.goto(`${BASE}/thing-model`, { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(2000);

  // 1. 属性列表卡片（用正确选择器 .model-card）
  console.log('\n--- R1: 属性列表用 .model-card ---');
  // 先选第一个产品
  await page.locator('.el-select').first().click();
  await page.waitForTimeout(800);
  const prods = await page.locator('.el-select-dropdown__item').allTextContents();
  console.log('  产品列表:', prods);
  await page.locator('.el-select-dropdown__item').first().click();
  await page.waitForTimeout(2000);
  await snap(page, 'R01-product-selected');

  // 切到属性标签
  await page.locator('.el-tabs__item:has-text("属性")').first().click();
  await page.waitForTimeout(1000);

  const propCards = await page.locator('.model-card.prop-card, .model-card:has(.card-name)').count();
  console.log('  .model-card 数量:', propCards);
  log('物模型-属性列表(复测)', propCards > 0 ? 'PASS' : 'WARN', `属性卡片正确显示${propCards}个`, '使用.model-card选择器');

  // 2. 服务弹窗 - 用标题精确检测
  console.log('\n--- R2: 服务弹窗（按标题检测）---');
  await page.locator('.el-tabs__item:has-text("服务")').first().click();
  await page.waitForTimeout(1000);
  // 确保无残留弹窗
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(800);

  // 检测点击前无"添加服务"标题弹窗可见
  const svcDlgBefore = await page.locator('.el-dialog:has(.el-dialog__title:has-text("添加服务"))').isVisible().catch(() => false);
  console.log('  点击前 添加服务弹窗可见:', svcDlgBefore);

  await page.locator('button:has-text("添加服务")').first().click();
  await page.waitForTimeout(1500);
  await snap(page, 'R02-service-dialog');

  // 用标题精确匹配
  const svcDlgAfter = await page.locator('.el-dialog:has(.el-dialog__title:has-text("添加服务"))').isVisible().catch(() => false);
  const svcTitleText = await page.locator('.el-dialog__title:has-text("添加服务")').first().textContent().catch(() => '');
  console.log('  点击后 添加服务弹窗可见:', svcDlgAfter, '| 标题:', svcTitleText);
  log('物模型-新增服务弹窗(复测)', svcDlgAfter ? 'PASS' : 'CRITICAL',
    svcDlgAfter ? '添加服务弹窗正确弹出' : '点击添加服务后弹窗未显示', '');

  // 检查服务弹窗表单内容
  if (svcDlgAfter) {
    const svcBody = await page.locator('.el-dialog:has(.el-dialog__title:has-text("添加服务")) .el-dialog__body').first().textContent().catch(() => '');
    const hasInputParams = svcBody.includes('输入参数');
    const hasOutputParams = svcBody.includes('输出参数');
    console.log('  服务弹窗表单: 输入参数:', hasInputParams, '输出参数:', hasOutputParams);
    log('物模型-服务弹窗表单', hasInputParams && hasOutputParams ? 'PASS' : 'WARN', '服务弹窗表单检查', `输入:${hasInputParams} 输出:${hasOutputParams}`);
  }
  // 关闭
  await page.locator('.el-dialog:has(.el-dialog__title:has-text("添加服务")) .el-dialog__headerbtn').first().click().catch(() => {});
  await page.waitForTimeout(800);

  // 3. 事件弹窗 - 用标题精确检测
  console.log('\n--- R3: 事件弹窗（按标题检测）---');
  await page.locator('.el-tabs__item:has-text("事件")').first().click();
  await page.waitForTimeout(1000);
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(800);

  await page.locator('button:has-text("添加事件")').first().click();
  await page.waitForTimeout(1500);
  await snap(page, 'R03-event-dialog');

  const evtDlg = await page.locator('.el-dialog:has(.el-dialog__title:has-text("添加事件"))').isVisible().catch(() => false);
  const evtTitleText = await page.locator('.el-dialog__title:has-text("添加事件")').first().textContent().catch(() => '');
  console.log('  点击后 添加事件弹窗可见:', evtDlg, '| 标题:', evtTitleText);
  log('物模型-新增事件弹窗(复测)', evtDlg ? 'PASS' : 'CRITICAL',
    evtDlg ? '添加事件弹窗正确弹出' : '点击添加事件后弹窗未显示', '');

  if (evtDlg) {
    const evtBody = await page.locator('.el-dialog:has(.el-dialog__title:has-text("添加事件")) .el-dialog__body').first().textContent().catch(() => '');
    const hasEventType = evtBody.includes('事件类型');
    const hasOutputParams = evtBody.includes('输出参数');
    console.log('  事件弹窗表单: 事件类型:', hasEventType, '输出参数:', hasOutputParams);
    log('物模型-事件弹窗表单', hasEventType ? 'PASS' : 'WARN', '事件弹窗表单检查', `事件类型:${hasEventType} 输出:${hasOutputParams}`);

    // 检查事件类型下拉选项
    const evtTypeSel = page.locator('.el-dialog:has(.el-dialog__title:has-text("添加事件")) .el-select').first();
    if (await evtTypeSel.isVisible().catch(() => false)) {
      await evtTypeSel.click();
      await page.waitForTimeout(600);
      const evtTypeOpts = await page.locator('.el-select-dropdown:visible .el-select-dropdown__item').allTextContents().catch(() => []);
      console.log('  事件类型选项:', evtTypeOpts);
      log('物模型-事件类型下拉', evtTypeOpts.length >= 3 ? 'PASS' : 'WARN', `事件类型选项${evtTypeOpts.length}个`, JSON.stringify(evtTypeOpts));
      await page.keyboard.press('Escape').catch(() => {});
      await page.waitForTimeout(300);
    }
  }
  // 关闭
  await page.locator('.el-dialog:has(.el-dialog__title:has-text("添加事件")) .el-dialog__headerbtn').first().click().catch(() => {});
  await page.waitForTimeout(800);

  // 4. 快捷添加温度 - 用正确选择器 .quick-add-item
  console.log('\n--- R4: 快捷添加温度（用 .quick-add-item）---');
  await page.locator('.el-tabs__item:has-text("属性")').first().click();
  await page.waitForTimeout(1000);

  const tempQuick = page.locator('.quick-add-item:has-text("温度")').first();
  const tempVisible = await tempQuick.isVisible().catch(() => false);
  console.log('  温度快捷添加项可见:', tempVisible);
  if (tempVisible) {
    const before = await page.locator('.model-card.prop-card, .model-card:has(.card-name)').count();
    console.log('  点击前属性卡片数:', before);
    await tempQuick.click();
    await page.waitForTimeout(2000);
    await snap(page, 'R04-quick-add-temp');
    const after = await page.locator('.model-card.prop-card, .model-card:has(.card-name)').count();
    console.log('  点击后属性卡片数:', after);

    // 检查是否出现新卡片含"温度"
    const tempCardExists = await page.locator('.model-card .card-name:has-text("温度")').first().isVisible().catch(() => false);
    const successMsg = await page.locator('.el-message--success').first().isVisible().catch(() => false);
    if (after > before || tempCardExists) {
      log('物模型-快捷添加温度(复测)', 'PASS', `温度属性已添加`, `卡片数${before}->${after}, 温度卡片:${tempCardExists}`);
    } else if (successMsg) {
      log('物模型-快捷添加温度(复测)', 'PASS', '温度添加成功（有成功提示）', '');
    } else {
      // 检查是否有错误提示
      const errMsg = await page.locator('.el-message--error').first().isVisible().catch(() => false);
      const msgText = await page.locator('.el-message').first().textContent().catch(() => '');
      log('物模型-快捷添加温度(复测)', errMsg ? 'WARN' : 'WARN', '点击后未明显增加', `错误提示:${errMsg} 消息:${msgText.slice(0,80)}`);
    }
  } else {
    log('物模型-快捷添加温度(复测)', 'WARN', '未找到温度快捷添加项', '');
  }

  // 5. 删除确认 - 用 .model-card 内的删除按钮
  console.log('\n--- R5: 删除属性确认对话框 ---');
  // 找一个属性卡片的删除按钮
  const delBtn = page.locator('.model-card .el-button--danger:has-text("删除")').first();
  const delVisible = await delBtn.isVisible().catch(() => false);
  console.log('  删除按钮可见:', delVisible);
  if (delVisible) {
    const beforeDel = await page.locator('.model-card.prop-card, .model-card:has(.card-name)').count();
    await delBtn.click();
    await page.waitForTimeout(1500);
    await snap(page, 'R05-delete-confirm');

    // Element Plus 删除可能用 ElMessageBox.confirm
    const msgBox = await page.locator('.el-message-box').first().isVisible().catch(() => false);
    const confirmDlg = await page.locator('.el-dialog:has-text("确认"), .el-dialog:has-text("确定删除"), .el-dialog:has-text("删除")').first().isVisible().catch(() => false);
    const msgBoxText = await page.locator('.el-message-box__message').first().textContent().catch(() => '');
    console.log('  ElMessageBox可见:', msgBox, '| 内容:', msgBoxText.slice(0, 80));
    console.log('  确认对话框可见:', confirmDlg);

    if (msgBox || confirmDlg) {
      log('物模型-删除确认(复测)', 'PASS', '删除确认对话框已弹出', msgBoxText.slice(0, 80));
      // 取消删除
      const cancelBtn = page.locator('.el-message-box button:has-text("取消")').first();
      if (await cancelBtn.isVisible().catch(() => false)) {
        await cancelBtn.click();
        await page.waitForTimeout(800);
      } else {
        await page.keyboard.press('Escape').catch(() => {});
        await page.waitForTimeout(500);
      }
    } else {
      // 可能直接删除了
      const afterDel = await page.locator('.model-card.prop-card, .model-card:has(.card-name)').count();
      if (afterDel < beforeDel) {
        log('物模型-删除确认(复测)', 'WARN', '点击删除后直接删除（无确认对话框）', `卡片${beforeDel}->${afterDel}`);
      } else {
        log('物模型-删除确认(复测)', 'WARN', '点击删除后无反应', '');
      }
    }
  } else {
    log('物模型-删除确认(复测)', 'WARN', '未找到删除按钮（可能无属性数据）', '');
  }

  // ============ 模板市场精确复测 ============
  console.log('\n===== 模板市场精确复测 =====');
  await page.goto(`${BASE}/template-market`, { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(2500);

  // 1. 模板卡片用 .template-card
  console.log('\n--- R6: 模板卡片用 .template-card ---');
  const tplCards = await page.locator('.template-card').count();
  console.log('  .template-card 数量:', tplCards);
  const cardNames = await page.locator('.template-card .card-title').allTextContents();
  console.log('  卡片名称:', cardNames);
  log('模板市场-卡片(复测)', tplCards >= 4 ? 'PASS' : 'CRITICAL',
    `找到${tplCards}个模板卡片`, JSON.stringify(cardNames));

  // 检查4个预期模板
  const hasBasic = cardNames.some(n => n.includes('基础版'));
  const hasStandard = cardNames.some(n => n.includes('标准版'));
  const hasPro = cardNames.some(n => n.includes('高级版'));
  const hasLivestock = cardNames.some(n => n.includes('养殖'));
  log('模板市场-模板完整性', hasBasic && hasStandard && hasPro && hasLivestock ? 'PASS' : 'WARN',
    '4个模板检查', `基础:${hasBasic} 标准:${hasStandard} 高级:${hasPro} 养殖:${hasLivestock}`);

  // 2. 预览物模型 - 用 .card-preview
  console.log('\n--- R7: 预览物模型（用 .card-preview）---');
  const previewArea = page.locator('.card-preview').first();
  await previewArea.click();
  await page.waitForTimeout(2000);
  await snap(page, 'R07-template-preview');
  const previewDlg = await page.locator('.el-dialog:visible').first().isVisible().catch(() => false);
  const previewTitle = await page.locator('.el-dialog:visible .el-dialog__title').first().textContent().catch(() => '');
  console.log('  预览弹窗可见:', previewDlg, '| 标题:', previewTitle);
  log('模板市场-预览(复测)', previewDlg ? 'PASS' : 'CRITICAL',
    previewDlg ? '预览弹窗正确弹出' : '预览弹窗未显示', `标题:${previewTitle}`);

  if (previewDlg) {
    const dlgBody = await page.locator('.el-dialog:visible .el-dialog__body').first().textContent().catch(() => '');
    const hasSensors = dlgBody.includes('传感器');
    const hasServices = dlgBody.includes('执行器服务') || dlgBody.includes('服务');
    const hasAlerts = dlgBody.includes('告警规则');
    const hasScenes = dlgBody.includes('自动化场景');
    console.log('  预览内容: 传感器:', hasSensors, '服务:', hasServices, '告警:', hasAlerts, '场景:', hasScenes);
    log('模板市场-预览内容', hasSensors && hasAlerts ? 'PASS' : 'WARN',
      '预览内容检查', `传感器:${hasSensors} 服务:${hasServices} 告警:${hasAlerts} 场景:${hasScenes}`);
  }
  // 关闭
  await page.locator('.el-dialog:visible .el-dialog__headerbtn').first().click().catch(() => {});
  await page.waitForTimeout(800);

  // 3. 分类筛选后卡片数（用正确选择器）
  console.log('\n--- R8: 分类筛选后卡片数 ---');
  await page.locator('.el-select').first().click();
  await page.waitForTimeout(800);
  await page.locator('.el-select-dropdown__item:has-text("农业")').first().click();
  await page.waitForTimeout(1500);
  await snap(page, 'R08-agri-filter');
  const agriCards = await page.locator('.template-card').count();
  const agriNames = await page.locator('.template-card .card-title').allTextContents();
  console.log('  农业筛选后卡片:', agriCards, agriNames);
  log('模板市场-农业筛选(复测)', agriCards === 3 ? 'PASS' : 'WARN',
    `农业筛选后${agriCards}个卡片`, JSON.stringify(agriNames));

  await browser.close();

  // 汇总
  console.log('\n===== 复测结果汇总 =====');
  const pass = findings.filter(f => f.sev === 'PASS').length;
  const warn = findings.filter(f => f.sev === 'WARN').length;
  const crit = findings.filter(f => f.sev === 'CRITICAL').length;
  console.log(`通过: ${pass} | 警告: ${warn} | 严重: ${crit} | 总计: ${findings.length}\n`);
  findings.forEach(f => {
    const tag = f.sev === 'CRITICAL' ? '❌' : f.sev === 'WARN' ? '⚠️' : '✅';
    console.log(`  ${tag} [${f.cat}] ${f.msg}${f.detail ? ' | ' + f.detail : ''}`);
  });

  fs.writeFileSync('/workspace/ui_test_recheck.json', JSON.stringify(findings, null, 2));
})();
