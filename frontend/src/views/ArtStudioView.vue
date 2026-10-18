<template>
  <div class="suli-card kun-page art-studio">
    <!-- 顶栏：方案选择 / 保存 / 状态 -->
    <div class="studio-head">
      <h3 style="margin:0">单图创作</h3>
      <el-select
        v-model="curPlanId" size="small" placeholder="选择方案" clearable class="w-plan"
        @change="(v: string) => loadPlan(v)"
      >
        <el-option v-for="p in plans" :key="p.id" :label="p.title || p.id" :value="p.id" />
      </el-select>
      <el-button size="small" @click="newPlan">新建方案</el-button>
      <el-button size="small" type="primary" :loading="saving" @click="savePlan">保存</el-button>
      <el-button size="small" type="danger" plain :disabled="!curPlanId" @click="delPlan">删除</el-button>
      <span style="flex:1" />
      <el-tag size="small" :type="statusTagType">{{ statusLabel }}</el-tag>
    </div>

    <div class="studio-grid">
      <!-- 左：方案（与 agent 讨论产出） -->
      <div class="studio-col">
        <el-input v-model="form.title" size="small" placeholder="标题" />

        <div class="block-title">方案意图</div>
        <div class="grow">
          <el-input v-model="form.intent_text" type="textarea" :rows="8" />
        </div>
        <div class="row">
          <el-button size="small" :loading="agentLoading" @click="discussWithAgent">与 agent 讨论方案</el-button>
          <el-button v-if="agentLoading" size="small" text @click="stopAgent">停止</el-button>
          <span class="suli-muted" v-if="agentProgress">{{ agentProgress }}</span>
        </div>
        <el-collapse v-if="agentAnswer" class="agent-answer">
          <el-collapse-item title="agent 回话" name="a">
            <pre class="agent-pre">{{ agentAnswer }}</pre>
          </el-collapse-item>
        </el-collapse>

        <div class="block-title">目标引擎</div>
        <el-checkbox-group v-model="form.engines" size="small" class="engines">
          <el-checkbox v-for="e in ENGINE_OPTS" :key="e.key" :value="e.key" :label="e.label" />
        </el-checkbox-group>

        <div class="block-title">参考图 <span class="suli-muted tnum">{{ form.ref_images.length }}/6</span></div>
        <div class="refs">
          <div v-for="(r, i) in form.ref_images" :key="i" class="ref-item">
            <img v-if="r.url" :src="r.url" :alt="r.name" />
            <span class="ref-name">{{ r.name }}</span>
            <el-button link type="danger" size="small" @click="form.ref_images.splice(i, 1)">移除</el-button>
          </div>
          <el-button size="small" :loading="refUploading" :disabled="form.ref_images.length >= 6" @click="refInput?.click()">
            + 参考图
          </el-button>
          <input ref="refInput" type="file" accept="image/*" style="display:none" @change="onRefFile" />
        </div>

        <div class="block-title">约束 / 改图指令</div>
        <el-input v-model="form.note" type="textarea" :rows="2" />

        <div class="row" style="margin-top:12px">
          <el-button type="primary" size="small" :loading="pushing" @click="pushToLport">直投 L-Port</el-button>
          <el-button size="small" @click="reload">刷新回传</el-button>
        </div>
        <div class="suli-muted" v-if="pushHint" style="margin-top:6px">{{ pushHint }}</div>
      </div>

      <!-- 右：回传提示词 -->
      <div class="studio-col">
        <div class="block-title">
          回传提示词
          <span class="suli-muted tnum">{{ promptKeys.length }}</span>
          <el-button v-if="promptKeys.length" size="small" text style="margin-left:auto" @click="copyAll">复制全部</el-button>
        </div>
        <el-empty v-if="!promptKeys.length" class="empty-fill" description="暂无回传" :image-size="64" />
        <div v-else class="prompt-scroll">
          <div v-for="k in promptKeys" :key="k" class="prompt-card">
            <div class="prompt-head">
              <b>{{ engineLabel(k) }}</b>
              <span class="suli-muted">{{ prompts[k]?.source || '' }}</span>
              <span style="flex:1" />
              <el-button size="small" text @click="copyPrompt(k)">复制</el-button>
            </div>
            <div class="prompt-row">
              <span class="lbl">正向</span>
              <pre>{{ prompts[k]?.positive || '—' }}</pre>
            </div>
            <div class="prompt-row" v-if="prompts[k]?.negative">
              <span class="lbl">负向</span>
              <pre>{{ prompts[k]?.negative }}</pre>
            </div>
            <div class="prompt-row" v-if="prompts[k]?.note">
              <span class="lbl">备注</span>
              <pre>{{ prompts[k]?.note }}</pre>
            </div>
            <div class="suli-muted" v-if="prompts[k]?.at" style="font-size:12px">回传于 {{ prompts[k]?.at }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

defineOptions({ name: 'ArtStudioView' })

const ENGINE_OPTS = [
  { key: 'novelai', label: 'NovelAI' },
  { key: 'tsubaki3', label: 'Tsubaki.3' },
  { key: 'seedream', label: 'Seedream' },
  { key: 'anima', label: 'Anima' },
  { key: 'gpt_image', label: 'GPT Image' },
  { key: 'flux', label: 'FLUX' },
  { key: 'sdxl', label: 'SDXL' },
  { key: 'pony', label: 'Pony' },
  { key: 'cloud', label: '云模板' },
]

type RefImg = { name: string; path: string; url: string }
type PlanForm = {
  title: string
  intent_text: string
  engines: string[]
  ref_images: RefImg[]
  note: string
}

const DEFAULT_ENGINES = ['novelai', 'tsubaki3', 'seedream']

const plans = ref<any[]>([])
const curPlanId = ref('')
const blankForm = (): PlanForm => ({ title: '', intent_text: '', engines: [...DEFAULT_ENGINES], ref_images: [], note: '' })
const form = ref<PlanForm>(blankForm())
const prompts = ref<Record<string, any>>({})
const status = ref('draft')
const saving = ref(false)
const pushing = ref(false)
const pushHint = ref('')
const agentLoading = ref(false)
const agentProgress = ref('')
const agentAnswer = ref('')
const agentAborter = ref<AbortController | null>(null)
const refInput = ref<HTMLInputElement | null>(null)
const refUploading = ref(false)

const promptKeys = computed(() => Object.keys(prompts.value))
const statusLabel = computed(() =>
  ({ draft: '草案', pushed: '已投 L-Port', returned: '已回传' } as Record<string, string>)[status.value] || status.value)
const statusTagType = computed<'success' | 'warning' | 'info'>(() =>
  status.value === 'returned' ? 'success' : status.value === 'pushed' ? 'warning' : 'info')

function engineLabel(k: string): string {
  return ENGINE_OPTS.find(e => e.key === k)?.label || k
}

async function loadPlans() {
  try {
    const r: any = await api.listPlans()
    plans.value = r?.data || []
  } catch {
    ElMessage.error('方案列表拉取失败，后端未起？')
  }
}

function newPlan() {
  curPlanId.value = ''
  form.value = blankForm()
  prompts.value = {}
  status.value = 'draft'
  pushHint.value = ''
  agentAnswer.value = ''
  agentProgress.value = ''
}

async function loadPlan(id: string) {
  if (!id) return newPlan()
  try {
    const r: any = await api.getPlan(id)
    const d = r?.data || {}
    form.value = {
      title: d.title || '',
      intent_text: d.intent_text || '',
      engines: Array.isArray(d.engines) && d.engines.length ? d.engines : [...DEFAULT_ENGINES],
      ref_images: Array.isArray(d.ref_images) ? d.ref_images : [],
      note: d.note || '',
    }
    prompts.value = d.prompts || {}
    status.value = d.status || 'draft'
    pushHint.value = d.push?.package_id ? '已投 ' + d.push.package_id : ''
  } catch (e: any) {
    ElMessage.error('方案拉取失败：' + (e?.response?.data?.msg || e?.message || e))
  }
}

/** 存当前表单；返回生效的方案 id（'' 表示失败）。 */
async function savePlan(): Promise<string> {
  if (!form.value.engines.length) {
    ElMessage.warning('至少选一个目标引擎')
    return ''
  }
  saving.value = true
  try {
    const body: any = {
      title: form.value.title,
      intent_text: form.value.intent_text,
      engines: form.value.engines,
      ref_images: form.value.ref_images,
      note: form.value.note,
    }
    if (curPlanId.value) body.id = curPlanId.value
    const r: any = await api.savePlan(body)
    const d = r?.data || {}
    curPlanId.value = d.id || curPlanId.value
    status.value = d.status || status.value
    await loadPlans()
    return curPlanId.value
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e?.response?.data?.msg || e?.message || e))
    return ''
  } finally {
    saving.value = false
  }
}

async function delPlan() {
  if (!curPlanId.value) return
  try {
    await api.deletePlan(curPlanId.value)
    ElMessage.success('已删除')
    newPlan()
    await loadPlans()
  } catch (e: any) {
    ElMessage.error('删除失败：' + (e?.response?.data?.msg || e?.message || e))
  }
}

async function pushToLport() {
  const id = await savePlan() // 直投前先存，保证包里是最新方案
  if (!id) return
  if (!form.value.intent_text.trim()) return ElMessage.warning('方案还没有意图文本：先与 agent 讨论出方案')
  pushing.value = true
  try {
    const r: any = await api.pushToLport(id)
    const d = r?.data || {}
    pushHint.value = `已投 ${d.package_id || ''}`
    status.value = 'pushed'
    ElMessage.success('已直投 L-Port：' + (d.package_id || ''))
  } catch (e: any) {
    ElMessage.error('直投失败：' + (e?.response?.data?.msg || e?.message || e))
  } finally {
    pushing.value = false
  }
}

async function reload() {
  if (curPlanId.value) await loadPlan(curPlanId.value)
  await loadPlans()
}

async function onRefFile(e: any) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (!f) return
  if (!f.type.startsWith('image/')) return ElMessage.warning('只要图片')
  if (f.size > 10 * 1024 * 1024) return ElMessage.warning('图片超过 10MB')
  refUploading.value = true
  try {
    const d: any = await api.uploadFile(f)
    const row: any = d?.data || d
    form.value.ref_images.push({ name: f.name, path: row.path, url: row.url })
  } catch {
    ElMessage.error('上传失败，后端未起？')
  } finally {
    refUploading.value = false
  }
}

async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text || '')
    ElMessage.success('已复制')
  } catch {
    ElMessage.warning('复制失败（浏览器不放行剪贴板）')
  }
}

function copyPrompt(k: string) {
  const p = prompts.value[k] || {}
  const parts: string[] = []
  if (p.positive) parts.push(p.positive)
  if (p.negative) parts.push('Negative: ' + p.negative)
  copyText(parts.join('\n\n'))
}

function copyAll() {
  const blocks = promptKeys.value.map(k => {
    const p = prompts.value[k] || {}
    const lines = [`【${engineLabel(k)}】`]
    if (p.positive) lines.push(p.positive)
    if (p.negative) lines.push('Negative: ' + p.negative)
    return lines.join('\n')
  })
  copyText(blocks.join('\n\n----------\n\n'))
}

function stopAgent() {
  agentAborter.value?.abort()
}

/** 讨论 brief：让 agent 与主人对齐方案，定稿后调本仓 API 落库（页面刷新即见）。 */
function agentBrief(planId: string): string {
  return [
    `我们来做一张单图的创作方案（Suli 单图创作页，方案 id=${planId}）。`,
    '先在回复里跟我讨论：主体 / 动作 / 环境 / 风格 / 机位 / 光 / 档位（档位只能 SFW|TEEN|NSFW 之一；角色一律成年设定）。',
    '讨论定稿后，把最终方案写成一段「意图文本」——可极简、可口语、可含圈子术语，只承载画面意图（发散成完整叙事与 15 维蓝图是 L-Port 的活）。',
    '然后调接口保存（HTTP POST，JSON）：',
    'POST /api/v1/art/plans',
    `{"id":"${planId}","title":"<标题>","intent_text":"<意图文本>","engines":["novelai","tsubaki3","seedream"],"note":"<约束/改图指令，可空>"}`,
    '保存成功后回复「方案已保存：<标题>」。',
  ].join('\n')
}

async function discussWithAgent() {
  const id = await savePlan()
  if (!id) return
  agentLoading.value = true
  agentProgress.value = '建会话…'
  agentAnswer.value = ''
  try {
    await api.dshEnsure('art', id)
  } catch {
    ElMessage.error('Agent 会话建失败，后端未起？')
    agentLoading.value = false
    agentProgress.value = ''
    return
  }
  const ac = new AbortController()
  agentAborter.value = ac
  agentProgress.value = '讨论中…'
  try {
    let done: any = null
    let errMsg = ''
    await api.dshRunStream(
      { scope: 'art', key: id, message: agentBrief(id) },
      (ev: string, d: any) => {
        if (ev === 'dsh') agentProgress.value = `讨论中…事件 ${d.n ?? ''}`
        else if (ev === 'retry') agentProgress.value = '检测到拒答，自动重试中…'
        else if (ev === 'done') done = d
        else if (ev === 'error') errMsg = d?.msg || '调用失败'
      },
      ac.signal,
    )
    if (done) {
      agentAnswer.value = done.answer || '(空回包)'
      agentProgress.value = '讨论完成'
      await loadPlan(id) // agent 若已落库，这里就刷出来
    } else {
      agentAnswer.value = '[失败] ' + (errMsg || '流中断')
      agentProgress.value = ''
    }
  } catch (e: any) {
    agentAnswer.value = '[失败] ' + (e?.message || e)
    agentProgress.value = ''
  } finally {
    agentLoading.value = false
    agentAborter.value = null
  }
}

onMounted(async () => {
  await loadPlans()
  if (plans.value.length) await loadPlan(plans.value[0].id)
})
</script>

<style scoped>
/* 工作台页统一放开 7xl 居中骨架（theme.css 的 .kun-page 是 96rem + margin:auto），
   否则宽屏下本页卡片被居中封在 1536px，与全宽顶栏（.topbar）左右都对不齐。 */
.kun-page { max-width:none; margin:0; width:100%; box-sizing:border-box }
/* 整页排版：卡片撑满中央工作区高度；内容更高时整页滚动，不裁切 */
.art-studio { min-height:100%; display:flex; flex-direction:column; padding:14px }
.studio-head { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.w-plan { width: 240px; }
.block-title { display:flex; align-items:center; gap:6px; margin:14px 0 6px; font-weight:600; font-size:13px; }
.studio-grid { display:grid; grid-template-columns: minmax(320px, 1fr) minmax(320px, 1fr); gap:18px; margin-top:12px; flex:1 0 auto; min-height:0 }
@media (max-width: 1000px) { .studio-grid { grid-template-columns: 1fr; flex:0 0 auto } }
.studio-col { min-width:0; display:flex; flex-direction:column; min-height:0 }
/* 意图框吃掉左栏剩余高度；右栏提示词列表内部滚动 */
.grow { flex:1 1 0; min-height:130px; display:flex }
.grow :deep(.el-textarea) { flex:1; display:flex }
.grow :deep(.el-textarea__inner) { height:100%; resize:none }
.prompt-scroll { flex:1 1 0; min-height:0; overflow:auto; padding-right:4px }
.empty-fill { flex:1; display:flex; flex-direction:column; justify-content:center }
.row { display:flex; align-items:center; gap:8px; margin-top:8px; flex-wrap:wrap; }
.engines { display:flex; flex-wrap:wrap; gap:4px 12px; }
.refs { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
.ref-item { display:flex; align-items:center; gap:6px; border:1px solid var(--el-border-color-lighter); border-radius:8px; padding:4px 8px; }
.ref-item img { width:40px; height:40px; object-fit:cover; border-radius:6px; }
.ref-name { font-size:12px; max-width:160px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.agent-answer { margin-top:8px; }
.agent-pre { white-space:pre-wrap; font-size:12px; margin:0; max-height:260px; overflow:auto; }
.prompt-card { border:1px solid var(--el-border-color-lighter); border-radius:10px; padding:10px; margin-bottom:10px; }
.prompt-head { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.prompt-row { display:flex; gap:8px; margin-top:6px; }
.prompt-row .lbl { flex:0 0 32px; font-size:12px; color:var(--el-text-color-secondary); }
.prompt-row pre { flex:1; margin:0; white-space:pre-wrap; word-break:break-word; font-size:12px; background:var(--el-fill-color-light); border-radius:6px; padding:6px 8px; }
</style>
