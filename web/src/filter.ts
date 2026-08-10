import type { Filters, PlotItem } from './types'
import { normalizeList } from './types'

function parseItemDate(s?: string): Date | null {
  if (!s) return null
  const raw = s.trim().slice(0, 10)
  const d = new Date(raw + 'T00:00:00')
  return Number.isNaN(d.getTime()) ? null : d
}

function parseFilterDate(s?: string | null): Date | null {
  if (!s) return null
  const d = new Date(s.trim().slice(0, 10) + 'T00:00:00')
  return Number.isNaN(d.getTime()) ? null : d
}

export type FilterMatchers = {
  /** Optional: localize operator CN name for substring search (e.g. EN UI). */
  operatorLabel?: (cnName: string) => string
}

export function matchesFilters(
  item: PlotItem,
  filters: Filters,
  matchers: FilterMatchers = {},
): boolean {
  const itemDate = parseItemDate(item.date)
  const start = parseFilterDate(filters.start)
  const end = parseFilterDate(filters.end)
  if (start && itemDate && itemDate < start) return false
  if (end && itemDate && itemDate > end) return false

  const types = filters.class
  if (types && types.length) {
    if (!item.class || !types.includes(item.class)) return false
  }

  const countries = filters.country
  if (countries && countries.length) {
    const itemC = normalizeList(item.country)
    const mode = filters.country_mode || 'any'
    if (mode === 'any') {
      if (!countries.some((c) => itemC.includes(c))) return false
    } else if (!countries.every((c) => itemC.includes(c))) {
      return false
    }
  }

  const opSearch = filters.new_operator?.trim()
  if (opSearch) {
    const q = opSearch.toLowerCase()
    const ops = normalizeList(item.new_operator)
    const found = ops.some((o) => {
      if (o.toLowerCase().includes(q)) return true
      const labeled = matchers.operatorLabel?.(o)
      return !!labeled && labeled.toLowerCase().includes(q)
    })
    if (!found) return false
  }

  const stages = filters.plot_stage
  if (stages && stages.length) {
    const stage = Number(item.plot_stage)
    if (!stages.includes(stage)) return false
  }

  const powers = filters.related_power
  if (powers && powers.length) {
    const itemP = normalizeList(item.related_power)
    const mode = filters.power_mode || 'any'
    if (mode === 'any') {
      if (!powers.some((p) => itemP.includes(p))) return false
    } else if (!powers.every((p) => itemP.includes(p))) {
      return false
    }
  }

  const rplots = filters.related_plot
  if (rplots && rplots.length) {
    const itemR = normalizeList(item.related_plot)
    const mode = filters.rplot_mode || 'any'
    if (mode === 'any') {
      if (!rplots.some((r) => itemR.includes(r))) return false
    } else if (!rplots.every((r) => itemR.includes(r))) {
      return false
    }
  }

  return true
}

export function collectFilterOptions(plots: PlotItem[]) {
  const classes = new Set<string>()
  const countries = new Set<string>()
  const stages = new Set<number>()
  const powers = new Set<string>()
  const rplots = new Set<string>()
  const years = new Set<number>()

  for (const p of plots) {
    if (p.class) classes.add(String(p.class))
    for (const c of normalizeList(p.country)) countries.add(c)
    if (p.plot_stage != null && p.plot_stage !== '') {
      const n = Number(p.plot_stage)
      if (!Number.isNaN(n)) stages.add(n)
    }
    for (const x of normalizeList(p.related_power)) powers.add(x)
    for (const x of normalizeList(p.related_plot)) rplots.add(x)
    if (p.date && p.date.length >= 4) {
      const y = Number(p.date.slice(0, 4))
      if (!Number.isNaN(y)) years.add(y)
    }
  }

  return {
    classes: [...classes].sort(),
    countries: [...countries].sort(),
    stages: [...stages].sort((a, b) => a - b),
    powers: [...powers].sort(),
    rplots: [...rplots].sort(),
    years: [...years].sort((a, b) => a - b),
  }
}
