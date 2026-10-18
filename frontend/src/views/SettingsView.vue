<template>
  <div class="kun-page" style="padding:14px">
    <h2 class="page-title">设置</h2>

    <!-- 模型 -->
    <div class="suli-card rel" style="padding:16px;margin-bottom:14px">
      <div v-if="mloading" class="wait-veil"><LoadingSpinner text="加载中…" /></div>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
        <h3 style="margin:0">模型</h3>
        <el-tag size="small" :type="app.health ? 'success' : 'warning'">{{ app.health ? '后端已接通' : '后端未接通' }}</el-tag>
        <span style="flex:1" />
        <el-button size="small" :loading="msaving" type="primary" :disabled="!app.health" @click="saveModels">保存模型配置</el-button>
        <el-button size="small" :disabled="!app.health" @click="loadModels">重新加载</el-button>
      </div>
      <div v-if="merror" class="suli-muted">{{ merror }}</div>
      <el-tabs v-model="mtab">
        <!-- LLM -->
        <el-tab-pane label="LLM（文本）" name="llm">
          <el-form label-width="120px" size="small" style="max-width:640px">
            <el-form-item label="服务商">
              <el-radio-group v-model="models.llm.provider" @change="onProviderChange('llm')">
                <el-radio-button label="opencode">opencode 网关</el-radio-button>
                <el-radio-button label="llamacpp">本地 llama.cpp</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <template v-if="models.llm.provider === 'opencode'">
              <el-form-item label="模型 id">
                <div style="display:flex;gap:8px;flex:1">
                  <el-select v-model="models.llm.model" filterable allow-create clearable placeholder="下拉选择" style="flex:1" @change="fillBaseIfEmpty('llm')">
                    <el-option v-for="o in catalogs.llm" :key="o.id" :label="o.id" :value="o.id" />
                  </el-select>
                  <el-button size="small" :loading="catalogLoading.llm" @click="loadCatalog('llm')">刷新</el-button>
                </div>
              </el-form-item>
              <el-form-item label="网关地址">
                <el-input v-model="models.llm.base" placeholder="https://opencode.ai/zen/go/v1" />
              </el-form-item>
              <el-form-item label="API Key">
                <el-input v-model="keys.llm" type="password" show-password :placeholder="models.llm.api_key_set ? '已设置' : 'API Key'" />
              </el-form-item>
              <el-form-item label="Effort">
                <el-select v-model="models.llm.effort" filterable allow-create clearable placeholder="默认" style="max-width:220px">
                  <el-option label="关 none" value="none" />
                  <el-option label="极简 minimal" value="minimal" />
                  <el-option label="低 low" value="low" />
                  <el-option label="中 medium" value="medium" />
                  <el-option label="高 high" value="high" />
                  <el-option label="超高 xhigh" value="xhigh" />
                </el-select>
                
              </el-form-item>
            </template>
            <template v-else>
              <el-form-item label="服务器地址">
                <el-input v-model="models.llm.local_url" placeholder="http://127.0.0.1:8080" />
              </el-form-item>
              <el-form-item label="模型名">
                <div style="display:flex;gap:8px;flex:1">
                  <el-select v-model="models.llm.local_model" filterable allow-create clearable placeholder="模型 id" style="flex:1">
                    <el-option v-for="o in catalogs.llm" :key="o.id" :label="o.id" :value="o.id" />
                  </el-select>
                  <el-button size="small" :loading="catalogLoading.llm" @click="loadCatalog('llm')">刷新</el-button>
                </div>
              </el-form-item>
              <el-form-item label="Key（可选）">
                <el-input v-model="keys.llm" type="password" show-password placeholder="Key" />
              </el-form-item>
            </template>
            <el-form-item>
              <el-button size="small" :loading="testingModels.llm" :disabled="!app.health" @click="testSection('llm')">测试连接</el-button>
              <span v-if="testResults.llm" class="suli-muted" style="margin-left:8px">{{ testResults.llm }}</span>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <!-- VLM -->
        <el-tab-pane label="VLM（识图）" name="vlm">
          <el-form label-width="120px" size="small" style="max-width:640px">
            <el-form-item label="服务商">
              <el-radio-group v-model="models.vlm.provider" @change="onProviderChange('vlm')">
                <el-radio-button label="opencode">opencode 网关</el-radio-button>
                <el-radio-button label="llamacpp">本地 llama.cpp</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <template v-if="models.vlm.provider === 'opencode'">
              <el-form-item label="模型 id">
                <div style="display:flex;gap:8px;flex:1">
                  <el-select v-model="models.vlm.model" filterable allow-create clearable placeholder="下拉选择" style="flex:1" @change="fillBaseIfEmpty('vlm')">
                    <el-option v-for="o in vlmOptions" :key="o.id" :label="o.id" :value="o.id" />
                  </el-select>
                  <el-button size="small" :loading="catalogLoading.vlm" @click="loadCatalog('vlm')">刷新</el-button>
                </div>
              </el-form-item>
              <el-form-item label="网关地址">
                <el-input v-model="models.vlm.base" placeholder="https://opencode.ai/zen/go/v1" />
              </el-form-item>
              <el-form-item label="API Key">
                <el-input v-model="keys.vlm" type="password" show-password :placeholder="models.vlm.api_key_set ? '已设置' : 'API Key'" />
              </el-form-item>
            </template>
            <template v-else>
              <el-form-item label="服务器地址">
                <el-input v-model="models.vlm.local_url" placeholder="http://127.0.0.1:8080" />
              </el-form-item>
              <el-form-item label="模型名">
                <div style="display:flex;gap:8px;flex:1">
                  <el-select v-model="models.vlm.local_model" filterable allow-create clearable placeholder="模型 id" style="flex:1">
                    <el-option v-for="o in catalogs.vlm" :key="o.id" :label="o.id" :value="o.id" />
                  </el-select>
                  <el-button size="small" :loading="catalogLoading.vlm" @click="loadCatalog('vlm')">刷新</el-button>
                </div>
              </el-form-item>
              <el-form-item label="Key（可选）">
                <el-input v-model="keys.vlm" type="password" show-password placeholder="Key" />
              </el-form-item>
            </template>
            <el-form-item>
              <el-button size="small" :loading="testingModels.vlm" :disabled="!app.health" @click="testSection('vlm')">测试连接</el-button>
              <span v-if="testResults.vlm" class="suli-muted" style="margin-left:8px">{{ testResults.vlm }}</span>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <!-- 绘图 -->
        <el-tab-pane label="绘图模型" name="image">
          <el-form label-width="120px" size="small" style="max-width:640px">
            <el-form-item label="服务商">
              <el-radio-group v-model="models.image.provider">
                <el-radio-button label="sd-webui">SD WebUI</el-radio-button>
                <el-radio-button label="comfyui">ComfyUI</el-radio-button>
                <el-radio-button label="custom">自定义接口</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="接口地址">
              <el-input v-model="models.image.endpoint" :placeholder="models.image.provider === 'comfyui' ? 'http://127.0.0.1:8188' : 'http://127.0.0.1:7860'" />
            </el-form-item>
            <el-form-item label="模型 / Checkpoint">
              <el-input v-model="models.image.model" placeholder="模型名" />
            </el-form-item>
            <el-form-item label="Key（可选）">
              <el-input v-model="keys.image" type="password" show-password :placeholder="models.image.api_key_set ? '已设置' : 'API Key'" />
            </el-form-item>
            <el-form-item>
              <el-button size="small" :loading="testingModels.image" :disabled="!app.health" @click="testSection('image')">测试连接</el-button>
              <span v-if="testResults.image" class="suli-muted" style="margin-left:8px">{{ testResults.image }}</span>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <el-skeleton v-if="mloading" :rows="4" animated />
    </div>

    <div class="suli-grid-3" style="grid-template-columns:repeat(2,minmax(0,1fr))">
      <!-- 外观 -->
      <div class="suli-card" style="padding:16px">
        <h3>外观</h3>
        <el-form label-width="130px" size="small">
          <el-form-item label="主题色">
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
              <el-button
                v-for="p in ACCENT_PRESETS" :key="p.value"
                :type="s.settings.accent === p.value ? 'primary' : 'default'"
                @click="s.settings.accent = p.value"
              >
                <span class="dot" :style="{ background: p.value }" />{{ p.label }}
              </el-button>
              <el-color-picker v-model="s.settings.accent" :show-alpha="false" />
            </div>
          </el-form-item>
          <el-form-item label="紧凑模式">
            <el-switch v-model="s.settings.compact" active-text="开" inactive-text="关" />
          </el-form-item>
        </el-form>
      </div>

      <!-- 布局 -->
      <div class="suli-card" style="padding:16px">
        <h3>布局</h3>
        <el-form label-width="150px" size="small">
          <el-form-item label="左侧导航默认收起">
            <el-switch v-model="s.settings.leftCollapsed" active-text="收起" inactive-text="展开" @change="syncLayout" />
          </el-form-item>
          <el-form-item label="右侧 Agent 默认收起">
            <el-switch v-model="s.settings.rightCollapsed" active-text="收起" inactive-text="展开" @change="syncLayout" />
          </el-form-item>
        </el-form>
      </div>

      <!-- 工作台 -->
      <div class="suli-card" style="padding:16px">
        <h3>工作台</h3>
        <el-form label-width="130px" size="small">
          <el-form-item label="大纲生成模式">
            <el-radio-group v-model="s.settings.outlineMode">
              <el-radio-button label="lite">轻生成</el-radio-button>
              <el-radio-button label="expert">专家dsh</el-radio-button>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </div>

      <!-- 后端 -->
      <div class="suli-card" style="padding:16px">
        <h3>后端连接</h3>
        <el-form label-width="130px" size="small">
          <el-form-item label="接口地址">
            <el-input :model-value="http.defaults.baseURL" readonly style="max-width:260px" />
          </el-form-item>
          <el-form-item label="状态">
            <el-tag :type="app.health ? 'success' : 'warning'" size="small">
              {{ app.health ? '后端已接通' : '本地Mock / 未接通' }}
            </el-tag>
          </el-form-item>
          <el-form-item>
            <el-button size="small" type="primary" :loading="testing" @click="test">测试连接</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 数据 / 关于 -->
    <div class="suli-card" style="padding:16px;margin-top:14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap">
      <div>
        <h3 style="margin:0">数据与关于</h3>
      </div>
      <span style="flex:1" />
      <el-popconfirm title="恢复全部默认设置？" @confirm="onReset">
        <template #reference><el-button size="small">恢复默认</el-button></template>
      </el-popconfirm>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useSettingsStore, ACCENT_PRESETS } from '../stores/settings'
import { useAppStore } from '../stores/app'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import { http, api } from '../api/client'
import { once } from '../utils/inflight'

interface TextModelCfg {
  provider: string; model: string; base: string
  local_url: string; local_model: string; api_key_set?: boolean
  effort?: string
}
interface ImageModelCfg { provider: string; endpoint: string; model: string; api_key_set?: boolean }

const s = useSettingsStore()
const app = useAppStore()
const testing = ref(false)

// ---- 模型配置（存后端） ----
const mtab = ref('llm')
const mloading = ref(false)
const msaving = ref(false)
const merror = ref('')
const models = ref<{ llm: TextModelCfg; vlm: TextModelCfg; image: ImageModelCfg }>({
  llm: { provider: 'opencode', model: '', base: '', local_url: '', local_model: '' },
  vlm: { provider: 'opencode', model: '', base: '', local_url: '', local_model: '' },
  image: { provider: 'sd-webui', endpoint: '', model: '' },
})
const keys = ref({ llm: '', vlm: '', image: '' })
const testResults = ref<Record<string, string>>({})
const testingModels = ref<Record<string, boolean>>({})

// ---- 模型下拉目录 ----
const OPENCODE_DEFAULT_BASE = 'https://opencode.ai/zen/go/v1'
const catalogs = ref<Record<'llm' | 'vlm', { id: string; endpoint: string }[]>>({ llm: [], vlm: [] })
const catalogLoading = ref<Record<string, boolean>>({})
const vlmOptions = computed(() => catalogs.value.vlm.filter(o => o.endpoint === 'chat/completions'))

function fillBaseIfEmpty(sec: 'llm' | 'vlm', base = OPENCODE_DEFAULT_BASE) {
  if (!models.value[sec].base.trim()) models.value[sec].base = base
}

async function loadCatalog(sec: 'llm' | 'vlm') {
  const cfg = models.value[sec]
  const url = cfg.provider === 'opencode' ? cfg.base : cfg.local_url
  const key = keys.value[sec]
  catalogLoading.value[sec] = true
  try {
    // 并发去重：llm/vlm 同配置、页面重挂载、连点刷新都只发一次请求
    const d = (await once(`catalog|${cfg.provider}|${url}|${key}`, () => api.getModelCatalog(cfg.provider, url, key))).data
    catalogs.value[sec] = d?.models || []
    if (cfg.provider === 'opencode' && d?.base) fillBaseIfEmpty(sec, d.base)
    const src = d?.source === 'curated' ? '，离线兜底' : d?.source === 'cache' ? '，缓存' : ''
    testResults.value[sec] = `模型列表已更新（${(d?.models || []).length} 个${src}）`
  } catch (e: any) {
    testResults.value[sec] = '列表失败：' + (e?.response?.data?.msg || e?.message || '未知错误')
  } finally {
    catalogLoading.value[sec] = false
  }
}

function onProviderChange(sec: 'llm' | 'vlm') {
  fillBaseIfEmpty(sec)
  loadCatalog(sec)
}

async function loadModels() {
  merror.value = ''
  if (!app.health) { merror.value = '后端未接通，模型配置暂不可用（后端 python run.py）'; return }
  mloading.value = true
  try {
    const d = (await api.getModelSettings()).data
    if (d?.llm) models.value.llm = d.llm
    if (d?.vlm) models.value.vlm = d.vlm
    if (d?.image) models.value.image = d.image
    keys.value = { llm: '', vlm: '', image: '' }
    loadCatalog('llm')
    loadCatalog('vlm')
  } catch {
    ElMessage.error('模型配置加载失败')
  } finally {
    mloading.value = false
  }
}

async function saveModels() {
  msaving.value = true
  try {
    const payload = {
      llm: { ...models.value.llm, api_key: keys.value.llm },
      vlm: { ...models.value.vlm, api_key: keys.value.vlm },
      image: { ...models.value.image, api_key: keys.value.image },
    }
    const d = (await api.saveModelSettings(payload)).data
    if (d?.llm) models.value.llm = d.llm
    if (d?.vlm) models.value.vlm = d.vlm
    if (d?.image) models.value.image = d.image
    keys.value = { llm: '', vlm: '', image: '' }
    ElMessage.success('模型配置已保存')
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e?.response?.data?.msg || e?.message || '未知错误'))
  } finally {
    msaving.value = false
  }
}

async function testSection(sec: 'llm' | 'vlm' | 'image') {
  testingModels.value[sec] = true
  testResults.value[sec] = ''
  try {
    const cfg = { ...(models.value[sec] as any), api_key: keys.value[sec] }
    const d = (await api.testModelSetting(sec, cfg)).data
    testResults.value[sec] = d?.detail || '连通正常'
  } catch (e: any) {
    testResults.value[sec] = '失败：' + (e?.response?.data?.msg || e?.message || '未知错误')
  } finally {
    testingModels.value[sec] = false
  }
}

function syncLayout() {
  app.leftCollapsed = s.settings.leftCollapsed
  app.rightCollapsed = s.settings.rightCollapsed
}

async function test() {
  testing.value = true
  try {
    app.health = (await api.health()).data
    ElMessage.success('后端已接通')
  } catch {
    app.health = null
    ElMessage.error('后端未起：后端 python run.py ＋ 前端 npm run dev')
  } finally {
    testing.value = false
  }
}

function onReset() {
  s.reset()
  syncLayout()
  ElMessage.success('已恢复默认设置')
}

onMounted(async () => {
  s.apply()
  try { app.health = (await api.health()).data } catch { app.health = null }
  await loadModels()
})
</script>

<style scoped>
/* 与顶栏对齐：取消96rem居中限宽，铺满中央区 */
.kun-page{max-width:none;margin:0;width:100%;box-sizing:border-box}
.dot{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:6px;vertical-align:-1px;border:1px solid rgba(0,0,0,.15)}
@media (max-width: 900px) {
  .suli-grid-3{grid-template-columns:1fr !important}
}
</style>
<style>
.suli-compact{--suli-radius:10px;--suli-radius-sm:8px}
.suli-compact .suli-card{border-width:1px}
</style>
