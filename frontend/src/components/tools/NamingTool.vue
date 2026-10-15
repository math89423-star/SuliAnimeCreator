<template>
  <div class="naming-tool">
    <!-- 随机组合台 -->
    <div class="suli-card gen-card">
      <div class="suli-muted row-label">气质筛选</div>
      <div class="chips">
        <el-tag
          v-for="n in poolNames"
          :key="n"
          :effect="poolOn[n] ? 'dark' : 'plain'"
          class="chip"
          @click="togglePool(n)"
        >{{ n }}</el-tag>
      </div>
      <div class="btns">
        <el-button type="primary" size="small" @click="rollCNDeck">随机中文名</el-button>
        <el-button type="primary" size="small" @click="rollENDeck">随机英文名</el-button>
        <el-button size="small" @click="rollTipDeck">摇一招启发</el-button>
        <el-button size="small" @click="copyCNDeck">复制中文候选</el-button>
        <el-button size="small" @click="copyENDeck">复制英文候选</el-button>
        <el-button size="small" @click="clearDeck">清空</el-button>
      </div>
      <div class="out-row">
        <span class="suli-muted out-label">中文</span>
        <div class="outs">
          <el-tag v-for="c in cnCands" :key="c.name" class="out-tag" @click="copyOne(c.name)">
            {{ c.name }}<span class="out-sub">{{ c.tag }}</span>
          </el-tag>
          <span v-if="!cnCands.length" class="suli-muted empty">待摇</span>
        </div>
      </div>
      <div class="out-row">
        <span class="suli-muted out-label">英文</span>
        <div class="outs">
          <el-tag v-for="c in enCands" :key="c.name" type="success" class="out-tag" @click="copyOne(c.name)">
            {{ c.name }}<span class="out-sub">{{ c.tag }}</span>
          </el-tag>
          <span v-if="!enCands.length" class="suli-muted empty">待摇</span>
        </div>
      </div>
      <div class="out-row">
        <span class="suli-muted out-label">招式</span>
        <div class="outs">
          <el-tag v-for="c in tipCands" :key="c.name" type="warning" class="out-tag" @click="copyOne(c.full)">
            {{ c.name }}<span class="out-sub">{{ c.tag }}</span>
          </el-tag>
          <span v-if="!tipCands.length" class="suli-muted empty">待摇</span>
        </div>
      </div>
    </div>

    <!-- 素材搜索托盘 -->
    <div class="tray suli-card">
      <div class="tray-row">
        <el-input v-model="query" placeholder="搜索：霜 / Luna / 词根 / 避雷 ..." clearable size="small" class="tray-search" />
        <span class="suli-muted count">{{ filtered.length }} / {{ allItems.length }}</span>
        <el-button size="small" @click="clearFilter">清空</el-button>
        <el-button size="small" text @click="toggleTray">{{ trayOpen ? '收起 ▲' : '展开 ▼' }}</el-button>
      </div>
      <template v-if="trayOpen">
      <div class="chips">
        <el-tag v-for="c in cats" :key="c" :effect="active === c ? 'dark' : 'plain'" class="chip" @click="active = c">{{ c }}</el-tag>
      </div>
      </template>
    </div>

    <!-- 统一卡片网格 -->
    <div v-if="filtered.length" class="card-grid">
      <div v-for="it in filtered" :key="it.id" class="suli-card tool-card" :class="{ open: isOpen(it.id) }" @click="toggleDetail(it.id)">
        <div class="cover">{{ it.cover }}</div>
        <div class="title-row"><span class="zh">{{ it.title }}</span><span v-if="it.en" class="en">{{ it.en }}</span></div>
        <div class="tags"><el-tag size="small" type="info">{{ it.cat }}</el-tag><el-tag v-if="it.tag" size="small">{{ it.tag }}</el-tag></div>
        <div class="summary">{{ it.summary }}</div>
        <el-dialog append-to-body :model-value="isOpen(it.id)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
          <div class="detail-block" @click.stop>
          <div class="detail-cols">
            <div class="detail-cover">{{ it.cover }}</div>
            <div>
              <div class="detail-title"><span class="zh">{{ it.title }}</span><span v-if="it.en" class="en">{{ it.en }}</span></div>
              <div class="tags"><el-tag size="small" type="info">{{ it.cat }}</el-tag><el-tag v-if="it.tag" size="small">{{ it.tag }}</el-tag></div>
              <p class="detail-summary">{{ it.summary }}</p>
            </div>
          </div>
          <ul class="plain"><li v-for="(d, i) in it.detail" :key="i">{{ d }}</li></ul>
          <pre class="suli-pre mono">复制文本：{{ it.copy }}</pre>
          <div class="detail-actions">
            <el-button size="small" @click.stop="addToCN(it)">加入中文候选</el-button>
            <el-button size="small" @click.stop="addToEN(it)">加入英文候选</el-button>
            <el-button type="primary" size="small" @click.stop="copyItem(it)">复制</el-button>
            <el-button size="small" @click.stop="openKey=null">收起</el-button>
          </div>
        </div>
        </el-dialog>
      </div>
    </div>
    <div v-else class="suli-muted empty-state">无匹配，换关键词或点清空。</div>

    <!-- 撞名自检 -->
    <div class="suli-card check-card">
      <h3>撞名自检 · 热门角色避让</h3>
      <div class="check-bar">
        <el-input v-model="checkInput" placeholder="输入候选名，如：萧炎 / 苏晞 / Luna" clearable @keyup.enter="runCheck" />
        <el-button type="primary" @click="runCheck">检测</el-button>
      </div>
      <div class="check-links">
        <el-link type="primary" :href="searchCN" target="_blank" rel="noopener">百度·名+角色</el-link>
        <el-link type="primary" :href="searchBK" target="_blank" rel="noopener">Bing·名+角色</el-link>
        <el-link type="primary" :href="searchNV" target="_blank" rel="noopener">Bing·名+小说</el-link>
      </div>
      <ul v-if="checked" class="plain">
        <li v-for="(l, i) in checkLines" :key="i">
          <span v-if="l.kind === 'hi'" class="risk-hi">{{ l.head }}</span><span v-else-if="l.kind === 'mid'" class="risk-mid">{{ l.head }}</span><span v-else-if="l.kind === 'ok'" class="risk-ok">{{ l.head }}</span>{{ l.body }}
        </li>
      </ul>
      <ul v-else class="plain"><li>等待检测……</li></ul>
      <div v-for="g in hotGroups" :key="g.tag" class="pool-block">
        <div class="subh"><span>{{ g.tag }}雷区（点卡片复制，拿去检索）</span></div>
        <div class="grid wide">
          <div v-for="x in g.items" :key="x.n" class="mini-card dim" @click="copyOne(x.n)">
            <div class="zh">{{ x.n }}</div>
            <div class="meta">{{ x.src }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { copyText } from '../../utils/clipboard'

interface Cand { name: string; tag: string; full: string }
interface HotName { n: string; src: string; tag: string }
interface CheckLine { kind: 'hi' | 'mid' | 'ok' | 'tip'; head: string; body: string }
interface CardItem { id: string; cat: string; tag: string; title: string; en: string; cover: string; summary: string; detail: string[]; copy: string }

/* ---- 词池（与 naming.html 一字不差） ---- */
const SURNAMES: string[] = ['顾','沈','陆','苏','江','白','温','阮','谢','宋','程','许','林','叶','唐','裴','萧','黎','简','霍']
const WILDCARDS: string[] = ['知','未','见','亦','初','晚','微','若','听','栖','言','与']

const CN_POOLS: Record<string, string[]> = {
  '清冷疏离': ['凛','霜','澈','寂','雪','寒','白','疏','月','汐'],
  '温柔治愈': ['暖','柔','晞','棠','绵','晏','柚','穗','雾','梨'],
  '活泼元气': ['晴','柠','果','葵','夏','菁','跃','糖','荞','沐'],
  '神秘幽深': ['幽','冥','夜','涟','檀','玄','眠','溯','朦','湮'],
  '典雅贵气': ['瑾','瑜','瑶','琬','泓','翎','霄','珮','璇','璋'],
  '少年锐气': ['冽','崖','穹','铮','临','越','砺','骋','彧','骁'],
  '邪气魅惑': ['魅','绯','罂','枭','惘','靡','妩','煞','胭','蚀'],
  '中式古风': ['微','若','卿','墨','澜','辞','鹤','筝','砚','袖']
}

const CN_COMBOS: string[] = ['知霜','凛月','疏白','未晞','绵棠','晏禾','柠夏','果晴','夜檀','玄溯','瑾瑜','翎霄','临冽','越崖','绯枭','靡音','若微','墨澜','栖月','见微']

const TECHNIQUES: Array<[string, string, string]> = [
  ['母题倒推法', '一句话母题 → 1 个意象字 + 1 个质感字 → 组合', '陆霜'],
  ['冷暖反差法', '姓清冷 + 名温柔，或姓柔软 + 名凛冽——反差即记忆点', '陆知暖'],
  ['虚实相生', '实词 + 虚词（若/未/知/亦/初/晚/微）', '江未晞'],
  ['典故化用', '《诗经》《楚辞》取词，但别叠生僻字', '沈见微'],
  ['颜色材质化', '绯/墨/银/玖…… 与发色瞳色配色联动', '白绯'],
  ['昵称测试', '定名前先想昵称：小霜、阿染、染染长不长得出来', '苏染'],
  ['双关谐音', '高风险高收益，必须过避雷清单', '吴晴(慎)']
]

const EN_POOLS: Record<string, Array<[string, string]>> = {
  '清冷': [['Elara','希腊·明亮'],['Isolde','亚瑟王·冰清'],['Vesper','拉丁·薄暮'],['Morana','斯拉夫·冬神'],['Arianell','威尔士·银']],
  '温柔': [['Elowen','康沃尔·榆树'],['Celine','法语·天堂'],['Liora','希伯来·我的光'],['Amaryllis','希腊·花名'],['Felicity','拉丁·幸福']],
  '元气': [['Poppy','英·罂粟花'],['Zoe','希腊·生命'],['Lumi','芬兰·雪'],['Kiki','昵称感'],['Bonnie','苏格兰·美']],
  '神秘': [['Morrigan','凯尔特·女战神'],['Selene','希腊·月神'],['Circe','希腊·女巫'],['Nyx','希腊·夜'],['Vespera','拉丁·晚祷']],
  '贵气': [['Aurelia','拉丁·金'],['Seraphina','希伯来·火焰翼'],['Ophelia','希腊'],['Cordelia','拉丁·心'],['Juliana','拉丁·世家']],
  '飒/少年': [['Kael','凯尔特·强音'],['Aeron','威尔士·战斗'],['Raven','英·乌鸦'],['Wren','英·鹪鹩'],['Sable','英·黑']],
  '邪气': [['Morgana','亚瑟王·女巫'],['Ravenna','意大利·黑羽城'],['Delphine','法语·海豚/幽'],['Noctis','拉丁·夜']],
  '奇幻造词': [['Aelira','ael+ira 空灵'],['Nivara','niv(雪)+ara'],['Solmira','sol(日)+mira'],['Vaelis','vae+lis 冷感'],['Sylwen','syl(林)+wen(圣)']]
}

const EN_ROOTS: Array<[string, string, string]> = [
  ['光','lux / luc / phos · Sól · Aine','Lucia'],
  ['月','luna / selene · Máni','Selene'],
  ['星','stella / aster','Estella'],
  ['雪','nix / niv · Snær','Nivara'],
  ['花','flos / flora · Blodeuwedd','Flora'],
  ['血','sanguis','Sanguine'],
  ['夜','nox / nyx · Nótt','Nyx'],
  ['风','ventus · Vindr · Gwynt','Zephyra'],
  ['海','mare / marin · Sær · Muir','Marina'],
  ['影','umbra / skia','Umbra'],
  ['心','cor / cardia · Hjarta','Cordelia'],
  ['金银','aurum / argentum · Arian','Aurelia'],
  ['圣','sanctus · Gwyn / Gwen','Seraphina'],
  ['雾','nephele','Nephele']
]

const EN_PREFIX: Array<[string, string]> = [['Ael','光/气'],['Ni','雪(niv-)'],['Syl','林(sylva)'],['Lu','光(lux)'],['El','光/星'],['Ver','真/春'],['Ast','星(aster)'],['Sol','太阳'],['Nox','夜'],['Sel','月']]
const EN_SUFFIX: Array<[string, string]> = [['ira','柔美收尾'],['ara','空灵'],['wen','凯尔特·白/圣'],['dra','奇幻'],['elle','法风柔'],['ine','法风'],['ora','拉丁感'],['is','清冷'],['yn','现代'],['th','神秘']]

const KANJI: Array<[string, string]> = [['玖','ku / kyū'],['染','zen'],['雪','setsu'],['凛','rin'],['绯','hi'],['霜','sō'],['澪','rei'],['蓮','ren'],['菫','kin'],['蕾','rai'],['枫','fū'],['夜','ya']]

const PITFALLS: string[] = [
  '撞热门角色名（先搜「名字＋角色」）',
  '烂大街组合（梓涵、雨欣、子轩类）',
  '生僻字（翀、鸩、婳）——不利读写与检索',
  '多音字（行/还/重）——喊错就废',
  '负面谐音（吴晴=无情、范桐=饭桶）',
  '性别指向混乱（除非设定需要）',
  '年代违和（现代都市角色叫慕容素心）',
  '与母题冲突（清冷角色叫甜甜）',
  '与项目内已有角色撞音/撞字',
  '太文青用力过猛（生僻+多音+典故叠满=没人会念）',
  '英文：知名角色/品牌同名（Saber、Lilith 类慎用）',
  '英文：通用词被搜索淹没（Snow、Grace、Sky）',
  '英文：拼写歧义（Ceilidh、Siobhan——好看但没人读得对）',
  '英文：与中文名母题脱节（中英必须同一气质）',
  '网文/小说角色重名（萧炎、叶修、韩立级高频名）——用下方自检清单先过一遍',
  '真人明星名（白鹿、刘亦菲）与历史人物名（萧衍、上官婉儿）同样要避',
  '英文：神话名超载（Nyx、Freya、Athena、Loki）——搜得到但不像你独占'
]

const SOUND_ROWS: Array<[string, string, string]> = [
  ['-a / -ia / -elle / -ine / -ette', '柔美、甜、法风', 'Liora / Celine / Roselle'],
  ['-x / -r / -n / -th', '飒、神秘、冷', 'Nyx / Aeron / Raven / Kaelith'],
  ['-y / -ie', '活泼、亲近', 'Poppy / Effie / Bonnie'],
  ['s / f / l / v', '柔和摩擦音', 'Selene / Felicity'],
  ['k / t / d / g', '有力、清晰', 'Kael / Cordelia'],
  ['r', '野性、张力', 'Morrigan / Ravenna'],
  ['w / ae / ei', '童话、奇幻', 'Elowen / Aelira']
]

const TRANSFER_ROWS: Array<[string, string, string]> = [
  ['工程代号 / 文件夹 / 文件名', '拼音音译（jiuran）', '唯一、稳定、跨语言不歧义'],
  ['作品内角色名 / 封面标题', '正式中文名 / 意译英文名', '可读、有气质'],
  ['海外署名 / 社区 ID', '音译或造词英文名', '检索友好']
]

const STEPS: string[] = [
  '① 提炼母题关键词 3 个（如：疏离、现代、工艺感）',
  '② 中文名发散：挑 2-3 类气质各出 3 个候选，全部念出来筛（语音转文字验证）',
  '③ 英文名生成：五路各出 1（音译/意译/造词/混成/神话），标注读音',
  '④ 重名检索：撞名自检过清单 ＋「名＋角色 / 名＋小说 / 名＋演员」外部三搜，撞了就换（变体四招）',
  '⑤ 终检 + 落盘 character.md（正式名/罗马字/读音）＋ PROGRESS 记录'
]

const FINAL_CHECK: string[] = [
  '喊得出？ · 记得住（2-3 音节）？ · 写得对（无生僻/多音/拼写坑）？ · 配母题（气质同频）？',
  '无负面联想（谐音/文化雷）？ · 昵称与缩写可延展？ · 中英名同母题？ · 重名三搜通过（角色/小说/真人）？'
]

const HEURISTICS: Record<string, Array<[string, string, string]>> = {
  '通用·音形义': [
    ['可发音优先', '看到会念、念了会拼；Q/X/变音符/撇号一律砍', 'Smaug ✓ / Whadahellaryucallinmethisforax ✗'],
    ['音节制', '现实人名多为 1-3 音节；超出当称号用，别当名字', 'Smaug（单音节照样霸气）'],
    ['拼写即读音', '英语 44 音素只有 26 字母，凭音拼写；拿不准问别人会怎么拼', 'Kael ✓ / Xx\'yrra ✗'],
    ['首字母不撞', '同作品角色首字母尽量不同；撞了让两人少同框', 'Stephen King 招'],
    ['软硬音', 'k/t/d/g 硬（飒）；s/f/l/m/n/v 软（柔）', 'Kael（硬）/ Selene（软）'],
    ['尾音定气场', '中文尾字多用二声四声有力；英语 -a 柔、-x 锐', '段誉/郭靖/杨过（四声收尾）'],
    ['乐感测试', '念出来顺口：首尾字母衔接流动', 'Jessica Jones'],
    ['昵称可延展', '全名长得出昵称，昵称量化亲疏', 'Gwendolyn → Gwen / Lyn'],
    ['字形不撞车', '同书别用同偏旁/近形字', '阿瀧/阿嚨/阿瓏 十连击 ✗'],
    ['含义别太直白', '用根义承载，不用大白话', 'Hope ✗ → Nadia（=希望）✓']
  ],
  '中文·网文社区': [
    ['网文大姓池', '萧叶方陈楚沈苏李秦林陆唐许——眼缘＋代入感', '萧、叶、沈、苏'],
    ['主角名常用字池', '东南北、易逸毅、宣轩类，陌生度低', '叶辰、苏逸'],
    ['生僻姓劝退', '冷门姓＋偏僻字＝第一眼就败；要冷只冷一个字', '翀姓 ✗'],
    ['声母韵母避重', '同声母/同韵母连发拗口要拆', '余永远 ✗ / 李玺绮 ✗'],
    ['声调错配', '一二声与三四声交错，避免全同调', '余云雯（全一声）✗'],
    ['音义结合', '名字暗合命运/身份，巧而不露', '岳不群=小人合而不群'],
    ['出戏三禁', '不违背背景、不违背形象、念着不拗口', '古代叫志明 ✗'],
    ['梦幻名看语境', '现代都市慎用玄幻名，仙侠古风可堆', '独孤醉（现代设定）✗'],
    ['身份用字分层', '醉梦魅恋情泪怜＝烟火气；贵族名门别用', '皇亲叫\'怜\' ✗'],
    ['撞名人一票否决', '撞明星/谐星名阻碍形象建立', '贺一航、吴宗宪式 ✗'],
    ['叠字控龄', '叠字降龄（眠眠）；成熟角色慎用，单名提气场', '阮眠眠 vs 陆凛'],
    ['三凑应急法', '朋友名 × 百家姓 × 字典随机字凑顺口（保底）', '阿辉、阿拓']
  ],
  '日系·ACG 命名法': [
    ['名字叙事法', '名字暗示能力与主题', '鸣人=鸣门卷+漩涡'],
    ['姓氏自然化', '姓氏取地理/自然：一块地、一件物', '春野、朽木、黑崎'],
    ['颜色·季节代码', '全名连读成一个意象', '春野樱=春天的樱'],
    ['数字命名法', '代号 → 读音 → 名字', 'FranXX 015 → ichi+go → Ichigo'],
    ['辈行名', '太郎/次郎/三郎标兄弟序位；同音不同字不算', '士郎≠四郎'],
    ['反讽命名', '名字即矛盾', '"光"写在夜神家姓下'],
    ['字谜·奇葩名', '成词成句/同字重复/数字名——留给梗角色', '糸色望=绝望'],
    ['反差萌命名', '名字与形象错位制造反差', '另类名字萌属性'],
    ['汉字不硬拼', '别拼历史不共现的字；别造假日语名', '龙+剑式 ✗'],
    ['绕开 cliché', '黑=Kuro、暗=Yami、Ren 已用烂；把组合打散', '暗＋河床 / 暗＋正午']
  ],
  '英文·西幻社区': [
    ['时代地域校检', '名字要合年代与地域；文化归属别错配', 'Kwan 是中文姓 ✗日裔'],
    ['姓氏四源', '父名/地名/职业/特征', 'Jackson / Washington / Carter / White'],
    ['根义承重', '用词源暗线承重，不写大白话', 'Vader=荷兰语父亲 · Frodo=以经验得智慧'],
    ['名姓配比', '常用名配独特姓（或全普通/全独特），别半吊子', 'Bilbo Baggins'],
    ['同首字母慎用', '主角团首字母别撞；撞了安排少同屏', 'Stephen King 招'],
    ['知名联想排查', '避开历史名人/品牌/明星', 'Adolf / Napoleon ✗'],
    ['拼写做旧', '读音不变拼写更难忘（低风险近形换字）', 'Jenkins → Jenkyns'],
    ['配角低调原则', '高辨识名留给重要角色，背景角色用普通名', '路人叫 Ann'],
    ['变体一致性', '定名后全局替换含昵称表；中途改名是灾难', '用编辑器整词替换'],
    ['问人直觉', '拿候选问 3 个人\'像什么性格\'', '"你不像叫 Arlene 的"']
  ],
  '造词·灵感': [
    ['词根拼装法', '实义词根＋风格后缀', 'niv(雪)＋ara → Nivara'],
    ['词典考古法', '查同义词的拉丁/古语翻译取碎片', 'shadow → sceadu'],
    ['首字母骰子', '随机字母开头硬造再修剪', 'Excel RND 法'],
    ['十十骰面法', '10 个名 × 10 个姓随机抽', '写作论坛法'],
    ['环境取材法', '招牌/菜单/路牌/包装上找音', 'craft store 法'],
    ['谐音换皮法', '取现成词发音换拼写', 'sceadu＝shadow'],
    ['母题锚词法', '先写 3 个母题词 → 查同义/翻译 → 拼装', '疏离+现代+工艺感'],
    ['读出声收尾', '候选全部读出声＋语音转文字验证', '识别不了就淘汰']
  ],
  '古风·国风（诗经楚辞派）': [
    ['男楚辞女诗经', '男名取楚辞瑰丽、女名取诗经柔美；按气质取用即可', '望舒《离骚》/ 静姝《静女》'],
    ['诗句截取法', '从原句截两字自带典故', '婉清《野有蔓草》'],
    ['香草美人系统', '楚辞香草字库：杜若、杜衡、木兰、蕙芷、辛夷、辟芷', '杜若、辛夷'],
    ['意象＋品格两段式', '前半意象字、后半品格字', '既明 / 信芳 / 修能'],
    ['平仄验音', '双阳平也顺（芙荷）；避免三字同调堆叠，仄声收尾有力', '芙荷'],
    ['查原句语境', '截词前先读原句，别截负面语境', '"扬波"另一义＝动乱'],
    ['生僻有度', '一字生僻配一字常见；铄金/凌虚式日常难念', '兰畹 ✓ / 铄金 ✗'],
    ['成对命名', '双胞胎/镜像角色用同根异字成对词', '杜若／杜衡'],
    ['朝代用字校验', '先秦/汉唐/明清风格不同；仙侠可超时代，都市不行', '明清背景别用先秦名'],
    ['传统附加层慎用', '五行八字/数理是现实起名层，虚构角色可无视', '除非角色设定需要']
  ],
  '世界观·语言一致性': [
    ['音色面板先行', '每个文化先定 5-8 辅音＋5 元音面板，再拼名', 'r/worldbuilding 共识'],
    ['命名语言法', '只造够起名的迷你词表，够用即停', 'Zompist naming language'],
    ['词根组合法', '词根 A＋词根 B 派生', 'rock=stun → stunriver'],
    ['文化可辨识性', '同文化名字像一家，异文化一耳朵听出差别', '两族音系明显不同'],
    ['地名分层逻辑', '老地名是河山；后世叠加翻译层', 'Los Angeles／Bakersfield'],
    ['冗余命名梗', '真实地名常双语冗余叠加，可当地层线索', 'River Avon＝河河'],
    ['后缀系统', '每文化配 3-5 个地名/家族后缀', '-ton/-burg/-ville/-chester'],
    ['禁装饰撇号', '撇号必须代表真实音（喉塞音），不能当装饰', 'apostrophe disease ✗'],
    ['三测收口', '读得顺、拼得出、同作品内不撞', '读+拼+查'],
    ['语义自然化', '含义要像母语者会有的意思，别像翻译腔', '"光明之风"式 ✗']
  ],
  '家族·派系·组织': [
    ['字辈系统', '同辈共享中间字（姓＋辈字＋名）', '家族链一目了然'],
    ['派系前缀/后缀', '门派组织统一格式化，批量产名不乱', '云梦江氏式'],
    ['命名呼应组', '主角团共享一个共同意象', '星象 / 矿物 / 花卉 / 乐器'],
    ['反派命名法', '硬音/矿物/古语；或圣洁字眼作反讽', '夜神"光"'],
    ['命名预算留白', '高辨识名只给重要角色，配角用普通名', '路人叫 Ann']
  ]
}

const HOT_NAMES: HotName[] = [
  { n: '蕾姆', src: 'Re:从零开始的异世界生活', tag: '日系ACG' },
  { n: '爱蜜莉雅', src: 'Re:从零开始的异世界生活', tag: '日系ACG' },
  { n: '初音未来', src: 'VOCALOID', tag: '日系ACG' },
  { n: '亚丝娜', src: '刀剑神域', tag: '日系ACG' },
  { n: '阿尔托莉雅', src: 'Fate 系列（Saber）', tag: '日系ACG' },
  { n: '御坂美琴', src: '魔法禁书目录 / 超炮', tag: '日系ACG' },
  { n: '灰原哀', src: '名侦探柯南', tag: '日系ACG' },
  { n: '绫波丽', src: 'EVA', tag: '日系ACG' },
  { n: '明日香', src: 'EVA', tag: '日系ACG' },
  { n: '薇尔莉特', src: '紫罗兰永恒花园', tag: '日系ACG' },
  { n: '祢豆子', src: '鬼灭之刃', tag: '日系ACG' },
  { n: '五条悟', src: '咒术回战', tag: '日系ACG' },
  { n: '雪之下雪乃', src: '我的青春恋爱物语果然有问题', tag: '日系ACG' },
  { n: '甘雨', src: '原神', tag: '国产游戏' },
  { n: '刻晴', src: '原神', tag: '国产游戏' },
  { n: '胡桃', src: '原神（亦为通用词）', tag: '国产游戏' },
  { n: '雷电将军', src: '原神', tag: '国产游戏' },
  { n: '八重神子', src: '原神', tag: '国产游戏' },
  { n: '纳西妲', src: '原神', tag: '国产游戏' },
  { n: '阿米娅', src: '明日方舟', tag: '国产游戏' },
  { n: '菲比', src: '鸣潮', tag: '国产游戏' },
  { n: '今汐', src: '鸣潮', tag: '国产游戏' },
  { n: '流萤', src: '崩坏：星穹铁道', tag: '国产游戏' },
  { n: '三月七', src: '崩坏：星穹铁道', tag: '国产游戏' },
  { n: '冯宝宝', src: '一人之下', tag: '国漫' },
  { n: '涂山苏苏', src: '狐妖小红娘', tag: '国漫' },
  { n: '萧炎', src: '斗破苍穹', tag: '网文小说' },
  { n: '林动', src: '武动乾坤', tag: '网文小说' },
  { n: '牧尘', src: '大主宰', tag: '网文小说' },
  { n: '韩立', src: '凡人修仙传', tag: '网文小说' },
  { n: '叶修', src: '全职高手', tag: '网文小说' },
  { n: '徐凤年', src: '雪中悍刀行', tag: '网文小说' },
  { n: '陈平安', src: '剑来', tag: '网文小说' },
  { n: '宁缺', src: '将夜', tag: '网文小说' },
  { n: '范闲', src: '庆余年', tag: '网文小说' },
  { n: '宁毅', src: '赘婿', tag: '网文小说' },
  { n: '叶凡', src: '遮天', tag: '网文小说' },
  { n: '石昊', src: '完美世界', tag: '网文小说' },
  { n: '罗峰', src: '吞噬星空', tag: '网文小说' },
  { n: '唐三', src: '斗罗大陆', tag: '网文小说' },
  { n: '张小凡', src: '诛仙', tag: '网文小说' },
  { n: '克莱恩', src: '诡秘之主', tag: '网文小说' },
  { n: '许七安', src: '大奉打更人', tag: '网文小说' },
  { n: '楚子航', src: '龙族', tag: '网文小说' },
  { n: '路明非', src: '龙族', tag: '网文小说' },
  { n: '张起灵', src: '盗墓笔记', tag: '网文小说' },
  { n: '吴邪', src: '盗墓笔记', tag: '网文小说' },
  { n: '胡八一', src: '鬼吹灯', tag: '网文小说' },
  { n: '哈利', src: '哈利·波特', tag: '西幻欧美' },
  { n: '赫敏', src: '哈利·波特', tag: '西幻欧美' },
  { n: '弗罗多', src: '指环王', tag: '西幻欧美' },
  { n: '莱戈拉斯', src: '指环王', tag: '西幻欧美' },
  { n: '丹妮莉丝', src: '权力的游戏', tag: '西幻欧美' },
  { n: '琼恩', src: '权力的游戏', tag: '西幻欧美' },
  { n: '凯特尼斯', src: '饥饿游戏', tag: '西幻欧美' },
  { n: '甘道夫', src: '指环王', tag: '西幻欧美' },
  { n: '白鹿', src: '演员', tag: '真人明星' },
  { n: '刘亦菲', src: '演员', tag: '真人明星' },
  { n: '杨幂', src: '演员', tag: '真人明星' },
  { n: '迪丽热巴', src: '演员', tag: '真人明星' },
  { n: '赵丽颖', src: '演员', tag: '真人明星' },
  { n: '萧衍', src: '历史人物（梁武帝）', tag: '历史人物' },
  { n: '上官婉儿', src: '历史人物（唐代）', tag: '历史人物' },
  { n: '李清照', src: '历史人物（宋代词人）', tag: '历史人物' },
  { n: '谢道韫', src: '历史人物（东晋才女）', tag: '历史人物' },
  { n: '卓文君', src: '历史人物（汉代）', tag: '历史人物' },
  { n: 'Luna', src: '哈利·波特 / 多作品通用', tag: '英文名' },
  { n: 'Saber', src: 'Fate 系列', tag: '英文名' },
  { n: 'Asuna', src: '刀剑神域', tag: '英文名' },
  { n: 'Mikasa', src: '进击的巨人', tag: '英文名' },
  { n: 'Levi', src: '进击的巨人', tag: '英文名' },
  { n: 'Naruto', src: '火影忍者', tag: '英文名' },
  { n: 'Sasuke', src: '火影忍者', tag: '英文名' },
  { n: 'Goku', src: '龙珠', tag: '英文名' },
  { n: 'Zelda', src: '塞尔达传说', tag: '英文名' },
  { n: 'Link', src: '塞尔达传说（通用词）', tag: '英文名' },
  { n: 'Aerith', src: '最终幻想 VII', tag: '英文名' },
  { n: 'Tifa', src: '最终幻想 VII', tag: '英文名' },
  { n: 'Cloud', src: '最终幻想 VII（通用词）', tag: '英文名' },
  { n: 'Sephiroth', src: '最终幻想 VII', tag: '英文名' },
  { n: 'Hermione', src: '哈利·波特', tag: '英文名' },
  { n: 'Katniss', src: '饥饿游戏', tag: '英文名' },
  { n: 'Raven', src: 'DC 少年泰坦（通用词）', tag: '英文名' },
  { n: 'Morrigan', src: '凯尔特神话 / 龙腾世纪', tag: '英文名' },
  { n: 'Selene', src: '黑夜传说 / 希腊月神', tag: '英文名' },
  { n: 'Freya', src: '北欧神话 / 战神', tag: '英文名' },
  { n: 'Loki', src: '北欧神话 / 漫威', tag: '英文名' },
  { n: 'Athena', src: '希腊神话', tag: '英文名' },
  { n: 'Artemis', src: '希腊神话', tag: '英文名' },
  { n: 'Persephone', src: '希腊神话', tag: '英文名' },
  { n: 'Nyx', src: '希腊神话（已高度超载）', tag: '英文名' }
]

/* ---- 派生索引 ---- */
const poolNames: string[] = Object.keys(CN_POOLS)
const enKeys: string[] = Object.keys(EN_POOLS)
const heurKeys: string[] = Object.keys(HEURISTICS)
const HEUR_FLAT: Array<{ g: string; t: [string, string, string] }> = []
heurKeys.forEach((k) => { heurGroup(k).forEach((t) => HEUR_FLAT.push({ g: k, t })) })
const prefixAll: string = EN_PREFIX.map((p) => p[0]).join(', ')
const suffixAll: string = EN_SUFFIX.map((s) => s[0]).join(', ')

function poolChars(n: string): string[] { return CN_POOLS[n] ?? [] }
function poolJoin(n: string): string { return poolChars(n).join('、') }
function enGroup(k: string): Array<[string, string]> { return EN_POOLS[k] ?? [] }
function heurGroup(k: string): Array<[string, string, string]> { return HEURISTICS[k] ?? [] }
function heurLine(t: [string, string, string]): string { return t[0] + '：' + t[1] + '（例：' + t[2] + '）' }

/* ---- 状态 ---- */
const poolOn = reactive<Record<string, boolean>>({})
poolNames.forEach((n) => { poolOn[n] = true })
const cnCands = ref<Cand[]>([])
const enCands = ref<Cand[]>([])
const tipCands = ref<Cand[]>([])
const query = ref<string>('')
const active = ref<string>('全部')
const openKey = ref<string | null>(null)
const TRAY_LS = 'suli-naming-tray'
let trayInit = true
try { trayInit = localStorage.getItem(TRAY_LS) !== '0' } catch {}
const trayOpen = ref<boolean>(trayInit)
function toggleTray(): void {
  trayOpen.value = !trayOpen.value
  try { localStorage.setItem(TRAY_LS, trayOpen.value ? '1' : '0') } catch {}
}

const checkInput = ref<string>('')
const checked = ref<boolean>(false)
const checkLines = ref<CheckLine[]>([])

const cnTotal = computed<number>(() => poolNames.reduce((s, n) => s + poolChars(n).length, 0))
const enTotal = computed<number>(() => enKeys.reduce((s, k) => s + enGroup(k).length, 0))
const heurTotal = computed<number>(() => heurKeys.reduce((s, k) => s + heurGroup(k).length, 0))
const hotTotal = computed<number>(() => HOT_NAMES.length)
const hotGroups = computed<Array<{ tag: string; items: HotName[] }>>(() => {
  const order: string[] = []
  const map = new Map<string, HotName[]>()
  for (const h of HOT_NAMES) {
    if (!map.has(h.tag)) { map.set(h.tag, []); order.push(h.tag) }
    const arr = map.get(h.tag)
    if (arr) arr.push(h)
  }
  return order.map((tag) => ({ tag, items: map.get(tag) ?? [] }))
})
const searchCN = computed<string>(() => 'https://www.baidu.com/s?wd=' + encodeURIComponent(checkInput.value.trim() + ' 角色'))
const searchBK = computed<string>(() => 'https://www.bing.com/search?q=' + encodeURIComponent(checkInput.value.trim() + ' 角色'))
const searchNV = computed<string>(() => 'https://www.bing.com/search?q=' + encodeURIComponent(checkInput.value.trim() + ' 小说 角色'))

/* ---- 统一卡片索引（只读派生，不改数据常量） ---- */
const cats: string[] = ['全部', '中文选字', '中文组合', '结构技法', '英文名库', '英文词根', '前后缀', '音韵速查', '汉字音读', '互转流程', '启发技巧', '避雷清单']
const allItems = computed<CardItem[]>(() => {
  const out: CardItem[] = []
  poolNames.forEach((n: string) => {
    poolChars(n).forEach((c: string) => {
      out.push({ id: 'cn-' + n + '-' + c, cat: '中文选字', tag: n, title: c, en: '', cover: c, summary: n + '气质单字', detail: ['所属气质：' + n, '用法：配姓成名，单名提气场、双名可加虚词', '整组：' + poolJoin(n)], copy: c })
    })
  })
  CN_COMBOS.forEach((c: string) => {
    out.push({ id: 'combo-' + c, cat: '中文组合', tag: '双字示例', title: c, en: '', cover: c, summary: '中文双字组合示例', detail: ['用法：直接用作名，或拆字替换'], copy: c })
  })
  TECHNIQUES.forEach((t: [string, string, string], i: number) => {
    out.push({ id: 'tech-' + i, cat: '结构技法', tag: '七式', title: t[0], en: '', cover: t[0].slice(0, 1), summary: t[1], detail: ['用法：' + t[1], '例：' + t[2]], copy: t[0] + '：' + t[1] + '（例：' + t[2] + '）' })
  })
  enKeys.forEach((k: string) => {
    enGroup(k).forEach((p: [string, string]) => {
      out.push({ id: 'en-' + k + '-' + p[0], cat: '英文名库', tag: k, title: p[0], en: p[1], cover: p[0].slice(0, 1).toUpperCase(), summary: k + '气质', detail: ['气质分区：' + k, '含义出处：' + p[1]], copy: p[0] })
    })
  })
  EN_ROOTS.forEach((r: [string, string, string], i: number) => {
    out.push({ id: 'root-' + i, cat: '英文词根', tag: '词根拼装', title: r[0], en: r[1], cover: r[0], summary: '成品名例：' + r[2], detail: ['词根：' + r[1], '成品名例：' + r[2], '用法：实义词根 + 风格后缀'], copy: r[1] })
  })
  EN_PREFIX.forEach((p: [string, string], i: number) => {
    out.push({ id: 'pre-' + i, cat: '前后缀', tag: '前缀', title: p[0], en: p[1], cover: p[0].slice(0, 1).toUpperCase(), summary: '前缀：' + p[1], detail: ['含义：' + p[1], '配方：前缀（意象）+ 后缀（风格收尾）', '全部前缀：' + prefixAll], copy: p[0] })
  })
  EN_SUFFIX.forEach((s: [string, string], i: number) => {
    out.push({ id: 'suf-' + i, cat: '前后缀', tag: '后缀', title: s[0], en: s[1], cover: s[0].slice(0, 1).toUpperCase(), summary: '后缀：' + s[1], detail: ['含义：' + s[1], '配方：前缀（意象）+ 后缀（风格收尾）', '全部后缀：' + suffixAll], copy: s[0] })
  })
  SOUND_ROWS.forEach((r: [string, string, string], i: number) => {
    out.push({ id: 'sound-' + i, cat: '音韵速查', tag: '音韵', title: r[0], en: '', cover: 'S', summary: r[1], detail: ['气质指向：' + r[1], '例子：' + r[2], '尾音定气质、音色定软硬'], copy: r[0] + ' / ' + r[1] + ' / ' + r[2] })
  })
  KANJI.forEach((k: [string, string], i: number) => {
    out.push({ id: 'kanji-' + i, cat: '汉字音读', tag: '日语音读', title: k[0], en: k[1], cover: k[0], summary: '日语汉字音读对照', detail: ['音读：' + k[1]], copy: k[0] + ' → ' + k[1] })
  })
  TRANSFER_ROWS.forEach((r: [string, string, string], i: number) => {
    out.push({ id: 'trans-' + i, cat: '互转流程', tag: '互转', title: r[0], en: '', cover: r[0].slice(0, 1), summary: r[1], detail: ['用名：' + r[1], '理由：' + r[2]], copy: r[0] + '：' + r[1] })
  })
  STEPS.forEach((s: string, i: number) => {
    out.push({ id: 'step-' + i, cat: '互转流程', tag: '五步流程', title: s.length > 12 ? s.slice(0, 12) + '…' : s, en: '', cover: '流', summary: s, detail: [s], copy: s })
  })
  FINAL_CHECK.forEach((s: string, i: number) => {
    out.push({ id: 'final-' + i, cat: '互转流程', tag: '终检', title: s.length > 12 ? s.slice(0, 12) + '…' : s, en: '', cover: '检', summary: s, detail: [s], copy: s })
  })
  heurKeys.forEach((k: string) => {
    heurGroup(k).forEach((t: [string, string, string]) => {
      out.push({ id: 'heur-' + k + '-' + t[0], cat: '启发技巧', tag: k, title: t[0], en: '', cover: t[0].slice(0, 1), summary: t[1], detail: ['用法：' + t[1], '例：' + t[2]], copy: heurLine(t) })
    })
  })
  PITFALLS.forEach((p: string, i: number) => {
    out.push({ id: 'pit-' + i, cat: '避雷清单', tag: '避雷', title: p.length > 10 ? p.slice(0, 10) + '…' : p, en: '', cover: '避', summary: p, detail: [p], copy: p })
  })
  return out
})
const filtered = computed<CardItem[]>(() => {
  const q: string = query.value.trim().toLowerCase()
  return allItems.value.filter((it: CardItem) => {
    if (active.value !== '全部' && it.cat !== active.value) return false
    if (!q) return true
    const hay: string = (it.title + ' ' + it.en + ' ' + it.summary + ' ' + it.tag + ' ' + it.cat + ' ' + it.copy + ' ' + it.detail.join(' ')).toLowerCase()
    return hay.includes(q)
  })
})
function clearFilter(): void {
  query.value = ''
  active.value = '全部'
}
function isOpen(key: string): boolean {
  return openKey.value === key
}
function toggleDetail(key: string): void {
  openKey.value = openKey.value === key ? null : key
}
function copyItem(it: CardItem): void {
  void copyText(it.copy)
}
function addToCN(it: CardItem): void {
  const name: string = it.title
  if (!cnCands.value.some((c: Cand) => c.name === name)) {
    cnCands.value.push({ name, tag: it.cat, full: name })
  }
  ElMessage.success('已加入中文候选：' + name)
}
function addToEN(it: CardItem): void {
  const name: string = it.en ? it.en.split(' ')[0] as string : it.title
  const target: string = it.en && /[A-Za-z]/.test(it.title) ? it.title : name
  if (!enCands.value.some((c: Cand) => c.name === target)) {
    enCands.value.push({ name: target, tag: it.cat, full: target })
  }
  ElMessage.success('已加入英文候选：' + target)
}

/* ---- 生成器（与原页逻辑一致） ---- */
function pick<T>(arr: readonly T[]): T {
  return arr[Math.floor(Math.random() * arr.length)] as T
}
function genCN(): Cand {
  const onPools = poolNames.filter((n) => poolOn[n])
  const pool = onPools.length ? poolChars(pick(onPools)) : poolChars(pick(poolNames))
  const surname = pick(SURNAMES)
  const a = pick(pool)
  let name: string
  let kind: string
  if (Math.random() < 0.6) {
    const b = pick(pool)
    if (b === a) return genCN()
    const head = Math.random() < 0.3 ? pick(WILDCARDS) : a
    if (head === surname || b === surname || head === b) return genCN()
    name = surname + head + b
    kind = '双名'
  } else {
    if (a === surname) return genCN()
    name = surname + a
    kind = '单名'
  }
  return { name, tag: onPools.join('/') + '·' + kind, full: name }
}
function genEN(): Cand {
  if (Math.random() < 0.5) {
    const key = pick(enKeys)
    const p = pick(enGroup(key))
    return { name: p[0], tag: key + '·真名', full: p[0] }
  }
  const pre = pick(EN_PREFIX)
  const suf = pick(EN_SUFFIX)
  return { name: pre[0] + suf[0], tag: '造词', full: pre[0] + '(' + pre[1] + ')+' + suf[0] + '(' + suf[1] + ')' }
}
function rollDeck(gen: () => Cand, target: { value: Cand[] }): void {
  const seen: Record<string, boolean> = {}
  const out: Cand[] = []
  let guard = 0
  while (out.length < 4 && guard++ < 40) {
    const g = gen()
    if (seen[g.name]) continue
    seen[g.name] = true
    out.push(g)
  }
  target.value = out
}
function togglePool(n: string): void { poolOn[n] = !poolOn[n] }
function copyOne(t: string): void { void copyText(t) }
function rollCNDeck(): void { rollDeck(genCN, cnCands) }
function rollENDeck(): void { rollDeck(genEN, enCands) }
function rollTipDeck(): void {
  const p = pick(HEUR_FLAT)
  tipCands.value = [{ name: p.t[0], tag: p.g, full: heurLine(p.t) }]
  copyOne(heurLine(p.t))
}
function copyCNDeck(): void {
  if (!cnCands.value.length) { ElMessage.warning('先摇一批中文候选'); return }
  void copyText(cnCands.value.map((c) => c.name).join('、'))
}
function copyENDeck(): void {
  if (!enCands.value.length) { ElMessage.warning('先摇一批英文候选'); return }
  void copyText(enCands.value.map((c) => c.name).join(', '))
}
function clearDeck(): void {
  cnCands.value = []
  enCands.value = []
}

/* ---- 撞名自检（与原页逻辑一致） ---- */
function norm(s: string): string { return s.replace(/\s+/g, '').toLowerCase() }
function runCheck(): void {
  const raw = checkInput.value.trim()
  if (!raw) {
    checked.value = true
    checkLines.value = [{ kind: 'tip', head: '', body: '请输入候选名再点检测。' }]
    return
  }
  const cand = norm(raw)
  const hi: HotName[] = []
  const mid: Array<{ h: HotName; why: string }> = []
  HOT_NAMES.forEach((h) => {
    const hn = norm(h.n)
    if (cand === hn) hi.push(h)
    else if (hn.length >= 2 && cand.includes(hn)) mid.push({ h, why: '包含「' + h.n + '」' })
    else if (cand.length >= 2 && hn.includes(cand)) mid.push({ h, why: '是「' + h.n + '」的一部分' })
  })
  const lines: CheckLine[] = []
  hi.forEach((h) => lines.push({ kind: 'hi', head: '● 高风险：', body: '与「' + h.n + '」（' + h.tag + '·' + h.src + '）完全重名——建议换字或换组合。' }))
  mid.slice(0, 6).forEach((m) => lines.push({ kind: 'mid', head: '● 中风险：', body: m.why + '（' + m.h.tag + '·' + m.h.src + '）。' }))
  if (!hi.length && !mid.length) {
    lines.push({ kind: 'ok', head: '● 清单内未命中：', body: '内置雷区里没有「' + raw + '」，但清单不穷尽——请点上方外链做「名字＋角色/小说/演员」三搜确认。' })
  }
  lines.push({ kind: 'tip', head: '', body: '变体四招：同音换字（炎→砚）· 近形换字（萧→筱）· 换姓保名（颜炎）· 保留意象换组合（炎→燎原/烬）。' })
  checked.value = true
  checkLines.value = lines
}
</script>

<style scoped>
.naming-tool {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #fff;
  color: var(--suli-text);
}
.gen-card, .check-card { padding: 12px; }
.gen-card { display: flex; flex-direction: column; gap: 8px; }
.row-label { font-size: 12px; }
.chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip { cursor: pointer; user-select: none; }
.btns { display: flex; gap: 6px; flex-wrap: wrap; }
.out-row { display: flex; gap: 8px; align-items: flex-start; }
.out-label { font-size: 12px; white-space: nowrap; padding-top: 5px; min-width: 32px; }
.outs { display: flex; gap: 6px; flex-wrap: wrap; flex: 1; min-width: 0; }
.out-tag { cursor: pointer; }
.out-sub { font-size: 11px; opacity: 0.75; margin-left: 4px; }
.empty { font-size: 12px; padding-top: 4px; }
.ct-title { font-weight: 700; font-size: 14px; color: var(--suli-text); margin-right: 8px; }
.pool-block { margin-bottom: 10px; }
.subh { font-size: 13px; font-weight: 700; color: var(--suli-text); margin: 10px 0 6px; display: flex; align-items: center; gap: 8px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(88px, 1fr)); gap: 8px; }
.grid.wide { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
.mini-card {
  background: #fff;
  border: 1px solid var(--suli-border);
  border-radius: 12px;
  padding: 8px 10px;
  cursor: pointer;
  transition: border-color 0.12s, box-shadow 0.12s, transform 0.12s;
}
.mini-card:hover { border-color: var(--suli-primary); box-shadow: var(--suli-shadow-sm); transform: translateY(-1px); }
.mini-card .zh { font-size: 15px; font-weight: 700; letter-spacing: 0.04em; color: var(--suli-text); }
.mini-card.dim .zh { font-size: 14px; }
.mini-card .en { font-size: 12px; color: var(--suli-text-2); font-family: var(--suli-mono); margin-top: 2px; word-break: break-word; }
.mini-card .meta { font-size: 11px; color: var(--suli-text-2); margin-top: 2px; line-height: 1.5; }
.suli-table { width: 100%; border-collapse: collapse; font-size: 12.5px; background: #fff; border: 1px solid var(--suli-border); border-radius: 12px; overflow: hidden; }
.suli-table th, .suli-table td { padding: 7px 9px; text-align: left; border-bottom: 1px solid var(--suli-border); vertical-align: top; color: var(--suli-text); }
.suli-table tr:last-child td { border-bottom: none; }
.suli-table th { font-size: 12px; color: var(--suli-text-2); font-weight: 700; }
.mono { font-family: var(--suli-mono); }
ul.plain { list-style: none; margin: 0; padding: 10px 12px; font-size: 13px; line-height: 1.9; color: var(--suli-text); background: #fff; border: 1px solid var(--suli-border); border-radius: 12px; }
ul.plain li::before { content: "· "; color: var(--suli-text-2); }
.check-card { display: flex; flex-direction: column; gap: 8px; }
.check-card h3 { margin: 0; font-size: 15px; }
.check-bar { display: flex; gap: 8px; }
.check-bar .el-input { flex: 1; min-width: 0; }
.check-links { display: flex; gap: 12px; flex-wrap: wrap; }
.risk-hi { color: #b23; font-weight: 700; }
.risk-mid { color: #b76b1e; font-weight: 700; }
.risk-ok { color: #2e7d4f; font-weight: 700; }
.naming-tool {
  --suli-primary: #FB7299;
  --suli-border: #e4e4e7;
}
.tray { position: sticky; top: 0; z-index: 10; background: #fff; border-bottom: 1px solid var(--suli-border); padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; }
.tray-row { display: flex; gap: 8px; align-items: center; }
.tray-search { flex: 1; min-width: 0; }
.count { font-size: 12px; white-space: nowrap; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px; }
.tool-card { padding: 12px; cursor: pointer; transition: box-shadow 0.15s, transform 0.15s, border-color 0.15s; }
.tool-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(251, 114, 153, 0.18); border-color: var(--suli-primary); }
.cover { height: 84px; display: flex; align-items: center; justify-content: center; font-size: 40px; font-weight: 800; background: #fff1f5; border-radius: 10px; overflow: hidden; }
.title-row { display: flex; gap: 8px; align-items: baseline; margin-top: 8px; }
.title-row .zh { font-size: 15px; font-weight: 700; color: var(--suli-text); }
.title-row .en { font-size: 12px; color: var(--suli-text-2); font-family: var(--suli-mono); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }
.summary { margin-top: 6px; font-size: 12.5px; color: var(--suli-text-2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.empty-state { padding: 18px; text-align: center; font-size: 13px; }
.tool-card.open { grid-column: span 2; border-color: var(--suli-primary,#FB7299); }
.detail-block { margin-top:10px; border-top:1px dashed var(--suli-border); padding-top:10px; display: flex; flex-direction: column; gap: 8px; }
.detail-cols { display:grid; grid-template-columns:220px 1fr; gap:12px; }
@media (max-width: 640px) { .detail-cols { grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); } }
.detail-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.detail-body { display: flex; flex-direction: column; gap: 8px; }
.detail-cover { height: 96px; display: flex; align-items: center; justify-content: center; font-size: 48px; font-weight: 800; background: #fff1f5; border-radius: 10px; }
.detail-title .zh { font-size: 18px; font-weight: 800; margin-right: 8px; }
.detail-title .en { font-size: 13px; color: var(--suli-text-2); font-family: var(--suli-mono); }
.detail-summary { margin: 0; font-size: 13px; line-height: 1.7; }
pre.suli-pre { background: #fafafa; border: 1px solid var(--suli-border); border-radius: 10px; padding: 10px 12px; font-size: 12.5px; white-space: pre-wrap; word-break: break-word; margin: 0; }

@container (max-width: 620px) {
  .card-grid { grid-template-columns: repeat(2, 1fr); }
  .detail-cols { grid-template-columns: 1fr; }
}
@container (max-width: 400px) {
  .card-grid { grid-template-columns: 1fr; }
}
/* pack-slots: backpack face */
.tool-card > .tags, .tool-card > .summary { display: none; }
.tool-card > .title-row { overflow: hidden; }
.tool-card > .title-row > * { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tool-card.open { box-shadow: 0 0 0 2px rgba(251,114,153,.45), 0 8px 20px rgba(251,114,153,.25); }</style>
