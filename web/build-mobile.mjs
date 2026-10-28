// Mobile (Android/Capacitor) web build: prepare inputs + vite build + post-process dist.
// - Copies the repo-root Plotline.json into web/public so the APK ships story
//   data (nothing is committed; the copy is regenerated on every build).
// - Optional --covers <dir>: temporarily applies a cover-image override
//   directory (e.g. downsized jpgs) to web/public/covers for a smaller APK.
//   Omit it to build with the upstream covers as-is.
// - Drops the Google Fonts <link> (unreachable in CN; WebView would wait on it
//   and fall back anyway) so first render is fully offline.
// Usage:
//   node build-mobile.mjs [--covers <dir>] [--with-shim]
//   (--with-shim fakes window.Capacitor for desktop preview testing of the
//   native code path.)
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

const root = new URL('.', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')
const withShim = process.argv.includes('--with-shim')

// ---- inputs ---------------------------------------------------------------
const repoRoot = path.resolve(root, '..')

// 1) Story data: root Plotline.json -> web/public/Plotline.json (regenerated).
const plotlineSrc = path.join(repoRoot, 'Plotline.json')
const plotlineDst = path.join(root, 'public', 'Plotline.json')
fs.copyFileSync(plotlineSrc, plotlineDst)
console.log('plotline copied ->', path.relative(repoRoot, plotlineDst))

// 2) Optional cover override (--covers <dir> with images + covers.json).
const coversIdx = process.argv.indexOf('--covers')
if (coversIdx !== -1) {
  const dir = process.argv[coversIdx + 1]
  if (!dir || !fs.existsSync(dir)) {
    console.error('--covers directory not found:', dir)
    process.exit(1)
  }
  const dst = path.join(root, 'public', 'covers')
  fs.rmSync(dst, { recursive: true, force: true })
  fs.cpSync(dir, dst, { recursive: true })
  console.log('covers override applied from', path.resolve(dir))
}

// ---- build ----------------------------------------------------------------
execFileSync('cmd', ['/c', 'npm', 'run', 'build'], { cwd: root, stdio: 'inherit' })

const idx = `${root}dist/index.html`.replaceAll('/', '\\')
let html = fs.readFileSync(`${root}dist/index.html`, 'utf8')

const before = html
html = html.replace(
  /\s*<link\s+rel="stylesheet"\s+href="https:\/\/fonts\.googleapis\.com[^>]*>/,
  '',
)
if (withShim) {
  html = html.replace(
    /<head>/,
    '<head><script>window.Capacitor = { isNativePlatform: () => true };</script>',
  )
}
fs.writeFileSync(`${root}dist/index.html`, html)
console.log(
  'fonts link removed:', before !== html || withShim ? 'yes' : 'CHECK (not found)',
  '| shim:', withShim ? 'injected' : 'no',
)
console.log('MOBILE_BUILD_DONE', idx)
