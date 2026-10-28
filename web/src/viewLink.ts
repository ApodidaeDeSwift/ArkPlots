import type { PlotItem } from './types'

/**
 * Where the detail "快捷跳转查看" button opens.
 * Side stories and story collections use 情报处理室 anchors (the HTML id
 * matches the story name). Main theme is not on that page; 剧情一览 lists
 * each chapter. Collabs whose room section says the story is not archived
 * there, plus Integrated Strategies and Reclamation Algorithm, use their
 * own PRTS pages. Comics use Terra Historicus. Anime uses Bilibili.
 */

const PRTS = 'https://prts.wiki/w/'

function wikiPage(title: string): string {
  return PRTS + encodeURIComponent(title.replace(/ /g, '_'))
}

function roomAnchor(anchor: string): string {
  return `${wikiPage('情报处理室')}#${encodeURIComponent(anchor)}`
}

function mainChapter(name: string): string {
  const chapter = name.replace(/^EP\d+\.\s*/, '').trim()
  return `${wikiPage('剧情一览')}#:~:text=${encodeURIComponent(chapter)}`
}

function comic(id: string): string {
  return `https://comic.hypergryph.com/terra-historicus/comic/${id}`
}

/** Official comic id, including stories filed under another class. */
const COMIC_ID: Record<string, string> = {
  '罗德岛相簿': '2865',
  '罗德岛闲逛部': '7748',
  '罗德岛源石记事——黑钢': '9382',
  '罗德岛源石记事——莱茵生命': '1421',
  'A1行动预备组': '0696',
  '信使安洁莉娜漫游手记': '2864',
  '序言组曲：无拘奏音': '1420',
  '罗德厨房——回甘': '8909',
  '暮岁闲谈：来拍电影吗': '5033',
  '序言组曲：猩红血钻': '3116',
  '暮岁闲谈：这是平凡人生': '4579',
  '精英干员：启程': '9381',
  '序言组曲：利锏银锋': '7747',
  '循途漫录：大将军，出击！': '7746',
  '循途漫录：王权金币': '4578',
  '暮岁闲谈：正是团圆时分': '8907',
  '序言组曲：孤行之人': '0694',
  '塞茜莉亚的安魂寻旅': '8908',
  '序言组曲：旧创': '0695',
  '一起吃个饭吧': '6252',
}

/** Bilibili episode that opens the series. Checked live. */
const ANIME_URL: Record<string, string> = {
  '61': 'https://www.bilibili.com/bangumi/play/ep706350',
  '79': 'https://www.bilibili.com/bangumi/play/ep789545',
  '108': 'https://www.bilibili.com/bangumi/play/ep1697091',
}

/** Room heading exists, but the story text lives on the activity page. */
const ACTIVITY_PAGE = new Set(['落叶逐火', '泰拉饭', '泡影苍霆', '好久不见'])

/** Plot name → HTML id on 情报处理室 when they differ. */
const ROOM_ALIAS: Record<string, string> = {
  烘炉示岁: '洪炉示岁',
}

const RA_PAGE: Record<string, string> = {
  '生息演算：沙中之火': '沙中之火',
  '生息演算：沙洲遗闻': '沙洲遗闻',
  '生息演算：重启锚点': '重启锚点',
}

export function viewLinkFor(item: PlotItem): string | null {
  const name = (item.name || '').trim()
  const kind = item.class || ''
  if (!name || kind === 'other') return null
  if (kind === 'anime') return ANIME_URL[String(item.id)] ?? null
  if (COMIC_ID[name]) return comic(COMIC_ID[name])
  if (kind === 'manga') return null
  if (ACTIVITY_PAGE.has(name) || kind === 'rougelike') return wikiPage(name)
  if (kind === 'RA') {
    const page = RA_PAGE[name]
    return page ? wikiPage(page) : null
  }
  if (kind === 'main') return mainChapter(name)
  return roomAnchor(ROOM_ALIAS[name] || name)
}
