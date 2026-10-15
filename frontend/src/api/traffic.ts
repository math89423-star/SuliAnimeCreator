import { http } from './http'
export const trafficApi = {
  generate: (p: any) => http.post('/v1/traffic/generate', p).then(r => r.data),
  library: (episode_id = '') => http.get('/v1/traffic/library', { params: episode_id ? { episode_id } : {} }).then(r => r.data),
  analyzeRefVideo: (path: string) => http.post('/v1/traffic/ref-video/analyze', { path }).then(r => r.data),
  packages: () => http.get('/v1/traffic/packages').then(r => r.data),
  package: (id: string) => http.get(`/v1/traffic/package/${id}`).then(r => r.data),
  exportBundle: (package_id: string) => http.get('/v1/traffic/export-bundle', { params: { package_id }, responseType: 'blob' }).then(r => r.data),
  feedback: (p: any) => http.post('/v1/traffic/feedback', p).then(r => r.data),
  report: (package_id: string) => http.get(`/v1/traffic/report/${package_id}`).then(r => r.data),
  demoSeed: (episode_id: string) => http.get('/v1/demo/seed', { params: { episode_id } }).then(r => r.data),
}
