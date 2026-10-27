import { Fragment, type ReactNode } from 'react'

type Block =
  | { type: 'h'; level: number; text: string }
  | { type: 'p'; text: string }
  | { type: 'ul'; items: string[] }
  | { type: 'ol'; items: string[] }
  | { type: 'quote'; text: string }
  | { type: 'code'; text: string }
  | { type: 'hr' }

function decodeEntities(text: string): string {
  return text
    .replace(/&nbsp;/gi, '\u00a0')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&amp;/gi, '&')
}

function prepareSource(source: string): string {
  return decodeEntities(
    source
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      .replace(/<!--[\s\S]*?-->/g, '')
      .replace(/<br\s*\/?>/gi, '\n'),
  )
}

function isBlockStart(line: string): boolean {
  return (
    line.startsWith('```') ||
    line.startsWith('>') ||
    /^#{1,6}(?:\s+|\S)/.test(line) ||
    /^(-{3,}|\*{3,}|_{3,})$/.test(line.trim()) ||
    /^\s*-\s*\S/.test(line) ||
    /^\s*[*+]\s+\S/.test(line) ||
    /^\s*\d+[.)]\s*\S/.test(line)
  )
}

function parseBlocks(source: string): Block[] {
  const lines = prepareSource(source).split('\n')
  const blocks: Block[] = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    if (!line.trim()) {
      i += 1
      continue
    }
    if (line.startsWith('```')) {
      const buf: string[] = []
      i += 1
      while (i < lines.length && !lines[i].startsWith('```')) {
        buf.push(lines[i])
        i += 1
      }
      if (i < lines.length) i += 1
      blocks.push({ type: 'code', text: buf.join('\n') })
      continue
    }
    const heading = /^(#{1,6})\s*(.+)$/.exec(line)
    if (heading) {
      blocks.push({ type: 'h', level: heading[1].length, text: heading[2].trim() })
      i += 1
      continue
    }
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(line.trim())) {
      blocks.push({ type: 'hr' })
      i += 1
      continue
    }
    if (line.startsWith('>')) {
      const buf: string[] = []
      while (i < lines.length && lines[i].startsWith('>')) {
        buf.push(lines[i].replace(/^>\s?/, ''))
        i += 1
      }
      blocks.push({ type: 'quote', text: buf.join('\n') })
      continue
    }
    if (/^\s*-\s*\S/.test(line) || /^\s*[*+]\s+\S/.test(line)) {
      const items: string[] = []
      const item = /^\s*(?:-\s*|[*+]\s+)(.*)$/
      while (i < lines.length && (/^\s*-\s*\S/.test(lines[i]) || /^\s*[*+]\s+\S/.test(lines[i]))) {
        items.push(lines[i].replace(item, '$1'))
        i += 1
      }
      blocks.push({ type: 'ul', items })
      continue
    }
    if (/^\s*\d+[.)]\s*\S/.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^\s*\d+[.)]\s*\S/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+[.)]\s*/, ''))
        i += 1
      }
      blocks.push({ type: 'ol', items })
      continue
    }
    const buf = [line]
    i += 1
    while (i < lines.length && lines[i].trim() && !isBlockStart(lines[i])) {
      buf.push(lines[i])
      i += 1
    }
    blocks.push({ type: 'p', text: buf.join('\n') })
  }
  return blocks
}

const INLINE =
  /!\[([^\]]*)\]\((https?:\/\/[^\s)]+)\)|\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|`([^`]+)`|\*\*([^*]+)\*\*|~~([^~]+)~~|\*([^*\n]+)\*|(https?:\/\/[^\s<]+)/g

function renderInline(text: string, key: string): ReactNode[] {
  const nodes: ReactNode[] = []
  const re = new RegExp(INLINE.source, 'g')
  let last = 0
  let match: RegExpExecArray | null
  let n = 0
  while ((match = re.exec(text))) {
    if (match.index > last) nodes.push(text.slice(last, match.index))
    const id = `${key}-${n}`
    n += 1
    if (match[2]) {
      nodes.push(<img key={id} src={match[2]} alt={match[1] || ''} />)
    } else if (match[4]) {
      nodes.push(
        <a key={id} href={match[4]} target="_blank" rel="noreferrer">
          {match[3]}
        </a>,
      )
    } else if (match[5] != null) {
      nodes.push(<code key={id}>{match[5]}</code>)
    } else if (match[6] != null) {
      nodes.push(<strong key={id}>{match[6]}</strong>)
    } else if (match[7] != null) {
      nodes.push(<del key={id}>{match[7]}</del>)
    } else if (match[8] != null) {
      nodes.push(<em key={id}>{match[8]}</em>)
    } else if (match[9]) {
      const href = match[9].replace(/[),.;]+$/, '')
      nodes.push(
        <a key={id} href={href} target="_blank" rel="noreferrer">
          {href}
        </a>,
      )
    }
    last = match.index + match[0].length
  }
  if (last < text.length) nodes.push(text.slice(last))
  return nodes
}

function renderLines(text: string, key: string): ReactNode {
  const lines = text.split('\n')
  return lines.map((line, index) => (
    <Fragment key={`${key}-l${index}`}>
      {index > 0 && <br />}
      {renderInline(line, `${key}-${index}`)}
    </Fragment>
  ))
}

/** Render GitHub release notes. Text is escaped by React; raw HTML is not executed. */
export function ReleaseNotes({ source }: { source: string }) {
  const blocks = parseBlocks(source)
  return (
    <div className="release-notes">
      {blocks.map((block, index) => {
        const key = `b${index}`
        if (block.type === 'h') {
          return (
            <div key={key} className={`release-notes-h release-notes-h${block.level}`}>
              {renderInline(block.text, key)}
            </div>
          )
        }
        if (block.type === 'ul' || block.type === 'ol') {
          const List = block.type === 'ul' ? 'ul' : 'ol'
          return (
            <List key={key}>
              {block.items.map((item, itemIndex) => (
                <li key={`${key}-${itemIndex}`}>{renderInline(item, `${key}-${itemIndex}`)}</li>
              ))}
            </List>
          )
        }
        if (block.type === 'quote') {
          return <blockquote key={key}>{renderLines(block.text, key)}</blockquote>
        }
        if (block.type === 'code') {
          return (
            <pre key={key}>
              <code>{block.text}</code>
            </pre>
          )
        }
        if (block.type === 'hr') return <hr key={key} />
        return <p key={key}>{renderLines(block.text, key)}</p>
      })}
    </div>
  )
}
