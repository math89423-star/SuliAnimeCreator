import { http } from './http'
export const trafficApi = {
  generate: (p: any) => http.post('/v1/traffic/generate', p).then(r => r.data),
  library: (episode_id = '') => http.get('/v1/traffic/library', { params: episode_id ? { episode_id } : {} }).then(r => r.data),
  analyzeRefVideo: (path: string) => http.post('/v1/traffic/ref-video/analyze', { path }).then(r => r.data),
  packages: () => http.get('/v1/traffic/packages').then(r => r.data),
  package: (id: string) => http.get(`/v1/traffic/package/${id}`).then(r => r.data),
  deletePackage: (id: string) => http.delete(`/v1/traffic/packages/${id}`).then(r => r.data),
  exportTrafficBundle: (package_id: string) => http.get('/v1/traffic/export-bundle', { params: { package_id }, responseType: 'blob' }).then(r => r.data),
  // 直投 L-Port：写进对方收件箱（共享挂载），run=true 时顺带触发出片
  pushToLport: (package_id: string, run = false, limit = 0) =>
    http.post('/v1/traffic/push-lport', { package_id, run, limit }).then(r => r.data),
  feedback: (p: any) => http.post('/v1/traffic/feedback', p).then(r => r.data),
  report: (package_id: string) => http.get(`/v1/traffic/report/${package_id}`).then(r => r.data),
  assets: (params: any = {}) => http.get('/v1/traffic/assets', { params }).then(r => r.data),
  rescanAssets: () => http.post('/v1/traffic/assets/rescan').then(r => r.data),
  renameAsset: (p: any) => http.post('/v1/traffic/assets/rename', p).then(r => r.data),
  deleteAssets: (items: any[]) => http.delete('/v1/traffic/assets', { data: { items } } as any).then(r => r.data),
}
