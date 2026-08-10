import type { Filters } from '../types'
import { useClassLabel, useT } from '../i18n'

type Options = {
  classes: string[]
  countries: string[]
  stages: number[]
  powers: string[]
  rplots: string[]
  years: number[]
}

type Props = {
  filters: Filters
  options: Options
  operatorDraft: string
  onOperatorDraft: (v: string) => void
  onOpenSelector: (key: 'class' | 'country' | 'stage' | 'power' | 'rplot') => void
  onDateChange: (which: 'start' | 'end', part: 'y' | 'm' | 'd', value: string) => void
  dateParts: {
    start: { y: string; m: string; d: string }
    end: { y: string; m: string; d: string }
  }
}

export function FilterBar({
  filters,
  options,
  operatorDraft,
  onOperatorDraft,
  onOpenSelector,
  onDateChange,
  dateParts,
}: Props) {
  const t = useT()
  const classLabel = useClassLabel()
  const months = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0'))
  const days = Array.from({ length: 31 }, (_, i) => String(i + 1).padStart(2, '0'))

  const countLabel = (labelKey: 'filter.class' | 'filter.country' | 'filter.stage' | 'filter.relatedPower' | 'filter.relatedPlot', n: number) =>
    t('filter.countLabel', { label: t(labelKey), count: n })

  return (
    <div className="filter-grid">
      <div className="filter-row full">
        <span className="filter-label">{t('filter.startDate')}</span>
        <div className="date-row">
          <select
            className="field"
            value={dateParts.start.y}
            onChange={(e) => onDateChange('start', 'y', e.target.value)}
          >
            <option value="">{t('filter.year')}</option>
            {options.years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
          <select
            className="field"
            value={dateParts.start.m}
            onChange={(e) => onDateChange('start', 'm', e.target.value)}
          >
            <option value="">{t('filter.month')}</option>
            {months.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <select
            className="field"
            value={dateParts.start.d}
            onChange={(e) => onDateChange('start', 'd', e.target.value)}
          >
            <option value="">{t('filter.day')}</option>
            {days.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="filter-row full">
        <span className="filter-label">{t('filter.endDate')}</span>
        <div className="date-row">
          <select
            className="field"
            value={dateParts.end.y}
            onChange={(e) => onDateChange('end', 'y', e.target.value)}
          >
            <option value="">{t('filter.year')}</option>
            {options.years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
          <select
            className="field"
            value={dateParts.end.m}
            onChange={(e) => onDateChange('end', 'm', e.target.value)}
          >
            <option value="">{t('filter.month')}</option>
            {months.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <select
            className="field"
            value={dateParts.end.d}
            onChange={(e) => onDateChange('end', 'd', e.target.value)}
          >
            <option value="">{t('filter.day')}</option>
            {days.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="filter-row">
        <span className="filter-label">{t('filter.class')}</span>
        <button type="button" className="btn chip-btn" onClick={() => onOpenSelector('class')}>
          {countLabel('filter.class', filters.class?.length || 0)}
        </button>
      </div>
      <div className="filter-row">
        <span className="filter-label">{t('filter.country')}</span>
        <button type="button" className="btn chip-btn" onClick={() => onOpenSelector('country')}>
          {countLabel('filter.country', filters.country?.length || 0)}
        </button>
      </div>
      <div className="filter-row">
        <span className="filter-label">{t('filter.stage')}</span>
        <button type="button" className="btn chip-btn" onClick={() => onOpenSelector('stage')}>
          {countLabel('filter.stage', filters.plot_stage?.length || 0)}
        </button>
      </div>
      <div className="filter-row">
        <span className="filter-label">{t('filter.relatedPower')}</span>
        <button type="button" className="btn chip-btn" onClick={() => onOpenSelector('power')}>
          {countLabel('filter.relatedPower', filters.related_power?.length || 0)}
        </button>
      </div>
      <div className="filter-row full">
        <span className="filter-label">{t('filter.relatedPlot')}</span>
        <button type="button" className="btn chip-btn" onClick={() => onOpenSelector('rplot')}>
          {countLabel('filter.relatedPlot', filters.related_plot?.length || 0)}
        </button>
      </div>
      <div className="filter-row full">
        <span className="filter-label">{t('filter.operator')}</span>
        <input
          className="field"
          value={operatorDraft}
          placeholder={t('filter.operatorPlaceholder')}
          onChange={(e) => onOperatorDraft(e.target.value)}
        />
      </div>
      {(filters.class?.length || 0) > 0 && (
        <div className="filter-row full empty" style={{ padding: 0 }}>
          {t('filter.selectedClasses', {
            list: (filters.class || []).map((c) => classLabel(c)).join('、'),
          })}
        </div>
      )}
    </div>
  )
}
