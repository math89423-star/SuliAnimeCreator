import { http } from './http'
export const toolsApi = {
  videoFrames: (p: { url?: string; path?: string; max_frames?: number; scene?: number }) =>
    http.post('/v1/tools/video-frames', p, { timeout: 200000 }).then(r => r.data),
}
