import { http } from './http'
export const boardApi = {
  saveScreenplay: (eid: string, md: string) => http.put(`/v1/scriptboard/screenplay/${eid}`, { screenplay_md: md }).then(r => r.data),
  getOutline: (eid: string) => http.get(`/v1/scriptboard/outline/${eid}`).then(r => r.data),
  saveOutline: (eid: string, p: any) => http.put(`/v1/scriptboard/outline/${eid}`, p).then(r => r.data),
  autoSplit: (eid: string, story_md: string, use_llm = false) => http.post(`/v1/scriptboard/auto-split/${eid}`, { story_md, use_llm }).then(r => r.data),
  uploadFile: (f: File) => { const fd = new FormData(); fd.append('file', f); return http.post('/v1/uploads', fd).then(r => r.data) },
  listShots: (eid: string) => http.get('/v1/scriptboard/shots', { params: { episode_id: eid } }).then(r => r.data),
  createShot: (p: any) => http.post('/v1/scriptboard/shots', p).then(r => r.data),
  uploadShotImage: (sid: string, f: File, kind = 'ref', extra: any = {}) => { const fd = new FormData(); fd.append('file', f); fd.append('kind', kind); if (extra.role) fd.append('role', extra.role); if (extra.desc) fd.append('desc', extra.desc); return http.post(`/v1/scriptboard/shots/${sid}/image`, fd).then(r => r.data) },
  setShotImageMeta: (sid: string, name: string, meta: any) => http.post(`/v1/scriptboard/shots/${sid}/image/meta`, { name, ...meta }).then(r => r.data),
  attachShotImage: (sid: string, name: string, kind = 'first') => http.post(`/v1/scriptboard/shots/${sid}/image/attach`, { name, kind }).then(r => r.data),
  deleteShotImage: (sid: string, name: string) => http.delete(`/v1/scriptboard/shots/${sid}/image/${name}`).then(r => r.data),
  reviewStat: (eid: string) => http.get(`/v1/scriptboard/review/${eid}`).then(r => r.data),
  reviewRun: (eid: string) => http.post(`/v1/scriptboard/review/run/${eid}`).then(r => r.data),
  updateShot: (sid: string, p: any) => http.put(`/v1/scriptboard/shots/${sid}`, p).then(r => r.data),
  deleteShot: (sid: string) => http.delete(`/v1/scriptboard/shots/${sid}`).then(r => r.data),
}
