/**
 * Open a link outside the app.
 *
 * Why this exists: inside the Capacitor Android WebView `window.open` does not
 * open anything — there is no second window, and Capacitor intercepts the call
 * without a target. So every external link (plot videos, release notes, the
 * repo link in settings) silently did nothing on Android while working fine in
 * the desktop browser.
 *
 * @capacitor/browser opens a Chrome Custom Tab instead, which is the expected
 * behaviour on Android. It is imported lazily so the desktop bundle never pulls
 * the plugin in.
 */
import { IS_NATIVE_APP } from './platform'

export async function openExternal(url: string | undefined | null): Promise<void> {
  if (!url) return

  if (IS_NATIVE_APP) {
    try {
      const { Browser } = await import('@capacitor/browser')
      await Browser.open({ url })
      return
    } catch {
      /* plugin missing or rejected the URL: fall back to the web path below */
    }
  }

  window.open(url, '_blank', 'noopener,noreferrer')
}
