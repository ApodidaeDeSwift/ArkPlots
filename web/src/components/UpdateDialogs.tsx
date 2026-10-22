import type { UpdateCheckResult } from '../api'
import { useT } from '../i18n'
import { ReleaseNotes } from './ReleaseNotes'

function notesOf(result: UpdateCheckResult): string {
  return (result.release_notes || '').trim()
}

function versionOf(result: UpdateCheckResult): string {
  return result.remote_version || result.current_version || '?'
}

function NotesBlock({ result }: { result: UpdateCheckResult }) {
  const t = useT()
  const notes = notesOf(result)
  const version = versionOf(result)
  return (
    <>
      <h4 className="update-dialog-notes-title">{t('version.notesTitle', { version })}</h4>
      {notes ? (
        <ReleaseNotes source={notes} />
      ) : (
        <p className="release-notes-empty">{t('version.notesEmpty')}</p>
      )}
    </>
  )
}

function AnnouncementBlock({ result }: { result: UpdateCheckResult }) {
  const t = useT()
  const notes = (result.update_notes || '').trim()
  return (
    <>
      <h4 className="update-dialog-notes-title">{t('version.announcementTitle')}</h4>
      {notes ? (
        <ReleaseNotes source={notes} />
      ) : (
        <p className="release-notes-empty">{t('version.announcementEmpty')}</p>
      )}
    </>
  )
}

type OfferProps = {
  result: UpdateCheckResult
  busy: boolean
  errorText: string
  onLater: () => void
  onConfirm: () => void
}

/** Shown when a launch-time check finds a newer release. */
export function UpdateOfferDialog({ result, busy, errorText, onLater, onConfirm }: OfferProps) {
  const t = useT()
  const version = versionOf(result)
  return (
    <div className="modal-backdrop modal-backdrop-front" onClick={busy ? undefined : onLater}>
      <div
        id="update-offer-dialog"
        className="modal update-dialog"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="update-offer-title"
      >
        <h3 id="update-offer-title">{t('version.promptTitle', { version })}</h3>
        <p className="update-dialog-ask">{t('version.promptAsk')}</p>
        <NotesBlock result={result} />
        {busy && (
          <div className="settings-progress" aria-hidden>
            <div className="settings-progress-bar" />
          </div>
        )}
        {errorText && <p className="update-dialog-error">{errorText}</p>}
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" disabled={busy} onClick={onLater}>
            {t('version.later')}
          </button>
          <button type="button" className="btn btn-accent" disabled={busy} onClick={onConfirm}>
            {busy ? t('version.applying') : t('version.updateNow')}
          </button>
        </div>
      </div>
    </div>
  )
}

type CompleteProps = {
  result: UpdateCheckResult
  restarting: boolean
  errorText: string
  onRestart: () => void
}

/** Shown after the installer has been scheduled, before the process exits. */
export function UpdateCompleteDialog({ result, restarting, errorText, onRestart }: CompleteProps) {
  const t = useT()
  return (
    <div className="modal-backdrop modal-backdrop-front">
      <div
        id="update-complete-dialog"
        className="modal update-dialog"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="update-complete-title"
      >
        <h3 id="update-complete-title">{t('version.completeTitle')}</h3>
        <p className="update-dialog-ask">{t('version.completeBody')}</p>
        <AnnouncementBlock result={result} />
        {restarting && (
          <div className="settings-progress" aria-hidden>
            <div className="settings-progress-bar" />
          </div>
        )}
        {errorText && <p className="update-dialog-error">{errorText}</p>}
        <div className="modal-actions">
          <button type="button" className="btn btn-accent" disabled={restarting} onClick={onRestart}>
            {restarting ? t('version.applying') : t('version.restartNow')}
          </button>
        </div>
      </div>
    </div>
  )
}
