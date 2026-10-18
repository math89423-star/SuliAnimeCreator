<template>
  <div class="nsfw-guide">
    <div class="suli-card intro">
      <h2 class="t">分级创作指南 · 成人向插画提示词九槽公式</h2>
      <p class="iron">
        <b>18+ 与合规铁律（每次必查）：</b>只画成年虚构角色；prompt 首槽与 negative 双锚定成年；
        不画真人可识别长相、不画未成年或幼态外观、不写非自愿叙事。
      </p>
    </div>

    <div class="tray suli-card">
      <div class="tray-row">
        <el-input v-model="query" clearable placeholder="搜索" class="search" />
        <span class="suli-muted count">{{ filtered.length }} / {{ cards.length }}</span>
        <el-button size="small" @click="clearFilter">清空</el-button>
        <el-button size="small" text @click="toggleTray">{{ trayOpen ? '收起 ▲' : '展开 ▼' }}</el-button>
      </div>
      <template v-if="trayOpen">
      <div class="tray-row chips">
        <el-tag
          v-for="c in cats"
          :key="c"
          :effect="active === c ? 'dark' : 'plain'"
          :type="active === c ? 'primary' : 'info'"
          class="chip"
          @click="active = c"
        >{{ c }}</el-tag>
      </div>
      </template>
    </div>

    <div class="grid">
      <div
        v-for="c in filtered"
        :key="c.id"
        class="suli-card tool-card"
        :class="{ open: isOpen(c.id) }"
        @click="toggleDetail(c.id)"
      >
        <div class="cover">{{ c.cover }}<span class="corner">{{ c.cat }}</span></div>
        <div class="t"><b>{{ c.title }}</b><span class="en">{{ c.en }}</span></div>
        <div class="pills">
          <el-tag v-for="t in c.tags" :key="t" size="small">{{ t }}</el-tag>
        </div>
        <div class="sum">{{ c.summary }}</div>
        <el-dialog append-to-body :model-value="isOpen(c.id)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
          <div class="detail-block">
          <div class="detail-cols">
            <div class="detail-main">
              <div class="dlg-sub"><span class="en">{{ c.en }}</span><el-tag size="small">{{ c.cat }}</el-tag></div>
              <div class="pills">
                <el-tag v-for="t in c.tags" :key="t" size="small">{{ t }}</el-tag>
              </div>
              <p class="sum-full">{{ c.summary }}</p>
              <pre class="suli-pre">{{ c.body }}</pre>
            </div>
            <div class="detail-side">
              <div v-if="c.tplKeys.length > 0" class="tpl-list">
                <div v-for="k in c.tplKeys" :key="k" class="tpl-item">
                  <div class="tpl-head">
                    <span class="mono">{{ k }}</span>
                    <el-button type="primary" size="small" @click.stop="onCopy(k)">复制</el-button>
                  </div>
                  <pre class="suli-pre">{{ TPL[k] }}</pre>
                </div>
              </div>
              <div v-if="c.id === 'params'" class="tbl-wrap">
                <table class="grid-tbl">
                  <tr><th>模型</th><th>CFG</th><th>步数</th><th>采样器</th><th>分辨率起点</th><th>备注</th></tr>
                  <tr v-for="r in paramRows" :key="r.model">
                    <td>{{ r.model }}</td><td>{{ r.cfg }}</td><td>{{ r.steps }}</td>
                    <td>{{ r.sampler }}</td><td>{{ r.res }}</td><td>{{ r.note }}</td>
                  </tr>
                </table>
              </div>
              <div v-if="c.id === 'debug'" class="tbl-wrap">
                <table class="grid-tbl">
                  <tr><th>症状</th><th>原因</th><th>修</th></tr>
                  <tr v-for="r in debugRows" :key="r.sym">
                    <td>{{ r.sym }}</td><td>{{ r.cause }}</td><td>{{ r.fix }}</td>
                  </tr>
                </table>
              </div>
              <div v-if="c.id === 'pose-lib'" class="tbl-wrap">
                <table class="grid-tbl">
                  <tr><th>中文</th><th>标准 tag</th><th>帖数</th><th>SDXL 写法</th><th>Flux 写法</th></tr>
                  <tr v-for="r in poseRows" :key="r.cn + r.tag">
                    <td>{{ r.cn }}</td><td><code class="c">{{ r.tag }}</code></td>
                    <td>{{ r.count }}</td><td><code class="c">{{ r.sdxl }}</code></td><td>{{ r.flux }}</td>
                  </tr>
                </table>
              </div>
              <div v-if="c.id === 'nsfw-pos'" class="tbl-wrap">
                <table class="grid-tbl">
                  <tr><th>中文</th><th>标准 tag</th><th>帖数</th><th>tag 轨写法（SDXL / NovelAI）</th><th>自然语言写法（Tsubaki / 视频）</th></tr>
                  <tr v-for="r in nsfwPosRows" :key="'np' + r.cn">
                    <td>{{ r.cn }}</td><td><code class="c">{{ r.tag }}</code></td>
                    <td>{{ r.count }}</td><td><code class="c">{{ r.sdxl }}</code></td><td>{{ r.nat }}</td>
                  </tr>
                </table>
              </div>
              <div v-if="c.id === 'nsfw-play'" class="tbl-wrap">
                <table class="grid-tbl">
                  <tr><th>中文</th><th>标准 tag</th><th>帖数</th><th>tag 轨写法（SDXL / NovelAI）</th><th>自然语言写法（Tsubaki / 视频）</th></tr>
                  <tr v-for="r in nsfwPlayRows" :key="'nw' + r.cn">
                    <td>{{ r.cn }}</td><td><code class="c">{{ r.tag }}</code></td>
                    <td>{{ r.count }}</td><td><code class="c">{{ r.sdxl }}</code></td><td>{{ r.nat }}</td>
                  </tr>
                </table>
              </div>
              <div class="detail-actions">
                <el-button size="small" @click.stop="copyDetailBody(c)">复制正文</el-button>
                <el-button type="primary" size="small" @click.stop="copyDetailTpl(c)">复制模板</el-button>
                <el-button size="small" @click.stop="openKey = null">收起</el-button>
              </div>
            </div>
          </div>
        </div>
        </el-dialog>
      </div>
    </div>
    <div v-if="filtered.length === 0" class="suli-muted empty">无匹配，换关键词或点清空。</div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { copyText } from '../../utils/clipboard'

const query = ref<string>('')
const active = ref<string>('全部')
const openKey = ref<string | null>(null)
const TRAY_LS = 'suli-nsfw-tray'
let trayInit = true
try { trayInit = localStorage.getItem(TRAY_LS) !== '0' } catch {}
const trayOpen = ref<boolean>(trayInit)
function toggleTray(): void {
  trayOpen.value = !trayOpen.value
  try { localStorage.setItem(TRAY_LS, trayOpen.value ? '1' : '0') } catch {}
}


interface GuideCard { id: string; cat: string; title: string; en: string; tags: string[]; summary: string; body: string; tplKeys: string[]; cover: string }

interface FormulaRow { slot: string; what: string; ex: string }
interface ParamRow { model: string; cfg: string; steps: string; sampler: string; res: string; note: string }
interface DebugRow { sym: string; cause: string; fix: string }
interface PoseRow { cn: string; tag: string; count: string; sdxl: string; flux: string }
interface TplMeta { key: string; title: string }
interface PoseGroup { title: string; sdxlKey: string; fluxKey: string }

const TPL: Record<string, string> = {
  'neg-pony': 'score_4, score_5, score_6, worst quality, low quality, bad anatomy, poorly drawn hands, watermark',
  'neg-ill': 'worst quality, low quality, normal quality, bad anatomy, deformed, watermark, text',
  'neg-sdxl': 'bad anatomy, poorly drawn hands, deformed, plastic skin, watermark',
  'neg-flux': '3-6 词或留空：deformed, extra fingers, watermark, text, low quality',
  't-pony': 'score_9, score_8_up, score_7_up, score_6_up, rating_explicit, source_anime, 1girl, adult, mature female, solo, [pose], [outfit + material], [setting], detailed background, soft lighting, depth of field, masterpiece',
  't-pony-neg': 'score_4, score_5, score_6, child, minor, underage, loli, shota, low quality, worst quality, bad anatomy, poorly drawn hands, watermark, text',
  't-ill': '1girl, adult, mature female, solo, [pose], [outfit], [setting], window light, cinematic lighting, depth of field, anime style, masterpiece, best quality, highres',
  't-ill-neg': 'child, minor, underage, loli, shota, worst quality, low quality, bad anatomy, bad hands, extra digits, watermark, text, jpeg artifacts',
  't-sdxl': '1woman, adult, 27 years old, [pose], looking at viewer, [garment + material], [setting + time], soft window light, rim light, medium shot, 85mm, shallow depth of field, photorealistic, best quality, highly detailed, film grain',
  't-sdxl-neg': 'child, minor, underage, lowres, bad anatomy, bad hands, extra fingers, deformed, plastic skin, watermark, text, jpeg artifacts',
  't-flux': 'A photorealistic medium shot of an adult woman, around 28, [pose] in [setting]. She wears [garment + material]. Soft [morning/evening] light comes through the window with a gentle rim light. Shot on 85mm with shallow depth of field and creamy bokeh.',
  't-flux-neg': 'child, minor, underage, deformed, extra fingers, watermark, text',
  't-pose1': '1woman, adult, solo, standing, contrapposto, hand_on_own_hip, looking at viewer, cowboy_shot',
  't-pose1f': 'A cowboy shot of an adult woman standing in contrapposto with hand on hip, looking at viewer, eye-level 85mm.',
  't-pose2': '1woman, adult, solo, sitting on chair, leaning_forward, hands resting on knees, looking at viewer, upper body',
  't-pose2f': 'An upper-body shot of an adult woman sitting on a chair and leaning forward with hands on knees, looking at viewer.',
  't-pose3': '1woman, adult, solo, full body, squatting, feet flat on ground, contact shadow',
  't-pose3f': 'lying, on_side, full body // Flux: lying on her side, full body, contact shadow',
  't-pose4': '1woman, adult, solo, walking, mid-stride, full body, looking to side',
  't-pose4f': 'Walking mid-stride along a street, coat still swaying // running: dynamic pose with hair in motion',
  't-pose5': '1woman, adult, solo, against_wall, crossed_arms, looking at viewer',
  't-pose5f': 'head_rest, sitting: chin resting on hand // tucking_hair: tucking hair behind ear',
  't-pose6': '2girls, adult, holding_hands, walking, mid-stride, full body',
  't-pose6f': '2girls, back-to-back, crossed_arms // Flux: two women back to back, arms crossed',
  't-pose7': '2girls, adult, hug, looking at viewer, upper body',
  't-pose7f': "arm_around_shoulder // Flux: one arm around the other's shoulder, shoulder-to-shoulder",
}

const formulaRows: FormulaRow[] = [
  { slot: '1 主体 + 成年锚', what: '数量 + 成年标记 + 身份', ex: '1woman, adult, mature female, 27 years old' },
  { slot: '2 动作姿态', what: '全身联动一句话，不堆形容词', ex: 'standing, contrapposto, looking at viewer' },
  { slot: '3 服装状态', what: '材质优先于颜色，状态词节制', ex: 'silk robe, partially open, lace trim' },
  { slot: '4 场景背景', what: '地点 + 时间 + 前后景', ex: 'modern bedroom, blurred background' },
  { slot: '5 光影', what: '方向 + 质地 + 色温', ex: 'soft window light, warm rim light' },
  { slot: '6 镜头', what: '景别 + 焦段 + 景深', ex: 'medium shot, 85mm, shallow depth of field' },
  { slot: '7 风格媒介', what: '只写一个主风格', ex: 'photorealistic / anime style（二选一）' },
  { slot: '8 质量 / score', what: '按模型填', ex: 'Pony 用 score 链；Illustrious 用 masterpiece' },
  { slot: '9 Negative', what: '单独字段，安全词常驻', ex: '见三、四节模板' },
]

const paramRows: ParamRow[] = [
  { model: 'Pony V6', cfg: '6-7（大于 9 必浓浆）', steps: '25-40', sampler: 'Euler a / DPM++ 2M Karras', res: '1024', note: 'CLIP skip 2' },
  { model: 'Illustrious', cfg: '4.5-7.5', steps: '20+（推荐 24）', sampler: 'Euler a / DPM 系', res: '1024，最高 1536', note: '质量词放尾；忌 close-up + upside-down + cowboy shot 混用' },
  { model: 'SDXL 写实', cfg: '7（需锁定时 9）', steps: '25-30', sampler: 'DPM++ 2M Karras（质）/ Euler A（速）', res: '1024 / 832x1216 / 1216x832', note: '忌 LMS / PLMS（解剖差）' },
  { model: 'Flux / SD3.5', cfg: 'Flux 取低 / 3.5 取 4-6', steps: '20-30', sampler: '默认推荐', res: '1024 起，事后超分', note: 'SD1.5 的 CFG 7-9 照搬必过饱和' },
]

const debugRows: DebugRow[] = [
  { sym: '全图平、质感差', cause: 'Pony 缺 score 链 / CLIP skip 错', fix: '补 score_9, score_8_up, score_7_up 起，CLIP skip 2' },
  { sym: '风格串味', cause: 'source 未约束', fix: '正加目标 source，负加不想要的 source' },
  { sym: '手爪、脸崩', cause: 'negative 缺失或过长 + 姿态太模糊', fix: '换短 negative + 权重手词 + 联动姿态重写 + inpaint' },
  { sym: 'Pony 写句子糊了', cause: '语言用错', fix: 'Pony / Illustrious 用 tag；Flux 用整句' },
  { sym: 'score 在 Illustrious 无效', cause: '跨模型标签', fix: '换 masterpiece, best quality' },
  { sym: '蜡皮塑料感', cause: '质量词堆太多', fix: '减质量词，负加 plastic skin, airbrushed，加胶片颗粒' },
  { sym: '年龄漂移显小', cause: '缺成年锚', fix: '正负双锚 + mature，见第四节' },
  { sym: '换模型直接复用糊了', cause: 'SD1.5 prompt 照搬 SDXL / Flux', fix: '按第二节重写，不复制' },
]

const modelTpls: TplMeta[] = [
  { key: 't-pony', title: 'Pony V6（正）' },
  { key: 't-pony-neg', title: 'Pony V6（负）' },
  { key: 't-ill', title: 'Illustrious（正）' },
  { key: 't-ill-neg', title: 'Illustrious（负）' },
  { key: 't-sdxl', title: 'SDXL 写实（正）' },
  { key: 't-sdxl-neg', title: 'SDXL 写实（负）' },
  { key: 't-flux', title: 'Flux / SD3.5（正·整句）' },
  { key: 't-flux-neg', title: 'Flux（负·极短）' },
]

const poseGroups: PoseGroup[] = [
  { title: '站姿叉腰', sdxlKey: 't-pose1', fluxKey: 't-pose1f' },
  { title: '坐 + 前倾', sdxlKey: 't-pose2', fluxKey: 't-pose2f' },
  { title: '蹲 / 躺全身', sdxlKey: 't-pose3', fluxKey: 't-pose3f' },
  { title: '走 / 跑动态', sdxlKey: 't-pose4', fluxKey: 't-pose4f' },
  { title: '靠墙 / 环胸 / 托腮', sdxlKey: 't-pose5', fluxKey: 't-pose5f' },
  { title: '双人：牵手 / 背靠背', sdxlKey: 't-pose6', fluxKey: 't-pose6f' },
  { title: '双人：拥抱 / 搭肩', sdxlKey: 't-pose7', fluxKey: 't-pose7f' },
]

const poseRows: PoseRow[] = [
  { cn: '站立', tag: 'standing', count: '1,338,211', sdxl: 'standing, looking at viewer', flux: 'standing, looking at viewer' },
  { cn: '坐', tag: 'sitting', count: '1,318,715', sdxl: 'sitting on chair', flux: 'sitting on a chair' },
  { cn: '躺（仰 / 侧 / 俯必选一）', tag: 'lying + on_back / on_side / on_stomach', count: '626,419', sdxl: 'lying, on_side, full body', flux: 'lying on her side, full body' },
  { cn: '回眸', tag: 'looking_back', count: '366,409', sdxl: 'looking_back, standing', flux: 'looking back over shoulder' },
  { cn: '手叉腰', tag: 'hand_on_own_hip', count: '230,885', sdxl: 'hand_on_own_hip, contrapposto', flux: 'one hand on her hip in contrapposto' },
  { cn: '前倾', tag: 'leaning_forward', count: '163,979', sdxl: 'leaning_forward, hands resting on knees', flux: 'leaning forward with hands on knees' },
  { cn: '跪 / 单膝跪', tag: 'kneeling / on_one_knee', count: '157,749 / 18,947', sdxl: 'kneeling / on_one_knee', flux: 'kneeling / kneeling on one knee' },
  { cn: '蹲', tag: 'squatting', count: '138,471', sdxl: 'squatting, feet flat, contact shadow', flux: 'squatting with feet flat, contact shadow' },
  { cn: '单腿站', tag: 'standing_on_one_leg', count: '128,024', sdxl: 'standing_on_one_leg', flux: 'standing on one leg' },
  { cn: '鸭子坐', tag: 'wariza', count: '109,398', sdxl: 'wariza, sitting on floor', flux: 'sitting on the floor in wariza' },
  { cn: '正坐', tag: 'seiza', count: '50,345', sdxl: 'seiza', flux: 'sitting in seiza' },
  { cn: '重心偏移站', tag: 'contrapposto', count: '37,807', sdxl: 'contrapposto, cowboy_shot', flux: 'standing in contrapposto, cowboy shot' },
  { cn: '双手背后', tag: 'arms_behind_back', count: '125,679', sdxl: 'standing, arms_behind_back', flux: 'standing with arms behind back' },
  { cn: '环胸', tag: 'crossed_arms', count: '123,319', sdxl: 'crossed_arms, looking at viewer', flux: 'arms crossed, looking at viewer' },
  { cn: '双手抱头后', tag: 'arms_behind_head', count: '73,135', sdxl: 'arms_behind_head, upper body', flux: 'arms behind head, relaxed upper body' },
  { cn: '走', tag: 'walking', count: '54,922', sdxl: 'walking, mid-stride, full body', flux: 'walking mid-stride, full body, coat swaying' },
  { cn: '跑', tag: 'running', count: '45,261', sdxl: 'running, dynamic pose, full body', flux: 'running, dynamic, hair and clothes in motion' },
  { cn: '托腮 / 枕头', tag: 'head_rest', count: '45,426', sdxl: 'head_rest, sitting, upper body', flux: 'chin resting on hand, sitting' },
  { cn: '靠墙', tag: 'against_wall', count: '19,972', sdxl: 'against_wall, leaning, full body', flux: 'leaning against a wall, full body' },
  { cn: '撩发 / 掖发', tag: 'tucking_hair', count: '6,151', sdxl: 'tucking_hair, looking at viewer', flux: 'tucking hair behind ear, looking at viewer' },
  { cn: '双人基数（必前置）', tag: '2girls', count: '1,444,264', sdxl: '2girls, standing side by side', flux: 'two women standing side by side' },
  { cn: '拥抱', tag: 'hug', count: '175,337', sdxl: '2girls, hug, looking at viewer', flux: 'two women hugging, looking at viewer' },
  { cn: '牵手', tag: 'holding_hands', count: '146,904', sdxl: '2girls, holding_hands, walking', flux: 'two women walking hand in hand' },
  { cn: '背靠背', tag: 'back-to-back', count: '22,939', sdxl: '2girls, back-to-back, crossed_arms', flux: 'two women standing back to back, arms crossed' },
  { cn: '抱膝（单人）', tag: 'hugging_own_legs', count: '19,746', sdxl: 'sitting, hugging_own_legs', flux: 'sitting hugging knees' },
  { cn: '搭肩', tag: 'arm_around_shoulder', count: '10,493', sdxl: '2girls, arm_around_shoulder', flux: "one arm around the other's shoulder" },
  { cn: '并肩', tag: 'shoulder-to-shoulder', count: '477', sdxl: '2girls, shoulder-to-shoulder', flux: 'standing shoulder to shoulder' },
]

interface NsfwRow { cn: string; tag: string; count: string; sdxl: string; nat: string }

// 数据源：skills/video/nsfw-directing/references/kb/*.md（2026-10 从 booru wiki 抓取核实）
// 帖数 = post_count；sdxl = tag 轨写法（NovelAI/Pony）；nat = 自然语言轨写法（Tsubaki.3 / PixAI 视频 / Seedream）
const nsfwPosRows: NsfwRow[] = [
  { cn: '骑乘位', tag: 'cowgirl_position', count: '57k', sdxl: 'cowgirl_position, sex, vaginal, penis', nat: 'she straddles him and sinks down slowly, hands braced on his chest' },
  { cn: '背面骑乘位', tag: 'reverse_cowgirl_position', count: '12.5k', sdxl: 'reverse_cowgirl_position, sex, from_behind', nat: 'she rides him facing away, back arched, hands on his knees' },
  { cn: '正常位 / 传教士', tag: 'missionary', count: '50.5k', sdxl: 'missionary, sex, leg_lock', nat: 'they face each other, her legs locked around his waist' },
  { cn: '后入·跪姿', tag: 'doggystyle', count: '43k', sdxl: 'doggystyle, sex, all_fours', nat: 'she kneels on all fours as he takes her from behind, gripping her hip' },
  { cn: '后入（总称）', tag: 'sex_from_behind', count: '110k', sdxl: 'sex_from_behind, sex, bent_over', nat: 'taking her from behind' },
  { cn: '俯卧后入', tag: 'prone_bone', count: '6.8k', sdxl: 'prone_bone, sex, on_stomach', nat: 'she lies flat on her stomach as he presses his weight down on her back' },
  { cn: '侧位', tag: 'spooning', count: '3.8k', sdxl: 'spooning, sex, on_side', nat: 'lying on their sides, he enters her from behind, one arm under her' },
  { cn: '立位靠墙', tag: 'against_wall, standing_sex', count: '20.2k / 24k', sdxl: 'against_wall, standing_sex, leg_up', nat: 'pressed against the wall, one leg lifted and hooked on his arm' },
  { cn: '种付位', tag: 'mating_press', count: '6.5k', sdxl: 'mating_press, sex, leg_up', nat: 'he folds her legs up and presses his whole weight down, kissing her' },
  { cn: '对面座位', tag: 'upright_straddle', count: '8.0k', sdxl: 'upright_straddle, sitting, sex', nat: 'she sits astride him face to face, arms around his neck' },
  { cn: '火车便当', tag: 'suspended_congress', count: '3.2k', sdxl: 'suspended_congress, sex, carrying', nat: 'he holds her up off the ground, legs wrapped around his waist' },
  { cn: '床沿前倾', tag: 'bent_over, on_bed', count: '85.8k', sdxl: 'bent_over, sex, from_behind, on_bed', nat: 'she bends over the bed edge, hands braced, hips lifted' },
  { cn: '口交', tag: 'fellatio', count: '100.5k', sdxl: 'fellatio, oral, penis, saliva', nat: 'she takes his cock into her mouth on her knees' },
  { cn: '深喉', tag: 'deepthroat, fellatio', count: '8.2k', sdxl: 'deepthroat, fellatio, saliva, tears', nat: 'she takes him all the way down, throat bulging, tears at the corner of her eyes' },
  { cn: '被挺入（口内）', tag: 'irrumatio', count: '8.3k', sdxl: 'irrumatio, fellatio, penis', nat: 'he holds the back of her head and thrusts into her mouth' },
  { cn: '舔阴', tag: 'cunnilingus', count: '16.8k', sdxl: 'cunnilingus, oral, pussy, spread_legs', nat: 'his face between her thighs, tongue on her clit, her back arching' },
  { cn: '手交 / 指交', tag: 'handjob / fingering', count: '54k / 48k', sdxl: 'handjob, penis, cum; fingering, pussy_juice', nat: 'her hand wrapped around his shaft, stroking slowly' },
  { cn: '乳交', tag: 'paizuri', count: '61k', sdxl: 'paizuri, breasts, penis, cum_on_breasts', nat: 'his cock between her pressed-together breasts, tip showing' },
  { cn: '腿交 / 素股', tag: 'thigh_sex', count: '5.7k', sdxl: 'thigh_sex, cum_on_thighs', nat: 'she clenches her thighs around his cock, sliding against it' },
  { cn: '足交', tag: 'footjob', count: '11.8k', sdxl: 'footjob, feet, penis', nat: 'her foot slides along the length of his cock' },
  { cn: '自慰', tag: 'female_masturbation', count: '37k', sdxl: 'female_masturbation, spread_legs, pussy_juice', nat: 'her own fingers between her legs, hips lifting' },
  { cn: '颜射 / 内射', tag: 'facial / cum_in_pussy', count: '62k / 147k', sdxl: 'facial, cum, cum_on_face; cum_in_pussy, cumdrip', nat: 'he finishes across her face / deep inside her, then pulls out and cum drips out' },
]

const nsfwPlayRows: NsfwRow[] = [
  { cn: '捆绑', tag: 'bondage, bound', count: '76k / 114k', sdxl: 'bondage, bound, rope', nat: 'silk rope looped around her wrists, loose enough to slip' },
  { cn: '受束（动不了）', tag: 'restrained', count: '72k', sdxl: 'restrained, bound, arms_up', nat: 'her wrists bound above her head, body unable to move' },
  { cn: '绳缚（日式纹样）', tag: 'shibari', count: '25k', sdxl: 'shibari, rope, bondage, crotch_rope', nat: 'interlocking rope pattern across her torso and thighs' },
  { cn: '项圈 / 牵绳', tag: 'collar / leash', count: '—', sdxl: 'collar, leash, kneeling', nat: 'a collar around her neck with the leash in his hand' },
  { cn: '震动器', tag: 'vibrator, sex_toy', count: '33k / 76k', sdxl: 'vibrator, sex_toy, pussy, spread_legs', nat: 'a vibrator pressed against her clit, her thighs trembling' },
  { cn: '假阳具', tag: 'dildo', count: '32k', sdxl: 'dildo, vaginal, object_insertion', nat: 'she rides a suction-cupped dildo' },
  { cn: '肛交', tag: 'anal', count: '76k', sdxl: 'anal, anus, sex, from_behind', nat: 'anal penetration, her hands gripping the sheets' },
  { cn: '肛珠', tag: 'anal_beads', count: '—', sdxl: 'anal_beads, anal, anus', nat: 'a string of beads sliding in one by one' },
  { cn: '3P', tag: 'threesome', count: '45k', sdxl: 'threesome, 1girl, 2boys, group_sex', nat: 'she takes two partners at once, one at each end' },
  { cn: '群交', tag: 'group_sex', count: '84k', sdxl: 'group_sex, multiple_boys, 1girl', nat: 'surrounded by several partners, hands everywhere' },
  { cn: '串刺', tag: 'spitroast', count: '7k', sdxl: 'spitroast, threesome, fellatio, sex', nat: 'one at her mouth, one behind her, both moving together' },
  { cn: '磨阴（女女）', tag: 'tribadism', count: '—', sdxl: 'tribadism, 2girls, pussy, spread_legs', nat: 'two women grinding their pussies together, hands braced' },
  { cn: '露出', tag: 'exhibitionism', count: '11k', sdxl: 'exhibitionism, outdoors, nude', nat: 'exposed in a public place, tense expression, passersby implied' },
  { cn: '内射 / 拔后外流', tag: 'cum_in_pussy / cumdrip', count: '147k / 44k', sdxl: 'cum_in_pussy, sex → cumdrip, cum_string', nat: 'still inside / after he pulls out, cum dripping down her thigh' },
  { cn: '体内溢出', tag: 'cum_overflow', count: '42k', sdxl: 'cum_overflow, sex, cum_in_pussy', nat: 'still inside her, cum spilling out around his cock' },
  { cn: '阿黑颜', tag: 'ahegao, rolling_eyes, tongue_out', count: '29k / 24k / 429k', sdxl: 'ahegao, rolling_eyes, tongue_out, sweat', nat: 'a fucked-silly face, eyes rolled up, tongue out, dripping sweat' },
  { cn: 'NTR 张力', tag: 'netorare', count: '—', sdxl: 'netorare, looking_at_viewer, oral', nat: 'the tension of being taken — 只写张力与知情关系，不写胁迫' },
]

const cats: string[] = ['全部', '九槽公式', '模型分流', 'Negative', '成年合规', '人体修复', '镜头光影', '参数', '翻车对照', '复制模板', '联动', '姿势库', 'NSFW 体位', 'NSFW 玩法']

const cards: GuideCard[] = [
  ...formulaRows.map((r, i): GuideCard => ({
    id: 'f' + (i + 1),
    cat: '九槽公式',
    title: r.slot,
    en: r.what,
    tags: ['九槽公式', '槽' + (i + 1)],
    summary: r.ex,
    body: '写什么：' + r.what + '\n示例：' + r.ex + '\n说明：顺序即权重，重要放前修饰放后；空槽跳过，negative 槽永不跳过。',
    tplKeys: [],
    cover: '槽' + (i + 1),
  })),
  {
    id: 'm-pony', cat: '模型分流', title: 'Pony V6 XL', en: 'tag model',
    tags: ['模型分流', 'Pony', 'tag'], summary: '逗号 tag，score 链开头，CLIP skip 2，CFG 6-7',
    body: '逗号 tag，不写长句。开头必须是 score 链（至少前 3 个）：score_9, score_8_up, score_7_up, score_6_up。rating 必写其一：rating_safe / rating_questionable / rating_explicit。source_anime 等仅 Pony V6 域有效，换 merge 失效就删。CLIP skip 2，CFG 6-7，Euler a / DPM++ 2M Karras，25-40 步，1024 起。V7 弱化 score，改首选 score_8, score_7_up + 自然语言加重。',
    tplKeys: ['t-pony', 't-pony-neg'], cover: 'Pony',
  },
  {
    id: 'm-ill', cat: '模型分流', title: 'Illustrious XL', en: 'danbooru tag',
    tags: ['模型分流', 'Illustrious', 'tag'], summary: '质量词放尾防稀释，tag + 短句混合，CFG 4.5-7.5',
    body: '不用 Pony score。质量词放尾部防稀释：masterpiece, best quality, highres, newest。tag + 短句混合，自然语言理解比 Pony 强。CFG 4.5-7.5（甜点 5.5），24 步起，512-1536 均可。用 explicit / sensitive / general / nsfw / sfw 体系，别混用 Pony rating。',
    tplKeys: ['t-ill', 't-ill-neg'], cover: 'Ill',
  },
  {
    id: 'm-sdxl', cat: '模型分流', title: 'SDXL 写实', en: 'RealVis / Juggernaut',
    tags: ['模型分流', 'SDXL', '写实'], summary: 'tag + 轻自然语言，摄影词有效，CFG 7 左右',
    body: 'tag + 轻自然语言。摄影词有效：RAW photo, 85mm f/1.4, film grain, Kodak Portra 400, volumetric light。CFG 7 左右，DPM++ 2M Karras，原生 1024，肖像 832x1216、横构 1216x832。',
    tplKeys: ['t-sdxl', 't-sdxl-neg'], cover: 'SDXL',
  },
  {
    id: 'm-flux', cat: '模型分流', title: 'Flux / SD3.5', en: 'natural language',
    tags: ['模型分流', 'Flux', '自然语言'], summary: '写整句不写 tag 汤，CFG 取低，negative 极短',
    body: '写整句，不写 tag 汤，质量词可省略。例：A photorealistic medium shot of an adult woman by a window… soft morning light… 85mm, shallow depth of field. CFG Flux 取低、SD3.5 取 4-6。negative 极短或省略。',
    tplKeys: ['t-flux', 't-flux-neg'], cover: 'Flux',
  },
  {
    id: 'n-pony', cat: 'Negative', title: 'Pony 生产 negative', en: 'neg-pony',
    tags: ['Negative', 'Pony'], summary: TPL['neg-pony'],
    body: TPL['neg-pony'] + '\n另按需加 source_furry / source_pony / source_cartoon（只排除不想要的风格）。权重：(bad hands:1.3) 强于堆近义词，上限 1.3-1.4，一次只加权 1-2 个 token。',
    tplKeys: ['neg-pony'], cover: 'Neg',
  },
  {
    id: 'n-ill', cat: 'Negative', title: 'Illustrious 生产 negative', en: 'neg-ill',
    tags: ['Negative', 'Illustrious'], summary: TPL['neg-ill'],
    body: TPL['neg-ill'] + '\n长版才加：lowres, bad hands, extra digits, jpeg artifacts, oldest, early。',
    tplKeys: ['neg-ill'], cover: 'Neg',
  },
  {
    id: 'n-sdxl', cat: 'Negative', title: 'SDXL 写实生产 negative', en: 'neg-sdxl',
    tags: ['Negative', 'SDXL'], summary: TPL['neg-sdxl'],
    body: TPL['neg-sdxl'] + '\n蜡皮加 plastic skin, (airbrushed:1.3)；全身加 extra limbs, (extra arms:1.3)。',
    tplKeys: ['neg-sdxl'], cover: 'Neg',
  },
  {
    id: 'n-flux', cat: 'Negative', title: 'Flux / SD3.5', en: 'neg-flux',
    tags: ['Negative', 'Flux'], summary: TPL['neg-flux'],
    body: TPL['neg-flux'] + '\nFlux 重 positive，negative 过长必降质。手崩优先改描述 + inpaint，不加长 negative。',
    tplKeys: ['neg-flux'], cover: 'Neg',
  },
  {
    id: 'age', cat: '成年合规', title: '成年锚定与平台合规', en: 'adult anchor',
    tags: ['成年合规', '合规', '成年锚'], summary: 'Positive 首槽与 Negative 双锚定成年',
    body: 'Positive 首槽：adult, mature female / mature male, 25-30 years old（三选二，年纪只写 20+ 数字）。Negative 常驻：child, minor, underage, loli, shota, aged_down。漂移年轻等于年龄锚缺失。Illustrious 系 Danbooru 幼态数据多，更要正负双锚，必要时 positive 加 mature。真人、名人、熟人长相一律不写；多人物先单人版验证再加人；文字招牌、手部特写提前预警返工。',
    tplKeys: [], cover: '18+',
  },
  {
    id: 'fix', cat: '人体修复', title: '人体 / 手部修复链', en: 'anatomy fix chain',
    tags: ['人体修复', '手部', 'inpaint'], summary: '不靠重抽靠分步：联动姿态 + 骨架 + inpaint + 先 1K 再超分',
    body: '1 联动姿态：不写 sitting 一个词，写 sitting cross-legged, hands resting on knees, leaning slightly forward。2 锁骨架：全身像上 ControlNet / pose 参考，权重 0.4-0.5。3 Inpaint：只圈手 / 脸，512 裁剪重绘，denoise 0.7-0.85。4 先 1K 定稿再超分到 2K / 4K。5 比例：人像 3:4 / 4:5，场景 16:9。Pony 易过高身形可在 negative 加 long body, long neck。',
    tplKeys: [], cover: '修复',
  },
  {
    id: 'lens', cat: '镜头光影', title: '镜头 / 光影 / 材质', en: 'camera light material',
    tags: ['镜头光影', '镜头', '光影', '材质'], summary: '写清 pose / angle / shot + 方向光 + 材质驱动',
    body: '镜头：每次写清 pose, camera angle, shot size。全身必脚下阴影 + 地平线；半身保留眼位线。光位：顺 / 侧 / 伦勃朗 / 逆 / 轮廓 / 顶 / 底 / 蝴蝶 / 三点。光影：必须写方向 warm light from the left。发丝肩衣轮廓光 + 环境色柔阴影 + 体积雾。材质：silk, lace, wet skin, film grain 比颜色词管用。配色 2-3 主色 + 1 点缀。',
    tplKeys: [], cover: '光影',
  },
  {
    id: 'params', cat: '参数', title: '参数速查', en: 'params / LoRA',
    tags: ['参数', 'CFG', 'LoRA'], summary: 'Pony 6-7 / Ill 4.5-7.5 / SDXL 7 / Flux 取低，弹窗看全表',
    body: 'Pony V6：CFG 6-7，25-40 步，Euler a / DPM++ 2M Karras，1024，CLIP skip 2。Illustrious：CFG 4.5-7.5，20+ 步，1024 最高 1536。SDXL 写实：CFG 7，25-30 步，1024 / 832x1216 / 1216x832。Flux / SD3.5：Flux 取低 / 3.5 取 4-6，20-30 步。LoRA 单权重 0.6-0.8，总量小于 2.0，最多 3 个。弹窗含全量表格。',
    tplKeys: [], cover: '参数',
  },
  {
    id: 'debug', cat: '翻车对照', title: '翻车对照表', en: 'debug table',
    tags: ['翻车对照', 'debug'], summary: '全图平 / 串味 / 手爪 / 蜡皮 / 年龄漂移对照修',
    body: '全图平：补 score_9, score_8_up, score_7_up。串味：正加目标 source 负加不想要的。手爪脸崩：换短 negative + 权重手词 + 联动重写 + inpaint。Pony 写句子糊：换 tag。score 跨模型无效：换 masterpiece。蜡皮：减质量词加胶片颗粒。年龄漂移：正负双锚 + mature。弹窗含全量表格。',
    tplKeys: [], cover: '排错',
  },
  {
    id: 'tpl-lib', cat: '复制模板', title: '复制模板（占位式）', en: 'copy templates',
    tags: ['复制模板', 'prompt', '占位'], summary: 'Pony / Ill / SDXL / Flux 正负 8 模板，中括号自己填',
    body: '模板只给结构与质量词，把 [姿态] / [服装] / [场景] 换成自己的成年虚构设定，年龄与安全词不要删。弹窗列出 8 个正负模板一键复制。',
    tplKeys: modelTpls.map((t): string => t.key), cover: '模板',
  },
  {
    id: 'link', cat: '联动', title: '与本项目联动', en: 'workflow link',
    tags: ['联动', 'STEP'], summary: 'STEP1-6 + 查表顺序，先身份镜头场景再色彩画法',
    body: 'STEP1 身份：先定成年身份再谈服装。STEP2 镜头：姿态 + 机位先冻，透视底另画。STEP3 场景：空背景板必带取景锁。STEP4A/B：只改色彩材质不返工姿态。STEP5/6：统一世界光后 2K 收尾。查表：发色瞳色查配色，服装查服装工具，花主题查花语，机位查构图。二次元吃 tag，写实吃整句。',
    tplKeys: [], cover: '联动',
  },
  {
    id: 'pose-lib', cat: '姿势库', title: '姿势库', en: 'pose library',
    tags: ['姿势库', 'pose', 'tag'], summary: '常用艺术姿势对照 + 7 组 SDXL / Flux 一键复制',
    body: '只收常用艺术姿势。SDXL 用 tag 串，Flux 用整句。躺必写 on_back / on_side / on_stomach 其一；坐必写载体；蹲 / 全身必带脚下阴影；双人必前置 2girls + 站位 + 连接点，先单人版再双人。弹窗含全量对照表 + 7 组一键复制。',
    tplKeys: poseGroups.flatMap((g): string[] => [g.sdxlKey, g.fluxKey]), cover: '姿势',
  },
  {
    id: 'nsfw-pos', cat: 'NSFW 体位', title: 'NSFW 体位表', en: 'nsfw positions',
    tags: ['NSFW 体位', 'sex', 'tag'], summary: '22 条体位 canonical + 帖数 + tag 轨 / 自然语言轨双写法',
    body: '词形从 booru wiki 抓取核实（源：skills/video/nsfw-directing/references/kb/positions-extra.md）。两条避坑：lotus 在 booru 是荷花、69 是 3D 渲染——对坐用 upright_straddle，69 位无可用 tag（用 fellatio + cunnilingus 叠）。自慰女向细化用 female_masturbation。写镜纪律：一镜一事件，锁位 + 接触点 + 反应三件套。',
    tplKeys: [], cover: 'NSFW',
  },
  {
    id: 'nsfw-play', cat: 'NSFW 玩法', title: 'NSFW 玩法 / 道具表', en: 'nsfw play & toys',
    tags: ['NSFW 玩法', 'bondage', 'cum', 'tag'], summary: '17 条玩法/道具/体液 canonical（源头：kb/play.md · kb/anatomy-fluids.md）',
    body: '两条红线：① 只写自愿——多人 / NTR 按知情合意写，不写胁迫（gangbang 的 wiki 别称含贬义措辞，本仓禁用）；② 不写疼痛与伤痕——束缚只写可解状态（loose enough to slip），否则模型画成伤检图。体液互斥：cumdrip 是拔出后、cum_overflow 是仍在体内，别混。penetration / grinding 是歧义 tag，tag 轨别用。',
    tplKeys: [], cover: 'NSFW',
  },
]

const filtered = computed<GuideCard[]>((): GuideCard[] => {
  const q: string = query.value.trim().toLowerCase()
  return cards.filter((c: GuideCard): boolean => {
    if (active.value !== '全部' && c.cat !== active.value) return false
    if (!q) return true
    const hay: string = (c.title + ' ' + c.en + ' ' + c.summary + ' ' + c.body + ' ' + c.tags.join(' ') + ' ' + c.tplKeys.map((k: string): string => TPL[k] ?? '').join(' ')).toLowerCase()
    return hay.includes(q)
  })
})

function isOpen(key: string): boolean {
  return openKey.value === key
}

function toggleDetail(key: string): void {
  openKey.value = openKey.value === key ? null : key
}

function clearFilter(): void {
  query.value = ''
  active.value = '全部'
}

async function onCopy(key: string): Promise<void> {
  const t: string = TPL[key] ?? ''
  if (!t) {
    ElMessage.warning('模板内容为空')
    return
  }
  await copyText(t)
}

async function copyDetailBody(c: GuideCard): Promise<void> {
  const t: string = c.body ?? ''
  if (!t) {
    ElMessage.warning('正文为空')
    return
  }
  await copyText(t)
}

async function copyDetailTpl(c: GuideCard): Promise<void> {
  const keys: string[] = c.tplKeys ?? []
  if (keys.length === 0) {
    await copyDetailBody(c)
    return
  }
  const s: string = keys.map((k: string): string => TPL[k] ?? '').filter((x: string): boolean => x.length > 0).join('\n')
  if (!s) {
    ElMessage.warning('模板内容为空')
    return
  }
  await copyText(s)
}
</script>

<style scoped>
.nsfw-guide {
  --suli-primary: #FB7299;
  --suli-border: #e4e4e7;
  color: var(--suli-text);
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}
.suli-card {
  background: #fff;
  border: 1px solid var(--suli-border);
  border-radius: 10px;
}
.suli-muted { color: #71717a; }
pre.suli-pre {
  white-space: pre-wrap;
  word-break: break-word;
  background: #fafafa;
  border: 1px solid var(--suli-border);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  line-height: 1.6;
}
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.intro { padding: 12px; }
.intro .t { margin: 0 0 6px; font-size: 16px; }
.intro p { margin: 6px 0; font-size: 13px; }
.iron {
  border: 1px solid var(--suli-border);
  border-left: 3px solid var(--suli-primary);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  background: #fff;
}
.tray {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #fff;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.tray-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.search { flex: 1; min-width: 200px; }
.count { font-size: 12px; white-space: nowrap; }
.chips .chip { cursor: pointer; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}
.tool-card {
  padding: 0;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.tool-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(251, 114, 153, 0.18);
}
.tool-card.open { grid-column: span 2; border-color: var(--suli-primary,#FB7299); }
.detail-block { margin-top: 10px; border-top: 1px dashed var(--suli-border); padding-top: 10px; padding-left: 10px; padding-right: 10px; padding-bottom: 10px; }
.detail-cols { display: grid; grid-template-columns: 220px 1fr; gap: 12px; }
.detail-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
@media (max-width: 720px) {
  .detail-cols { grid-template-columns: repeat(auto-fit,minmax(200px,1fr)); }
}
.cover {
  position: relative;
  background: #fdf2f7;
  border-bottom: 1px solid var(--suli-border);
  padding: 14px 10px;
  font-weight: 700;
  font-size: 15px;
  color: var(--suli-primary);
}
.corner {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 11px;
  font-weight: 400;
  background: #fff;
  border: 1px solid var(--suli-border);
  border-radius: 999px;
  padding: 1px 8px;
  color: #71717a;
}
.t { display: flex; flex-direction: column; gap: 2px; padding: 8px 10px 0; }
.t b { font-size: 13.5px; line-height: 1.4; }
.en { font-size: 12px; color: #71717a; }
.pills { display: flex; flex-wrap: wrap; gap: 4px; padding: 6px 10px 0; }
.sum {
  padding: 6px 10px 10px;
  font-size: 12.5px;
  color: #3f3f46;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.empty { padding: 16px; text-align: center; }
.dlg { display: flex; flex-direction: column; gap: 8px; }
.dlg-sub { display: flex; align-items: center; gap: 8px; }
.dlg-sub .en { font-size: 12px; color: #71717a; }
.sum-full { font-size: 13px; margin: 0; }
.tpl-list { display: flex; flex-direction: column; gap: 8px; }
.tpl-item { border-top: 1px dashed var(--suli-border); padding-top: 8px; }
.tpl-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin: 4px 0;
}
.tbl-wrap { overflow-x: auto; margin: 8px 0; }
.grid-tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 12.5px;
  min-width: 520px;
}
.grid-tbl th, .grid-tbl td {
  border: 1px solid var(--suli-border);
  padding: 6px 8px;
  text-align: left;
  vertical-align: top;
}
.grid-tbl th { background: #fafafa; white-space: nowrap; }
.c {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  background: #fafafa;
  border: 1px solid var(--suli-border);
  border-radius: 6px;
  padding: 1px 6px;
  word-break: break-word;
}

@container (max-width: 620px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
  .detail-cols { grid-template-columns: 1fr; }
}
@container (max-width: 400px) {
  .grid { grid-template-columns: 1fr; }
}
/* pack-slots: backpack face */
.tool-card > .pills, .tool-card > .sum { display: none; }
.tool-card > .t { overflow: hidden; }
.tool-card > .t > * { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tool-card.open { box-shadow: 0 0 0 2px rgba(251,114,153,.45), 0 8px 20px rgba(251,114,153,.25); }</style>
