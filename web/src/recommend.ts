import type { MessageKey } from './i18n'
import type { PlotItem } from './types'
import { extractPreplotId } from './types'

export type RecommendBuckets = {
  urgent: string[]
  recSupp: string[]
  recContinue: string[]
  canContinue: string[]
}

export type RecommendBucketKey = keyof RecommendBuckets

/** Message key pairs for each recommendation bucket (titles / tips). */
export const RECOMMEND_I18N_KEYS: Record<
  RecommendBucketKey,
  { title: MessageKey; tip: MessageKey }
> = {
  urgent: { title: 'recommend.urgentTitle', tip: 'recommend.urgentTip' },
  recSupp: { title: 'recommend.recSuppTitle', tip: 'recommend.recSuppTip' },
  recContinue: {
    title: 'recommend.recContinueTitle',
    tip: 'recommend.recContinueTip',
  },
  canContinue: {
    title: 'recommend.canContinueTitle',
    tip: 'recommend.canContinueTip',
  },
}

/** Stored status value meaning "finished reading" (locale-independent data key). */
export const READ_DONE_STATUS = '已读'

export function computeRecommendations(
  plots: PlotItem[],
  records: Record<string, string>,
): RecommendBuckets {
  const plotsMap = new Map(plots.map((p) => [String(p.id), p]))
  const isRead = (pid: string) => records[pid] === READ_DONE_STATUS

  const collectNecessaryChain = (pid: string, out: Set<string>) => {
    const item = plotsMap.get(String(pid))
    if (!item) return
    for (const ne of item.necessary_plot || []) {
      const nid = extractPreplotId(ne)
      if (!nid || out.has(nid)) continue
      out.add(nid)
      collectNecessaryChain(nid, out)
    }
  }

  const urgent = new Set<string>()
  const recSupp = new Set<string>()
  const recContinue = new Set<string>()
  const canContinue = new Set<string>()

  for (const p of plots) {
    const pid = String(p.id)
    if (!isRead(pid)) continue
    for (const ne of p.necessary_plot || []) {
      const nid = extractPreplotId(ne)
      if (!nid) continue
      if (!isRead(nid)) {
        urgent.add(nid)
        collectNecessaryChain(nid, urgent)
      }
    }
    for (const oe of p.optional_plot || []) {
      const oid = extractPreplotId(oe)
      if (!oid) continue
      if (!isRead(oid)) recSupp.add(oid)
    }
  }

  for (const p of plots) {
    const pid = String(p.id)
    if (isRead(pid)) continue
    const necessaryIds = (p.necessary_plot || [])
      .map(extractPreplotId)
      .filter((x): x is string => !!x)
    const optionalIds = (p.optional_plot || [])
      .map(extractPreplotId)
      .filter((x): x is string => !!x)
    const necessaryOk = necessaryIds.length ? necessaryIds.every(isRead) : true
    const optionalOk = optionalIds.length ? optionalIds.every(isRead) : true
    if (necessaryOk && optionalOk) recContinue.add(pid)
    else if (necessaryOk && !optionalOk) canContinue.add(pid)
  }

  const urgentF = new Set([...urgent].filter((x) => !isRead(x)))
  const recSuppF = new Set(
    [...recSupp].filter((x) => !isRead(x) && !urgentF.has(x)),
  )
  const recContinueF = new Set(
    [...recContinue].filter(
      (x) => !isRead(x) && !urgentF.has(x) && !recSuppF.has(x),
    ),
  )
  const canContinueF = new Set(
    [...canContinue].filter(
      (x) =>
        !isRead(x) &&
        !urgentF.has(x) &&
        !recSuppF.has(x) &&
        !recContinueF.has(x),
    ),
  )

  const sortIds = (ids: Set<string>) =>
    [...ids].sort((a, b) => Number(a) - Number(b) || a.localeCompare(b))

  return {
    urgent: sortIds(urgentF),
    recSupp: sortIds(recSuppF),
    recContinue: sortIds(recContinueF),
    canContinue: sortIds(canContinueF),
  }
}
