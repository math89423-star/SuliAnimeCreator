import { http } from './http'
export const directorApi = {
  assemble: (shots: any[]) => http.post('/v1/director/prompts/assemble', { shots }).then(r => r.data),
  assembleEpisode: (eid: string, p: any = {}) => http.post(`/v1/director/prompts/assemble-episode/${eid}`, p).then(r => r.data),
  assembleI2VA: (shots: any[], p: any = {}) => http.post('/v1/director/prompts/assemble-i2va', { shots, ...p }).then(r => r.data),
  assembleI2VAEpisode: (eid: string, p: any = {}) => http.post(`/v1/director/prompts/assemble-i2va-episode/${eid}`, p).then(r => r.data),
  exportBundle: (params: any) => http.get('/v1/director/export-bundle', { params, responseType: 'blob' }).then(r => r.data),
  // 草案直投 L-Port：写进对方收件箱 suli_packages/<pkg>/（ZIP + story_text 可吃的 package.json），回 package_id，前端轮询回执
  pushToLport: (body: any) => http.post('/v1/director/push-lport', body).then(r => r.data),
  draftDoc: (params: any) => http.get('/v1/director/draft-doc', { params, responseType: 'blob' }).then(r => r.data),
  directorTiers: () => http.get('/v1/director/tiers').then(r => r.data),
  directorEngines: () => http.get('/v1/director/engines').then(r => r.data),
  exportInfo: (episode_id: string) => http.get('/v1/director/export', { params: { episode_id } }).then(r => r.data),
}
