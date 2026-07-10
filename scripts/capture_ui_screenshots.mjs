/**
 * Capturas reales de la UI de lablog (Playwright + API real).
 * Uso: node scripts/capture_ui_screenshots.mjs
 * Requiere API :8000 y Vite :5173.
 */
import { chromium } from '../ui/node_modules/playwright/index.mjs'
import { mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const OUT = join(ROOT, 'docs/assets/screenshots')
const BASE = process.env.LABLOG_UI_URL || 'http://127.0.0.1:5173'
const API = process.env.LABLOG_API_URL || 'http://127.0.0.1:8000/api/v1'

mkdirSync(OUT, { recursive: true })

const LATEX_DEMO = String.raw`% lablog-diagram: preset=rc_series_charge version=1
% lablog-param: R=1000
% lablog-param: C=1e-06
% lablog-param: V0=5
\section{Sesión RC}
La constante de tiempo es $\tau = RC$.
\begin{equation}
  v_C(t) = V_0\left(1 - e^{-t/RC}\right)
\end{equation}
`

async function api(path, init = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init.headers || {}) },
    ...init,
  })
  if (!res.ok) {
    const t = await res.text()
    throw new Error(`${init.method || 'GET'} ${path} -> ${res.status} ${t}`)
  }
  if (res.status === 204) return null
  const text = await res.text()
  return text ? JSON.parse(text) : null
}

async function seed() {
  const page = await api('/pages', {
    method: 'POST',
    body: JSON.stringify({ title: 'RC lab session', project_id: 'optics-bench' }),
  })
  const id = page.page_id
  const detail = await api(`/pages/${id}`)
  await api(`/pages/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ raw: LATEX_DEMO, version: detail.version }),
  })
  // second empty-ish page for sidebar density
  await api('/pages', {
    method: 'POST',
    body: JSON.stringify({ title: 'Notas de óptica', project_id: 'optics-bench' }),
  })
  return id
}

async function shot(page, name, opts = {}) {
  const path = join(OUT, name)
  await page.screenshot({ path, fullPage: false, ...opts })
  console.log('wrote', path)
}

async function main() {
  console.log('seeding API…')
  const pageId = await seed()
  console.log('page', pageId)

  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
    colorScheme: 'dark',
  })
  const page = await context.newPage()

  await page.addInitScript(() => {
    localStorage.setItem('lablog-welcome-dismissed', 'true')
    localStorage.setItem('lablog-theme', 'dark')
  })

  await page.goto(BASE, { waitUntil: 'networkidle', timeout: 60_000 })
  // wait shell
  await page.locator('button[title="Nueva página"], button[title*="Nueva"]').first().waitFor({
    timeout: 30_000,
  })
  // select seeded page if visible
  const rc = page.getByText('RC lab session').first()
  if (await rc.isVisible().catch(() => false)) {
    await rc.click()
    await page.waitForTimeout(800)
  }

  // 1. Workbench main
  await shot(page, '01-workbench.png')

  // 2. Diagrams panel
  const diagramsBtn = page.locator('button[title*="Diagrama"], button:has-text("Diagramas")').first()
  // sidebar tool buttons use labels
  const diagramsTool = page.getByRole('button', { name: /Diagramas|diagrams/i }).first()
  if (await diagramsTool.isVisible().catch(() => false)) {
    await diagramsTool.click()
    await page.waitForTimeout(600)
    await shot(page, '02-diagrams-panel.png')
  } else {
    // try toolbar / panels via shortcut-like click on CircuitBoard
    await page.keyboard.press('Meta+Shift+D').catch(() => {})
    await page.keyboard.press('Control+Shift+D').catch(() => {})
    await page.waitForTimeout(500)
    await shot(page, '02-diagrams-panel.png')
  }

  // 3. Parameters if possible
  const paramsTool = page.getByRole('button', { name: /Parámetros|Parameters/i }).first()
  if (await paramsTool.isVisible().catch(() => false)) {
    await paramsTool.click()
    await page.waitForTimeout(500)
    await shot(page, '03-parameters-panel.png')
  }

  // 4. Settings / shortcuts
  const prefs = page
    .locator(
      'button[data-testid="settings-trigger"], button[title="Preferencias"], button[aria-label="Preferencias"]',
    )
    .first()
  if (await prefs.isVisible().catch(() => false)) {
    await prefs.click()
    await page.waitForTimeout(400)
    await shot(page, '04-settings.png')
    // open shortcuts section if present
    const shortcuts = page.getByText(/Atajos|Shortcuts|Teclado/i).first()
    if (await shortcuts.isVisible().catch(() => false)) {
      await shortcuts.click().catch(() => {})
      await page.waitForTimeout(300)
      await shot(page, '05-shortcuts.png')
    }
    await page.keyboard.press('Escape')
  }

  // 5. Command palette
  await page.keyboard.press('Meta+K').catch(() => {})
  await page.keyboard.press('Control+K').catch(() => {})
  await page.waitForTimeout(400)
  const palette = page.locator('[cmdk-root], [role="dialog"]').first()
  if (await palette.isVisible().catch(() => false)) {
    await shot(page, '06-command-palette.png')
    await page.keyboard.press('Escape')
  } else {
    await shot(page, '06-command-palette.png')
  }

  // 6. Lab mode
  const lab = page.getByRole('button', { name: /Laboratorio|Lab/i }).first()
  if (await lab.isVisible().catch(() => false)) {
    await lab.click()
    await page.waitForTimeout(800)
    await shot(page, '07-lab-mode.png')
    // back
    const back = page.getByRole('button', { name: /Volver al editor|editor/i }).first()
    if (await back.isVisible().catch(() => false)) await back.click()
    await page.waitForTimeout(500)
  }

  // 7. Cells panel
  const cells = page.getByRole('button', { name: /Celdas|Cells/i }).first()
  if (await cells.isVisible().catch(() => false)) {
    await cells.click()
    await page.waitForTimeout(500)
    await shot(page, '08-cells-panel.png')
  }

  await browser.close()
  console.log('done →', OUT)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
