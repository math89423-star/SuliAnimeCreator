import { http } from './http'

/** 单图创作（art plan）：方案 CRUD → 直投 L-Port 收件箱 → 各引擎提示词回传收口。 */
export const artPlanApi = {
  /** 方案列表（投影：不含提示词正文，只给状态与计数）。 */
  listPlans: () => http.get('/v1/art/plans').then(r => r.data),
  /** 方案详情（带 prompts / blueprint）。 */
  getPlan: (id: string) => http.get(`/v1/art/plans/${id}`).then(r => r.data),
  /** 建/改方案（agent 讨论定稿后也调这里落库）。 */
  savePlan: (body: any) => http.post('/v1/art/plans', body).then(r => r.data),
  deletePlan: (id: string) => http.delete(`/v1/art/plans/${id}`).then(r => r.data),
  /** 直投 L-Port：写收件箱 suli_packages/<pkg>/（包型 art_plan），回 package_id。 */
  pushToLport: (plan_id: string) => http.post('/v1/art/push-lport', { plan_id }).then(r => r.data),
  /** 回程收口（L-Port 调；本仓页面用不到，留作审计/自测）。 */
  importPrompts: (body: any) => http.post('/v1/art/prompts/import', body).then(r => r.data),
}
