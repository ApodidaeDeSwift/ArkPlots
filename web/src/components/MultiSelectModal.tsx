import { useState } from 'react'
import { useT } from '../i18n'

type Mode = 'any' | 'all'

type Props = {
  title: string
  options: string[]
  selected: string[]
  onChange: (next: string[], mode?: Mode) => void
  showMode?: boolean
  mode?: Mode
  /** Optional display resolver (e.g. class code → label). */
  resolveLabel?: (opt: string) => string
  onClose: () => void
}

export function MultiSelectModal({
  title,
  options,
  selected,
  onChange,
  showMode,
  mode = 'any',
  resolveLabel,
  onClose,
}: Props) {
  const t = useT()
  const labelOf = resolveLabel || ((opt: string) => opt)
  const [local, setLocal] = useState<Set<string>>(() => new Set(selected))
  const [localMode, setLocalMode] = useState<Mode>(mode)

  const toggle = (opt: string) => {
    setLocal((prev) => {
      const next = new Set(prev)
      if (next.has(opt)) next.delete(opt)
      else next.add(opt)
      return next
    })
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>{title}</h3>
        <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
          <button type="button" className="btn btn-ghost" onClick={() => setLocal(new Set(options))}>
            {t('actions.selectAll')}
          </button>
          <button type="button" className="btn btn-ghost" onClick={() => setLocal(new Set())}>
            {t('actions.selectNone')}
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() =>
              setLocal((prev) => {
                const next = new Set<string>()
                for (const o of options) if (!prev.has(o)) next.add(o)
                return next
              })
            }
          >
            {t('actions.invert')}
          </button>
        </div>
        {showMode && (
          <div className="toggles" style={{ marginBottom: 10 }}>
            <label>
              <input
                type="radio"
                checked={localMode === 'any'}
                onChange={() => setLocalMode('any')}
              />{' '}
              {t('filter.matchAny')}
            </label>
            <label>
              <input
                type="radio"
                checked={localMode === 'all'}
                onChange={() => setLocalMode('all')}
              />{' '}
              {t('filter.matchAll')}
            </label>
          </div>
        )}
        <div className="check-grid">
          {options.map((opt) => (
            <label key={opt}>
              <input type="checkbox" checked={local.has(opt)} onChange={() => toggle(opt)} />
              <span>{labelOf(opt)}</span>
            </label>
          ))}
        </div>
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            {t('actions.cancel')}
          </button>
          <button
            type="button"
            className="btn btn-accent"
            onClick={() => {
              onChange([...local], showMode ? localMode : undefined)
              onClose()
            }}
          >
            {t('actions.confirm')}
          </button>
        </div>
      </div>
    </div>
  )
}
