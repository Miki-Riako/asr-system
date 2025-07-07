import { test, expect } from '@playwright/test';

test.describe('核心功能测试', () => {
  // 登录测试用户
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[placeholder*="用户名"]', 'testuser');
    await page.fill('input[placeholder*="密码"]', 'password123');
    await page.click('button:has-text("登录")');
    
    // 等待登录成功
    await page.waitForURL(/\/dashboard|\//, { timeout: 10000 });
  });

  test('热词管理功能', async ({ page }) => {
    // 导航到热词管理页面
    await page.click('text=热词管理');
    await expect(page).toHaveURL(/\/hotwords/);
    
    // 验证页面元素
    await expect(page.locator('text=添加热词')).toBeVisible();
    await expect(page.locator('text=批量导入')).toBeVisible();
    
    // 添加新热词
    await page.click('button:has-text("添加热词")');
    
    // 填写热词表单
    await page.fill('input[placeholder*="热词"]', '机器学习');
    
    // 设置权重 - 找到滑块并设置
    const slider = page.locator('.el-slider__runway');
    if (await slider.isVisible()) {
      await slider.click({ position: { x: 80, y: 0 } }); // 点击滑块位置设置权重
    }
    
    // 保存热词
    await page.click('button:has-text("添加")');
    
    // 验证热词添加成功
    await expect(page.locator('text=机器学习')).toBeVisible({ timeout: 5000 });
    
    // 测试搜索功能
    await page.fill('input[placeholder*="搜索热词"]', '机器');
    await expect(page.locator('text=机器学习')).toBeVisible();
    
    // 清空搜索
    await page.fill('input[placeholder*="搜索热词"]', '');
  });

  test('文件转写功能页面', async ({ page }) => {
    // 导航到文件转写页面
    await page.click('text=文件转写');
    await expect(page).toHaveURL(/\/transcription/);
    
    // 验证页面元素
    await expect(page.locator('text=音频文件上传')).toBeVisible();
    await expect(page.locator('text=热词设置')).toBeVisible();
    
    // 验证文件上传区域
    await expect(page.locator('.el-upload-dragger')).toBeVisible();
    
    // 验证热词开关
    await expect(page.locator('.el-switch')).toBeVisible();
    
    // 测试热词开关切换
    const hotwordSwitch = page.locator('.el-switch');
    await hotwordSwitch.click();
    
    // 验证热词管理链接
    await expect(page.locator('text=管理我的热词')).toBeVisible();
  });

  test('任务详情页面导航', async ({ page }) => {
    // 导航到首页
    await page.goto('/');
    
    // 如果有任务列表，测试点击查看详情
    const taskLinks = page.locator('text=查看详情');
    const taskCount = await taskLinks.count();
    
    if (taskCount > 0) {
      await taskLinks.first().click();
      
      // 验证进入任务详情页面
      await expect(page).toHaveURL(/\/task\//);
      await expect(page.locator('text=任务详情')).toBeVisible();
    }
  });

  test('导航功能测试', async ({ page }) => {
    // 测试各页面间的导航
    const pages = [
      { text: '首页', url: '/' },
      { text: '文件转写', url: '/transcription' },
      { text: '热词管理', url: '/hotwords' }
    ];

    for (const testPage of pages) {
      if (await page.locator(`text=${testPage.text}`).isVisible()) {
        await page.click(`text=${testPage.text}`);
        await expect(page).toHaveURL(new RegExp(testPage.url.replace('/', '\\/')));
        
        // 验证页面加载完成
        await page.waitForLoadState('networkidle');
      }
    }
  });

  test('响应式设计测试', async ({ page }) => {
    // 测试不同屏幕尺寸
    const viewports = [
      { width: 1920, height: 1080 }, // 桌面
      { width: 768, height: 1024 },  // 平板
      { width: 375, height: 667 }    // 手机
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      
      // 验证页面在不同尺寸下正常显示
      await page.goto('/');
      await expect(page.locator('header')).toBeVisible();
      
      // 在小屏幕上可能有汉堡菜单
      if (viewport.width < 768) {
        // 检查是否有移动端菜单
        const mobileMenu = page.locator('.mobile-menu');
        if (await mobileMenu.isVisible()) {
          await mobileMenu.click();
        }
      }
    }
  });
}); 