import { http } from './http'

/** 报告库（拉片 / 深度拆解分析报告，后端自动入库） */
export const reportsApi = {
  reportList: (kind = '') => http.get('/v1/reports' + (kind ? `?kind=${kind}` : '')).then(r => r.data),
  reportGet: (id: string) => http.get(`/v1/reports/${encodeURIComponent(id)}`).then(r => r.data),
  reportDelete: (id: string) => http.delete(`/v1/reports/${encodeURIComponent(id)}`).then(r => r.data),
}
