/** Persisted UI preferences. Filter state is not stored here. */
export const SETTINGS_STORAGE_KEY = 'arkplots.settings'

export type DisplaySettings = {
  showCover: boolean
  showReason: boolean
  showNecessary: boolean
  showOptional: boolean
}

/** Matches the previous in-panel defaults: cover, reasons, and both prerequisite lists on. */
export const DEFAULT_DISPLAY_SETTINGS: DisplaySettings = {
  showCover: true,
  showReason: true,
  showNecessary: true,
  showOptional: true,
}

function pickBool(value: unknown, fallback: boolean): boolean {
  return typeof value === 'boolean' ? value : fallback
}

export function loadDisplaySettings(): DisplaySettings {
  try {
    const raw = localStorage.getItem(SETTINGS_STORAGE_KEY)
    if (!raw) return { ...DEFAULT_DISPLAY_SETTINGS }
    const parsed = JSON.parse(raw) as Partial<DisplaySettings>
    return {
      showCover: pickBool(parsed.showCover, DEFAULT_DISPLAY_SETTINGS.showCover),
      showReason: pickBool(parsed.showReason, DEFAULT_DISPLAY_SETTINGS.showReason),
      showNecessary: pickBool(parsed.showNecessary, DEFAULT_DISPLAY_SETTINGS.showNecessary),
      showOptional: pickBool(parsed.showOptional, DEFAULT_DISPLAY_SETTINGS.showOptional),
    }
  } catch {
    return { ...DEFAULT_DISPLAY_SETTINGS }
  }
}

export function saveDisplaySettings(settings: DisplaySettings): void {
  localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings))
}
