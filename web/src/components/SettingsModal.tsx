import { useEffect, useState } from 'react'
import { applyUpdate, checkUpdate, fetchVersion, type UpdateCheckResult } from '../api'
import { useI18n, useT } from '../i18n'
import type { DisplaySettings } from '../settings'
import { APP_VERSION } from '../version'

type Props = {
  settings: DisplaySettings
  onChange: (next: DisplaySettings) => void
  onClose: () => void
}

type UpdatePhase =
  | 'idle'
  | 'checking'
  | 'ready'
  | 'applying'
  | 'restarting'
  | 'error'

function pickWarning(result: UpdateCheckResult | null, locale: string): string {
  if (!result) return ''
  if (locale.startsWith('zh')) {
    return result.warning || result.warning_en || ''
  }
  return result.warning_en || result.warning || ''
}

export function SettingsModal({ settings, onChange, onClose }: Props) {
  const t = useT()
  const { locale } = useI18n()
  const [supportOpen, setSupportOpen] = useState(false)
  const [versionLabel, setVersionLabel] = useState(APP_VERSION)
  const [phase, setPhase] = useState<UpdatePhase>('idle')
  const [result, setResult] = useState<UpdateCheckResult | null>(null)
  const [statusText, setStatusText] = useState('')

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

  const onCheckUpdate = async () => {
    setPhase('checking')
    setStatusText(t('version.checking'))
    setResult(null)
    try {
      const data = await checkUpdate()
      setResult(data)
      const warn = pickWarning(data, locale)

      if (!data.ok) {
        setPhase('error')
        if (data.error === 'network_error' || data.error === 'http_error') {
          setStatusText([t('version.networkError'), warn].filter(Boolean).join('\n'))
        } else {
          setStatusText(
            [data.message || t('version.checkFailed'), warn].filter(Boolean).join('\n'),
          )
        }
        return
      }

      if (data.up_to_date || !data.update_available) {
        setPhase('ready')
        setStatusText([t('version.upToDate'), warn].filter(Boolean).join('\n'))
        return
      }

      const remote = data.remote_version || '?'
      if (!data.has_asset) {
        setPhase('ready')
        setStatusText(
          [
            t('version.availableNoAsset', { version: remote }),
            warn,
            data.html_url ? t('version.openReleaseHint') : '',
          ]
            .filter(Boolean)
            .join('\n'),
        )
        return
      }

      if (!data.frozen) {
        setPhase('ready')
        setStatusText(
          [t('version.availableDevOnly', { version: remote }), warn].filter(Boolean).join('\n'),
        )
        return
      }

      setPhase('ready')
      setStatusText(
        [t('version.available', { version: remote }), warn, t('version.dataSafe')]
          .filter(Boolean)
          .join('\n'),
      )
    } catch (err) {
      setPhase('error')
      setStatusText(
        t('version.networkError') +
          '\n' +
          (err instanceof Error ? err.message : String(err)),
      )
    }
  }

  const onApplyUpdate = async () => {
    setPhase('applying')
    setStatusText(t('version.applying'))
    try {
      const data = await applyUpdate(true)
      setResult(data)
      const warn = pickWarning(data, locale)
      if (data.applied) {
        setPhase('restarting')
        setStatusText([t('version.restarting'), warn, t('version.dataSafe')].filter(Boolean).join('\n'))
        return
      }
      setPhase('error')
      if (data.error === 'no_asset') {
        setStatusText([t('version.noAsset'), warn].filter(Boolean).join('\n'))
      } else if (data.error === 'not_frozen') {
        setStatusText([t('version.devOnly'), warn].filter(Boolean).join('\n'))
      } else if (data.error === 'download_failed' || data.error === 'network_error') {
        setStatusText([t('version.downloadFailed'), warn].filter(Boolean).join('\n'))
      } else if (data.message === 'already_up_to_date') {
        setPhase('ready')
        setStatusText([t('version.upToDate'), warn].filter(Boolean).join('\n'))
      } else {
        setStatusText(
          [data.message || t('version.applyFailed'), warn].filter(Boolean).join('\n'),
        )
      }
    } catch (err) {
      setPhase('error')
      setStatusText(
        t('version.downloadFailed') +
          '\n' +
          (err instanceof Error ? err.message : String(err)),
      )
    }
  }

  const canApply =
    phase === 'ready' &&
    !!result?.ok &&
    !!result.update_available &&
    !!result.has_asset &&
    !!result.frozen

  const busy = phase === 'checking' || phase === 'applying' || phase === 'restarting'

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
            <div className="settings-version-actions">
              <button
                type="button"
                className="btn"
                disabled={busy}
                onClick={() => void onCheckUpdate()}
              >
                {phase === 'checking' ? t('version.checking') : t('version.check')}
              </button>
              {canApply && (
                <button
                  type="button"
                  className="btn"
                  disabled={busy}
                  onClick={() => void onApplyUpdate()}
                >
                  {t('version.apply')}
                </button>
              )}
              {phase === 'applying' && (
                <button type="button" className="btn" disabled>
                  {t('version.applying')}
                </button>
              )}
              {result?.html_url && result.update_available && !result.has_asset && (
                <a
                  className="btn btn-ghost"
                  href={result.html_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {t('version.openRelease')}
                </a>
              )}
            </div>
            {statusText && (
              <div
                className={
                  phase === 'error'
                    ? 'settings-note settings-note-error'
                    : 'settings-note'
                }
              >
                {statusText.split('\n').map((line, i) => (
                  <div key={i}>{line}</div>
                ))}
              </div>
            )}
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
