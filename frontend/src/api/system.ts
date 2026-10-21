import { http } from './http'
export const systemApi = {
  health: () => http.get('/health').then(r => r.data),
  artTools: () => http.get('/v1/art/tools').then(r => r.data),
  imageModels: () => http.get('/v1/art/image-models').then(r => r.data),
  getModelSettings: () => http.get('/v1/settings/models').then(r => r.data),
  saveModelSettings: (p: any) => http.put('/v1/settings/models', p).then(r => r.data),
  testModelSetting: (section: string, config: any) => http.post('/v1/settings/models/test', { section, config }).then(r => r.data),
  getModelCatalog: (provider: string, base = '', key = '', force = false) => http.post('/v1/settings/models/catalog', { provider, base, key, force }).then(r => r.data),
  receipts: (params: string | Record<string, string> = '') => http.get('/v1/receipts', {
    params: typeof params === 'string' ? (params ? { package_id: params } : {}) : (params || {}),
  }).then(r => r.data),
  addReceipt: (p: any) => http.post('/v1/receipts', p).then(r => r.data),
}
