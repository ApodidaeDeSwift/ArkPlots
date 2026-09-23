import { useEffect, useState } from 'react'
import { fetchVersion } from '../api'
import { useT } from '../i18n'
import type { DisplaySettings } from '../settings'
import { APP_VERSION } from '../version'

type Props = {
  settings: DisplaySettings
  onChange: (next: DisplaySettings) => void
  onClose: () => void
}

export function SettingsModal({ settings, onChange, onClose }: Props) {
  const t = useT()
  const [updateNote, setUpdateNote] = useState(false)
  const [supportOpen, setSupportOpen] = useState(false)
  const [versionLabel, setVersionLabel] = useState(APP_VERSION)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      const info = await fetchVersion()
      if (cancelled) return
      if (info?.version) setVersionLabel(String(info.version))
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const toggle = (key: keyof DisplaySettings) => {
    onChange({ ...settings, [key]: !settings[key] })
  }

  return (
    <>
      <div className="modal-backdrop" onClick={onClose}>
        <div
          className="modal settings-modal"
          onClick={(e) => e.stopPropagation()}
          role="dialog"
          aria-labelledby="settings-title"
        >
          <h3 id="settings-title">{t('settings.title')}</h3>

          <section className="settings-section">
            <h4>{t('settings.display')}</h4>
            <div className="settings-checks">
              <label>
                <input
                  type="checkbox"
                  checked={settings.showCover}
                  onChange={() => toggle('showCover')}
                />
                {t('settings.showCover')}
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={settings.showReason}
                  onChange={() => toggle('showReason')}
                />
                {t('settings.showReason')}
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={settings.showNecessary}
                  onChange={() => toggle('showNecessary')}
                />
                {t('settings.showNecessary')}
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={settings.showOptional}
                  onChange={() => toggle('showOptional')}
                />
                {t('settings.showOptional')}
              </label>
            </div>
          </section>

          <section className="settings-section">
            <h4>{t('version.label')}</h4>
            <div className="settings-version">
              {t('version.current', { version: versionLabel })}
            </div>
            <button type="button" className="btn" onClick={() => setUpdateNote(true)}>
              {t('version.check')}
            </button>
            {updateNote && <div className="settings-note">{t('version.unavailable')}</div>}
          </section>

          <section className="settings-section">
            <h4>{t('support.title')}</h4>
            <button type="button" className="btn" onClick={() => setSupportOpen(true)}>
              {t('support.open')}
            </button>
          </section>

          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              {t('actions.close')}
            </button>
          </div>
        </div>
      </div>

      {supportOpen && (
        <div
          className="modal-backdrop modal-backdrop-front"
          onClick={() => setSupportOpen(false)}
        >
          <div
            className="modal"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-labelledby="support-title"
          >
            <h3 id="support-title">{t('support.title')}</h3>
            <p className="support-copy">{t('support.body')}</p>
            <p className="support-thanks">{t('support.thanks')}</p>
            <img className="support-image" src="/coffee.png" alt={t('support.imageAlt')} />
            <div className="modal-actions">
              <button type="button" className="btn btn-ghost" onClick={() => setSupportOpen(false)}>
                {t('actions.close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
