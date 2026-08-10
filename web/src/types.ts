export type ReadStatus = '未读' | '计划读' | '正在读' | '已读'

export type PreplotRef =
  | number
  | string
  | {
      id?: number | string
      pid?: number | string
      plot_id?: number | string
      ID?: number | string
      Id?: number | string
      reason?: string
    }

export type VideoEntry = {
  name?: string
  title?: string
  label?: string
  url?: string
  link?: string
  href?: string
}

export type PlotItem = {
  id: number | string
  name?: string
  date?: string
  class?: string
  country?: string | string[]
  new_operator?: string | string[]
  plot_stage?: number | string
  related_power?: string | string[]
  related_plot?: string | string[]
  description?: string
  necessary_plot?: PreplotRef[]
  optional_plot?: PreplotRef[]
  Videos?: VideoEntry[] | Record<string, string> | string
  videos?: VideoEntry[] | Record<string, string> | string
  Video?: VideoEntry[] | Record<string, string> | string
}

export type PlotlineFile = {
  name?: string
  description?: string
  data: PlotItem[]
}

export type Filters = {
  start?: string | null
  end?: string | null
  class?: string[]
  country?: string[]
  country_mode?: 'any' | 'all'
  new_operator?: string
  plot_stage?: number[]
  related_power?: string[]
  power_mode?: 'any' | 'all'
  related_plot?: string[]
  rplot_mode?: 'any' | 'all'
}

/**
 * Canonical read-status values persisted in Read_record.json.
 * Keep these stable; translate only in the UI via i18n status.* keys.
 */
export const READ_STATUSES: ReadStatus[] = ['未读', '计划读', '正在读', '已读']

/** Canonical class codes used in Plotline.json (not localized). */
export const CLASS_CODES = [
  'main',
  'sidestory',
  'interlude',
  'ministory',
  'manga',
  'anime',
  'rougelike',
  'RA',
  'other',
] as const

export function normalizeList(v: unknown): string[] {
  if (v == null) return []
  if (Array.isArray(v)) return v.filter((x) => x != null).map(String)
  return [String(v)]
}

export function extractPreplotId(entry: PreplotRef | null | undefined): string | null {
  if (entry == null) return null
  if (typeof entry === 'number' || typeof entry === 'string') {
    const s = String(entry)
    return s || null
  }
  const id = entry.id ?? entry.pid ?? entry.plot_id ?? entry.ID ?? entry.Id
  if (id == null || id === '') return null
  return String(id)
}

export function extractPreplotReason(entry: PreplotRef): string {
  if (entry && typeof entry === 'object' && 'reason' in entry) {
    return String(entry.reason || '')
  }
  return ''
}

export function parseVideos(
  item: PlotItem,
  defaultName = 'video',
): { name: string; url: string }[] {
  const vids = item.Videos ?? item.videos ?? item.Video
  const out: { name: string; url: string }[] = []
  if (!vids) return out
  if (typeof vids === 'string') {
    out.push({ name: vids, url: vids })
    return out
  }
  if (!Array.isArray(vids) && typeof vids === 'object') {
    for (const [name, url] of Object.entries(vids)) {
      out.push({ name: String(name), url: String(url) })
    }
    return out
  }
  for (const v of vids) {
    if (typeof v === 'string') {
      out.push({ name: v, url: v })
    } else if (v && typeof v === 'object') {
      const name = v.name || v.title || v.label || defaultName
      const url = v.url || v.link || v.href
      if (url) out.push({ name: String(name), url: String(url) })
    }
  }
  return out
}
