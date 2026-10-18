<template>
  <div class="palette-tool">
    <div class="tray">
      <div class="tray-row">
        <el-input v-model="query" clearable placeholder="搜索" class="search" />
        <span class="suli-muted count">{{ filtered.length }} / {{ totalColors }}</span>
        <el-button size="small" @click="clearFilter">清空</el-button>
        <el-button size="small" text @click="toggleTray">{{ trayOpen ? '收起 ▲' : '展开 ▼' }}</el-button>
      </div>
      <template v-if="trayOpen">
      <div class="tray-row">
        <el-tag
          v-for="f in families"
          :key="f"
          :effect="active === f ? 'dark' : 'plain'"
          :type="active === f ? 'primary' : 'info'"
          class="chip-tag"
          @click="setActive(f)"
        >{{ f }}</el-tag>
      </div>
      <div class="tray-row combo">
        <span class="tray-label">组合:</span>
        <div class="picked">
          <span v-if="picked.length === 0" class="suli-muted empty-hint">暂无</span>
          <span v-for="(c, i) in picked" :key="c.en" class="chip">
            <i :style="{ background: c.hex }" />
            <b>{{ c.en }}</b>
            <span class="chip-x" @click.stop="removeAt(i)">&#215;</span>
          </span>
        </div>
        <el-button type="primary" size="small" @click="copyAll">复制组合prompt</el-button>
        <el-button size="small" @click="clearAll">清空组合</el-button>
      </div>
      </template>
    </div>

    <div class="grid">
      <div
        v-for="c in filtered"
        :key="c.en"
        class="suli-card tool-card card"
        :class="{ open: isOpen(c.en) }"
        @click="toggleDetail(c.en)"
      >
        <div class="cover" :style="{ background: c.hex }">
          <el-tag size="small" class="fam-chip">{{ c.family }}</el-tag>
        </div>
        <div class="meta">
          <div class="title"><span class="zh">{{ c.zh }}</span><span class="en">{{ c.en }}</span></div>
          <div class="pills"><span class="mono pill">{{ c.hex }}</span><span class="pill ghost">{{ c.familyEn }}</span></div>
          <div class="sum suli-muted">{{ c.tip }}</div>
        </div>
        <el-dialog append-to-body :model-value="isOpen(c.en)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
          <div class="detail-block">
          <div class="detail-cols">
            <div class="dlg-sw" :style="{ background: c.hex }" />
            <div class="dlg-rows">
              <div>中文名：{{ c.zh }}</div>
              <div>英文名：<span class="mono">{{ c.en }}</span></div>
              <div>色值：<span class="mono">{{ c.hex }}</span></div>
              <div>分类：{{ c.family }}（<span class="mono">{{ c.familyEn }}</span>）</div>
              <div class="suli-muted">{{ c.tip }}</div>
              <pre class="suli-pre">{{ c.en }} color palette</pre>
            </div>
          </div>
          <div class="dlg-bar">
            <el-button size="small" @click.stop="copyHex(c)">复制hex</el-button>
            <el-button size="small" @click.stop="copyEn(c)">复制英文名</el-button>
            <el-button size="small" type="primary" @click.stop="addColor(c)">加入组合</el-button>
            <el-button size="small" @click.stop="openKey = null">收起</el-button>
          </div>
        </div>
        </el-dialog>
      </div>
    </div>

    <p v-if="filtered.length === 0" class="suli-muted empty">没有匹配的颜色，换个关键词或点「清空」放宽筛选。</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { copyText } from '../../utils/clipboard'

interface PaletteColor {
  zh: string
  en: string
  hex: string
}

interface PaletteFamily {
  family: string
  en: string
  tip: string
  colors: PaletteColor[]
}

const DATA: PaletteFamily[] = [{"family": "红系","en": "reds","tip": "大面积红用深红系收敛，点缀用亮红；crimson 偏蓝红、vermilion 偏橘红。","colors": [{"zh": "大红","en": "true red","hex": "#FF0000"},{"zh": "朱红","en": "vermilion","hex": "#E34234"},{"zh": "绯红","en": "scarlet","hex": "#FF2400"},{"zh": "深红","en": "crimson","hex": "#DC143C"},{"zh": "酒红","en": "burgundy","hex": "#800020"},{"zh": "砖红","en": "brick red","hex": "#CB4154"},{"zh": "日落红","en": "sunset red","hex": "#FD5E53"},{"zh": "樱桃红","en": "cherry red","hex": "#DE3163"},{"zh": "红发","en": "red hair","hex": "#B93A32"},{"zh": "葡萄酒红","en": "wine red","hex": "#722F37"},{"zh": "宝石红","en": "ruby red","hex": "#9B111E"},{"zh": "牛血红","en": "oxblood","hex": "#4A0000"},{"zh": "玫瑰红","en": "rose red","hex": "#C21E56"},{"zh": "覆盆子红","en": "raspberry","hex": "#E30B5D"},{"zh": "番茄红","en": "tomato red","hex": "#FF6347"},{"zh": "胭脂红","en": "carmine","hex": "#960018"},{"zh": "火光红","en": "firebrick red","hex": "#B22222"},{"zh": "蘇芳","en": "suoh","hex": "#8E354A"},{"zh": "退紅","en": "taikoh","hex": "#F8C3CD"},{"zh": "一斥染","en": "ikkonzome","hex": "#F4A7B9"},{"zh": "桑染","en": "mulberry","hex": "#64363C"},{"zh": "苺","en": "ichigo","hex": "#B5495B"},{"zh": "薄紅","en": "pale crimson","hex": "#E87A90"},{"zh": "今様","en": "imayoh","hex": "#D05A6E"},{"zh": "中紅","en": "medium crimson","hex": "#DB4D6D"},{"zh": "梅鼠","en": "plum blossom gray","hex": "#9E7A7A"},{"zh": "燕脂","en": "enji","hex": "#9F353A"},{"zh": "紅","en": "crimson red","hex": "#CB1B45"},{"zh": "鴇","en": "toki","hex": "#EEA9A9"},{"zh": "長春","en": "cyohsyun","hex": "#BF6766"},{"zh": "深緋","en": "deep scarlet","hex": "#86473F"},{"zh": "桜鼠","en": "cherry blossom gray","hex": "#B19693"},{"zh": "甚三紅","en": "jinzamomi","hex": "#EB7A77"},{"zh": "小豆","en": "azuki","hex": "#954A45"},{"zh": "蘇芳香","en": "suohkoh","hex": "#A96360"},{"zh": "赤紅","en": "akabeni","hex": "#CB4042"},{"zh": "真朱","en": "shinsyu","hex": "#AB3B3A"},{"zh": "栗梅","en": "kuriume","hex": "#904840"},{"zh": "銀朱","en": "ginsyu","hex": "#C73E3A"},{"zh": "紅鳶","en": "benitobi","hex": "#994639"},{"zh": "曙","en": "akebono","hex": "#F19483"},{"zh": "紅樺","en": "benikaba","hex": "#B54434"},{"zh": "珊瑚朱","en": "sangosyu","hex": "#F17C67"},{"zh": "猩猩緋","en": "syojyohi","hex": "#E83015"},{"zh": "鉛丹","en": "entan","hex": "#D75455"},{"zh": "芝翫茶","en": "shikancha","hex": "#B55D4C"},{"zh": "似紫","en": "nisemurasaki","hex": "#562E37"},{"zh": "紫鳶","en": "murasakitobi","hex": "#60373E"},{"zh": "虹色","en": "nijiiro","hex": "#F6BFBC"},{"zh": "珊瑚","en": "sangoiro","hex": "#F5B1AA"},{"zh": "水柿","en": "mizugakiiro","hex": "#E4AB9B"},{"zh": "鴇浅葱","en": "tokiasagi","hex": "#B88884"},{"zh": "赤茶","en": "akacha","hex": "#BB5535"},{"zh": "浅蘇芳","en": "asasuou","hex": "#A25768"},{"zh": "煉瓦","en": "rengairo","hex": "#B55233"},{"zh": "薔薇","en": "barairo","hex": "#E9546B"},{"zh": "韓紅","en": "karakurenaiiro","hex": "#E95464"},{"zh": "赤","en": "aka","hex": "#E60033"},{"zh": "赤錆","en": "akasabiiro","hex": "#8A3319"},{"zh": "猩々緋","en": "shoujouhi","hex": "#E2041B"},{"zh": "緋色","en": "hiiro","hex": "#D3381C"},{"zh": "赤丹","en": "akani","hex": "#CE5242"},{"zh": "紅赤","en": "beniaka","hex": "#D9333F"},{"zh": "臙脂","en": "enjiiro","hex": "#B94047"},{"zh": "朱緋","en": "ake","hex": "#BA2636"},{"zh": "錆色","en": "sabiiro","hex": "#6C3524"},{"zh": "茜色","en": "akaneiro","hex": "#B7282E"},{"zh": "紅海老茶","en": "beniebicha","hex": "#A73836"},{"zh": "真紅／濃紅","en": "shinku","hex": "#A22041"},{"zh": "丹色","en": "niiro","hex": "#E45E32"},{"zh": "東雲","en": "shinonomeiro","hex": "#F19072"},{"zh": "浅緋","en": "usukihi","hex": "#DF7163"},{"zh": "真赭","en": "masoho","hex": "#D57C6B"},{"zh": "赭","en": "soho","hex": "#AB6953"},{"zh": "糖果红","en": "candy red","hex": "#FF355E"},{"zh": "熔岩红","en": "lava red","hex": "#CF1020"},{"zh": "玫瑰木红","en": "rosewood","hex": "#65000B"},{"zh": "石榴红","en": "pomegranate red","hex": "#C0392B"},{"zh": "蔓越莓红","en": "cranberry red","hex": "#9E1B32"},{"zh": "淡红","en": "pastel red","hex": "#FF6961"},{"zh": "消防红","en": "fire engine red","hex": "#CE2029"}]},{"family": "粉系","en": "pinks","tip": "moe 系腮红、少女感、樱花场景主力；dusty rose 显高级不腻。","colors": [{"zh": "樱花粉","en": "sakura pink","hex": "#FFB7C5"},{"zh": "蜜桃粉","en": "peach pink","hex": "#FFCBA4"},{"zh": "粉红","en": "pink","hex": "#FFC0CB"},{"zh": "桃红","en": "hot pink","hex": "#FF69B4"},{"zh": "品红","en": "magenta","hex": "#FF00FF"},{"zh": "珊瑚粉","en": "coral pink","hex": "#F88379"},{"zh": "豆沙粉","en": "dusty rose","hex": "#D8A7B1"},{"zh": "裸粉","en": "nude pink","hex": "#E3BC9A"},{"zh": "婴儿粉","en": "baby pink","hex": "#F4C2C2"},{"zh": "棉花糖粉","en": "cotton candy pink","hex": "#FFBCD9"},{"zh": "玫瑰粉","en": "rose pink","hex": "#FF66CC"},{"zh": "鲑鱼粉","en": "salmon pink","hex": "#FF91A4"},{"zh": "芭比粉","en": "barbie pink","hex": "#E0218A"},{"zh": "西瓜粉","en": "watermelon pink","hex": "#FC6C85"},{"zh": "撫子","en": "nadeshiko","hex": "#DC9FB4"},{"zh": "紅梅","en": "kohbai","hex": "#E16B8C"},{"zh": "韓紅花","en": "karakurenai","hex": "#D0104C"},{"zh": "藤煤竹","en": "fujisusutake","hex": "#574C57"},{"zh": "紅藤","en": "red wisteria","hex": "#B481BB"},{"zh": "黒紅","en": "dark red","hex": "#3F2B36"},{"zh": "茄子紺","en": "nasukon","hex": "#572A3F"},{"zh": "葡萄鼠","en": "budohnezumi","hex": "#5E3D50"},{"zh": "鳩羽鼠","en": "hatobanezumi","hex": "#72636E"},{"zh": "杜若","en": "kakitsubata","hex": "#622954"},{"zh": "蒲葡","en": "ebizome","hex": "#6D2E5B"},{"zh": "牡丹","en": "botan","hex": "#C1328E"},{"zh": "梅紫","en": "plum purple","hex": "#A8497A"},{"zh": "躑躅","en": "tsutsuji","hex": "#E03C8A"},{"zh": "桜色","en": "sakurairo","hex": "#FEF4F4"},{"zh": "古代紫","en": "kodaimurasaki","hex": "#895B8A"},{"zh": "薄桜","en": "usuzakura","hex": "#FDEFF2"},{"zh": "鴇鼠","en": "tokinezu","hex": "#E4D2D8"},{"zh": "京紫","en": "kyoumurasaki","hex": "#9D5B8B"},{"zh": "若紫","en": "wakamurasaki","hex": "#BC64A4"},{"zh": "紅紫","en": "benimurasaki","hex": "#B44C97"},{"zh": "浅紫","en": "asamurasaki","hex": "#C4A3BF"},{"zh": "桃色","en": "momoiro","hex": "#F09199"},{"zh": "淡紅藤","en": "awabenifuji","hex": "#E6CDE3"},{"zh": "石竹","en": "sekichikuiro","hex": "#E5ABBE"},{"zh": "薄紅梅","en": "usukoubai","hex": "#E597B2"},{"zh": "桃花","en": "momohanairo","hex": "#E198B4"},{"zh": "濃色","en": "kokiiro","hex": "#634950"},{"zh": "赤紫","en": "akamurasaki","hex": "#EB6EA5"},{"zh": "暗紅","en": "ankoushoku","hex": "#74325C"},{"zh": "桑の実","en": "kuwanomiiro","hex": "#55295B"},{"zh": "泡泡糖粉","en": "bubblegum pink","hex": "#FFC1CC"},{"zh": "火烈鸟粉","en": "flamingo pink","hex": "#FC8EAC"},{"zh": "淡粉","en": "pastel pink","hex": "#FFD1DC"},{"zh": "霓虹粉","en": "neon pink","hex": "#FF6EC7"},{"zh": "玫瑰石英粉","en": "rose quartz","hex": "#F7CAC9"}]},{"family": "橙系","en": "oranges","tip": "黄昏、灯火、秋日主力；marigold 做点缀很出彩。","colors": [{"zh": "橙色","en": "orange","hex": "#FFA500"},{"zh": "柑橘橙","en": "tangerine","hex": "#F28500"},{"zh": "胡萝卜橙","en": "carrot orange","hex": "#ED9121"},{"zh": "珊瑚橙","en": "coral","hex": "#FF7F50"},{"zh": "南瓜橙","en": "pumpkin orange","hex": "#FF7518"},{"zh": "余烬橙","en": "ember orange","hex": "#E25822"},{"zh": "杏色","en": "apricot","hex": "#FBCEB1"},{"zh": "金盏花","en": "marigold","hex": "#EAA221"},{"zh": "姜橙发","en": "ginger orange","hex": "#C76B3F"},{"zh": "琥珀橙","en": "amber orange","hex": "#FFBF00"},{"zh": "焦橙","en": "burnt orange","hex": "#CC5500"},{"zh": "赤陶橙","en": "terracotta","hex": "#E2725B"},{"zh": "柿子橙","en": "persimmon orange","hex": "#EC5800"},{"zh": "蜜桃橙","en": "peach orange","hex": "#FFE5B4"},{"zh": "哈密瓜橙","en": "cantaloupe","hex": "#FFA62F"},{"zh": "落日橙","en": "sunset orange","hex": "#FF8C42"},{"zh": "灰桜","en": "haizakura","hex": "#D7C4BB"},{"zh": "柿渋","en": "kakishibu","hex": "#A35E47"},{"zh": "紅緋","en": "blood red","hex": "#F75C2F"},{"zh": "弁柄","en": "bengara","hex": "#9A5034"},{"zh": "照柿","en": "terigaki","hex": "#C46243"},{"zh": "江戸茶","en": "red brown","hex": "#AF5F3C"},{"zh": "洗朱","en": "araisyu","hex": "#FB966E"},{"zh": "唐茶","en": "karacha","hex": "#B47157"},{"zh": "ときがら茶","en": "tokigaracha","hex": "#DB8E71"},{"zh": "黄丹","en": "ohni","hex": "#F05E1C"},{"zh": "纁","en": "sohi","hex": "#ED784A"},{"zh": "遠州茶","en": "ensyucha","hex": "#CA7853"},{"zh": "樺茶","en": "kabacha","hex": "#B35C37"},{"zh": "赤香","en": "akakoh","hex": "#E3916E"},{"zh": "雀茶","en": "suzumecha","hex": "#8F5A3C"},{"zh": "宍","en": "shishi","hex": "#F0A986"},{"zh": "宗伝唐茶","en": "sodenkaracha","hex": "#A0674B"},{"zh": "樺","en": "kaba","hex": "#C1693C"},{"zh": "深支子","en": "kokikuchinashi","hex": "#FB9966"},{"zh": "代赭","en": "taisya","hex": "#A36336"},{"zh": "洗柿","en": "araigaki","hex": "#E79460"},{"zh": "赤朽葉","en": "akakuchiba","hex": "#C78550"},{"zh": "礪茶","en": "tonocha","hex": "#985F2A"},{"zh": "赤白橡","en": "akashirotsurubami","hex": "#E1A679"},{"zh": "萱草","en": "kanzo","hex": "#FC9F4D"},{"zh": "洒落柿","en": "sharegaki","hex": "#FFBA84"},{"zh": "紅鬱金","en": "beniukon","hex": "#E98B2A"},{"zh": "枇杷茶","en": "biwacha","hex": "#B17844"},{"zh": "丁子茶","en": "chojicha","hex": "#96632E"},{"zh": "琥珀","en": "kohaku","hex": "#CA7A2C"},{"zh": "薄柿","en": "usugaki","hex": "#ECB88A"},{"zh": "丁子染","en": "chojizome","hex": "#B07736"},{"zh": "柴染","en": "fushizome","hex": "#967249"},{"zh": "朽葉","en": "kuchiba","hex": "#E2943B"},{"zh": "金茶","en": "golden brown","hex": "#C7802D"},{"zh": "狐","en": "kitsune","hex": "#9B6E23"},{"zh": "薄香","en": "usukoh","hex": "#EBB471"},{"zh": "砥粉","en": "tonoko","hex": "#D7B98E"},{"zh": "黄土","en": "ohdo","hex": "#B68E55"},{"zh": "黄唐茶","en": "kigaracha","hex": "#C18A26"},{"zh": "白橡","en": "shirotsurubami","hex": "#DCB879"},{"zh": "飴色","en": "ameiro","hex": "#DEB068"},{"zh": "駱駝","en": "rakudairo","hex": "#BF794E"},{"zh": "土色","en": "tsuchiiro","hex": "#BC763C"},{"zh": "一斤染","en": "ikkonzomeiro","hex": "#F5B199"},{"zh": "土器","en": "kawarakeiro","hex": "#C37854"},{"zh": "柑子","en": "koujiiro","hex": "#F6AD49"},{"zh": "蜜柑","en": "mikaniro","hex": "#F08300"},{"zh": "柿色","en": "kakiiro","hex": "#ED6D3D"},{"zh": "黄赤／人参色","en": "kiaka","hex": "#EC6800"},{"zh": "蜂蜜","en": "hachimitsuiro","hex": "#FDDEA5"},{"zh": "肌色","en": "hadairo","hex": "#FCE2C4"},{"zh": "薄卵","en": "usutamagoiro","hex": "#FDE8D0"},{"zh": "雄黄","en": "yuuou","hex": "#F9C89B"},{"zh": "朱色","en": "shuiro","hex": "#EB6101"},{"zh": "小麦","en": "komugiiro","hex": "#E49E61"},{"zh": "黄茶","en": "kicha","hex": "#E17B34"},{"zh": "肉色／人色","en": "nikuiro","hex": "#F1BF99"},{"zh": "肉桂","en": "nikkeiiro","hex": "#DD7A56"},{"zh": "香色／丁子色","en": "kouiro","hex": "#EFCD9A"},{"zh": "枯色","en": "kareiro","hex": "#E0C38C"},{"zh": "淡香","en": "usukou","hex": "#F3BF88"},{"zh": "赤橙／金赤","en": "akadaidai","hex": "#EA5506"},{"zh": "淡橙","en": "pastel orange","hex": "#FFB347"},{"zh": "霓虹橙","en": "neon orange","hex": "#FF5F1F"},{"zh": "桃肤橙","en": "peach puff","hex": "#FFDAB9"},{"zh": "血橙","en": "blood orange","hex": "#D93A25"}]},{"family": "黄系","en": "yellows","tip": "灯光、夏日、金发常用；大面积黄易脏，多用 cream / beige 打底。","colors": [{"zh": "柠檬黄","en": "lemon yellow","hex": "#FFF44F"},{"zh": "鹅黄","en": "pale yellow","hex": "#FFF38C"},{"zh": "明黄","en": "bright yellow","hex": "#FFEB00"},{"zh": "金黄","en": "golden yellow","hex": "#FFDF00"},{"zh": "芥末黄","en": "mustard","hex": "#E1AD01"},{"zh": "奶油黄","en": "cream","hex": "#FFFDD0"},{"zh": "米黄","en": "beige","hex": "#F5F5DC"},{"zh": "土黄","en": "ochre","hex": "#CC7722"},{"zh": "金发","en": "golden blonde","hex": "#E6BE4B"},{"zh": "铂金发","en": "platinum blonde","hex": "#EDE6D3"},{"zh": "金丝雀黄","en": "canary yellow","hex": "#FFEF00"},{"zh": "向日葵黄","en": "sunflower yellow","hex": "#FFDA03"},{"zh": "蜂蜜黄","en": "honey yellow","hex": "#F0C300"},{"zh": "麦秆黄","en": "straw yellow","hex": "#E4D96F"},{"zh": "玉米黄","en": "maize","hex": "#FBEC5D"},{"zh": "柠檬霜黄","en": "lemon chiffon","hex": "#FFFACD"},{"zh": "香草黄","en": "vanilla","hex": "#F3E5AB"},{"zh": "櫨染","en": "hajizome","hex": "#DDA52D"},{"zh": "桑茶","en": "kuwacha","hex": "#C99833"},{"zh": "玉子","en": "tamago","hex": "#F9BF45"},{"zh": "黄橡","en": "kitsurubami","hex": "#BA9132"},{"zh": "玉蜀黍","en": "tamamorokoshi","hex": "#E8B647"},{"zh": "花葉","en": "hanaba","hex": "#F7C242"},{"zh": "浅黄","en": "usuki","hex": "#FAD689"},{"zh": "黄朽葉","en": "kikuchiba","hex": "#D9AB42"},{"zh": "梔子","en": "kuchinashi","hex": "#F6C555"},{"zh": "籐黄","en": "tohoh","hex": "#FFC408"},{"zh": "鬱金","en": "ukon","hex": "#EFBB24"},{"zh": "芥子","en": "karashi","hex": "#CAAD5F"},{"zh": "肥後煤竹","en": "higosusutake","hex": "#8D742A"},{"zh": "菜種油","en": "nataneyu","hex": "#A28C37"},{"zh": "鶯茶","en": "uguisucha","hex": "#6C6024"},{"zh": "黄海松茶","en": "kimirucha","hex": "#867835"},{"zh": "海松茶","en": "mirucha","hex": "#62592C"},{"zh": "刈安","en": "kariyasu","hex": "#E9CD4C"},{"zh": "菜の花","en": "nanohana","hex": "#F7D94C"},{"zh": "黄蘗","en": "kihada","hex": "#FBE251"},{"zh": "蒸栗","en": "mushikuri","hex": "#D9CD90"},{"zh": "青朽葉","en": "aokuchiba","hex": "#ADA142"},{"zh": "女郎花","en": "ominaeshi","hex": "#DDD23B"},{"zh": "鶸茶","en": "hiwacha","hex": "#A5A051"},{"zh": "鶸","en": "hiwa","hex": "#BEC23F"},{"zh": "鶯","en": "uguisu","hex": "#6C6A2D"},{"zh": "苔","en": "koke","hex": "#838A2D"},{"zh": "麹塵","en": "kikujin","hex": "#B1B479"},{"zh": "藍媚茶","en": "aikobicha","hex": "#4B4E2A"},{"zh": "海松","en": "miru","hex": "#5B622E"},{"zh": "千歳茶","en": "sensaicha","hex": "#4D5139"},{"zh": "砂色","en": "sunairo","hex": "#DCD3B2"},{"zh": "緑黄","en": "ryokuoushoku","hex": "#DCCB18"},{"zh": "若草","en": "wakakusairo","hex": "#C3D825"},{"zh": "黄緑","en": "kimidori","hex": "#B8D200"},{"zh": "象牙","en": "zougeiro","hex": "#F8F4E6"},{"zh": "練色","en": "neriiro","hex": "#EDE4CD"},{"zh": "灰白","en": "kaihakushoku","hex": "#E9E4D4"},{"zh": "枯草","en": "karekusairo","hex": "#E4DC8A"},{"zh": "淡黄","en": "tankou","hex": "#F8E58C"},{"zh": "生成り","en": "kinariiro","hex": "#FBFAF5"},{"zh": "蒲公英","en": "tanpopoiro","hex": "#FFD900"},{"zh": "中黄","en": "chuuki","hex": "#FFEA00"},{"zh": "黄檗","en": "kihadairo","hex": "#FEF263"},{"zh": "卵色","en": "tamagoiro","hex": "#FCD575"},{"zh": "金糸雀","en": "kanariairo","hex": "#EBD842"},{"zh": "黄支子","en": "kikuchinashiiro","hex": "#FFDB4F"},{"zh": "支子","en": "kuchinashiiro","hex": "#FBCA4D"},{"zh": "向日葵","en": "himawariiro","hex": "#FCC800"},{"zh": "山吹","en": "yamabukiiro","hex": "#F8B500"},{"zh": "藤黄","en": "touou","hex": "#F7C114"},{"zh": "金色","en": "konjiki","hex": "#E6B422"},{"zh": "香蕉黄","en": "banana yellow","hex": "#FFE135"},{"zh": "黄油黄","en": "butter yellow","hex": "#FFF1B8"},{"zh": "蒲公英黄","en": "dandelion yellow","hex": "#F0E130"},{"zh": "奶黄","en": "pastel yellow","hex": "#FDFD96"},{"zh": "霓虹黄","en": "neon yellow","hex": "#EAF900"}]},{"family": "绿系","en": "greens","tip": "抹茶、制服、自然场景；emerald 做宝石点缀，matcha 压得住大面积。","colors": [{"zh": "薄荷绿","en": "mint green","hex": "#98FF98"},{"zh": "抹茶绿","en": "matcha green","hex": "#8A9A5B"},{"zh": "草绿","en": "grass green","hex": "#7EC850"},{"zh": "翡翠绿","en": "emerald","hex": "#50C878"},{"zh": "青瓷绿","en": "celadon","hex": "#ACE1AF"},{"zh": "橄榄绿","en": "olive","hex": "#808000"},{"zh": "苔藓绿","en": "moss green","hex": "#5B7553"},{"zh": "墨绿","en": "deep green","hex": "#0B3D2E"},{"zh": "青柠绿","en": "lime green","hex": "#32CD32"},{"zh": "玉绿","en": "jade green","hex": "#00A86B"},{"zh": "森林绿","en": "forest green","hex": "#228B22"},{"zh": "猎人绿","en": "hunter green","hex": "#355E3B"},{"zh": "鼠尾草绿","en": "sage green","hex": "#B2AC88"},{"zh": "海沫绿","en": "seafoam green","hex": "#9FE2BF"},{"zh": "开心果绿","en": "pistachio","hex": "#93C572"},{"zh": "春绿","en": "spring green","hex": "#00FF7F"},{"zh": "梅幸茶","en": "baikocha","hex": "#89916B"},{"zh": "鶸萌黄","en": "hiwamoegi","hex": "#90B44B"},{"zh": "柳染","en": "yanagizome","hex": "#91AD70"},{"zh": "裏柳","en": "urayanagi","hex": "#B5CAA0"},{"zh": "岩井茶","en": "iwaicha","hex": "#646A58"},{"zh": "萌黄","en": "moegi","hex": "#7BA23F"},{"zh": "苗","en": "nae","hex": "#86C166"},{"zh": "柳煤竹","en": "yanagisusutake","hex": "#4A593D"},{"zh": "松葉","en": "matsuba","hex": "#42602D"},{"zh": "青丹","en": "aoni","hex": "#516E41"},{"zh": "薄青","en": "usuao","hex": "#91B493"},{"zh": "柳鼠","en": "yanaginezumi","hex": "#808F7C"},{"zh": "常磐","en": "tokiwa","hex": "#1B813E"},{"zh": "若竹","en": "wakatake","hex": "#5DAC81"},{"zh": "千歳緑","en": "chitosemidori","hex": "#36563C"},{"zh": "緑","en": "green","hex": "#227D51"},{"zh": "白緑","en": "byakuroku","hex": "#A8D8B9"},{"zh": "老竹","en": "oitake","hex": "#6A8372"},{"zh": "木賊","en": "tokusa","hex": "#2D6D4B"},{"zh": "御納戸茶","en": "onandocha","hex": "#465D4C"},{"zh": "錆青磁","en": "sabiseiji","hex": "#86A697"},{"zh": "柳茶","en": "yanagicha","hex": "#939650"},{"zh": "璃寛茶","en": "rikancha","hex": "#616138"},{"zh": "翡翠","en": "hisuiiro","hex": "#38B48B"},{"zh": "灰黄緑","en": "haikimidori","hex": "#E6EAE3"},{"zh": "若芽","en": "wakameiro","hex": "#E0EBAF"},{"zh": "若菜","en": "wakanairo","hex": "#D8E698"},{"zh": "若苗","en": "wakanaeiro","hex": "#C7DC68"},{"zh": "草色","en": "kusairo","hex": "#7B8D42"},{"zh": "若葉","en": "wakabairo","hex": "#B9D08B"},{"zh": "夏虫","en": "natsumushiiro","hex": "#CEE4AE"},{"zh": "柳色","en": "yanagiiro","hex": "#A8C97F"},{"zh": "青白橡","en": "aoshirotsurubami","hex": "#9BA88D"},{"zh": "白磁","en": "hakuji","hex": "#F8FBF8"},{"zh": "裏葉柳","en": "urahayanagi","hex": "#C1D8AC"},{"zh": "山葵","en": "wasabiiro","hex": "#A8BF93"},{"zh": "淡萌黄","en": "usumoegi","hex": "#93CA76"},{"zh": "薄萌葱","en": "usumoegiiro","hex": "#BADCAD"},{"zh": "若緑","en": "wakamidori","hex": "#98D98E"},{"zh": "浅緑","en": "asamidori","hex": "#88CB7F"},{"zh": "薄緑","en": "usumidori","hex": "#69B076"},{"zh": "青磁鼠","en": "seijinezu","hex": "#BED2C3"},{"zh": "千草鼠","en": "chigusanezu","hex": "#BED3CA"},{"zh": "濡羽","en": "nurebairo","hex": "#000B00"},{"zh": "深緑","en": "fukamidori","hex": "#00552E"},{"zh": "淡绿","en": "pastel green","hex": "#77DD77"},{"zh": "霓虹绿","en": "neon green","hex": "#39FF14"},{"zh": "牛油果绿","en": "avocado green","hex": "#568203"},{"zh": "蕨绿","en": "fern green","hex": "#4F7942"},{"zh": "薄荷奶油绿","en": "mint cream","hex": "#F5FFFA"}]},{"family": "青系","en": "cyans & teals","tip": "日系水色、初音色都在这；tiffany 做清凉点缀，teal 压暗夜场景。","colors": [{"zh": "水色","en": "mizu blue","hex": "#7DB9B3"},{"zh": "初音绿","en": "turquoise","hex": "#39C5CF"},{"zh": "蒂芙尼蓝","en": "tiffany blue","hex": "#81D8D0"},{"zh": "浅葱色","en": "asagi blue","hex": "#00A3AF"},{"zh": "水鸭青","en": "teal","hex": "#008080"},{"zh": "孔雀蓝","en": "peacock blue","hex": "#005F6B"},{"zh": "苍青","en": "dark cyan","hex": "#008B8B"},{"zh": "水蓝","en": "aqua","hex": "#00FFFF"},{"zh": "海水蓝","en": "aquamarine","hex": "#7FFFD4"},{"zh": "碧绿","en": "viridian","hex": "#40826D"},{"zh": "鸭蛋青","en": "duck egg blue","hex": "#C3FBF4"},{"zh": "罗宾蛋蓝","en": "robin egg blue","hex": "#00CCCC"},{"zh": "緑青","en": "rokusyoh","hex": "#24936E"},{"zh": "青竹","en": "aotake","hex": "#00896C"},{"zh": "ビロード","en": "veludo","hex": "#096148"},{"zh": "虫襖","en": "mushiao","hex": "#20604F"},{"zh": "藍海松茶","en": "aimirucha","hex": "#0F4C3A"},{"zh": "沈香茶","en": "tonocha2","hex": "#4F726C"},{"zh": "青緑","en": "aomidori","hex": "#00AA90"},{"zh": "青磁","en": "seiji","hex": "#69B0AC"},{"zh": "鉄","en": "tetsu","hex": "#26453D"},{"zh": "水浅葱","en": "mizuasagi","hex": "#66BAB7"},{"zh": "青碧","en": "blue green","hex": "#268785"},{"zh": "錆鉄御納戸","en": "sabitetsuonando","hex": "#405B55"},{"zh": "高麗納戸","en": "korainando","hex": "#305A56"},{"zh": "白群","en": "byakugun","hex": "#78C2C4"},{"zh": "御召茶","en": "omeshicha","hex": "#376B6D"},{"zh": "瓶覗","en": "kamenozoki","hex": "#A5DEE4"},{"zh": "深川鼠","en": "fukagawanezumi","hex": "#77969A"},{"zh": "錆浅葱","en": "sabiasagi","hex": "#6699A1"},{"zh": "水","en": "mizu","hex": "#81C7D4"},{"zh": "浅葱","en": "asagi","hex": "#33A6B8"},{"zh": "御納戸","en": "onando","hex": "#0C4842"},{"zh": "藍","en": "indigo","hex": "#0D5661"},{"zh": "新橋","en": "shinbashi","hex": "#0089A7"},{"zh": "鉄御納戸","en": "tetsuonando","hex": "#255359"},{"zh": "萌葱","en": "moegiiro","hex": "#006E54"},{"zh": "花緑青","en": "hanarokushou","hex": "#00A381"},{"zh": "湊鼠","en": "minatonezumi","hex": "#80989B"},{"zh": "百入茶","en": "momoshiochairo","hex": "#1F3134"},{"zh": "藍白","en": "aijiro","hex": "#EBF6F7"},{"zh": "白藍","en": "shiraai","hex": "#C1E4E9"},{"zh": "秘色","en": "hisokuiro","hex": "#ABCED8"},{"zh": "浅縹","en": "asahanada","hex": "#84B9CB"},{"zh": "納戸","en": "nandoiro","hex": "#008899"},{"zh": "卯の花","en": "unohanairo","hex": "#F7FCFE"},{"zh": "常磐緑","en": "tokiwamidori","hex": "#028760"},{"zh": "天鵞絨","en": "biroudo","hex": "#2F5D50"},{"zh": "薄荷蓝","en": "mint blue","hex": "#A2E8DD"},{"zh": "电光青","en": "electric cyan","hex": "#0FF0FC"},{"zh": "鸭绿","en": "teal blue","hex": "#367588"},{"zh": "湖雾青","en": "aqua mist","hex": "#F0FFFF"}]},{"family": "蓝系","en": "blues","tip": "校服、夜空、海景；klein 极浓慎用大面积，dusty blue 最百搭。","colors": [{"zh": "天空蓝","en": "sky blue","hex": "#87CEEB"},{"zh": "矢车菊蓝","en": "cornflower blue","hex": "#6495ED"},{"zh": "宝蓝","en": "royal blue","hex": "#4169E1"},{"zh": "钴蓝","en": "cobalt blue","hex": "#0047AB"},{"zh": "克莱因蓝","en": "klein blue","hex": "#002FA7"},{"zh": "群青","en": "ultramarine","hex": "#120A8F"},{"zh": "藏青","en": "navy","hex": "#000080"},{"zh": "雾蓝","en": "dusty blue","hex": "#8CA3B8"},{"zh": "蔚蓝","en": "azure","hex": "#007FFF"},{"zh": "天青","en": "cerulean","hex": "#007BA7"},{"zh": "蓝宝石蓝","en": "sapphire blue","hex": "#0F52BA"},{"zh": "牛仔蓝","en": "denim blue","hex": "#1560BD"},{"zh": "钢蓝","en": "steel blue","hex": "#4682B4"},{"zh": "午夜蓝","en": "midnight blue","hex": "#191970"},{"zh": "冰蓝","en": "ice blue","hex": "#D6ECFF"},{"zh": "婴儿蓝","en": "baby blue","hex": "#89CFF0"},{"zh": "长春花蓝","en": "periwinkle","hex": "#CCCCFF"},{"zh": "普鲁士蓝","en": "prussian blue","hex": "#003153"},{"zh": "錆御納戸","en": "sabionando","hex": "#336774"},{"zh": "花浅葱","en": "hanaasagi","hex": "#1E88A8"},{"zh": "舛花","en": "masuhana","hex": "#577C8A"},{"zh": "熨斗目花","en": "noshimehana","hex": "#2B5F75"},{"zh": "千草","en": "chigusa","hex": "#3A8FB7"},{"zh": "御召御納戸","en": "omeshionando","hex": "#2E5C6E"},{"zh": "縹","en": "hanada","hex": "#006284"},{"zh": "勿忘草","en": "wasurenagusa","hex": "#7DB9DE"},{"zh": "群青","en": "gunjyo","hex": "#51A8DD"},{"zh": "露草","en": "tsuyukusa","hex": "#2EA9DF"},{"zh": "黒橡","en": "kurotsurubami","hex": "#0B1013"},{"zh": "紺","en": "navy blue","hex": "#0F2540"},{"zh": "褐","en": "kachi","hex": "#08192D"},{"zh": "瑠璃","en": "lapis blue","hex": "#005CAF"},{"zh": "瑠璃紺","en": "dark blue lapis lazuli","hex": "#0B346E"},{"zh": "紅碧","en": "benimidori","hex": "#7B90D2"},{"zh": "鉄紺","en": "tetsukon","hex": "#261E47"},{"zh": "紺青","en": "konjyo","hex": "#113285"},{"zh": "紅掛花","en": "benikakehana","hex": "#4E4F97"},{"zh": "紺桔梗","en": "navy blue bellflower","hex": "#211E55"},{"zh": "二藍","en": "futaai","hex": "#70649A"},{"zh": "楝","en": "ouchi","hex": "#9B90C2"},{"zh": "藤鼠","en": "fujinezu","hex": "#A6A5C4"},{"zh": "紺鼠","en": "konnezu","hex": "#44617B"},{"zh": "藍鉄","en": "aitetsu","hex": "#393F4C"},{"zh": "青褐","en": "aokachi","hex": "#393E4F"},{"zh": "褐返","en": "kachikaeshi","hex": "#203744"},{"zh": "月白","en": "geppaku","hex": "#EAF4FC"},{"zh": "白菫","en": "shirosumireiro","hex": "#EAEDF7"},{"zh": "白花","en": "shirahanairo","hex": "#E8ECEF"},{"zh": "空色","en": "sorairo","hex": "#A0D8EF"},{"zh": "青藤","en": "aofujiiro","hex": "#84A2D4"},{"zh": "薄花","en": "usuhanairo","hex": "#698AAB"},{"zh": "天色","en": "amairoiro","hex": "#2CA9E1"},{"zh": "青","en": "ao","hex": "#0095D9"},{"zh": "薄藍","en": "usuai","hex": "#0094C8"},{"zh": "紺碧","en": "konpeki","hex": "#007BBB"},{"zh": "薄群青","en": "usugunjou","hex": "#5383C3"},{"zh": "薄花桜","en": "usuhanazakura","hex": "#5A79BA"},{"zh": "薄縹","en": "usuhanada","hex": "#507EA4"},{"zh": "紺瑠璃","en": "konruri","hex": "#164A84"},{"zh": "青藍","en": "seiran","hex": "#274A78"},{"zh": "深縹","en": "kokihanada","hex": "#2A4073"},{"zh": "留紺","en": "tomekon","hex": "#1C305C"},{"zh": "濃藍","en": "koiai","hex": "#0F2350"},{"zh": "淡藤","en": "awafujiiro","hex": "#BBC8E6"},{"zh": "紅掛空","en": "benikakesorairo","hex": "#8491C3"},{"zh": "花色","en": "hanairo","hex": "#4D5AAF"},{"zh": "紺藍","en": "konai","hex": "#4A488E"},{"zh": "紅桔梗","en": "benikikyou","hex": "#4D4398"},{"zh": "藤納戸","en": "fujinando","hex": "#706CAA"},{"zh": "淡蓝","en": "pastel blue","hex": "#AEC6CF"},{"zh": "霓虹蓝","en": "neon blue","hex": "#1F51FF"},{"zh": "深海蓝","en": "deep sea blue","hex": "#006994"},{"zh": "蓝莓蓝","en": "blueberry","hex": "#4F86F7"}]},{"family": "紫系","en": "purples","tip": "梦幻、夜樱、魔法少女；藤色桔梗色是和风首选，grape 压得住暗景。","colors": [{"zh": "薰衣草紫","en": "lavender","hex": "#B57EDC"},{"zh": "丁香紫","en": "lilac","hex": "#C8A2C8"},{"zh": "紫罗兰","en": "violet","hex": "#8F00FF"},{"zh": "葡萄紫","en": "grape purple","hex": "#6F2DA8"},{"zh": "藤色","en": "wisteria","hex": "#8B81C3"},{"zh": "桔梗色","en": "kikyo purple","hex": "#5654A4"},{"zh": "灰紫","en": "mauve","hex": "#E0B0FF"},{"zh": "梅紫","en": "plum","hex": "#DDA0DD"},{"zh": "兰花紫","en": "orchid","hex": "#DA70D6"},{"zh": "紫水晶紫","en": "amethyst","hex": "#9966CC"},{"zh": "鸢尾紫","en": "iris purple","hex": "#5A4FCF"},{"zh": "天芥紫","en": "heliotrope","hex": "#DF73FF"},{"zh": "蓟紫","en": "thistle","hex": "#D8BFD8"},{"zh": "拜占庭紫","en": "byzantium","hex": "#702963"},{"zh": "茄子紫","en": "eggplant","hex": "#614051"},{"zh": "藤紫","en": "wisteria purple","hex": "#8A6BBE"},{"zh": "桔梗","en": "kikyo","hex": "#6A4C9C"},{"zh": "紫苑","en": "shion","hex": "#8F77B5"},{"zh": "滅紫","en": "messhi","hex": "#533D5B"},{"zh": "薄","en": "usu","hex": "#B28FCE"},{"zh": "半","en": "hashita","hex": "#986DB2"},{"zh": "江戸紫","en": "edomurasaki","hex": "#77428D"},{"zh": "紫紺","en": "blue violet","hex": "#3C2F41"},{"zh": "深紫","en": "deep purple","hex": "#4A225D"},{"zh": "菫","en": "sumire","hex": "#66327C"},{"zh": "紫","en": "purple","hex": "#592C63"},{"zh": "菖蒲","en": "ayame","hex": "#6F3381"},{"zh": "暁鼠","en": "akatsukinezu","hex": "#D3CFD9"},{"zh": "濃鼠","en": "koinezu","hex": "#4F455C"},{"zh": "葡萄","en": "ebiiro","hex": "#640125"},{"zh": "漆黒","en": "shikkoku","hex": "#0D0015"},{"zh": "白藤","en": "shirafujiiro","hex": "#DBD0E6"},{"zh": "青紫","en": "aomurasaki","hex": "#674598"},{"zh": "竜胆","en": "rindouiro","hex": "#9079AD"},{"zh": "本紫","en": "honmurasaki","hex": "#65318E"},{"zh": "烏羽","en": "karasubairo","hex": "#180614"},{"zh": "薄葡萄","en": "usubudou","hex": "#C0A2C7"},{"zh": "似せ紫","en": "nisemurasakiiro","hex": "#513743"},{"zh": "淡紫","en": "pastel purple","hex": "#B39EB5"},{"zh": "霓虹紫","en": "neon purple","hex": "#BC13FE"},{"zh": "皇家紫","en": "royal purple","hex": "#7851A9"},{"zh": "三色堇紫","en": "pansy purple","hex": "#78184A"}]},{"family": "棕系","en": "browns","tip": "发色、秋冬服装、木质场景；camel/khaki 是万能中性色。","colors": [{"zh": "巧克力棕","en": "chocolate brown","hex": "#7B3F00"},{"zh": "咖啡棕","en": "coffee brown","hex": "#6F4E37"},{"zh": "焦糖棕","en": "caramel","hex": "#C68E5B"},{"zh": "卡其色","en": "khaki","hex": "#C3B091"},{"zh": "驼色","en": "camel","hex": "#C19A6B"},{"zh": "栗色","en": "chestnut","hex": "#954535"},{"zh": "亚麻色","en": "linen","hex": "#FAF0E6"},{"zh": "燕麦色","en": "oatmeal","hex": "#D8CFC4"},{"zh": "栗发","en": "chestnut hair","hex": "#6E4B2A"},{"zh": "棕褐","en": "tan","hex": "#D2B48C"},{"zh": "摩卡棕","en": "mocha","hex": "#967969"},{"zh": "深褐","en": "sepia","hex": "#704214"},{"zh": "铁锈褐","en": "russet","hex": "#80461B"},{"zh": "棕土","en": "umber","hex": "#635147"},{"zh": "赭石棕","en": "sienna","hex": "#A0522D"},{"zh": "灰褐","en": "taupe","hex": "#8B8589"},{"zh": "胡桃棕","en": "walnut","hex": "#773F1A"},{"zh": "沙色","en": "sand","hex": "#C2B280"},{"zh": "海老茶","en": "maroon","hex": "#734338"},{"zh": "黒鳶","en": "kurotobi","hex": "#554236"},{"zh": "水がき","en": "mizugaki","hex": "#B9887D"},{"zh": "紅檜皮","en": "benihiwada","hex": "#884C3A"},{"zh": "檜皮","en": "hiwada","hex": "#854836"},{"zh": "鳶","en": "tobi","hex": "#724832"},{"zh": "栗皮茶","en": "kurikawacha","hex": "#6A4028"},{"zh": "百塩茶","en": "momoshiocha","hex": "#724938"},{"zh": "焦茶","en": "kogecha","hex": "#563F2E"},{"zh": "胡桃","en": "kurumi","hex": "#947A6D"},{"zh": "黄櫨染","en": "kohrozen","hex": "#7D532C"},{"zh": "煎茶","en": "sencha","hex": "#855B32"},{"zh": "憲法染","en": "kenpohzome","hex": "#43341B"},{"zh": "伽羅","en": "kyara","hex": "#78552B"},{"zh": "煤竹","en": "susutake","hex": "#6E552F"},{"zh": "銀煤竹","en": "ginsusutake","hex": "#82663A"},{"zh": "白茶","en": "shiracha","hex": "#BC9F77"},{"zh": "媚茶","en": "kobicha","hex": "#876633"},{"zh": "生壁／生壁色","en": "namakabe","hex": "#7D6C46"},{"zh": "利休白茶","en": "rikyushiracha","hex": "#B4A582"},{"zh": "灰汁","en": "aku","hex": "#877F6C"},{"zh": "利休茶","en": "rikyucha","hex": "#897D55"},{"zh": "路考茶","en": "rokohcha","hex": "#74673E"},{"zh": "紅消鼠","en": "benikeshinezumi","hex": "#52433D"},{"zh": "檳榔子染","en": "binrojizome","hex": "#3A3226"},{"zh": "枯茶","en": "karachairo","hex": "#8D6449"},{"zh": "櫨色","en": "hajiiro","hex": "#B77B57"},{"zh": "丁字染／香染","en": "choujizome","hex": "#AD7D4C"},{"zh": "焦香","en": "kogarekou","hex": "#AE7C58"},{"zh": "灰梅","en": "haiume","hex": "#E8D3C7"},{"zh": "渋紙","en": "shibukamiiro","hex": "#946243"},{"zh": "空五倍子","en": "utsubushiiro","hex": "#9D896C"},{"zh": "国防","en": "kokuboushoku","hex": "#7B6C3E"},{"zh": "亜麻","en": "amairo","hex": "#D6C6AF"},{"zh": "榛色","en": "hashibamiiro","hex": "#BFA46F"},{"zh": "梅染","en": "umezome","hex": "#B48A76"},{"zh": "木蘭","en": "mokuranjiki","hex": "#C7B370"},{"zh": "油色","en": "aburairo","hex": "#A19361"},{"zh": "利休","en": "rikyuuiro","hex": "#8F8667"},{"zh": "団十郎茶","en": "danjuuroucha","hex": "#9F563A"},{"zh": "灰茶","en": "haicha","hex": "#98623C"},{"zh": "枯野","en": "karenoiro","hex": "#D3CBC6"},{"zh": "茶色","en": "chairo","hex": "#965042"},{"zh": "根岸","en": "negishiiro","hex": "#938B4B"},{"zh": "茶鼠","en": "chanezumi","hex": "#A99E93"},{"zh": "柿茶","en": "kakicha","hex": "#954E2A"},{"zh": "胡桃染","en": "kurumizome","hex": "#A58F86"},{"zh": "抹茶","en": "macchairo","hex": "#C5C56A"},{"zh": "砺茶","en": "tonochairo","hex": "#9F6F55"},{"zh": "赤銅","en": "shakudouiro","hex": "#752100"},{"zh": "黄枯茶","en": "kigarachairo","hex": "#765C47"},{"zh": "赤褐","en": "sekkasshoku","hex": "#683F36"},{"zh": "茶褐","en": "chakasshoku","hex": "#664032"},{"zh": "憲法","en": "kenpouiro","hex": "#543F32"},{"zh": "黒茶","en": "kurocha","hex": "#583822"},{"zh": "涅色","en": "kuriiro","hex": "#554738"},{"zh": "葡萄茶","en": "ebicha","hex": "#6C2C2F"},{"zh": "赤墨","en": "akasumi","hex": "#3F312B"},{"zh": "素色","en": "soshoku","hex": "#EAE5E3"},{"zh": "鉄黒","en": "tetsuguro","hex": "#281A14"},{"zh": "黒檀","en": "kokutan","hex": "#250D00"},{"zh": "憲法黒茶","en": "kenpoukurocha","hex": "#241A08"},{"zh": "暗黒","en": "ankokushoku","hex": "#16160E"},{"zh": "可可棕","en": "cocoa brown","hex": "#875442"},{"zh": "肉桂棕","en": "cinnamon","hex": "#D2691E"},{"zh": "榛果棕","en": "hazelnut","hex": "#B88A5C"},{"zh": "太妃棕","en": "toffee brown","hex": "#B5651D"}]},{"family": "灰系","en": "grays","tip": "背景、影棚、雨天；warm gray 配暖光、cool gray 配夜景。","colors": [{"zh": "雾灰","en": "mist gray","hex": "#C9C9C9"},{"zh": "银灰","en": "silver gray","hex": "#A9A9A9"},{"zh": "中灰","en": "neutral gray","hex": "#808080"},{"zh": "暖灰","en": "warm gray","hex": "#8B8680"},{"zh": "鼠色","en": "stone gray","hex": "#94948F"},{"zh": "炭灰","en": "charcoal","hex": "#36454F"},{"zh": "石墨灰","en": "graphite","hex": "#3B3B3B"},{"zh": "银发","en": "silver hair","hex": "#D7D7DE"},{"zh": "烟灰发","en": "ash gray hair","hex": "#9AA0A6"},{"zh": "石板灰","en": "slate gray","hex": "#708090"},{"zh": "浅灰白","en": "ash gray","hex": "#B2BEB5"},{"zh": "鸽灰","en": "dove gray","hex": "#6D6C6C"},{"zh": "锡灰","en": "pewter","hex": "#899499"},{"zh": "铅灰","en": "iron gray","hex": "#52595D"},{"zh": "枪灰","en": "gunmetal","hex": "#2A3439"},{"zh": "烟灰","en": "smoke gray","hex": "#738276"},{"zh": "鉛","en": "namari","hex": "#787878"},{"zh": "灰","en": "gray","hex": "#828282"},{"zh": "素鼠","en": "sunezumi","hex": "#787D7B"},{"zh": "利休鼠","en": "rikyunezumi","hex": "#707C74"},{"zh": "鈍","en": "nibi","hex": "#656765"},{"zh": "青鈍","en": "aonibi","hex": "#535953"},{"zh": "溝鼠","en": "dobunezumi","hex": "#4F4F48"},{"zh": "藍墨茶","en": "aisumicha","hex": "#373C38"},{"zh": "消炭","en": "keshizumi","hex": "#434343"},{"zh": "豆がら茶","en": "mamegaracha","hex": "#8B968D"},{"zh": "山鳩","en": "yamabatoiro","hex": "#767C6B"},{"zh": "錆鼠","en": "sabinezu","hex": "#47585C"},{"zh": "薄梅鼠","en": "usuumenezu","hex": "#DCD6D9"},{"zh": "藍鼠","en": "ainezu","hex": "#6C848D"},{"zh": "仙斎茶","en": "sensaichairo","hex": "#474B42"},{"zh": "牡丹鼠","en": "botannezu","hex": "#D3CCD6"},{"zh": "黒緑","en": "kuromidori","hex": "#333631"},{"zh": "霞色","en": "kasumiiro","hex": "#C8C2C6"},{"zh": "薄鼠","en": "usunezu","hex": "#9790A4"},{"zh": "鳩羽","en": "hatobairo","hex": "#95859C"},{"zh": "桔梗鼠","en": "kikyounezu","hex": "#95949A"},{"zh": "紫鼠","en": "murasakinezu","hex": "#71686C"},{"zh": "蕎麦切","en": "sobakiriiro","hex": "#D4DCD6"},{"zh": "薄雲鼠","en": "usukumonezu","hex": "#D4DCDA"},{"zh": "潤色","en": "urumiiro","hex": "#C8C2BE"},{"zh": "江戸鼠","en": "edonezu","hex": "#928178"},{"zh": "煤色","en": "susuiro","hex": "#887F7A"},{"zh": "白梅鼠","en": "shiraumenezu","hex": "#E5E4E6"},{"zh": "白鼠","en": "shironezu","hex": "#DCDDDD"},{"zh": "絹鼠","en": "kinunezu","hex": "#DDDCD6"},{"zh": "灰青","en": "haiao","hex": "#C0C6C9"},{"zh": "銀鼠","en": "ginnezu","hex": "#AFAFB0"},{"zh": "薄鈍","en": "usunibi","hex": "#ADADAD"},{"zh": "薄墨","en": "usuzumiiro","hex": "#A3A3A2"},{"zh": "錫色","en": "suzuiro","hex": "#9EA1A3"},{"zh": "源氏鼠","en": "genjinezu","hex": "#888084"},{"zh": "丼鼠","en": "dobunezumiiro","hex": "#595455"},{"zh": "羊羹","en": "youkaniro","hex": "#383C3C"},{"zh": "紫黒","en": "shikoku","hex": "#2E2930"},{"zh": "革色","en": "kawairo","hex": "#475950"},{"zh": "紫水晶","en": "murasakisuishou","hex": "#E7E7EB"},{"zh": "淡灰","en": "pastel gray","hex": "#CFCFC4"},{"zh": "暗灰","en": "dim gray","hex": "#696969"},{"zh": "水泥灰","en": "cement gray","hex": "#85898B"},{"zh": "云灰","en": "cloud gray","hex": "#E8E8E8"}]},{"family": "肤色系","en": "skin tones","tip": "肤色从瓷白到黝黑渐变；腮红单独列最后，写进表情/皮肤位。","colors": [{"zh": "白皙","en": "fair skin","hex": "#F6E3CE"},{"zh": "瓷肌","en": "porcelain skin","hex": "#FBF1E4"},{"zh": "浅肤","en": "light skin","hex": "#EFD0AC"},{"zh": "小麦肌","en": "wheat skin","hex": "#D9A05B"},{"zh": "蜜糖肌","en": "honey tan skin","hex": "#C68642"},{"zh": "古铜肌","en": "bronze skin","hex": "#8C6A4F"},{"zh": "棕肤","en": "brown skin","hex": "#6B4A32"},{"zh": "深肤","en": "dark skin","hex": "#4A3226"},{"zh": "黝黑","en": "ebony skin","hex": "#2C2019"},{"zh": "腮红","en": "blush pink","hex": "#F5A3B0"},{"zh": "苍白肤","en": "pale skin","hex": "#FBE9E3"},{"zh": "玫瑰肤","en": "rosy skin","hex": "#F3C6B4"},{"zh": "日光肤","en": "sunkissed skin","hex": "#D99A6C"},{"zh": "橄榄肤","en": "olive skin","hex": "#B08D57"},{"zh": "晒黑肤","en": "tanned skin","hex": "#C08A5E"},{"zh": "灰调肤","en": "grayish skin","hex": "#C9C0BB"},{"zh": "鳥の子","en": "torinoko","hex": "#DAC9A6"},{"zh": "牛奶肤","en": "milky skin","hex": "#F7E3D5"},{"zh": "蜜桃肤","en": "peachy skin","hex": "#F9D9C4"},{"zh": "蜜色肤","en": "honey beige","hex": "#D9B08C"},{"zh": "摩卡肤","en": "mocha skin","hex": "#8D5B3F"}]},{"family": "黑白系","en": "black & white","tip": "JK 制服黑白配直接取：白衬衫 white / off-white，黑外套 black / ink black。","colors": [{"zh": "纯白／白","en": "white","hex": "#FFFFFF"},{"zh": "米白","en": "off-white","hex": "#FAF9F6"},{"zh": "象牙白","en": "ivory","hex": "#FFFFF0"},{"zh": "珍珠白","en": "pearl white","hex": "#F2EDE4"},{"zh": "纯黑","en": "black","hex": "#000000"},{"zh": "墨黑","en": "ink black","hex": "#1A1A1A"},{"zh": "曜石黑","en": "obsidian","hex": "#0B0B0D"},{"zh": "雪白","en": "snow white","hex": "#FFFAFA"},{"zh": "骨白","en": "bone white","hex": "#F9F6EE"},{"zh": "粉笔白","en": "chalk white","hex": "#F8F8F8"},{"zh": "墨玉黑","en": "jet black","hex": "#0A0A0A"},{"zh": "哑光黑","en": "matte black","hex": "#232323"},{"zh": "白練","en": "shironeri","hex": "#FCFAF2"},{"zh": "胡粉","en": "gofun","hex": "#FFFFFB"},{"zh": "墨","en": "sumi","hex": "#1C1C1C"},{"zh": "呂","en": "ro","hex": "#0C0C0C"},{"zh": "乳白","en": "nyuuhakushoku","hex": "#F3F3F3"},{"zh": "黒／蝋色","en": "kuro","hex": "#2B2B2B"},{"zh": "幽灵白","en": "ghost white","hex": "#F8F8FF"},{"zh": "银白","en": "silver white","hex": "#F5F5F5"},{"zh": "乌鸦黑","en": "raven black","hex": "#141414"},{"zh": "煤黑","en": "coal black","hex": "#121212"}]},{"family": "金属系","en": "metallics","tip": "写进材质位：发饰、耳饰、眼眸高光，如 golden hair accessory。","colors": [{"zh": "黄金","en": "gold","hex": "#FFD700"},{"zh": "香槟金","en": "champagne gold","hex": "#E6C87A"},{"zh": "纯银","en": "silver","hex": "#DCDCDC"},{"zh": "古铜","en": "copper","hex": "#B87333"},{"zh": "玫瑰金","en": "rose gold","hex": "#B76E79"},{"zh": "珍珠","en": "pearl","hex": "#EDE6D6"},{"zh": "山吹茶","en": "gold brown","hex": "#D19826"},{"zh": "铂金","en": "platinum","hex": "#E5E4E2"},{"zh": "黄铜","en": "brass","hex": "#B5A642"},{"zh": "青铜","en": "bronze","hex": "#CD7F32"},{"zh": "锈铁","en": "rust iron","hex": "#B7410E"},{"zh": "黑金","en": "black gold","hex": "#2B2118"},{"zh": "古金","en": "antique gold","hex": "#A67C00"},{"zh": "钛银","en": "titanium","hex": "#878681"},{"zh": "镍银","en": "nickel silver","hex": "#C5C5C5"}]},{"family": "发色系","en": "hair colors","tip": "按 booru tag 习惯直接用词组：pink hair / blue hair；双色发写 two-tone hair，渐变发写 gradient hair。","colors": [{"zh": "黑发","en": "black hair","hex": "#131313"},{"zh": "深棕发","en": "dark brown hair","hex": "#3B2B20"},{"zh": "栗棕发","en": "chestnut brown hair","hex": "#5C3A21"},{"zh": "奶茶棕发","en": "milk tea brown hair","hex": "#A67B5B"},{"zh": "灰棕发","en": "ash brown hair","hex": "#6E5A4E"},{"zh": "蜜糖棕发","en": "honey brown hair","hex": "#9C6B3C"},{"zh": "亚麻金发","en": "ash blonde","hex": "#D8C08A"},{"zh": "草莓金发","en": "strawberry blonde","hex": "#E4A87E"},{"zh": "蜜糖金发","en": "honey blonde","hex": "#E0B15C"},{"zh": "白发","en": "white hair","hex": "#F2F2F2"},{"zh": "灰银发","en": "ash silver hair","hex": "#BFBFC7"},{"zh": "粉发","en": "pink hair","hex": "#F5A0B8"},{"zh": "淡粉发","en": "pastel pink hair","hex": "#FBD3DE"},{"zh": "紫发","en": "purple hair","hex": "#8E5EA8"},{"zh": "薰衣草紫发","en": "lavender hair","hex": "#C7A8DD"},{"zh": "蓝发","en": "blue hair","hex": "#3F6BA8"},{"zh": "浅蓝发","en": "light blue hair","hex": "#8FB8E0"},{"zh": "藏蓝发","en": "navy hair","hex": "#1E3A6E"},{"zh": "薄荷发","en": "mint hair","hex": "#9FD9C7"},{"zh": "青绿发","en": "teal hair","hex": "#3E8E8A"},{"zh": "橙发","en": "orange hair","hex": "#E08A3C"},{"zh": "双色发","en": "two-tone hair","hex": "#B98BB0"},{"zh": "渐变色发","en": "gradient hair","hex": "#C9A0C4"}]},{"family": "瞳色系","en": "eye colors","tip": "瞳色直接写 crimson eyes / amber eyes；异色瞳写 heterochromia, mismatched eyes。色值取自对应色系，作示意。","colors": [{"zh": "红瞳","en": "crimson eyes","hex": "#C1121F"},{"zh": "朱瞳","en": "vermilion eyes","hex": "#E5493B"},{"zh": "琥珀瞳","en": "amber eyes","hex": "#E8A33D"},{"zh": "金瞳","en": "golden eyes","hex": "#F0C040"},{"zh": "翡翠瞳","en": "emerald eyes","hex": "#2E9E6B"},{"zh": "青瞳","en": "azure eyes","hex": "#3A78C2"},{"zh": "冰蓝瞳","en": "ice blue eyes","hex": "#A8D8F0"},{"zh": "紫瞳","en": "violet eyes","hex": "#8E5AC8"},{"zh": "薰衣草瞳","en": "lavender eyes","hex": "#BFA3E0"},{"zh": "粉瞳","en": "pink eyes","hex": "#F2A0C0"},{"zh": "榛瞳","en": "hazel eyes","hex": "#A97C3F"},{"zh": "棕瞳","en": "brown eyes","hex": "#6B4A2F"},{"zh": "灰瞳","en": "gray eyes","hex": "#9AA0A8"},{"zh": "黑瞳","en": "black eyes","hex": "#1C1C1C"},{"zh": "血瞳","en": "blood red eyes","hex": "#8A0F1A"},{"zh": "异色瞳","en": "heterochromia","hex": "#7FB2D9"}]}];

interface FlatColor {
  zh: string
  en: string
  hex: string
  family: string
  familyEn: string
  tip: string
}

const totalColors: number = DATA.reduce((n: number, f: PaletteFamily) => n + f.colors.length, 0)

const query = ref<string>('')
const active = ref<string>('全部')
const openKey = ref<string | null>(null)
const TRAY_LS = 'suli-palette-tray'
let trayInit = true
try { trayInit = localStorage.getItem(TRAY_LS) !== '0' } catch {}
const trayOpen = ref<boolean>(trayInit)
function toggleTray(): void {
  trayOpen.value = !trayOpen.value
  try { localStorage.setItem(TRAY_LS, trayOpen.value ? '1' : '0') } catch {}
}


const families: string[] = ['全部', ...DATA.map((f: PaletteFamily) => f.family)]

const allColors: FlatColor[] = DATA.flatMap((f: PaletteFamily) =>
  f.colors.map((c: PaletteColor) => ({
    zh: c.zh,
    en: c.en,
    hex: c.hex,
    family: f.family,
    familyEn: f.en,
    tip: f.tip
  }))
)

const filtered = computed<FlatColor[]>(() => {
  const q: string = query.value.trim().toLowerCase()
  return allColors.filter((c: FlatColor) => {
    if (active.value !== '全部' && c.family !== active.value) return false
    if (!q) return true
    return (
      c.zh.includes(query.value.trim()) ||
      c.en.toLowerCase().includes(q) ||
      c.hex.toLowerCase().includes(q) ||
      c.family.includes(query.value.trim())
    )
  })
})

const picked = ref<PaletteColor[]>([])

function combinedPrompt(): string {
  const words: string[] = picked.value.map((c: PaletteColor) => c.en)
  if (words.length === 0) return ''
  if (words.length === 1) return words[0] + ' color palette'
  const last: string = words.pop() as string
  return words.join(', ') + ' and ' + last + ' color palette'
}

function isOpen(key: string): boolean {
  return openKey.value === key
}

function toggleDetail(key: string): void {
  openKey.value = openKey.value === key ? null : key
}

function setActive(f: string): void {
  active.value = f
}

function clearFilter(): void {
  query.value = ''
  active.value = '全部'
}

async function copyHex(c: FlatColor): Promise<void> {
  await copyText(c.hex)
}

async function copyEn(c: FlatColor): Promise<void> {
  await copyText(c.en)
}

function addColor(c: PaletteColor): void {
  void copyText(c.en)
  if (!picked.value.some((p: PaletteColor) => p.en === c.en)) {
    picked.value.push(c)
  }
}

function removeAt(i: number): void {
  picked.value.splice(i, 1)
}

async function copyAll(): Promise<void> {
  const s: string = combinedPrompt()
  if (!s) {
    ElMessage.warning('组合栏是空的，先点色卡')
    return
  }
  await copyText(s)
  ElMessage.success('已复制组合：' + s)
}

function clearAll(): void {
  picked.value = []
}
</script>

<style scoped>
.palette-tool {
  --suli-primary: #FB7299;
  --suli-border: #e4e4e7;
  background: #fff;
  padding-bottom: 24px;
}
.suli-card {
  background: #fff;
  border: 1px solid var(--suli-border);
  border-radius: 10px;
}
.suli-muted {
  color: #71717a;
}
.mono {
  font-family: Consolas, monospace;
}
pre.suli-pre {
  background: #f4f4f6;
  border: 1px solid var(--suli-border);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12.5px;
  overflow-x: auto;
}
.tray {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #fff;
  border-bottom: 1px solid var(--suli-border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 10px 16px;
  margin: -8px -8px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.tray-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.search {
  max-width: 320px;
  flex: 1;
  min-width: 200px;
}
.count {
  font-size: 13px;
  white-space: nowrap;
}
.chip-tag {
  cursor: pointer;
}
.tray-label {
  font-size: 13px;
  color: #71717a;
  white-space: nowrap;
}
.combo .picked {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  flex: 1;
  min-height: 28px;
  align-items: center;
}
.empty-hint {
  font-size: 13px;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #f4f4f6;
  border: 1px solid var(--suli-border);
  border-radius: 20px;
  padding: 3px 6px 3px 3px;
  font-size: 13px;
}
.chip i {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: inline-block;
  border: 1px solid rgba(0, 0, 0, 0.15);
}
.chip b {
  font-weight: 400;
  font-family: Consolas, monospace;
}
.chip-x {
  cursor: pointer;
  color: #71717a;
  padding: 0 4px;
}
.chip-x:hover {
  color: #18181b;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}
.tool-card.card {
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.12s, box-shadow 0.12s;
}
.tool-card.card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(251, 114, 153, 0.18), 0 4px 14px rgba(0, 0, 0, 0.1);
  border-color: var(--suli-primary);
}
.tool-card.open {
  border-color: var(--suli-primary,#FB7299);
}
.detail-block {
  margin-top: 10px;
  border-top: 1px dashed var(--suli-border);
  padding-top: 10px;
  margin-left: 12px;
  margin-right: 12px;
  margin-bottom: 12px;
}
.detail-cols {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 12px;
}
@media (max-width: 560px) {
  .detail-cols {
    grid-template-columns: repeat(auto-fit,minmax(200px,1fr));
  }
}
.cover {
  position: relative;
  height: 84px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
.fam-chip {
  position: absolute;
  top: 8px;
  right: 8px;
}
.card .meta {
  padding: 10px 12px 12px;
}
.title {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.title .zh {
  font-size: 15px;
  font-weight: 700;
  color: #18181b;
}
.title .en {
  font-size: 12.5px;
  color: #71717a;
  font-family: Consolas, monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.pills {
  display: flex;
  gap: 6px;
  margin-top: 6px;
  flex-wrap: wrap;
}
.pill {
  font-size: 11.5px;
  border: 1px solid var(--suli-border);
  border-radius: 20px;
  padding: 1px 8px;
  background: #fafafa;
}
.pill.ghost {
  background: #fff;
  color: #71717a;
}
.sum {
  font-size: 12.5px;
  margin-top: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty {
  font-size: 13px;
  padding: 24px 4px;
  text-align: center;
}
.dlg-sw {
  height: 120px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}
.dlg-rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
  font-size: 14px;
}
.dlg-bar {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}
@media (max-width: 560px) {
  .grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 8px;
  }
  .tray {
    padding: 8px 10px;
  }
}

@container (max-width: 620px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
  .detail-cols { grid-template-columns: 1fr; }
}
@container (max-width: 400px) {
  .grid { grid-template-columns: 1fr; }
}
/* pack-slots: backpack face */
.tool-card > .meta > .pills, .tool-card > .meta > .sum { display: none; }
.tool-card > .meta > .title { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tool-card.open { box-shadow: 0 0 0 2px rgba(251,114,153,.45), 0 8px 20px rgba(251,114,153,.25); }</style>
