import type { PlotlineFile } from './types'

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

export function fetchPlots() {
  return jsonFetch<PlotlineFile>('/api/plots')
}

export function fetchRecords() {
  return jsonFetch<Record<string, string>>('/api/records')
}

/** Runtime version from the local server (preferred over the build-time constant). */
export async function fetchVersion(): Promise<AppVersionInfo | null> {
  try {
    return await jsonFetch<AppVersionInfo>('/api/version', { cache: 'no-store' })
  } catch {
    return null
  }
}

/** Compare local build with GitHub ``APP_Ver*`` releases on the chosen channel. */
export function checkUpdate(channel: UpdateChannel) {
  const query = channel === 'preview' ? '?channel=preview' : '?channel=release'
  return jsonFetchSoft<UpdateCheckResult>(`/api/update/check${query}`, { cache: 'no-store' })
}

/** Download the release exe and schedule a safe in-place replace (packaged builds only).

`deferExit` keeps the process alive so the UI can show release notes before restart.
 */
export function applyUpdate(restart = true, deferExit = true, channel: UpdateChannel = 'release') {
  return jsonFetchSoft<UpdateCheckResult>('/api/update/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ restart, defer_exit: deferExit, channel }),
  })
}

/** Finish a deferred update by closing this process so the swapper can restart it. */
export function exitAfterUpdate() {
  return jsonFetchSoft<{ ok: boolean; error?: string; will_restart?: boolean }>(
    '/api/update/exit',
    { method: 'POST' },
  )
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

export function saveRecords(records: Record<string, string>) {
  return jsonFetch<Record<string, string>>('/api/records', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(records),
  })
}
