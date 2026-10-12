import { http } from './http'
export const dshApi = {
  dshSessions: (scope = '') => http.get('/v1/dsh/sessions', { params: scope ? { scope } : {} }).then(r => r.data),
  dshEnsure: (scope: string, key: string) => http.post('/v1/dsh/sessions', { scope, key }).then(r => r.data),
  dshDeleteSession: (scope: string, key: string) => http.delete('/v1/dsh/sessions', { data: { scope, key }, params: { scope, key } }).then(r => r.data),
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
