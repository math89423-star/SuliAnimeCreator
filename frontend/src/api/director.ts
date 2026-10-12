import { http } from './http'
export const directorApi = {
  assemble: (shots: any[]) => http.post('/v1/director/prompts/assemble', { shots }).then(r => r.data),
  assembleEpisode: (eid: string, p: any = {}) => http.post(`/v1/director/prompts/assemble-episode/${eid}`, p).then(r => r.data),
  assembleI2VA: (shots: any[], p: any = {}) => http.post('/v1/director/prompts/assemble-i2va', { shots, ...p }).then(r => r.data),
  assembleI2VAEpisode: (eid: string, p: any = {}) => http.post(`/v1/director/prompts/assemble-i2va-episode/${eid}`, p).then(r => r.data),
  exportBundle: (params: any) => http.get('/v1/director/export-bundle', { params, responseType: 'blob' }).then(r => r.data),
  directorTiers: () => http.get('/v1/director/tiers').then(r => r.data),
  directorEngines: () => http.get('/v1/director/engines').then(r => r.data),
}
