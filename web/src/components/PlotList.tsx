import type { MouseEvent } from 'react'
import type { PlotItem } from '../types'
import { normalizeList } from '../types'
import {
  useClassLabel,
  useI18n,
  useLocalizedList,
  usePlotName,
  useStatusLabel,
  useT,
} from '../i18n'

type Props = {
  items: PlotItem[]
  records: Record<string, string>
  selectedIds: Set<string>
  activeId: string | null
  multiMode: boolean
  onSelect: (id: string, e: MouseEvent) => void
  onToggleCheck: (id: string) => void
}

export function PlotList({
  items,
  records,
  selectedIds,
  activeId,
  multiMode,
  onSelect,
  onToggleCheck,
}: Props) {
  const t = useT()
  const { locale } = useI18n()
  const statusLabel = useStatusLabel()
  const classLabel = useClassLabel()
  const plotName = usePlotName()
  const lists = useLocalizedList()
  const sep = locale === 'zh-CN' ? '、' : ', '

  if (!items.length) {
    return <div className="empty">{t('list.empty')}</div>
  }

  return (
    <div className="plot-list">
      {items.map((p) => {
        const id = String(p.id)
        const status = records[id] || '未读'
        const typeLabel = classLabel(p.class)
        const displayName = plotName(id, p.name) || t('list.unnamed')
        const line2 = [
          normalizeList(p.country).length
            ? t('list.country', {
                value: lists.countries(normalizeList(p.country), sep),
              })
            : '',
          normalizeList(p.related_power).length
            ? t('list.power', {
                value: lists.powers(normalizeList(p.related_power), sep),
              })
            : '',
          normalizeList(p.related_plot).length
            ? t('list.relatedPlot', {
                value: lists.relatedPlots(normalizeList(p.related_plot), sep),
              })
            : '',
          normalizeList(p.new_operator).length
            ? t('list.operator', {
                value: lists.operators(normalizeList(p.new_operator), sep),
              })
            : '',
        ]
          .filter(Boolean)
          .join('  |  ')

        return (
          <div
            key={id}
            className={`plot-item${activeId === id ? ' active' : ''}${selectedIds.has(id) ? ' checked' : ''}`}
            onClick={(e) => onSelect(id, e)}
          >
            <div className="plot-line1">
              {multiMode && (
                <input
                  type="checkbox"
                  checked={selectedIds.has(id)}
                  onClick={(e) => e.stopPropagation()}
                  onChange={() => onToggleCheck(id)}
                />
              )}
              <span className={`status-pill status-${status}`}>{statusLabel(status)}</span>
              <span className="plot-meta">#{id}</span>
              <span className="plot-name">{displayName}</span>
              {typeLabel && <span className="plot-meta">{typeLabel}</span>}
              {p.date && <span className="plot-meta">{p.date}</span>}
              {p.plot_stage != null && p.plot_stage !== '' && (
                <span className="plot-meta">
                  {t('list.stage', { value: String(p.plot_stage) })}
                </span>
              )}
            </div>
            {line2 && <div className="plot-line2">{line2}</div>}
          </div>
        )
      })}
    </div>
  )
}
