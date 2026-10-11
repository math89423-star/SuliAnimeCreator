import { defineAsyncComponent } from 'vue'
// 美术工具原生组件注册表：懒加载，首屏不进包
export const TOOL_TABS = [
  { id: 'composition-camera', name: '构图', desc: '景别/机位/透视/构图' },
  { id: 'costume', name: '服装', desc: '18流派198单品+搭配' },
  { id: 'palette', name: '配色', desc: '15系764色+和色465' },
  { id: 'flowers', name: '花语', desc: '101花三层花语+tag' },
  { id: 'naming', name: '取名', desc: '75招+91撞名自检' },
  { id: 'shot-grammar', name: '镜头', desc: '运镜31/机位21/景别7' },
  { id: 'nsfw-guide', name: '分级', desc: '九槽+模型分流' },
]
export const TOOL_COMPONENTS: Record<string, any> = {
  'composition-camera': defineAsyncComponent(() => import('./CompositionCamera.vue')),
  'costume': defineAsyncComponent(() => import('./CostumeTool.vue')),
  'palette': defineAsyncComponent(() => import('./PaletteTool.vue')),
  'flowers': defineAsyncComponent(() => import('./FlowersTool.vue')),
  'naming': defineAsyncComponent(() => import('./NamingTool.vue')),
  'shot-grammar': defineAsyncComponent(() => import('./ShotGrammar.vue')),
  'nsfw-guide': defineAsyncComponent(() => import('./NsfwGuide.vue')),
}
