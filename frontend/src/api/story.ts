import { http } from './http'
export const storyApi = {
  storySuggest: (idea: string) => http.post('/v1/story/suggest', { idea }).then(r => r.data),
  storyExpand: (idea: string, n = 3) => http.post('/v1/story/expand', { idea, n }).then(r => r.data),
  storyConfirm: (pick: any) => http.post('/v1/story/confirm', { pick }).then(r => r.data),
  storyList: () => http.get('/v1/story/list').then(r => r.data),
  deleteConfirmedOne: (key: string | number) => http.delete(`/v1/story/confirmed/${encodeURIComponent(String(key))}`).then(r => r.data),
  clearConfirmed: () => http.delete('/v1/story/confirmed').then(r => r.data),
  clearDrafts: () => http.delete('/v1/story/drafts').then(r => r.data),
  screenplayGenerate: (p: any) => http.post('/v1/story/screenplay/generate', p).then(r => r.data),
  confirmToEpisode: (pick: any, episode_id: string) => http.post('/v1/story/confirm-to-episode', { pick, episode_id }).then(r => r.data),
}
