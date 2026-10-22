#!/usr/bin/env bash
# SuliAnimeCreator 运维入口（容器模式）
#   cmd.bash start          拉起容器（不构建，镜像缺失时报错，用 rebuild 先建）
#   cmd.bash rebuild        构建镜像并重建容器
#   cmd.bash restart        只重启容器（不构建）
#   cmd.bash stop           停容器（数据卷保留）
#   cmd.bash status         容器状态 + 后端健康
#   cmd.bash logs [backend|frontend]   看容器日志（默认 backend）
#   cmd.bash build          只构建镜像不启动
#   cmd.bash dsh list       已装的 dsh 版本 + 当前使用版本
#   cmd.bash dsh install <版本>   装一个 dsh 版本（宿主装 + 打破甲补丁，不重建镜像）
#   cmd.bash dsh use <版本>       切换默认 dsh 版本（写 .env 的 DSH_VERSION）
#   cmd.bash dsh status [版本]    看某版本的破甲补丁状态
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"

preflight() {
  # 首次部署三件套：只提醒/建目录，不拦流程
  [ -d "$ROOT/dsh-home" ] || { mkdir -p "$ROOT/dsh-home"; echo "已建 dsh-home/（空）：把宿主 ~/.dsh/{profiles,.credentials.yaml} 拷进去后再 restart，dsh 会话才可用"; }
  [ -f "$ROOT/.env" ] || echo "提醒：缺 .env（cp .env.example .env 填 OPENCODE_API_KEY，不填则 LLM 全走本地模板回退）"
  # dsh CLI 已移出镜像（装在宿主 dsh-runtime/<版本>/），容器按 DSH_VERSION 选版本：
  # 宿主没装对应版本 → 后端起得来但一调 agent 就报 dsh binary not found。
  local ver
  ver="$(grep -E '^DSH_VERSION=' "$ROOT/.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"' \r')"
  ver="${ver:-0.2.0-rc.2}"
  [ -x "$ROOT/dsh-runtime/$ver/bin/dsh" ] || echo "提醒：dsh@$ver 未装（$ROOT/dsh-runtime/$ver）→ 跑 cmd.bash dsh install $ver"
}

health() {
  if curl -sf --max-time 5 http://127.0.0.1:5001/api/health >/dev/null 2>&1; then echo "后端健康 OK :5001"; else echo "后端未就绪（看日志：cmd.bash logs backend）"; fi
}

dsh_cmd() {
  case "${1:-list}" in
    list)       "$ROOT/scripts/dsh-runtime.sh" list;;
    install)    [ -n "${2:-}" ] || { echo "用法: cmd.bash dsh install <版本>"; return 1; }
                 "$ROOT/scripts/dsh-runtime.sh" install "$2";;
    use)        [ -n "${2:-}" ] || { echo "用法: cmd.bash dsh use <版本>"; return 1; }
                 "$ROOT/scripts/dsh-runtime.sh" use "$2";;
    status)     "$ROOT/scripts/dsh-runtime.sh" status "${2:-}";;
    *) echo "用法: cmd.bash dsh {list|install <版本>|use <版本>|status [版本]}"; return 1;;
  esac
}

case "${1:-status}" in
  start)
    preflight
    (cd "$ROOT" && docker compose up -d)
    for _ in 1 2 3 4 5 6; do sleep 3; curl -sf --max-time 3 http://127.0.0.1:5001/api/health >/dev/null 2>&1 && break; done
    health
    echo "前端地址 http://127.0.0.1:5173";;
  stop)
    (cd "$ROOT" && docker compose down)
    echo "已停（数据在 ./backend/data，dsh 会话在 ./dsh-home，均保留）";;
  rebuild)
    preflight
    (cd "$ROOT" && docker compose up --build -d --force-recreate)
    for _ in 1 2 3 4 5 6; do sleep 3; curl -sf --max-time 3 http://127.0.0.1:5001/api/health >/dev/null 2>&1 && break; done
    health
    echo "前端地址 http://127.0.0.1:5173";;
  restart)
    (cd "$ROOT" && docker compose restart)
    for _ in 1 2 3 4 5 6; do sleep 3; curl -sf --max-time 3 http://127.0.0.1:5001/api/health >/dev/null 2>&1 && break; done
    health;;
  status)
    (cd "$ROOT" && docker compose ps)
    health;;
  logs)
    # 对外仍用 backend/frontend 这两个友好名，内部映射到 compose service 名
    # （service 名是 suli-anime-backend，见 compose 里改名理由）。
    case "${2:-backend}" in
      backend)  svc="suli-anime-backend";;
      frontend) svc="frontend";;
      *)        svc="$2";;
    esac
    (cd "$ROOT" && docker compose logs --tail=80 "$svc");;
  build)
    (cd "$ROOT" && docker compose build);;
  dsh)
    dsh_cmd "${2:-list}" "${3:-}";;
  check)
    # 推送前自检：扫敏感物 + 核对 gitignore 覆盖 + 列待推规模
    "$ROOT/scripts/pre-push-check.sh" "${2:-}";;
  push)
    # 自检 → 有命中就停下让人确认 → 推送（只推已跟踪 + 已 add 的，不自动 add 全部）
    "$ROOT/scripts/pre-push-check.sh" || { echo "自检未过，已停下"; exit 1; }
    echo
    # 交互确认：非交互 shell（无 tty）时 read 会直接失败 → 视为取消，不盲推
    ans=""
    if [ -t 0 ]; then
      read -r -p "确认推送？(y/N) " ans || ans=""
    else
      echo "非交互环境，不自动推送（要推请直接 git push）"
      exit 1
    fi
    [ "$ans" = "y" ] || [ "$ans" = "Y" ] || { echo "已取消"; exit 1; }
    (cd "$ROOT" && git push -u origin "$(git rev-parse --abbrev-ref HEAD)");;
  *) echo "用法: cmd.bash {start|stop|rebuild|restart|status|logs [backend|frontend]|build|dsh {list|install <版本>|use <版本>|status [版本]}|check|push}"; exit 1;;
esac
