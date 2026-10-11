<template>
  <div class="flowers-tool">
    <!-- 白色 sticky tray：搜索 + 气质 chips + 季节单选 + 计数 + 清空 + 组合复制 -->
    <div class="tray">
      <div class="tray-row">
        <el-input
          v-model="query"
          clearable
          placeholder="搜索：花名 / 花语关键词 / tag"
          class="search-input"
        />
        <span class="suli-muted count">共 {{ visibleFlowers.length }} / {{ FLOWERS.length }}</span>
        <el-button size="small" @click="clearFilters">清空筛选</el-button>
        <el-button type="primary" size="small" @click="copyTray">复制组合prompt</el-button>
        <el-button size="small" @click="clearTray">清空组合</el-button>
        <el-button size="small" text @click="toggleTray">{{ trayOpen ? '收起 ▲' : '展开 ▼' }}</el-button>
      </div>
      <template v-if="trayOpen">
      <div class="tray-row">
        <span class="tray-label">气质</span>
        <el-tag
          v-for="c in cats"
          :key="c"
          :effect="catOn[c] ? 'dark' : 'plain'"
          :type="catOn[c] ? 'primary' : 'info'"
          class="chip"
          @click="toggleCat(c)"
        >{{ c }}</el-tag>
      </div>
      <div class="tray-row">
        <span class="tray-label">季节</span>
        <el-tag
          v-for="s in seasons"
          :key="s"
          :effect="seasonOnly === s ? 'dark' : 'plain'"
          :type="seasonOnly === s ? 'primary' : 'info'"
          class="chip"
          @click="toggleSeason(s)"
        >{{ s }}</el-tag>
      </div>
      <div class="tray-row">
        <span class="tray-label">组合</span>
        <span v-if="tray.length === 0" class="suli-muted">暂无，点卡片详情「加组合」添加</span>
        <el-tag
          v-for="t in tray"
          :key="t.tag"
          closable
          class="chip"
          @click="copyTag(t.tag)"
          @close="removeFromTray(t.tag)"
        >{{ t.zh }}</el-tag>
      </div>
      <div class="suli-muted hint">点卡片看全字段详情 · 详情里点色块取色值 · 点 tag 与花语行复制</div>
      </template>
    </div>

    <div class="intro suli-muted">
      角色设计用花卉参考：<strong>花语（中/日系/西式）· booru tag（已逐条核对）· 学名 · 花色色值 · 季节 · 用法与避雷</strong>。
      顶部筛选气质/季节或搜索 → 点卡片进详情「加组合」攒花束 → 「复制组合prompt」得
      <code>cherry blossoms, wisteria, floating petals</code> 式组合句。花语跨文化有雷区，出图前先看底部「文化避雷」。
    </div>

    <!-- 统一过滤网格：单花一卡，整卡点击就地展开 -->
    <div class="grid">
      <div
        v-for="f in visibleFlowers"
        :key="f.tag"
        class="suli-card tool-card"
        :class="{ open: isOpen(f.tag) }"
        @click="toggleDetail(f.tag)"
      >
        <div class="cover">
          <img
            v-if="imgSrc(f) && imgOk[f.tag]"
            class="photo"
            loading="lazy"
            :src="imgSrc(f)"
            :alt="f.zh + ' 实物图'"
            @error="imgOk[f.tag] = false"
          />
          <div v-else class="cover-ph">{{ f.zh.charAt(0) }}</div>
          <span class="cat-chip">{{ f.cat }}</span>
        </div>
        <div class="hd">
          <span class="zh">{{ f.zh }}</span>
          <span class="suli-muted en">{{ f.en }}</span>
        </div>
        <div class="tag-row">
          <el-tag size="small" class="chip mono" @click.stop="copyTag(firstTag(f.tag))">{{ firstTag(f.tag) }}</el-tag>
          <span class="suli-muted season">{{ f.season }}</span>
        </div>
        <div class="suli-muted ellipsis" :title="f.mCN">{{ f.mCN }}</div>
        <div v-if="isOpen(f.tag)" class="detail-block" @click.stop>
          <div class="detail-cols">
            <div class="dlg-cover">
              <img
                v-if="imgSrc(f) && imgOk[f.tag]"
                :src="imgSrc(f)"
                :alt="f.zh"
                class="dlg-img"
                @error="imgOk[f.tag] = false"
              />
              <div v-else class="cover-ph big">{{ f.zh.charAt(0) }}</div>
            </div>
            <div class="detail-main">
              <div class="detail-title">
                <span class="zh">{{ f.zh }}</span>
                <span class="suli-muted en"> | {{ f.en }}</span>
              </div>
              <div class="dlg-meta">
                <span class="suli-muted mono">{{ f.latin }}</span>
                <el-tag size="small" class="chip">{{ f.cat }}</el-tag>
                <el-tag size="small" type="info" class="chip">{{ f.season }}</el-tag>
              </div>
              <div class="dlg-tagrow">
                <el-tag size="small" class="chip mono" @click.stop="copyTag(firstTag(f.tag))">{{ firstTag(f.tag) }}</el-tag>
                <el-button size="small" @click.stop="copyTag(firstTag(f.tag))">复制tag</el-button>
                <el-button size="small" type="primary" @click.stop="addToTray(f)">加组合</el-button>
              </div>
              <div class="mean">
                <div class="mean-row" @click.stop="copyText(f.mCN)"><b>中：</b>{{ f.mCN }}</div>
                <div class="mean-row" @click.stop="copyText(f.mJP)"><b>日：</b>{{ f.mJP }}</div>
                <div class="mean-row" @click.stop="copyText(f.mEN)"><b>西：</b>{{ f.mEN }}</div>
              </div>
              <div class="sw">
                <span
                  v-for="(col, i) in f.colors"
                  :key="i"
                  class="swdot"
                  :style="{ background: col[0] }"
                  :title="col[1] + ' ' + col[0]"
                  @click.stop="copyText(col[0])"
                />
                <span class="suli-muted swtxt">{{ f.colors.map((c) => c[1] + ' ' + c[0]).join(' / ') }}</span>
              </div>
            </div>
          </div>
          <pre class="suli-pre note-pre">{{ f.note }}</pre>
          <div class="dlg-bar">
            <el-button size="small" @click.stop="stepOpen(-1)">上一张</el-button>
            <el-button size="small" @click.stop="stepOpen(1)">下一张</el-button>
            <el-button size="small" @click.stop="copyImgPath(f)">复制图片路径</el-button>
            <a :href="commonsUrlFor(f)" target="_blank" rel="noopener" class="commons-link" @click.stop>Commons 搜大图</a>
            <el-button size="small" @click.stop="openKey=null">收起</el-button>
          </div>
          <div class="suli-muted dlg-cap">{{ f.latin }}（{{ visibleFlowers.findIndex((x) => x.tag === f.tag) + 1 }} / {{ visibleFlowers.length }}）</div>
        </div>
      </div>
    </div>

    <p v-if="visibleFlowers.length === 0" class="suli-muted empty">没有匹配的花，换个关键词或点「清空筛选」放宽条件。</p>

    <!-- 通用组合词 -->
    <section>
      <h3>Prompt 组合通用词 <span class="suli-muted">Generic Flower Tags</span></h3>
      <p class="suli-muted tip">与单花 tag 搭配的场景词；点击 tag 复制。带 (*) 的为常用但建议出图前 autocomplete 复查。</p>
      <table class="gentable">
        <tr><th>用途</th><th>tag 组合</th><th>说明</th></tr>
        <tr v-for="(g, i) in genericTags" :key="i">
          <td>{{ g.use }}</td>
          <td class="mono tagcell" @click="copyText(g.tags)">{{ g.tags }}</td>
          <td>{{ g.desc }}</td>
        </tr>
      </table>
    </section>

    <!-- 用法 -->
    <section>
      <h3>角色设计用法 <span class="suli-muted">Design Workflow</span></h3>
      <ul class="plain suli-card">
        <li><b>母题层</b>：把花当「第四锚点」——大锚引花形（发剪影/花冠轮廓）、中锚引花色（服装主色）、小锚用实物花（发夹/胸针）落地。</li>
        <li><b>花语叙事</b>：角色名/命运与花语互文；进阶玩法＝<b>花语反差</b>（外表彼岸花、内里铃兰），一本正经的反差即记忆点。</li>
        <li><b>配色</b>：取 2 个花色当主/辅色（点色块复制），点缀色回配色工具找同色系深/浅两档，凑三层。</li>
        <li><b>场景</b>：季节＝花种铁律（春樱/夏绣球/秋彼岸/冬山茶），花与天气配对（绣球＋雨、紫藤＋黄昏、向日葵＋正午）。</li>
        <li><b>角色卡/表情包</b>：用单花 tag 当装饰飞散元素，比堆小物干净。</li>
        <li><b>避雷</b>：见下节——花语跨文化同花不同义，出图/署名/文案前先对照。</li>
      </ul>
    </section>

    <!-- 避雷 -->
    <section>
      <h3>文化避雷 <span class="suli-muted">Cultural Notes</span></h3>
      <ul class="plain suli-card">
        <li><b>菊花</b>：中式＝高洁长寿；日本黄菊＝皇室（慎用）；欧美部分地区＝悼念（别用在喜庆场景）。</li>
        <li><b>白花系</b>（白百合/白山茶/白菊）：婚礼与葬礼双用，看场景颜色与场合；纯洁/悼念两读。</li>
        <li><b>彼岸花（spider_lily）</b>：日系＝冥界/离别/再会，默认丧感——想玩“艳丽死亡美学”正合适，告白场景请绕开。</li>
        <li><b>虞美人（红罂粟）</b>：英联邦＝阵亡纪念，红色别乱配欢快场景。</li>
        <li><b>水仙（daffodil/narcissus）</b>：西式“自恋”；中式春节吉祥年花——署名场景注意语境。</li>
        <li><b>紫阳花（绣球）</b>：花语含“变心/移り気”，告白向慎用；雨景/家族团圆向安全。</li>
        <li><b>山茶</b>：日系落花（ぽとり）有“斩首/死亡”联想，古风战斗场景除外慎用。</li>
        <li><b>玫瑰色系</b>：黄玫瑰＝友情/嫉妒（日系），告白别送黄。</li>
      </ul>
    </section>

    <p class="suli-muted foot">花语素材库 · 数据来源：通用花语/花言葉/floriography 常识整理 + Danbooru tag 逐条核对 · 实物图：Wikimedia Commons（CC/公有领域，仅供本地参考）· 配色联动配色工具 · 命名联动取名工具。</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { copyText } from '../../utils/clipboard'

interface Flower {
  zh: string
  en: string
  tag: string
  latin: string
  season: string
  cat: string
  mCN: string
  mJP: string
  mEN: string
  colors: [string, string][]
  note: string
}

interface TrayItem { zh: string; tag: string }
interface GenericTag { use: string; tags: string; desc: string }

/* 实物图映射：键＝tag 归一化名（与源页 FLOWER_IMGS 一致），路径改为绝对路径 */
const FLOWER_IMGS: Record<string, string> = {
  'cherry_blossoms': '/tools/flowers/cherry_blossoms.jpg',
  'plum_blossoms': '/tools/flowers/plum_blossoms.jpg',
  'peach_blossoms': '/tools/flowers/peach_blossoms.jpg',
  'camellia': '/tools/flowers/camellia.jpg',
  'wisteria': '/tools/flowers/wisteria.jpg',
  'lily_of_the_valley': '/tools/flowers/lily_of_the_valley.jpg',
  'dandelion': '/tools/flowers/dandelion.jpg',
  'tulip': '/tools/flowers/tulip.jpg',
  'violet_(flower)': '/tools/flowers/violet__flower_.jpg',
  'pansy': '/tools/flowers/pansy.jpg',
  'daisy_(flower)': '/tools/flowers/daisy__flower_.jpg',
  'hyacinth': '/tools/flowers/hyacinth.jpg',
  'primrose_(flower)': '/tools/flowers/primrose__flower_.jpg',
  'snowdrop_(flower)': '/tools/flowers/snowdrop__flower_.jpg',
  'iris_(flower)': '/tools/flowers/iris__flower_.jpg',
  'bluebell_(flower)': '/tools/flowers/bluebell__flower_.jpg',
  'larkspur_(flower)': '/tools/flowers/larkspur__flower_.jpg',
  'cornflower': '/tools/flowers/cornflower.jpg',
  'gardenia_(flower)': '/tools/flowers/gardenia__flower_.jpg',
  'jasmine_(flower)': '/tools/flowers/jasmine__flower_.jpg',
  'hydrangea': '/tools/flowers/hydrangea.jpg',
  'lotus': '/tools/flowers/lotus.jpg',
  'water_lily_flower': '/tools/flowers/water_lily_flower.jpg',
  'sunflower': '/tools/flowers/sunflower.jpg',
  'lavender_(flower)': '/tools/flowers/lavender__flower_.jpg',
  'chinese_bellflower': '/tools/flowers/chinese_bellflower.jpg',
  'cosmos_(flower)': '/tools/flowers/cosmos__flower_.jpg',
  'spider_lily': '/tools/flowers/spider_lily.jpg',
  'gentiana_(flower)': '/tools/flowers/gentiana__flower_.jpg',
  'chrysanthemum': '/tools/flowers/chrysanthemum.jpg',
  'osmanthus': '/tools/flowers/osmanthus.jpg',
  'hibiscus': '/tools/flowers/hibiscus.jpg',
  'dahlia': '/tools/flowers/dahlia.jpg',
  'carnation': '/tools/flowers/carnation.jpg',
  'rose': '/tools/flowers/rose.jpg',
  'lily_(flower)': '/tools/flowers/lily__flower_.jpg',
  'calla_lily': '/tools/flowers/calla_lily.jpg',
  'forget-me-not_(flower)': '/tools/flowers/forget-me-not__flower_.jpg',
  "baby's-breath": '/tools/flowers/baby_s-breath.jpg',
  'anemone_(flower)': '/tools/flowers/anemone__flower_.jpg',
  'poppy_(flower)': '/tools/flowers/poppy__flower_.jpg',
  'morning_glory': '/tools/flowers/morning_glory.jpg',
  'daffodil': '/tools/flowers/daffodil.jpg',
  'marigold': '/tools/flowers/marigold.jpg',
  'lilac': '/tools/flowers/lilac.jpg',
  'magnolia': '/tools/flowers/magnolia.jpg',
  'pear_blossoms': '/tools/flowers/pear_blossoms.jpg',
  'apple_blossoms': '/tools/flowers/apple_blossoms.jpg',
  'rapeseed_blossoms': '/tools/flowers/rapeseed_blossoms.jpg',
  'geranium': '/tools/flowers/geranium.jpg',
  'begonia_(flower)': '/tools/flowers/begonia__flower_.jpg',
  'anthurium': '/tools/flowers/anthurium.jpg',
  'phalaenopsis': '/tools/flowers/phalaenopsis.jpg',
  'plumeria': '/tools/flowers/plumeria.jpg',
  'snapdragon': '/tools/flowers/snapdragon.jpg',
  'sweet_pea': '/tools/flowers/sweet_pea.jpg',
  'freesia_(flower)': '/tools/flowers/freesia__flower_.jpg',
  'nemophila_(flower)': '/tools/flowers/nemophila__flower_.jpg',
  'forsythia': '/tools/flowers/forsythia.jpg',
  'dianthus': '/tools/flowers/dianthus.jpg',
  'mimosa_(flower)': '/tools/flowers/mimosa__flower_.jpg',
  'edelweiss_(flower)': '/tools/flowers/edelweiss__flower_.jpg',
  'jacaranda': '/tools/flowers/jacaranda.jpg',
  'protea_(flower)': '/tools/flowers/protea__flower_.jpg',
  "angel's_trumpet_(flower)": '/tools/flowers/angel_s_trumpet__flower_.jpg',
  'epiphyllum': '/tools/flowers/epiphyllum.jpg',
  'hepatica_(flower)': '/tools/flowers/hepatica__flower_.jpg',
  'hellebore': '/tools/flowers/hellebore.jpg',
  'columbine_(flower)': '/tools/flowers/columbine__flower_.jpg',
  'blue_lotus': '/tools/flowers/blue_lotus.jpg',
  'oleander': '/tools/flowers/oleander.jpg',
  'bird_of_paradise_flower': '/tools/flowers/bird_of_paradise_flower.jpg',
  'gloriosa_(flower)': '/tools/flowers/gloriosa__flower_.jpg',
  'bougainvillea_(flower)': '/tools/flowers/bougainvillea__flower_.jpg',
  'rhododendron': '/tools/flowers/rhododendron.jpg',
  'tweedia': '/tools/flowers/tweedia.jpg',
  'jade_vine': '/tools/flowers/jade_vine.jpg',
  'titan_arum': '/tools/flowers/titan_arum.jpg',
  'peony_(flower)': '/tools/flowers/peony__flower_.jpg',
  'pomegranate_flower': '/tools/flowers/pomegranate_flower.jpg',
  'crape_myrtle': '/tools/flowers/crape_myrtle.jpg',
  'honeysuckle': '/tools/flowers/honeysuckle.jpg',
  'clematis_(flower)': '/tools/flowers/clematis__flower_.jpg',
  'winter_jasmine': '/tools/flowers/winter_jasmine.jpg',
  'hosta': '/tools/flowers/hosta.jpg',
  'plumbago_(flower)': '/tools/flowers/plumbago__flower_.jpg',
  'ranunculus': '/tools/flowers/ranunculus.jpg',
  'alstroemeria_(flower)': '/tools/flowers/alstroemeria__flower_.jpg',
  'allium_(flower)': '/tools/flowers/allium__flower_.jpg',
  'rafflesia_(flower)': '/tools/flowers/rafflesia__flower_.jpg',
  'venus_flytrap': '/tools/flowers/venus_flytrap.jpg',
  'cotton_(plant)': '/tools/flowers/cotton__plant_.jpg',
  'chinese_trumpet_vine': '/tools/flowers/chinese_trumpet_vine.jpg',
  'crocus_(flower)': '/tools/flowers/crocus__flower_.jpg',
  "four_o'clock_(flower)": '/tools/flowers/four_o_clock__flower_.jpg',
  'california_poppy': '/tools/flowers/california_poppy.jpg',
  'hollyhock': '/tools/flowers/hollyhock.jpg',
  'dendrobium': '/tools/flowers/dendrobium.jpg',
  'bleeding_heart_(flower)': '/tools/flowers/bleeding_heart__flower_.jpg',
  'black_spider_lily': '/tools/flowers/black_spider_lily.jpg',
  'bellflower': '/tools/flowers/bellflower.jpg'
}

/* 数据：源页 FLOWERS 全量 101 条（中/英/tag/学名/季节/气质/中花语/日花语/西花语/色值/备注） */
const FLOWERS: Flower[] = [
  { zh: '樱花', en: 'cherry blossom', tag: 'cherry_blossoms', latin: 'Prunus serrulata', season: '春', cat: '清冷·高洁', mCN: '生命的短暂与纯粹之美', mJP: '精神美・優美な女性', mEN: 'Transience・gentle beauty', colors: [['#FFB7C5', '樱粉'], ['#FEDFE1', '淡樱'], ['#FFF5F7', '白樱']], note: '飘落＝时间流逝；花雨/毕业/春日场景常客。别名 sakura' },
  { zh: '梅花', en: 'plum blossom', tag: 'plum_blossoms', latin: 'Prunus mume', season: '冬→春', cat: '清冷·高洁', mCN: '坚强高雅・五福', mJP: '高潔・忠実', mEN: 'Hope・resilience', colors: [['#F7C8D8', '粉梅'], ['#C41E3A', '红梅'], ['#FFFDF5', '白梅']], note: '岁寒三友；中式古风场景首选，配雪' },
  { zh: '桃花', en: 'peach blossom', tag: 'peach_blossoms（未核对，用前 autocomplete）', latin: 'Prunus persica', season: '春', cat: '纯爱·恋慕', mCN: '爱情的俘虏・桃李满天下', mJP: 'チャーミング・あなたに夢中', mEN: 'Sweet love・captivation', colors: [['#FFC0CB', '桃粉'], ['#FF9EAF', '桃红']], note: '桃花运/春日少女感；中式婚礼意象' },
  { zh: '山茶花', en: 'camellia', tag: 'camellia · white_camellia', latin: 'Camellia japonica', season: '冬→春', cat: '高贵·典雅', mCN: '理想的爱・谦让・可爱', mJP: '控えめな素晴らしさ・純白の理想の愛', mEN: 'Admiration・perfection', colors: [['#C41E3A', '山茶红'], ['#FFB7C5', '粉山茶'], ['#FFFFFF', '白山茶']], note: '有 camellia_print。日系落花＝『斩首/死亡』联想，战斗场景除外慎用' },
  { zh: '紫藤', en: 'wisteria', tag: 'wisteria', latin: 'Wisteria floribunda', season: '春', cat: '高贵·典雅', mCN: '沉醉的爱・为情执着', mJP: '優しさ・歓迎', mEN: 'Steadfastness', colors: [['#9A7BD1', '藤紫'], ['#C3B1E1', '淡藤']], note: '花瀑/藤棚场景；日系古风、黄昏光最佳。有 wisteria_print' },
  { zh: '铃兰', en: 'lily of the valley', tag: 'lily_of_the_valley', latin: 'Convallaria majalis', season: '春', cat: '纯爱·恋慕', mCN: '幸福归来・纯洁', mJP: '幸福が訪れる', mEN: 'Return of happiness', colors: [['#FFFFFF', '铃兰白'], ['#EAF6E9', '叶缘绿']], note: '婚纱/香水经典；有 lily_of_the_valley_print' },
  { zh: '蒲公英', en: 'dandelion', tag: 'dandelion · dandelion_seed · dandelion_clock', latin: 'Taraxacum', season: '春', cat: '元气·希望', mCN: '无法停留的爱・自由', mJP: '真心の愛・幸福', mEN: 'Hope・healing', colors: [['#FFD700', '蒲公英黄'], ['#FFFACD', '绒毛黄']], note: '吹散种子的 dandelion_clock 是名场面素材' },
  { zh: '郁金香', en: 'tulip', tag: 'tulip（色变体：red/pink/white/yellow/purple/black_tulip）', latin: 'Tulipa', season: '春', cat: '纯爱·恋慕', mCN: '爱的告白（红）・无望的爱（黄）・失恋（白）', mJP: '博愛・思いやり', mEN: 'Perfect love', colors: [['#FF3B30', '红'], ['#FFD700', '黄'], ['#FFFFFF', '白'], ['#A45EE5', '紫']], note: '荷兰/花海场景；花语看颜色再定' },
  { zh: '紫罗兰', en: 'violet', tag: 'violet_(flower)', latin: 'Viola', season: '春', cat: '清冷·高洁', mCN: '永恒的美・谦逊忠诚', mJP: '誠実・小さな幸せ', mEN: 'Modesty・faithfulness', colors: [['#7F00FF', '紫罗兰'], ['#C8A2C8', '淡紫']], note: '维多利亚花语代表花；书卷/古典气质' },
  { zh: '三色堇', en: 'pansy', tag: 'pansy（色变体：purple/yellow/pink/blue/pansy）', latin: 'Viola tricolor', season: '春', cat: '温柔·守护', mCN: '思念・请想念我', mJP: 'もの思い・私を思って', mEN: 'Thoughts of you', colors: [['#6A0DAD', '紫'], ['#FFD700', '黄'], ['#FFC0CB', '粉']], note: '脸谱感花瓣；配 wistful 表情' },
  { zh: '雏菊', en: 'daisy', tag: 'daisy_(flower)', latin: 'Bellis perennis', season: '春', cat: '元气·希望', mCN: '天真・和平・隐瞒的爱', mJP: '純潔・無邪気', mEN: 'Innocence', colors: [['#FFFFFF', '花瓣白'], ['#FFE4B5', '花心黄']], note: '「他爱我他不爱我」摘瓣梗；野花田' },
  { zh: '风信子', en: 'hyacinth', tag: 'hyacinth', latin: 'Hyacinthus', season: '春', cat: '元气·希望', mCN: '重生・胜利・竞技', mJP: 'スポーツ・ゲーム', mEN: 'Constancy・playfulness', colors: [['#6A5ACD', '蓝紫'], ['#FFC0CB', '粉'], ['#FFFFFF', '白']], note: '希腊神话少年之名；葡萄风信子=grape_hyacinth' },
  { zh: '报春花', en: 'primrose', tag: 'primrose_(flower)', latin: 'Primula', season: '春', cat: '元气·希望', mCN: '青春・初恋・希望（也含幻灭）', mJP: '青春の始まりと終わり', mEN: 'Young love', colors: [['#FFD700', '报春黄'], ['#FFB6C1', '粉']], note: '双义花语：青春的开始与结束——适合成长向角色' },
  { zh: '雪滴花', en: 'snowdrop', tag: 'snowdrop_(flower)', latin: 'Galanthus', season: '冬→春', cat: '清冷·高洁', mCN: '希望・逆境坚韧', mJP: '希望・慰め', mEN: 'Consolation・hope', colors: [['#FFFFFF', '雪白'], ['#E0F7FA', '冰蓝']], note: '雪中开花＝绝境希望；西方也有墓地花联想' },
  { zh: '鸢尾', en: 'iris', tag: 'iris_(flower)', latin: 'Iris', season: '春', cat: '高贵·典雅', mCN: '好消息・信任・勇气', mJP: '希望・メッセージ', mEN: 'Faith・wisdom', colors: [['#5D3FD3', '鸢尾紫'], ['#8A2BE2', '蓝紫']], note: '法国国花 fleur-de-lis；骑士/贵族气质' },
  { zh: '蓝铃花', en: 'bluebell', tag: 'bluebell_(flower)', latin: 'Hyacinthoides', season: '春末', cat: '温柔·守护', mCN: '恒久的爱・感恩', mJP: '訪問・感謝', mEN: 'Humility・constancy', colors: [['#5B7BD5', '蓝铃蓝']], note: '英伦林地花；童话/森林场景' },
  { zh: '飞燕草', en: 'larkspur', tag: 'larkspur_(flower)', latin: 'Delphinium', season: '夏', cat: '清冷·高洁', mCN: '轻盈・自由・清明', mJP: '清明・自由', mEN: 'Levity・fickleness', colors: [['#4169E1', '飞燕蓝'], ['#B19CD9', '淡紫']], note: '注意：delphinium 无独立 tag，统一用 larkspur_(flower)' },
  { zh: '矢车菊', en: 'cornflower', tag: 'cornflower', latin: 'Centaurea cyanus', season: '夏', cat: '元气·希望', mCN: '遇见幸福・温柔', mJP: '優雅・繊細', mEN: 'Hope in adversity', colors: [['#6495ED', '矢车蓝']], note: '普鲁士蓝之花的德系意象；麦田场景' },
  { zh: '栀子', en: 'gardenia', tag: 'gardenia_(flower)', latin: 'Gardenia jasminoides', season: '初夏', cat: '纯爱·恋慕', mCN: '永恒的爱・一生守候・喜悦', mJP: 'とても幸せです・喜び', mEN: 'Secret love・purity', colors: [['#FFFFF0', '栀白'], ['#F5F5DC', '米白']], note: '南方夏天/校园场景；香气意象强' },
  { zh: '茉莉', en: 'jasmine', tag: 'jasmine_(flower)', latin: 'Jasminum', season: '夏', cat: '温柔·守护', mCN: '忠贞・质朴・你是我的', mJP: '愛想の良さ・優雅', mEN: 'Amiability', colors: [['#FFFFFF', '茉莉白']], note: '中式庭院/簪花；花茶意象' },
  { zh: '绣球（紫阳花）', en: 'hydrangea', tag: 'hydrangea', latin: 'Hydrangea macrophylla', season: '初夏·梅雨', cat: '神秘·危险', mCN: '团圆・希望（也含『变心』）', mJP: '移り気・家族団欒', mEN: 'Gratitude・heartfelt', colors: [['#7788DD', '绣球蓝'], ['#C9A0DC', '绣球紫'], ['#FFC0CB', '绣球粉']], note: '雨天场景标配；有 hydrangea_hair_ornament。告白向慎用『变心』义' },
  { zh: '荷花', en: 'lotus', tag: 'lotus · white_lotus · lotus_hair_ornament', latin: 'Nelumbo nucifera', season: '夏', cat: '高贵·典雅', mCN: '出淤泥不染・圣洁', mJP: '清らかな心・離れゆく愛', mEN: 'Purity・enlightenment', colors: [['#FFB7C5', '荷粉'], ['#FFFFFF', '荷白']], note: '中式/佛系意象；有 lotus_hair_ornament 类实物 tag' },
  { zh: '睡莲', en: 'water lily', tag: 'water_lily_flower', latin: 'Nymphaea', season: '夏', cat: '清冷·高洁', mCN: '洁净・纯真・洁身自好', mJP: '清純な心・信頼', mEN: 'Purity of heart', colors: [['#FFF0F5', '睡莲白'], ['#E6E6FA', '淡紫']], note: '区分：lily_pad＝荷叶；水面倒影名场面' },
  { zh: '向日葵', en: 'sunflower', tag: 'sunflower · sunflower_field · sunflower_hair_ornament', latin: 'Helianthus', season: '夏', cat: '元气·希望', mCN: '忠诚・爱慕・我的眼中只有你', mJP: 'あなただけを見つめる', mEN: 'Adoration', colors: [['#FFC300', '葵黄'], ['#FF8C00', '深葵']], note: '正午光/花田；发饰 tag 现成' },
  { zh: '薰衣草', en: 'lavender', tag: 'lavender_(flower)', latin: 'Lavandula', season: '夏', cat: '温柔·守护', mCN: '等待爱情・期待', mJP: '期待・沈黙', mEN: 'Devotion・serenity', colors: [['#967BB6', '薰衣紫'], ['#B49FCC', '淡薰衣']], note: '普罗旺斯花田；紫系配色来源' },
  { zh: '桔梗', en: 'chinese bellflower', tag: 'chinese_bellflower', latin: 'Platycodon grandiflorus', season: '夏秋', cat: '清冷·高洁', mCN: '永恒的爱・不变的心', mJP: '変わらぬ愛・誠実', mEN: 'Endless love', colors: [['#6A5ACD', '桔梗紫']], note: '注意：bellflower＝风铃草属通用 tag；桔梗用 chinese_bellflower' },
  { zh: '波斯菊（秋英）', en: 'cosmos', tag: 'cosmos_(flower)', latin: 'Cosmos bipinnatus', season: '秋', cat: '元气·希望', mCN: '少女的真心・和谐清净', mJP: '乙女の真心', mEN: 'Order・harmony', colors: [['#FFB6C1', '粉'], ['#F5F5DC', '米白'], ['#C71585', '深粉']], note: '秋日摇曳感；随风情侣场景' },
  { zh: '彼岸花', en: 'red spider lily', tag: 'spider_lily', latin: 'Lycoris radiata', season: '秋', cat: '神秘·危险', mCN: '生死离别・冥界・回忆', mJP: '情熱・独立・再会・悲しみ', mEN: '—', colors: [['#FF2400', '彼岸红']], note: '默认丧感：离别/冥界/再会主题；有 spider_lily_print。别名 red_spider_lily；变体 black_spider_lily（黑色彼岸花）' },
  { zh: '龙胆', en: 'gentian', tag: 'gentiana_(flower)', latin: 'Gentiana', season: '秋', cat: '清冷·高洁', mCN: '正义・坚贞・忧郁', mJP: '正義・寂しさ', mEN: 'Sweetness', colors: [['#0F52BA', '龙胆蓝']], note: '深蓝系蓝紫配色；高山清冷气质' },
  { zh: '菊花', en: 'chrysanthemum', tag: 'chrysanthemum · chrysanthemum_print', latin: 'Chrysanthemum morifolium', season: '秋', cat: '高贵·典雅', mCN: '高洁・长寿・隐逸', mJP: '高貴・高尚', mEN: '—', colors: [['#FFD700', '菊黄'], ['#F5F5DC', '菊白'], ['#8B0000', '菊红']], note: '跨文化重雷区：日黄菊＝皇室；欧美部分＝悼念。见底部避雷' },
  { zh: '桂花', en: 'osmanthus', tag: 'osmanthus · gold_osmanthus', latin: 'Osmanthus fragrans', season: '秋', cat: '温柔·守护', mCN: '收获・高贵・甜蜜回忆', mJP: '謙虚・真実', mEN: '—', colors: [['#FFD700', '金桂'], ['#F0E68C', '淡金']], note: '中秋/香气场景；中式庭院标配' },
  { zh: '木槿（扶桑）', en: 'hibiscus', tag: 'hibiscus', latin: 'Hibiscus syriacus', season: '夏', cat: '元气·希望', mCN: '纤细之美・温柔的坚持', mJP: '繊細な美・新しい恋', mEN: 'Delicate beauty', colors: [['#FF69B4', '槿粉'], ['#FF6347', '槿红']], note: '夏日/南国场景；有 hibiscus_print' },
  { zh: '大丽花', en: 'dahlia', tag: 'dahlia', latin: 'Dahlia pinnata', season: '夏秋', cat: '高贵·典雅', mCN: '华丽・大吉大利（也有『见异思迁』负面版）', mJP: '華麗・優雅', mEN: 'Dignity・elegance', colors: [['#FF6F61', '珊瑚'], ['#8B008B', '深紫红']], note: '花型层叠＝华丽礼服意象；注意负面义版本' },
  { zh: '康乃馨', en: 'carnation', tag: 'carnation · red_carnation · pink_carnation · white_carnation', latin: 'Dianthus caryophyllus', season: '四季', cat: '温柔·守护', mCN: '母爱（红）・感恩（粉）・纯洁（白）', mJP: '母の愛・感謝', mEN: 'Admiration・gratitude', colors: [['#FF69B4', '康乃馨粉'], ['#FF0000', '红'], ['#FFFFFF', '白']], note: '母亲节/感谢场景；色变体 tag 现成' },
  { zh: '玫瑰', en: 'rose', tag: 'rose（色变体：blue_rose 等，用前 autocomplete 核对）', latin: 'Rosa', season: '四季', cat: '纯爱·恋慕', mCN: '爱（红）・我足以与你相配（白）・初恋（粉）・友情/嫉妒（黄）・奇迹（蓝）・温柔真心（黑）', mJP: '愛・美', mEN: 'Love', colors: [['#E4002B', '红'], ['#FFFFFF', '白'], ['#FFC0CB', '粉'], ['#FFD700', '黄'], ['#4169E1', '蓝']], note: '黄玫瑰告白慎用（日系＝嫉妒）；黑玫瑰有 black_rose tag' },
  { zh: '百合', en: 'lily', tag: 'lily_(flower) · white_lily', latin: 'Lilium', season: '夏', cat: '高贵·典雅', mCN: '纯洁・百年好合・高雅', mJP: '純潔・威厳', mEN: 'Purity', colors: [['#FFFFFF', '白百合'], ['#FFB7C5', '香水百合']], note: '白百合婚礼/宗教双语境；百合叠义（yuri）注意场合' },
  { zh: '马蹄莲', en: 'calla lily', tag: 'calla_lily', latin: 'Zantedeschia', season: '四季', cat: '高贵·典雅', mCN: '优雅高贵・纯洁无瑕', mJP: '華麗・素敵な美しさ', mEN: 'Magnificent beauty', colors: [['#FFFFFF', '马蹄白'], ['#FFB6C1', '粉']], note: '极简线条花型＝高级感；婚纱/静物' },
  { zh: '勿忘我', en: 'forget-me-not', tag: 'forget-me-not_(flower)', latin: 'Myosotis', season: '春', cat: '悲伤·离别', mCN: '永恒的记忆・不要忘记我', mJP: '私を忘れないで', mEN: 'True love・memories', colors: [['#6CB4EE', '勿忘蓝']], note: '离别/纪念场景；小蓝花簇适合远景点缀' },
  { zh: '满天星', en: "baby's breath", tag: "baby's-breath", latin: 'Gypsophila', season: '四季', cat: '温柔·守护', mCN: '纯洁的心・思念・配角之爱', mJP: '清らかな心・無邪気', mEN: 'Everlasting love', colors: [['#FFFFFF', '星白'], ['#FFE4E1', '淡粉']], note: '花束填充/星点背景；注意 tag 是连字符 baby\'s-breath' },
  { zh: '银莲花', en: 'anemone', tag: 'anemone_(flower)', latin: 'Anemone coronaria', season: '春', cat: '悲伤·离别', mCN: '虚幻的期望・被风吹拂的爱', mJP: 'はかない恋・見捨てられた恋', mEN: 'Forsaken', colors: [['#FF2E63', '银莲红'], ['#E6E6FA', '淡紫']], note: '『风之花』＝易逝的爱；悲剧向角色合适' },
  { zh: '虞美人', en: 'poppy', tag: 'poppy_(flower)', latin: 'Papaver rhoeas', season: '春', cat: '悲伤·离别', mCN: '遗忘・安慰・睡眠', mJP: '慰め・忘却', mEN: 'Remembrance', colors: [['#FF4500', '虞美人红']], note: '英联邦阵亡纪念（红）；别配欢快场景。希腊神话睡神之花' },
  { zh: '牵牛花', en: 'morning glory', tag: 'morning_glory', latin: 'Ipomoea', season: '夏', cat: '元气·希望', mCN: '爱情・短暂的美・牵绊', mJP: 'はかない恋・固い絆', mEN: 'Affection', colors: [['#8A2BE2', '紫'], ['#FF69B4', '粉']], note: '朝开午谢＝『一日花』，短暂主题专用' },
  { zh: '水仙', en: 'daffodil (narcissus)', tag: 'daffodil', latin: 'Narcissus', season: '冬→春', cat: '清冷·高洁', mCN: '纯洁・吉祥（中式年花）・自尊', mJP: 'うぬぼれ・神秘', mEN: 'Self-love・new beginnings', colors: [['#FFD700', '水仙黄'], ['#FFFFFF', '白瓣']], note: '西式＝自恋（narcissus 神话）；中式春节吉祥——看语境' },
  { zh: '金盏花', en: 'marigold', tag: 'marigold', latin: 'Calendula', season: '夏秋', cat: '悲伤·离别', mCN: '离别・失望（墨西哥亡灵节＝纪念）', mJP: '別れの悲しみ・失望', mEN: 'Grief・despair', colors: [['#FFA500', '金盏橙']], note: '双语境：日系丧感／墨西哥纪念；亡灵节同款是万寿菊' },
  { zh: '丁香', en: 'lilac', tag: 'lilac（tag 待核对）', latin: 'Syringa', season: '春', cat: '温柔·守护', mCN: '初恋・纯洁・忧愁', mJP: '思い出', mEN: 'First love', colors: [['#C8A2C8', '丁香紫'], ['#E6D7F5', '淡丁']], note: '紫丁香＝初恋回忆；雨中丁香意象' },
  { zh: '玉兰', en: 'magnolia', tag: 'magnolia', latin: 'Magnolia denudata', season: '春', cat: '高贵·典雅', mCN: '高洁・报恩・纯洁友谊', mJP: '崇高・恩返し', mEN: 'Dignity・nobility', colors: [['#FFFFFF', '玉兰白'], ['#F7E7F5', '淡紫玉兰']], note: '早春先花后叶；中式庭院/校园场景' },
  { zh: '梨花', en: 'pear blossom', tag: 'pear_blossoms', latin: 'Pyrus', season: '春', cat: '清冷·高洁', mCN: '纯情・离别・『梨花带雨』', mJP: '純情・慰め', mEN: 'Affection・comfort', colors: [['#FFFFFF', '梨白'], ['#F0FFF0', '新绿']], note: '梨花带雨＝哭泣的美人；含离别义，送别场景好用' },
  { zh: '苹果花', en: 'apple blossom', tag: 'apple_blossoms', latin: 'Malus domestica', season: '春', cat: '温柔·守护', mCN: '优先・好事将近・选择', mJP: '選択・優先', mEN: 'Promise・better things coming', colors: [['#FFD1DC', '苹果粉'], ['#FFF5EE', '乳白']], note: '欧美『好事将至』；果园/婚礼场景' },
  { zh: '油菜花', en: 'rapeseed blossom', tag: 'rapeseed_blossoms', latin: 'Brassica napus', season: '春', cat: '元气·希望', mCN: '加油・质朴的快乐・春天', mJP: '快活・明るい', mEN: 'Cheerfulness', colors: [['#FFD700', '菜花黄'], ['#FFFACD', '浅黄']], note: '日系『菜の花』春景标配；黄油色花海' },
  { zh: '天竺葵', en: 'geranium', tag: 'geranium', latin: 'Pelargonium', season: '夏', cat: '温柔·守护', mCN: '安慰・真挚友谊・决心', mJP: '決心・真実の愛', mEN: 'Comfort・determination', colors: [['#FF6F91', '玫红'], ['#FF4D6D', '深玫红']], note: '窗台花/阳台场景；花色从白到红跨全谱' },
  { zh: '秋海棠', en: 'begonia', tag: 'begonia_(flower)', latin: 'Begonia', season: '夏秋', cat: '温柔·守护', mCN: '苦恋・呵护・亲切', mJP: '恋の悩み・親切', mEN: 'Beware（警惕）', colors: [['#FFB3C6', '海棠粉'], ['#FFC9DE', '淡粉']], note: '花语偏苦恋/单恋——暗恋向角色合适' },
  { zh: '红掌', en: 'anthurium', tag: 'anthurium', latin: 'Anthurium andraeanum', season: '四季', cat: '纯爱·恋慕', mCN: '热情・激烈的心跳・好运', mJP: '情熱・熱心', mEN: 'Hospitality', colors: [['#E4002B', '佛焰红'], ['#FF69B4', '粉红掌']], note: '蜡质心形苞片＝热带/现代感；婚礼与酒店花艺' },
  { zh: '蝴蝶兰', en: 'phalaenopsis', tag: 'phalaenopsis', latin: 'Phalaenopsis', season: '冬→春', cat: '高贵·典雅', mCN: '我爱你・幸福向你飞来・高贵', mJP: '幸福が飛んでくる', mEN: 'Elegance', colors: [['#FFFFFF', '白兰'], ['#C9A0DC', '紫兰'], ['#FFC0CB', '粉兰']], note: '年花/婚礼；花型像飞舞的蝶' },
  { zh: '鸡蛋花', en: 'frangipani', tag: 'plumeria', latin: 'Plumeria', season: '夏', cat: '元气·希望', mCN: '希望・新的开始・单纯的爱', mJP: '気品・輝き', mEN: 'New beginnings', colors: [['#FFF8E7', '蛋花白'], ['#FFE4B5', '乳黄'], ['#FFD1DC', '粉']], note: '南洋/夏威夷/海岛场景；可作耳后簪花' },
  { zh: '金鱼草', en: 'snapdragon', tag: 'snapdragon', latin: 'Antirrhinum', season: '春→夏', cat: '元气·希望', mCN: '多嘴・傲慢・欲望（也有『优雅』）', mJP: 'おしゃべり・欲望', mEN: 'Deception・graciousness', colors: [['#FF6F61', '珊瑚红'], ['#FFD700', '黄'], ['#FFC0CB', '粉']], note: '花语有趣：适合多嘴角色/八卦担当' },
  { zh: '香豌豆', en: 'sweet pea', tag: 'sweet_pea', latin: 'Lathyrus odoratus', season: '春', cat: '温柔·守护', mCN: '甜蜜的回忆・启程・温柔喜悦', mJP: '門出・優しい思い出', mEN: 'Blissful pleasure・farewell', colors: [['#C8A2C8', '淡紫'], ['#FFB7C5', '粉'], ['#FFFFFF', '白']], note: '英国毕业/离别赠花；优雅藤本花' },
  { zh: '小苍兰', en: 'freesia', tag: 'freesia_(flower)', latin: 'Freesia', season: '春', cat: '温柔·守护', mCN: '纯粹・清香・期待再会', mJP: '清香・期待', mEN: 'Innocence・friendship', colors: [['#FFD700', '小苍兰黄'], ['#FFF8DC', '乳白']], note: '香氛系花；日系婚礼与香水意象' },
  { zh: '粉蝶花', en: 'nemophila', tag: 'nemophila_(flower)', latin: 'Nemophila menziesii', season: '春', cat: '元气·希望', mCN: '可爱・成功・诚实的心', mJP: '可憐・成功', mEN: 'Victory', colors: [['#7EC8E3', '粉蝶蓝'], ['#9AD0F5', '淡蓝']], note: '日立海滨公园『蓝海』名场面；蓝天花田' },
  { zh: '连翘', en: 'forsythia', tag: 'forsythia', latin: 'Forsythia', season: '春', cat: '元气·希望', mCN: '希望・预言・期待', mJP: '希望・期待', mEN: 'Anticipation', colors: [['#FFD700', '连翘金']], note: '早春金黄灌木；花开＝春天开始' },
  { zh: '石竹', en: 'dianthus', tag: 'dianthus', latin: 'Dianthus chinensis', season: '春→夏', cat: '温柔·守护', mCN: '纯洁的爱・才能・大胆', mJP: '純愛・才能', mEN: 'Boldness・devotion', colors: [['#FF69B4', '石竹粉'], ['#FFC0CB', '浅粉']], note: '与康乃馨同属；注意与康乃馨区分使用' },
  { zh: '金合欢（银荆）', en: 'mimosa', tag: 'mimosa_(flower)', latin: 'Acacia dealbata', season: '春', cat: '温柔·守护', mCN: '秘密的爱・友谊・女性力量', mJP: '友情・秘密の愛', mEN: 'Secret love・safety', colors: [['#FFD700', '金合欢黄']], note: '意大利三八节之花；tag 对应银荆/金合欢，非含羞草' },
  { zh: '雪绒花', en: 'edelweiss', tag: 'edelweiss_(flower)', latin: 'Leontopodium nivale', season: '夏（高山）', cat: '清冷·高洁', mCN: '勇气・重要回忆・高洁', mJP: '勇気・大切な思い出', mEN: 'Devotion・courage・noble purity', colors: [['#FFFDF5', '雪绒白'], ['#E8E4D5', '灰绿']], note: '阿尔卑斯高山花，采到＝勇气的证明（《音乐之声》名曲）' },
  { zh: '蓝花楹', en: 'jacaranda', tag: 'jacaranda', latin: 'Jacaranda mimosifolia', season: '春末夏初', cat: '高贵·典雅', mCN: '绝望中等待爱情・宁静深远', mJP: '慕情・遠い思い', mEN: 'Wisdom・rebirth', colors: [['#9E7FD4', '蓝楹紫'], ['#B7A0E3', '淡楹']], note: 'tag 极冷门（全站个位数）——出图建议搭配 blue flowers；紫色花雨街景' },
  { zh: '帝王花', en: 'protea', tag: 'protea_(flower)', latin: 'Protea cynaroides', season: '四季（南非冬雨）', cat: '高贵·典雅', mCN: '胜利・荣誉・华丽的转变', mJP: '王権・勝利', mEN: 'Transformation・daring', colors: [['#E86A90', '帝王粉'], ['#F2B5C4', '淡帝']], note: '南非国花，最古老被子植物之一；花型像王冠' },
  { zh: '曼陀罗（天使喇叭）', en: "angel's trumpet", tag: "angel's_trumpet_(flower)", latin: 'Datura / Brugmansia', season: '夏秋', cat: '神秘·危险', mCN: '不可预知的死亡与爱・理性', mJP: '夢の中・偽りの魅力', mEN: 'Deceitful charms', colors: [['#FFF8DC', '乳白'], ['#FFD1DC', '粉'], ['#C9A0DC', '淡紫']], note: '全株有毒（别做食物道具）；tag 是 angel\'s_trumpet_(flower)，曼陀罗/天使喇叭同属' },
  { zh: '昙花', en: 'epiphyllum', tag: 'epiphyllum', latin: 'Epiphyllum oxypetalum', season: '夏夜', cat: '神秘·危险', mCN: '刹那的美丽・一瞬的永恒', mJP: 'はかない美・一瞬の永遠', mEN: 'Brief beauty', colors: [['#FFFFFF', '夜白'], ['#FFF0F5', '淡粉']], note: '夜间开花数小时即谢＝『昙花一现』；月下/深夜场景名场面' },
  { zh: '雪割草', en: 'hepatica', tag: 'hepatica_(flower)', latin: 'Hepatica nobilis', season: '早春', cat: '清冷·高洁', mCN: '耐心・信赖・初春希望', mJP: '忍耐・信頼', mEN: 'Confidence', colors: [['#7B68EE', '雪割蓝'], ['#C8A2C8', '淡紫'], ['#FFFFFF', '白']], note: '日本『雪割草』：破雪报春的耐心花；冬末残雪场景' },
  { zh: '圣诞玫瑰（铁筷子）', en: 'hellebore', tag: 'hellebore', latin: 'Helleborus niger', season: '冬', cat: '神秘·危险', mCN: '安慰・丑闻（双面）', mJP: '慰め・悪口', mEN: 'Serenity・scandal', colors: [['#F2EDE4', '乳白'], ['#C8B7D8', '灰紫']], note: '冬花园代表；『丑闻』花语适合亦正亦邪角色' },
  { zh: '耧斗菜', en: 'columbine', tag: 'columbine_(flower)', latin: 'Aquilegia', season: '春', cat: '温柔·守护', mCN: '坦率・自由・愚直的爱', mJP: '誠実・心配', mEN: 'Folly・deserted love', colors: [['#8A7BD8', '耧斗紫'], ['#E6D7F5', '淡紫'], ['#FFD1DC', '粉']], note: '花型像鸽子/小丑帽；西式花语偏『愚行』，反差可用' },
  { zh: '蓝睡莲', en: 'blue lotus', tag: 'blue_lotus', latin: 'Nymphaea caerulea', season: '夏', cat: '神秘·危险', mCN: '神圣・复活・灵魂升华', mJP: '神聖・再生', mEN: 'Sacred mystery', colors: [['#6E8CD5', '蓝莲'], ['#A6B8E8', '淡蓝']], note: '古埃及圣花；区别于普通睡莲（water_lily_flower）' },
  { zh: '夹竹桃', en: 'oleander', tag: 'oleander', latin: 'Nerium oleander', season: '夏', cat: '神秘·危险', mCN: '危险的爱・谨慎', mJP: '危険な愛・用心', mEN: 'Beware', colors: [['#FF6F91', '夹竹粉'], ['#FFC0CB', '浅粉'], ['#FFFFFF', '白']], note: '全株剧毒（勿做食物道具）；路边/校园场景常见灌木' },
  { zh: '鹤望兰（天堂鸟）', en: 'bird of paradise', tag: 'bird_of_paradise_flower', latin: 'Strelitzia reginae', season: '四季', cat: '元气·希望', mCN: '飞向天堂的鸟・自由・热恋', mJP: '飛翔・自由', mEN: 'Freedom・joyfulness', colors: [['#FF8C00', '橙冠'], ['#5B7BD5', '蓝瓣']], note: '花型像极乐鸟；热带/现代花艺场景' },
  { zh: '嘉兰百合', en: 'gloriosa', tag: 'gloriosa_(flower)', latin: 'Gloriosa superba', season: '夏', cat: '高贵·典雅', mCN: '荣光・勇敢・华丽', mJP: '栄光・勇敢', mEN: 'Glorious beauty', colors: [['#FF3B30', '嘉兰红'], ['#FFD700', '金']], note: '火焰状反卷花瓣；全株有毒（观赏花）' },
  { zh: '三角梅（簕杜鹃）', en: 'bougainvillea', tag: 'bougainvillea_(flower)', latin: 'Bougainvillea', season: '四季（温暖）', cat: '元气·希望', mCN: '热情・坚韧・隐忍的爱', mJP: '情熱・忍耐', mEN: 'Passion', colors: [['#E4007F', '三角玫红'], ['#FF69B4', '粉'], ['#C71585', '深玫红']], note: '『花瓣』其实是苞片；南国白墙花瀑场景' },
  { zh: '高山杜鹃', en: 'rhododendron', tag: 'rhododendron', latin: 'Rhododendron', season: '春末夏初（高山）', cat: '清冷·高洁', mCN: '庄严・警戒・征服危险', mJP: '威厳・危険な魅力', mEN: 'Danger・beware', colors: [['#E75480', '高山玫红'], ['#C71585', '深红'], ['#F7C8D8', '淡粉']], note: '部分种类有毒；高原雪山/云海场景' },
  { zh: '蓝星花', en: 'tweedia', tag: 'tweedia', latin: 'Tweedia caerulea', season: '四季（温暖）', cat: '温柔·守护', mCN: '互信的心・信任・幸福', mJP: '信頼・幸福', mEN: 'True love', colors: [['#6CB4EE', '星蓝'], ['#9AD0F5', '淡星蓝']], note: '星形小蓝花；与勿忘我同色系可组『蓝色花束』' },
  { zh: '绿玉藤', en: 'jade vine', tag: 'jade_vine', latin: 'Strongylodon macrobotrys', season: '春（热带）', cat: '神秘·危险', mCN: '神秘的美丽・诱惑', mJP: '神秘・魅力', mEN: 'Enchantment', colors: [['#00A86B', '玉藤绿'], ['#71D6A8', '淡玉']], note: '教堂蓝绿渐变爪形花串；热带雨林稀有藤本' },
  { zh: '尸花（泰坦魔芋）', en: 'titan arum', tag: 'titan_arum', latin: 'Amorphophallus titanum', season: '四季（偶开）', cat: '神秘·危险', mCN: '极致的绽放・短暂与巨大', mJP: '—', mEN: 'Awe・rare bloom', colors: [['#7D2E46', '魔芋紫红'], ['#B23A5B', '暗玫'], ['#5B6E4A', '茎绿']], note: '世界最大花序，开花仅 1-2 天且气味强烈；奇迹/稀有主题' },
  { zh: '牡丹', en: 'peony', tag: 'peony_(flower) · chinese_peony', latin: 'Paeonia suffruticosa', season: '春末', cat: '高贵·典雅', mCN: '富贵・圆满・雍容华贵', mJP: '富貴・風格', mEN: 'Bashfulness・honor', colors: [['#E4007F', '牡丹玫红'], ['#FF69B4', '粉'], ['#FFFFFF', '白']], note: '中式『花中之王』；chinese_peony 亦可作 tag' },
  { zh: '石榴花', en: 'pomegranate flower', tag: 'pomegranate_flower', latin: 'Punica granatum', season: '夏', cat: '纯爱·恋慕', mCN: '成熟的美丽・多子多福・热烈的爱', mJP: '子孫繁栄・成熟した美', mEN: 'Fertility・hope', colors: [['#FF3B30', '榴红'], ['#FF6F61', '浅榴']], note: '中式吉祥（多子多福）；『石榴裙』意象' },
  { zh: '紫薇', en: 'crape myrtle', tag: 'crape_myrtle', latin: 'Lagerstroemia indica', season: '夏秋', cat: '高贵·典雅', mCN: '好运・沉醉的爱・和平', mJP: '雄弁・愛を信じる', mEN: 'Eloquent・felicity', colors: [['#E75480', '紫薇玫'], ['#C71585', '深紫薇'], ['#FFB7C5', '淡粉']], note: '花期百日（百日红）；tag 冷门（个位数）' },
  { zh: '金银花（忍冬）', en: 'honeysuckle', tag: 'honeysuckle', latin: 'Lonicera japonica', season: '春夏', cat: '温柔·守护', mCN: '真挚的爱・全心全意・奉献', mJP: '愛の絆・献身', mEN: 'Devotion・bonds of love', colors: [['#FFFDF5', '金银白'], ['#FFD700', '金瓣']], note: '藤蔓缠绕＝羁绊；药草/庭院意象。tag 冷门' },
  { zh: '铁线莲', en: 'clematis', tag: 'clematis_(flower)', latin: 'Clematis', season: '春末夏初', cat: '高贵·典雅', mCN: '心灵之美・高洁・旅人的喜悦', mJP: '精神の美・旅人の喜び', mEN: "Mental beauty・traveler's joy", colors: [['#8A2BE2', '铁线紫'], ['#C9A0DC', '淡紫'], ['#FFFFFF', '白']], note: '『藤本皇后』；有 clematis_print' },
  { zh: '迎春花', en: 'winter jasmine', tag: 'winter_jasmine', latin: 'Jasminum nudiflorum', season: '冬→春', cat: '元气·希望', mCN: '希望・新的开始・坚韧', mJP: '希望・新しい始まり', mEN: 'Hope', colors: [['#FFD700', '迎春金']], note: '早春第一花；与连翘易混（迎春 6 瓣 / 连翘 4 瓣）' },
  { zh: '玉簪', en: 'hosta', tag: 'hosta', latin: 'Hosta', season: '夏', cat: '清冷·高洁', mCN: '恬静・纯洁・幽雅', mJP: '静けさ・沈黙', mEN: 'Devotion', colors: [['#FFFFFF', '玉簪白'], ['#E6E6FA', '淡紫']], note: '阴生植物/庭院阴凉处；花似白玉簪' },
  { zh: '蓝雪花', en: 'plumbago', tag: 'plumbago_(flower)', latin: 'Plumbago auriculata', season: '夏秋', cat: '清冷·高洁', mCN: '冷静・沉着・优雅', mJP: '冷静・落ち着き', mEN: 'Calm・serenity', colors: [['#6CB4EE', '雪蓝'], ['#7EC8E3', '浅蓝']], note: '淡蓝小簇花；南国藤架/阳台场景' },
  { zh: '花毛茛（洋牡丹）', en: 'ranunculus', tag: 'ranunculus', latin: 'Ranunculus asiaticus', season: '春', cat: '温柔·守护', mCN: '迷人的魅力・受欢迎', mJP: '魅力的・あなたは魅力に満ちている', mEN: 'Radiant charm', colors: [['#FFC0CB', '粉'], ['#FF8C69', '珊瑚'], ['#FFFFFF', '白']], note: '层叠花瓣＝小牡丹感；婚礼花艺常客' },
  { zh: '六出花（秘鲁百合）', en: 'alstroemeria', tag: 'alstroemeria_(flower)', latin: 'Alstroemeria', season: '夏', cat: '纯爱·恋慕', mCN: '友谊・羁绊・新的联系', mJP: '友情・新しい絆', mEN: 'Friendship・devotion', colors: [['#FF8C69', '珊瑚橙'], ['#FFD700', '黄'], ['#FFC0CB', '粉']], note: '叶片翻转＝『逆境中的友谊』；花束常客' },
  { zh: '大花葱', en: 'allium', tag: 'allium_(flower)', latin: 'Allium giganteum', season: '春末夏初', cat: '高贵·典雅', mCN: '圆满・团结・无尽的爱', mJP: '正しい主張・無限', mEN: 'Unity・patience', colors: [['#9A7BD1', '葱紫'], ['#C9A0DC', '淡葱紫']], note: '球状花序＝紫色星球；现代花艺雕塑感' },
  { zh: '大王花', en: 'rafflesia', tag: 'rafflesia_(flower)', latin: 'Rafflesia arnoldii', season: '四季（偶开）', cat: '神秘·危险', mCN: '巨大的绽放・孤独的美・短暂', mJP: '—', mEN: 'Rare wonder・decay', colors: [['#B23A5B', '大王红'], ['#7D2E46', '暗红']], note: '世界最大单花：无叶无根寄生，开花数天腐肉味；稀有奇观' },
  { zh: '捕蝇草', en: 'venus flytrap', tag: 'venus_flytrap', latin: 'Dionaea muscipula', season: '夏', cat: '神秘·危险', mCN: '敏捷・陷阱・危险的魅力', mJP: '—', mEN: 'Cunning', colors: [['#8BC34A', '陷阱绿'], ['#E75480', '内膜红']], note: '食虫植物（非花）——战斗/反派角色符号；有同名角色 tag' },
  { zh: '棉花', en: 'cotton', tag: 'cotton_(plant)', latin: 'Gossypium', season: '秋', cat: '温柔·守护', mCN: '温柔・纯朴・珍惜眼前人', mJP: '素朴・温もり', mEN: 'Softness・domesticity', colors: [['#FFF8F0', '棉白'], ['#F5F0E6', '米白']], note: '棉花花语含『珍惜身边人』；秋收/乡野场景' },
  { zh: '凌霄花', en: 'chinese trumpet vine', tag: 'chinese_trumpet_vine', latin: 'Campsis grandiflora', season: '夏', cat: '元气·希望', mCN: '志向高远・向上・荣耀', mJP: '名声・高みを目指す', mEN: 'Victory・ambition', colors: [['#FF7043', '凌霄橙'], ['#FF9E80', '浅橙']], note: '攀援向上；中式庭院棚架/花墙' },
  { zh: '番红花', en: 'crocus', tag: 'crocus_(flower)', latin: 'Crocus sativus', season: '春·秋', cat: '元气·希望', mCN: '青春的喜悦・等待（春/秋两版花语不同）', mJP: '青春の喜び・待つ・青春の悲しみ', mEN: 'Cheerfulness・youth', colors: [['#C8A2C8', '番红紫'], ['#FF9933', '藏红花橙']], note: '春番红花＝青春喜悦；秋番红花柱头＝藏红花香料' },
  { zh: '紫茉莉', en: "four o'clock flower", tag: "four_o'clock_(flower)", latin: 'Mirabilis jalapa', season: '夏秋', cat: '温柔·守护', mCN: '胆小・害羞・夜色之美', mJP: '臆病・内気・あなたを想う', mEN: 'Timidity', colors: [['#C71585', '紫茉莉玫'], ['#FFD700', '黄'], ['#FFFFFF', '白']], note: '傍晚四点开花（four o\'clock）；童年记忆花' },
  { zh: '花菱草', en: 'california poppy', tag: 'california_poppy', latin: 'Eschscholzia californica', season: '春', cat: '元气·希望', mCN: '希望・富足・许诺', mJP: '希望・約束', mEN: 'Hope・prosperity', colors: [['#FF8C00', '金橙'], ['#FFD700', '花菱黄']], note: '加州州花；金橙色花海场景' },
  { zh: '蜀葵', en: 'hollyhock', tag: 'hollyhock', latin: 'Alcea rosea', season: '夏', cat: '元气·希望', mCN: '梦・丰饶・热情', mJP: '豊かさ・夢', mEN: 'Ambition・fruitfulness', colors: [['#C71585', '蜀葵玫'], ['#FF69B4', '粉'], ['#7B68EE', '紫']], note: '高杆花墙笔直挺立；中式别称『一丈红』' },
  { zh: '石斛兰', en: 'dendrobium', tag: 'dendrobium', latin: 'Dendrobium', season: '春', cat: '高贵·典雅', mCN: '坚毅・勇敢・吉祥', mJP: '堅忍・勇敢', mEN: 'Strength・endurance', colors: [['#C8A2C8', '石斛紫'], ['#FFFFFF', '白'], ['#FF69B4', '粉']], note: '台湾父亲节花；与蝴蝶兰区分使用' },
  { zh: '荷包牡丹', en: 'bleeding heart', tag: 'bleeding_heart_(flower)', latin: 'Lamprocapnos spectabilis', season: '春', cat: '悲伤·离别', mCN: '含泪的爱・不渝・答应你', mJP: '従順・恋心', mEN: 'Bleeding heart・hopeless love', colors: [['#FF4D6D', '泣血红'], ['#FFB7C5', '粉']], note: '心形垂串＝泣血的心；悲剧向角色绝配' },
  { zh: '黑色彼岸花', en: 'black spider lily', tag: 'black_spider_lily', latin: 'Lycoris radiata', season: '秋', cat: '神秘·危险', mCN: '绝望的爱・去往彼岸', mJP: '—', mEN: '—', colors: [['#2B2B33', '墨黑'], ['#4A2E3D', '暗玫']], note: '彼岸花变体（全站仅个位数）；妖异/黑化/反派主题' },
  { zh: '风铃草', en: 'bellflower', tag: 'bellflower', latin: 'Campanula', season: '夏', cat: '温柔·守护', mCN: '感谢・诚挚・恒定', mJP: '感謝・誠実', mEN: 'Gratitude・constancy', colors: [['#8A7BD8', '风铃紫'], ['#B19CD9', '淡紫']], note: '与桔梗区分：桔梗=chinese_bellflower、风铃草=bellflower' }
]

const genericTags: GenericTag[] = [
  { use: '单朵/捧花', tags: 'holding_flower, bouquet, flower_in_hair', desc: '持花/花束/簪花' },
  { use: '头饰', tags: 'flower_hair_ornament, flower_crown, wreath', desc: '花饰/花冠/花环' },
  { use: '场景', tags: 'flower_field, flower_garden, flower_shop', desc: '花田/花园/花店' },
  { use: '花瓣', tags: 'petals, falling_petals, floating_petals (*)', desc: '落瓣/飘瓣（花雨）' },
  { use: '纹样', tags: 'floral_print, flower_print', desc: '印花（cherry_blossom_print 未核对）' },
  { use: '道具', tags: 'vase, flower_pot, pressed_flower (*)', desc: '花瓶/花盆/压花' },
  { use: '氛围', tags: 'petal_on_water, flower_petals_on_ground (*)', desc: '水面落花/满地花瓣' }
]

/* ---------- 状态 ---------- */
const cats = computed<string[]>(() => [...new Set(FLOWERS.map((f: Flower) => f.cat))])
const seasons: string[] = ['春', '夏', '秋', '冬', '四季']
const catOn = reactive<Record<string, boolean>>({})
FLOWERS.forEach((f: Flower) => { catOn[f.cat] = true })
const seasonOnly = ref<string | null>(null)
const query = ref<string>('')
const tray = ref<TrayItem[]>([])
// 托盘头折叠：默认展开，状态落盘记住
const TRAY_LS = 'suli-flowers-tray'
let trayInit = true
try { trayInit = localStorage.getItem(TRAY_LS) !== '0' } catch {}
const trayOpen = ref<boolean>(trayInit)
function toggleTray(): void {
  trayOpen.value = !trayOpen.value
  try { localStorage.setItem(TRAY_LS, trayOpen.value ? '1' : '0') } catch {}
}
const imgOk = reactive<Record<string, boolean>>({})
FLOWERS.forEach((f: Flower) => { imgOk[f.tag] = true })

function toggleCat(c: string): void {
  catOn[c] = !catOn[c]
}
function toggleSeason(s: string): void {
  seasonOnly.value = seasonOnly.value === s ? null : s
}
function matchSeason(f: Flower, s: string): boolean {
  if (s === '四季') return f.season.includes('四季')
  return f.season.includes(s)
}
function firstTag(tag: string): string {
  return tag.split('（')[0].split(' · ')[0].trim()
}
function imgSrc(f: Flower): string {
  return FLOWER_IMGS[firstTag(f.tag)] || ''
}

const visibleFlowers = computed<Flower[]>(() => {
  const q: string = query.value.trim().toLowerCase()
  return FLOWERS.filter((f: Flower) => {
    if (!catOn[f.cat]) return false
    if (seasonOnly.value && !matchSeason(f, seasonOnly.value)) return false
    if (q) {
      const hay: string = (f.zh + f.en + f.tag + f.mCN + f.mJP + f.mEN + f.note).toLowerCase()
      if (!hay.includes(q)) return false
    }
    return true
  })
})
function clearFilters(): void {
  query.value = ''
  seasonOnly.value = null
  FLOWERS.forEach((f: Flower) => { catOn[f.cat] = true })
}

/* ---------- 托盘 ---------- */
function copyTag(tag: string): void {
  copyText(tag)
}
function addToTray(f: Flower): void {
  const tag: string = firstTag(f.tag)
  if (!tray.value.some((t: TrayItem) => t.tag === tag)) {
    tray.value.push({ zh: f.zh, tag })
    ElMessage.success('已加入组合：' + f.zh)
  } else {
    ElMessage.info('已在组合里：' + f.zh)
  }
}
function removeFromTray(tag: string): void {
  tray.value = tray.value.filter((t: TrayItem) => t.tag !== tag)
}
function clearTray(): void {
  tray.value = []
}
function copyTray(): void {
  if (tray.value.length === 0) {
    ElMessage.info('先把花加进组合')
    return
  }
  copyText(tray.value.map((t: TrayItem) => t.tag).join(', '))
}

/* ---------- 就地展开 ---------- */
const openKey = ref<string | null>(null)
function isOpen(key: string): boolean {
  return openKey.value === key
}
function toggleDetail(key: string): void {
  openKey.value = openKey.value === key ? null : key
}
function commonsUrlFor(f: Flower): string {
  return 'https://commons.wikimedia.org/w/index.php?search=' + encodeURIComponent(f.latin)
}
function stepOpen(d: number): void {
  const list: Flower[] = visibleFlowers.value
  if (list.length === 0) return
  const cur: number = list.findIndex((f: Flower) => f.tag === openKey.value)
  const base: number = cur < 0 ? 0 : cur
  const next: number = (base + d + list.length) % list.length
  openKey.value = list[next].tag
}
function copyImgPath(f: Flower): void {
  copyText(imgSrc(f))
}
function onKey(e: KeyboardEvent): void {
  if (openKey.value === null) return
  if (e.key === 'ArrowLeft') stepOpen(-1)
  else if (e.key === 'ArrowRight') stepOpen(1)
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.flowers-tool {
  padding: 12px;
  background: #fff;
  color: var(--suli-text);
  font-size: 13px;
  line-height: 1.7;
}
.tray {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #fff;
  border: 1px solid var(--suli-border);
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.tray-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.tray-label {
  font-size: 12px;
  color: var(--suli-text-2);
  white-space: nowrap;
}
.chip { cursor: pointer; }
.search-input { flex: 1; min-width: 160px; max-width: 300px; }
.hint { font-size: 12px; }
.intro { margin: 12px 2px; }
.intro code {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 12px;
  background: #f4f4f5;
  padding: 1px 6px;
  border-radius: 4px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
  margin-top: 12px;
}
.tool-card {
  padding: 10px 10px 12px;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.tool-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(251, 114, 153, 0.18);
  border-color: var(--suli-primary);
}
.cover {
  position: relative;
  width: 100%;
  height: 150px;
  border-radius: 8px;
  overflow: hidden;
  background: #f4f4f5;
}
.photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  background: #f4f4f5;
}
.cover-ph {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 44px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #FB7299, #FFB7C5);
}
.cover-ph.big {
  height: 220px;
  border-radius: 10px;
  font-size: 64px;
}
.cat-chip {
  position: absolute;
  left: 8px;
  top: 8px;
  font-size: 11px;
  line-height: 1;
  padding: 4px 8px;
  border-radius: 999px;
  color: #fff;
  background: rgba(251, 114, 153, 0.92);
}
.hd { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.zh { font-size: 16px; font-weight: 700; color: var(--suli-text); }
.en { font-size: 12px; }
.tag-row { margin-top: 6px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.mono { font-family: ui-monospace, Consolas, monospace; }
.season { font-size: 11.5px; }
.ellipsis {
  margin-top: 6px;
  font-size: 12.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.mean { margin-top: 8px; font-size: 12.5px; color: var(--suli-text); }
.mean-row { cursor: pointer; border-radius: 6px; padding: 1px 4px; }
.mean-row:hover { background: #f4f4f5; }
.mean b { color: var(--suli-text-2); font-weight: 600; }
.sw { display: flex; gap: 6px; margin-top: 9px; flex-wrap: wrap; align-items: center; }
.swdot {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  cursor: pointer;
}
.swtxt { font-size: 11.5px; }
.note-pre { margin-top: 10px; }
.dlg-cover { width: 100%; }
.dlg-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; width: 100%; }
.dlg-tagrow { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; width: 100%; }
section { margin-top: 20px; }
.tip { margin: 2px 0 8px; }
.gentable {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border: 1px solid var(--suli-border);
  border-radius: 10px;
  font-size: 13px;
}
.gentable th,
.gentable td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid var(--suli-border);
  vertical-align: top;
}
.gentable tr:last-child td { border-bottom: none; }
.tagcell { font-family: ui-monospace, Consolas, monospace; font-size: 12.5px; cursor: pointer; }
.tagcell:hover { background: #f4f4f5; }
ul.plain {
  list-style: none;
  margin: 0;
  padding: 12px 16px;
  font-size: 13px;
  line-height: 1.9;
}
.count { font-size: 12px; white-space: nowrap; }
ul.plain li::before { content: "- "; color: #FB7299; }
.foot { margin: 20px 2px 4px; font-size: 12px; }
.empty { padding: 16px 4px; }
.tool-card.open { grid-column: span 2; border-color: var(--suli-primary,#FB7299); }
.detail-block { margin-top: 10px; border-top: 1px dashed var(--suli-border); padding-top: 10px; }
.detail-cols { display: grid; grid-template-columns: 220px 1fr; gap: 12px; }
@media (max-width: 640px) { .detail-cols { grid-template-columns: repeat(auto-fit,minmax(200px,1fr)); } }
.detail-title { display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap; }
.detail-main { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.dlg-img { width: 100%; height: 220px; object-fit: cover; border-radius: 10px; }
.dlg-cap { font-size: 13px; text-align: center; }
.dlg-bar { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; align-items: center; }
.commons-link { font-size: 13px; }

@container (max-width: 620px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
  .detail-cols { grid-template-columns: 1fr; }
}
@container (max-width: 400px) {
  .grid { grid-template-columns: 1fr; }
}
/* pack-slots: backpack face */
.tool-card > .tag-row, .tool-card > .ellipsis { display: none; }
.tool-card > .hd { overflow: hidden; }
.tool-card > .hd > * { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tool-card.open { box-shadow: 0 0 0 2px rgba(251,114,153,.45), 0 8px 20px rgba(251,114,153,.25); }</style>
