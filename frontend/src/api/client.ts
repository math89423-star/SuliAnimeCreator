/** api 门面：保持旧 `import { api } from '../api/client'` 可用。
 * 新代码请按域直引：story/character/board/director/dsh/system。
 */
import { http } from './http'
import { storyApi } from './story'
import { projectApi } from './project'
import { characterApi, DIMS } from './character'
import { boardApi } from './board'
import { directorApi } from './director'
import { dshApi } from './dsh'
import { systemApi } from './system'
import { trafficApi } from './traffic'
import { toolsApi } from './tools'
import { reportsApi } from './reports'
import { artPlanApi } from './art'

export { http, DIMS }
export const api = {
  ...systemApi,
  ...storyApi,
  ...projectApi,
  ...characterApi,
  ...boardApi,
  ...directorApi,
  ...dshApi,
  ...trafficApi,
  ...toolsApi,
  ...reportsApi,
  ...artPlanApi,
}
export type Api = typeof api
