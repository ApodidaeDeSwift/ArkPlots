import type { PlotItem } from '../types'
import {
  computeRecommendations,
  RECOMMEND_I18N_KEYS,
  type RecommendBuckets,
} from '../recommend'
import { usePlotName, useT } from '../i18n'

type Props = {
  plots: PlotItem[]
  records: Record<string, string>
  onJump: (id: string) => void
}

export function RecommendPanel({ plots, records, onJump }: Props) {
  const t = useT()
  const plotName = usePlotName()
  const buckets: RecommendBuckets = computeRecommendations(plots, records)
  const plotsMap = new Map(plots.map((p) => [String(p.id), p]))

  const sections: (keyof RecommendBuckets)[] = [
    'urgent',
    'recSupp',
    'recContinue',
    'canContinue',
  ]

  return (
    <div>
      {sections.map((key) => {
        const keys = RECOMMEND_I18N_KEYS[key]
        const ids = buckets[key]
        return (
          <div className="rec-section" key={key}>
            <h4>
              <span className="tip" title={t(keys.tip)}>
                ?
              </span>
              {t(keys.title)} ({ids.length})
            </h4>
            {!ids.length && <div className="empty">{t('recommend.empty')}</div>}
            {ids.map((pid) => (
              <div className="rec-item" key={pid}>
                <button type="button" className="linkish" onClick={() => onJump(pid)}>
                  {plotName(pid, plotsMap.get(pid)?.name) || `ID:${pid}`}
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => onJump(pid)}>
                  {t('actions.jump')}
                </button>
              </div>
            ))}
          </div>
        )
      })}
    </div>
  )
}
