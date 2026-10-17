import { http } from './http'

export const projectApi = {
  listProjects: () => http.get('/v1/projects').then(r => r.data),
  createProject: (name: string, extra: any = {}) => http.post('/v1/projects', { name, ...extra }).then(r => r.data),
  updateProject: (pid: string, p: any) => http.put(`/v1/projects/${pid}`, p).then(r => r.data),
  deleteProject: (pid: string, mode: 'detach' | 'cascade' = 'detach') =>
    http.delete(`/v1/projects/${pid}`, { params: { mode }, data: { mode } }).then(r => r.data),
  listProjectEpisodes: (pid: string) => http.get(`/v1/projects/${pid}/episodes`).then(r => r.data),
  createProjectEpisode: (pid: string, p: { episode_id?: string; title?: string; move?: boolean } = {}) =>
    http.post(`/v1/projects/${pid}/episodes`, p).then(r => r.data),
  removeProjectEpisode: (pid: string, eid: string, mode: 'unregister' | 'delete' = 'unregister') =>
    http.delete(`/v1/projects/${pid}/episodes/${encodeURIComponent(eid)}`, { params: { mode }, data: { mode } }).then(r => r.data),
}
