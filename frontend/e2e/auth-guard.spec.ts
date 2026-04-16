import { test, expect } from '@playwright/test';

test.describe('Auth Guard (mocked)', () => {
  test('hides settings entry for non-admin users and redirects settings route', async ({ page }) => {
    await page.route('**/api/access-code/check', route =>
      route.fulfill({ json: { data: { enabled: false, mode: 'proxy_header' } } })
    );
    await page.route('**/api/auth/me', route =>
      route.fulfill({ json: { data: { authenticated: true, role: 'user', auth_mode: 'proxy_header', email: 'user@company.com' } } })
    );

    await page.goto('/');
    await expect(page.getByRole('button', { name: /设置|Settings/ })).toHaveCount(0);

    await page.goto('/settings');
    await expect(page).toHaveURL(/\/$/);
  });

  test('shows settings entry for admin users', async ({ page }) => {
    await page.route('**/api/access-code/check', route =>
      route.fulfill({ json: { data: { enabled: false, mode: 'proxy_header' } } })
    );
    await page.route('**/api/auth/me', route =>
      route.fulfill({ json: { data: { authenticated: true, role: 'admin', auth_mode: 'proxy_header', email: 'admin@company.com' } } })
    );

    await page.goto('/');
    await expect(page.getByRole('button', { name: /设置|Settings/ })).toBeVisible();
  });
});
