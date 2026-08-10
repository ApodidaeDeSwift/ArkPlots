import type { ReadStatus } from '../types'
import type { MessageKey } from './types'
import { useI18n, useT } from './I18nProvider'
import {
  resolveCountry,
  resolveOperator,
  resolvePlotName,
  resolvePower,
  resolveRelatedPlotTag,
} from './content'

export { I18nProvider, useI18n, useT } from './I18nProvider'
export { DEFAULT_LOCALE, listLocales, localeRegistry, resolveLocale } from './locales'
export type { LocaleCode, MessageKey, Messages, TranslateParams, Translator } from './types'
export {
  resolveCountry,
  resolveOperator,
  resolvePlotName,
  resolvePower,
  resolveRelatedPlotTag,
} from './content'

/** Stored ReadStatus → message key for display. */
const STATUS_MESSAGE_KEY: Record<ReadStatus, MessageKey> = {
  未读: 'status.unread',
  计划读: 'status.planned',
  正在读: 'status.reading',
  已读: 'status.read',
}

const CLASS_MESSAGE_KEY: Record<string, MessageKey> = {
  main: 'classLabel.main',
  sidestory: 'classLabel.sidestory',
  interlude: 'classLabel.interlude',
  ministory: 'classLabel.ministory',
  manga: 'classLabel.manga',
  anime: 'classLabel.anime',
  rougelike: 'classLabel.rougelike',
  RA: 'classLabel.RA',
  other: 'classLabel.other',
}

export function useStatusLabel() {
  const t = useT()
  return (status: string) => {
    const key = STATUS_MESSAGE_KEY[status as ReadStatus]
    return key ? t(key) : status
  }
}

export function useClassLabel() {
  const t = useT()
  return (code: string | undefined | null) => {
    if (!code) return ''
    const key = CLASS_MESSAGE_KEY[code]
    return key ? t(key) : code
  }
}

/** Localized plot display name; falls back to Plotline.json `name`. */
export function usePlotName() {
  const { locale } = useI18n()
  return (id: string | number | null | undefined, fallbackName?: string | null) =>
    resolvePlotName(locale, id, fallbackName)
}

export function useCountryLabel() {
  const { locale } = useI18n()
  return (raw: string | null | undefined) => resolveCountry(locale, raw)
}

export function usePowerLabel() {
  const { locale } = useI18n()
  return (raw: string | null | undefined) => resolvePower(locale, raw)
}

export function useOperatorLabel() {
  const { locale } = useI18n()
  return (raw: string | null | undefined) => resolveOperator(locale, raw)
}

export function useRelatedPlotTagLabel() {
  const { locale } = useI18n()
  return (raw: string | null | undefined) => resolveRelatedPlotTag(locale, raw)
}

/** Join helper that localizes each token then joins. */
export function useLocalizedList() {
  const country = useCountryLabel()
  const power = usePowerLabel()
  const operator = useOperatorLabel()
  const related = useRelatedPlotTagLabel()
  return {
    countries: (vals: string[], sep = ', ') => vals.map(country).join(sep),
    powers: (vals: string[], sep = ', ') => vals.map(power).join(sep),
    operators: (vals: string[], sep = ', ') => vals.map(operator).join(sep),
    relatedPlots: (vals: string[], sep = ', ') => vals.map(related).join(sep),
  }
}

export function statusLabelKey(status: ReadStatus): MessageKey {
  return STATUS_MESSAGE_KEY[status]
}
