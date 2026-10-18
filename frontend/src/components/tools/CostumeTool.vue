<template>
  <div class="costume-tool">
    <!-- 白色 sticky 搭配台 -->
    <div class="tray">
      <div class="tray-row">
        <span class="tray-label">搭配台</span>
        <span class="tray-slots">
          <el-tag
            v-if="activeStyle"
            closable
            type="warning"
            class="mono-tag"
            :title="'风格: ' + activeStyle.zh"
            @close="activeStyle = null"
          >{{ activeStyle.en }}</el-tag>
          <template v-for="s in slots" :key="s.k">
            <el-tag
              v-for="(c, i) in s.v"
              :key="s.k + c.tag"
              closable
              class="mono-tag"
              :title="c.zh"
              @close="removeFromSlot(s.k, i)"
            >{{ c.tag }}</el-tag>
          </template>
          <span v-if="isEmpty" class="suli-muted tray-empty">还没选</span>
        </span>
        <el-button type="primary" size="small" @click="onCopyOutfit">复制成套 prompt</el-button>
        <el-button size="small" @click="onCopyPoint">复制指向句</el-button>
        <el-button size="small" @click="onClearAll">清空</el-button>
        <el-button size="small" text @click="toggleTray">{{ trayOpen ? '收起 ▲' : '展开 ▼' }}</el-button>
      </div>
      <template v-if="trayOpen">
      <div class="tray-row">
        <span class="tray-label">分类</span>
        <el-tag
          v-for="c in cats"
          :key="c"
          :effect="activeCat === c ? 'dark' : 'plain'"
          :type="activeCat === c ? 'primary' : 'info'"
          class="chip"
          @click="activeCat = c"
        >{{ c }}</el-tag>
        <span class="suli-muted count">{{ filtered.length }} / {{ allCards.length }}</span>
        <el-button size="small" @click="clearFilter">清空筛选</el-button>
      </div>
      <div class="tray-row">
        <el-input
          v-model="query"
          placeholder="搜索"
          clearable
          size="small"
          class="tray-search"
        />
      </div>
      </template>
    </div>

    <div class="grid">
      <div
        v-for="c in filtered"
        :key="c.key"
        class="suli-card tool-card"
        :class="{ picked: c.picked, open: isOpen(c.key) }"
        @click="toggleDetail(c.key)"
      >
        <div v-if="c.styleIdx >= 0 && styleImgOk[c.styleIdx]" class="style-photo">
          <img
            :src="styles[c.styleIdx].img || ''" :alt="c.zh" loading="lazy"
            @error="styleImgOk[c.styleIdx] = false"
          />
        </div>
        <div v-else-if="itemImg(c) && itemImgOk[c.key] !== false" class="style-photo">
          <img
            :src="itemImg(c)" :alt="c.zh" loading="lazy"
            @error="itemImgOk[c.key] = false"
          />
        </div>
        <div v-else class="cover">
          <span>{{ c.cover }}</span>
        </div>
        <div class="zh">{{ c.zh }}</div>
        <div class="en muted">{{ c.en }}</div>
        <div class="tag-list">
          <el-tag size="small" type="info">{{ c.cat }}</el-tag>
          <el-tag v-if="c.tag" size="small" class="mono-tag">{{ shortTag(c.tag) }}</el-tag>
        </div>
        <div class="suli-muted note">{{ c.summary }}</div>
        <el-dialog append-to-body :model-value="isOpen(c.key)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
          <div class="detail-block">
          <div class="detail-cols">
            <div class="dlg-cover">
              <img
                v-if="c.styleIdx >= 0 && styleImgOk[c.styleIdx]"
                :src="styles[c.styleIdx].img || ''" :alt="c.zh" loading="lazy"
                @error="styleImgOk[c.styleIdx] = false"
              />
              <img
                v-else-if="itemImg(c) && itemImgOk[c.key] !== false"
                :src="itemImg(c)" :alt="c.zh" loading="lazy"
                @error="itemImgOk[c.key] = false"
              />
              <span v-else>{{ c.cover }}</span>
            </div>
            <div>
              <div class="suli-muted">{{ c.en }} ｜ {{ c.cat }}</div>
              <div v-if="c.tag" class="dlg-tags">
                <el-tag
                  v-for="t in c.tag.split(',').map((x) => x.trim()).filter(Boolean)"
                  :key="t"
                  size="small"
                  class="mono-tag"
                  @click.stop="copyOne(t)"
                >{{ t }}</el-tag>
              </div>
              <p class="dlg-note">{{ c.summary }}</p>
              <p v-if="c.pair" class="suli-muted">搭法：{{ c.pair }}</p>
              <p v-if="c.risk" class="risk">注意：{{ c.risk }}</p>
              <pre v-if="c.pre" class="suli-pre mono">{{ c.pre }}</pre>
              <div v-if="c.html" class="dlg-html" v-html="c.html"></div>
              <div class="detail-actions">
                <el-button v-if="c.tag" size="small" @click.stop="copyDetail(c)">复制 tag</el-button>
                <el-button v-if="c.kind !== 'howto'" size="small" type="primary" @click.stop="pickDetail(c)">加入搭配台</el-button>
                <el-button size="small" @click.stop="openKey = null">收起</el-button>
              </div>
            </div>
          </div>
        </div>
        </el-dialog>
      </div>
    </div>
    <p v-if="!filtered.length" class="suli-muted empty">无匹配，换关键词或清空筛选。</p>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import type { Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { copyText } from '../../utils/clipboard'

interface StylePack {
  zh: string
  en: string
  tags: string[]
  desc: string
  pair: string
  risk: string
  img?: string
}

interface CostumeItem {
  zh: string
  tag: string
  note: string
  pair: string
  risk: string
}

interface CostumeGroup {
  group: string
  sub: string
  items: CostumeItem[]
}

interface Slot {
  k: string
  v: CostumeItem[]
}

interface CardItem {
  key: string
  kind: 'style' | 'item' | 'howto'
  zh: string
  en: string
  cat: string
  tag: string
  summary: string
  pair: string
  risk: string
  pre: string
  html: string
  cover: string
  picked: boolean
  group: string
  styleIdx: number
  itemRef: CostumeItem | null
  styleRef: StylePack | null
}

interface Howto {
  h: string
  p: string
  pre: string
}

const styles: StylePack[] = [
  { zh: '学院 JK', en: 'school uniform', tags: ['serafuku', 'pleated skirt', 'blazer', 'necktie', 'loafers', 'kneehighs'], desc: '水手服或西装衬衫＋百褶裙，整齐校服轮廓', pair: '上装换领结/领带调气质；裙长定角色年龄感', risk: '胸前校徽易乱入，negative 常驻 emblem' },
  { zh: 'Lolita 甜系', en: 'sweet lolita', tags: ['lolita fashion', 'frills', 'lace', 'petticoat', 'hair bow'], desc: '白粉主色、蕾丝荷叶边、大裙撑，甜点感', pair: '搭玛丽珍+过膝袜；配饰只留一件大蝴蝶结', risk: '层数过多易糊，裙撑写 petticoat 别写 stiffer' },
  { zh: 'Lolita 古典', en: 'classical lolita', tags: ['lolita fashion', 'blouse', 'lace', 'mary janes'], desc: '暗色系、素雅蕾丝，贵妇感不甜腻', pair: '酒红/墨绿＋金饰；领口加蕾丝提精致度', risk: '低对比暗色易脏，光影阶段再压暗' },
  { zh: 'Lolita 哥特', en: 'gothic lolita', tags: ['gothic lolita', 'corset', 'lace', 'cross', 'platform shoes'], desc: '黑白＋暗红，束腰十字架，冷艳', pair: '配十字架项链；甲油暗红', risk: '与地雷系易混，取一样学够' },
  { zh: '女仆', en: 'maid', tags: ['maid', 'maid headdress', 'apron', 'frills', 'black thighhighs'], desc: '黑白长裙＋围裙＋头饰，服务感', pair: '领口用白围裙压住黑色；袖口加蕾丝', risk: '头饰细碎易崩，写 maid headdress 就够' },
  { zh: '地雷系', en: 'jirai kei', tags: ['jirai kei', 'black skirt', 'cross necklace', 'platform shoes', 'choker'], desc: '黑粉主色、暗黑小物堆叠，厌世甜', pair: '上装短小＋高腰下装；点缀色只留一个暗红或粉', risk: '小物>2件即乱，signature 只留一件' },
  { zh: '量产型', en: 'ryousangata', tags: ['ryousangata', 'white blouse', 'pleated skirt', 'hair bow', 'frills'], desc: '白粉主色、蕾丝小物，甜妹量产', pair: '配色统一不可花；发型配大蝴蝶结', risk: '与甜系 Lolita 区分在裙长与裙撑' },
  { zh: '哥特暗黑', en: 'gothic', tags: ['gothic', 'corset', 'velvet', 'cross', 'lace'], desc: '黑＋暗紫红，丝绒束腰，教堂感', pair: '金属用银不用金；加披风定剪影', risk: '全黑丢结构，材质对比要写（velvet vs lace）' },
  { zh: '朋克街头', en: 'punk', tags: ['punk', 'studs', 'leather jacket', 'plaid skirt', 'safety pins'], desc: '皮革铆钉格纹，叛逆轮廓', pair: '格纹裙＋破洞袜；金属配件集中在上装', risk: '铆钉/别针细密，易糊，写 studs 即可' },
  { zh: '机能科幻', en: 'techwear', tags: ['techwear', 'harness', 'straps', 'buckles', 'cargo pants'], desc: '黑灰多口袋绑带，未来城市感', pair: '荧光色只做点缀；结构线要利落', risk: '绑带数量失控，复杂系带降级为粗带' },
  { zh: '和风', en: 'japanese clothes', tags: ['kimono', 'obi', 'geta', 'kanzashi', 'cherry blossoms'], desc: '和服/浴衣＋腰带，花纹讲究', pair: '花纹单一大图案；腰带做色块焦点', risk: '小纹样易糊，写大图案或无图案' },
  { zh: '巫女', en: 'miko', tags: ['miko', 'hakama', 'detached sleeves', 'ribbon', 'tabi'], desc: '白衣红袴，巫女装束', pair: '上白下红为铁则；加发带收气质', risk: '袖子结构常崩，写 detached sleeves 防糊' },
  { zh: '军装战术', en: 'military', tags: ['military uniform', 'epaulettes', 'medals', 'peacoat', 'beret'], desc: '制服硬挺、肩章勋章，纪律感', pair: '配色藏青/军绿＋金扣；贝雷帽压气质', risk: '勋章细碎，写 epaulettes 提层次就够' },
  { zh: '运动', en: 'sports', tags: ['gym uniform', 'track jacket', 'bloomers', 'sneakers', 'whistle'], desc: '体操服/运动夹克，活力日常', pair: '上下撞色；袜选短袜或过膝', risk: '运动服文字/Logo 一律不写' },
  { zh: '泳装夏', en: 'swimsuit', tags: ['school swimsuit', 'one-piece swimsuit', 'sun hat', 'parasol'], desc: '泳装＋沙滩小物，夏日清爽', pair: '配遮阳帽/纱裙；湿发湿身加分', risk: 'nsfw 词别混入；写 one-piece swimsuit 别写 bikini 除非要' },
  { zh: '冬装大衣', en: 'winter coat', tags: ['duffle coat', 'turtleneck', 'scarf', 'mittens', 'boots'], desc: '厚大衣＋围巾手套，冬季轮廓', pair: '大衣定剪影、内搭高领；围巾做点缀色', risk: '层次多易臃肿，层数≤3' },
  { zh: '魔法幻想', en: 'fantasy', tags: ['witch hat', 'cape', 'staff', 'floating', 'magic'], desc: '女巫法师：斗篷尖帽杖，神秘感', pair: '斗篷定剪影，帽子定职业；配饰留一件魔法物', risk: '魔法特效留给光影阶段，服装阶段不写' },
  { zh: '中式', en: 'chinese clothes', tags: ['china dress', 'hanfu', 'wide sleeves', 'tassel', 'hair ornament'], desc: '旗袍或汉服，立领盘扣流苏', pair: '旗袍走窄轮廓、汉服走大袖；配发簪', risk: '刺绣细纹易崩，写大图案或素面' },
]
// 流派配图：public/tools/costume/<idx>.jpg（Safebooru solo 示例，脚本补全，缺图自动回退首字）
styles.forEach((s, i) => { s.img = `/tools/costume/${i}.jpg` })
const styleImgOk: Ref<boolean[]> = ref(styles.map(() => true))

// 单品配图：public/tools/costume/items/<file>.jpg（Safebooru solo 示例，脚本补全，缺图自动回退首字）
// 键 = CardItem.key（'item-'+group+'-'+zh+'-'+tag），198 件全量已补
const ITEM_IMGS: Record<string, string> = {
  'item-上装 · 外搭-西装外套-blazer': '/tools/costume/items/item_000.jpg',
  'item-上装 · 外搭-西装马甲-waistcoat': '/tools/costume/items/item_001.jpg',
  'item-上装 · 外搭-皮夹克-leather jacket': '/tools/costume/items/item_002.jpg',
  'item-上装 · 外搭-牛仔夹克-denim jacket': '/tools/costume/items/item_003.jpg',
  'item-上装 · 外搭-飞行员夹克-bomber jacket': '/tools/costume/items/item_004.jpg',
  'item-上装 · 外搭-军装大衣-peacoat': '/tools/costume/items/item_005.jpg',
  'item-上装 · 外搭-风衣-trench coat': '/tools/costume/items/item_006.jpg',
  'item-上装 · 外搭-羊毛大衣-winter coat': '/tools/costume/items/item_007.jpg',
  'item-上装 · 外搭-斗篷-cape': '/tools/costume/items/item_008.jpg',
  'item-上装 · 外搭-短披肩-capelet': '/tools/costume/items/item_009.jpg',
  'item-上装 · 外搭-连帽斗篷-hooded cape': '/tools/costume/items/item_010.jpg',
  'item-上装 · 外搭-针织披肩-shawl': '/tools/costume/items/item_011.jpg',
  'item-上装 · 外搭-羽织-haori': '/tools/costume/items/item_012.jpg',
  'item-上装 · 外搭-实验室白袍-labcoat': '/tools/costume/items/item_013.jpg',
  'item-上装 · 外搭-双排扣西装-double-breasted jacket': '/tools/costume/items/item_014.jpg',
  'item-上装 · 内搭-白衬衫-white shirt': '/tools/costume/items/item_015.jpg',
  'item-上装 · 内搭-水手领衬衫-sailor collar, shirt': '/tools/costume/items/item_016.jpg',
  'item-上装 · 内搭-彼得潘领-peter pan collar': '/tools/costume/items/item_017.jpg',
  'item-上装 · 内搭-立领衬衫-high collar, shirt': '/tools/costume/items/item_018.jpg',
  'item-上装 · 内搭-高领衫-turtleneck': '/tools/costume/items/item_019.jpg',
  'item-上装 · 内搭-V领上衣-v-neck': '/tools/costume/items/item_020.jpg',
  'item-上装 · 内搭-露肩衬衫-off shoulder, shirt': '/tools/costume/items/item_021.jpg',
  'item-上装 · 内搭-蕾丝衬衫-lace, shirt': '/tools/costume/items/item_022.jpg',
  'item-上装 · 内搭-泡泡袖衬衫-puffy sleeves, shirt': '/tools/costume/items/item_023.jpg',
  'item-上装 · 内搭-荷叶边衬衫-frilled shirt': '/tools/costume/items/item_024.jpg',
  'item-上装 · 内搭-飘带衬衫-ribbon, shirt': '/tools/costume/items/item_025.jpg',
  'item-上装 · 内搭-针织衫-sweater': '/tools/costume/items/item_026.jpg',
  'item-上装 · 内搭-针织开衫-cardigan': '/tools/costume/items/item_027.jpg',
  'item-上装 · 内搭-针织马甲-sweater vest': '/tools/costume/items/item_028.jpg',
  'item-上装 · 内搭-卫衣-hoodie': '/tools/costume/items/item_029.jpg',
  'item-上装 · 内搭-T恤-t-shirt': '/tools/costume/items/item_030.jpg',
  'item-上装 · 内搭-条纹衫-striped shirt': '/tools/costume/items/item_031.jpg',
  'item-上装 · 内搭-吊带背心-camisole': '/tools/costume/items/item_032.jpg',
  'item-上装 · 内搭-无袖背心-tank top': '/tools/costume/items/item_033.jpg',
  'item-上装 · 内搭-制服衬衫-dress shirt': '/tools/costume/items/item_034.jpg',
  'item-连衣裙 · 连体-A字连衣裙-a-line dress': '/tools/costume/items/item_035.jpg',
  'item-连衣裙 · 连体-衬衫裙-long shirt': '/tools/costume/items/item_036.jpg',
  'item-连衣裙 · 连体-背心裙-suspender skirt': '/tools/costume/items/item_037.jpg',
  'item-连衣裙 · 连体-针织连衣裙-sweater dress': '/tools/costume/items/item_038.jpg',
  'item-连衣裙 · 连体-吊带连衣裙-sundress': '/tools/costume/items/item_039.jpg',
  'item-连衣裙 · 连体-蛋糕裙-frilled dress': '/tools/costume/items/item_040.jpg',
  'item-连衣裙 · 连体-蓬蓬裙-petticoat': '/tools/costume/items/item_041.jpg',
  'item-连衣裙 · 连体-洛丽塔裙-lolita fashion, dress': '/tools/costume/items/item_042.jpg',
  'item-连衣裙 · 连体-JSK 吊带洛丽塔-suspender skirt, lolita fashion': '/tools/costume/items/item_043.jpg',
  'item-连衣裙 · 连体-晚礼服-evening gown': '/tools/costume/items/item_044.jpg',
  'item-连衣裙 · 连体-婚纱-wedding dress': '/tools/costume/items/item_045.jpg',
  'item-连衣裙 · 连体-旗袍-china dress': '/tools/costume/items/item_046.jpg',
  'item-连衣裙 · 连体-汉服-hanfu, wide sleeves': '/tools/costume/items/item_047.jpg',
  'item-连衣裙 · 连体-女仆装-maid, apron': '/tools/costume/items/item_048.jpg',
  'item-连衣裙 · 连体-护士服-nurse, nurse cap': '/tools/costume/items/item_049.jpg',
  'item-连衣裙 · 连体-巫女服-miko, hakama': '/tools/costume/items/item_050.jpg',
  'item-和服 · 长袍-和服-kimono': '/tools/costume/items/item_051.jpg',
  'item-和服 · 长袍-浴衣-yukata': '/tools/costume/items/item_052.jpg',
  'item-和服 · 长袍-振袖-furisode': '/tools/costume/items/item_053.jpg',
  'item-和服 · 长袍-羽织袴-hakama, haori': '/tools/costume/items/item_054.jpg',
  'item-和服 · 长袍-甚平-jinbei': '/tools/costume/items/item_055.jpg',
  'item-和服 · 长袍-作务衣-japanese clothes': '/tools/costume/items/item_056.jpg',
  'item-和服 · 长袍-道袍-robe': '/tools/costume/items/item_057.jpg',
  'item-和服 · 长袍-法袍-robe': '/tools/costume/items/item_058.jpg',
  'item-下装-百褶裙-pleated skirt': '/tools/costume/items/item_059.jpg',
  'item-下装-刀褶裙-pleated skirt': '/tools/costume/items/item_060.jpg',
  'item-下装-迷你裙-miniskirt': '/tools/costume/items/item_061.jpg',
  'item-下装-背带裙-suspender skirt': '/tools/costume/items/item_062.jpg',
  'item-下装-鱼尾裙-long skirt': '/tools/costume/items/item_063.jpg',
  'item-下装-包臀裙-pencil skirt': '/tools/costume/items/item_064.jpg',
  'item-下装-牛仔短裤-denim shorts': '/tools/costume/items/item_065.jpg',
  'item-下装-百褶短裤-pleated shorts': '/tools/costume/items/item_066.jpg',
  'item-下装-工装裤-cargo pants': '/tools/costume/items/item_067.jpg',
  'item-下装-西装长裤-pants': '/tools/costume/items/item_068.jpg',
  'item-下装-连体裤-jumpsuit': '/tools/costume/items/item_069.jpg',
  'item-下装-背带裤-overalls': '/tools/costume/items/item_070.jpg',
  'item-袜装 · 腿部-短袜-ankle socks': '/tools/costume/items/item_071.jpg',
  'item-袜装 · 腿部-中筒袜-kneehighs': '/tools/costume/items/item_072.jpg',
  'item-袜装 · 腿部-过膝袜-over-kneehighs': '/tools/costume/items/item_073.jpg',
  'item-袜装 · 腿部-大腿袜-thighhighs': '/tools/costume/items/item_074.jpg',
  'item-袜装 · 腿部-松垮袜-loose socks': '/tools/costume/items/item_075.jpg',
  'item-袜装 · 腿部-条纹袜-striped socks': '/tools/costume/items/item_076.jpg',
  'item-袜装 · 腿部-连裤袜-pantyhose': '/tools/costume/items/item_077.jpg',
  'item-袜装 · 腿部-厚黑丝-black pantyhose': '/tools/costume/items/item_078.jpg',
  'item-袜装 · 腿部-网袜-fishnet stockings': '/tools/costume/items/item_079.jpg',
  'item-袜装 · 腿部-吊带袜-garter belt, thighhighs': '/tools/costume/items/item_080.jpg',
  'item-袜装 · 腿部-腿环-thigh strap': '/tools/costume/items/item_081.jpg',
  'item-袜装 · 腿部-袜套-leg warmers': '/tools/costume/items/item_082.jpg',
  'item-袜装 · 腿部-赤足裸腿-bare legs': '/tools/costume/items/item_083.jpg',
  'item-鞋-乐福鞋-loafers': '/tools/costume/items/item_084.jpg',
  'item-鞋-玛丽珍-mary janes': '/tools/costume/items/item_085.jpg',
  'item-鞋-室内鞋-uwabaki': '/tools/costume/items/item_086.jpg',
  'item-鞋-厚底鞋-platform shoes': '/tools/costume/items/item_087.jpg',
  'item-鞋-高跟鞋-high heels': '/tools/costume/items/item_088.jpg',
  'item-鞋-短靴-ankle boots': '/tools/costume/items/item_089.jpg',
  'item-鞋-长靴-knee boots': '/tools/costume/items/item_090.jpg',
  'item-鞋-系带长靴-lace-up boots': '/tools/costume/items/item_091.jpg',
  'item-鞋-运动鞋-sneakers': '/tools/costume/items/item_092.jpg',
  'item-鞋-凉鞋-sandals': '/tools/costume/items/item_093.jpg',
  'item-鞋-木屐-geta': '/tools/costume/items/item_094.jpg',
  'item-鞋-草履-zouri': '/tools/costume/items/item_095.jpg',
  'item-鞋-足袋-tabi': '/tools/costume/items/item_096.jpg',
  'item-头部 · 发饰-发带-hairband': '/tools/costume/items/item_097.jpg',
  'item-头部 · 发饰-丝带发饰-hair ribbon': '/tools/costume/items/item_098.jpg',
  'item-头部 · 发饰-大蝴蝶结-hair bow': '/tools/costume/items/item_099.jpg',
  'item-头部 · 发饰-发夹-hairclip': '/tools/costume/items/item_100.jpg',
  'item-头部 · 发饰-蕾丝发带-lace headband': '/tools/costume/items/item_101.jpg',
  'item-头部 · 发饰-发圈-scrunchie': '/tools/costume/items/item_102.jpg',
  'item-头部 · 发饰-花朵发饰-hair flower': '/tools/costume/items/item_103.jpg',
  'item-头部 · 发饰-发簪-hair stick': '/tools/costume/items/item_104.jpg',
  'item-头部 · 发饰-兽耳发饰-animal ears, hairband': '/tools/costume/items/item_105.jpg',
  'item-头部 · 发饰-头纱-veil': '/tools/costume/items/item_106.jpg',
  'item-头部 · 发饰-贝雷帽-beret': '/tools/costume/items/item_107.jpg',
  'item-头部 · 发饰-报童帽-newsboy cap': '/tools/costume/items/item_108.jpg',
  'item-头部 · 发饰-宽檐帽-sun hat': '/tools/costume/items/item_109.jpg',
  'item-头部 · 发饰-女巫帽-witch hat': '/tools/costume/items/item_110.jpg',
  'item-头部 · 发饰-护士帽-nurse cap': '/tools/costume/items/item_111.jpg',
  'item-头部 · 发饰-空乘帽-pillbox hat': '/tools/costume/items/item_112.jpg',
  'item-面部 · 耳部-眼镜-glasses': '/tools/costume/items/item_113.jpg',
  'item-面部 · 耳部-墨镜-sunglasses': '/tools/costume/items/item_114.jpg',
  'item-面部 · 耳部-单片眼镜-monocle': '/tools/costume/items/item_115.jpg',
  'item-面部 · 耳部-眼罩-eyepatch': '/tools/costume/items/item_116.jpg',
  'item-面部 · 耳部-耳钉-earrings': '/tools/costume/items/item_117.jpg',
  'item-面部 · 耳部-耳环-hoop earrings': '/tools/costume/items/item_118.jpg',
  'item-面部 · 耳部-耳坠-tassel earrings': '/tools/costume/items/item_119.jpg',
  'item-面部 · 耳部-口罩-mask': '/tools/costume/items/item_120.jpg',
  'item-面部 · 耳部-唇彩-lipstick': '/tools/costume/items/item_121.jpg',
  'item-面部 · 耳部-腮红-blush': '/tools/costume/items/item_122.jpg',
  'item-颈部 · 胸肩-项圈-choker': '/tools/costume/items/item_123.jpg',
  'item-颈部 · 胸肩-丝带颈饰-ribbon choker': '/tools/costume/items/item_124.jpg',
  'item-颈部 · 胸肩-十字架项链-cross necklace': '/tools/costume/items/item_125.jpg',
  'item-颈部 · 胸肩-珍珠项链-pearl necklace': '/tools/costume/items/item_126.jpg',
  'item-颈部 · 胸肩-领结-bowtie': '/tools/costume/items/item_127.jpg',
  'item-颈部 · 胸肩-领带-necktie': '/tools/costume/items/item_128.jpg',
  'item-颈部 · 胸肩-领巾-neckerchief': '/tools/costume/items/item_129.jpg',
  'item-颈部 · 胸肩-围巾-scarf': '/tools/costume/items/item_130.jpg',
  'item-颈部 · 胸肩-胸针-brooch': '/tools/costume/items/item_131.jpg',
  'item-颈部 · 胸肩-肩章-epaulettes': '/tools/costume/items/item_132.jpg',
  'item-颈部 · 胸肩-肩上搭外套-jacket on shoulders': '/tools/costume/items/item_133.jpg',
  'item-腰部 · 手部-腰带-belt': '/tools/costume/items/item_134.jpg',
  'item-腰部 · 手部-腰封-corset': '/tools/costume/items/item_135.jpg',
  'item-腰部 · 手部-蝴蝶结腰带-belt bow': '/tools/costume/items/item_136.jpg',
  'item-腰部 · 手部-链条腰带-chain belt': '/tools/costume/items/item_137.jpg',
  'item-腰部 · 手部-背带-suspenders': '/tools/costume/items/item_138.jpg',
  'item-腰部 · 手部-绑带腰具-harness': '/tools/costume/items/item_139.jpg',
  'item-腰部 · 手部-手套-gloves': '/tools/costume/items/item_140.jpg',
  'item-腰部 · 手部-指虎手套-fingerless gloves': '/tools/costume/items/item_141.jpg',
  'item-腰部 · 手部-长手套-elbow gloves': '/tools/costume/items/item_142.jpg',
  'item-腰部 · 手部-袖套-detached sleeves': '/tools/costume/items/item_143.jpg',
  'item-腰部 · 手部-臂环-armlet': '/tools/costume/items/item_144.jpg',
  'item-腰部 · 手部-袖口花边-wrist cuffs': '/tools/costume/items/item_145.jpg',
  'item-腰部 · 手部-手链-bracelet': '/tools/costume/items/item_146.jpg',
  'item-腰部 · 手部-戒指-ring': '/tools/costume/items/item_147.jpg',
  'item-布艺 · 装饰-蕾丝-lace': '/tools/costume/items/item_148.jpg',
  'item-布艺 · 装饰-荷叶边-frills': '/tools/costume/items/item_149.jpg',
  'item-布艺 · 装饰-荷叶袖-ruffles, sleeves': '/tools/costume/items/item_150.jpg',
  'item-布艺 · 装饰-缎带-ribbon': '/tools/costume/items/item_151.jpg',
  'item-布艺 · 装饰-蝴蝶结-bow': '/tools/costume/items/item_152.jpg',
  'item-布艺 · 装饰-绗缝-quilted clothes': '/tools/costume/items/item_153.jpg',
  'item-布艺 · 装饰-绒球-pom pom (clothes)': '/tools/costume/items/item_154.jpg',
  'item-布艺 · 装饰-穗子-tassel': '/tools/costume/items/item_155.jpg',
  'item-布艺 · 装饰-刺绣-embroidery': '/tools/costume/items/item_156.jpg',
  'item-布艺 · 装饰-拼接-patchwork': '/tools/costume/items/item_157.jpg',
  'item-金属 · 宝石-链条-chains': '/tools/costume/items/item_158.jpg',
  'item-金属 · 宝石-铆钉-studs': '/tools/costume/items/item_159.jpg',
  'item-金属 · 宝石-宝石-jewelry': '/tools/costume/items/item_160.jpg',
  'item-金属 · 宝石-珍珠-pearls': '/tools/costume/items/item_161.jpg',
  'item-金属 · 宝石-金饰-gold, jewelry': '/tools/costume/items/item_162.jpg',
  'item-金属 · 宝石-银饰-silver, jewelry': '/tools/costume/items/item_163.jpg',
  'item-幻想 · 战斗-肩甲-pauldrons': '/tools/costume/items/item_164.jpg',
  'item-幻想 · 战斗-护腕-bracer': '/tools/costume/items/item_165.jpg',
  'item-幻想 · 战斗-披风-cloak': '/tools/costume/items/item_166.jpg',
  'item-幻想 · 战斗-腰带包-waist bag': '/tools/costume/items/item_167.jpg',
  'item-幻想 · 战斗-刀鞘-scabbard': '/tools/costume/items/item_168.jpg',
  'item-幻想 · 战斗-法杖-staff': '/tools/costume/items/item_169.jpg',
  'item-幻想 · 战斗-翅膀-wings': '/tools/costume/items/item_170.jpg',
  'item-幻想 · 战斗-尾巴-tail': '/tools/costume/items/item_171.jpg',
  'item-幻想 · 战斗-光环-halo': '/tools/costume/items/item_172.jpg',
  'item-季候 · 功能-书包-school bag': '/tools/costume/items/item_173.jpg',
  'item-季候 · 功能-单肩包-shoulder bag': '/tools/costume/items/item_174.jpg',
  'item-季候 · 功能-手提包-handbag': '/tools/costume/items/item_175.jpg',
  'item-季候 · 功能-雨伞-umbrella': '/tools/costume/items/item_176.jpg',
  'item-季候 · 功能-耳机-headphones': '/tools/costume/items/item_177.jpg',
  'item-季候 · 功能-手套围巾组合-mittens': '/tools/costume/items/item_178.jpg',
  'item-季候 · 功能-圣诞帽-santa hat': '/tools/costume/items/item_179.jpg',
  'item-季候 · 功能-祭典面具-fox mask': '/tools/costume/items/item_180.jpg',
  'item-季候 · 功能-眼镜链-eyewear strap': '/tools/costume/items/item_181.jpg',
  'item-材质 · 纹理-丝绒-velvet': '/tools/costume/items/item_182.jpg',
  'item-材质 · 纹理-缎面-satin': '/tools/costume/items/item_183.jpg',
  'item-材质 · 纹理-皮革-leather': '/tools/costume/items/item_184.jpg',
  'item-材质 · 纹理-牛仔-denim': '/tools/costume/items/item_185.jpg',
  'item-材质 · 纹理-丝绸-silk': '/tools/costume/items/item_186.jpg',
  'item-材质 · 纹理-羊毛-wool': '/tools/costume/items/item_187.jpg',
  'item-材质 · 纹理-网眼-mesh': '/tools/costume/items/item_188.jpg',
  'item-材质 · 纹理-漆皮-leather': '/tools/costume/items/item_189.jpg',
  'item-材质 · 纹理-羽绒-down jacket': '/tools/costume/items/item_190.jpg',
  'item-材质 · 纹理-亮片-sequins': '/tools/costume/items/item_191.jpg',
  'item-下装-高腰裙-high-waisted skirt': '/tools/costume/items/item_192.jpg',
  'item-鞋-帆布鞋-canvas shoes': '/tools/costume/items/item_193.jpg',
  'item-颈部 · 胸肩-吊坠项链-pendant necklace': '/tools/costume/items/item_194.jpg',
  'item-布艺 · 装饰-褶皱-pleats': '/tools/costume/items/item_195.jpg',
  'item-金属 · 宝石-金属扣-buckles': '/tools/costume/items/item_196.jpg',
  'item-金属 · 宝石-别针-safety pins': '/tools/costume/items/item_197.jpg',
}
const itemImgOk = reactive<Record<string, boolean>>({})
function itemImg(c: { key: string }): string {
  return ITEM_IMGS[c.key] || ''
}

const groups: CostumeGroup[] = [
  { group: '上装 · 内搭', sub: '衬衫 / 上衣', items: [
    { zh: '白衬衫', tag: 'white shirt', note: '基础打底，领口可松可扣', pair: '搭领结/背心/西装', risk: '' },
    { zh: '水手领衬衫', tag: 'sailor collar, shirt', note: '后领方形水手领片', pair: 'JK 必备，搭百褶裙', risk: '' },
    { zh: '彼得潘领', tag: 'peter pan collar', note: '圆角小翻领，幼态', pair: '搭开衫、连衣裙', risk: '' },
    { zh: '立领衬衫', tag: 'high collar, shirt', note: '中式/军装立领', pair: '搭马甲、中式外套', risk: '' },
    { zh: '高领衫', tag: 'turtleneck', note: '包住脖颈，秋冬', pair: '搭大衣、西装', risk: '' },
    { zh: 'V领上衣', tag: 'v-neck', note: '露出颈部线条的 V 领', pair: '搭领结/项链', risk: '' },
    { zh: '露肩衬衫', tag: 'off shoulder, shirt', note: '肩线敞开，露锁骨', pair: '搭细项链；春秋', risk: '肩部易崩，构图别裁肩' },
    { zh: '蕾丝衬衫', tag: 'lace, shirt', note: '透视蕾丝面料', pair: '内搭打底背心', risk: '蕾丝网眼过密易糊' },
    { zh: '泡泡袖衬衫', tag: 'puffy sleeves, shirt', note: '肩头鼓起，法式', pair: '搭高腰下装', risk: '袖山易画崩，写 puffy sleeves' },
    { zh: '荷叶边衬衫', tag: 'frilled shirt', note: '前襟一排荷叶边', pair: 'Lolita 内搭', risk: '' },
    { zh: '飘带衬衫', tag: 'ribbon, shirt', note: '领口系飘带', pair: '搭西装、背心裙', risk: '飘带细长易断' },
    { zh: '针织衫', tag: 'sweater', note: '套头针织，柔软', pair: '冬季日常', risk: '' },
    { zh: '针织开衫', tag: 'cardigan', note: '可长可短的开襟', pair: '学院/慵懒两用', risk: '' },
    { zh: '针织马甲', tag: 'sweater vest', note: '无袖套头，学院感', pair: '叠穿衬衫', risk: '' },
    { zh: '卫衣', tag: 'hoodie', note: '连帽，休闲', pair: '街头/运动混搭', risk: '帽子与头发易打架' },
    { zh: 'T恤', tag: 't-shirt', note: '基础圆领', pair: '短裤短裙日常', risk: '' },
    { zh: '条纹衫', tag: 'striped shirt', note: '横条纹基础款', pair: '搭纯色下装', risk: '' },
    { zh: '吊带背心', tag: 'camisole', note: '细肩带无袖', pair: '搭罩衫/开衫', risk: '' },
    { zh: '无袖背心', tag: 'tank top', note: '宽肩带运动款', pair: '搭短裤、工装裤', risk: '' },
    { zh: '制服衬衫', tag: 'dress shirt', note: '挺括正规', pair: '西装三件套', risk: '' },
  ] },
  { group: '上装 · 外搭', sub: '外套 / 西装 / 大衣', items: [
    { zh: '西装外套', tag: 'blazer', note: '结构感的翻领外套', pair: 'JK 西装/通勤', risk: '胸前纹章易乱入，negative 常驻 emblem' },
    { zh: '双排扣西装', tag: 'double-breasted jacket', note: '两列扣，正式', pair: '高腰下装显腰线', risk: '' },
    { zh: '西装马甲', tag: 'waistcoat', note: '三件套中层', pair: '搭衬衫领带', risk: '' },
    { zh: '皮夹克', tag: 'leather jacket', note: '机车感硬挺皮革', pair: '搭紧身下装、靴子', risk: '' },
    { zh: '牛仔夹克', tag: 'denim jacket', note: '短款休闲', pair: '搭连衣裙压甜', risk: '' },
    { zh: '飞行员夹克', tag: 'bomber jacket', note: '棒球领松紧口', pair: '街头混搭', risk: '' },
    { zh: '军装大衣', tag: 'peacoat', note: '双排扣毛呢，海军', pair: '冬季定剪影', risk: '' },
    { zh: '风衣', tag: 'trench coat', note: '系腰带长外套', pair: '搭高领内搭', risk: '腰带细，写 belt 即可' },
    { zh: '羊毛大衣', tag: 'winter coat', note: '厚实长款', pair: '围巾手套同色系', risk: '' },
    { zh: '斗篷', tag: 'cape', note: '无袖披挂，定剪影', pair: '幻想/贵族', risk: '手臂被遮，构图留手' },
    { zh: '短披肩', tag: 'capelet', note: '只盖到肩背', pair: 'Lolita/哥特', risk: '' },
    { zh: '连帽斗篷', tag: 'hooded cape', note: '带兜帽', pair: '魔法/旅人', risk: '兜帽压头发，写 hood down 或抬起' },
    { zh: '针织披肩', tag: 'shawl', note: '绕肩一搭', pair: '秋冬柔情', risk: '' },
    { zh: '羽织', tag: 'haori', note: '和风外披', pair: '搭和服、现代混搭', risk: '' },
    { zh: '实验室白袍', tag: 'labcoat', note: '长白袍', pair: '科研/反差萌', risk: '' },
  ] },
  { group: '连衣裙 · 连体', sub: '裙型 / 礼服 / 传统', items: [
    { zh: 'A字连衣裙', tag: 'a-line dress', note: '上窄下散，显比例', pair: '搭玛丽珍', risk: '' },
    { zh: '衬衫裙', tag: 'long shirt', note: '衬衫改良的连衣裙', pair: '腰带收腰', risk: '' },
    { zh: '背心裙', tag: 'suspender skirt', note: '无袖内搭连衣裙', pair: '搭衬衫打底', risk: '' },
    { zh: '针织连衣裙', tag: 'sweater dress', note: '贴身针织长裙', pair: '配长靴', risk: '贴身易糊，写 loose fit 慎用' },
    { zh: '吊带连衣裙', tag: 'sundress', note: '细吊带裙', pair: '夏天/内搭', risk: '' },
    { zh: '蛋糕裙', tag: 'frilled dress', note: '多层横向接缝', pair: '甜系/梦幻', risk: '' },
    { zh: '蓬蓬裙', tag: 'petticoat', note: '裙摆蓬起', pair: 'Lolita 内裙撑', risk: '' },
    { zh: '洛丽塔裙', tag: 'lolita fashion, dress', note: '蕾丝层叠主裙', pair: '配头饰+玛丽珍', risk: '裙撑勿太大，会压身体比例' },
    { zh: 'JSK 吊带洛丽塔', tag: 'suspender skirt, lolita fashion', note: '吊带款主裙', pair: '搭内衬 blouse', risk: '' },
    { zh: '晚礼服', tag: 'evening gown', note: '长摆正式裙', pair: '高跟+手套', risk: '' },
    { zh: '婚纱', tag: 'wedding dress', note: '白纱长裙', pair: '配头纱 veil', risk: '白上白细节易丢' },
    { zh: '旗袍', tag: 'china dress', note: '立领开叉曲线', pair: '配发簪/小包', risk: '刺绣细纹易崩' },
    { zh: '汉服', tag: 'hanfu, wide sleeves', note: '交领大袖传统裙', pair: '配披帛/发簪', risk: '花纹多写大图案' },
    { zh: '女仆装', tag: 'maid, apron', note: '长裙＋围裙＋头饰', pair: '黑白为主', risk: '细边饰易糊' },
    { zh: '护士服', tag: 'nurse, nurse cap', note: '白裙＋护士帽', pair: '白＋点缀色', risk: '' },
    { zh: '巫女服', tag: 'miko, hakama', note: '白衣红袴', pair: '袖口用 detached sleeves', risk: '' },
  ] },
  { group: '和服 · 长袍', sub: '日式 / 长袍', items: [
    { zh: '和服', tag: 'kimono', note: '直裁长衣＋腰带', pair: '配 obi、木屐', risk: '花纹写大图案' },
    { zh: '浴衣', tag: 'yukata', note: '夏季轻薄和服', pair: '配团扇、木屐', risk: '' },
    { zh: '振袖', tag: 'furisode', note: '未婚女性长袖', pair: '正式场合', risk: '' },
    { zh: '羽织袴', tag: 'hakama, haori', note: '武士/毕业式装束', pair: '配袴裙', risk: '' },
    { zh: '甚平', tag: 'jinbei', note: '夏日家居套装', pair: '祭典日常', risk: '' },
    { zh: '作务衣', tag: 'japanese clothes', note: '职人工作装（无专 tag，写 japanese clothes）', pair: '和风现代混搭', risk: '' },
    { zh: '道袍', tag: 'robe', note: '宽袖中式长袍', pair: '修仙/道姑', risk: '' },
    { zh: '法袍', tag: 'robe', note: '法师/教士长袍', pair: '配兜帽', risk: '' },
  ] },
  { group: '下装', sub: '裙 / 裤', items: [
    { zh: '百褶裙', tag: 'pleated skirt', note: '细密斜褶，JK 标配', pair: '搭制服上装', risk: '褶数多会糊，写 pleated skirt 即可' },
    { zh: '刀褶裙', tag: 'pleated skirt', note: '一边倒的利落褶（同 tag，褶型靠参考图定）', pair: '学院/通勤', risk: '' },
    { zh: '迷你裙', tag: 'miniskirt', note: '膝上短裙', pair: '搭过膝袜露绝对领域', risk: '' },
    { zh: '背带裙', tag: 'suspender skirt', note: '带背带扣的裙', pair: '搭衬衫/毛衣', risk: '' },
    { zh: '高腰裙', tag: 'high-waisted skirt', note: '腰线上提', pair: '拉长腿部比例', risk: '' },
    { zh: '鱼尾裙', tag: 'long skirt', note: '下摆收窄再散', pair: '显身材曲线', risk: '' },
    { zh: '包臀裙', tag: 'pencil skirt', note: '窄身直筒', pair: '通勤/御姐', risk: '' },
    { zh: '牛仔短裤', tag: 'denim shorts', note: '休闲短裤', pair: 'T恤/背心', risk: '' },
    { zh: '百褶短裤', tag: 'pleated shorts', note: '裙感短裤，防走光', pair: '运动/学院', risk: '' },
    { zh: '工装裤', tag: 'cargo pants', note: '多口袋宽松裤', pair: '机能/街头', risk: '口袋多易糊，写 cargo pants 即可' },
    { zh: '西装长裤', tag: 'pants', note: '挺括直筒', pair: '西装上装', risk: '' },
    { zh: '连体裤', tag: 'jumpsuit', note: '一体式工装', pair: 'T恤打底', risk: '' },
    { zh: '背带裤', tag: 'overalls', note: '背带工装裤', pair: '休闲日常', risk: '' },
  ] },
  { group: '袜装 · 腿部', sub: '袜 / 绑带', items: [
    { zh: '短袜', tag: 'ankle socks', note: '到脚踝', pair: '乐福鞋/运动鞋', risk: '' },
    { zh: '中筒袜', tag: 'kneehighs', note: '到小腿中段', pair: '学院日常', risk: '' },
    { zh: '过膝袜', tag: 'over-kneehighs', note: '越膝盖，绝对领域', pair: '短裙', risk: '袜口位置易漂移，写 over-kneehighs' },
    { zh: '大腿袜', tag: 'thighhighs', note: '到大腿', pair: '短裙/热裤', risk: '' },
    { zh: '松垮袜', tag: 'loose socks', note: '堆叠在脚踝', pair: 'Y2K/辣妹', risk: '' },
    { zh: '条纹袜', tag: 'striped socks', note: '横条纹长袜', pair: '运动/学院', risk: '' },
    { zh: '连裤袜', tag: 'pantyhose', note: '半透丝袜质感', pair: '通勤/礼服', risk: '高光写好更真实' },
    { zh: '厚黑丝', tag: 'black pantyhose', note: '不透明厚袜', pair: '黑裙/制服', risk: '' },
    { zh: '网袜', tag: 'fishnet stockings', note: '网格透肉', pair: '朋克/暗黑', risk: '网格密易糊，降低密度' },
    { zh: '吊带袜', tag: 'garter belt, thighhighs', note: '腰带吊袜结构', pair: '哥特/礼服', risk: '细吊带易崩，绘粗带' },
    { zh: '腿环', tag: 'thigh strap', note: '大腿上的装饰带', pair: '短裙点睛', risk: '细环易丢，写 thigh strap 加粗' },
    { zh: '袜套', tag: 'leg warmers', note: '脚踝到小腿的套', pair: '运动/Y2K', risk: '' },
    { zh: '赤足裸腿', tag: 'bare legs', note: '不穿袜', pair: '夏日/居家', risk: '' },
  ] },
  { group: '鞋', sub: '鞋 / 靴', items: [
    { zh: '乐福鞋', tag: 'loafers', note: '学院皮鞋基础款', pair: 'JK 标配', risk: '' },
    { zh: '玛丽珍', tag: 'mary janes', note: '圆头搭扣小皮鞋', pair: 'Lolita/学院', risk: '' },
    { zh: '室内鞋', tag: 'uwabaki', note: '白布鞋', pair: '日本学校场景', risk: '' },
    { zh: '厚底鞋', tag: 'platform shoes', note: '鞋底加厚', pair: '地雷系/哥特', risk: '' },
    { zh: '高跟鞋', tag: 'high heels', note: '细高跟', pair: '礼服/御姐', risk: '脚踝易崩，构图别切脚' },
    { zh: '短靴', tag: 'ankle boots', note: '到脚踝的靴', pair: '秋冬百搭', risk: '' },
    { zh: '长靴', tag: 'knee boots', note: '过膝靴', pair: '搭短裙压气势', risk: '' },
    { zh: '系带长靴', tag: 'lace-up boots', note: '多排鞋带', pair: '哥特/军装', risk: '鞋带细节易糊，写 lace-up 即可' },
    { zh: '运动鞋', tag: 'sneakers', note: '球鞋', pair: '街头运动', risk: '' },
    { zh: '帆布鞋', tag: 'canvas shoes', note: '低帮布鞋', pair: '休闲日常', risk: '' },
    { zh: '凉鞋', tag: 'sandals', note: '露趾绑带', pair: '夏装', risk: '脚趾结构易崩' },
    { zh: '木屐', tag: 'geta', note: '日式咔哒木屐', pair: '浴衣/和服', risk: '' },
    { zh: '草履', tag: 'zouri', note: '和服正装鞋', pair: '着物', risk: '' },
    { zh: '足袋', tag: 'tabi', note: '分趾白袜', pair: '木屐/和服', risk: '' },
  ] },
  { group: '头部 · 发饰', sub: '发饰 / 帽', items: [
    { zh: '发带', tag: 'hairband', note: '箍在头顶的饰带', pair: '任何风格收干净感', risk: '' },
    { zh: '丝带发饰', tag: 'hair ribbon', note: '缎带蝴蝶结发饰', pair: 'Lolita/学院', risk: '' },
    { zh: '大蝴蝶结', tag: 'hair bow', note: '夸张尺寸蝴蝶结', pair: '量产型/甜系', risk: '过大压头，注意比例' },
    { zh: '发夹', tag: 'hairclip', note: '一字夹/小夹', pair: '侧发固定', risk: '' },
    { zh: '蕾丝发带', tag: 'lace headband', note: '花边发箍', pair: '女仆/Lolita', risk: '' },
    { zh: '发圈', tag: 'scrunchie', note: '大肠圈', pair: '日常少女', risk: '' },
    { zh: '花朵发饰', tag: 'hair flower', note: '头顶一朵花', pair: '夏天/度假', risk: '' },
    { zh: '发簪', tag: 'hair stick', note: '中式/日式簪子', pair: '汉服/和风', risk: '细簪易丢，写粗簪' },
    { zh: '兽耳发饰', tag: 'animal ears, hairband', note: '猫耳/狐耳', pair: '幻想/装饰性', risk: '' },
    { zh: '头纱', tag: 'veil', note: '薄纱罩头', pair: '婚礼/哥特', risk: '' },
    { zh: '贝雷帽', tag: 'beret', note: '法式圆帽', pair: '学院/艺术生', risk: '' },
    { zh: '报童帽', tag: 'newsboy cap', note: '八片帽', pair: '复古街头', risk: '' },
    { zh: '宽檐帽', tag: 'sun hat', note: '遮阳大檐', pair: '夏装/度假', risk: '帽檐遮脸，注意构图' },
    { zh: '女巫帽', tag: 'witch hat', note: '尖顶帽', pair: '魔法风', risk: '' },
    { zh: '护士帽', tag: 'nurse cap', note: '小方白帽', pair: '护士装', risk: '' },
    { zh: '空乘帽', tag: 'pillbox hat', note: '小圆筒帽', pair: '制服风', risk: '' },
  ] },
  { group: '面部 · 耳部', sub: '眼镜 / 耳饰', items: [
    { zh: '眼镜', tag: 'glasses', note: '圆框/方框', pair: '学者感或反差萌', risk: '镜片反光留给光影' },
    { zh: '墨镜', tag: 'sunglasses', note: '遮眼', pair: '帅感/街头', risk: '遮眼会丢眼神，慎用' },
    { zh: '单片眼镜', tag: 'monocle', note: '单片复古', pair: '贵族/蒸汽朋克', risk: '' },
    { zh: '眼罩', tag: 'eyepatch', note: '遮单眼', pair: '战斗/神秘', risk: '' },
    { zh: '耳钉', tag: 'earrings', note: '小颗粒', pair: '精致点缀', risk: '' },
    { zh: '耳环', tag: 'hoop earrings', note: '环状', pair: '街头/辣妹', risk: '' },
    { zh: '耳坠', tag: 'tassel earrings', note: '垂坠款', pair: '礼服', risk: '细碎易糊，写粗坠' },
    { zh: '口罩', tag: 'mask', note: '遮下半脸', pair: '病弱/神秘', risk: '' },
    { zh: '唇彩', tag: 'lipstick', note: '亮面唇', pair: '成人感', risk: '' },
    { zh: '腮红', tag: 'blush', note: '脸颊红晕', pair: '可爱/害羞', risk: '' },
  ] },
  { group: '颈部 · 胸肩', sub: '项饰 / 胸饰 / 肩饰', items: [
    { zh: '项圈', tag: 'choker', note: '贴颈细带', pair: '甜酷/暗黑', risk: '细带易丢，加粗或加吊坠' },
    { zh: '丝带颈饰', tag: 'ribbon choker', note: '系带式', pair: '女仆/Lolita', risk: '' },
    { zh: '十字架项链', tag: 'cross necklace', note: '宗教符号吊坠', pair: '哥特/地雷系', risk: '' },
    { zh: '吊坠项链', tag: 'pendant necklace', note: '单颗吊坠', pair: '礼服/日常', risk: '细链易糊，写粗链' },
    { zh: '珍珠项链', tag: 'pearl necklace', note: '整串珍珠', pair: '古典优雅', risk: '珍珠颗粒过小易糊' },
    { zh: '领结', tag: 'bowtie', note: '蝴蝶结领', pair: '西装/学院', risk: '' },
    { zh: '领带', tag: 'necktie', note: '细长领带', pair: '制服/通勤', risk: '' },
    { zh: '领巾', tag: 'neckerchief', note: '三角巾', pair: '学院/水手风', risk: '' },
    { zh: '围巾', tag: 'scarf', note: '颈部长巾', pair: '冬装点睛色', risk: '尾端易乱飘' },
    { zh: '胸针', tag: 'brooch', note: '胸前装饰别针', pair: '贵族/制服', risk: '' },
    { zh: '肩章', tag: 'epaulettes', note: '肩上章片', pair: '军装', risk: '' },
    { zh: '肩上搭外套', tag: 'jacket on shoulders', note: '外套披肩式穿法', pair: '气势登场', risk: '结构易崩，写清楚' },
  ] },
  { group: '腰部 · 手部', sub: '腰带 / 手套 / 袖', items: [
    { zh: '腰带', tag: 'belt', note: '普通皮带', pair: '收腰', risk: '' },
    { zh: '腰封', tag: 'corset', note: '宽腰束形', pair: '哥特/礼服', risk: '' },
    { zh: '蝴蝶结腰带', tag: 'belt bow', note: '背后/侧面系蝴蝶结', pair: '甜系', risk: '' },
    { zh: '链条腰带', tag: 'chain belt', note: '金属链垂坠', pair: '街头/暗黑', risk: '' },
    { zh: '背带', tag: 'suspenders', note: '双肩背带', pair: '中性/复古', risk: '' },
    { zh: '绑带腰具', tag: 'harness', note: '机能风绑带', pair: '机能/战斗', risk: '复杂系带易崩，降级粗带' },
    { zh: '手套', tag: 'gloves', note: '全指', pair: '礼服/战斗', risk: '' },
    { zh: '指虎手套', tag: 'fingerless gloves', note: '半指', pair: '街头/战斗', risk: '' },
    { zh: '长手套', tag: 'elbow gloves', note: '过肘长套', pair: '礼服/贵妇', risk: '' },
    { zh: '袖套', tag: 'detached sleeves', note: '分离式袖', pair: '和风/幻想', risk: '结构常崩，写 detached sleeves' },
    { zh: '臂环', tag: 'armlet', note: '上臂装饰环', pair: '异域/战斗', risk: '' },
    { zh: '袖口花边', tag: 'wrist cuffs', note: '袖口独立花边', pair: '女仆/Lolita', risk: '' },
    { zh: '手链', tag: 'bracelet', note: '腕部饰品', pair: '日常点缀', risk: '' },
    { zh: '戒指', tag: 'ring', note: '指上小件', pair: '细节特写用', risk: '手部特写易崩，少用' },
  ] },
  { group: '布艺 · 装饰', sub: '装饰元素', items: [
    { zh: '蕾丝', tag: 'lace', note: '镂空花边', pair: '任何甜/古典', risk: '纹样过密易糊' },
    { zh: '荷叶边', tag: 'frills', note: '层叠波浪边', pair: 'Lolita/女仆', risk: '' },
    { zh: '褶皱', tag: 'pleats', note: '规则褶', pair: '学院/通勤', risk: '' },
    { zh: '荷叶袖', tag: 'ruffles, sleeves', note: '袖口大波浪', pair: '甜系', risk: '' },
    { zh: '缎带', tag: 'ribbon', note: '丝缎长条', pair: '点缀色利器', risk: '' },
    { zh: '蝴蝶结', tag: 'bow', note: '通用蝴蝶结', pair: '全风格通用', risk: '' },
    { zh: '绗缝', tag: 'quilted clothes', note: '格子压线', pair: '秋冬质感', risk: '' },
    { zh: '绒球', tag: 'pom pom (clothes)', note: '毛球装饰', pair: '冬季可爱', risk: '' },
    { zh: '穗子', tag: 'tassel', note: '流苏坠', pair: '中式/和风', risk: '' },
    { zh: '刺绣', tag: 'embroidery', note: '布面绣花', pair: '民族/传统', risk: '细密刺绣易崩' },
    { zh: '拼接', tag: 'patchwork', note: '异材质拼块', pair: '潮流/机能', risk: '' },
  ] },
  { group: '金属 · 宝石', sub: '材质配件', items: [
    { zh: '金属扣', tag: 'buckles', note: '皮带/鞋扣', pair: '机能/军装', risk: '' },
    { zh: '链条', tag: 'chains', note: '垂挂金属链', pair: '暗黑/街头', risk: '细链必崩，写粗链' },
    { zh: '铆钉', tag: 'studs', note: '金属颗粒', pair: '朋克', risk: '密集颗粒易糊' },
    { zh: '别针', tag: 'safety pins', note: '安全别针装饰', pair: '朋克', risk: '' },
    { zh: '宝石', tag: 'jewelry', note: '镶嵌宝石', pair: '贵族/魔法', risk: '' },
    { zh: '珍珠', tag: 'pearls', note: '珍珠元素', pair: '古典优雅', risk: '' },
    { zh: '金饰', tag: 'gold, jewelry', note: '金色饰品', pair: '暖色点缀', risk: '' },
    { zh: '银饰', tag: 'silver, jewelry', note: '银色饰品', pair: '冷色点缀', risk: '' },
  ] },
  { group: '幻想 · 战斗', sub: '风格组件', items: [
    { zh: '肩甲', tag: 'pauldrons', note: '硬质护肩', pair: '骑士/战斗', risk: '结构复杂，写单侧' },
    { zh: '护腕', tag: 'bracer', note: '小臂护具', pair: '战斗风', risk: '' },
    { zh: '披风', tag: 'cloak', note: '长披挂', pair: '英雄登场', risk: '动态需风，构图留位' },
    { zh: '腰带包', tag: 'waist bag', note: '腰间小包', pair: '冒险/机能', risk: '' },
    { zh: '刀鞘', tag: 'scabbard', note: '佩刀鞘', pair: '武士/战斗', risk: '' },
    { zh: '法杖', tag: 'staff', note: '手持长杖', pair: '法师', risk: '武器结构长青描写' },
    { zh: '翅膀', tag: 'wings', note: '背生翼', pair: '天使/精灵', risk: '与头发打架，构图留背' },
    { zh: '尾巴', tag: 'tail', note: '兽尾', pair: '兽人/恶魔', risk: '' },
    { zh: '光环', tag: 'halo', note: '头顶光环', pair: '天使/圣洁', risk: '' },
  ] },
  { group: '季候 · 功能', sub: '小物 / 场景物', items: [
    { zh: '书包', tag: 'school bag', note: '双肩学生包', pair: '学院', risk: '' },
    { zh: '单肩包', tag: 'shoulder bag', note: '斜挎小包', pair: '日常/街头', risk: '' },
    { zh: '手提包', tag: 'handbag', note: '手提出行包', pair: '通勤/淑女', risk: '' },
    { zh: '雨伞', tag: 'umbrella', note: '和伞或折叠伞', pair: '雨天/和风', risk: '手柄与手部易崩' },
    { zh: '耳机', tag: 'headphones', note: '头戴式', pair: '音乐/街头', risk: '压在头发上注意层级' },
    { zh: '手套围巾组合', tag: 'mittens', note: '冬季保暖件', pair: '冬装', risk: '' },
    { zh: '圣诞帽', tag: 'santa hat', note: '红色尖帽', pair: '节日', risk: '' },
    { zh: '祭典面具', tag: 'fox mask', note: '狐面等', pair: '祭典/和风', risk: '' },
    { zh: '眼镜链', tag: 'eyewear strap', note: '镜腿挂链', pair: '复古知性', risk: '细链易崩' },
  ] },
  { group: '材质 · 纹理', sub: '面料 / 质感', items: [
    { zh: '丝绒', tag: 'velvet', note: '绒面吸光，低调华贵', pair: '哥特/礼服', risk: '' },
    { zh: '缎面', tag: 'satin', note: '强反光顺滑', pair: '礼服/正装', risk: '高光要留光影阶段' },
    { zh: '皮革', tag: 'leather', note: '硬挺微光', pair: '机车/朋克', risk: '' },
    { zh: '牛仔', tag: 'denim', note: '粗纹耐磨', pair: '休闲', risk: '' },
    { zh: '丝绸', tag: 'silk', note: '细腻光泽', pair: '古典', risk: '' },
    { zh: '羊毛', tag: 'wool', note: '厚实保暖', pair: '大衣', risk: '' },
    { zh: '网眼', tag: 'mesh', note: '透气网格', pair: '运动/机能', risk: '' },
    { zh: '漆皮', tag: 'leather', note: '强反光皮面', pair: '暗黑/未来', risk: '' },
    { zh: '羽绒', tag: 'down jacket', note: '膨膨绗缝', pair: '冬季日常', risk: '' },
    { zh: '亮片', tag: 'sequins', note: '金属光片，自带闪光点', pair: '舞台/辣妹/夜店', risk: '密集亮片易糊，写局部' },
  ] },
]

const howtos: Howto[] = [
  { h: '① 选型句（穿什么）', p: '从本表挑到叶节点，记录中文路径，例如：<code>上装-外搭-西装-学院西装</code>。选型单先给用户拍板，定了再定样。', pre: 'white shirt, black ribbon tie, navy blazer, pleated skirt' },
  { h: '② 定样句（什么颜色材质）', p: '主色定最大面积、点缀色抓眼（配色查配色工具）。同一句里颜色词紧贴单品词，模型会绑色。', pre: 'black pleated skirt, crisp white shirt, wine red ribbon tie' },
  { h: '③ 指向句（定版唯一手段）', p: '服装有参考图/已冻结时，禁止重写细节，只写指向句，让模型照抄参考图。', pre: 'wear the exact outfit shown in the outfit reference image, keep every garment identical, do not redesign' },
  { h: '④ 层级顺序（从内到外）', p: '验证顺序＝身体 → 内搭 → 外搭 → 配饰固定层；外套先定剪影，再决定内搭露多少。', pre: 'body → inner layer → outer layer → accessory layer' },
  { h: '⑤ 铁律', p: '件数≤2 件加饰、signature 唯一；细链条/小字/多小物难生成，复杂系带降级粗带；文字与 Logo 一律不写；大面积布料留白，忌全身开花。', pre: '' },
  { h: '⑥ negative 常驻', p: '校徽纹章与文字是底模顽固行为，常驻负面；有红色配饰时眼色写死。', pre: 'emblem, crest, badge, text, logo, watermark, extra fingers, bad hands, redesigned outfit, different clothes in panels' },
]

const ANCHOR_SENTENCE = 'same character as the reference image, identical face shape, hairstyle, hair color, outfit and accessories, keep character identity fully consistent'
const POINT_SENTENCE = 'wear the exact outfit shown in the outfit reference image, keep every garment identical, do not redesign'

const query: Ref<string> = ref('')
const activeCat = ref<string>('全部')
const activeStyle: Ref<StylePack | null> = ref(null)
const openKey: Ref<string | null> = ref(null)
const TRAY_LS = 'suli-costume-tray'
let trayInit = true
try { trayInit = localStorage.getItem(TRAY_LS) !== '0' } catch {}
const trayOpen: Ref<boolean> = ref(trayInit)
function toggleTray(): void {
  trayOpen.value = !trayOpen.value
  try { localStorage.setItem(TRAY_LS, trayOpen.value ? '1' : '0') } catch {}
}

const slots: Ref<Slot[]> = ref([
  { k: '上装', v: [] },
  { k: '下装', v: [] },
  { k: '袜', v: [] },
  { k: '鞋', v: [] },
  { k: '配饰', v: [] },
])

function slotOf(group: string): string {
  if (/上装|连体|和服/.test(group)) return '上装'
  if (/下装/.test(group)) return '下装'
  if (/袜装/.test(group)) return '袜'
  if (group === '鞋') return '鞋'
  return '配饰'
}

function displayGroup(group: string): string {
  return group.replace(' · ', ' / ')
}

const isEmpty = computed<boolean>(
  () => !activeStyle.value && !slots.value.some((s) => s.v.length > 0),
)

const outfitPrompt = computed<string>(() => {
  const parts: string[] = []
  if (activeStyle.value) parts.push(...activeStyle.value.tags)
  slots.value.forEach((s) => s.v.forEach((c) => parts.push(c.tag)))
  return parts.join(', ')
})

const cats = computed<string[]>(() => {
  const arr: string[] = ['全部', '风格包']
  for (const g of groups) arr.push(g.group)
  arr.push('描述法')
  return arr
})

const allCards = computed<CardItem[]>(() => {
  const arr: CardItem[] = []
  styles.forEach((s, i) => {
    arr.push({
      key: 'style-' + i, kind: 'style', zh: s.zh, en: s.en, cat: '风格包',
      tag: s.tags.join(', '), summary: s.desc, pair: s.pair, risk: s.risk,
      pre: '', html: '', cover: s.zh.slice(0, 1),
      picked: activeStyle.value !== null && activeStyle.value.zh === s.zh,
      group: '', styleIdx: i, itemRef: null, styleRef: s,
    })
  })
  for (const g of groups) {
    for (const it of g.items) {
      const slot = slots.value.find((x) => x.k === slotOf(g.group))
      arr.push({
        key: 'item-' + g.group + '-' + it.zh + '-' + it.tag, kind: 'item',
        zh: it.zh, en: it.tag, cat: g.group, tag: it.tag,
        summary: it.note, pair: it.pair, risk: it.risk,
        pre: '', html: '', cover: it.zh.slice(0, 1),
        picked: slot ? slot.v.some((x) => x.tag === it.tag) : false,
        group: g.group, styleIdx: -1, itemRef: it, styleRef: null,
      })
    }
  }
  howtos.forEach((h, i) => {
    arr.push({
      key: 'howto-' + i, kind: 'howto', zh: h.h, en: 'how to describe',
      cat: '描述法', tag: '', summary: h.pre || '描述法', pair: '', risk: '',
      pre: h.pre, html: h.p, cover: h.h.replace(/^[①②③④⑤⑥\s]*/, '').slice(0, 1),
      picked: false, group: '', styleIdx: -1, itemRef: null, styleRef: null,
    })
  })
  return arr
})

const filtered = computed<CardItem[]>(() => {
  const q = query.value.trim().toLowerCase()
  return allCards.value.filter((c) => {
    if (activeCat.value !== '全部' && c.cat !== activeCat.value) return false
    if (!q) return true
    return (c.zh + ' ' + c.en + ' ' + c.cat + ' ' + c.tag + ' ' + c.summary + ' ' + c.pair + ' ' + c.risk + ' ' + c.pre).toLowerCase().includes(q)
  })
})

function clearFilter(): void {
  query.value = ''
  activeCat.value = '全部'
}

function shortTag(t: string): string {
  return t.length > 26 ? t.slice(0, 26) + '…' : t
}

function copyOne(t: string): void {
  copyText(t)
}

function isOpen(key: string): boolean {
  return openKey.value === key
}

function toggleDetail(key: string): void {
  openKey.value = openKey.value === key ? null : key
}

function copyDetail(c: CardItem): void {
  if (c.tag) copyText(c.tag)
}

function pickDetail(c: CardItem): void {
  if (c.kind === 'style' && c.styleRef) {
    onStyleClick(c.styleRef)
    return
  }
  if (c.kind === 'item' && c.itemRef) {
    onItemClick(c.group, c.itemRef)
  }
}

function onItemClick(group: string, item: CostumeItem): void {
  copyText(item.tag)
  const slot = slots.value.find((s) => s.k === slotOf(group))
  if (!slot) return
  const i = slot.v.findIndex((x) => x.tag === item.tag)
  if (i >= 0) slot.v.splice(i, 1)
  else slot.v.push(item)
}

function onStyleClick(s: StylePack): void {
  copyText(s.tags.join(', '))
  activeStyle.value = activeStyle.value && activeStyle.value.zh === s.zh ? null : s
}

function removeFromSlot(k: string, i: number): void {
  const slot = slots.value.find((s) => s.k === k)
  if (slot) slot.v.splice(i, 1)
}

function onCopyOutfit(): void {
  const s = outfitPrompt.value
  if (!s) {
    ElMessage.warning('搭配台是空的，先点卡片')
    return
  }
  copyText(s)
}

function onCopyPoint(): void {
  copyText(ANCHOR_SENTENCE + ', ' + POINT_SENTENCE)
}

function onClearAll(): void {
  activeStyle.value = null
  slots.value.forEach((s) => { s.v.length = 0 })
}
</script>

<style scoped>
:root {
  --suli-primary: #FB7299;
}
.costume-tool {
  --suli-primary: #FB7299;
  background: #fff;
  border-radius: 12px;
  padding: 16px;
}
.tray {
  position: sticky;
  top: 0;
  z-index: 20;
  background: #fff;
  border: 1px solid var(--suli-border);
  border-radius: 10px;
  padding: 10px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.tray-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.tray-row + .tray-row {
  margin-top: 8px;
}
.tray-label {
  font-size: 12.5px;
  color: var(--suli-text-2);
  white-space: nowrap;
}
.tray-slots {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 120px;
}
.tray-search {
  width: 220px;
  max-width: 100%;
}
.tray-empty {
  font-size: 12.5px;
}
.mono-tag,
.mono,
.tag {
  font-family: Consolas, monospace;
}
.chip {
  cursor: pointer;
}
.count {
  font-size: 12.5px;
  margin-left: auto;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
  margin-top: 12px;
}
.tool-card {
  cursor: pointer;
  padding: 12px 12px 13px;
  transition: transform 0.08s, box-shadow 0.08s, border-color 0.08s;
}
.tool-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(251, 114, 153, 0.22);
  border-color: var(--suli-primary);
}
.tool-card.picked {
  border-color: var(--suli-primary);
  box-shadow: 0 0 0 2px rgba(251, 114, 153, 0.35);
}
.tool-card.open {
  border-color: var(--suli-primary, #FB7299);
}
.detail-block {
  margin-top: 10px;
  border-top: 1px dashed var(--suli-border);
  padding-top: 10px;
}
.detail-cols {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 16px;
  align-items: start;
}
@media (max-width: 640px) {
  .detail-cols {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
}
.detail-actions {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.cover {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #FB7299, #f9a8c0);
  margin-bottom: 8px;
  overflow: hidden;
  flex: none;
}
.cover img { width: 100%; height: 100%; object-fit: cover; }
.style-photo { margin: -2px -2px 8px; border-radius: 10px; overflow: hidden; aspect-ratio: 16/10; background: var(--suli-bg-2, #f4f4f5); }
.style-photo img { width: 100%; height: 100%; object-fit: cover; display: block; }
.en.muted {
  font-size: 12px;
  color: var(--suli-text-2);
  font-family: Consolas, monospace;
  word-break: break-word;
}
.empty {
  margin: 18px 2px;
  font-size: 13px;
}
.dlg-cover {
  width: 100%;
  aspect-ratio: 3 / 4;
  max-height: 54vh;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 64px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #FB7299, #f9a8c0);
  margin-bottom: 10px;
  overflow: hidden;
  flex: none;
}
.dlg-cover img { width: 100%; height: 100%; object-fit: cover; display: block; }
.dlg-tags {
  margin: 8px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.dlg-tags .mono-tag {
  cursor: pointer;
}
.dlg-note {
  font-size: 13.5px;
  line-height: 1.8;
  color: var(--suli-text);
  margin: 8px 0;
}
.dlg-html {
  font-size: 13px;
  line-height: 1.85;
  color: var(--suli-text-2);
}
.zh {
  font-size: 14.5px;
  font-weight: 600;
  color: var(--suli-text);
}
.tag {
  font-size: 12.5px;
  color: #b4553c;
  margin-top: 3px;
  word-break: break-word;
}
.note {
  font-size: 12.5px;
  margin-top: 5px;
  line-height: 1.55;
}
.pair {
  font-size: 12px;
  margin-top: 4px;
  line-height: 1.5;
}
.risk {
  display: inline-block;
  font-size: 11px;
  color: #a3423c;
  background: #fbeeea;
  border-radius: 4px;
  padding: 1px 6px;
  margin-top: 6px;
}
.tag-list {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.howto {
  padding: 16px 18px;
}
.howto h3 {
  font-size: 15px;
  color: var(--suli-text);
  margin: 14px 0 6px;
}
.howto h3:first-child {
  margin-top: 0;
}
.howto p {
  font-size: 13.5px;
  color: var(--suli-text-2);
  line-height: 1.85;
  margin: 0;
}
.howto pre {
  background: #f4f2ee;
  border: 1px solid var(--suli-border);
  color: var(--suli-text);
  border-radius: 8px;
  padding: 12px 14px;
  margin: 8px 0;
  font-size: 12.5px;
  line-height: 1.7;
  overflow-x: auto;
  white-space: pre-wrap;
}
.foot {
  margin: 24px 0 0;
  font-size: 12.5px;
  line-height: 1.8;
}

@container (max-width: 620px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
  .detail-cols { grid-template-columns: 1fr; }
}
@container (max-width: 400px) {
  .grid { grid-template-columns: 1fr; }
}
/* pack-slots: backpack face */
.tool-card > .tag-list, .tool-card > .note { display: none; }
.tool-card > .zh, .tool-card > .en { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tool-card.open { box-shadow: 0 0 0 2px rgba(251,114,153,.45), 0 8px 20px rgba(251,114,153,.25); }</style>
