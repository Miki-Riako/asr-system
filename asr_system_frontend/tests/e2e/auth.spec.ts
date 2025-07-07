import { test, expect } from '@playwright/test';

test.describe('用户认证流程', () => {
  const testUser = {
    username: `testuser_${Date.now()}`,
    password: 'password123'
  };

  test('用户注册流程', async ({ page }) => {
    await page.goto('/register');
    
    // 填写注册表单
    await page.fill('input[placeholder*="用户名"]', testUser.username);
    await page.fill('input[placeholder*="密码"]', testUser.password);
    
    // 提交注册
    await page.click('button:has-text("注册")');
    
    // 验证注册成功 - 可能跳转到登录页面或显示成功消息
    await expect(page.locator('text=注册成功')).toBeVisible({ timeout: 10000 });
  });

  test('用户登录流程', async ({ page }) => {
    await page.goto('/login');
    
    // 填写登录表单
    await page.fill('input[placeholder*="用户名"]', testUser.username);
    await page.fill('input[placeholder*="密码"]', testUser.password);
    
    // 提交登录
    await page.click('button:has-text("登录")');
    
    // 验证登录成功 - 跳转到主页面
    await expect(page).toHaveURL(/\/dashboard|\/$/);
    
    // 验证用户信息显示
    await expect(page.locator(`text=${testUser.username}`)).toBeVisible({ timeout: 10000 });
  });

  test('登录失败处理', async ({ page }) => {
    await page.goto('/login');
    
    // 使用错误密码登录
    await page.fill('input[placeholder*="用户名"]', 'wronguser');
    await page.fill('input[placeholder*="密码"]', 'wrongpassword');
    
    await page.click('button:has-text("登录")');
    
    // 验证错误消息显示
    await expect(page.locator('text=用户名或密码错误')).toBeVisible({ timeout: 5000 });
  });

  test('完整用户流程：注册->登录->访问功能', async ({ page }) => {
    const uniqueUser = {
      username: `e2euser_${Date.now()}`,
      password: 'test123456'
    };

    // 步骤1：注册
    await page.goto('/register');
    await page.fill('input[placeholder*="用户名"]', uniqueUser.username);
    await page.fill('input[placeholder*="密码"]', uniqueUser.password);
    await page.click('button:has-text("注册")');
    
    // 等待注册成功
    await expect(page.locator('text=注册成功')).toBeVisible({ timeout: 10000 });

    // 步骤2：登录
    await page.goto('/login');
    await page.fill('input[placeholder*="用户名"]', uniqueUser.username);
    await page.fill('input[placeholder*="密码"]', uniqueUser.password);
    await page.click('button:has-text("登录")');
    
    // 等待进入主页面
    await page.waitForURL(/\/dashboard|\//, { timeout: 10000 });

    // 步骤3：验证可以访问功能页面
    if (await page.locator('text=文件转写').isVisible()) {
      await page.click('text=文件转写');
      await expect(page.locator('text=音频文件上传')).toBeVisible({ timeout: 5000 });
    }

    if (await page.locator('text=热词管理').isVisible()) {
      await page.click('text=热词管理');
      await expect(page.locator('text=添加热词')).toBeVisible({ timeout: 5000 });
    }
  });
}); 