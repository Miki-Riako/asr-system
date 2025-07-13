import { test, expect } from '@playwright/test';

// 测试前的准备工作
test.beforeEach(async ({ page }) => {
  // 访问登录页面
  await page.goto('/login');
  
  // 执行登录
  await page.fill('input[placeholder="请输入用户名/邮箱"]', 'testuser');
  await page.fill('input[placeholder="请输入密码"]', 'testpass123');
  
  // 获取并输入验证码
  const captchaText = await page.textContent('.captcha-box');
  await page.fill('input[placeholder="输入验证码"]', captchaText);
  
  // 点击登录按钮
  await page.click('button:has-text("登录")');
  
  // 等待登录成功，跳转到主页
  await page.waitForURL('/');
  
  // 导航到热词管理页面
  await page.goto('/hotwords');
  await page.waitForLoadState('networkidle');
});

test.describe('热词管理功能测试', () => {
  
  test('页面加载和基本元素显示', async ({ page }) => {
    // 检查页面标题
    await expect(page.locator('h1')).toContainText('热词管理');
    
    // 检查主要按钮是否存在
    await expect(page.locator('button:has-text("添加热词")')).toBeVisible();
    await expect(page.locator('button:has-text("批量导入")')).toBeVisible();
    await expect(page.locator('button:has-text("批量删除")')).toBeVisible();
    
    // 检查搜索框
    await expect(page.locator('input[placeholder="搜索热词..."]')).toBeVisible();
    
    // 检查热词列表表格
    await expect(page.locator('.el-table')).toBeVisible();
  });
  
  test('添加热词功能', async ({ page }) => {
    // 点击添加热词按钮
    await page.click('button:has-text("添加热词")');
    
    // 等待对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('添加热词');
    
    // 填写热词信息
    await page.fill('.el-dialog input[placeholder="请输入热词"]', '测试热词');
    
    // 设置权重滑块 - 点击滑块的特定位置来设置权重
    const slider = page.locator('.el-slider__runway');
    const sliderBox = await slider.boundingBox();
    // 点击滑块的80%位置（对应权重8）
    await slider.click({ 
      position: { 
        x: sliderBox.width * 0.8, 
        y: sliderBox.height / 2 
      } 
    });
    
    // 保存热词
    await page.click('.el-dialog button:has-text("保存")');
    
    // 等待对话框关闭
    await expect(page.locator('.el-dialog')).toBeHidden();
    
    // 验证热词已添加到列表中
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '测试热词' })).toBeVisible();
    
    // 验证成功消息
    await expect(page.locator('.el-message--success')).toBeVisible();
  });
  
  test('搜索热词功能', async ({ page }) => {
    // 先添加几个热词
    const testWords = ['搜索测试1', '搜索测试2', '其他热词'];
    
    for (const word of testWords) {
      await page.click('button:has-text("添加热词")');
      await page.fill('.el-dialog input[placeholder="请输入热词"]', word);
      await page.click('.el-dialog button:has-text("保存")');
      await page.waitForTimeout(500); // 等待添加完成
    }
    
    // 使用搜索功能
    await page.fill('input[placeholder="搜索热词..."]', '搜索测试');
    
    // 等待搜索结果
    await page.waitForTimeout(1000);
    
    // 验证搜索结果
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '搜索测试1' })).toBeVisible();
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '搜索测试2' })).toBeVisible();
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '其他热词' })).toBeHidden();
    
    // 清空搜索
    await page.fill('input[placeholder="搜索热词..."]', '');
    await page.waitForTimeout(1000);
    
    // 验证所有热词都显示
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '其他热词' })).toBeVisible();
  });
  
  test('编辑热词功能', async ({ page }) => {
    // 先添加一个热词
    await page.click('button:has-text("添加热词")');
    await page.fill('.el-dialog input[placeholder="请输入热词"]', '待编辑热词');
    await page.click('.el-dialog button:has-text("保存")');
    await page.waitForTimeout(500);
    
    // 找到编辑按钮并点击
    const editButton = page.locator('.el-table').locator('tr').filter({ hasText: '待编辑热词' }).locator('button').filter({ hasText: '编辑' });
    await editButton.click();
    
    // 等待编辑对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('编辑热词');
    
    // 修改热词内容
    await page.fill('.el-dialog input[placeholder="请输入热词"]', '已编辑热词');
    
    // 保存修改
    await page.click('.el-dialog button:has-text("保存")');
    
    // 等待对话框关闭
    await expect(page.locator('.el-dialog')).toBeHidden();
    
    // 验证修改成功
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '已编辑热词' })).toBeVisible();
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '待编辑热词' })).toBeHidden();
    
    // 验证成功消息
    await expect(page.locator('.el-message--success')).toBeVisible();
  });
  
  test('删除热词功能', async ({ page }) => {
    // 先添加一个热词
    await page.click('button:has-text("添加热词")');
    await page.fill('.el-dialog input[placeholder="请输入热词"]', '待删除热词');
    await page.click('.el-dialog button:has-text("保存")');
    await page.waitForTimeout(500);
    
    // 找到删除按钮并点击
    const deleteButton = page.locator('.el-table').locator('tr').filter({ hasText: '待删除热词' }).locator('button').filter({ hasText: '删除' });
    await deleteButton.click();
    
    // 等待确认对话框出现
    await expect(page.locator('.el-message-box')).toBeVisible();
    await expect(page.locator('.el-message-box__content')).toContainText('确定要删除热词');
    
    // 确认删除
    await page.click('.el-message-box button:has-text("确定")');
    
    // 验证热词已被删除
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '待删除热词' })).toBeHidden();
    
    // 验证成功消息
    await expect(page.locator('.el-message--success')).toBeVisible();
  });
  
  test('批量删除功能', async ({ page }) => {
    // 先添加几个热词
    const testWords = ['批量删除1', '批量删除2', '保留热词'];
    
    for (const word of testWords) {
      await page.click('button:has-text("添加热词")');
      await page.fill('.el-dialog input[placeholder="请输入热词"]', word);
      await page.click('.el-dialog button:has-text("保存")');
      await page.waitForTimeout(500);
    }
    
    // 选中要删除的热词
    await page.check('.el-table').locator('tr').filter({ hasText: '批量删除1' }).locator('.el-checkbox__input');
    await page.check('.el-table').locator('tr').filter({ hasText: '批量删除2' }).locator('.el-checkbox__input');
    
    // 点击批量删除按钮
    await page.click('button:has-text("批量删除")');
    
    // 等待确认对话框
    await expect(page.locator('.el-message-box')).toBeVisible();
    await expect(page.locator('.el-message-box__content')).toContainText('确定要删除选中的');
    
    // 确认删除
    await page.click('.el-message-box button:has-text("确定")');
    
    // 验证热词已被删除
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '批量删除1' })).toBeHidden();
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '批量删除2' })).toBeHidden();
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '保留热词' })).toBeVisible();
  });
  
  test('批量导入功能', async ({ page }) => {
    // 点击批量导入按钮
    await page.click('button:has-text("批量导入")');
    
    // 等待导入对话框出现
    await expect(page.locator('.el-dialog')).toBeVisible();
    await expect(page.locator('.el-dialog__title')).toContainText('批量导入热词');
    
    // 创建测试文件内容
    const csvContent = `导入热词1,5
导入热词2,8
导入热词3,3`;
    
    // 使用文件上传
    const fileInput = page.locator('.el-dialog input[type="file"]');
    
    // 创建一个模拟的文件
    await fileInput.setInputFiles({
      name: 'test_hotwords.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(csvContent)
    });
    
    // 点击导入按钮
    await page.click('.el-dialog button:has-text("导入")');
    
    // 等待导入完成
    await page.waitForTimeout(2000);
    
    // 验证导入成功消息
    await expect(page.locator('.el-message--success')).toBeVisible();
    
    // 验证导入的热词出现在列表中
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '导入热词1' })).toBeVisible();
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '导入热词2' })).toBeVisible();
    await expect(page.locator('.el-table').locator('td').filter({ hasText: '导入热词3' })).toBeVisible();
  });
  
  test('热词权重显示和排序', async ({ page }) => {
    // 添加不同权重的热词
    const testWords = [
      { word: '高权重热词', weight: 90 },
      { word: '低权重热词', weight: 10 },
      { word: '中等权重热词', weight: 50 }
    ];
    
    for (const { word, weight } of testWords) {
      await page.click('button:has-text("添加热词")');
      await page.fill('.el-dialog input[placeholder="请输入热词"]', word);
      
      // 设置权重
      const slider = page.locator('.el-slider__runway');
      const sliderBox = await slider.boundingBox();
      await slider.click({ 
        position: { 
          x: sliderBox.width * (weight / 100), 
          y: sliderBox.height / 2 
        } 
      });
      
      await page.click('.el-dialog button:has-text("保存")');
      await page.waitForTimeout(500);
    }
    
    // 验证权重显示
    await expect(page.locator('.el-table').locator('tr').filter({ hasText: '高权重热词' })).toBeVisible();
    await expect(page.locator('.el-table').locator('tr').filter({ hasText: '低权重热词' })).toBeVisible();
    await expect(page.locator('.el-table').locator('tr').filter({ hasText: '中等权重热词' })).toBeVisible();
    
    // 检查权重标签是否正确显示
    const highWeightRow = page.locator('.el-table').locator('tr').filter({ hasText: '高权重热词' });
    await expect(highWeightRow.locator('.el-tag')).toBeVisible();
  });
  
  test('表单验证功能', async ({ page }) => {
    // 点击添加热词按钮
    await page.click('button:has-text("添加热词")');
    
    // 不输入任何内容直接保存
    await page.click('.el-dialog button:has-text("保存")');
    
    // 验证表单验证信息显示
    await expect(page.locator('.el-form-item__error')).toBeVisible();
    
    // 输入空的热词
    await page.fill('.el-dialog input[placeholder="请输入热词"]', '   ');
    await page.click('.el-dialog button:has-text("保存")');
    
    // 验证仍然有错误信息
    await expect(page.locator('.el-form-item__error')).toBeVisible();
    
    // 输入正确的热词
    await page.fill('.el-dialog input[placeholder="请输入热词"]', '有效热词');
    await page.click('.el-dialog button:has-text("保存")');
    
    // 验证保存成功
    await expect(page.locator('.el-dialog')).toBeHidden();
    await expect(page.locator('.el-message--success')).toBeVisible();
  });
  
  test('响应式设计测试', async ({ page }) => {
    // 测试移动端视图
    await page.setViewportSize({ width: 375, height: 667 });
    
    // 验证页面在移动端仍然可用
    await expect(page.locator('h1')).toContainText('热词管理');
    await expect(page.locator('button:has-text("添加热词")')).toBeVisible();
    
    // 测试添加热词在移动端的表现
    await page.click('button:has-text("添加热词")');
    await expect(page.locator('.el-dialog')).toBeVisible();
    
    // 恢复桌面视图
    await page.setViewportSize({ width: 1280, height: 720 });
  });
  
  test('错误处理测试', async ({ page }) => {
    // 模拟网络错误情况
    await page.route('**/hotwords', (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ detail: '服务器内部错误' })
        });
      } else {
        route.continue();
      }
    });
    
    // 尝试添加热词
    await page.click('button:has-text("添加热词")');
    await page.fill('.el-dialog input[placeholder="请输入热词"]', '错误测试热词');
    await page.click('.el-dialog button:has-text("保存")');
    
    // 验证错误消息显示
    await expect(page.locator('.el-message--error')).toBeVisible();
    
    // 验证对话框仍然打开（用户可以重试）
    await expect(page.locator('.el-dialog')).toBeVisible();
  });
  
});

test.describe('热词管理权限测试', () => {
  
  test('未登录用户无法访问热词管理', async ({ page }) => {
    // 清除登录状态
    await page.evaluate(() => localStorage.removeItem('token'));
    
    // 尝试访问热词管理页面
    await page.goto('/hotwords');
    
    // 验证被重定向到登录页面
    await expect(page).toHaveURL('/login');
  });
  
}); 