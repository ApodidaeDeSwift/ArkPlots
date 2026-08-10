import type { MessageKey, Messages, TranslateParams } from './types'

function getByPath(messages: Messages, key: MessageKey): string {
  const parts = key.split('.')
  let cur: unknown = messages
  for (const part of parts) {
    if (cur == null || typeof cur !== 'object') return key
    cur = (cur as Record<string, unknown>)[part]
  }
  return typeof cur === 'string' ? cur : key
}

export function createT(messages: Messages) {
  return (key: MessageKey, params?: TranslateParams): string => {
    let text = getByPath(messages, key)
    if (params) {
      for (const [name, value] of Object.entries(params)) {
        text = text.replaceAll(`{${name}}`, String(value))
      }
    }
    return text
  }
}
