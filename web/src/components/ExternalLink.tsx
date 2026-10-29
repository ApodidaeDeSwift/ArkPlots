import type { AnchorHTMLAttributes, ReactNode } from 'react'
import { openExternal } from '../openExternal'
import { IS_NATIVE_APP } from '../platform'

type Props = AnchorHTMLAttributes<HTMLAnchorElement> & { children?: ReactNode }

/**
 * An `<a target="_blank">` that also works inside the Android WebView.
 *
 * Desktop keeps the plain anchor behaviour (middle-click, right-click "copy
 * link", and so on still work). On Android the click is intercepted and handed
 * to the system browser, because `target="_blank"` there just does nothing.
 */
export function ExternalLink({ href, children, onClick, ...rest }: Props) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      {...rest}
      onClick={(e) => {
        onClick?.(e)
        if (e.defaultPrevented) return
        if (IS_NATIVE_APP && href) {
          e.preventDefault()
          void openExternal(href)
        }
      }}
    >
      {children}
    </a>
  )
}
