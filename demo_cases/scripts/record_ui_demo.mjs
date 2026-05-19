import { chromium } from 'playwright'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { existsSync, mkdirSync, rmSync } from 'node:fs'
import { readdir, readFile, rm, writeFile } from 'node:fs/promises'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const demoRoot = path.resolve(__dirname, '..')
const projectRoot = path.resolve(demoRoot, '..')
const baseUrl = process.env.DEMO_FRONTEND_URL || 'http://127.0.0.1:3003'
const backendUrl = process.env.DEMO_BACKEND_URL || 'http://127.0.0.1:8000'
const pdfDocPath = process.env.DEMO_PDF_DOC || path.join(
  process.env.HOME || '',
  'Desktop',
  'Multimodal fusion-driven precision irrigation decision model for greenhouse cucumber integrating enhanced YOLO11n and TSMixer.pdf',
)
const sampleImagePath = process.env.DEMO_IMAGE_PATH || path.join(
  demoRoot,
  'images',
  'cucumber_monitor_original_0420.jpg',
)
const recordingsDir = path.join(demoRoot, 'recordings')
const screenshotsDir = path.join(demoRoot, 'screenshots')
const userLiteratureDir = path.join(projectRoot, 'data', 'user_literature')

mkdirSync(recordingsDir, { recursive: true })
mkdirSync(screenshotsDir, { recursive: true })
if (process.env.DEMO_KEEP_OLD_RECORDINGS !== '1') {
  rmSync(recordingsDir, { recursive: true, force: true })
  rmSync(screenshotsDir, { recursive: true, force: true })
  mkdirSync(recordingsDir, { recursive: true })
  mkdirSync(screenshotsDir, { recursive: true })
}

const markersPath = path.join(recordingsDir, 'recording-markers.json')
let recordingStartedAt = 0
const markers = []

function mark(name, extra = {}) {
  if (!recordingStartedAt) return
  markers.push({
    name,
    seconds: Number(((Date.now() - recordingStartedAt) / 1000).toFixed(3)),
    ...extra,
  })
}

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function ensureOk(response, label) {
  if (!response?.ok()) {
    throw new Error(`${label} failed: ${response?.status()} ${response?.statusText()}`)
  }
}

async function warmEndpoint(url) {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Warm endpoint failed: ${url} -> ${response.status}`)
  }
  return response
}

async function removeExistingPdfUpload() {
  const filename = path.basename(pdfDocPath)
  if (!existsSync(pdfDocPath)) {
    throw new Error(`PDF file not found: ${pdfDocPath}`)
  }
  if (!existsSync(userLiteratureDir)) return

  const entries = await readdir(userLiteratureDir)
  for (const entry of entries) {
    if (!entry.endsWith('.metadata.json') || entry.startsWith('._')) continue
    const metadataPath = path.join(userLiteratureDir, entry)
    let metadata
    try {
      metadata = JSON.parse(await readFile(metadataPath, 'utf-8'))
    } catch {
      continue
    }
    if (metadata?.original_filename !== filename) continue

    const candidates = [
      metadataPath,
      metadata?.stored_path,
      metadata?.chunks_path,
      metadata?.assets_dir,
    ].filter(Boolean)

    for (const candidate of candidates) {
      await rm(candidate, { recursive: true, force: true })
    }
  }
}

async function prewarmDemoData() {
  await warmEndpoint(`${backendUrl}/api/health`)
  await warmEndpoint(`${backendUrl}/api/episodes/latest`)
  await warmEndpoint(`${backendUrl}/api/episodes?page=1&page_size=120`)
  await warmEndpoint(`${backendUrl}/api/stats/trend?days=7`)
  await warmEndpoint(`${backendUrl}/api/stats/trend?days=14`)
  await warmEndpoint(`${backendUrl}/api/stats/trend?days=30`)
  await warmEndpoint(`${backendUrl}/api/vision/image/1030`)
  await warmEndpoint(`${backendUrl}/api/vision/image/1031`)
  await fetch(`${backendUrl}/api/chat/history`, { method: 'DELETE' })
  await removeExistingPdfUpload()
}

async function launchBrowser() {
  const headless = process.env.DEMO_HEADLESS !== '0'
  try {
    return await chromium.launch({ headless })
  } catch (error) {
    console.warn(`默认 Chromium 不可用，尝试使用本机 Chrome: ${error.message}`)
    return chromium.launch({ channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome', headless })
  }
}

async function waitForPageReady(page) {
  await page.waitForLoadState('networkidle')
  await page.waitForFunction(() => {
    const loadingText = document.body?.innerText || ''
    return !document.querySelector('.chart-loading')
      && !document.querySelector('.glass-panel .ph-spinner')
      && !loadingText.includes('Loading history data')
      && !loadingText.includes('Loading latest episode')
      && !loadingText.includes('加载趋势数据')
  }, undefined, { timeout: 30_000 })
}

async function stabilizeScrollForRecording(page) {
  await page.addStyleTag({
    content: `
      html, body, .content-scroll, * {
        scroll-behavior: auto !important;
      }
      .content-scroll {
        overscroll-behavior: contain;
        scrollbar-gutter: stable;
      }
    `,
  })
}

async function navigateBySidebar(page, label) {
  await page.locator('.nav-item').filter({ hasText: label }).click()
  await waitForPageReady(page)
  await stabilizeScrollForRecording(page)
  await page.evaluate(() => {
    const scroller = document.querySelector('.content-scroll')
    if (scroller) scroller.scrollTop = 0
  })
}

async function jumpToSection(page, selector, offset = 0) {
  await page.evaluate(({ targetSelector, targetOffset }) => {
    const target = document.querySelector(targetSelector)
    if (!target) return
    const scroller = document.querySelector('.content-scroll')
    if (scroller) {
      const targetTop = target.getBoundingClientRect().top - scroller.getBoundingClientRect().top
      scroller.style.scrollBehavior = 'auto'
      scroller.scrollTop = Math.max(0, scroller.scrollTop + targetTop + targetOffset)
      return
    }
    const top = target.getBoundingClientRect().top + window.scrollY + targetOffset
    document.documentElement.style.scrollBehavior = 'auto'
    document.body.style.scrollBehavior = 'auto'
    window.scrollTo(0, Math.max(0, top))
  }, { targetSelector: selector, targetOffset: offset })
  await delay(400)
}

async function showKnowledgeUploadPanel(page) {
  await page.evaluate(() => {
    const chatScroller = document.querySelector('.knowledge-chat-container .chat-messages')
    if (chatScroller) {
      chatScroller.style.scrollBehavior = 'auto'
      chatScroller.scrollTop = 0
    }
    const pageScroller = document.querySelector('.content-scroll')
    if (pageScroller) {
      pageScroller.style.scrollBehavior = 'auto'
      pageScroller.scrollTop = 0
    }
  })
  await delay(600)
}

async function viewportScreenshot(page, filename) {
  await page.screenshot({ path: path.join(screenshotsDir, filename), fullPage: false })
}

async function closeFloatingChat(page) {
  const closeButton = page.locator('.chat-panel--open .chat-panel__action[title="关闭"]')
  if (await closeButton.count()) {
    await closeButton.click()
    await delay(400)
  }
}

async function waitForKnowledgeAnswer(page, options = {}) {
  const minAgentMessages = options.minAgentMessages || 1
  await page.waitForFunction((count) => {
    const root = document.querySelector('.knowledge-chat-container') || document
    const streaming = root.querySelector('.chat-message__cursor')
      || root.querySelector('.chat-message__typing')
      || root.querySelector('.chat-typing')
      || root.querySelector('.chat-input-btn--send .ph-spinner')
    const agentMessages = root.querySelectorAll('.chat-msg--agent .chat-rich').length
    return !streaming && agentMessages >= count
  }, minAgentMessages, { timeout: options.timeout || 90_000 })
}

async function waitForSideChatAnswer(page) {
  await page.waitForFunction(() => {
    const panel = document.querySelector('.chat-panel--open')
    const streaming = document.querySelector('.chat-panel .chat-message__cursor')
      || document.querySelector('.chat-panel .chat-message__typing')
      || document.querySelector('.chat-panel .chat-typing')
    const messages = document.querySelectorAll('.chat-panel .chat-message--assistant').length
      || document.querySelectorAll('.chat-panel .chat-msg--agent').length
    return panel && !streaming && messages >= 1
  }, undefined, { timeout: 90_000 })
}

async function waitForVisionResult(page) {
  await page.waitForFunction(() => {
    const text = document.body?.innerText || ''
    const resultImage = document.querySelector('.image-viewer img[src^="data:image"]')
      || document.querySelector('.image-viewer__image img[src^="data:image"]')
    return text.includes('分割指标')
      && text.includes('总实例数')
      && text.includes('处理时间')
      && !!resultImage
      && !document.querySelector('.image-upload__loading')
  }, undefined, { timeout: 120_000 })
}

async function waitForPredictionResult(page) {
  await page.waitForFunction(() => {
    const text = document.body?.innerText || ''
    return text.includes('预测时间:')
      && text.includes('视觉分析结果')
      && !!document.querySelector('.predict-page__visualization img')
      && !document.querySelector('.prediction-result--loading')
      && !document.querySelector('.image-upload__loading')
  }, undefined, { timeout: 120_000 })
}

async function waitForPdfUploadIndexed(page) {
  const filename = path.basename(pdfDocPath)
  await page.waitForFunction((expectedFilename) => {
    const text = document.body?.innerText || ''
    return text.includes(expectedFilename)
      && text.includes('chunks')
      && (text.includes('indexed') || text.includes('fallback_indexed'))
      && !text.includes('上传中')
      && !text.includes('服务端索引中')
  }, filename, { timeout: 600_000 })
}

await prewarmDemoData()

const browser = await launchBrowser()
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: {
    dir: recordingsDir,
    size: { width: 1440, height: 900 },
  },
})
recordingStartedAt = Date.now()
const page = await context.newPage()
mark('recording_start')

try {
  await page.goto(baseUrl, { waitUntil: 'networkidle' })
  await stabilizeScrollForRecording(page)
  await waitForPageReady(page)
  mark('dashboard_top_ready')
  await page.getByRole('button', { name: '14D' }).click()
  await delay(500)
  await page.getByRole('button', { name: '7D' }).click()
  await delay(5000)
  await viewportScreenshot(page, '01-dashboard-top.png')

  await jumpToSection(page, '.grid-charts', -24)
  await delay(5000)
  await viewportScreenshot(page, '02-dashboard-bottom.png')

  await navigateBySidebar(page, '今日决策链')
  mark('decision_chain_ready')
  await delay(2500)
  await jumpToSection(page, '.final-decision', -48)
  await delay(4000)
  await viewportScreenshot(page, '03-decision-chain.png')

  await navigateBySidebar(page, '灌水预测')
  await page.locator('input[type="file"]').first().setInputFiles(sampleImagePath)
  await page.locator('.env-form__date').fill('2024-10-31')
  await page.locator('.env-form__input').fill('42000')
  mark('predict_submit')
  await page.getByRole('button', { name: /开始预测/ }).click()
  await waitForPredictionResult(page)
  mark('predict_result_ready')
  await delay(5000)
  await viewportScreenshot(page, '04-irrigation-predict.png')

  await navigateBySidebar(page, '视觉分析')
  mark('vision_upload_start')
  await page.locator('input[type="file"]').first().setInputFiles(sampleImagePath)
  await waitForVisionResult(page)
  mark('vision_result_ready')
  await delay(5000)
  await viewportScreenshot(page, '05-vision-analysis.png')

  await navigateBySidebar(page, '数据分析')
  await page.locator('.analytics-search__input').fill('最近长势如何？灌水是否合适？有哪些注意的地方')
  await page.locator('.analytics-search__shortcut').click()
  await waitForSideChatAnswer(page)
  await delay(2500)
  await viewportScreenshot(page, '06-history-trend-question.png')
  await closeFloatingChat(page)

  await navigateBySidebar(page, '智能问答')
  const knowledgeRoot = page.locator('.knowledge-chat-container')
  const input = knowledgeRoot.locator('.chat-input-field').first()
  await input.fill('开花期最佳灌水量是多少？')
  await knowledgeRoot.locator('.chat-input-btn--send').first().click()
  await waitForKnowledgeAnswer(page, { minAgentMessages: 1 })
  const directAssetCount = await knowledgeRoot.locator('.chat-rich__asset').count()
  if (directAssetCount !== 0) {
    throw new Error(`Direct irrigation case should not render images, got ${directAssetCount}`)
  }
  await delay(2500)
  await viewportScreenshot(page, '07-knowledge-flowering-irrigation.png')

  await showKnowledgeUploadPanel(page)
  await delay(1500)
  await viewportScreenshot(page, '08-knowledge-upload-ready.png')

  mark('pdf_upload_start')
  const fileChooserPromise = page.waitForEvent('filechooser')
  await page.locator('.knowledge-upload button').click()
  const fileChooser = await fileChooserPromise
  await fileChooser.setFiles(pdfDocPath)
  await waitForPdfUploadIndexed(page)
  await showKnowledgeUploadPanel(page)
  mark('pdf_indexed_ready')
  await delay(5000)
  await viewportScreenshot(page, '08-knowledge-pdf-indexing.png')

  await input.fill('论文中的是如何进行视觉模型改进的')
  await knowledgeRoot.locator('.chat-input-btn--send').first().click()
  await waitForKnowledgeAnswer(page, { minAgentMessages: 2, timeout: 120_000 })
  await page.waitForFunction(() => {
    const root = document.querySelector('.knowledge-chat-container') || document
    return root.querySelectorAll('.chat-rich__asset img').length > 0
  }, undefined, { timeout: 30_000 })
  await delay(3500)
  await viewportScreenshot(page, '09-knowledge-paper-visual-model.png')

  await navigateBySidebar(page, '系统设置')
  await delay(3500)
  await viewportScreenshot(page, '10-settings.png')
} finally {
  await context.close()
  await browser.close()
  await writeFile(markersPath, JSON.stringify(markers, null, 2), 'utf-8')
  console.log(`录屏文件目录: ${recordingsDir}`)
  console.log(`截图文件目录: ${screenshotsDir}`)
  console.log(`录屏标记: ${markersPath}`)
  console.log(`项目根目录: ${projectRoot}`)
}
