#!/usr/bin/env bash
# SuliAnimeCreator 运维入口（容器模式）
#   cmd.bash start          拉起容器（不构建，镜像缺失时报错，用 rebuild 先建）
#   cmd.bash rebuild        构建镜像并重建容器
#   cmd.bash restart        只重启容器（不构建）
#   cmd.bash stop           停容器（数据卷保留）
#   cmd.bash status         容器状态 + 后端健康
#   cmd.bash logs [backend|frontend]   看容器日志（默认 backend）
#   cmd.bash build          只构建镜像不启动
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"

preflight() {
  # 首次部署三件套：只提醒/建目录，不拦流程
  [ -d "$ROOT/dsh-home" ] || { mkdir -p "$ROOT/dsh-home"; echo "已建 dsh-home/（空）：把宿主 ~/.dsh/{profiles,.credentials.yaml} 拷进去后再 restart，dsh 会话才可用"; }
  [ -f "$ROOT/.env" ] || echo "提醒：缺 .env（cp .env.example .env 填 OPENCODE_API_KEY，不填则 LLM 全走本地模板回退）"
}

health() {
  if curl -sf --max-time 5 http://127.0.0.1:5001/api/health >/dev/null 2>&1; then echo "后端健康 OK :5001"; else echo "后端未就绪（看日志：cmd.bash logs backend）"; fi
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
    (cd "$ROOT" && docker compose logs --tail=80 "${2:-backend}");;
  build)
    (cd "$ROOT" && docker compose build);;
  *) echo "用法: cmd.bash {start|stop|rebuild|restart|status|logs [backend|frontend]|build}"; exit 1;;
esac
