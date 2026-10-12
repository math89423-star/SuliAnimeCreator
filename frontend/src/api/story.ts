import { http } from './http'
export const storyApi = {
  listProjects: () => http.get('/v1/projects').then(r => r.data),
  createProject: (name: string) => http.post('/v1/projects', { name }).then(r => r.data),
  storySuggest: (idea: string) => http.post('/v1/story/suggest', { idea }).then(r => r.data),
  storyConfirm: (pick: any) => http.post('/v1/story/confirm', { pick }).then(r => r.data),
  storyList: () => http.get('/v1/story/list').then(r => r.data),
}
