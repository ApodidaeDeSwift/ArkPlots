import type { PlotlineFile } from './types'

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
  warning?: string
  warning_en?: string
  frozen?: boolean
  error?: string
  message?: string
  applied?: boolean
  will_restart?: boolean
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

/** Compare local build with the floating GitHub ``APP版本`` release. */
export function checkUpdate() {
  return jsonFetchSoft<UpdateCheckResult>('/api/update/check', { cache: 'no-store' })
}

/** Download the release exe and schedule a safe in-place replace (packaged builds only). */
export function applyUpdate(restart = true) {
  return jsonFetchSoft<UpdateCheckResult>('/api/update/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ restart }),
  })
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
