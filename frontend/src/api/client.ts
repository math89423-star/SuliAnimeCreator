/** api 门面：保持旧 `import { api } from '../api/client'` 可用。
 * 新代码请按域直引：story/character/board/director/dsh/system。
 */
import { http } from './http'
import { storyApi } from './story'
import { characterApi, DIMS } from './character'
import { boardApi } from './board'
import { directorApi } from './director'
import { dshApi } from './dsh'
import { systemApi } from './system'
import { trafficApi } from './traffic'

export { http, DIMS }
export const api = {
  ...systemApi,
  ...storyApi,
  ...characterApi,
  ...boardApi,
  ...directorApi,
  ...dshApi,
  ...trafficApi,
}
export type Api = typeof api
