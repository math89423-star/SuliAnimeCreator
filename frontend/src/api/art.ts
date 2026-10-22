import { http } from './http'

/** 单图创作（art plan）：方案 CRUD → 直投 L-Port 收件箱 → 各引擎提示词回传收口。 */
export const artPlanApi = {
  /** 方案列表（投影：不含提示词正文，只给状态与计数）。 */
  listPlans: () => http.get('/v1/art/plans').then(r => r.data),
  /** 方案详情（带 prompts / blueprint）。 */
  getPlan: (id: string) => http.get(`/v1/art/plans/${id}`).then(r => r.data),
  /** 方案轻量状态（回传等待轮询：不含提示词正文）。 */
  planStatus: (id: string) => http.get(`/v1/art/plans/${id}/status`).then(r => r.data),
  /** 建/改方案（agent 讨论定稿后也调这里落库）。 */
  savePlan: (body: any) => http.post('/v1/art/plans', body).then(r => r.data),
  deletePlan: (id: string) => http.delete(`/v1/art/plans/${id}`).then(r => r.data),
  /** 直投 L-Port：写收件箱 suli_packages/<pkg>/（包型 art_plan），回 package_id。 */
  pushToLport: (plan_id: string) => http.post('/v1/art/push-lport', { plan_id }).then(r => r.data),
  /** 回程收口（L-Port 调；本仓页面用不到，留作审计/自测）。 */
  importPrompts: (body: any) => http.post('/v1/art/prompts/import', body).then(r => r.data),
  /** 漫画页序列（页条）：带 page 上下文的方案，按页序升序。 */
  listComics: (episode_id = '') => http.get('/v1/art/comics', { params: { episode_id } }).then(r => r.data),
  /** 挂本页成图（漫画页）：传图落 uploads 并写进方案的 page.image。 */
  uploadPlanImage: (id: string, f: File) => { const fd = new FormData(); fd.append('file', f); return http.post(`/v1/art/plans/${id}/image`, fd).then(r => r.data) },
  /** 撤掉本页成图（文件仍留在 uploads）。 */
  deletePlanImage: (id: string) => http.delete(`/v1/art/plans/${id}/image`).then(r => r.data),
  /** 读本集漫画剧本（页/格分条）。 */
  getComicScript: (episode_id: string) => http.get('/v1/art/comic-script', { params: { episode_id } }).then(r => r.data),
  /** 存本集漫画剧本（整体覆盖）。 */
  saveComicScript: (body: any) => http.post('/v1/art/comic-script', body).then(r => r.data),
  /** 从本集大纲转成漫画剧本（冷启动）。 */
  comicScriptFromOutline: (body: any) => http.post('/v1/art/comic-script/from-outline', body).then(r => r.data),
  /** 拆格：一条剧本 = 一个方案（页序/格序/上一格链自动排好）。 */
  splitComicScript: (body: any) => http.post('/v1/art/comic-script/split', body).then(r => r.data),
}
