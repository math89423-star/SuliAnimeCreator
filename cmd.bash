#!/usr/bin/env bash
# SuliAnimeCreator 运维入口（本地进程模式；容器模式走 docker-up/down）
#   cmd.bash start [all|backend|frontend]   启动本地进程（默认 all，可重复执行，已起跳过）
#   cmd.bash stop [all|backend|frontend]    停止本地进程
#   cmd.bash status                         本地进程状态 + 后端健康
#   cmd.bash logs [backend|frontend]        看日志（默认 backend）
#   cmd.bash docker-up | cmd.bash docker-down   容器模式（一键前后端）
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
RUN="$ROOT/.run"
mkdir -p "$RUN/logs"

backend_pid() { cat "$RUN/backend.pid" 2>/dev/null || true; }
frontend_pid() { cat "$RUN/frontend.pid" 2>/dev/null || true; }
alive() { [ -n "${1:-}" ] && kill -0 "$1" 2>/dev/null; }

start_backend() {
  local pid; pid="$(backend_pid)"
  if alive "$pid"; then echo "backend 已在跑 pid=$pid"; return 0; fi
  (cd "$ROOT/backend" || exit 1; FLASK_DEBUG=1 nohup python run.py > "$RUN/logs/backend.log" 2>&1 & echo $! > "$RUN/backend.pid")
  echo "backend 启动中 pid=$(backend_pid) 日志 .run/logs/backend.log"
}
start_frontend() {
  local pid; pid="$(frontend_pid)"
  if alive "$pid"; then echo "frontend 已在跑 pid=$pid"; return 0; fi
  (cd "$ROOT/frontend" || exit 1; nohup npm run dev > "$RUN/logs/frontend.log" 2>&1 & echo $! > "$RUN/frontend.pid")
  echo "frontend 启动中 pid=$(frontend_pid) 日志 .run/logs/frontend.log"
}
stop_one() { # $1=backend|frontend（杀进程树，防 reloader/子进程残留）
  local pid kids
  pid="$(cat "$RUN/$1.pid" 2>/dev/null || true)"
  if alive "$pid"; then
    kill "$pid" 2>/dev/null
    sleep 1
    kids="$(pgrep -P "$pid" 2>/dev/null || true)"
    [ -n "$kids" ] && kill $kids 2>/dev/null
    sleep 1
    if alive "$pid"; then kill -9 "$pid" 2>/dev/null; fi
    kids="$(pgrep -P "$pid" 2>/dev/null || true)"
    [ -n "$kids" ] && kill -9 $kids 2>/dev/null
    echo "已停 $1 pid=$pid"
  else
    echo "$1 未在跑"
  fi
  rm -f "$RUN/$1.pid"
}
health() {
  if curl -sf --max-time 5 http://127.0.0.1:5001/api/health >/dev/null 2>&1; then echo "后端健康 OK :5001"; else echo "后端未起（cmd.bash start backend）"; fi
}

case "${1:-status}" in
  start)
    _t="${2:-all}"
    case "$_t" in
      backend) start_backend ;;
      frontend) start_frontend ;;
      *) start_backend; start_frontend ;;
    esac
    for _ in 1 2 3 4; do sleep 2; curl -sf --max-time 3 http://127.0.0.1:5001/api/health >/dev/null 2>&1 && break; done
    health
    if [ "$_t" = "all" ] || [ "$_t" = "backend" ]; then echo "后端地址 http://127.0.0.1:5001（健康 /api/health）"; fi
    if [ "$_t" = "all" ] || [ "$_t" = "frontend" ]; then echo "前端地址 http://127.0.0.1:5173"; fi ;;
  stop)
    case "${2:-all}" in
      backend) stop_one backend ;;
      frontend) stop_one frontend ;;
      *) stop_one backend; stop_one frontend ;;
    esac ;;
  status)
    for s in backend frontend; do
      pid="$(cat "$RUN/$s.pid" 2>/dev/null || true)"
      if alive "$pid"; then echo "$s 运行中 pid=$pid"; else echo "$s 未在跑"; fi
    done; health ;;
  logs)
    tail -n 50 "$RUN/logs/${2:-backend}.log" 2>/dev/null || echo "暂无日志" ;;
  docker-up) (cd "$ROOT" && docker compose up --build -d) ;;
  docker-down) (cd "$ROOT" && docker compose down) ;;
  *) echo "用法: cmd.bash {start|stop} [all|backend|frontend] | status | logs [backend|frontend] | docker-up | docker-down"; exit 1 ;;
esac
