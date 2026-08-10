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

export function saveRecords(records: Record<string, string>) {
  return jsonFetch<Record<string, string>>('/api/records', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(records),
  })
}
