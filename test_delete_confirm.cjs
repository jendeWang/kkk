const { chromium } = require('playwright');

async function testDeleteConfirm() {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });

  try {
    // 登录
    await page.goto('http://localhost:3000/login');
    await page.waitForTimeout(2000);
    await page.fill('input[placeholder="用户名"]', 'admin');
    await page.fill('input[placeholder="密码"]', 'admin123');
    await page.click('button:has-text("登录")');
    await page.waitForTimeout(3000);
    // 高级模式
    const simple = await page.locator('text=简化').first().isVisible().catch(() => false);
    if (simple) { await page.locator('text=简化').first().click(); await page.waitForTimeout(1000); }

    // 物模型编辑器
    await page.goto('http://localhost:3000/thing-model');
    await page.waitForTimeout(4000);

    // 选择产品
    await page.locator('.el-select').first().click();
    await page.waitForTimeout(800);
    await page.locator('.el-select-dropdown__item').first().click();
    await page.waitForTimeout(2000);

    // 确保在属性标签页
    await page.locator('.el-tabs__item:has-text("属性")').first().click();
    await page.waitForTimeout(500);

    // 找删除按钮
    const delBtn = page.locator('.model-card .el-button--danger').first();
    if (await delBtn.isVisible().catch(() => false)) {
      console.log('找到删除按钮，点击...');
      await delBtn.click();
      await page.waitForTimeout(1500);

      // 检查确认框
      const confirmBox = await page.locator('.el-message-box, .el-overlay').isVisible().catch(() => false);
      const confirmText = await page.locator('.el-message-box__message').textContent().catch(() => '');
      
      if (confirmBox || confirmText.length > 0) {
        console.log('✅ 删除确认对话框显示！');
        console.log('确认框内容: ' + confirmText);
        // 取消
        const cancelBtn = page.locator('button:has-text("取消")').first();
        if (await cancelBtn.isVisible()) await cancelBtn.click();
        console.log('测试通过');
      } else {
        console.log('❌ 删除确认对话框未显示');
        // 截图看看
        await page.screenshot({ path: '/workspace/images/ui_test/delete_no_confirm.png' });
      }
    } else {
      console.log('⚠️ 删除按钮未找到');
    }
  } catch (e) {
    console.log('异常: ' + e.message);
  } finally {
    await browser.close();
  }
}

testDeleteConfirm();