import { useState } from 'react'
import { READ_STATUSES, type ReadStatus } from '../types'
import { useStatusLabel, useT } from '../i18n'

type Props = {
  title: string
  initial?: ReadStatus
  onSave: (status: ReadStatus) => void
  onClose: () => void
}

export function StatusModal({ title, initial = '已读', onSave, onClose }: Props) {
  const t = useT()
  const statusLabel = useStatusLabel()
  const [status, setStatus] = useState<ReadStatus>(initial)
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>{title}</h3>
        <label className="filter-label">{t('status.label')}</label>
        <select
          className="field"
          value={status}
          onChange={(e) => setStatus(e.target.value as ReadStatus)}
        >
          {READ_STATUSES.map((s) => (
            <option key={s} value={s}>
              {statusLabel(s)}
            </option>
          ))}
        </select>
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            {t('actions.cancel')}
          </button>
          <button
            type="button"
            className="btn btn-accent"
            onClick={() => {
              onSave(status)
              onClose()
            }}
          >
            {t('actions.save')}
          </button>
        </div>
      </div>
    </div>
  )
}
