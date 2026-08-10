import type { PlotItem } from '../types'
import {
  extractPreplotId,
  extractPreplotReason,
  normalizeList,
} from '../types'
import {
  useClassLabel,
  useI18n,
  useLocalizedList,
  usePlotName,
  useStatusLabel,
  useT,
} from '../i18n'

type Props = {
  item: PlotItem | null
  plotsMap: Map<string, PlotItem>
  records: Record<string, string>
  canBack: boolean
  canForward: boolean
  onBack: () => void
  onForward: () => void
  onJump: (id: string) => void
  showNecessary: boolean
  showOptional: boolean
  showReason: boolean
  onToggleNecessary: (v: boolean) => void
  onToggleOptional: (v: boolean) => void
  onToggleReason: (v: boolean) => void
}

export function DetailPanel({
  item,
  plotsMap,
  records,
  canBack,
  canForward,
  onBack,
  onForward,
  onJump,
  showNecessary,
  showOptional,
  showReason,
  onToggleNecessary,
  onToggleOptional,
  onToggleReason,
}: Props) {
  const t = useT()
  const { locale } = useI18n()
  const statusLabel = useStatusLabel()
  const classLabel = useClassLabel()
  const plotName = usePlotName()
  const lists = useLocalizedList()
  const sep = locale === 'zh-CN' ? '、' : ', '
  const dash = t('detail.emDash')

  if (!item) {
    return (
      <>
        <div className="detail-toolbar">
          <button type="button" className="btn btn-ghost" disabled={!canBack} onClick={onBack}>
            ↩
          </button>
          <button type="button" className="btn btn-ghost" disabled={!canForward} onClick={onForward}>
            ↪
          </button>
          <span className="filter-label">{t('detail.history')}</span>
        </div>
        <div className="empty">{t('detail.pickHint')}</div>
      </>
    )
  }

  const id = String(item.id)
  const status = records[id] || '未读'
  const typeLabel = classLabel(item.class)
  const titleName = plotName(id, item.name)

  const renderPreplots = (list: PlotItem['necessary_plot'], title: string) => {
    const entries = list || []
    if (!entries.length) return null
    return (
      <div className="preplot-block">
        <h4>{title}</h4>
        {entries.map((entry, idx) => {
          const pid = extractPreplotId(entry)
          if (!pid) return null
          const target = plotsMap.get(pid)
          const name = plotName(pid, target?.name) || `ID:${pid}`
          const st = records[pid] || '未读'
          const reason = extractPreplotReason(entry)
          return (
            <div className="preplot-item" key={`${pid}-${idx}`}>
              <span className={`status-pill status-${st}`}>{statusLabel(st)}</span>
              <button type="button" className="preplot-link" onClick={() => onJump(pid)}>
                {name}
              </button>
              {showReason && reason && <div className="preplot-reason">{reason}</div>}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="detail-fade" key={id}>
      <div className="detail-toolbar">
        <button type="button" className="btn btn-ghost" disabled={!canBack} onClick={onBack}>
          ↩
        </button>
        <button type="button" className="btn btn-ghost" disabled={!canForward} onClick={onForward}>
          ↪
        </button>
        <span className="filter-label">{t('detail.history')}</span>
      </div>
      <div className="toggles">
        <label>
          <input
            type="checkbox"
            checked={showNecessary}
            onChange={(e) => onToggleNecessary(e.target.checked)}
          />{' '}
          {t('detail.necessary')}
        </label>
        <label>
          <input
            type="checkbox"
            checked={showOptional}
            onChange={(e) => onToggleOptional(e.target.checked)}
          />{' '}
          {t('detail.optional')}
        </label>
        <label>
          <input
            type="checkbox"
            checked={showReason}
            onChange={(e) => onToggleReason(e.target.checked)}
          />{' '}
          {t('detail.showReason')}
        </label>
      </div>
      <h2 className="detail-title">{titleName}</h2>
      <div className="detail-kv">
        <div>
          <span>{t('detail.status')}</span>
          <span className={`status-pill status-${status}`}>{statusLabel(status)}</span>
        </div>
        <div>
          <span>ID</span>
          <span>{id}</span>
        </div>
        <div>
          <span>{t('detail.type')}</span>
          <span>{typeLabel || dash}</span>
        </div>
        <div>
          <span>{t('detail.date')}</span>
          <span>{item.date || dash}</span>
        </div>
        <div>
          <span>{t('detail.stage')}</span>
          <span>{item.plot_stage ?? dash}</span>
        </div>
        <div>
          <span>{t('detail.country')}</span>
          <span>
            {lists.countries(normalizeList(item.country), sep) || dash}
          </span>
        </div>
        <div>
          <span>{t('detail.power')}</span>
          <span>
            {lists.powers(normalizeList(item.related_power), sep) || dash}
          </span>
        </div>
        <div>
          <span>{t('detail.relatedPlot')}</span>
          <span>
            {lists.relatedPlots(normalizeList(item.related_plot), sep) || dash}
          </span>
        </div>
        <div>
          <span>{t('detail.operator')}</span>
          <span>
            {lists.operators(normalizeList(item.new_operator), sep) || dash}
          </span>
        </div>
        <div>
          <span>{t('detail.description')}</span>
          <span>{item.description || dash}</span>
        </div>
      </div>
      {showNecessary && renderPreplots(item.necessary_plot, t('detail.necessary'))}
      {showOptional && renderPreplots(item.optional_plot, t('detail.optional'))}
    </div>
  )
}
