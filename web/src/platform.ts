/**
 * Runtime platform detection.
 *
 * Lives in its own module because two unrelated layers need it:
 *   - api.ts       decides whether data comes from the local server or from
 *                  the bundled JSON + localStorage
 *   - settings.ts  picks the default for "check for updates on launch"
 *
 * If this sat in api.ts, settings.ts would have to import api.ts at runtime,
 * which inverts the dependency direction (api already type-imports settings)
 * and drags the whole API layer into the settings module.
 */

type CapacitorGlobal = { isNativePlatform?: () => boolean }

const w =
  typeof window !== 'undefined'
    ? (window as unknown as { Capacitor?: CapacitorGlobal })
    : undefined

/** True inside the Capacitor Android shell (no local Python server available). */
export const IS_NATIVE_APP = !!w?.Capacitor?.isNativePlatform?.()
