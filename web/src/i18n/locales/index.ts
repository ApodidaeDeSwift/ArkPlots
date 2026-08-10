import type { LocaleCode, Messages } from '../types'
import enUS from './en-US'
import zhCN from './zh-CN'

/**
 * Register new locales here after adding `./<code>.ts`.
 * Example:
 *   import jaJP from './ja-JP'
 *   export const localeRegistry = { 'zh-CN': zhCN, 'en-US': enUS, 'ja-JP': jaJP }
 */
export const localeRegistry: Record<LocaleCode, Messages> = {
  'zh-CN': zhCN,
  'en-US': enUS,
}

export const DEFAULT_LOCALE: LocaleCode = 'zh-CN'

export function listLocales(): { code: LocaleCode; nativeName: string }[] {
  return Object.entries(localeRegistry).map(([code, messages]) => ({
    code,
    nativeName: messages.meta.nativeName,
  }))
}

export function resolveLocale(code: string | null | undefined): LocaleCode {
  if (code && code in localeRegistry) return code
  return DEFAULT_LOCALE
}
