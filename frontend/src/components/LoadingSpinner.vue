<template>
  <span class="load-spin" :style="{ width: size + 'px', height: size + 'px' }" />
  <span v-if="text" class="load-text">{{ text }}</span>
</template>
<script setup lang="ts">
withDefaults(defineProps<{ size?: number; text?: string }>(), { size: 16, text: '' })
</script>
<style scoped>
.load-spin {
  display: inline-block; flex-shrink: 0; border-radius: 50%;
  border: 2px solid var(--el-border-color, #dcdfe6);
  border-top-color: var(--suli-primary, #ec4899);
  animation: load-rot 0.8s linear infinite; vertical-align: -3px;
}
.load-text { font-size: 12px; color: var(--suli-text-2, #909399); margin-left: 6px; }
@keyframes load-rot { to { transform: rotate(360deg); } }
</style>
