import type { PlotlineFile } from './types'
import { APP_VERSION } from './version'

import type { UpdateChannel } from './settings'

export type AppVersionInfo = {
  name?: string
  version: string
  channel?: string
  exe_stem?: string
  release_exe?: string
  github_repo?: string
  update_tag_prefix?: string
  update_tag?: string
  update_html_url?: string | null
  update_manifest_url?: string | null
}

export type UpdateCheckResult = {
  ok: boolean
  update_available?: boolean
  up_to_date?: boolean
  current_version?: string
  remote_version?: string
  remote_tag?: string
  remote_name?: string
  asset_name?: string | null
  asset_url?: string | null
  asset_size?: number | null
  has_asset?: boolean
  html_url?: string
  /** Markdown body of the release being offered (empty when GitHub has none). */
  release_notes?: string
  /** Post-update announcement: contents of Update.md for the installed version. */
  update_notes?: string
  warning?: string
  warning_en?: string
  frozen?: boolean
  error?: string
  message?: string
  applied?: boolean
  will_restart?: boolean
  exit_deferred?: boolean
  note?: string
  target_exe?: string
}

// ---------------------------------------------------------------------------
// Native app mode (Capacitor / Android)
//
// Packaged builds have no local Python server: plot data ships inside the
// app, read records live in localStorage, and "check for updates" becomes
// "check for newer Plotline.json upstream" (desktop keeps the exe flow).
// ---------------------------------------------------------------------------

/** True inside the Capacitor Android shell (no local server available).
 *  Defined in platform.ts so the settings layer can use it without importing
 *  this module; re-exported here to keep existing call sites unchanged. */
import { IS_NATIVE_APP } from './platform'
export { IS_NATIVE_APP }

const PLOTS_STORAGE_KEY = 'arkplots.plots.v1'
const RECORDS_STORAGE_KEY = 'arkplots.records.v1'

// ===========================================================================
// [MOBILE DATA UPDATER] — 可整体移除/重写的一段，从这里开始
//
// 移动端没有本地 Python 服务，"检查更新"就变成了"从上游拉最新的
// Plotline.json 存进 localStorage"。它依赖两个公网源（jsDelivr 优先，
// raw.githubusercontent 兜底），国内访问都不算稳定，这块的最终形态
// 由维护者决定。
//
// 如果想换掉这段实现：
//   1. 删掉本节内标了 [UPDATER] 的函数与常量（不连续的几处，见标记）
//   2. checkUpdate / applyUpdate / exitAfterUpdate 里的 IS_NATIVE_APP 分支
//      改成返回 { ok: false, error: 'unsupported' }
//   3. 可一并去掉 App.tsx 对 DATA_UPDATED_EVENT 的监听
// 其余能力（打包数据离线读取、阅读记录存本地、窄屏 UI）都不依赖它。
// ===========================================================================

/** Fired on window after a mobile data update stored fresh Plotline.json. [UPDATER] */
export const DATA_UPDATED_EVENT = 'arkplots:data-updated'

/** Upstream Plotline.json sources for the mobile data updater, tried in order. [UPDATER] */
const PLOTLINE_REMOTE_SOURCES = [
  'https://cdn.jsdelivr.net/gh/ApodidaeDeSwift/ArkPlots@APP_Release/Plotline.json',
  'https://raw.githubusercontent.com/ApodidaeDeSwift/ArkPlots/APP_Release/Plotline.json',
]

function readJsonStorage<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    return null
  }
}

function writeJsonStorage(key: string, value: unknown): void {
  localStorage.setItem(key, JSON.stringify(value))
}

/** Latest entry date in a plot file, used as the version label. [UPDATER] */
function latestPlotDate(file: PlotlineFile): string {
  let latest = ''
  for (const p of file.data || []) {
    const d = p?.date
    if (typeof d === 'string' && d > latest) latest = d
  }
  return latest
}

/** Locale sniff for the update release-notes wording. [UPDATER] */
function isZhLocale(): boolean {
  try {
    const loc = localStorage.getItem('arkplots.locale') || ''
    return !loc || loc === 'zh-CN'
  } catch {
    return true
  }
}

/** Plots actually in use on mobile: localStorage copy (online-updated) or bundled static file. */
async function loadNativePlots(): Promise<{ file: PlotlineFile; text: string }> {
  const stored = localStorage.getItem(PLOTS_STORAGE_KEY)
  if (stored) {
    try {
      return { file: JSON.parse(stored) as PlotlineFile, text: stored }
    } catch {
      /* fall through to bundled copy */
    }
  }
  const res = await fetch('Plotline.json', { cache: 'force-cache' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const text = await res.text()
  return { file: JSON.parse(text) as PlotlineFile, text }
}

/** Fetch the newest upstream Plotline.json; null when every source fails. [UPDATER] */
async function fetchRemotePlotline(): Promise<string | null> {
  for (const url of PLOTLINE_REMOTE_SOURCES) {
    try {
      const res = await fetch(`${url}?t=${Date.now()}`, { cache: 'no-store' })
      if (!res.ok) continue
      const text = await res.text()
      JSON.parse(text) as PlotlineFile // reject non-JSON payloads
      return text
    } catch {
      /* try next source */
    }
  }
  return null
}

async function nativeFetchPlots(): Promise<PlotlineFile> {
  const { file } = await loadNativePlots()
  return file
}

async function nativeFetchRecords(): Promise<Record<string, string>> {
  return readJsonStorage<Record<string, string>>(RECORDS_STORAGE_KEY) || {}
}

async function nativeSaveRecords(records: Record<string, string>): Promise<Record<string, string>> {
  writeJsonStorage(RECORDS_STORAGE_KEY, records)
  return records
}

async function nativeFetchVersion(): Promise<AppVersionInfo> {
  return {
    name: 'ArkPlots',
    version: APP_VERSION,
    channel: 'android',
    github_repo: 'ApodidaeDeSwift/ArkPlots',
    update_html_url: 'https://github.com/ApodidaeDeSwift/ArkPlots/releases',
  }
}

/**
 * Mobile update check: compare upstream Plotline.json with the copy in use.
 * [UPDATER]
 *
 * `_channel` is accepted for signature parity with the desktop check; mobile
 * data sync has no release-channel concept, so it is intentionally ignored.
 */
async function nativeCheckUpdate(
  _channel: UpdateChannel = 'release',
): Promise<UpdateCheckResult> {
  const remoteText = await fetchRemotePlotline()
  if (remoteText == null) {
    return { ok: false, error: 'network_error' }
  }
  const { file: local, text: localText } = await loadNativePlots()
  if (remoteText === localText) {
    return { ok: true, up_to_date: true, current_version: APP_VERSION }
  }
  let remote: PlotlineFile
  try {
    remote = JSON.parse(remoteText) as PlotlineFile
  } catch {
    return { ok: false, error: 'download_invalid' }
  }
  const zh = isZhLocale()
  const localCount = (local.data || []).length
  const remoteCount = (remote.data || []).length
  return {
    ok: true,
    update_available: true,
    current_version: APP_VERSION,
    remote_version: latestPlotDate(remote) || `${remoteCount}`,
    has_asset: true,
    frozen: true,
    release_notes: zh
      ? `剧情数据更新：**${localCount} → ${remoteCount} 条**（最新条目日期 ${latestPlotDate(remote) || '未知'}）。下载后立即生效，阅读记录保持不变。`
      : `Plot data update: **${localCount} → ${remoteCount} entries** (latest entry ${latestPlotDate(remote) || 'unknown'}). Applies immediately; read records are kept.`,
  }
}

/**
 * Mobile apply: store upstream Plotline.json locally, then notify. [UPDATER]
 *
 * `_channel` is accepted for signature parity and ignored (see
 * nativeCheckUpdate).
 */
async function nativeApplyUpdate(
  _channel: UpdateChannel = 'release',
): Promise<UpdateCheckResult> {
  const remoteText = await fetchRemotePlotline()
  if (remoteText == null) {
    return { ok: false, error: 'network_error' }
  }
  let remote: PlotlineFile
  try {
    remote = JSON.parse(remoteText) as PlotlineFile
  } catch {
    return { ok: false, error: 'download_invalid' }
  }
  localStorage.setItem(PLOTS_STORAGE_KEY, remoteText)
  window.dispatchEvent(new CustomEvent(DATA_UPDATED_EVENT))
  return {
    ok: true,
    applied: true,
    remote_version: latestPlotDate(remote) || `${(remote.data || []).length}`,
    note: 'data_updated',
  }
}

/** Mobile has nothing to restart after a data swap. [UPDATER] */
async function nativeExitAfterUpdate(): Promise<{ ok: boolean; will_restart?: boolean }> {
  return { ok: true, will_restart: false }
}

// ---------------------------------------------------------------------------
// HTTP backend (desktop: local Python server)
// ---------------------------------------------------------------------------

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    let detail = res.statusText
    try {
      const err = await res.json()
      detail = err.error || err.hint || detail
    } catch {
      /* ignore */
    }
    throw new Error(detail || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

/** Like jsonFetch, but returns parsed JSON even on soft HTTP errors (e.g. 502). */
async function jsonFetchSoft<T extends { error?: string; message?: string }>(
  url: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(url, init)
  let data: T | null = null
  try {
    data = (await res.json()) as T
  } catch {
    data = null
  }
  if (data && typeof data === 'object') {
    return data
  }
  if (!res.ok) {
    throw new Error(res.statusText || `HTTP ${res.status}`)
  }
  throw new Error('Empty response')
}

/** id -> relative path under site root (e.g. covers/12.png). Missing file => {}. */
export async function fetchCovers(): Promise<Record<string, string>> {
  try {
    const res = await fetch('/covers/covers.json', { cache: 'no-store' })
    if (!res.ok) return {}
    const data = (await res.json()) as unknown
    if (!data || typeof data !== 'object' || Array.isArray(data)) return {}
    const out: Record<string, string> = {}
    for (const [k, v] of Object.entries(data as Record<string, unknown>)) {
      if (v != null && String(v)) out[String(k)] = String(v)
    }
    return out
  } catch {
    return {}
  }
}

// Public API — desktop hits the local server; native apps use bundled data.

export function fetchPlots(): Promise<PlotlineFile> {
  return IS_NATIVE_APP ? nativeFetchPlots() : jsonFetch<PlotlineFile>('/api/plots')
}

export function fetchRecords(): Promise<Record<string, string>> {
  return IS_NATIVE_APP ? nativeFetchRecords() : jsonFetch<Record<string, string>>('/api/records')
}

/** Runtime version from the local server (preferred over the build-time constant). */
export async function fetchVersion(): Promise<AppVersionInfo | null> {
  try {
    return IS_NATIVE_APP
      ? await nativeFetchVersion()
      : await jsonFetch<AppVersionInfo>('/api/version', { cache: 'no-store' })
  } catch {
    return null
  }
}

/** Desktop: compare with GitHub ``APP_Ver*`` releases on the chosen channel. Mobile: compare plot data. */
export function checkUpdate(channel: UpdateChannel = 'release'): Promise<UpdateCheckResult> {
  if (IS_NATIVE_APP) return nativeCheckUpdate(channel)
  const query = channel === 'preview' ? '?channel=preview' : '?channel=release'
  return jsonFetchSoft<UpdateCheckResult>(`/api/update/check${query}`, { cache: 'no-store' })
}

/** Desktop: download the release exe and schedule a safe in-place replace.
 *
 * Mobile: store updated Plotline.json; `deferExit` and `channel` have no
 * meaning there.
 */
export function applyUpdate(
  restart = true,
  deferExit = true,
  channel: UpdateChannel = 'release',
): Promise<UpdateCheckResult> {
  if (IS_NATIVE_APP) return nativeApplyUpdate(channel)
  return jsonFetchSoft<UpdateCheckResult>('/api/update/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ restart, defer_exit: deferExit, channel }),
  })
}

/** Desktop: finish a deferred update by closing this process. Mobile: no-op. */
export function exitAfterUpdate(): Promise<{ ok: boolean; error?: string; will_restart?: boolean }> {
  return IS_NATIVE_APP
    ? nativeExitAfterUpdate()
    : jsonFetchSoft<{ ok: boolean; error?: string; will_restart?: boolean }>(
        '/api/update/exit',
        { method: 'POST' },
      )
}

export function saveRecords(records: Record<string, string>): Promise<Record<string, string>> {
  return IS_NATIVE_APP
    ? nativeSaveRecords(records)
    : jsonFetch<Record<string, string>>('/api/records', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(records),
      })
}
