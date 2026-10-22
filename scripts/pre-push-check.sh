#!/usr/bin/env bash
# 推送前自检 —— 确认要出网的内容里没有敏感物。
#
# 为什么需要它：`.gitignore` 只挡**未跟踪**的文件，已经进过版本库的文件它管不着
# （backend/data/uploads/ 就是这样：gitignore 里有，但历史提交里还留着 18 张图）。
# 所以推之前必须扫「实际会推出去的清单」，而不是只扫 `git diff`。
#
# 用法：
#   scripts/pre-push-check.sh          扫将要推送的提交（相对远端）
#   scripts/pre-push-check.sh --all    扫全部已跟踪文件（首次推空库 / 想全量体检时用）
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

MODE="${1:-staged}"

# 敏感模式：真 key / token / 私钥 / 明文口令。
# 刻意不匹配普通单词（如 password= 出现在文档散文里会误报），只认有形状的东西。
PATTERNS='(sk-[A-Za-z0-9_-]{24,}|oc_sk_[A-Za-z0-9_-]{24,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16})'

echo "=== ① 远端与分支 ==="
if git remote get-url origin >/dev/null 2>&1; then
  echo "  origin: $(git remote get-url origin)"
  case "$(git remote get-url origin)" in
    git@github.com:*|https://github.com/*) ;;
    *) echo "  ⚠ origin 指向非 GitHub 地址，确认一下这是不是你要的" ;;
  esac
else
  echo "  （无 origin）"
fi
echo "  当前分支: $(git rev-parse --abbrev-ref HEAD)"

echo
echo "=== ② 仓库可见性提醒 ==="
echo "  本仓含 NSFW craft 与角色库 → 必须是私有库，别改 public。"

echo
echo "=== ③ 忽略规则覆盖情况（这些目录不该进版本库）==="
for d in dsh-home dsh-runtime node_modules frontend/node_modules; do
  n="$(git ls-files "$d" | wc -l | tr -d ' ')"
  if [ "$n" -eq 0 ]; then
    echo "  ✓ $d/  0 个已跟踪文件"
  else
    echo "  ⚠ $d/  有 $n 个已跟踪文件 —— gitignore 对已跟踪文件无效，要清得 git rm --cached"
  fi
done
for f in .env backend/data/model_settings.json; do
  if git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
    echo "  ⚠ $f 已进版本库 —— 里面有明文 key，立刻处理"
  else
    echo "  ✓ $f  未进版本库"
  fi
done

echo
echo "=== ④ 密钥形态扫描 ==="
if [ "$MODE" = "--all" ]; then
  echo "  范围：全部已跟踪文件"
  LIST="$(git ls-files)"
else
  echo "  范围：相对远端的待推提交 + 未跟踪文件"
  LIST="$( { git diff --name-only origin/main...HEAD 2>/dev/null; git ls-files -o --exclude-standard; } | sort -u )"
fi
# 分批喂给 grep，避免参数过长（文件多时 xargs 会分批，命中结果仍全）
HITS="$(printf '%s\n' "$LIST" | grep -v '^$' | tr '\n' '\0' | xargs -0 -r grep -lIE "$PATTERNS" 2>/dev/null)"
if [ -z "$HITS" ]; then
  echo "  ✓ 未命中密钥形态"
else
  echo "  ⚠ 以下文件命中，逐个确认是不是真 key："
  printf '%s\n' "$HITS" | sed 's/^/      /'
fi

echo
echo "=== ⑤ 待推内容规模 ==="
if [ "$MODE" = "--all" ]; then
  echo "  已跟踪文件: $(git ls-files | wc -l | tr -d ' ')"
else
  echo "  待推提交:   $(git log --oneline origin/main..HEAD 2>/dev/null | wc -l | tr -d ' ')"
  echo "  待推文件:   $(printf '%s\n' "$LIST" | grep -c . | tr -d ' ')"
fi
echo "  最大文件:"
if [ "$MODE" = "--all" ]; then
  git ls-files -z | xargs -0 du -k 2>/dev/null | sort -rn | head -3 | sed 's/^/      /'
else
  printf '%s\n' "$LIST" | grep -v '^$' | tr '\n' '\0' | xargs -0 -r du -k 2>/dev/null | sort -rn | head -3 | sed 's/^/      /'
fi

echo
echo "提醒：推已有历史的仓库只做 git remote add + git push -u origin main；"
echo "      别跑 git init / 首个 first commit（那是给空仓库准备的）。"
