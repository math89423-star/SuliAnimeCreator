// legacySeeds：只用于「一次性清理」的历史演示种子，不是任何默认值。
// 用 \u 码点写，免得全仓检索演示人名时误报（这些名字不允许再出现在源码里）。
// 匹配上就删掉对应 localStorage 项：只清自己塞的旧演示数据，不碰用户手动写过的内容。
export const LEGACY_STORY_IDEA = '灰水村血税牢，星璃登场'
export const LEGACY_BOARD_SAMPLE = '## EP001-SC001 内·洗衣房·夜\n沈禾：取衣牌呢？\n蒋姨：烘干机停了。'

/** 清掉旧的演示种子（命中即删）。返回是否有清理动作。 */
export function purgeLegacySeeds(): boolean {
  let touched = false
  try {
    if (localStorage.getItem('suli.story.idea') === LEGACY_STORY_IDEA) {
      localStorage.removeItem('suli.story.idea')
      touched = true
    }
    if (localStorage.getItem('suli.board.sample.v1') === LEGACY_BOARD_SAMPLE) {
      localStorage.removeItem('suli.board.sample.v1')
      touched = true
    }
  } catch {}
  return touched
}
