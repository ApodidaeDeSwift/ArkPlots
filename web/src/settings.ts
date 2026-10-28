/** Persisted UI preferences. Filter state is not stored here. */
import { APP_CHANNEL } from './version'

export const SETTINGS_STORAGE_KEY = 'arkplots.settings'

/** 正式版 = GitHub 普通 Release；测试版 = 另外包含 Pre-release。缺省跟当前安装包通道走。 */
export type UpdateChannel = 'release' | 'preview'

export type DisplaySettings = {
  showCover: boolean
  showReason: boolean
  showNecessary: boolean
  showOptional: boolean
  /** When true, check GitHub for an update on every launch. */
  checkUpdatesOnLaunch: boolean
  /** Which GitHub releases the updater may offer. */
  updateChannel: UpdateChannel
}

/** The synced channel is a single literal, so compare it as text. */
function defaultUpdateChannel(channel: string): UpdateChannel {
  return channel === 'preview' ? 'preview' : 'release'
}

/** Matches the previous in-panel defaults: cover, reasons, and both prerequisite lists on. */
export const DEFAULT_DISPLAY_SETTINGS: DisplaySettings = {
  showCover: true,
  showReason: true,
  showNecessary: true,
  showOptional: true,
  checkUpdatesOnLaunch: true,
  updateChannel: defaultUpdateChannel(APP_CHANNEL),
}

function pickBool(value: unknown, fallback: boolean): boolean {
  return typeof value === 'boolean' ? value : fallback
}

function pickChannel(value: unknown, fallback: UpdateChannel): UpdateChannel {
  return value === 'release' || value === 'preview' ? value : fallback
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
      checkUpdatesOnLaunch: pickBool(
        parsed.checkUpdatesOnLaunch,
        DEFAULT_DISPLAY_SETTINGS.checkUpdatesOnLaunch,
      ),
      updateChannel: pickChannel(parsed.updateChannel, DEFAULT_DISPLAY_SETTINGS.updateChannel),
    }
  } catch {
    return { ...DEFAULT_DISPLAY_SETTINGS }
  }
}

export function saveDisplaySettings(settings: DisplaySettings): void {
  localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings))
}
