import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { createT } from './createTranslator'
import { DEFAULT_LOCALE, listLocales, localeRegistry, resolveLocale } from './locales'
import type { LocaleCode, MessageKey, TranslateParams, Translator } from './types'

const STORAGE_KEY = 'arkplots.locale'

function readStoredLocale(): LocaleCode {
  try {
    return resolveLocale(localStorage.getItem(STORAGE_KEY))
  } catch {
    return DEFAULT_LOCALE
  }
}

const I18nContext = createContext<Translator | null>(null)

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<LocaleCode>(() => readStoredLocale())

  const setLocale = useCallback((code: LocaleCode) => {
    const next = resolveLocale(code)
    setLocaleState(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      /* ignore quota / private mode */
    }
    document.documentElement.lang = next
  }, [])

  const value = useMemo<Translator>(() => {
    const messages = localeRegistry[locale] ?? localeRegistry[DEFAULT_LOCALE]
    const t = createT(messages)
    return {
      locale,
      t,
      setLocale,
      availableLocales: listLocales(),
    }
  }, [locale, setLocale])

  useEffect(() => {
    document.documentElement.lang = locale
  }, [locale])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): Translator {
  const ctx = useContext(I18nContext)
  if (!ctx) {
    throw new Error('useI18n must be used within I18nProvider')
  }
  return ctx
}

/** Convenience hook when only `t` is needed. */
export function useT() {
  return useI18n().t
}

export type { MessageKey, TranslateParams, LocaleCode }
