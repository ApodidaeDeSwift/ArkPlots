import type { LocaleCode } from '../types'
import { countriesEnUS } from './countries.en-US'
import { operatorsEnUS } from './operators.en-US'
import { plotNamesEnUS } from './plotNames.en-US'
import { powersEnUS } from './powers.en-US'
import { relatedPlotsEnUS } from './relatedPlots.en-US'

/**
 * Content locale packs keyed by locale code.
 * zh-CN uses Plotline.json values directly (no override tables).
 */
const plotNamePacks: Record<string, Record<string, string>> = {
  'en-US': plotNamesEnUS,
}

const countryPacks: Record<string, Record<string, string>> = {
  'en-US': countriesEnUS,
}

const powerPacks: Record<string, Record<string, string>> = {
  'en-US': powersEnUS,
}

const operatorPacks: Record<string, Record<string, string>> = {
  'en-US': operatorsEnUS,
}

const relatedPlotPacks: Record<string, Record<string, string>> = {
  'en-US': relatedPlotsEnUS,
}

function resolveFromPack(
  packs: Record<string, Record<string, string>>,
  locale: LocaleCode,
  raw: string | null | undefined,
): string {
  const key = (raw ?? '').trim()
  if (!key) return ''
  const pack = packs[locale]
  if (pack && pack[key]) return pack[key]
  return key
}

export function resolvePlotName(
  locale: LocaleCode,
  id: string | number | null | undefined,
  fallbackName?: string | null,
): string {
  const pid = id == null ? '' : String(id)
  const pack = plotNamePacks[locale]
  if (pack && pid && pack[pid]) return pack[pid]
  return fallbackName || (pid ? `ID:${pid}` : '')
}

export function resolveCountry(locale: LocaleCode, raw: string | null | undefined): string {
  return resolveFromPack(countryPacks, locale, raw)
}

export function resolvePower(locale: LocaleCode, raw: string | null | undefined): string {
  return resolveFromPack(powerPacks, locale, raw)
}

export function resolveOperator(locale: LocaleCode, raw: string | null | undefined): string {
  return resolveFromPack(operatorPacks, locale, raw)
}

export function resolveRelatedPlotTag(
  locale: LocaleCode,
  raw: string | null | undefined,
): string {
  return resolveFromPack(relatedPlotPacks, locale, raw)
}

export function mapTerms(
  locale: LocaleCode,
  values: string[],
  resolver: (locale: LocaleCode, raw: string) => string,
): string[] {
  return values.map((v) => resolver(locale, v))
}
