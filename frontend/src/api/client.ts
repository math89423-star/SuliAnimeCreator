import axios from 'axios'
export const http = axios.create({ baseURL: '/api', timeout: 15000 })
export const api = {
  health: () => http.get('/health').then(r => r.data),
  listProjects: () => http.get('/v1/projects').then(r => r.data),
  createProject: (name: string) => http.post('/v1/projects', { name }).then(r => r.data),
  storySuggest: (idea: string) => http.post('/v1/story/suggest', { idea }).then(r => r.data),
  storyConfirm: (pick: any) => http.post('/v1/story/confirm', { pick }).then(r => r.data),
  storyList: () => http.get('/v1/story/list').then(r => r.data),
  listCharacters: () => http.get('/v1/characters').then(r => r.data),
  gallery: () => http.get('/v1/characters/gallery').then(r => r.data),
  createCharacter: (p: any) => http.post('/v1/characters', p).then(r => r.data),
  updateCharacter: (id: string, p: any) => http.put(`/v1/characters/${id}`, p).then(r => r.data),
  charConstants: () => http.get('/v1/characters/constants').then(r => r.data),
  listAssets: (id: string) => http.get(`/v1/characters/${id}/assets`).then(r => r.data),
  addAssetMeta: (id: string, p: any) => http.post(`/v1/characters/${id}/assets`, p).then(r => r.data),
  listSlotPrompts: (id: string) => http.get(`/v1/characters/${id}/slot-prompts`).then(r => r.data),
  genSlotPrompt: (id: string, kind: string, slot: string) => http.post(`/v1/characters/${id}/slot-prompts/generate`, { kind, slot }).then(r => r.data),
  saveSlotPrompt: (id: string, kind: string, slot: string, prompt: string) => http.put(`/v1/characters/${id}/slot-prompts`, { kind, slot, prompt }).then(r => r.data),
  listOutfits: (id: string) => http.get(`/v1/characters/${id}/outfits`).then(r => r.data),
  createOutfit: (id: string, p: any) => http.post(`/v1/characters/${id}/outfits`, p).then(r => r.data),
  deleteOutfit: (id: string, oid: number) => http.delete(`/v1/characters/${id}/outfits/${oid}`).then(r => r.data),
  activateOutfit: (id: string, oid: number) => http.post(`/v1/characters/${id}/outfits/${oid}/activate`).then(r => r.data),
  listOutfitCats: (id: string) => http.get(`/v1/characters/${id}/outfit-categories`).then(r => r.data),
  saveOutfitCat: (id: string, category: string, description: string) => http.put(`/v1/characters/${id}/outfit-categories`, { category, description }).then(r => r.data),
  getDoc: (id: string) => http.get(`/v1/characters/${id}/doc`).then(r => r.data),
  saveDoc: (id: string, doc_html: string) => http.put(`/v1/characters/${id}/doc`, { doc_html }).then(r => r.data),
  iterate: (id: string, dimension: string, instruction: string) => http.post(`/v1/characters/${id}/iterate`, { dimension, instruction }).then(r => r.data),
  listVersions: (id: string) => http.get(`/v1/characters/${id}/versions`).then(r => r.data),
  rollback: (id: string, version_id: number) => http.post(`/v1/characters/${id}/rollback`, { version_id }).then(r => r.data),
  freezeVersions: (id: string) => http.post(`/v1/characters/${id}/freeze`).then(r => r.data),
  pack: (id: string) => http.get(`/v1/characters/${id}/pack`).then(r => r.data),
  saveScreenplay: (eid: string, md: string) => http.put(`/v1/scriptboard/screenplay/${eid}`, { screenplay_md: md }).then(r => r.data),
  autoSplit: (eid: string, story_md: string, use_llm = false) => http.post(`/v1/scriptboard/auto-split/${eid}`, { story_md, use_llm }).then(r => r.data),
  uploadFile: (f: File) => { const fd = new FormData(); fd.append('file', f); return http.post('/v1/uploads', fd).then(r => r.data) },
  uploadAvatar: (id: string, f: File) => { const fd = new FormData(); fd.append('file', f); return http.post(`/v1/characters/${id}/avatar`, fd).then(r => r.data) },
  uploadSlotImage: (id: string, kind: string, slot: string, f: File) => { const fd = new FormData(); fd.append('file', f); fd.append('kind', kind); fd.append('slot', slot); return http.post(`/v1/characters/${id}/assets/file`, fd).then(r => r.data) },
  listShots: (eid: string) => http.get('/v1/scriptboard/shots', { params: { episode_id: eid } }).then(r => r.data),
  createShot: (p: any) => http.post('/v1/scriptboard/shots', p).then(r => r.data),
  uploadShotImage: (sid: string, f: File, kind = 'ref') => { const fd = new FormData(); fd.append('file', f); fd.append('kind', kind); return http.post(`/v1/scriptboard/shots/${sid}/image`, fd).then(r => r.data) },
  deleteShotImage: (sid: string, name: string) => http.delete(`/v1/scriptboard/shots/${sid}/image/${name}`).then(r => r.data),
  reviewStat: (eid: string) => http.get(`/v1/scriptboard/review/${eid}`).then(r => r.data),
  reviewRun: (eid: string) => http.post(`/v1/scriptboard/review/run/${eid}`).then(r => r.data),
  updateShot: (sid: string, p: any) => http.put(`/v1/scriptboard/shots/${sid}`, p).then(r => r.data),
  deleteShot: (sid: string) => http.delete(`/v1/scriptboard/shots/${sid}`).then(r => r.data),
  assemble: (shots: string[]) => http.post('/v1/director/prompts/assemble', { shots }).then(r => r.data),
  assembleEpisode: (eid: string, p: any = {}) => http.post(`/v1/director/prompts/assemble-episode/${eid}`, p).then(r => r.data),
  artTools: () => http.get('/v1/art/tools').then(r => r.data),
  receipts: (package_id = '') => http.get('/v1/receipts', { params: package_id ? { package_id } : {} }).then(r => r.data),
  addReceipt: (p: any) => http.post('/v1/receipts', p).then(r => r.data),
  dshSessions: (scope = '') => http.get('/v1/dsh/sessions', { params: scope ? { scope } : {} }).then(r => r.data),
  dshEnsure: (scope: string, key: string) => http.post('/v1/dsh/sessions', { scope, key }).then(r => r.data),
  dshRun: (p: { scope: string; key: string; message: string; session_id?: string }) => http.post('/v1/dsh/run', p, { timeout: 200000 }).then(r => r.data),
  dshRunStream: async (p: { scope: string; key: string; message: string; session_id?: string }, onEvent: (ev: string, data: any) => void, signal?: AbortSignal) => {
    const res = await fetch('/api/v1/dsh/stream', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(p), signal,
    })
    if (!res.ok || !res.body) throw new Error('stream HTTP ' + res.status)
    const reader = res.body.getReader()
    const dec = new TextDecoder()
    let buf = ''
    let evName = ''
    const pump = async (): Promise<void> => {
      const { done, value } = await reader.read()
      if (done) return
      buf += dec.decode(value, { stream: true })
      let idx: number
      while ((idx = buf.indexOf('\n\n')) >= 0) {
        const frame = buf.slice(0, idx)
        buf = buf.slice(idx + 2)
        let data = ''
        for (const line of frame.split('\n')) {
          if (line.startsWith('event:')) evName = line.slice(6).trim()
          else if (line.startsWith('data:')) data += line.slice(5).trim()
        }
        if (evName && data) {
          try { onEvent(evName, JSON.parse(data)) } catch { onEvent(evName, { raw: data }) }
          evName = ''
        }
      }
      return pump()
    }
    await pump()
  },
}
export const DIMS = [
  { key: 'hairstyle', label: '发型' }, { key: 'face', label: '面部' },
  { key: 'physique', label: '体态' }, { key: 'identity', label: '身份' },
]
