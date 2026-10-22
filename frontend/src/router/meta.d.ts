import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    icon?: string
    /** 这一页不挂右侧 Agent 栏 */
    noRightChat?: boolean
  }
}
