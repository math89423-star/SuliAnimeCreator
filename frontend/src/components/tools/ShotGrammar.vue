<template>
  <div class="shot-tool">
    <div class="tray">
      <div class="tray-inner">
        <el-input v-model="query" size="small" clearable placeholder="搜索" class="search" />
        <div class="filter-chips">
          <el-tag
            v-for="f in FILTERS"
            :key="f.k"
            size="small"
            :effect="active === f.k ? 'dark' : 'plain'"
            class="fchip"
            @click="active = f.k"
          >{{ f.n }}</el-tag>
        </div>
        <span class="suli-muted count">{{ filtered.length }}卡</span>
        <el-button size="small" @click="clearQuery()">清空</el-button>
        <el-button type="primary" size="small" @click="copyAll()">复制组合句{{ picked.length ? '(' + picked.length + ')' : '' }}</el-button>
        <el-button size="small" @click="clearAll()">清空组合</el-button>
        <el-button size="small" text @click="toggleTray">{{ trayOpen ? '收起 ▲' : '展开 ▼' }}</el-button>
      </div>
      <template v-if="trayOpen">
      <div class="picked-row">
        <span class="tray-label">运镜句组合:</span>
        <div class="chips">
          <span v-if="picked.length === 0" class="suli-muted empty-hint">暂无</span>
          <span v-for="(p, i) in picked" :key="p" class="chip">
            <b>{{ shortChip(p) }}</b>
            <span class="chip-x" @click.stop="removeAt(i)">&#215;</span>
          </span>
        </div>
      </div>
      </template>
    </div>

    <div v-if="filtered.length > 0" class="grid">
      <article v-for="d in filtered" :key="d.zh" class="suli-card tool-card" :class="{ open: isOpen(d.zh) }" @click="toggleDetail(d.zh)">
        <div class="cover" v-html="demo(d.dk)"></div>
        <div class="body">
          <div class="title-row">
            <span class="zh">{{ d.zh }}</span>
            <el-tag size="small" effect="plain" class="catchip">{{ catName(d.cat) }}</el-tag>
          </div>
          <div class="en mono">{{ d.en }}</div>
          <div class="pills">
            <el-tag size="small" effect="plain">{{ d.src }}</el-tag>
            <el-tag size="small" :type="confType(d.conf)" effect="light">{{ d.conf }}</el-tag>
          </div>
          <p class="summary suli-muted">{{ d.cn }}</p>
          <el-dialog append-to-body :model-value="isOpen(d.zh)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
            <div class="detail-block">
            <div class="detail-cols">
              <div class="dlg-cover" v-html="demo(d.dk)"></div>
              <div class="dlg-main">
                <div class="dlg-title-row">
                  <span class="zh">{{ d.zh }}</span>
                  <el-tag size="small" effect="plain">{{ catName(d.cat) }}</el-tag>
                </div>
                <pre class="suli-pre mono">{{ d.en }}</pre>
                <p class="dlg-cn">{{ d.cn }}</p>
                <p class="dlg-use">▸ {{ d.use }}</p>
                <div class="pills">
                  <el-tag size="small" effect="plain">{{ d.src }}</el-tag>
                  <el-tag size="small" :type="confType(d.conf)" effect="light">{{ d.conf }}</el-tag>
                </div>
              </div>
            </div>
            <div class="film">真片：{{ filmOf(d.dk).t }}<a :href="filmOf(d.dk).u" target="_blank" rel="noopener" @click.stop>看真实演示 →</a></div>
            <div class="fullbox">
              <div class="fullname">完整视频prompt（5s可投喂）</div>
              <pre class="suli-pre mono">{{ fullOf(d).en }} {{ fullOf(d).snd }}</pre>
              <div class="fullcn">{{ fullOf(d).cn }}</div>
            </div>
            <div class="detail-actions">
              <el-button size="small" @click.stop="copyEn(d)">复制英文句</el-button>
              <el-button size="small" @click.stop="addPicked(d)">加入组合</el-button>
              <el-button size="small" type="primary" @click.stop="copyFullActive(d)">复制完整prompt</el-button>
              <el-button size="small" @click.stop="openKey = null">收起</el-button>
            </div>
          </div>
        </el-dialog>
        </div>
      </article>
    </div>
    <p v-else class="suli-muted empty">无匹配卡片，换关键词或点清空重试。</p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { copyText } from '../../utils/clipboard'

interface ShotItem {
  cat: string
  zh: string
  en: string
  cn: string
  use: string
  src: string
  conf: string
  dk: string
}

interface FullPrompt {
  en: string
  cn: string
  snd: string
}

/* ---------- SVG 图解（源文件函数原样搬运，v-html 渲染） ---------- */
const INK = '#4a4238'
const RED = '#c0392b'
const FILL = '#e9e2d6'
const TXT = '#8d8173'
const GRID = '#cfc7b8'

function svgW(inner: string): string {
  return `<svg viewBox="0 0 220 132" xmlns="http://www.w3.org/2000/svg" class="dia">${inner}</svg>`
}
function txt(t: string, x: number, y: number, s = 9.5): string {
  return `<text x="${x}" y="${y}" font-size="${s}" fill="${TXT}" font-family="sans-serif">${t}</text>`
}
function fig(cx: number, cy: number, s = 0.62): string {
  return `<g transform="translate(${cx},${cy}) scale(${s})" stroke="${INK}" stroke-width="2.4" fill="${FILL}"><circle cx="0" cy="-40" r="10"/><path d="M-8 -24 Q0 -31 8 -24 L6 8 L-6 8 Z"/><path d="M-7 -22 L-13 6 M7 -22 L13 6"/><path d="M-3.5 8 L-4.5 50 M3.5 8 L4.5 50"/></g>`
}
function camera(x: number, y: number): string {
  return `<g transform="translate(${x},${y})"><rect x="-13" y="-8" width="23" height="15" rx="3" fill="#fff" stroke="${INK}" stroke-width="1.6"/><circle cx="8" cy="0" r="4.5" fill="${RED}" opacity=".85"/></g>`
}
function dot(path: string, dur = '1.8s'): string {
  return `<circle r="4.2" fill="${RED}" opacity=".9"><animateMotion path="${path}" dur="${dur}" repeatCount="indefinite"/></circle>`
}
function arrow(path: string): string {
  return `<path d="${path}" fill="none" stroke="${RED}" stroke-width="1.8" stroke-dasharray="5 3" marker-end="url(#arw)"/>`
}
const DEFS = `<defs><marker id="arw" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6 Z" fill="${RED}"/></marker></defs>`

function demo(kind: string): string {
  const g = `<line x1="14" y1="114" x2="206" y2="114" stroke="${INK}" stroke-width="1.4"/>`
  switch (kind) {
    case 'push': return svgW(DEFS + g + fig(130, 66) + camera(40, 60) + arrow('M52 60 L104 60') + dot('M52 60 L104 60') + txt('push in 相机前进·背景视差', 14, 18))
    case 'pull': return svgW(DEFS + g + fig(90, 66, 0.5) + camera(120, 60) + arrow('M108 60 L56 60') + dot('M108 60 L56 60') + txt('pull out 相机后退·交代环境', 14, 18))
    case 'zoomin': return svgW(DEFS + `<rect x="60" y="20" width="100" height="80" fill="none" stroke="${GRID}" stroke-width="1.4"/><rect x="85" y="38" width="50" height="44" fill="none" stroke="${RED}" stroke-width="1.8"/>` + dot('M60 20 L85 38') + txt('zoom in 机位不动·只变焦', 14, 122))
    case 'zoomout': return svgW(DEFS + `<rect x="85" y="38" width="50" height="44" fill="none" stroke="${GRID}" stroke-width="1.4"/><rect x="60" y="20" width="100" height="80" fill="none" stroke="${RED}" stroke-width="1.8"/>` + dot('M85 38 L60 20') + txt('zoom out 机位不动·只变焦', 14, 122))
    case 'panL': return svgW(DEFS + g + fig(110, 66) + camera(110, 96) + `<path d="M96 88 A22 22 0 0 1 70 70" fill="none" stroke="${RED}" stroke-width="1.8" marker-end="url(#arw)"/>` + dot('M96 88 A22 22 0 0 1 70 70') + txt('pan left 原地水平左转', 14, 18))
    case 'panR': return svgW(DEFS + g + fig(110, 66) + camera(110, 96) + `<path d="M124 88 A22 22 0 0 0 150 70" fill="none" stroke="${RED}" stroke-width="1.8" marker-end="url(#arw)"/>` + dot('M124 88 A22 22 0 0 0 150 70') + txt('pan right 原地水平右转', 14, 18))
    case 'truckL': return svgW(DEFS + g + fig(110, 66) + camera(150, 60) + arrow('M150 44 L70 44') + dot('M150 44 L70 44') + txt('truck left 整机左移·有视差', 14, 18))
    case 'truckR': return svgW(DEFS + g + fig(110, 66) + camera(70, 60) + arrow('M70 44 L150 44') + dot('M70 44 L150 44') + txt('truck right 整机右移·有视差', 14, 18))
    case 'tiltU': return svgW(DEFS + g + fig(120, 62, 0.7) + camera(50, 90) + `<path d="M60 80 A24 24 0 0 1 66 52" fill="none" stroke="${RED}" stroke-width="1.8" marker-end="url(#arw)"/>` + dot('M60 80 A24 24 0 0 1 66 52') + txt('tilt up 原地仰·揭示高度', 14, 18))
    case 'tiltD': return svgW(DEFS + g + fig(120, 62, 0.7) + camera(50, 50) + `<path d="M60 60 A24 24 0 0 0 66 88" fill="none" stroke="${RED}" stroke-width="1.8" marker-end="url(#arw)"/>` + dot('M60 60 A24 24 0 0 0 66 88') + txt('tilt down 原地俯·从上往下', 14, 18))
    case 'pedU': return svgW(DEFS + camera(50, 100) + arrow('M50 100 L50 40') + dot('M50 100 L50 40') + fig(140, 66) + txt('pedestal up 整机上升', 14, 18))
    case 'pedD': return svgW(DEFS + camera(50, 40) + arrow('M50 40 L50 100') + dot('M50 40 L50 100') + fig(140, 66) + txt('pedestal down 整机下降', 14, 18))
    case 'arc': return svgW(DEFS + fig(110, 70, 0.6) + `<path d="M50 100 A70 40 0 0 1 170 100" fill="none" stroke="${RED}" stroke-width="1.8" stroke-dasharray="5 3"/>` + dot('M50 100 A70 40 0 0 1 170 100', '2.4s') + camera(50, 100) + txt('arc 环绕·5s只转180°', 14, 18))
    case 'track': return svgW(DEFS + g + fig(90, 66, 0.6) + fig(140, 66, 0.6) + arrow('M40 44 L180 44') + dot('M40 44 L180 44') + txt('tracking 跟随主体平移', 14, 18))
    case 'static': return svgW(DEFS + g + fig(110, 66) + camera(40, 60) + `<line x1="52" y1="60" x2="80" y2="60" stroke="${GRID}" stroke-width="2" stroke-dasharray="3 3"/>` + txt('static 锁死·只许首尾≤2s', 14, 18))
    case 'shakeS': return svgW(DEFS + g + fig(110, 66) + camera(50, 60) + `<path d="M58 54 l6 4 l-6 4 l6 4" fill="none" stroke="${RED}" stroke-width="1.6"/>` + txt('shake slightly 轻抖·呼吸感', 14, 18))
    case 'shakeB': return svgW(DEFS + g + fig(110, 66) + camera(50, 60) + `<path d="M58 50 l10 6 l-10 6 l10 6 l-10 6" fill="none" stroke="${RED}" stroke-width="1.8"/>` + txt('shake strongly 重抖·慎用', 14, 18))
    case 'pov': return svgW(DEFS + `<path d="M110 118 L50 20 L170 20 Z" fill="rgba(192,57,43,.07)" stroke="${RED}" stroke-width="1.4" stroke-dasharray="5 4"/>` + fig(110, 60, 0.4) + arrow('M110 110 L110 50') + dot('M110 110 L110 50') + txt('POV=角色眼睛·须身体入画', 14, 124))
    case 'rollC': return svgW(DEFS + `<rect x="70" y="30" width="80" height="60" fill="none" stroke="${INK}" stroke-width="1.6"/><g><animateTransform attributeName="transform" type="rotate" from="0 110 60" to="360 110 60" dur="3s" repeatCount="indefinite"/><rect x="70" y="30" width="80" height="60" fill="none" stroke="${RED}" stroke-width="1.8"/></g>` + txt('roll clockwise 绕镜头轴转', 14, 18))
    case 'rollCC': return svgW(DEFS + `<rect x="70" y="30" width="80" height="60" fill="none" stroke="${INK}" stroke-width="1.6"/><g><animateTransform attributeName="transform" type="rotate" from="360 110 60" to="0 110 60" dur="3s" repeatCount="indefinite"/><rect x="70" y="30" width="80" height="60" fill="none" stroke="${RED}" stroke-width="1.8"/></g>` + txt('roll 逆时针·眩晕慎用', 14, 18))
    case 'dollyzoom': return svgW(DEFS + fig(110, 70, 0.55) + arrow('M50 100 L90 80') + arrow('M170 30 L130 50') + txt('dolly zoom 机进+镜出·背景拉伸', 14, 18))
    case 'crash': return svgW(DEFS + g + fig(120, 66, 0.7) + camera(40, 60) + arrow('M52 60 L100 60') + dot('M52 60 L100 60', '0.7s') + txt('crash zoom 急推·一集一次', 14, 18))
    case 'whip': return svgW(DEFS + `<rect x="30" y="40" width="60" height="50" fill="none" stroke="${GRID}" stroke-width="1.4"/><rect x="130" y="40" width="60" height="50" fill="none" stroke="${RED}" stroke-width="1.8"/>` + arrow('M90 65 L130 65') + dot('M90 65 L130 65', '0.6s') + txt('whip pan 快甩·必带motion blur', 14, 122))
    case 'fpv': return svgW(DEFS + `<path d="M20 100 C70 80 90 60 120 55 S180 40 200 30" fill="none" stroke="${RED}" stroke-width="1.8" stroke-dasharray="5 3"/>` + dot('M20 100 C70 80 90 60 120 55 S180 40 200 30', '2s') + txt('FPV 穿行·航点三站缺一乱飞', 14, 122))
    case 'dive': return svgW(DEFS + camera(110, 20) + arrow('M110 30 L110 95') + dot('M110 30 L110 95') + fig(110, 100, 0.5) + txt('dive 高速俯冲+急停', 14, 122))
    case 'crane': return svgW(DEFS + camera(50, 100) + arrow('M50 100 L50 35') + dot('M50 100 L50 35', '2.2s') + fig(150, 80, 0.5) + txt('crane 起点越低落差越大', 14, 18))
    case 'cut': return svgW(DEFS + `<rect x="24" y="34" width="80" height="56" fill="none" stroke="${GRID}" stroke-width="1.5"/>` + txt('A', 60, 62, 12) + `<rect x="118" y="34" width="80" height="56" fill="none" stroke="${RED}" stroke-width="1.8"/>` + txt('B', 154, 62, 12) + arrow('M104 62 L118 62') + txt('硬切·切点带新信息', 60, 112))
    default: return svgW(DEFS + g + fig(110, 66) + camera(40, 60) + arrow('M52 60 L100 60') + dot('M52 60 L100 60') + txt(kind, 14, 18))
  }
}

/* ---------- 分类 / 数据（源文件 DATA 一条不丢，共 102 条） ---------- */
const CATS: Array<[string, string]> = [
  ['move', '运镜·H3官方20'],
  ['adv', '高级运镜·社区'],
  ['cut', '切镜语法'],
  ['rhy', '节奏与预算'],
  ['still', '静态高级·搬运'],
  ['anti', '反模式'],
  ['tpl', 'H3句式模板'],
]

const FILTERS: Array<{ k: string; n: string }> = [
  { k: 'all', n: '全部' },
  { k: 'move', n: '运镜20' },
  { k: 'adv', n: '高级' },
  { k: 'cut', n: '切镜' },
  { k: 'rhy', n: '节奏' },
  { k: 'still', n: '静态' },
  { k: 'anti', n: '反模式' },
  { k: 'tpl', n: '模板' },
]

const DATA: ShotItem[] = [
  { cat: 'move', zh: '前推逼近 push in', en: 'The camera pushes in with small amplitude at slow speed toward the folded letter in her hands.', cn: '镜头以小幅慢速前推，落在她手中的折信上。', use: '动因=逼近；压力累积最稳的一招，不确定就用它。', src: 'H3官方§4.3原句', conf: '已验证', dk: 'push' },
  { cat: 'move', zh: '后拉揭示 pull out', en: 'The camera pulls out with small amplitude at slow speed, revealing the full room around her.', cn: '镜头小幅慢速后拉，露出她身后完整房间。', use: '动因=释放；结尾交代空间用。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'pull' },
  { cat: 'move', zh: '变焦进 zoom in', en: 'The camera zooms in at slow speed toward her eyes, the camera body stays still.', cn: '镜头机位不动、缓慢变焦，落在她的眼睛上。', use: '机位不动只变焦；无视差，和push观感不同。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'zoomin' },
  { cat: 'move', zh: '变焦出 zoom out', en: 'The camera zooms out at slow speed, revealing the street beyond the window.', cn: '镜头机位不动、缓慢拉开变焦，露出窗外街道。', use: '机位不动；揭示环境但无行走感。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'zoomout' },
  { cat: 'move', zh: '左摇 pan left', en: 'The camera pans left at slow speed, following her as she crosses the room.', cn: '镜头原地向左慢摇，跟住她穿过房间。', use: '原地转；跟横向动作，不搬机位。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'panL' },
  { cat: 'move', zh: '右摇 pan right', en: 'The camera pans right with large amplitude at fast speed, revealing the open doorway.', cn: '镜头大幅快速右摇，带出敞开的门。', use: 'H3官方原句；揭示门/新人物用。', src: 'H3官方§4.3原句', conf: '已验证', dk: 'panR' },
  { cat: 'move', zh: '左移 truck left', en: 'The camera trucks left with small amplitude at slow speed beside the cyclist.', cn: '镜头在骑行者身侧小幅慢速左移。', use: '整机平移有视差；别和pan混。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'truckL' },
  { cat: 'move', zh: '右移 truck right', en: 'The camera trucks right with small amplitude at slow speed as she lifts her gaze toward the city lights.', cn: '镜头小幅慢速右移，她抬头看向城市灯火。', use: 'H3官方I2VA例文句式；跟随+揭示。', src: 'H3官方§4.3例文', conf: '已验证', dk: 'truckR' },
  { cat: 'move', zh: '上摇 tilt up', en: 'The camera tilts up at slow speed from her shoes to her face.', cn: '镜头从她的鞋慢速上摇到脸。', use: '揭示高度/从产品到脸；Kling官方同款。', src: 'H3+Kling官方', conf: '已验证', dk: 'tiltU' },
  { cat: 'move', zh: '下摇 tilt down', en: 'The camera tilts down at slow speed from the tower top to the gate.', cn: '镜头从塔顶慢速下摇到大门。', use: '交代高大建筑/从上往下。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'tiltD' },
  { cat: 'move', zh: '升机 pedestal up', en: 'The camera pedestals up at slow speed, rising from the table to her face.', cn: '整机慢速上升，从桌面升到她的脸。', use: '整机垂直升降；crane的短版。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'pedU' },
  { cat: 'move', zh: '降机 pedestal down', en: 'The camera pedestals down at slow speed, settling to the letter on the table.', cn: '整机慢速下降，落在桌上信件。', use: '垂直落幅到道具。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'pedD' },
  { cat: 'move', zh: '环绕 arc', en: 'The camera arcs around the subject with small amplitude at slow speed.', cn: '镜头小幅慢速环绕主体。', use: '5s只转180°；转360°必穿模。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'arc' },
  { cat: 'move', zh: '跟踪 tracking', en: 'The camera tracks the subject at slow speed as she walks through the corridor.', cn: '镜头慢速跟随她穿过走廊。', use: '跟走路的人；和主体同速。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'track' },
  { cat: 'move', zh: '静止 static', en: 'The camera holds a static shot as the runner exits the frame.', cn: '镜头锁死静止，跑者跑出画框。', use: 'H3官方原句；只许首尾定格≤2s。', src: 'H3官方§4.3原句', conf: '已验证', dk: 'static' },
  { cat: 'move', zh: '轻抖 shake slightly', en: 'The camera shakes slightly as she runs down the stairs.', cn: '她跑下楼梯时镜头轻微抖动。', use: '呼吸感/手持；次级运动不占主运镜。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'shakeS' },
  { cat: 'move', zh: '重抖 shake strongly', en: 'The camera shakes strongly as the blast hits.', cn: '冲击波袭来时镜头剧烈抖动。', use: '惊变专用；日常慎用。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'shakeB' },
  { cat: 'move', zh: '主观 POV', en: "The camera holds the subject's point of view as she sprints forward, arms at the frame edges.", cn: '镜头即她的主观视角向前冲，双臂在画面边缘。', use: '必写身体入画，否则成空飞。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'pov' },
  { cat: 'move', zh: '顺时针滚 roll C', en: 'The camera rolls clockwise with small amplitude, ending on her face.', cn: '镜头小幅顺时针滚转，落在她脸上。', use: '眩晕/梦境；幅度必小。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'rollC' },
  { cat: 'move', zh: '逆时针滚 roll CC', en: 'The camera rolls counterclockwise with small amplitude.', cn: '镜头小幅逆时针滚转。', use: '同上，反向。', src: 'H3官方§4.3词表', conf: '已验证', dk: 'rollCC' },
  { cat: 'adv', zh: '希区柯克 dolly zoom', en: 'Dolly back while zooming in on her shocked face, subject size constant, background stretches.', cn: '机位后拉同时变焦推进，她脸大小不变、背景被拉伸。', use: '心理惊变；双向写全，Seedance最稳。', src: 'Seedance官方8式', conf: '待复测', dk: 'dollyzoom' },
  { cat: 'adv', zh: '急推 crash zoom', en: 'The camera crash-zooms onto the cross in her hands at fast speed.', cn: '镜头急速推到她手中的十字架上。', use: '一集最多一次；落幅必须是新信息。', src: 'Kling Masterclass', conf: '待复测', dk: 'crash' },
  { cat: 'adv', zh: '快甩 whip pan', en: 'The camera whips right with motion blur from her face to the open door.', cn: '镜头从她的脸向右快甩，带动态模糊到敞开的门。', use: 'A→B同轴；blur必写。', src: 'Seedance+Kling', conf: '待复测', dk: 'whip' },
  { cat: 'adv', zh: 'FPV穿行', en: 'Aggressive FPV flight threading through the corridor, banking past the pillars, bursting into the hall.', cn: 'FPV穿走廊、掠过柱子、冲进大厅。', use: '航点through→past→into三站写全。', src: 'Seedance社区', conf: '未实测', dk: 'fpv' },
  { cat: 'adv', zh: '俯冲 dive', en: 'High-speed vertical dive from the tower top straight down toward her, ending in a sudden hover.', cn: '从塔顶高速垂直俯冲向她，终点急停悬住。', use: '起点终点+急停缺一穿模。', src: 'Kling Masterclass', conf: '未实测', dk: 'dive' },
  { cat: 'adv', zh: '升降 crane', en: 'The camera rises from the ground to high above, revealing the courtyard.', cn: '镜头从地面升到高空，露出庭院。', use: '起点越低落差越大。', src: 'Kling Masterclass', conf: '待复测', dk: 'crane' },
  { cat: 'adv', zh: '手持呼吸 handheld', en: 'Handheld framing with a small amount of natural sway, slow push in.', cn: '手持构图带轻微自然晃动，慢推。', use: '别写shaky，要写sway；UGC感。', src: 'VIDEOAI社区', conf: '待复测', dk: 'shakeS' },
  { cat: 'adv', zh: '低位跟踪 low track', en: 'A low tracking shot follows the paper boat at water level at slow speed.', cn: '低位镜头贴水面慢速跟踪纸船。', use: '跟宠物/船/脚步用。', src: 'Seedance社区', conf: '待复测', dk: 'track' },
  { cat: 'adv', zh: '全环绕360 full orbit', en: 'The camera orbits a full 360 degrees around them at steady speed, radius constant.', cn: '镜头匀速绕他们一整圈，半径不变。', use: '只用于5s+或双人对峙；5s内360必穿模，先用arc180。', src: 'StudioBinder arc（Dark Knight全周）', conf: '待复测', dk: 'arc' },
  { cat: 'adv', zh: '机械臂 Mo-cap rig', en: 'Robotic-arm motion control: fast lateral passes with snappy accelerations, hard stops, zero shake, face locked stable.', cn: '机械臂式：快速横移+脆加速+硬停，零抖动，脸锁稳。', use: 'Kling Masterclass真机章；脸稳是验收线。', src: 'Kling Masterclass', conf: '待复测', dk: 'truckR' },
  { cat: 'adv', zh: '自拍 framing selfie', en: "Selfie framing at arm's length, slight natural sway, face stable in the upper third.", cn: '手臂长度自拍构图，轻微自然晃，脸稳在上三分之一。', use: 'UGC双签名之一；自带手持感，不另加shake。', src: 'VIDEOAI社区', conf: '待复测', dk: 'shakeS' },
  { cat: 'adv', zh: '前跟 track forward', en: 'The camera tracks forward at her walking pace, distance constant, horizon stable.', cn: '镜头以她步速前跟，距离不变，地平线稳。', use: '跟走路/跑步；别加zoom。', src: 'Kling官方tracking', conf: '待复测', dk: 'track' },
  { cat: 'adv', zh: '侧视差 parallax lateral', en: 'The camera trucks sideways past the foreground pillars, mid-ground subject sharp, background sliding.', cn: '镜头横移掠过前景柱子，中景主体清晰，背景滑动。', use: '前景必须有东西可掠；平地空景别用。', src: 'Seedance社区', conf: '未实测', dk: 'truckL' },
  { cat: 'adv', zh: '推仰复合 dolly+tilt', en: 'Slow dolly forward while tilting up from the shoes to the face.', cn: '慢推同时上摇，从鞋到脸。', use: '复合只许两轴；三轴必拆。', src: 'Seedance复合句式', conf: '未实测', dk: 'tiltU' },
  { cat: 'adv', zh: '长焦压缩 telephoto', en: 'Shot on 85mm, background compressed behind her, shallow depth of field.', cn: '85mm长焦，背景压在她身后，浅景深。', use: '街灯/人群压成一叠；脸最讨喜。', src: 'StudioBinder镜头篇', conf: '待复测', dk: 'zoomin' },
  { cat: 'adv', zh: '广角拉伸 wide', en: 'Shot on 24mm low angle, stride foreshortened huge, ground tilted a few degrees.', cn: '24mm低机位广角，跨步近大远小拉得巨大，地面微斜。', use: '先读速度再读脸；脸别一起拉。', src: 'StudioBinder镜头篇', conf: '待复测', dk: 'pov' },
  { cat: 'cut', zh: '180度线', en: 'Both cameras stay on the same side of the A-B axis, she is frame-left facing right.', cn: '两机位全在AB轴同侧，她在左框朝右。', use: '双人必写左右+朝向锁轴。', src: 'StudioBinder', conf: '已验证', dk: 'cut' },
  { cat: 'cut', zh: '正反打', en: 'Shot-reverse-shot, same side of the axis, framing one step apart, eyelines mirrored.', cn: '正反打，同侧轴线，景别差一档，视线互反。', use: '对话≥2轮必分镜切。', src: 'StudioBinder', conf: '已验证', dk: 'cut' },
  { cat: 'cut', zh: '视线匹配', en: 'She looks off-frame right; cut to the statue knees on the image-right edge.', cn: '她看向画外右；切到画面右缘的神像膝盖。', use: 'A看右→B从左回看。', src: 'StudioBinder', conf: '已验证', dk: 'cut' },
  { cat: 'cut', zh: '动作匹配', en: 'Cut on the midpoint of her head-turn, the next shot completes the turn.', cn: '在她转头中点切，下一镜接完转头。', use: '切点落动作中点。', src: 'StudioBinder', conf: '已验证', dk: 'cut' },
  { cat: 'cut', zh: '对话切', en: '[Shot 2] At 00:03.500, cut to the reverse angle as his line ends and she reacts.', cn: '00:03.5切反打，他话音落、她反应。', use: '切点落尾音；反应延迟0.3-0.5s。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'cut', zh: '动作反应拆', en: 'Action shot: the window rattles harder; reaction shot: she turns in panic.', cn: '动作镜：窗颤升级；反应镜：她惊慌转头。', use: '环境异动+人物反应必拆两切。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'cut', zh: '双轴对齐', en: 'story_time: window escalates 1-3s; camera_time: 0-1s her, 1-3s window, 3-5s her with rattle continuing.', cn: '世界轴窗1-3s升级；镜头轴0-1她、1-3窗、3-5她（窗颤延续）。', use: '切点两侧世界状态相等。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'cut', zh: 'J-cut', en: 'Her next line enters under the end of Shot 1, 0.5s before the cut.', cn: '她下句台词提前0.5s压进上一镜尾。', use: '声音先进画面，H3前三式可写。', src: 'StudioBinder转场', conf: '待复测', dk: 'cut' },
  { cat: 'cut', zh: '声音桥', en: 'Choir hum carries across the cut without breaking.', cn: '唱诗班低鸣不断，横跨切点。', use: '声过切点不断。', src: 'StudioBinder转场', conf: '待复测', dk: 'cut' },
  { cat: 'cut', zh: '图形匹配', en: 'Cut from the round window to her round pupil, shapes matched.', cn: '从圆形花窗切到她的圆形瞳孔，形对形。', use: '关键帧预埋同形。', src: 'StudioBinder转场', conf: '未实测', dk: 'cut' },
  { cat: 'cut', zh: '前景穿越', en: 'The camera pushes past the pillar, emerging on her face.', cn: '镜头掠过柱子（前景擦除），落在她脸上。', use: '柱/衣褶划过=天然擦除。', src: '本项目固化', conf: '待复测', dk: 'cut' },
  { cat: 'cut', zh: '景别拉档', en: 'Cut from medium-wide to close-up on the same side, one step tighter.', cn: '同侧从中景切近景，紧一档。', use: '正反切景别差一档。', src: 'StudioBinder', conf: '已验证', dk: 'cut' },
  { cat: 'cut', zh: '30度规则', en: 'The cut shifts the angle by more than 30 degrees, same subject, new information in frame.', cn: '切镜夹角超30度，同主体，框内有新信息。', use: '小于30°像跳帧；不够就拉大景别差。', src: 'StudioBinder剪辑', conf: '待复测', dk: 'cut' },
  { cat: 'cut', zh: '越轴警告 crossing', en: 'Crossing the axis flips her from frame-left to frame-right; do not cross without a neutral insert.', cn: '越轴会让她从左框跳右框；无中性镜头别越。', use: '双人必守；乱了加俯瞰/插入全景洗轴。', src: 'StudioBinder 180线', conf: '已验证', dk: 'cut' },
  { cat: 'cut', zh: '主观剪 POV cut', en: 'She looks off-frame; cut to her optical POV rushing forward, then cut back to her reaction.', cn: '她看画外；切她的主观前冲；再切回她反应。', use: '看→所见→反应三段；POV须身体入画。', src: 'StudioBinder POV', conf: '待复测', dk: 'pov' },
  { cat: 'cut', zh: '蒙太奇 montage', en: 'Rapid montage: hands, strap, door, face, each under 1s, beat-synced.', cn: '快剪蒙太奇：手、包带、门、脸，每镜1s内，卡点。', use: '一镜一信息；H3内至多2-3切。', src: 'StudioBinder剪辑', conf: '未实测', dk: 'cut' },
  { cat: 'cut', zh: '淡入淡出 fade', en: 'Fade in from black / fade out to black between sequences.', cn: '段落之间黑场淡入/淡出。', use: '叠化后期做，不进H3 prompt；H3只写硬切。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'cut', zh: '卡点剪 on beat', en: 'Cut exactly on the beat drop, motion landing with the drum hit.', cn: '切点落在鼓点上，动作落幅和鼓齐。', use: 'whip/动作匹配优先卡点。', src: 'Seedance社区', conf: '待复测', dk: 'whip' },
  { cat: 'rhy', zh: '一镜一运镜', en: 'One shot, one camera move tied to one reveal.', cn: '一镜只给一个运镜，绑定一个揭示。', use: '无动因的运镜不写。', src: 'H3+Kling官方', conf: '已验证', dk: 'static' },
  { cat: 'rhy', zh: '四段式运镜句', en: 'Slow push in as she turns, revealing the door, pressure builds.', cn: '慢推+她转身+带出门+压力累积。', use: '运镜+主体+揭示+情绪，缺落点=漂。', src: '本项目固化', conf: '已验证', dk: 'push' },
  { cat: 'rhy', zh: '落幅必写', en: 'The camera pushes in, ending on the cross in her hands.', cn: '前推，落在她手中的十字架上。', use: 'reveal/ending on必填。', src: 'H3官方', conf: '已验证', dk: 'push' },
  { cat: 'rhy', zh: '幅度速度', en: 'with small amplitude at slow speed / with large amplitude at fast speed.', cn: '小幅慢速（累积）/大幅快速（惊变）。', use: '中幅常速省略。', src: 'H3官方§4.3', conf: '已验证', dk: 'push' },
  { cat: 'rhy', zh: 'push连用禁令', en: 'No more than two push-ins in a row; the third shot must reverse.', cn: 'push连用不超2镜，第3镜必换向。', use: '防审美疲劳。', src: '本项目固化', conf: '待复测', dk: 'pull' },
  { cat: 'rhy', zh: 'motion budget', en: 'One subject move + one camera move + one environment move per shot.', cn: '一镜=一主体动作+一运镜+一环境动。', use: '超预算强制拆镜。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'rhy', zh: '时长5s铁律', en: 'Hold a fully static frame after the action until 5.00s for trimming.', cn: '动作完后静止保持到5s，留裁剪余量。', use: 'H3最低5s；内容不足写hold。', src: '本项目固化', conf: '已验证', dk: 'static' },
  { cat: 'rhy', zh: '三振换镜', en: 'After 3 failed pulls on the same setup, change the shot, not the words.', cn: '同一镜连败3次就换镜，不改第4遍词。', use: '缩短/拉近/拆半/降级。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'rhy', zh: '首尾帧可达', en: 'Small change 5s, big change 10s; unreachable states get a middle frame.', cn: '小变5s大变10s；到不了加中间帧。', use: '正面坐→背面奔不硬插。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'rhy', zh: '静帧稳再转视频', en: 'Lock the keyframe before running video; bad boards get no video.', cn: '冻住关键帧再跑视频；废分镜不做视频。', use: '3s空镜例外。', src: '本项目固化', conf: '已验证', dk: 'static' },
  { cat: 'rhy', zh: '开场钩子3s', en: 'Something moves or reveals within the first 3 seconds.', cn: '前3s必有动或有揭示。', use: '社交类1.5-3s/切；钩子先行。', src: '本项目固化', conf: '已验证', dk: 'push' },
  { cat: 'rhy', zh: '三段式时长', en: '3s hook, 10s build, 5s cliffhanger to end the episode.', cn: '3s钩子、10s立角、5s悬念收。', use: '一集2-3分钟拆8-15镜。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'rhy', zh: '漂移藏切', en: 'Hide drift with a cut within 1s of its onset.', cn: '漂移刚露头1s内用切藏掉。', use: '60帧后漂移肉眼可见；别硬撑。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'rhy', zh: '一镜一信息', en: 'One shot delivers one emotion, one action, one piece of information.', cn: '一镜只给一情绪一动作一信息。', use: '长一镜拆wide→action→reaction。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'still', zh: '纵深三层·街角', en: 'Shot past a blurred foreground railing, mid-ground subject sharp, background lights compressed.', cn: '从虚化的前景栏杆后看，她中景清晰，背景灯被压缩。', use: '前景虚+中景实+后景压。', src: '本手册搬运', conf: '已验证', dk: 'cut' },
  { cat: 'still', zh: '逆光剪影·窗边', en: 'Backlit silhouette against a bright window, rim light on the outline.', cn: '逆光剪影贴亮窗，轮廓光勾边。', use: '主体暗背景亮。', src: '本手册搬运', conf: '已验证', dk: 'cut' },
  { cat: 'still', zh: '视线接力·过肩', en: 'Over-the-shoulder foreground out of focus, subject looking off-frame.', cn: '前景过肩虚焦，她看画外。', use: '代入感。', src: '本手册搬运', conf: '已验证', dk: 'cut' },
  { cat: 'still', zh: '镜面双打', en: 'Facing the mirror, reflection meeting her eyes, frame split in two.', cn: '面对镜子，真身与倒影各半。', use: '最便宜的双主体。', src: '本手册搬运', conf: '已验证', dk: 'cut' },
  { cat: 'still', zh: '贴地动势', en: 'Ground-level camera, foreground streaks, foreshortened stride.', cn: '贴地机位，前景拖痕，近大远小。', use: '低+缩+粒子=快。', src: '本手册搬运', conf: '已验证', dk: 'cut' },
  { cat: 'still', zh: '框中框·走廊', en: 'Two nested doorways, subject small in the far light.', cn: '两重门框套叠，她在远光里很小。', use: '中间层压暗。', src: '本手册搬运', conf: '已验证', dk: 'cut' },
  { cat: 'still', zh: '插入特写', en: 'Close-up insert of hands gripping the strap, subject blurred behind.', cn: '特写落在攥包带的手上，她在后方虚掉。', use: '不拍脸也是语法。', src: '本手册搬运', conf: '已验证', dk: 'cut' },
  { cat: 'still', zh: '俯瞰破格', en: 'Directly overhead, symmetrical layout, one cup off-grid.', cn: '垂直俯瞰对称桌面，只有一只杯子歪掉。', use: '对称必留一破。', src: '本手册搬运', conf: '已验证', dk: 'cut' },
  { cat: 'anti', zh: '堆运镜', en: 'pan left then tilt up then dolly in in one 5s shot.', cn: '5s里又摇又仰又推。', use: '必废：模型只取其一或乱动。', src: 'H3+Seedance官方', conf: '已验证', dk: 'cut' },
  { cat: 'anti', zh: '无落点运镜', en: 'The camera pushes in.', cn: '镜头前推。（没写落在哪）', use: '漂：缺reveal/ending on。', src: 'H3官方', conf: '已验证', dk: 'push' },
  { cat: 'anti', zh: '整镜static行进', en: 'Static for the full 5s walk.', cn: '5s行走全程静止。', use: '死画面；static只许首尾≤2s。', src: '本项目固化', conf: '已验证', dk: 'static' },
  { cat: 'anti', zh: '标签堆砌', en: 'cinematic, pan right, 4k, dynamic camera.', cn: '结尾堆标签式运镜。', use: '须写成自然动作句。', src: 'H3官方', conf: '已验证', dk: 'panR' },
  { cat: 'anti', zh: 'push三连', en: 'Three push-ins in a row.', cn: '连续三镜全是push。', use: '第3镜必换向。', src: '本项目固化', conf: '待复测', dk: 'push' },
  { cat: 'anti', zh: '150词超限', en: '200-word prompt with 10 constraints.', cn: '200词10约束。', use: '超150词先砍配角句保主约束。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'anti', zh: 'between双关', en: 'Standing between the benches.', cn: '站在凳子之间。', use: '侧向/纵向双关；改past/flanked by。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'anti', zh: '人物系方位', en: 'Behind her is the statue.', cn: '她身后是神像。', use: '人物系判废；用画面左/右。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'anti', zh: '临场发明机位', en: 'A brand-new angle behind her never in the Bible.', cn: 'Bible里没有的脑后新机位。', use: '先补机位参考再出镜。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'anti', zh: '无声景', en: 'No soundscape, dialogue only.', cn: '只有对白，无环境声。', use: '底噪+动态+细节三层必写其一。', src: 'H3官方', conf: '已验证', dk: 'static' },
  { cat: 'anti', zh: '5s硬转360', en: 'A full 360 orbit crammed into a 5s single shot.', cn: '5s单镜硬塞一整圈360。', use: '必穿模；改arc180或拆两镜。', src: '本项目固化', conf: '已验证', dk: 'arc' },
  { cat: 'anti', zh: '空推无物', en: 'A slow push in with nothing new revealed at the end.', cn: '慢推到底，落幅空无一物。', use: '白推；落幅必是脸/手/门/窗/字。', src: '本项目固化', conf: '已验证', dk: 'push' },
  { cat: 'tpl', zh: 'T2VA单镜模板', en: '[Shot 1] Cinematic, medium-wide frames her opening the shutters. The camera pushes in at slow speed.', cn: '中景她开百叶窗，慢推。', use: '无图从零起；先风格+构图再动作。', src: 'H3官方Case1', conf: '已验证', dk: 'push' },
  { cat: 'tpl', zh: 'I2VA首帧模板', en: '<Picture 1> is fully referenced at 0.00s. The camera trucks right at slow speed as she looks up.', cn: '首帧全参考，右移，她抬头。', use: '同机位只改神态走编辑。', src: 'H3官方Case2', conf: '已验证', dk: 'truckR' },
  { cat: 'tpl', zh: 'FL2VA首尾模板', en: 'Picture 1 at 0.00s, Picture 2 at 8.00s. The camera pulls out as she opens the umbrella.', cn: '首0s尾8s，后拉，她开伞。', use: '只写路径不复述两帧。', src: 'H3官方Case3', conf: '已验证', dk: 'pull' },
  { cat: 'tpl', zh: 'L2VA尾帧模板', en: '<Picture 1> aligns with the 6.00s mark. The camera pushes in as the glass tips and shatters.', cn: '尾帧6s对齐，前推，杯倒碎裂。', use: '先兼容早态再落尾帧。', src: 'H3官方Case4', conf: '已验证', dk: 'push' },
  { cat: 'tpl', zh: '切镜时间戳', en: '[Shot 2] At 00:04.000, the camera cuts to a closer angle. The camera arcs around the subject.', cn: '00:04切更近机位，环绕。', use: '两运镜=两shot+时间戳。', src: 'H3官方', conf: '已验证', dk: 'cut' },
  { cat: 'tpl', zh: '对白制式', en: 'The calm young woman (S1) says: <d>[English] First batch of the morning.</d>', cn: '她（S1）说：第一炉好了。', use: '说话人全片稳定；旁白声明嘴闭。', src: 'H3官方', conf: '已验证', dk: 'static' },
  { cat: 'tpl', zh: '声景三层', en: 'Room tone hums low; footsteps rise with the push in; cloth rustles on the turn.', cn: '房间底噪+脚步随推起+转身衣响。', use: '底噪+动态+细节；对白不重复。', src: 'H3官方', conf: '已验证', dk: 'static' },
  { cat: 'tpl', zh: '无配乐N/A', en: 'non_diegetic_music: N/A.', cn: '无配乐。', use: '无则显式N/A不省略。', src: 'H3官方', conf: '已验证', dk: 'static' },
  { cat: 'tpl', zh: '交付抬头', en: '5s｜图：<Picture 1>=首帧全身（构图）｜<Picture 2>=尾帧（落幅）', cn: '抬头先行再贴正文。', use: '图=哪张管什么。', src: '本项目固化', conf: '已验证', dk: 'cut' },
  { cat: 'tpl', zh: '幅度省略律', en: 'Medium amplitude and normal speed are omitted.', cn: '中幅常速不写。', use: '写了等于废话抢权重。', src: 'H3官方§4.3', conf: '已验证', dk: 'static' },
  { cat: 'tpl', zh: '一主运镜声明', en: 'One continuous move, no cuts.', cn: '一镜到底，无切。', use: 'FL2VA单shot声明。', src: 'H3官方', conf: '已验证', dk: 'static' },
  { cat: 'tpl', zh: '防穿模收尾', en: 'She settles into the exact pose and composition of Picture 2.', cn: '她落回图2的姿态构图。', use: '尾帧像素级对齐。', src: 'H3官方', conf: '已验证', dk: 'static' },
  { cat: 'tpl', zh: '双人对话模板', en: '[Shot 1] Medium-wide frames both across the table. [Shot 2] At 00:03.000, cut to reverse close-up as S1 finishes and S2 reacts.', cn: '中景框住桌两边；00:03切反打近景，S1话落S2反应。', use: '≥2轮必分镜；景别差一档。', src: 'H3+本项目', conf: '已验证', dk: 'cut' },
  { cat: 'tpl', zh: '产品环绕模板', en: 'Orbit halfway around the bottle at product height, reflections rotating, background depth visible.', cn: '半圈环绕产品瓶，腰高，反光转动，背景有纵深。', use: '一集产品只转半圈；全圈留旗舰镜。', src: 'Seedance+Kling产品', conf: '待复测', dk: 'arc' },
]

/* ---------- 真片例 / 声景 / 完整prompt用例（源文件原样搬运） ---------- */
const SB = 'https://www.studiobinder.com/blog/different-types-of-camera-movements-in-film/'

const FILM: Record<string, { t: string; u: string }> = {
  push: { t: '真片：《教父》Michael起身段 / 《刺杀杰西·詹姆斯》push-in分析（StudioBinder点名）', u: SB },
  pull: { t: '真片：《闪灵》结尾拉开、Jack孤立（Kubrick，StudioBinder点名）', u: SB },
  zoomin: { t: '真片：《全金属外壳》zoom（Kubrick，StudioBinder点名）', u: SB },
  zoomout: { t: '真片：《全金属外壳》zoom（Kubrick，StudioBinder点名）', u: SB },
  panL: { t: '官方未点名真片：看StudioBinder总片pan段 + Kling官方pan示例', u: 'https://kling.ai/blog/kling-ai-camera-control-video-guide' },
  panR: { t: '官方未点名真片：看StudioBinder总片pan段 + Kling官方pan示例', u: 'https://kling.ai/blog/kling-ai-camera-control-video-guide' },
  truckL: { t: '真片：《1917》Deakins tracking/Steadicam段（truck属tracking，StudioBinder点名）', u: SB },
  truckR: { t: '真片：《1917》Deakins tracking/Steadicam段（truck属tracking，StudioBinder点名）', u: SB },
  tiltU: { t: '真片：《侏罗纪公园》初见恐龙tilt-up（Spielberg，StudioBinder点名）', u: SB },
  tiltD: { t: '真片：《侏罗纪公园》tilt段 + Kling官方tilt示例（鞋→脸）', u: 'https://kling.ai/blog/kling-ai-camera-control-video-guide' },
  pedU: { t: '真片：归boom/crane家族，看StudioBinder establishing/boom段（Kubrick/Wes Anderson/Bay）', u: SB },
  pedD: { t: '真片：归boom/crane家族，看StudioBinder establishing/boom段', u: SB },
  arc: { t: '真片：《黑暗骑士》Joker派对360° / 《复联》集结arc / 《月光》开场（StudioBinder点名）', u: 'https://www.studiobinder.com/blog/arc-shot-in-film-definition/' },
  track: { t: '真片：《1917》Deakins一镜式tracking（StudioBinder点名）', u: SB },
  static: { t: '真片：《华尔街之狼》即兴戏static多机位（Scorsese，StudioBinder点名）', u: SB },
  shakeS: { t: '真片：《大空头》Jenga戏手持纪录感（StudioBinder点名，轻抖参照）', u: SB },
  shakeB: { t: '真片：《大空头》手持家族；重抖看Kling handheld段', u: 'https://kling.ai/blog/kling-ai-camera-control-video-guide' },
  pov: { t: '官方未点名真片：看Kling Masterclass POV/Locked Rig真机演示', u: 'https://www.youtube.com/watch?v=TKkg-8P7jTM' },
  rollC: { t: '真片：《黑豹》Killmonger登基慢滚（StudioBinder点名）', u: SB },
  rollCC: { t: '真片：《黑豹》Killmonger登基慢滚（StudioBinder点名）', u: SB },
  dollyzoom: { t: '真片：《指环王1》Frodo + 希区柯克《Vertigo》（dolly zoom命名出处）', u: SB },
  crash: { t: '官方未点名真片：看Kling Masterclass crash zoom章真机演示', u: 'https://www.youtube.com/watch?v=TKkg-8P7jTM' },
  whip: { t: '真片：《爱乐之城》Sebastian×Mia whip pan（StudioBinder video essay点名）+ Wes Anderson式', u: SB },
  fpv: { t: '官方未点名真片：看Seedance官方8式FPV/穿行demo', u: 'https://www.seedance.tv/blog/seedance-2-0-camera-movement-prompts' },
  dive: { t: '官方未点名真片：看Kling Masterclass crane/dive章真机演示', u: 'https://www.youtube.com/watch?v=TKkg-8P7jTM' },
  crane: { t: '真片：establishing/boom段（Kubrick/Wes Anderson/Bay，StudioBinder点名）+ Kling crane章', u: 'https://www.youtube.com/watch?v=TKkg-8P7jTM' },
  cut: { t: '方法卡无独立片例：看对应运镜真片；对话类参照《华尔街之狼》static对白', u: SB },
}

const SND: Record<string, string> = {
  move: 'Room tone hums low; breath and cloth rise with the move. Music: N/A.',
  adv: 'Wind and footsteps swell with the move; impacts land dry. Music: N/A.',
  cut: 'Ambience carries across the cut; the next line enters on the beat. Music: N/A.',
  rhy: 'Pulse steadies under the shot; silence holds the landing. Music: N/A.',
  still: 'Rain and distant traffic bed the frame; a single cloth rustle. Music: N/A.',
  anti: 'Corrected version below. Do not run the red text. Music: N/A.',
  tpl: 'Soundscape as written; no extra score. Music: N/A.',
}

const CASES: Record<string, [string, string, string, string]> = {
  '前推逼近 push in': ['a dim study with rain on the window', '雨点敲窗的昏暗书房', 'she looks up from the letter, eyes widening', '她从信上抬起头，眼睛睁大'],
  '后拉揭示 pull out': ['a tiny attic room at midnight', '午夜的逼仄阁楼', 'she sits alone hugging her knees as the walls widen out', '她抱膝独坐，墙壁向四周退开'],
  '变焦进 zoom in': ['a festival stall row at night', '夜晚的祭典摊位街', 'her smile freezes as the lens tightens on her eyes', '镜头收紧到她眼睛上，笑容凝住'],
  '变焦出 zoom out': ['a close-up of the cracked amulet', '碎裂护身符的特写', 'the lens widens to reveal the ruined shrine hall', '镜头拉开，露出破败的神社大殿'],
  '左摇 pan left': ['a riverside path at sunset', '日落的河岸小径', 'she runs left across the frame, hair streaming', '她向左跑过画面，发丝飞扬'],
  '右摇 pan right': ['a dormitory hallway after lights-out', '熄灯后的宿舍走廊', 'she turns and walks right toward the ajar door', '她转身向右走向虚掩的门'],
  '左移 truck left': ['a cyclist crossing the bridge at dawn', '黎明过桥的骑行者', 'the camera slides left beside her, river lights streaking', '镜头在她身侧左移，河面灯光拉成线'],
  '右移 truck right': ['a night train carriage with rain on glass', '雨夜列车车厢', 'she lifts her gaze toward the city lights', '她抬头看向城市灯火'],
  '上摇 tilt up': ['a rain-soaked platform, boots first', '雨湿的站台，先拍靴子', 'the lens rises from her boots to her rain-streaked face', '镜头从靴子升到她挂雨的脸'],
  '下摇 tilt down': ['the clock tower against storm clouds', '风暴云下的钟楼', 'the lens drops from the tower face to the tiny gate below', '镜头从钟面降到下方小小的门'],
  '升机 pedestal up': ['a canteen table with a cold lunch box', '摆着冷掉便当的食堂桌', 'the camera rises from the lunch box to her downcast face', '镜头从便当升到她低垂的脸'],
  '降机 pedestal down': ['her standing figure in the corridor', '走廊里她的站姿', 'the camera sinks to the letter dropped on the floor', '镜头降到掉在地上的信'],
  '环绕 arc': ['the rooftop duel at dusk, both motionless', '黄昏天台对峙，两人静止', 'the camera arcs 180 degrees between the two blades', '镜头在两柄刀之间转过180度'],
  '跟踪 tracking': ['a lantern-lit shopping street', '灯笼亮起的商店街', 'she weaves through the crowd, never looking back', '她穿过人群，始终不回头'],
  '静止 static': ['the classroom doorway at noon', '正午的教室门口', 'the runner exits the frame, papers settling behind', '跑者跑出画框，纸张在身后落定'],
  '轻抖 shake slightly': ['stone stairs in the rain, she descends', '雨中石阶，她往下走', 'the frame breathes lightly with each step', '画面随脚步轻轻呼吸'],
  '重抖 shake strongly': ['the courtyard as the blast wave hits', '冲击波袭来的庭院', 'tiles lift and the frame jolts hard', '瓦片掀起，画面剧烈一震'],
  '主观 POV': ['a flooded alley she sprints through', '她狂奔穿过的积水小巷', 'her arms pump at the frame edges, water bursting', '双臂在画面边缘摆动，水花炸开'],
  '顺时针滚 roll C': ['the infirmary ceiling, fever dream', '发烧梦里的医务室天花板', 'the ceiling rolls as her eyelids flutter', '天花板旋转，她眼睑颤动'],
  '逆时针滚 roll CC': ['the Ferris wheel cabin at night', '夜晚的摩天轮座舱', 'city lights smear in a slow reverse roll', '城市灯光在缓慢反转中拖开'],
  '希区柯克 dolly zoom': ['the corridor stretching behind her', '她身后拉长的走廊', 'she freezes, the walls stretching unnaturally', '她僵住，墙壁不自然地拉伸'],
  '急推 crash zoom': ['the chapel altar, candles guttering', '烛火摇曳的教堂祭坛', 'the lens slams onto the cross in her hands', '镜头砸到她手中的十字架上'],
  '快甩 whip pan': ['her startled face in the kitchen', '厨房里她受惊的脸', 'the frame whips right with blur to the intruder at the door', '画面带模糊向右甩到门口的不速之客'],
  'FPV穿行': ['the night market arcade, lanterns overhead', '夜市拱廊，头顶灯笼', 'the camera threads stalls, banks past pillars, bursts into the square', '镜头穿摊位、掠柱子、冲进广场'],
  '俯冲 dive': ['the bell tower above the festival crowd', '祭典人群上方的钟楼', 'the camera dives straight down, hovering above her umbrella', '镜头垂直俯冲，在她伞上方急停'],
  '升降 crane': ['the walled courtyard at dawn', '黎明的围合庭院', 'the camera climbs from the moss stones to high above the roofs', '镜头从青苔石地升到屋顶高空'],
  '手持呼吸 handheld': ['the convenience store at 2am, fluorescent buzz', '凌晨两点的便利店，荧光灯嗡鸣', 'she picks the rice ball, frame swaying almost imperceptibly', '她拿起饭团，画面几乎不可察地晃'],
  '低位跟踪 low track': ['the puddle reflecting neon', '倒映霓虹的水洼', 'the paper boat drifts, camera skimming the water', '纸船漂走，镜头贴水面滑行'],
  '全环绕360 full orbit': ['two fencers frozen mid-lunge', '僵持在弓步中的两名剑手', 'the camera completes the full circle, blades crossing twice', '镜头转完一整圈，双剑交错两次'],
  '机械臂 Mo-cap rig': ['the kneeling archer centered in the dojo', '道场中央跪着的弓手', 'micro snaps left-right, a lateral pass, a crash punch to the eyes', '左右微震、横移掠过、急推到眼'],
  '自拍 framing selfie': ['the seaside promenade, gulls crying', '海鸥鸣叫的海滨步道', "she holds the lens at arm's length, smiling into the wind", '她手臂伸直举镜，迎风笑'],
  '前跟 track forward': ['the morning commute stairs', '早高峰的楼梯', 'the camera backs up ahead of her at her pace', '镜头在她前方同速后退跟随'],
  '侧视差 parallax lateral': ['the torii-lined approach, fog low', '雾气低垂的鸟居参道', 'pillars whip past the foreground, she stays sharp mid-frame', '前景柱子掠过，她在中景保持清晰'],
  '推仰复合 dolly+tilt': ['the suit of armor in the museum hall', '博物馆大厅的铠甲', 'the camera pushes in while tilting from greaves to helm', '镜头前推同时从胫甲摇到头盔'],
  '长焦压缩 telephoto': ['the crowded crossing at dusk', '黄昏拥挤的十字路口', 'crowds stack behind her shoulder, lights blooming', '人群压在她肩后，灯光晕开'],
  '广角拉伸 wide': ['the starting blocks, rain hammering', '暴雨中的起跑器', 'her launch stretches huge, track tilting a few degrees', '她起跑被拉得巨大，跑道微斜'],
  '180度线': ['two rivals across the kotatsu', '被炉两侧的对手', 'both stay left-right locked, glares mirrored', '两人左右锁定，瞪视互为镜像'],
  '正反打': ['the confession in the stairwell', '楼梯间的告白', 'his plea ends, cut to her close-up reaction', '他说完，切她近景反应'],
  '视线匹配': ['she stares past the fence', '她盯着栅栏外', 'cut to the stray cat on the image-right wall', '切到画面右侧墙头上的野猫'],
  '动作匹配': ['she starts turning the doorknob', '她开始拧门把手', 'cut mid-turn, the next shot finishes the push open', '拧到一半切，下一镜接完推开'],
  '对话切': ['the rooftop argument at 00:03', '天台争吵00:03', 'his last syllable lands, cut to her 0.4s-late flinch', '他尾音落，切她慢0.4秒的瑟缩'],
  '动作反应拆': ['the window suddenly rattling harder', '窗户突然剧烈抖动', 'action: glass shuddering; reaction: she spins around', '动作镜玻璃震颤；反应镜她猛转身'],
  '双轴对齐': ['story: bells toll 1-3s; camera: her 0-1, bells 1-3, her 3-5 bells still ringing', '世界轴1-3秒钟响；镜头轴0-1她、1-3钟、3-5她钟声延续', 'reaction shot keeps the ringing going', '反应镜里钟声延续不断'],
  'J-cut': ['the classroom rooftop, wind rising', '风起的天台', 'her reply enters 0.5s before we see her face', '先闻其声0.5秒，才见她的脸'],
  '声音桥': ['the choir rehearsal bleeding through walls', '穿墙而来的合唱排练', 'the hum never breaks across three cuts', '哼鸣横跨三切不断'],
  '图形匹配': ['the full moon over the lake', '湖面上的满月', 'cut to her round pupil reflecting it', '切到她映着月亮的圆形瞳孔'],
  '前景穿越': ['the colonnade at noon', '正午的柱廊', 'the camera slips past a pillar onto her startled eyes', '镜头掠过柱子落到她惊愕的眼'],
  '景别拉档': ['the quarrel across the counter', '柜台两侧的争吵', 'wide two-shot cuts to her tight close-up, same side', '全景双人切她特写，同侧'],
  '30度规则': ['the tea-pouring, kettle steaming', '茶壶冒汽的倒茶', 'second angle swings 45 degrees to the pouring stream', '第二机位转45度对准水流'],
  '越轴警告 crossing': ['the duelists mid-exchange', '交手中的剑手', 'a top-down insert resets the axis before the next cut', '俯瞰插入镜先洗轴再切'],
  '主观剪 POV cut': ['she peers over the cliff edge', '她探头看悬崖下', 'POV: the drop rushing up; back: her white knuckles', '深渊扑面；回她发白的指节'],
  '蒙太奇 montage': ['the morning rush, 4 beats', '早晨四拍', 'kettle, strap, door, her sprint, each under 1s', '水壶、包带、门、她开跑，每镜1秒内'],
  '淡入淡出 fade': ['the festival ends, lanterns dimming', '祭典散场，灯笼渐暗', 'fade to black, hold 0.5s before the next sequence', '黑场淡出，停0.5秒再进下段'],
  '卡点剪 on beat': ['the drum solo climax', '架子鼓独奏高潮', 'the whip lands exactly on the crash cymbal', '快甩精准落在镲片上'],
  '一镜一运镜': ['the corridor walk, one lantern flickering', '走廊独行，一盏灯忽明忽暗', 'single slow push tied to the flicker reveal', '只用一个慢推，绑定灯光揭示'],
  '四段式运镜句': ['the archive room, dust in shafts', '档案室，光柱里有尘', 'push as she turns, revealing the red box, dread rising', '她转身时推，带出红盒子，恐惧上升'],
  '落幅必写': ['the workshop bench, tools laid out', '摆满工具的工作台', 'the move ends on the half-carved flute', '运镜落在半成品笛子上'],
  '幅度速度': ['the platform farewell', '站台送别', 'small-slow push for ache; large-fast pan reserved for shock', '小幅慢推给心酸；大幅快摇留给惊变'],
  'push连用禁令': ['three consecutive goodbyes', '连续三场告别', 'push, push, then pull out to the empty platform', '推、推，然后拉出到空站台'],
  'motion budget': ['the rainy duel, one gust', '雨中对决，一阵风', 'one step, one truck, one gust, nothing else moves', '一步、一移、一阵风，其余全冻'],
  '时长5s铁律': ['the 3s spell-cast', '3秒施法', 'action ends at 3s, frame holds dead still to 5s', '动作3秒结束，画面死静保持到5秒'],
  '三振换镜': ['the failed window-rattle insert', '连败三轮的窗颤插入镜', 'abandon the insert; cut wide and show the whole room shaking', '放弃插入镜；切全景让整屋震'],
  '首尾帧可达': ['seated reading to window sprint', '从坐着看书到冲向窗口', 'add a rising middle frame, no direct morph', '加起身中间帧；不许直接变'],
  '静帧稳再转视频': ['the keyframe of the kneeling vow', '跪地立誓的关键帧', 'freeze the composition first, video only after approval', '先冻构图，过审才跑视频'],
  '开场钩子3s': ['the black screen, a bell tolls', '黑屏，一声钟响', 'by second 2 the lantern flares red in her eyes', '第2秒灯笼红光在她眼中亮起'],
  '三段式时长': ['the episode arc', '本集弧线', '3s bell-hook, 10s shrine-build, 5s door-creak cliffhanger', '3秒钟声钩、10秒神社铺、5秒门响悬念'],
  '漂移藏切': ['the long corridor glide at frame 70', '长走廊滑镜第70帧', 'drift blooms; cut within 1s to her feet landing', '漂移露头；1秒内切她落脚'],
  '一镜一信息': ['the three-clue room', '三条线索的房间', 'this shot delivers only the wet footprints', '本镜只交代潮湿脚印'],
  '纵深三层·街角': ['rainy shopping street, neon stacked', '雨夜商店街，霓虹层叠', 'hold static 4s, only rain streaks and her sleeve move', '静止4秒，只有雨丝和她衣袖动'],
  '逆光剪影·窗边': ['the laundry room, noon backlight', '正午逆光的洗衣房', 'silhouette holds, dust drifting in the beam', '剪影保持，只有光柱里尘埃漂'],
  '视线接力·过肩': ['the platform, his shoulder foreground', '站台，他的肩膀前景', 'she boards without looking back, shoulder soft', '她不回头上车，肩膀虚着'],
  '镜面双打': ['the washroom mirror, 2am', '凌晨两点的洗手间镜子', 'real back soft, reflected eyes sharpening', '真身后脑虚，镜中眼神变锐'],
  '贴地动势': ['the marathon final straight', '马拉松最后直道', 'ground-level hold as spikes thunder past', '贴地保持，钉鞋轰鸣而过'],
  '框中框·走廊': ['the inn corridor, doors nested', '旅馆走廊，门套门', 'she shrinks toward the far light, mid layers dark', '她向远光走小，中间层压暗'],
  '插入特写': ['the strap about to snap', '即将绷断的包带', 'knuckles whiten, thread popping one by one', '指节发白，线一根根崩'],
  '俯瞰破格': ['the breakfast table, perfect symmetry', '对称完美的早餐桌', 'one cup tips over, milk spreading', '一只杯子倒下，牛奶漫开'],
  '堆运镜': ['FIX: the corridor walk', '修正：走廊独行', 'keep ONLY the slow push; delete pan and tilt', '只留慢推，删掉摇和仰'],
  '无落点运镜': ['FIX: the push with no target', '修正：无落点的推', 'push toward the amulet glowing on the shelf', '推向架上发光的护身符'],
  '整镜static行进': ['FIX: the 5s walk', '修正：5秒行走', '0-1s static feet plant, 1-4s slow track, 4-5s static hold', '0-1秒静止落脚、1-4秒慢跟、4-5秒静止'],
  '标签堆砌': ['FIX: the tag-stacked line', '修正：标签堆砌句', 'rewrite as: the camera pans right, revealing the doorway', '改写：镜头右摇，带出门口'],
  'push三连': ['FIX: push push push', '修正：三连推', 'third shot becomes a pull out to the empty street', '第三镜改成拉出到空街'],
  '150词超限': ['FIX: the 200-word prompt', '修正：200词prompt', 'cut to 120 words, keep the main spatial sentence', '砍到120词，保主空间句'],
  'between双关': ['FIX: standing between the benches', '修正：凳间站位', 'rewrite: standing past all benches, centered on the aisle', '站在所有凳子之外，走道居中'],
  '人物系方位': ['FIX: statue behind her', '修正：神像在她身后', 'rewrite: the statue knees press the image-right edge', '改写：神像膝盖压画面右缘'],
  '临场发明机位': ['FIX: the unplanned back angle', '修正：临场脑后机位', 'file it as new cam-D reference first, then shoot', '先补cam-D机位参考，再出镜'],
  '无声景': ['FIX: dialogue-only shot', '修正：纯对白镜', 'add room tone plus sleeve rustle under the line', '加房间底噪加台词下衣物摩擦声'],
  '5s硬转360': ['FIX: the crammed 360', '修正：硬塞360', 'split into two 180 arcs across a doorway cut', '拆成两镜180，中间用门切'],
  '空推无物': ['FIX: the empty push', '修正：空推', 'end the push on the scar on her palm', '推落到她掌心疤痕上'],
  'T2VA单镜模板': ['a baker opening shutters at dawn', '黎明开百叶窗的面包师', 'steam rises as the push settles on the first loaf', '推镜落定时蒸汽升起，第一炉面包'],
  'I2VA首帧模板': ['Picture 1: girl by the rain-streaked train window', '图1：雨痕车窗边的女孩', 'she lifts her gaze as the camera trucks right', '镜头右移时她抬头'],
  'FL2VA首尾模板': ['Picture 1 closed umbrella, Picture 2 open canopy', '图1收伞、图2开伞', 'she raises and snaps it open mid-pull', '后拉途中她举伞撑开'],
  'L2VA尾帧模板': ['Picture 1: shattered glass layout', '图1：碎玻璃布局', 'fingertips strike, glass tips, shards settle to match', '指尖一击，杯倒，碎片落成图样'],
  '切镜时间戳': ['the interrogation, two chairs', '审讯，两把椅子', 'at 00:04 cut closer as he stands', '00:04他起身时切更近'],
  '对白制式': ['the bakery counter, morning rush', '早高峰面包柜台', 'S1 places the loaf and speaks the line', 'S1放下麵包说出台词'],
  '声景三层': ['the corridor turn', '走廊转身', 'hum low, steps rising, sleeve cutting air', '底噪低鸣、脚步渐起、衣袖划风'],
  '无配乐N/A': ['the silent prayer', '无声的祈祷', 'no score; only breath and rain on tiles', '无配乐；只有呼吸和瓦上雨声'],
  '交付抬头': ['the 5s shrine-gate shot', '5秒神社鸟居镜', 'Picture 1 wide gate, Picture 2 fox statue close-up', '图1全景鸟居，图2狐狸像特写'],
  '幅度省略律': ['the standard walk-and-talk', '标准边走边谈', 'medium moves unwritten, only the final reveal stated', '中幅不写，只写最终揭示'],
  '一主运镜声明': ['the umbrella opening, one take', '一镜到底的开伞', 'single pull out, no cuts, canopy blooms once', '只后拉，无切，伞开一次'],
  '防穿模收尾': ['the shattered glass', '碎裂的玻璃', 'every shard lands exactly as Picture 2', '每块碎片精确落成图2'],
  '双人对话模板': ['the diner booth, rain outside', '雨夜小餐馆卡座', 'S1 accuses, S2 laughs, cut on the laugh peak', 'S1质问，S2笑，切在笑声顶点'],
  '产品环绕模板': ['the perfume bottle on black acrylic', '黑亚克力上的香水瓶', 'half orbit, reflections sweeping once', '半圈环绕，反光扫过一次'],
}

/* ---------- 状态与交互 ---------- */
const picked = ref<string[]>([])
const active = ref<string>('all')
const query = ref<string>('')
const openKey = ref<string | null>(null)
const TRAY_LS = 'suli-shot-tray'
let trayInit = true
try { trayInit = localStorage.getItem(TRAY_LS) !== '0' } catch {}
const trayOpen = ref<boolean>(trayInit)
function toggleTray(): void {
  trayOpen.value = !trayOpen.value
  try { localStorage.setItem(TRAY_LS, trayOpen.value ? '1' : '0') } catch {}
}


function shortChip(p: string): string {
  return p.length > 42 ? p.slice(0, 42) + '…' : p
}

function filmOf(dk: string): { t: string; u: string } {
  return FILM[dk] ?? FILM.cut
}

function fullOf(d: ShotItem): FullPrompt {
  const c: [string, string, string, string] = CASES[d.zh] ?? ['a quiet shrine corridor at dusk', '黄昏寂静的神社走廊', 'she turns toward the lens', '她转向镜头']
  const cam: string = d.en.replace(/\.$/, '')
  return {
    en: '[Shot 1] 2D-animated, cinematic, ' + c[0] + '. ' + cam + ' as ' + c[2] + '. Hold the last frame static until 5.00s.',
    cn: '【Shot 1】二次元电影感，' + c[1] + '。' + d.cn.replace(/。$/, '') + '，' + c[3] + '。动作完成后静止保持到5秒。',
    snd: 'Soundscape: ' + (SND[d.cat] ?? SND.move),
  }
}

function confType(conf: string): 'success' | 'warning' | 'danger' | 'info' {
  if (conf === '已验证') return 'success'
  if (conf === '待复测') return 'warning'
  return 'danger'
}

function catName(cat: string): string {
  const hit: [string, string] | undefined = CATS.find(([k]) => k === cat)
  return hit ? hit[1] : cat
}

const filtered = computed(() => {
  const kw: string = query.value.trim().toLowerCase()
  return DATA.filter((d: ShotItem) => {
    if (active.value !== 'all' && d.cat !== active.value) return false
    if (!kw) return true
    return (d.zh + d.en + d.cn + d.use + d.src + d.conf).toLowerCase().includes(kw)
  })
})

function isOpen(key: string): boolean {
  return openKey.value === key
}

function toggleDetail(key: string): void {
  openKey.value = openKey.value === key ? null : key
}

function clearQuery(): void {
  query.value = ''
  active.value = 'all'
}

async function copyEn(d: ShotItem): Promise<void> {
  await copyText(d.en)
  ElMessage.success('已复制英文句：' + d.zh)
}

function addPicked(d: ShotItem): void {
  if (!picked.value.includes(d.en)) picked.value.push(d.en)
  ElMessage.success('已加入组合：' + d.zh)
}

async function copyFull(d: ShotItem): Promise<void> {
  const fp: FullPrompt = fullOf(d)
  await copyText(fp.en + ' ' + fp.snd)
  ElMessage.success('已复制完整视频prompt：' + d.zh)
}

async function copyFullActive(d: ShotItem): Promise<void> {
  await copyFull(d)
}

async function copyAll(): Promise<void> {
  if (picked.value.length === 0) {
    ElMessage.warning('组合栏是空的')
    return
  }
  await copyText(picked.value.join(' '))
  ElMessage.success('已复制组合句，共' + picked.value.length + '条')
}

function removeAt(i: number): void {
  picked.value.splice(i, 1)
}

function clearAll(): void {
  picked.value = []
}
</script>

<style scoped>
.shot-tool {
  background: #fff;
  padding-bottom: 24px;
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
}
.tray-inner {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.tray-label {
  font-size: 13px;
  color: var(--suli-text-2);
  white-space: nowrap;
}
.chips {
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
  padding: 4px 6px 4px 12px;
  font-size: 12px;
  color: var(--suli-text);
  max-width: 100%;
}
.chip b {
  font-weight: 400;
  font-family: Consolas, monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chip-x {
  cursor: pointer;
  color: var(--suli-text-2);
  padding: 0 4px;
  flex-shrink: 0;
}
.chip-x:hover {
  color: var(--suli-text);
}
.search {
  min-width: 180px;
  max-width: 300px;
  flex: 1;
}
.filter-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  align-items: center;
}
.fchip {
  cursor: pointer;
}
.count {
  font-size: 12.5px;
  font-family: Consolas, monospace;
  white-space: nowrap;
}
.picked-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}
.tool-card {
  overflow: hidden;
  cursor: pointer;
  border: 1px solid var(--suli-border, #e4e4e7);
  transition: transform 0.12s, box-shadow 0.12s, border-color 0.12s;
}
.tool-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(251, 114, 153, 0.18);
  border-color: var(--suli-primary, #FB7299);
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
  grid-template-columns: 220px 1fr;
  gap: 12px;
}
.detail-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
}
.cover {
  width: 100%;
  display: block;
  max-height: 240px;
  overflow: hidden;
  background: #fff;
  border-bottom: 1px solid var(--suli-border, #e4e4e7);
}
.cover :deep(svg) {
  width: 100%;
  height: auto;
  display: block;
}
.body {
  padding: 9px 12px 12px;
}
.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: space-between;
}
.zh {
  font-size: 14px;
  font-weight: 700;
  color: var(--suli-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.catchip {
  flex-shrink: 0;
}
.en {
  font-size: 12px;
  color: var(--suli-text-2);
  margin-top: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mono {
  font-family: Consolas, monospace;
}
.pills {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.summary {
  font-size: 12.5px;
  margin: 6px 0 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty {
  padding: 28px 0;
  text-align: center;
  font-size: 13px;
}
.dlg-cover {
  border: 1px solid var(--suli-border, #e4e4e7);
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}
.dlg-cover :deep(svg) {
  width: 100%;
  height: auto;
  display: block;
}
.dlg-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}
.dlg-title-row .zh {
  white-space: normal;
  font-size: 16px;
}
.dlg-cn {
  font-size: 13px;
  color: var(--suli-text);
  margin: 8px 0 0;
  line-height: 1.7;
}
.dlg-use {
  font-size: 12.5px;
  color: var(--suli-text-2);
  margin: 6px 0 0;
  line-height: 1.7;
}
.film {
  font-size: 12px;
  color: var(--suli-text-2);
  margin-top: 8px;
  line-height: 1.65;
  background: #f4f4f6;
  border-radius: 6px;
  padding: 5px 8px;
}
.film a {
  font-weight: 700;
  margin-left: 6px;
  white-space: nowrap;
  color: var(--suli-primary, #FB7299);
}
.fullbox {
  margin-top: 10px;
  border: 1px solid var(--suli-border, #e4e4e7);
  border-radius: 8px;
  padding: 8px 10px;
}
.fullname {
  font-size: 12.5px;
  font-weight: 700;
  color: var(--suli-text);
}
.fullcn {
  font-size: 12px;
  color: var(--suli-text-2);
  margin-top: 6px;
  line-height: 1.65;
}
@media (max-width: 720px) {
  .detail-cols {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
}
@media (max-width: 560px) {
  .grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  .detail-cols {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
  .tray {
    padding: 8px 10px;
  }
  .intro {
    padding: 14px;
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
.tool-card > .body > .en, .tool-card > .body > .pills, .tool-card > .body > .summary { display: none; }
.tool-card > .body > .title-row { overflow: hidden; }
.tool-card > .body > .title-row > * { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tool-card.open { box-shadow: 0 0 0 2px rgba(251,114,153,.45), 0 8px 20px rgba(251,114,153,.25); }</style>
