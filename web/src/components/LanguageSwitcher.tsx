import { useI18n } from '../i18n'

/** Compact language switcher; grows automatically as locales are registered. */
export function LanguageSwitcher() {
  const { locale, setLocale, availableLocales, t } = useI18n()

  if (availableLocales.length <= 1) {
    return (
      <label className="lang-switch" title={t('lang.label')}>
        <span className="filter-label">{t('lang.label')}</span>
        <select className="field lang-select" value={locale} disabled aria-label={t('lang.label')}>
          {availableLocales.map((l) => (
            <option key={l.code} value={l.code}>
              {l.nativeName}
            </option>
          ))}
        </select>
      </label>
    )
  }

  return (
    <label className="lang-switch" title={t('lang.label')}>
      <span className="filter-label">{t('lang.label')}</span>
      <select
        className="field lang-select"
        value={locale}
        aria-label={t('lang.label')}
        onChange={(e) => setLocale(e.target.value)}
      >
        {availableLocales.map((l) => (
          <option key={l.code} value={l.code}>
            {l.nativeName}
          </option>
        ))}
      </select>
    </label>
  )
}
