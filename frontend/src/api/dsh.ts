import { http } from './http'

/** SSE 解析（`event:`/`data:` 帧）：/stream 与 /runs/<id>/stream 共用 */
async function readSSE(res: Response, onEvent: (ev: string, data: any) => void): Promise<void> {
  const reader = res.body!.getReader()
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
        // `: ping` 心跳注释行直接忽略
      }
      if (evName && data) {
        try { onEvent(evName, JSON.parse(data)) } catch { onEvent(evName, { raw: data }) }
        evName = ''
      }
    }
    return pump()
  }
  await pump()
}

async function openSSE(url: string, init: RequestInit, onEvent: (ev: string, data: any) => void): Promise<void> {
  let res: Response
  try {
    res = await fetch(url, init)
  } catch (e: any) {
    throw new Error('stream fetch failed: ' + (e?.message || e))
  }
  if (!res.ok || !res.body) {
    let body = ''
    try { body = await res.text() } catch {}
    throw new Error('stream HTTP ' + res.status + (body ? ' ' + body.slice(0, 200) : ''))
  }
  await readSSE(res, onEvent)
}

export const dshApi = {
  dshSessions: (scope = '') => http.get('/v1/dsh/sessions', { params: scope ? { scope } : {} }).then(r => r.data),
  dshEnsure: (scope: string, key: string) => http.post('/v1/dsh/sessions', { scope, key }).then(r => r.data),
  // 单会话收敛：一集一会话，默认 scope=episode key=episodeId，不再按角色/故事分域建会话
  dshEnsureEpisode: (episodeId: string) => http.post('/v1/dsh/sessions', { scope: 'episode', key: episodeId }).then(r => r.data),
  dshSkills: () => http.get('/v1/dsh/skills').then(r => r.data),
  dshDeleteSession: (scope: string, key: string) => http.delete('/v1/dsh/sessions', { data: { scope, key }, params: { scope, key } }).then(r => r.data),
  dshRename: (scope: string, key: string, new_key: string) => http.put('/v1/dsh/sessions/rename', { scope, key, new_key }).then(r => r.data),
  dshRun: (p: { scope: string; key: string; message: string; session_id?: string }) => http.post('/v1/dsh/run', p, { timeout: 200000 }).then(r => r.data),

  // —— 长任务持久化（run 由后端持有，客户端只跟随）——
  dshRunStart: (p: { scope: string; key: string; message: string; session_id?: string; model?: string }) =>
    http.post('/v1/dsh/run/start', p).then(r => r.data),
  dshRuns: (params: { scope?: string; key?: string; limit?: number } = {}) =>
    http.get('/v1/dsh/runs', { params }).then(r => r.data),
  dshRunState: (runId: string) => http.get(`/v1/dsh/runs/${runId}`).then(r => r.data),
  dshRunStop: (runId: string) => http.post(`/v1/dsh/runs/${runId}/stop`).then(r => r.data),
  /** 跟随 run：`from` 是回放游标（事件序号）；断线只断跟随，后端继续跑 */
  dshRunFollow: (runId: string, from: number, onEvent: (ev: string, data: any) => void, signal?: AbortSignal) =>
    openSSE(`/api/v1/dsh/runs/${encodeURIComponent(runId)}/stream?from=${from}`, { method: 'GET', signal }, onEvent),

  /** 兼容旧调用：起 run 后原地跟随（断线不再杀任务） */
  dshRunStream: (p: { scope: string; key: string; message: string; session_id?: string }, onEvent: (ev: string, data: any) => void, signal?: AbortSignal) =>
    openSSE('/api/v1/dsh/stream', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(p), signal,
    }, onEvent),
}
