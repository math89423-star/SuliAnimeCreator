import { http } from './http'
export const toolsApi = {
  videoFrames: (p: { url?: string; path?: string; max_frames?: number; scene?: number }) =>
    http.post('/v1/tools/video-frames', p, { timeout: 200000 }).then(r => r.data),
  /** H站下载入库：贴 hanime1.me 观片页链接或视频 id，落 uploads 并返回 {name, path,url, bytes, duration_s}；
   *  下载耗时随体积（百 MB 级），不设客户端超时（后端单步读超时兜底）。 */
  hanime1Fetch: (url: string, quality = 'best') =>
    http.post('/v1/tools/hanime1-fetch', { url, quality }, { timeout: 0 }).then(r => r.data),
}
