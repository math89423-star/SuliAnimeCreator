import { http } from './http'
export const storyApi = {
  listProjects: () => http.get('/v1/projects').then(r => r.data),
  createProject: (name: string) => http.post('/v1/projects', { name }).then(r => r.data),
  storySuggest: (idea: string) => http.post('/v1/story/suggest', { idea }).then(r => r.data),
  storyExpand: (idea: string, n = 3) => http.post('/v1/story/expand', { idea, n }).then(r => r.data),
  storyConfirm: (pick: any) => http.post('/v1/story/confirm', { pick }).then(r => r.data),
  storyList: () => http.get('/v1/story/list').then(r => r.data),
  screenplayGenerate: (p: any) => http.post('/v1/story/screenplay/generate', p).then(r => r.data),
  confirmToEpisode: (pick: any, episode_id: string) => http.post('/v1/story/confirm-to-episode', { pick, episode_id }).then(r => r.data),
}
