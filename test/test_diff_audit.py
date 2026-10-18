"""diff 正确性审计：把“当前工作区 diff 是否正确”变成可重复执行的断言。

覆盖：py 全编译通过；无密钥泄漏；exportBundle 重名坑已填；
      restart 不构建 / rebuild 才构建；frontend 引用与后端路由对齐。
"""
import pathlib
import py_compile
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _diff():
    # 逐文件 diff（data 下 root 权文件会导致整仓 diff 失败，逐个取）
    out = subprocess.run(["git", "diff", "--", "backend/app", "frontend/src",
                          "skills", "cmd.bash", "docker-compose.yml",
                          "backend/Dockerfile", "README.md", "docs", "AGENTS.md",
                          "backend/AGENTS.md"],
                         capture_output=True, text=True, cwd=ROOT)
    return out.stdout


def test_py_compiles():
    bad = []
    for p in (ROOT / "backend" / "app").rglob("*.py"):
        try:
            py_compile.compile(str(p), doraise=True)
        except py_compile.PyCompileError as e:
            bad.append(f"{p}: {e}")
    assert not bad, bad


def test_no_secrets_in_diff():
    diff = _diff()
    hits = []
    for i, line in enumerate(diff.splitlines()):
        if not line.startswith("+") or line.startswith("+++"):
            continue
        body = line[1:]
        if re.search(r"(sk-[A-Za-z0-9]{8,}|ghp_[A-Za-z0-9]+|-----BEGIN [A-Z ]*PRIVATE KEY)", body):
            hits.append((i, body[:60]))
        if re.search(r"(?i)(password|passwd)\s*[:=]\s*\S+", body) and "OPENCODE" not in body:
            hits.append((i, body[:60]))
    assert not hits, hits


def test_export_bundle_name_clash_fixed():
    """director 用 exportBundle，traffic 必须改名，二者不可再撞。"""
    traffic = (ROOT / "frontend" / "src" / "api" / "traffic.ts").read_text()
    director = (ROOT / "frontend" / "src" / "api" / "director.ts").read_text()
    assert "exportTrafficBundle" in traffic
    assert re.search(r"\bexportBundle\b", director)
    assert not re.search(r"\bexportBundle\s*:", traffic), "traffic 侧还有 exportBundle 导出"


def test_restart_does_not_build():
    cmd = (ROOT / "cmd.bash").read_text()
    m = re.search(r"restart\)(.*?)(?=\n  \w+\)|\nesac)", cmd, re.S)
    assert m, "cmd.bash 缺 restart 分支"
    body = m.group(1)
    assert "--build" not in body, "restart 分支带了 --build"
    assert "restart" in body


def test_frontend_backend_route_alignment():
    """前端调的后端路径必须真实存在于 backend 路由表。"""
    routes = set()
    for p in (ROOT / "backend" / "app" / "api").glob("*.py"):
        src = p.read_text()
        prefix = re.search(r'url_prefix="([^"]+)"', src)
        pre = prefix.group(1) if prefix else ""
        for m in re.finditer(r'@bp\.(get|post|put|delete)\("([^"]+)"', src):
            routes.add(pre + m.group(2))
    for path in ("/v1/traffic/generate", "/v1/traffic/export-bundle",
                 "/v1/traffic/feedback", "/v1/director/export-bundle",
                 "/v1/director/push-lport",
                 "/v1/director/draft-doc", "/v1/tools/video-frames",
                 "/v1/uploads", "/v1/dsh/run",
                 "/v1/projects/<pid>", "/v1/projects/<pid>/episodes",
                 "/v1/projects/<pid>/episodes/<eid>"):
        assert "/api" + path in routes, f"后端缺路由 /api{path}，前端调了会 404/405"


def test_traffic_mount_contract_in_code():
    src = (ROOT / "backend" / "app" / "api" / "traffic.py").read_text()
    assert '"search_word"' in src and '"app_name"' in src and '"overlay_text"' in src
    assert "mount_ok" in src


def test_workspace_clear_buttons_exist():
    """board / traffic 两页必须有清空工作区按钮（二次确认+成功提示齐全）。"""
    board = (ROOT / "frontend" / "src" / "views" / "ScriptboardView.vue").read_text()
    traffic = (ROOT / "frontend" / "src" / "views" / "TrafficView.vue").read_text()
    for name, src in (("board", board), ("traffic", traffic)):
        assert "clearWorkspace" in src, f"{name} 缺 clearWorkspace"
        assert "清空" in src, f"{name} 缺清空按钮文案"
        assert "ElMessageBox.confirm" in src, f"{name} 清空缺二次确认"
        assert "工作区已清空" in src, f"{name} 缺成功提示"


def test_frontend_cache_and_chunk_recovery():
    """页面壳缓存策略：index.html/SPA 回退不许缓存（否则构建哈希一换，旧标签页点导航就去找已删的 chunk）；
    路由懒加载必须带 chunk 404 自愈（2026-10-16 事故：/board 点“美术工具”没反应）。"""
    ng = (ROOT / "frontend" / "nginx.conf").read_text()
    assert "no-cache" in ng, "nginx 缺 index.html 不缓存"
    assert "immutable" in ng, "nginx 缺 assets 长缓存"
    router = (ROOT / "frontend" / "src" / "router" / "index.ts").read_text()
    assert "withChunkRecovery" in router and "window.location.reload()" in router, "路由缺 chunk 404 自愈"


def test_character_clear_routes_and_buttons():
    """角色页「清除」三件套：槽位 / 单栏提示词 / 本组，前端按钮与后端两条 DELETE 路由必须同时在。"""
    view = (ROOT / "frontend" / "src" / "views" / "CharacterView.vue").read_text()
    api = (ROOT / "frontend" / "src" / "api" / "character.ts").read_text()
    back = (ROOT / "backend" / "app" / "api" / "character.py").read_text()
    for name in ("clearSlot", "clearSection", "clearPrompt"):
        assert name in view, f"CharacterView 缺 {name}"
    assert "清除该槽位" in view and "清空本组" in view, "角色页缺清除按钮文案"
    assert "el-popconfirm" in view, "角色页清除缺二次确认"
    for name in ("clearSlotAssets", "clearSlotPrompts"):
        assert name in api, f"character.ts 缺 {name}"
    assert '@bp.delete("/<cid>/assets")' in back, "后端缺 DELETE /characters/<cid>/assets"
    assert '@bp.delete("/<cid>/slot-prompts")' in back, "后端缺 DELETE /characters/<cid>/slot-prompts"


def test_character_clear_slots_env_kind():
    """清除按 kind（head/half/full × dressed/undressed）隔离，槽位三件套不许写死单一 kind。"""
    src = (ROOT / "backend" / "app" / "api" / "character.py").read_text()
    seg = src[src.index("def clear_assets"):src.index("def clear_slot_prompts")]
    assert 'a.get("kind") != kind' in seg and 'a.get("slot") != slot' in seg
    assert "_persist()" in seg, "清图后没落盘"


def test_outfit_tab_is_card_list():
    """服装四分类 tab 必须是「一行一件」卡片列表（与槽位卡同族），不许退回 el-table。"""
    view = (ROOT / "frontend" / "src" / "views" / "CharacterView.vue").read_text()
    seg = view[view.index('label="服装四分类"'):view.index('label="文档交付"')]
    assert "outfit-list" in seg and "outfit-card" in seg, "服装 tab 缺卡片结构"
    assert "<el-table" not in seg, "服装 tab 还在用表格"
    assert "outCatLabel" in seg and "outfit-chip" in seg, "服装卡缺分类中文名/色块"
    api = (ROOT / "frontend" / "src" / "api" / "character.ts").read_text()
    assert "updateOutfit" in api, "卡片就地编辑缺 updateOutfit 契约"


def test_sse_long_run_guards():
    """长任务防掐断（2026-10-16 事故）：nginx 读超时不许退回 200s；SSE 不许开缓冲；
    前端进度条必须显示事件计数与静默提示，否则长剧本看着像卡死。"""
    ng = (ROOT / "frontend" / "nginx.conf").read_text()
    m = re.search(r"proxy_read_timeout\s+(\d+)s", ng)
    assert m, "nginx 缺 proxy_read_timeout"
    assert int(m.group(1)) >= 900, f"/api/ 读超时 {m.group(1)}s 太短：dsh 单步静默会掐流并杀掉本轮"
    assert "proxy_buffering off" in ng, "SSE 必须关 nginx buffering"
    chat = (ROOT / "frontend" / "src" / "components" / "RightChat.vue").read_text()
    assert "evCount" in chat and "无新事件" in chat, "RightChat 缺事件计数/静默提示"
    assert "超60s可点停止重试" not in chat, "旧的误导文案（60s 就劝停）不该留着"


def test_run_persistence_contracts():
    """长任务持久化（2026-10-16 事故二）：run 归后端持有，切页/刷新只断"跟随"。
    断线即杀进程 + 前端不记 run_id = 一整轮 3–5 分钟成果全丢，两者都必须钉住。"""
    back = (ROOT / "backend" / "app" / "api" / "dsh.py").read_text()
    for frag in ('@bp.post("/run/start")', '@bp.get("/runs")', '@bp.get("/runs/<rid>")',
                 '@bp.get("/runs/<rid>/stream")', '@bp.post("/runs/<rid>/stop")'):
        assert frag in back, f"后端缺 {frag}"
    assert "threading.Thread(target=_run_worker" in back, "run 没跑在后端线程里（会被客户端断线带走）"
    follow = back[back.index("def _follow("):back.index("def _start_from_body(")]
    assert 'yield ": ping' in follow, "SSE 跟随缺心跳：单步静默会被中间层按空闲掐断"
    compat = back[back.index('@bp.post("/stream")'):]
    assert "proc.kill()" not in compat, "兼容 /stream 仍在按断线杀进程（要停只能走 /runs/<id>/stop）"

    fe = (ROOT / "frontend" / "src" / "components" / "RightChat.vue").read_text()
    assert "dsh-run:" in fe and "resumeIfAny" in fe, "前端没持久化 run_id / 没有重连逻辑"
    assert "dshRunStart" in fe and "dshRunFollow" in fe
    assert "last.a.startsWith('[失败]')" in fe, "断流占位没被真实结果覆盖的通道（刷新后会永远显示失败）"
    w = fe[fe.index("watch(() => [store.episodeId"):]
    head = w[:500]
    assert "aborter.value?.abort()" in head, "切页应只断本地跟随"
    assert "stop()" not in head, "切页还在调用 stop()（= 杀后端任务，历史 bug）"

    api = (ROOT / "frontend" / "src" / "api" / "dsh.ts").read_text()
    for fn in ("dshRunStart", "dshRuns", "dshRunState", "dshRunStop", "dshRunFollow"):
        assert fn in api, f"dsh.ts 缺 {fn}"


def test_blanking_guards():
    """清库护栏（2026-10-16 事故三）：空内容不许静默覆盖已有剧本/大纲。
    剧本页有 3s debounce 自动保存，切集/切页时 script 可能为空 → 曾把 2187 字稿冲成 0。"""
    board = (ROOT / "backend" / "app" / "api" / "scriptboard.py").read_text()
    seg = board[board.index("def save_screenplay"):board.index("def get_screenplay")]
    assert 'b.get("force")' in seg and 'kept' in seg, "剧本 PUT 缺空覆盖护栏"
    oseg = board[board.index("def save_outline"):board.index("def outline_generate")]
    assert 'b.get("force")' in oseg and 'kept' in oseg, "大纲 PUT 缺空覆盖护栏"
    dv = (ROOT / "frontend" / "src" / "views" / "DirectorView.vue").read_text()
    assert "scriptLoadedFor" in dv, "剧本页缺「这稿属于哪一集」标记（跨集误写）"
    assert "if (silent && !script.value.trim()) return" in dv, "自动保存没拦空内容"
    m = re.search(r"onUnmounted\(\(\) => ([^)]*\(|\{[^}]*\})", dv)
    assert m and "clearTimeout(scriptTimer)" in dv[m.start():m.start() + 200], "卸载没清 debounce 定时器"
    assert "force: true" in dv, "手动清空没走 force（否则后端会拒）"


def test_get_screenplay_kept_flag():
    """护栏返回结构：kept 字段必须回传，前端据此回读真稿。"""
    board = (ROOT / "backend" / "app" / "api" / "scriptboard.py").read_text()
    seg = board[board.index("def save_screenplay"):board.index("def get_screenplay")]
    assert '"kept": True' in seg and '"kept": False' in seg


def test_project_switch_moves_workspace():
    """顶栏项目必须真切换：新建/换项目时 Episode + 当前角色跟着走（以前项目只是标签，点了跟没点一样）。"""
    app = (ROOT / "frontend" / "src" / "App.vue").read_text()
    for frag in ("snapshotCtx", "applyCtx", "suli.projectCtx", "watch(() => store.projectId"):
        assert frag in app, f"App.vue 缺项目现场切换：{frag}"
    assert "已新建并切换" in app, "新建后缺切换提示"
    rv = [l for l in app.splitlines() if "router-view" in l]
    assert rv and "store.projectId" in rv[0] and "store.episodeId" in rv[0], "router-view 缺按项目+集号重挂"


def test_project_workspace_contracts():
    """项目/集号/回执闭环：删除、集号归属、回执归位的前后端契约必须同时在。"""
    proj = (ROOT / "frontend" / "src" / "api" / "project.ts").read_text()
    for fn in ("deleteProject", "listProjectEpisodes", "createProjectEpisode", "removeProjectEpisode"):
        assert fn in proj, f"project.ts 缺 {fn}"
    app = (ROOT / "frontend" / "src" / "App.vue").read_text()
    for frag in ("confirmDeleteProject", "episodePick", "openEpisodeDialog", "submitEpisodeDialog", "onEpisodePicked"):
        assert frag in app, f"App.vue 缺工作区操作：{frag}"
    panel = (ROOT / "frontend" / "src" / "components" / "director" / "ReceiptPanel.vue").read_text()
    assert "projectId" in panel and "project_id" in panel and "receiptLine" in panel, "回执面板缺项目归位"
    director = (ROOT / "frontend" / "src" / "views" / "DirectorView.vue").read_text()
    assert ":project-id=\"store.projectId\"" in director, "导演页没把项目传给回执面板"
    assert "project_id: store.projectId" in director, "导出包没带项目归属"
    receipts = (ROOT / "backend" / "app" / "api" / "receipts.py").read_text()
    assert "project_id" in receipts and "episode_id" in receipts and "delete_scoped" in receipts, "回执后端缺归位/清理"
    projects = (ROOT / "backend" / "app" / "api" / "projects.py").read_text()
    assert '@bp.delete("/<pid>")' in projects and "cascade" in projects, "项目后端缺删除/级联"
    assert '@bp.post("/<pid>/episodes")' in projects, "项目后端缺集号新建"


def test_director_push_contracts():
    """草案直投闭环：后端直投口（独立 suli_packages 收件箱，不污染投流 packages）+
    前端直投键与回执轮询 + 回执面板刷新信号必须同时在。"""
    back = (ROOT / "backend" / "app" / "api" / "director.py").read_text()
    assert '@bp.post("/push-lport")' in back, "后端缺 POST /director/push-lport"
    assert "suli_packages" in back, "直投没写独立收件箱（会污染投流 packages 列表）"
    assert "_build_director_bundle" in back, "出包与直投没共用构建函数（两处会飘）"
    assert "director_push_db.json" in back, "直投缺推送记录落盘"
    api = (ROOT / "frontend" / "src" / "api" / "director.ts").read_text()
    assert "pushToLport" in api and "/v1/director/push-lport" in api, "director.ts 缺 pushToLport"
    dv = (ROOT / "frontend" / "src" / "views" / "DirectorView.vue").read_text()
    for frag in ("pushToLport", "直投 L-Port", "ensurePoller", "receiptRefreshKey", "去回执页查看"):
        assert frag in dv, f"导演页缺直投/等回执：{frag}"
    assert "push-status" in dv and "LoadingSpinner" in dv, "直投等待条缺 loading 动画"
    for frag in ("suli.director.pushes", "resumePush", "curPushes", "ensurePoller"):
        assert frag in dv, f"直投缺刷新持久化/多包并行：{frag}（刷新/切页回来要续等，多包互不覆盖）"
    panel = (ROOT / "frontend" / "src" / "components" / "director" / "ReceiptPanel.vue").read_text()
    assert "refreshKey" in panel, "回执面板缺 refreshKey（回执到了不会自动刷）"


def test_lport_prompt_return_contracts():
    """详细提示词回传闭环（2026-10-18）：Suli 收口端点 + 导演页「提示词」页签 +
    分镜卡嵌块必须同时在（L-Port 侧 push-prompts-to-suli 对端，跨库静态夹在两侧测试）。"""
    sb = (ROOT / "backend" / "app" / "api" / "scriptboard.py").read_text()
    assert '@bp.post("/shots/prompts/import")' in sb, "后端缺 POST /scriptboard/shots/prompts/import"
    assert "_norm_prompt_item" in sb and "lport_prompts" in sb, "收口缺字段归一/落位"
    dv = (ROOT / "frontend" / "src" / "views" / "DirectorView.vue").read_text()
    for frag in ('label="提示词"', "lport_prompts", "copyAllPrompts", "reloadPrompts", "写详细提示词并回传"):
        assert frag in dv, f"导演页缺提示词回传页签：{frag}"
    card = (ROOT / "frontend" / "src" / "components" / "director" / "ShotCard.vue").read_text()
    assert "lport_prompts" in card and "copyLp" in card, "分镜卡缺回传提示词嵌块"
    pos = (ROOT / "docs" / "POSITIONING.md").read_text()
    assert "push-prompts-to-suli" in pos and "shots/prompts/import" in pos, "POSITIONING 缺回传契约"


def test_lib_head_buttons_stop_propagation():
    """素材库 header 整行是折叠开关，行内按钮必须 .stop，否则一点删除就折叠空白。"""
    src = (ROOT / "frontend" / "src" / "views" / "TrafficView.vue").read_text()
    assert '@click.stop="enterDelMode"' in src
    assert '@click.stop="confirmDelSel"' in src
    assert '@click.stop="exitDelMode"' in src


def test_programmatic_ep_styles_imported():
    """编程式 ElMessage/ElMessageBox 样式必须在 main.ts 显式引入，
    否则确认框裸奔跑到左上角（resolver 只管模板里用到的组件）"""
    main = (ROOT / "frontend" / "src" / "main.ts").read_text()
    assert "theme-chalk/el-message.css" in main
    assert "theme-chalk/el-message-box.css" in main


def test_clear_path_kills_pending_autosave():
    """清空复活护栏（2026-10-16 用户报告：清空后刷新剧本又回来了）：
    1) 清空必须掐掉 3s 自动保存定时器，否则它在清空之后拿旧稿再 PUT 一次；
    2) 分镜页「清空工作区」写空稿必须带 force，否则后端护栏拒掉、界面却报成功；
    3) 导演页清空期间要有 scriptClearing 闸门，丢弃清空进行中的自动保存回写。"""
    board = (ROOT / "frontend" / "src" / "views" / "ScriptboardView.vue").read_text()
    clear_seg = board[board.index("async function clearWorkspace"):board.index("async function onShotImg")]
    assert "clearTimeout(scriptTimer)" in clear_seg, "分镜页清空没掐自动保存定时器"
    assert "await save(true, true)" in clear_seg, "分镜页清空写空稿没带 force（后端会拒）"
    assert "force ? { force: true } : {}" in board, "分镜页 save() 没接 force 参数"
    assert "savedScript.value = ''" in clear_seg, "分镜页清空没重置已保存基线"

    dv = (ROOT / "frontend" / "src" / "views" / "DirectorView.vue").read_text()
    dv_seg = dv[dv.index("async function clearScript"):dv.index("async function clearShots")]
    assert "clearTimeout(scriptTimer)" in dv_seg, "导演页清空没掐自动保存定时器"
    assert "scriptClearing.value = true" in dv_seg, "导演页清空没有闸门"
    assert "if (scriptClearing.value) return" in dv, "saveScript 没在清空期间丢弃自动保存"
    assert "savedScript.value = ''" in dv_seg and "scriptLoadedFor.value = ''" in dv_seg, "导演页清空没重置基线"
