import { ref, computed } from 'vue'
export function usePagination<T>(source: () => T[], size = 8) {
  const page = ref(1)
  const pageSize = ref(size)
  const total = computed(() => source().length)
  const rows = computed(() => {
    const all = source()
    const start = (page.value - 1) * pageSize.value
    return all.slice(start, start + pageSize.value)
  })
  function reset() { page.value = 1 }
  return { page, pageSize, total, rows, reset }
}
