import { useT } from '../i18n'
import { openExternal } from '../openExternal'
import { ExternalLink } from './ExternalLink'

type Video = { name: string; url: string }

type Props = {
  title: string
  videos: Video[]
  onClose: () => void
}

export function VideoModal({ title, videos, onClose }: Props) {
  const t = useT()

  const copy = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url)
      alert(t('video.copied'))
    } catch {
      alert(t('video.copyFailed'))
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>{t('video.title', { name: title })}</h3>
        {!videos.length && <div className="empty">{t('video.empty')}</div>}
        {videos.map((v) => (
          <div className="video-row" key={v.url + v.name}>
            <ExternalLink href={v.url}>
              {v.name || v.url}
            </ExternalLink>
            <button type="button" className="btn btn-ghost" onClick={() => void openExternal(v.url)}>
              {t('actions.open')}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => copy(v.url)}>
              {t('actions.copyLink')}
            </button>
          </div>
        ))}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            {t('actions.close')}
          </button>
        </div>
      </div>
    </div>
  )
}
