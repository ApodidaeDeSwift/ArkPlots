import { useCallback, useEffect, useMemo, useState, type MouseEvent } from 'react'
import { fetchPlots, fetchRecords, saveRecords } from './api'
import { collectFilterOptions, matchesFilters } from './filter'
import { DetailPanel } from './components/DetailPanel'
import { FilterBar } from './components/FilterBar'
import { LanguageSwitcher } from './components/LanguageSwitcher'
import { MultiSelectModal } from './components/MultiSelectModal'
import { PlotList } from './components/PlotList'
import { RecommendPanel } from './components/RecommendPanel'
import { StatusModal } from './components/StatusModal'
import { VideoModal } from './components/VideoModal'
import {
  useClassLabel,
  useCountryLabel,
  useOperatorLabel,
  usePlotName,
  usePowerLabel,
  useRelatedPlotTagLabel,
  useT,
} from './i18n'
import type { Filters, PlotItem, ReadStatus } from './types'
import { parseVideos } from './types'
import './styles/theme.css'

type SelectorKey = 'class' | 'country' | 'stage' | 'power' | 'rplot'

function composeDate(y: string, m: string, d: string): string | null {
  if (!y) return null
  const mm = m || '01'
  const dd = d || '01'
  return `${y}-${mm}-${dd}`
}

const emptyDate = { y: '', m: '', d: '' }

export default function App() {
  const t = useT()
  const classLabel = useClassLabel()
  const countryLabel = useCountryLabel()
  const powerLabel = usePowerLabel()
  const relatedPlotTagLabel = useRelatedPlotTagLabel()
  const operatorLabel = useOperatorLabel()
  const plotName = usePlotName()
  const [plots, setPlots] = useState<PlotItem[]>([])
  const [records, setRecords] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [filters, setFilters] = useState<Filters>({})
  const [appliedFilters, setAppliedFilters] = useState<Filters>({})
  const [operatorDraft, setOperatorDraft] = useState('')
  const [dateParts, setDateParts] = useState({
    start: { ...emptyDate },
    end: { ...emptyDate },
  })

  const [multiMode, setMultiMode] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [activeId, setActiveId] = useState<string | null>(null)
  const [lastSelectedId, setLastSelectedId] = useState<string | null>(null)

  const [history, setHistory] = useState<string[]>([])
  const [historyPos, setHistoryPos] = useState(-1)
  const [suppressHistory, setSuppressHistory] = useState(false)

  const [showNecessary, setShowNecessary] = useState(true)
  const [showOptional, setShowOptional] = useState(true)
  const [showReason, setShowReason] = useState(true)

  const [selector, setSelector] = useState<SelectorKey | null>(null)
  const [statusModal, setStatusModal] = useState<'single' | 'batch' | null>(null)
  const [videoOpen, setVideoOpen] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        setLoading(true)
        const [plotFile, rec] = await Promise.all([fetchPlots(), fetchRecords()])
        if (cancelled) return
        setPlots(plotFile.data || [])
        setRecords(rec)
        setError(null)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const options = useMemo(() => collectFilterOptions(plots), [plots])
  const plotsMap = useMemo(
    () => new Map(plots.map((p) => [String(p.id), p])),
    [plots],
  )

  const filtered = useMemo(
    () =>
      plots.filter((p) =>
        matchesFilters(p, appliedFilters, { operatorLabel }),
      ),
    [plots, appliedFilters, operatorLabel],
  )

  const activeItem = activeId ? plotsMap.get(activeId) || null : null

  const openPlot = useCallback(
    (pid: string, recordHistory = true) => {
      setActiveId(pid)
      if (!recordHistory || suppressHistory) return
      setHistory((prev) => {
        const base = prev.slice(0, Math.max(0, historyPos + 1))
        if (base[base.length - 1] === pid) {
          setHistoryPos(base.length - 1)
          return base
        }
        const next = [...base, pid]
        setHistoryPos(next.length - 1)
        return next
      })
    },
    [historyPos, suppressHistory],
  )

  const applyFilters = () => {
    const next: Filters = {
      ...filters,
      new_operator: operatorDraft.trim() || undefined,
      start: composeDate(dateParts.start.y, dateParts.start.m, dateParts.start.d),
      end: composeDate(dateParts.end.y, dateParts.end.m, dateParts.end.d),
    }
    setFilters(next)
    setAppliedFilters(next)
    setSelectedIds(new Set())
    setLastSelectedId(null)
  }

  const resetFilters = () => {
    setFilters({})
    setAppliedFilters({})
    setOperatorDraft('')
    setDateParts({ start: { ...emptyDate }, end: { ...emptyDate } })
    setSelectedIds(new Set())
  }

  const persistRecords = async (next: Record<string, string>) => {
    setRecords(next)
    try {
      await saveRecords(next)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  const onSelectItem = (id: string, e: MouseEvent) => {
    if (multiMode) {
      setSelectedIds((prev) => {
        const next = new Set(prev)
        if (next.has(id)) next.delete(id)
        else next.add(id)
        return next
      })
      setLastSelectedId(id)
      openPlot(id)
      return
    }

    const ctrl = e.ctrlKey || e.metaKey
    const shift = e.shiftKey
    if (shift && lastSelectedId) {
      const ids = filtered.map((p) => String(p.id))
      const a = ids.indexOf(lastSelectedId)
      const b = ids.indexOf(id)
      if (a >= 0 && b >= 0) {
        const [lo, hi] = a < b ? [a, b] : [b, a]
        const next = new Set(selectedIds)
        for (let i = lo; i <= hi; i++) next.add(ids[i])
        setSelectedIds(next)
      }
    } else if (ctrl) {
      setSelectedIds((prev) => {
        const next = new Set(prev)
        if (next.has(id)) next.delete(id)
        else next.add(id)
        return next
      })
      setLastSelectedId(id)
    } else {
      setSelectedIds(new Set([id]))
      setLastSelectedId(id)
    }
    openPlot(id)
  }

  const jumpTo = (pid: string) => {
    openPlot(pid, true)
    setSelectedIds(new Set([pid]))
    setLastSelectedId(pid)
  }

  const historyBack = () => {
    if (historyPos <= 0) return
    const pos = historyPos - 1
    const pid = history[pos]
    setSuppressHistory(true)
    setHistoryPos(pos)
    setActiveId(pid)
    setSelectedIds(new Set([pid]))
    setSuppressHistory(false)
  }

  const historyForward = () => {
    if (historyPos >= history.length - 1) return
    const pos = historyPos + 1
    const pid = history[pos]
    setSuppressHistory(true)
    setHistoryPos(pos)
    setActiveId(pid)
    setSelectedIds(new Set([pid]))
    setSuppressHistory(false)
  }

  const onDateChange = (
    which: 'start' | 'end',
    part: 'y' | 'm' | 'd',
    value: string,
  ) => {
    setDateParts((prev) => ({
      ...prev,
      [which]: { ...prev[which], [part]: value },
    }))
  }

  const selectorConfig = (() => {
    switch (selector) {
      case 'class':
        return {
          title: t('selector.class'),
          options: options.classes,
          selected: filters.class || [],
          showMode: false as boolean,
          mode: 'any' as const,
          resolveLabel: classLabel as (opt: string) => string,
        }
      case 'country':
        return {
          title: t('selector.country'),
          options: options.countries,
          selected: filters.country || [],
          showMode: true,
          mode: filters.country_mode || 'any',
          resolveLabel: countryLabel as (opt: string) => string,
        }
      case 'stage':
        return {
          title: t('selector.stage'),
          options: options.stages.map(String),
          selected: (filters.plot_stage || []).map(String),
          showMode: false,
          mode: 'any' as const,
          resolveLabel: undefined as ((opt: string) => string) | undefined,
        }
      case 'power':
        return {
          title: t('selector.power'),
          options: options.powers,
          selected: filters.related_power || [],
          showMode: true,
          mode: filters.power_mode || 'any',
          resolveLabel: powerLabel as (opt: string) => string,
        }
      case 'rplot':
        return {
          title: t('selector.rplot'),
          options: options.rplots,
          selected: filters.related_plot || [],
          showMode: true,
          mode: filters.rplot_mode || 'any',
          resolveLabel: relatedPlotTagLabel as (opt: string) => string,
        }
      default:
        return null
    }
  })()

  if (loading) {
    return <div className="loading">{t('app.loading')}</div>
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-name">ArkPlots</div>
          <div className="brand-sub">{t('app.brandSub')}</div>
        </div>
        <div className="topbar-actions">
          <LanguageSwitcher />
          <button type="button" className="btn btn-accent" onClick={applyFilters}>
            {t('actions.filter')}
          </button>
          <button type="button" className="btn" onClick={resetFilters}>
            {t('actions.resetFilters')}
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => {
              setMultiMode((v) => !v)
              setSelectedIds(new Set())
            }}
          >
            {multiMode ? t('actions.cancelMultiSelect') : t('actions.multiSelect')}
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => setStatusModal('single')}
            disabled={!activeId}
          >
            {t('actions.setReadStatus')}
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => setStatusModal('batch')}
            disabled={!selectedIds.size}
          >
            {t('actions.batchSet')}
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => setVideoOpen(true)}
            disabled={!activeItem}
          >
            {t('actions.relatedVideos')}
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => {
              void (async () => {
                try {
                  const [plotFile, rec] = await Promise.all([fetchPlots(), fetchRecords()])
                  setPlots(plotFile.data || [])
                  setRecords(rec)
                  setError(null)
                } catch (e) {
                  setError(e instanceof Error ? e.message : String(e))
                }
              })()
            }}
          >
            {t('actions.refreshData')}
          </button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <div className="workspace">
        <section className="panel">
          <div className="panel-header">
            <span>{t('panels.filtersList')}</span>
            <span>
              {filtered.length} / {plots.length}
            </span>
          </div>
          <div className="panel-body">
            <FilterBar
              filters={filters}
              options={options}
              operatorDraft={operatorDraft}
              onOperatorDraft={setOperatorDraft}
              onOpenSelector={setSelector}
              onDateChange={onDateChange}
              dateParts={dateParts}
            />
            <PlotList
              items={filtered}
              records={records}
              selectedIds={selectedIds}
              activeId={activeId}
              multiMode={multiMode}
              onSelect={onSelectItem}
              onToggleCheck={(id) => {
                setSelectedIds((prev) => {
                  const next = new Set(prev)
                  if (next.has(id)) next.delete(id)
                  else next.add(id)
                  return next
                })
              }}
            />
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <span>{t('panels.detailPreview')}</span>
          </div>
          <div className="panel-body">
            <DetailPanel
              item={activeItem}
              plotsMap={plotsMap}
              records={records}
              canBack={historyPos > 0}
              canForward={historyPos >= 0 && historyPos < history.length - 1}
              onBack={historyBack}
              onForward={historyForward}
              onJump={jumpTo}
              showNecessary={showNecessary}
              showOptional={showOptional}
              showReason={showReason}
              onToggleNecessary={setShowNecessary}
              onToggleOptional={setShowOptional}
              onToggleReason={setShowReason}
            />
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <span>{t('panels.recommendations')}</span>
          </div>
          <div className="panel-body">
            <RecommendPanel plots={plots} records={records} onJump={jumpTo} />
          </div>
        </section>
      </div>

      {selector && selectorConfig && (
        <MultiSelectModal
          title={selectorConfig.title}
          options={selectorConfig.options}
          selected={selectorConfig.selected}
          showMode={selectorConfig.showMode}
          mode={selectorConfig.mode}
          resolveLabel={selectorConfig.resolveLabel}
          onClose={() => setSelector(null)}
          onChange={(next, mode) => {
            if (selector === 'class') {
              setFilters((f) => ({ ...f, class: next }))
            } else if (selector === 'country') {
              setFilters((f) => ({
                ...f,
                country: next,
                country_mode: mode || 'any',
              }))
            } else if (selector === 'stage') {
              setFilters((f) => ({
                ...f,
                plot_stage: next.map(Number).filter((n) => !Number.isNaN(n)),
              }))
            } else if (selector === 'power') {
              setFilters((f) => ({
                ...f,
                related_power: next,
                power_mode: mode || 'any',
              }))
            } else if (selector === 'rplot') {
              setFilters((f) => ({
                ...f,
                related_plot: next,
                rplot_mode: mode || 'any',
              }))
            }
          }}
        />
      )}

      {statusModal && (
        <StatusModal
          title={
            statusModal === 'batch' ? t('status.batchTitle') : t('status.setTitle')
          }
          initial={(activeId && (records[activeId] as ReadStatus)) || '已读'}
          onClose={() => setStatusModal(null)}
          onSave={(status) => {
            const next = { ...records }
            if (statusModal === 'batch') {
              for (const id of selectedIds) next[id] = status
            } else if (activeId) {
              next[activeId] = status
            }
            void persistRecords(next)
          }}
        />
      )}

      {videoOpen && activeItem && (
        <VideoModal
          title={plotName(activeItem.id, activeItem.name) || String(activeItem.id)}
          videos={parseVideos(activeItem, t('video.defaultName'))}
          onClose={() => setVideoOpen(false)}
        />
      )}
    </div>
  )
}
