import { expect, test } from '@playwright/test'

test.describe('lablog UI smoke', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('lablog-welcome-dismissed', 'true')
    })

    // Respuestas array para cualquier GET de listado (evita .map en no-arrays).
    await page.route('**/api/v1/**', async (route) => {
      if (route.request().method() !== 'GET') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
        return
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: '[]',
      })
    })
  })

  test('shell carga y preferencias de personalización', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/lablog/i)
    await expect(page.locator('button[title="Nueva página"]')).toBeVisible({ timeout: 20_000 })

    const prefs = page.locator(
      'button[data-testid="settings-trigger"], button[title="Preferencias"], button[aria-label="Preferencias"]',
    )
    await expect(prefs.first()).toBeVisible({ timeout: 10_000 })
    await prefs.first().click()
    await expect(page.getByText('Densidad de UI')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText('Fuente del editor LaTeX')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Nord' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Exportar' })).toBeVisible()
  })
})
