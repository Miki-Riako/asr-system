import { test, expect } from '@playwright/test';

test.describe('应用冒烟测试', () => {
  test('应用正常加载', async ({ page }) => {
    await page.goto('/');
    
    // 验证页面标题
    await expect(page).toHaveTitle(/语音识别系统/);
    
    // 验证页面包含关键元素
    await expect(page.locator('text=登录')).toBeVisible();
  });

  test('登录页面正常加载', async ({ page }) => {
    await page.goto('/login');
    
    // 验证登录表单存在
    await expect(page.locator('input[type="text"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button:has-text("登录")')).toBeVisible();
  });

  test('注册页面正常加载', async ({ page }) => {
    await page.goto('/register');
    
    // 验证注册表单存在
    await expect(page.locator('input[type="text"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button:has-text("注册")')).toBeVisible();
  });
}); 