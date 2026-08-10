/**
 * i18n message schema.
 *
 * To add a language later:
 * 1. Create `locales/<code>.ts` exporting a `Messages` object (same shape as zh-CN).
 * 2. Register it in `locales/index.ts` (`localeRegistry` + `localeMeta`).
 * 3. The language switcher picks it up automatically.
 *
 * Data keys that must stay stable across locales:
 * - ReadStatus values stored in Read_record.json ('未读' | '计划读' | '正在读' | '已读')
 * - Plot class codes (main, sidestory, …)
 * Only UI labels are translated.
 */

export type LocaleCode = string

export type Messages = {
  meta: {
    /** Native name shown in the language switcher, e.g. 简体中文 */
    nativeName: string
  }
  app: {
    brandSub: string
    loading: string
  }
  panels: {
    filtersList: string
    detailPreview: string
    recommendations: string
  }
  actions: {
    filter: string
    resetFilters: string
    multiSelect: string
    cancelMultiSelect: string
    setReadStatus: string
    batchSet: string
    relatedVideos: string
    refreshData: string
    jump: string
    open: string
    copyLink: string
    close: string
    cancel: string
    confirm: string
    save: string
    selectAll: string
    selectNone: string
    invert: string
  }
  filter: {
    startDate: string
    endDate: string
    year: string
    month: string
    day: string
    class: string
    country: string
    stage: string
    relatedPower: string
    relatedPlot: string
    operator: string
    operatorPlaceholder: string
    selectedClasses: string
    matchAny: string
    matchAll: string
    countLabel: string
  }
  selector: {
    class: string
    country: string
    stage: string
    power: string
    rplot: string
  }
  list: {
    empty: string
    unnamed: string
    country: string
    power: string
    relatedPlot: string
    operator: string
    stage: string
  }
  detail: {
    history: string
    pickHint: string
    necessary: string
    optional: string
    showReason: string
    status: string
    type: string
    date: string
    stage: string
    country: string
    power: string
    relatedPlot: string
    operator: string
    description: string
    emDash: string
  }
  status: {
    label: string
    setTitle: string
    batchTitle: string
    /** Display labels keyed by stored ReadStatus value */
    unread: string
    planned: string
    reading: string
    read: string
  }
  classLabel: {
    main: string
    sidestory: string
    interlude: string
    ministory: string
    manga: string
    anime: string
    rougelike: string
    RA: string
    other: string
  }
  recommend: {
    urgentTitle: string
    urgentTip: string
    recSuppTitle: string
    recSuppTip: string
    recContinueTitle: string
    recContinueTip: string
    canContinueTitle: string
    canContinueTip: string
    empty: string
  }
  video: {
    title: string
    empty: string
    defaultName: string
    copied: string
    copyFailed: string
  }
  lang: {
    label: string
  }
}

export type TranslateParams = Record<string, string | number>

export type Translator = {
  locale: LocaleCode
  t: (key: MessageKey, params?: TranslateParams) => string
  setLocale: (code: LocaleCode) => void
  availableLocales: { code: LocaleCode; nativeName: string }[]
}

/** Dot-path keys into Messages (leaf strings only). */
export type MessageKey =
  | `meta.${keyof Messages['meta']}`
  | `app.${keyof Messages['app']}`
  | `panels.${keyof Messages['panels']}`
  | `actions.${keyof Messages['actions']}`
  | `filter.${keyof Messages['filter']}`
  | `selector.${keyof Messages['selector']}`
  | `list.${keyof Messages['list']}`
  | `detail.${keyof Messages['detail']}`
  | `status.${keyof Messages['status']}`
  | `classLabel.${keyof Messages['classLabel']}`
  | `recommend.${keyof Messages['recommend']}`
  | `video.${keyof Messages['video']}`
  | `lang.${keyof Messages['lang']}`
