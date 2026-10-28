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

const w = typeof window !== 'undefined'
  ? (window as unknown as { Capacitor?: { isNativePlatform?: () => boolean } })
  : undefined
/** True inside the Capacitor Android shell (no local server available). */
export const IS_NATIVE_APP = !!w?.Capacitor?.isNativePlatform?.()

const PLOTS_STORAGE_KEY = 'arkplots.plots.v1'
const RECORDS_STORAGE_KEY = 'arkplots.records.v1'
/** Fired on window after a mobile data update stored fresh Plotline.json. */
export const DATA_UPDATED_EVENT = 'arkplots:data-updated'

/** Upstream Plotline.json sources for the mobile data updater, tried in order. */
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

function latestPlotDate(file: PlotlineFile): string {
  let latest = ''
  for (const p of file.data || []) {
    const d = p?.date
    if (typeof d === 'string' && d > latest) latest = d
  }
  return latest
}

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

/** Fetch the newest upstream Plotline.json; returns raw text or null when all sources fail. */
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

/** Mobile update check: compare upstream Plotline.json with the copy in use. */
async function nativeCheckUpdate(): Promise<UpdateCheckResult> {
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

/** Mobile apply: store upstream Plotline.json locally, then notify listeners. */
async function nativeApplyUpdate(): Promise<UpdateCheckResult> {
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
  if (IS_NATIVE_APP) return nativeCheckUpdate()
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
  if (IS_NATIVE_APP) return nativeApplyUpdate()
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
