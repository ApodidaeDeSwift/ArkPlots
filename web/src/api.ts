import type { PlotlineFile } from './types'

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

export function fetchPlots() {
  return jsonFetch<PlotlineFile>('/api/plots')
}

export function fetchRecords() {
  return jsonFetch<Record<string, string>>('/api/records')
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
