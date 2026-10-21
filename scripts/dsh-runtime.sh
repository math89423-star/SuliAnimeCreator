#!/usr/bin/env bash
# dsh 运行时管理 —— dsh 版本与后端镜像解耦。
#
# 背景：dsh CLI 原先由 backend 镜像构建期 `npm i -g` 装死，升级 dsh 要重建整个后端镜像
# （重装 600+ 包 + node24 apt 层）。本脚本把 dsh 装到宿主 dsh-runtime/<版本>/ 目录，
# 容器只挂载该目录并按 DSH_VERSION 选版本 —— 升版本 = 宿主装一次 + 改 env + 重启容器，
# 不碰镜像、不动 Flask。
#
# 每版本目录自带完整的 @deepseek-ai/* bundle（profile 的 dsh-base/dsh-headless 从这里解析），
# 所以不同版本的 bundle 互不干扰。
#
# 破甲补丁（LLMCoreBreak/dsh）在**安装时**对目标版本目录单独打：
#   · 打补丁要改写 dsh 安装目录里的文件，容器启动时那个 4 秒定时器在 one-shot headless 下不可靠；
#   · 打补丁必须只落在目标版本上（corebreak 的 enumerateHosts 会枚举 PATH 里的所有 dsh 宿主），
#     所以这里用隔离 PATH + DSH_AI_BASE 双重定向。
#
# 用法：
#   scripts/dsh-runtime.sh install <版本>    装一个版本（幂等：已装则只补补丁）
#   scripts/dsh-runtime.sh list              列已装版本 + 补丁状态
#   scripts/dsh-runtime.sh status [版本]     看某版本的补丁状态（默认 DSH_VERSION）
#   scripts/dsh-runtime.sh use <版本>        切默认版本（写 .env 的 DSH_VERSION）
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME_DIR="$ROOT/dsh-runtime"
DSH_HOME_DIR="$ROOT/dsh-home"
COREBREAK_SRC="/home/administrator/LLMCoreBreak/dsh"
# 宿主 node 的 ABI 需与容器内 node 一致（两者同为 node 24 → modules ABI 137）
NODE_ABI_MIN=137

die() { echo "✗ $*" >&2; exit 1; }

# 该版本的 @deepseek-ai 包根（corebreak 打补丁的目标目录）
ai_base_of() {
  local ver="$1"
  echo "$RUNTIME_DIR/$ver/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai"
}

# 该版本的 dsh 可执行文件
bin_of() {
  echo "$RUNTIME_DIR/$1/bin/dsh"
}

# 从 .env 读当前 DSH_VERSION（未设则用 default）
current_version() {
  local v=""
  [ -f "$ROOT/.env" ] && v="$(grep -E '^DSH_VERSION=' "$ROOT/.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"' \r')"
  echo "${v:-0.2.0-rc.2}"
}

check_prereq() {
  command -v node >/dev/null 2>&1 || die "宿主缺 node（装 dsh 需要）"
  command -v npm >/dev/null 2>&1 || die "宿主缺 npm"
  local abi
  abi="$(node -p 'process.versions.modules' 2>/dev/null || echo 0)"
  [ "$abi" -ge "$NODE_ABI_MIN" ] || die "宿主 node ABI=$abi < $NODE_ABI_MIN（需 node 24+），装出的原生模块在容器里跑不了"
  [ -d "$DSH_HOME_DIR" ] || die "缺 $DSH_HOME_DIR（dsh 家目录）：先 cmd.bash start 建出来"
  [ -d "$COREBREAK_SRC" ] || die "缺破甲内核 $COREBREAK_SRC"
}

install_dsh() {
  local ver="$1"
  local prefix="$RUNTIME_DIR/$ver"
  check_prereq

  if [ ! -x "$(bin_of "$ver")" ]; then
    echo "→ 安装 dsh@$ver 到 $prefix（首次约 1 分钟）"
    rm -rf "$prefix"
    mkdir -p "$prefix"
    npm i -g --prefix "$prefix" "@deepseek-ai/dsh@$ver" --no-audit --no-fund \
      || die "npm i 失败（网络？版本号不存在？）"
  else
    echo "→ dsh@$ver 已装在 $prefix，跳过安装"
  fi

  # bundle 自检：profile 的 dsh-base/dsh-headless 从这里解析，缺了就等于没装
  local base; base="$(ai_base_of "$ver")"
  for pkg in dsh-base dsh-headless; do
    [ -d "$base/$pkg" ] || die "bundle 缺失：$base/$pkg（安装不完整，重装该版本）"
  done

  # 破甲补丁：只打这一份 dsh（隔离 PATH + DSH_AI_BASE 双定向）
  echo "→ 打破甲补丁（仅本版本目录）"
  local core="$DSH_HOME_DIR/profiles/headless/node_modules/dsh-corebreak"
  # profile 里的 dsh-corebreak 软链必须指向 LLMCoreBreak/dsh 真实位置：
  # 早期版本指向的是仓库改名前的路径（~/<旧名>/dsh），软链悬空 = 破甲层整个不加载
  # （表现是 dsh 启动 stderr「skipping profile bundle "dsh-corebreak"」）。
  # dsh-home 不入库（有明文凭据），所以每次安装都顺手校正一次，保证新机器也成立。
  for prof in headless web; do
    local plink="$DSH_HOME_DIR/profiles/$prof/node_modules/dsh-corebreak"
    [ -d "$DSH_HOME_DIR/profiles/$prof" ] || continue
    mkdir -p "$(dirname "$plink")"
    if [ ! -e "$plink" ] || [ "$(readlink -f "$plink")" != "$COREBREAK_SRC" ]; then
      echo "  · 修正 profile/$prof 的 dsh-corebreak 软链 → $COREBREAK_SRC"
      rm -f "$plink"
      ln -s "$COREBREAK_SRC" "$plink"
    fi
  done
  [ -e "$core" ] || die "profile 里找不到 corebreak：$core（软链修正后仍不可达？）"
  local cb_bin; cb_bin="$(readlink -f "$core")/bin/dsh-corebreak.js"
  [ -f "$cb_bin" ] || die "corebreak 入口不存在：$cb_bin"

  ( cd "$prefix" \
    && PATH="$prefix/bin:/usr/bin:/bin" \
       DSH_HOME="$DSH_HOME_DIR" \
       DSH_AI_BASE="$base" \
       node "$cb_bin" apply ) || die "打补丁失败"

  # 补丁自检：21 条里应有 20 条已应用（step-pin-hook 对 dsh 0.2.x 失配，属已知缺口）
  # status 输出形如「补丁 21 条 — 已应用 20 · 待应用 0 · 别家等效 0 · 未命中 1」
  local applied
  applied="$( cd "$prefix" && PATH="$prefix/bin:/usr/bin:/bin" DSH_HOME="$DSH_HOME_DIR" \
              DSH_AI_BASE="$base" node "$cb_bin" status 2>/dev/null \
              | grep -F "宿主: $base" -A 1 | grep -o '已应用 [0-9]*' | head -1 | grep -o '[0-9]*' )"
  echo "→ 补丁状态：已应用 ${applied:-?}/21"
  [ "${applied:-0}" -ge 19 ] || die "补丁命中数异常（${applied:-?}/21），该版本可能与 corebreak 不兼容"

  echo "✓ dsh@$ver 就绪"
}

case "${1:-status}" in
  install)
    [ -n "${2:-}" ] || die "用法：scripts/dsh-runtime.sh install <版本>"
    install_dsh "$2";;
  list)
    echo "已装版本（$RUNTIME_DIR）："
    if [ -d "$RUNTIME_DIR" ]; then
      for d in "$RUNTIME_DIR"/*/; do
        [ -d "$d" ] || continue
        v="$(basename "$d")"
        if [ -x "$d/bin/dsh" ]; then
          printf "  %-16s %s\n" "$v" "$("$d/bin/dsh" --version 2>/dev/null | head -1)"
        else
          printf "  %-16s (不完整)\n" "$v"
        fi
      done
    fi
    echo "当前 DSH_VERSION：$(current_version)";;
  status)
    ver="${2:-$(current_version)}"
    base="$(ai_base_of "$ver")"
    [ -d "$base" ] || die "版本 $ver 未装：$base"
    ( cd "$RUNTIME_DIR/$ver" && PATH="$RUNTIME_DIR/$ver/bin:/usr/bin:/bin" \
        DSH_HOME="$DSH_HOME_DIR" DSH_AI_BASE="$base" \
        node "$DSH_HOME_DIR/profiles/headless/node_modules/dsh-corebreak/bin/dsh-corebreak.js" status );;
  use)
    [ -n "${2:-}" ] || die "用法：scripts/dsh-runtime.sh use <版本>"
    [ -x "$(bin_of "$2")" ] || die "版本 $2 未装：先 scripts/dsh-runtime.sh install $2"
    touch "$ROOT/.env"
    if grep -qE '^DSH_VERSION=' "$ROOT/.env"; then
      sed -i "s|^DSH_VERSION=.*|DSH_VERSION=$2|" "$ROOT/.env"
    else
      echo "DSH_VERSION=$2" >> "$ROOT/.env"
    fi
    echo "✓ DSH_VERSION → $2（cmd.bash restart 后生效）";;
  *) echo "用法: scripts/dsh-runtime.sh {install <版本>|list|status [版本]|use <版本>}"; exit 1;;
esac
