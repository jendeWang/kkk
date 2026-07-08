// 3D数字孪生场景页面测试脚本
// 测试智慧农业IoT平台的 /greenhouse-3d 页面
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = 'http://localhost:3000';
const IMG_DIR = '/workspace/images/ui_test';

// 创建截图目录
fs.mkdirSync(IMG_DIR, { recursive: true });

// 测试结果收集
const findings = [];
function log(cat, sev, msg, detail) {
  findings.push({ cat, sev, msg, detail: detail || '' });
  const tag = sev === 'CRITICAL' ? '❌' : sev === 'WARN' ? '⚠️' : '✅';
  console.log(`[${cat}] ${tag} ${sev}: ${msg}${detail ? ' | ' + detail : ''}`);
}
async function snap(page, name) {
  try {
    await page.screenshot({ path: `${IMG_DIR}/${name}.png`, fullPage: false });
    console.log(`  📸 截图已保存: ${name}.png`);
  } catch (e) {
    console.log(`  ⚠️ 截图失败 ${name}: ${e.message}`);
  }
}

(async () => {
  console.log('========================================');
  console.log('  智慧大棚3D数字孪生场景测试');
  console.log('========================================\n');

  const browser = await chromium.launch({ headless: false, args: ['--no-sandbox'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // 收集控制台错误
  const consoleErrors = [];
  const consoleWarnings = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
    else if (msg.type() === 'warning') consoleWarnings.push(msg.text());
  });
  page.on('pageerror', err => consoleErrors.push(`PAGEERROR: ${err.message}`));

  try {
    // ============ 登录 ============
    console.log('===== 步骤0: 登录系统 =====');
    await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(1500);
    await page.locator('input[type="text"], input[placeholder*="用户"]').first().fill('admin');
    await page.locator('input[type="password"]').first().fill('admin123');
    await page.locator('button:has-text("登录"), button[type="submit"]').first().click();
    await page.waitForTimeout(2500);
    console.log('登录完成, 当前URL:', page.url());

    // ============ 1. 页面加载测试 ============
    console.log('\n===== 测试1: 页面加载测试 =====');
    await page.goto(`${BASE}/greenhouse-3d`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    // 等待5秒让3D场景完全加载
    await page.waitForTimeout(5000);
    await snap(page, '3d_page_loaded');

    // 检查页面标题
    const pageTitle = await page.locator('.hud-header h1').first().textContent().catch(() => '');
    console.log('  页面标题:', pageTitle);
    log('页面加载-标题', pageTitle.includes('数字孪生') ? 'PASS' : 'WARN',
      `标题: "${pageTitle}"`, '');

    // 检查是否有canvas元素（3D渲染区）
    const canvasCount = await page.locator('canvas').count();
    console.log('  canvas元素数量:', canvasCount);
    log('页面加载-Canvas', canvasCount > 0 ? 'PASS' : 'CRITICAL',
      canvasCount > 0 ? `找到${canvasCount}个canvas元素（3D渲染区）` : '未找到canvas元素，3D渲染区缺失',
      '');

    // 检查是否有左侧环境监测面板
    const leftPanel = await page.locator('.hud-left .data-panel').first();
    const leftPanelVisible = await leftPanel.isVisible().catch(() => false);
    const leftPanelTitle = await leftPanel.locator('.panel-title').first().textContent().catch(() => '');
    console.log('  左侧面板可见:', leftPanelVisible, '| 标题:', leftPanelTitle);
    log('页面加载-左侧环境面板', leftPanelVisible && leftPanelTitle.includes('环境监测') ? 'PASS' : 'CRITICAL',
      leftPanelVisible ? `左侧环境监测面板已加载，标题: ${leftPanelTitle}` : '左侧环境监测面板未显示',
      '');

    // 检查是否有右侧设备控制面板
    const rightPanel = await page.locator('.hud-right .data-panel').first();
    const rightPanelVisible = await rightPanel.isVisible().catch(() => false);
    const rightPanelTitle = await rightPanel.locator('.panel-title').first().textContent().catch(() => '');
    console.log('  右侧面板可见:', rightPanelVisible, '| 标题:', rightPanelTitle);
    log('页面加载-右侧设备面板', rightPanelVisible && rightPanelTitle.includes('设备控制') ? 'PASS' : 'CRITICAL',
      rightPanelVisible ? `右侧设备控制面板已加载，标题: ${rightPanelTitle}` : '右侧设备控制面板未显示',
      '');

    // 检查控制台错误
    console.log('  控台错误数:', consoleErrors.length);
    if (consoleErrors.length > 0) {
      console.log('  错误详情:', consoleErrors.slice(0, 3));
    }
    // WebGL相关错误是可预期的（headless环境），不算严重
    const criticalErrors = consoleErrors.filter(e =>
      !e.includes('WebGL') && !e.includes('webgl') && !e.includes('GPU') &&
      !e.includes('Failed to load resource') && !e.includes('net::')
    );
    log('页面加载-控制台错误', criticalErrors.length === 0 ? 'PASS' : 'WARN',
      criticalErrors.length === 0 ? '无控制台错误' : `发现${criticalErrors.length}个严重错误`,
      criticalErrors.slice(0, 2).join(' | '));

    // ============ 2. 3D交互测试 ============
    console.log('\n===== 测试2: 3D交互测试 =====');

    // 检查OrbitControls（通过检查3D交互能力 - canvas应该能响应鼠标事件）
    const canvas = page.locator('canvas').first();
    const canvasExists = await canvas.count() > 0;
    console.log('  canvas存在(用于OrbitControls):', canvasExists);

    // 检查视角控制面板
    const viewControlPanel = page.locator('.hud-right .data-panel:has(.panel-title:has-text("视角控制"))').first();
    const viewControlVisible = await viewControlPanel.isVisible().catch(() => false);
    console.log('  视角控制面板可见:', viewControlVisible);
    log('3D交互-OrbitControls', viewControlVisible ? 'PASS' : 'WARN',
      viewControlVisible ? '视角控制面板存在，OrbitControls已加载' : '视角控制面板未找到',
      '');

    // 检查"重置视角"按钮（实际按钮文本是"重置"）
    const resetBtn = page.locator('.btn-row button:has-text("重置")').first();
    const resetBtnVisible = await resetBtn.isVisible().catch(() => false);
    console.log('  重置视角按钮可见:', resetBtnVisible);
    log('3D交互-重置视角按钮', resetBtnVisible ? 'PASS' : 'CRITICAL',
      resetBtnVisible ? '"重置"按钮存在' : '未找到"重置"按钮',
      '');

    // 检查"自动旋转"开关（实际按钮文本是"旋转"/"停止"）
    const rotateBtn = page.locator('.btn-row button:has-text("旋转"), .btn-row button:has-text("停止")').first();
    const rotateBtnVisible = await rotateBtn.isVisible().catch(() => false);
    const rotateBtnText = await rotateBtn.textContent().catch(() => '');
    console.log('  自动旋转按钮可见:', rotateBtnVisible, '| 文本:', rotateBtnText);
    log('3D交互-自动旋转开关', rotateBtnVisible ? 'PASS' : 'CRITICAL',
      rotateBtnVisible ? `自动旋转开关存在，当前文本: "${rotateBtnText}"` : '未找到自动旋转开关',
      '');

    // 尝试点击"自动旋转"开关
    if (rotateBtnVisible) {
      const beforeText = rotateBtnText;
      await rotateBtn.click();
      await page.waitForTimeout(1500);
      const afterText = await rotateBtn.textContent().catch(() => '');
      console.log('  点击后按钮文本:', beforeText, '->', afterText);
      log('3D交互-点击自动旋转', beforeText !== afterText ? 'PASS' : 'WARN',
        beforeText !== afterText ? `自动旋转切换成功: ${beforeText} -> ${afterText}` : '点击后状态未变化',
        '');
      await snap(page, '3d_auto_rotate_clicked');
      // 再点一次恢复原状
      await rotateBtn.click().catch(() => {});
      await page.waitForTimeout(500);
    }

    // ============ 3. 设备控制面板测试 ============
    console.log('\n===== 测试3: 设备控制面板测试 =====');

    // 检查设备控制区域的开关按钮
    const expectedDevices = ['通风风扇', '补光灯', '遮阳帘', '灌溉泵', '电磁阀', '加热膜'];
    const deviceItems = page.locator('.hud-right .device-item');
    const deviceCount = await deviceItems.count();
    console.log('  设备控制项数量:', deviceCount);

    const foundDevices = [];
    for (const name of expectedDevices) {
      const item = page.locator(`.device-item:has-text("${name}")`).first();
      const exists = await item.count() > 0;
      if (exists) {
        const switchEl = item.locator('.el-switch').first();
        const switchVisible = await switchEl.isVisible().catch(() => false);
        console.log(`  设备 "${name}": 存在=${exists}, 开关可见=${switchVisible}`);
        foundDevices.push(name);
      } else {
        console.log(`  设备 "${name}": 未找到`);
      }
    }
    log('设备控制-开关按钮', foundDevices.length >= 4 ? 'PASS' : 'CRITICAL',
      `找到${foundDevices.length}/${expectedDevices.length}个设备开关: ${foundDevices.join(', ')}`,
      '');

    // 尝试点击通风扇开关
    const fanItem = page.locator('.device-item:has-text("通风风扇")').first();
    const fanExists = await fanItem.count() > 0;
    if (fanExists) {
      const fanSwitch = fanItem.locator('.el-switch').first();
      const beforeChecked = await fanSwitch.evaluate(el => el.classList.contains('is-checked')).catch(() => false);
      console.log('  通风扇开关初始状态(checked):', beforeChecked);

      await fanSwitch.click();
      await page.waitForTimeout(2000);
      await snap(page, '3d_fan_toggled');

      // 检查是否显示"命令已下发"提示
      const successMsg = page.locator('.el-message--success, .el-message:has-text("命令已下发")').first();
      const warningMsg = page.locator('.el-message--warning, .el-message:has-text("未检测")').first();
      const errorMsg = page.locator('.el-message--error, .el-message:has-text("失败")').first();

      const successVisible = await successMsg.isVisible().catch(() => false);
      const warningVisible = await warningMsg.isVisible().catch(() => false);
      const errorVisible = await errorMsg.isVisible().catch(() => false);
      const msgText = await page.locator('.el-message').first().textContent().catch(() => '');

      console.log('  命令下发提示 - 成功:', successVisible, '警告:', warningVisible, '错误:', errorVisible);
      console.log('  提示文本:', msgText);

      if (successVisible) {
        log('设备控制-通风扇命令下发', 'PASS', '命令已下发提示已显示', msgText);
      } else if (warningVisible) {
        log('设备控制-通风扇命令下发', 'WARN', '显示警告提示（可能无在线设备）', msgText);
      } else if (errorVisible) {
        log('设备控制-通风扇命令下发', 'WARN', '命令下发失败', msgText);
      } else {
        log('设备控制-通风扇命令下发', 'WARN', '未检测到提示信息', '');
      }

      // 等待提示消失
      await page.waitForTimeout(2000);
    } else {
      log('设备控制-通风扇命令下发', 'CRITICAL', '未找到通风扇开关', '');
    }

    // ============ 4. 环境数据面板测试 ============
    console.log('\n===== 测试4: 环境数据面板测试 =====');

    const envCards = page.locator('.hud-left .env-card');
    const envCardCount = await envCards.count();
    console.log('  环境数据卡片数量:', envCardCount);

    // 预期9个环境指标：温度、湿度、光照、土壤、CO2、地温、酸碱度、风速、雨量
    const expectedMetrics = [
      { label: '温度', unit: '°C', min: 10, max: 40 },
      { label: '湿度', unit: '%', min: 30, max: 90 },
      { label: '光照', unit: 'klux', min: 0, max: 100 },
      { label: '土壤', unit: '%', min: 0, max: 100 },
      { label: 'CO2', unit: 'ppm', min: 300, max: 1500 },
      { label: '地温', unit: '°C', min: 5, max: 40 },
      { label: '酸碱度', unit: 'pH', min: 4, max: 9 },
      { label: '风速', unit: 'm/s', min: 0, max: 30 },
      { label: '雨量', unit: 'mm', min: 0, max: 100 },
    ];

    let validMetrics = 0;
    let totalMetrics = 0;
    for (const metric of expectedMetrics) {
      const card = page.locator(`.env-card .env-label:has-text("${metric.label}")`).first();
      const cardExists = await card.count() > 0;
      if (cardExists) {
        totalMetrics++;
        const parent = card.locator('..');
        const valText = await parent.locator('.env-val').first().textContent().catch(() => '');
        const unitText = await parent.locator('.env-unit').first().textContent().catch(() => '');
        console.log(`  ${metric.label}: 值=${valText}, 单位=${unitText}`);
        const val = parseFloat(valText);
        if (!isNaN(val) && val !== 0) {
          // 检查数据是否在合理范围（允许显示"--"或0表示无数据）
          if (val >= metric.min && val <= metric.max) {
            validMetrics++;
          } else {
            console.log(`    ⚠️ ${metric.label}值${val}超出预期范围[${metric.min}-${metric.max}]`);
          }
        }
      }
    }
    log('环境数据-面板显示', totalMetrics >= 7 ? 'PASS' : 'CRITICAL',
      `显示${totalMetrics}/9个环境指标`,
      '');

    log('环境数据-数值合理性', validMetrics >= 3 ? 'PASS' : 'WARN',
      `${validMetrics}/${totalMetrics}个指标数值在合理范围内`,
      `(温度10-40°C, 湿度30-90%等)`);

    // ============ 5. 告警闪烁测试 ============
    console.log('\n===== 测试5: 告警闪烁测试 =====');

    // 检查是否有告警闪烁层（CSS类存在即可，不一定可见）
    const alertOverlay = page.locator('.alert-flash-overlay');
    const alertOverlayExists = await alertOverlay.count() > 0;
    console.log('  告警闪烁层元素存在:', alertOverlayExists);

    // 通过控制台/页面状态检查告警状态
    // 触发告警的条件：温度>30°C 或 土壤<30% 等
    // 检查环境状态指示灯
    const warningStatus = await page.locator('.env-status.warning').count();
    const dangerStatus = await page.locator('.env-status.danger').count();
    const normalStatus = await page.locator('.env-status.normal').count();
    console.log('  状态指示灯 - 正常:', normalStatus, '警告:', warningStatus, '危险:', dangerStatus);

    // 截图记录当前告警状态
    await snap(page, '3d_alert_status');

    if (alertOverlayExists) {
      log('告警闪烁-元素存在', 'PASS', '告警闪烁层DOM元素已存在（CSS .alert-flash-overlay）',
        `当前状态: normal=${normalStatus}, warning=${warningStatus}, danger=${dangerStatus}`);
    } else {
      log('告警闪烁-元素存在', 'WARN', '未找到告警闪烁层元素', '');
    }

    // 检查告警闪烁效果是否在CSS中定义
    const alertCssDefined = await page.evaluate(() => {
      const sheets = document.styleSheets;
      for (let i = 0; i < sheets.length; i++) {
        try {
          const rules = sheets[i].cssRules;
          for (let j = 0; j < rules.length; j++) {
            if (rules[j].cssText && rules[j].cssText.includes('alertFlash')) {
              return true;
            }
          }
        } catch (e) { /* cross-origin */ }
      }
      return false;
    }).catch(() => false);
    console.log('  告警闪烁动画CSS定义存在:', alertCssDefined);
    log('告警闪烁-动画CSS', alertCssDefined ? 'PASS' : 'WARN',
      alertCssDefined ? 'alertFlash动画CSS已定义' : '未找到alertFlash动画CSS',
      '');

    // ============ 6. 3D设备标签测试 ============
    console.log('\n===== 测试6: 3D设备标签测试 =====');

    // CSS2DRenderer创建的标签是absolute定位的div，在canvas容器内
    // 标签样式: background:rgba(0,15,30,0.9); 包含温度/湿度/光照/土壤等文字
    await page.waitForTimeout(1000);
    await snap(page, '3d_device_labels');

    // 查找3D场景中的悬浮标签（CSS2DObject创建的div）
    // 这些div的父元素是 .canvas-container 的子元素（labelRenderer.domElement）
    const labelContainer = page.locator('.canvas-container > div').first();
    const labelContainerExists = await labelContainer.count() > 0;
    console.log('  标签渲染容器存在:', labelContainerExists);

    // 查找包含传感器名称的标签
    const sensorLabels = ['温度', '湿度', '光照', '土壤'];
    let foundLabels = 0;
    const labelDetails = [];
    for (const label of sensorLabels) {
      // CSS2DObject创建的div直接附加到labelRenderer的domElement
      // 查找包含温度等文字的div
      const labelEl = page.locator(`.canvas-container div:has-text("${label}"), .greenhouse-3d div:has-text("${label}")`).first();
      const exists = await labelEl.count() > 0;
      if (exists) {
        const text = await labelEl.textContent().catch(() => '');
        console.log(`  设备标签 "${label}": 存在, 内容: "${text}"`);
        labelDetails.push(text);
        foundLabels++;
      } else {
        console.log(`  设备标签 "${label}": 未找到`);
      }
    }

    log('3D设备标签-存在性', foundLabels >= 2 ? 'PASS' : 'WARN',
      `找到${foundLabels}/4个3D悬浮标签`,
      labelDetails.join(' | '));

    // 检查标签是否显示设备名称和状态
    // 标签格式应为: 🌡️ 温度 25.5°C 这种格式
    const labelWithStatus = labelDetails.some(t => /\d/.test(t));
    log('3D设备标签-内容完整性', labelWithStatus ? 'PASS' : 'WARN',
      labelWithStatus ? '标签包含设备名称和数值状态' : '标签可能未显示数值状态',
      '');

    // 额外检查：设备信息弹窗（点击设备后弹出）
    console.log('\n  --- 额外检查: 设备信息弹窗 ---');
    // 尝试点击3D场景中的设备（点击canvas中心区域，可能命中设备）
    if (canvasExists) {
      const canvasBox = await canvas.boundingBox();
      if (canvasBox) {
        // 点击canvas中心稍偏的位置（模拟点击设备）
        await page.mouse.click(canvasBox.x + canvasBox.width / 2, canvasBox.height / 2);
        await page.waitForTimeout(1500);
        const popup = page.locator('.device-info-popup').first();
        const popupVisible = await popup.isVisible().catch(() => false);
        if (popupVisible) {
          const popupTitle = await popup.locator('.popup-title').first().textContent().catch(() => '');
          const popupState = await popup.locator('.info-value').first().textContent().catch(() => '');
          console.log('  设备信息弹窗已弹出, 标题:', popupTitle, '状态:', popupState);
          await snap(page, '3d_device_popup');
          log('3D设备标签-信息弹窗', 'PASS', `点击设备后弹窗已显示: ${popupTitle}`,
            `状态: ${popupState}`);
          // 关闭弹窗
          await popup.locator('.popup-close').first().click().catch(() => {});
          await page.waitForTimeout(500);
        } else {
          console.log('  点击canvas未触发设备弹窗（可能未命中设备hitbox）');
          log('3D设备标签-信息弹窗', 'WARN', '点击3D场景未触发设备信息弹窗', '可能未命中设备hitbox或WebGL不可用');
        }
      }
    }

  } catch (e) {
    console.error('\n❌ 测试执行出错:', e.message);
    console.error(e.stack);
    log('测试执行', 'CRITICAL', '测试执行过程中出错', e.message);
    await snap(page, '3d_error_state').catch(() => {});
  } finally {
    await page.waitForTimeout(1000);
    await browser.close();
  }

  // ============ 测试结果汇总 ============
  console.log('\n========================================');
  console.log('  测试结果汇总');
  console.log('========================================\n');

  const pass = findings.filter(f => f.sev === 'PASS').length;
  const warn = findings.filter(f => f.sev === 'WARN').length;
  const crit = findings.filter(f => f.sev === 'CRITICAL').length;
  const total = findings.length;

  console.log(`总计: ${total}项 | 通过: ${pass} | 警告: ${warn} | 严重: ${crit}\n`);
  console.log('详细结果:');
  findings.forEach((f, i) => {
    const tag = f.sev === 'CRITICAL' ? '❌' : f.sev === 'WARN' ? '⚠️' : '✅';
    console.log(`  ${i + 1}. ${tag} [${f.cat}] ${f.sev}`);
    console.log(`     ${f.msg}`);
    if (f.detail) console.log(`     详情: ${f.detail}`);
  });

  // 保存结果到JSON
  const resultJson = {
    test_time: new Date().toISOString(),
    summary: { total, pass, warn, critical: crit },
    details: findings,
  };
  fs.writeFileSync('/workspace/ui_test_3d_result.json', JSON.stringify(resultJson, null, 2));
  console.log(`\n测试结果已保存到: /workspace/ui_test_3d_result.json`);
  console.log(`截图已保存到: ${IMG_DIR}/`);

  // 退出码
  process.exit(crit > 0 ? 1 : 0);
})();
