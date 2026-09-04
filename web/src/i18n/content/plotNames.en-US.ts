/**
 * English display names for Plotline entries.
 * Sourced primarily from Moegirl (西文标题) and Arknights Terra Wiki;
 * keyed by plot id so CN `name` in Plotline.json stays the source of truth.
 */
export const plotNamesEnUS: Record<string, string> = {
  '1': "EP0. Evil Time (Part 1)", // EP0. 黑暗时代·上
  '2': "EP1. Evil Time (Part 2)", // EP1. 黑暗时代·下
  '3': "EP2. Separated Hearts", // EP2. 异卵同生
  '4': "EP3. Stinging Shock", // EP3. 二次呼吸
  '5': "EP4. Burning Run", // EP4. 急性衰竭
  '6': "Grani and The Treasure of Knights", // 骑兵与猎人
  '7': "EP5. Necessary Solutions", // EP5. 靶向药物
  '8': "Heart of Surging Flame", // 火蓝之心
  '9': "Operational Intelligence", // 战地秘闻
  '10': "Code of Brawl", // 喧闹法则
  '11': "EP6. Partial Necrosis", // EP6. 局部坏死
  '12': "Ancient Forge", // 烘炉示岁
  '13': "Stories of the Afternoon", // 午间逸话
  '14': "The God of Art", // 艺术之神
  '15': "Darknights' Memoir", // 生于黑夜
  '16': "EP7. The Birth of Tragedy", // EP7. 苦难摇篮
  '17': "Children of Ursus", // 乌萨斯的孩子们
  '18': "Twilight of Wolumonde", // 沃伦姆德的薄暮
  '19': "The Great Chief Returns", // 密林悍将归来
  '20': "Ceobe's Fungimist", // 刻俄柏的灰蕈迷境
  '21': "Rewinding Breeze", // 踏寻往昔之风
  '22': "Maria Nearl", // 玛莉娅·临光
  '23': "EP8. Roaring Flare", // EP8. 怒号光明
  '24': "Mansfield Break", // 孤岛风云
  '25': "Beyond Here", // 此地之外
  '26': "Who is Real", // 画中人
  '27': "Operation Originium Dust", // 源石尘行动
  '28': "Loyal to the Beat!", // 泰拉说唱之夜！
  '29': "A Walk in the Dust", // 遗尘漫步
  '30': "Rhodes Island's Photo Album", // 罗德岛相簿
  '31': "Under Tides", // 覆潮之下
  '32': "Rhodes Island's Walkabout Club", // 罗德岛闲逛部
  '33': "Preluding Lights", // 灯火序曲
  '34': "Interlocking Competition: Hymnoi Wisdom", // 荷谟伊智境
  '35': "Rhodes Island's Records of Originium — Blacksteel", // 罗德岛源石纪事——黑钢
  '36': "Vigilo", // 如我所见
  '37': "Rhodes Island's Records of Originium — Rhine Lab", // 罗德岛源石纪事——莱茵生命
  '38': "Dossoles Holiday", // 多索雷斯假日
  '39': "EP9. Stormwatch", // EP9. 风暴瞭望
  '40': "Pinus Sylvestris", // 红松林
  '41': "Near Light", // 长夜临光
  '42': "Break the Ice", // 风雪过境
  '43': "Phantom & Crimson Solitaire", // 傀影与猩红孤钻
  '44': "Invitation to Wine", // 将进酒
  '45': "A Light Spark in Darkness", // 阴云火花
  '46': "Guide Ahead", // 吾导先路
  '47': "Challengers Assemble: Barrage Fortress!", // 狂弹要塞！罗德大兵集结
  '48': "EP10. Shatterpoint", // EP10. 破碎日冕
  '49': "Stultifera Navis", // 愚人号
  '50': "Reserve Op Team A1", // A1行动预备组
  '51': "Lingering Echoes", // 尘影余音
  '52': "Dorothy's Vision", // 绿野幻梦
  '53': "To Be Continued", // 未尽篇章
  '54': "Ideal City: Carnival in the Endless Summer", // 理想城：长夏狂欢季
  '55': "An Obscure Wanderer", // 日暮寻路
  '56': "It's Been A While", // 好久不见
  '57': "Mizuki & Caerula Arbor", // 水月与深蓝之树
  '58': "EP11. Return to Mist", // EP11. 淬火尘霾
  '59': "IL SIRACUSANO", // 叙拉古人
  '60': "What the Firelight Casts", // 照我以火
  '61': "Lee's Detective Agency", // 鲤氏侦探事务所
  '62': "Where Vernal Winds Will Never Blow", // 登临意
  '63': "Reclamation Algorithm: Fire Within the Sand", // 生息演算：沙中之火
  '64': "A Death in Chunfen", // 春分
  '65': "A Flurry to the Flame", // 落叶逐火
  '66': "Last All-Arounder Beauty Girl! U-Official Takes You to Terra's Every Corner!", // 主播U：全能系美少女
  '67': "EP12. All Quiet Under the Thunder", // EP12. 惊霆无声
  '68': "Lone Trail", // 孤星
  '69': "Messenger Angelina's Travelogue", // 信使安洁莉娜漫游手记
  '70': "Hortus de Escapismo", // 空想花庭
  '71': "Prelude Suite: Unrestrained Melodies", // 序言组曲：无拘奏音
  '72': "Skógrinn Svartr Vill Einn Draumr", // 眠于树影之中
  '73': "Expeditioner's Jǫklumarkar", // 探索者的银凇止境
  '74': "So Long, Adele: Home Away From Home", // 火山旅梦
  '75': "Come Catastrophes or Wakes of Vultures", // 不义之财
  '76': "Design of Strife", // 纷争演绎
  '77': "EP13. The Whirlpool That Is Passion", // EP13. 恶兆湍流
  '78': "Zwillingstürme im Herbst", // 崔林特尔梅之金
  '79': "Popukar's Drawing Diary", // 小刻的画图写话
  '80': "The Rides to Lake Silberneherze", // 银心湖列车
  '81': "Rhodes Kitchen — Aftertaste", // 罗德厨房——回甘
  '82': "To the Grinning Valley", // 去咧嘴谷
  '83': "Here a People Sows", // 怀黍离
  '84': "Let's Have a Meal", // 一起吃个饭吧
  '85': "Reclamation Algorithm: Tales Within the Sand", // 生息演算：沙洲遗闻
  '86': "Operation Lucent Arrowhead", // 水晶箭行动
  '87': "You Can Be Good Enough! Terra Investment Master Class", // 好得不能再好了！泰拉投资大师课
  '88': "Babel", // 巴别塔
  '89': "EP14. Absolved Will Be the Seekers", // EP14. 慈悲灯塔
  '90': "Path of Life", // 生路
  '91': "A Kazdelian Rescue", // 熔炉“还魂”记
  '92': "Cecelia's Requiem Journey", // 塞茜莉亚的安魂寻旅
  '93': "Sarkaz's Furnaceside Fables", // 萨卡兹的无终奇语
  '94': "Adventure That Cannot Wait for the Sun", // 太阳甩在身后
  '95': "Delicious on Terra", // 泰拉饭
  '96': "Ending a Grand Overture", // 追迹日落以西
  '97': "Prelude Suite: Old Wounds", // 序言组曲：旧创
  '98': "I Portatori Dei Velluti", // 揭幕者们
  '99': "Stronghold Protocol", // 卫戍协议
  '100': "Exodus from the Pale Sea", // 出苍白海
  '101': "Such is the Joy of Our Reunion", // 相见欢
  '102': "New Year's Chat: Want to Make a Movie?", // 暮岁闲谈：来拍电影吗
  '103': "See You Soon", // 我们明日见
  '104': "When Elegies are Ashes", // 挽歌燃烧殆尽
  '105': "ARK no NIGHTS", // ARKnoNIGHTS
  '106': "EP15. Dissociative Recombination", // EP15. 离解复合
  '107': "The Masses' Travels", // 众生行记
  '108': "U Explores Terra", // U探泰拉
  '109': "Prelude Suite: Crimson Solitaire", // 序言组曲：猩红血钻
  '110': "Act or Die", // 红丝绒
  '111': "Fantasy in the Mirage", // 镜中集
  '112': "Sui's Garden of Grotesqueries", // 岁的界园志异
  '113': "New Year's Chat: This Is an Ordinary Life", // 暮岁闲谈：这是平凡人生
  '114': "Ato", // 墟
  '115': "Somniloquium Serenum", // 无忧梦呓
  '116': "Elite Operators: Departure", // 精英干员：启程
  '117': "EP16. Abnormal Spectrum", // EP16. 反常光谱
  '118': "Prelude Suite: Silver Blades", // 序言组曲：利锏银锋
  '119': "Retracing Our Steps 1101", // 雪山降临1101
  '120': "Unrealized Realities", // 未许之地
  '121': "Medjehtiqedti Bound", // 雅赛努斯复仇记
  '122': "First of a Thousand Autumns", // 辞岁行
  '123': "Crossing", // 十字路口
  '124': "People, a People", // 人们，我们
  '125': "EP17. Critical Phase Transition", // EP17. 相变临界
  '126': "Reclamation Algorithm: Relaunch Anchor", // 生息演算：重启锚点
  '127': "Thunder in the Azure Dream", // 泡影苍霆
  '128': "The Great General Strikes!", // 大将军出击！
  '129': "Jungle Complex", // 丛林症结
  '130': "The Black Flow of the Drowning Seekers", // 沉沦者的黑流树海
  '131': "Till the Lands Become an Orange", // 直到大地变成一颗酸橙
  '132': "Interactive Exhibition", // 奇象巡展
  '133': "Sur le lac lune vivante", // 月行水上
}
