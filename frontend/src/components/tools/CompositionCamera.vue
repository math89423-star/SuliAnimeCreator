<template>
  <div class="comp-cam">
    <svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
      <marker id="arw" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6 Z" fill="#c0392b" /></marker>
      <linearGradient id="softshade" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="#e9e2d6" stop-opacity="1" />
        <stop offset="1" stop-color="#3a3440" stop-opacity="0.5" />
      </linearGradient>
    </defs></svg>

    <div class="tray">
      <div class="tray-inner">
        <span class="tray-label">镜头句组合：</span>
        <div class="chips">
          <span v-if="picked.length === 0" class="suli-muted empty-hint">暂无</span>
          <el-tag
            v-for="(p, i) in picked"
            :key="p"
            closable
            size="small"
            class="pick-tag"
            @close="removePick(i)"
          >{{ p }}</el-tag>
        </div>
        <el-button type="primary" size="small" @click="copyAllLine">复制组合句</el-button>
        <el-button size="small" @click="clearAll">清空组合</el-button>
        <el-button size="small" text @click="toggleTray">{{ trayOpen ? '收起 ▲' : '展开 ▼' }}</el-button>
      </div>
      <template v-if="trayOpen">
      <div class="tray-inner tray-search">
        <el-input
          v-model="query"
          placeholder="搜索"
          clearable
          size="small"
          class="search"
        />
        <el-tag
          v-for="s in secChips"
          :key="s.id"
          size="small"
          effect="plain"
          class="chip"
          :type="activeSec === s.id ? 'primary' : 'info'"
          @click="toggleSec(s.id)"
        >{{ s.title }}</el-tag>
        <span class="suli-muted count">{{ totalCount }} 卡</span>
        <el-button size="small" @click="clearFilter">清空筛选</el-button>
      </div>
      </template>
    </div>

    <div class="intro suli-card">
      <h1>构图镜头手册 Composition &amp; Camera</h1>
    </div>

    <section class="suli-card block">
      <h2>全部词条 <small>{{ filteredSecs.length }} 卡</small></h2>
      <div class="card-grid">
        <div
          v-for="it in filteredSecs"
          :key="it.en"
          class="suli-card tool-card"
          :class="{ open: isOpen('sec:' + it.secId + ':' + it.en) }"
          @click="toggleDetail('sec:' + it.secId + ':' + it.en, () => openSec(it))"
        >
          <div class="cover" v-html="it.dia"></div>
          <div class="body">
            <div class="t-zh">{{ it.zh }}</div>
            <div class="t-en mono">{{ it.en }}</div>
            <div class="pills"><el-tag size="small" effect="plain">{{ it.secTitle }}</el-tag></div>
            <div class="t-note">{{ it.note }}</div>
          </div>
          <el-dialog append-to-body :model-value="isOpen('sec:' + it.secId + ':' + it.en)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
            <div class="detail-block" @click.stop>
            <div v-if="detail" class="dlg">
              <div class="detail-cols">
                <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                <div class="detail-main">
                  <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                  <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                  <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                  <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                  <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                  <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                  <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                  <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                  <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                  <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                  <div v-if="detail.rows.length > 0" class="row">
                    <span class="k">逐段拆解</span>
                    <div class="v">
                      <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                        <div class="mono">{{ r[0] }}</div>
                        <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                      </div>
                    </div>
                  </div>
                  <div v-if="detail.url" class="row">
                    <span class="k">链接</span>
                    <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                  </div>
                </div>
              </div>
              <div class="dlg-actions">
                <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                <el-button size="small" @click.stop="openKey=null">收起</el-button>
              </div>
            </div>
          </div>
        </el-dialog>
      </div>
      </div>
      <p v-if<p v-if="filteredSecs.length === 0" class="suli-muted">没有命中，换个关键词或分类试试。</p>
    </section>

    <!-- flattened: SECTIONS 已拍平为顶部全部词条网格 -->

      <section class="suli-card block">
        <h3>自然语言描述法 <small>Describe It in Words {{ filteredNlways.length }} 卡</small></h3>
        <div class="card-grid">
          <div
            v-for="w in filteredNlways"
            :key="w.name"
            class="suli-card tool-card"
            :class="{ open: isOpen('nlway:' + w.name) }"
            @click="toggleDetail('nlway:' + w.name, () => openNlway(w))"
          >
            <div class="body">
              <div class="t-zh">{{ w.name }}</div>
              <div class="t-en mono">{{ w.en }}</div>
              <div class="pills"><el-tag size="small" effect="plain">自然语言法</el-tag></div>
              <div class="t-note">{{ w.cn }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('nlway:' + w.name)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredNlways.length === 0" class="suli-muted">本小节无命中。</p>
      </section>

      <section class="suli-card block">
        <h3>活感工作台 <small>Dead Prompt to Alive {{ filteredPairs.length }} 卡</small></h3>
        <div class="card-grid">
          <div
            v-for="(p, i) in filteredPairs"
            :key="i"
            class="suli-card tool-card"
            :class="{ open: isOpen('pair:' + i) }"
            @click="toggleDetail('pair:' + i, () => openPair(p))"
          >
            <div class="body">
              <div class="t-zh">死：{{ p[0] }} → 活：{{ p[1] }}</div>
              <div class="t-en mono">{{ p[2] }}</div>
              <div class="pills"><el-tag size="small" effect="plain">活感工作台</el-tag></div>
              <div class="t-note">{{ p[3] }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('pair:' + i)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredPairs.length === 0" class="suli-muted">本小节无命中。</p>
      </section>

      <section class="suli-card block">
        <h3>组合实战 <small>Worked Examples {{ filteredCombos.length }} 卡</small></h3>
        <div class="card-grid">
          <div
            v-for="c in filteredCombos"
            :key="c.en"
            class="suli-card tool-card"
            :class="{ open: isOpen('combo:' + c.en) }"
            @click="toggleDetail('combo:' + c.en, () => openCombo(c, '组合实战'))"
          >
            <div class="cover" v-html="c.dia"></div>
            <div class="body">
              <div class="t-zh">{{ c.zh }}</div>
              <div class="t-en mono">{{ c.en }}</div>
              <div class="pills"><el-tag size="small" effect="plain">组合实战</el-tag></div>
              <div class="t-note">{{ c.note }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('combo:' + c.en)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredCombos.length === 0" class="suli-muted">本小节无命中。</p>
      </section>

      <section class="suli-card block">
        <h3>高级镜头感 <small>Advanced Cinematic {{ filteredProcombos.length }} 卡</small></h3>
        <div class="card-grid">
          <div
            v-for="c in filteredProcombos"
            :key="c.en"
            class="suli-card tool-card"
            :class="{ open: isOpen('procombo:' + c.en) }"
            @click="toggleDetail('procombo:' + c.en, () => openCombo(c, '高级镜头'))"
          >
            <div class="cover" v-html="c.dia"></div>
            <div class="body">
              <div class="t-zh">{{ c.zh }}</div>
              <div class="t-en mono">{{ c.en }}</div>
              <div class="pills"><el-tag size="small" effect="plain">高级镜头</el-tag></div>
              <div class="t-note">{{ c.note }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('procombo:' + c.en)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredProcombos.length === 0" class="suli-muted">本小节无命中。</p>
      </section>

      <section class="suli-card block">
        <h3>拆解实战 <small>Worked Dissections {{ filteredDissects.length }} 卡</small></h3>
        <div class="card-grid">
          <div
            v-for="d in filteredDissects"
            :key="d.zh"
            class="suli-card tool-card"
            :class="{ open: isOpen('dissect:' + d.zh) }"
            @click="toggleDetail('dissect:' + d.zh, () => openDissect(d))"
          >
            <div class="body">
              <div class="t-zh">{{ d.zh }}</div>
              <div class="t-en mono">{{ d.tag }}</div>
              <div class="pills"><el-tag size="small" effect="plain">拆解实战</el-tag></div>
              <div class="t-note">{{ d.cn }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('dissect:' + d.zh)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredDissects.length === 0" class="suli-muted">本小节无命中。</p>
      </section>

      <section class="suli-card block">
        <h3>速查表 <small>Quick Reference {{ filteredQuick.length + filteredPosecam.length }} 卡</small></h3>
        <h4 class="subh">情绪 → 机位</h4>
        <div class="card-grid">
          <div
            v-for="(r, ri) in filteredQuick"
            :key="'q' + ri"
            class="suli-card tool-card"
            :class="{ open: isOpen('quick:q' + ri) }"
            @click="toggleDetail('quick:q' + ri, () => openRow(r[0] ?? '', r[1] ?? '', r[2] ?? '', '情绪速查'))"
          >
            <div class="body">
              <div class="t-zh">{{ r[0] }}</div>
              <div class="t-en mono">{{ r[1] }}</div>
              <div class="pills"><el-tag size="small" effect="plain">情绪速查</el-tag></div>
              <div class="t-note">{{ r[2] }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('quick:q' + ri)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredQuick.length === 0" class="suli-muted">情绪速查无命中。</p>
        <h4 class="subh">姿态 → 机位</h4>
        <div class="card-grid">
          <div
            v-for="(r, ri) in filteredPosecam"
            :key="'p' + ri"
            class="suli-card tool-card"
            :class="{ open: isOpen('posecam:p' + ri) }"
            @click="toggleDetail('posecam:p' + ri, () => openRow(r[0] ?? '', r[1] ?? '', r[2] ?? '', '姿态速查'))"
          >
            <div class="body">
              <div class="t-zh">{{ r[0] }}</div>
              <div class="t-en mono">{{ r[1] }}</div>
              <div class="pills"><el-tag size="small" effect="plain">姿态速查</el-tag></div>
              <div class="t-note">{{ r[2] }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('posecam:p' + ri)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredPosecam.length === 0" class="suli-muted">姿态速查无命中。</p>
      </section>

      <section class="suli-card block">
        <h3>易混辨析 <small>Confusable Terms {{ filteredConfused.length }} 卡</small></h3>
        <div class="card-grid">
          <div
            v-for="(r, ri) in filteredConfused"
            :key="ri"
            class="suli-card tool-card"
            :class="{ open: isOpen('confused:' + ri) }"
            @click="toggleDetail('confused:' + ri, () => openRow((r[0] ?? '') + ' vs ' + (r[1] ?? ''), r[2] ?? '', r[3] ?? '', '易混辨析'))"
          >
            <div class="body">
              <div class="t-zh">{{ r[0] }} vs {{ r[1] }}</div>
              <div class="t-en mono">{{ r[2] }}</div>
              <div class="pills"><el-tag size="small" effect="plain">易混辨析</el-tag></div>
              <div class="t-note">{{ r[3] }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('confused:' + ri)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredConfused.length === 0" class="suli-muted">本小节无命中。</p>
      </section>

      <section class="suli-card block">
        <h3>避雷清单 <small>Prompt Pitfalls {{ filteredPitfalls.length }} 卡</small></h3>
        <div class="card-grid">
          <div
            v-for="(r, ri) in filteredPitfalls"
            :key="ri"
            class="suli-card tool-card"
            :class="{ open: isOpen('pitfall:' + ri) }"
            @click="toggleDetail('pitfall:' + ri, () => openRow(r[0] ?? '', r[1] ?? '', r[2] ?? '', '避雷清单'))"
          >
            <div class="body">
              <div class="t-zh">{{ r[0] }}</div>
              <div class="t-en mono">{{ r[1] }}</div>
              <div class="pills"><el-tag size="small" effect="plain">避雷清单</el-tag></div>
              <div class="t-note">{{ r[2] }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('pitfall:' + ri)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredPitfalls.length === 0" class="suli-muted">本小节无命中。</p>
      </section>

      <section class="suli-card block">
        <h3>黑话焚诀 <small>Community Cheat Codes</small></h3>
        <h4 class="subh">黑话 → 手册对照 {{ filteredJargon.length }} 卡</h4>
        <div class="card-grid">
          <div
            v-for="(r, ri) in filteredJargon"
            :key="'j' + ri"
            class="suli-card tool-card"
            :class="{ open: isOpen('jargon:j' + ri) }"
            @click="toggleDetail('jargon:j' + ri, () => openRow(r[0] ?? '', r[1] ?? '', r[2] ?? '', '黑话对照'))"
          >
            <div class="body">
              <div class="t-zh">{{ r[0] }}</div>
              <div class="t-en mono">{{ r[1] }}</div>
              <div class="pills"><el-tag size="small" effect="plain">黑话对照</el-tag></div>
              <div class="t-note">{{ r[2] }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('jargon:j' + ri)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredJargon.length === 0" class="suli-muted">黑话对照无命中。</p>
        <h4 class="subh">社区词频榜 {{ filteredFreq.length }} 卡</h4>
        <div class="card-grid">
          <div
            v-for="(r, ri) in filteredFreq"
            :key="'f' + ri"
            class="suli-card tool-card"
            :class="{ open: isOpen('freq:f' + ri) }"
            @click="toggleDetail('freq:f' + ri, () => openRow(r[0] ?? '', r[1] ?? '', r[2] ?? '', '词频榜'))"
          >
            <div class="body">
              <div class="t-zh">{{ r[0] }}</div>
              <div class="t-en mono">{{ r[1] }}</div>
              <div class="pills"><el-tag size="small" effect="plain">词频榜</el-tag></div>
              <div class="t-note">{{ r[2] }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('freq:f' + ri)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredFreq.length === 0" class="suli-muted">词频榜无命中。</p>
        <h4 class="subh">焚诀卡 {{ filteredCheats.length }} 卡</h4>
        <div class="card-grid">
          <div
            v-for="c in filteredCheats"
            :key="c.zh"
            class="suli-card tool-card"
            :class="{ open: isOpen('cheat:' + c.zh) }"
            @click="toggleDetail('cheat:' + c.zh, () => openCheat(c, '焚诀卡'))"
          >
            <div class="body">
              <div class="t-zh">{{ c.zh }}</div>
              <div class="t-en mono">{{ c.en }}</div>
              <div class="pills"><el-tag size="small" effect="plain">焚诀卡</el-tag></div>
              <div class="t-note">{{ c.note }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('cheat:' + c.zh)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredCheats.length === 0" class="suli-muted">焚诀卡无命中。</p>
        <h4 class="subh">描改模板 {{ filteredTrace.length }} 卡</h4>
        <div class="card-grid">
          <div
            v-for="c in filteredTrace"
            :key="c.zh"
            class="suli-card tool-card"
            :class="{ open: isOpen('trace:' + c.zh) }"
            @click="toggleDetail('trace:' + c.zh, () => openCheat(c, '描改模板'))"
          >
            <div class="body">
              <div class="t-zh">{{ c.zh }}</div>
              <div class="t-en mono">{{ c.en }}</div>
              <div class="pills"><el-tag size="small" effect="plain">描改模板</el-tag></div>
              <div class="t-note">{{ c.note }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('trace:' + c.zh)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredTrace.length === 0" class="suli-muted">描改模板无命中。</p>
      </section>

      <section class="suli-card block">
        <h3>名词案例 <small>Term Examples {{ filteredGloss.length }} 卡</small></h3>
        <div class="card-grid">
          <div
            v-for="g in filteredGloss"
            :key="g.zh + g.tag"
            class="suli-card tool-card"
            :class="{ open: isOpen('gloss:' + g.zh + g.tag) }"
            @click="toggleDetail('gloss:' + g.zh + g.tag, () => openGloss(g))"
          >
            <div class="body">
              <div class="t-zh">{{ g.zh }}</div>
              <div class="t-en mono">{{ g.tag }}</div>
              <div class="pills"><el-tag size="small" effect="plain">名词案例</el-tag></div>
              <div class="t-note">{{ g.cn || g.en }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('gloss:' + g.zh + g.tag)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredGloss.length === 0" class="suli-muted">本小节无命中。</p>
      </section>

      <section class="suli-card block">
        <h3>工具句 <small>防裁切 · 保险 {{ filteredTools.length }} 卡</small></h3>
        <div class="card-grid">
          <div
            v-for="(t, ti) in filteredTools"
            :key="ti"
            class="suli-card tool-card"
            :class="{ open: isOpen('tool:' + ti) }"
            @click="toggleDetail('tool:' + ti, () => openRow(t[0] ?? '', t[1] ?? '', t[2] ?? '', '工具句'))"
          >
            <div class="body">
              <div class="t-zh">{{ t[0] }}</div>
              <div class="t-en mono">{{ t[1] }}</div>
              <div class="pills"><el-tag size="small" effect="plain">工具句</el-tag></div>
              <div class="t-note">{{ t[2] }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('tool:' + ti)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredTools.length === 0" class="suli-muted">本小节无命中。</p>
      </section>

      <section class="suli-card block">
        <h3>教学资源 <small>External Guides {{ filteredRes.length }} 卡</small></h3>
        <div class="card-grid">
          <div
            v-for="r in filteredRes"
            :key="r.url"
            class="suli-card tool-card"
            :class="{ open: isOpen('res:' + r.url) }"
            @click="toggleDetail('res:' + r.url, () => openRes(r))"
          >
            <div class="body">
              <div class="t-zh">{{ r.t }}</div>
              <div class="t-en mono">{{ r.url }}</div>
              <div class="pills"><el-tag size="small" effect="plain">{{ r.lang }}</el-tag></div>
              <div class="t-note">{{ r.note }}</div>
            </div>
            <el-dialog append-to-body :model-value="isOpen('res:' + r.url)" @update:model-value="(v: boolean) => { if (!v) openKey = null }" width="min(880px,94vw)" destroy-on-close class="tool-dialog">
              <div class="detail-block" @click.stop>
              <div v-if="detail" class="dlg">
                <div class="detail-cols">
                  <div v-if="detail.dia" class="dlg-cover" v-html="detail.dia"></div>
                  <div class="detail-main">
                    <div class="pills"><el-tag size="small" effect="plain">{{ detail.secTitle }}</el-tag></div>
                    <div class="row"><span class="k">英文</span><pre class="suli-pre mono">{{ detail.en }}</pre></div>
                    <div v-if="detail.parts" class="row"><span class="k">拆解</span><div class="v">{{ detail.parts }}</div></div>
                    <div v-if="detail.ex" class="row"><span class="k">用例</span><div class="v">{{ detail.ex }}</div></div>
                    <div v-if="detail.sayEn" class="row"><span class="k">说法</span><div class="v">{{ detail.sayEn }}</div></div>
                    <div v-if="detail.sayCn" class="row"><span class="k">中文说法</span><div class="v">{{ detail.sayCn }}</div></div>
                    <div v-if="detail.nl" class="row"><span class="k">自然语言 EN</span><pre class="suli-pre mono">{{ detail.nl }}</pre></div>
                    <div v-if="detail.nlc" class="row"><span class="k">自然语言中文</span><div class="v">{{ detail.nlc }}</div></div>
                    <div v-if="detail.note" class="row"><span class="k">说明</span><div class="v">{{ detail.note }}</div></div>
                    <div v-if="detail.extra" class="row"><span class="k">补充</span><div class="v">{{ detail.extra }}</div></div>
                    <div v-if="detail.rows.length > 0" class="row">
                      <span class="k">逐段拆解</span>
                      <div class="v">
                        <div v-for="(r, ri) in detail.rows" :key="ri" class="drow">
                          <div class="mono">{{ r[0] }}</div>
                          <div>{{ r[1] }} ｜ {{ r[2] }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-if="detail.url" class="row">
                      <span class="k">链接</span>
                      <div class="v"><a :href="detail.url" target="_blank" rel="noopener" @click.stop>{{ detail.url }}</a></div>
                    </div>
                  </div>
                </div>
                <div class="dlg-actions">
                  <el-button type="primary" size="small" @click.stop="copyDetailEn">复制英文</el-button>
                  <el-button size="small" @click.stop="addDetailPick">加入组合</el-button>
                  <el-button v-if="detail.nl" size="small" @click.stop="copyDetailNl">复制自然语言版</el-button>
                  <el-button v-if="detail.url" size="small" @click.stop="openDetailUrl">新窗口打开</el-button>
                  <el-button size="small" @click.stop="openKey=null">收起</el-button>
                </div>
              </div>
            </div>
        </el-dialog>
        </div>
        </div>
        <p v-if<p v-if="filteredRes.length === 0" class="suli-muted">本小节无命中。</p>
      </section>



  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { copyText } from '../../utils/clipboard'

interface NlWord {
  en: string
  cn: string
}

interface SecItem {
  zh: string
  en: string
  note: string
  dia: string
}

interface Sec {
  id: string
  title: string
  sub: string
  tip: string
  items: SecItem[]
}

interface Combo {
  zh: string
  en: string
  parts: string
  nl: string
  nlc: string
  note: string
  dia: string
}

interface Dissect {
  zh: string
  en: string
  cn: string
  tag: string
  rows: string[][]
}

interface NlWay {
  name: string
  en: string
  cn: string
}

interface ResItem {
  lang: string
  t: string
  url: string
  note: string
}

interface Cheat {
  zh: string
  en: string
  note: string
}

interface PageDef {
  id: string
  title: string
}

interface GlossRow {
  zh: string
  tag: string
  en: string
  cn: string
}

/* ================= 基础 ================= */
const INK  = '#4a4238';
const RED  = '#c0392b';
const FILL = '#e9e2d6';
const TXT  = '#8d8173';
const GRID = '#cfc7b8';
const DIM  = 'rgba(74,66,56,.12)';

const svg = (inner: string): string => `<svg viewBox="0 0 200 130" xmlns="http://www.w3.org/2000/svg" class="dia">${inner}</svg>`;
const txt = (t: string, x: number, y: number, size = 9.5): string => `<text x="${x}" y="${y}" font-size="${size}" fill="${TXT}" font-family="sans-serif">${t}</text>`;

/* 人物剪影：cx,cy 为中心；总高 = 100*s（头顶 -50s ～ 脚底 +50s） */
function figure(cx: number, cy: number, s = 1, op = 1, fill: string = FILL, stroke: string = INK): string {
  return `<g transform="translate(${cx},${cy}) scale(${s})" opacity="${op}" stroke="${stroke}" stroke-width="1.8" fill="${fill}" stroke-linejoin="round">
    <circle cx="0" cy="-40" r="10"/>
    <path d="M-8 -24 Q0 -31 8 -24 L6 8 L-6 8 Z"/>
    <path d="M-7 -22 L-13 6 M7 -22 L13 6"/>
    <path d="M-3.5 8 L-4.5 50 M3.5 8 L4.5 50"/>
  </g>`;
}

/* 相机图标：默认镜头朝右 */
function cam(x: number, y: number, rot: number, s = 1): string {
  return `<g transform="translate(${x},${y}) rotate(${rot}) scale(${s})">
    <rect x="-14" y="-8" width="24" height="16" rx="3" fill="#fff" stroke="${INK}" stroke-width="1.6"/>
    <rect x="-10" y="-12" width="9" height="4.5" rx="1.5" fill="#fff" stroke="${INK}" stroke-width="1.3"/>
    <circle cx="9" cy="0" r="5" fill="${RED}" opacity=".8"/>
  </g>`;
}

/* ================= 1. 景别 ================= */
function shotSvg(kind: string): string {
  const W = 200, H = 130;
  let body = figure(100, 70, 1), x = 66, y = 10, w = 68, h = 100;
  if (kind === 'ecu')       { y = 30; h = 24; }
  if (kind === 'closeup')   { y = 22; h = 38; }
  if (kind === 'portrait')  { y = 14; h = 50; }
  if (kind === 'bust')      { y = 10; h = 62; }
  if (kind === 'cowboy')    { y = 10; h = 86; }
  if (kind === 'full')      { y = 16; h = 106; }
  if (kind === 'wide')      { body = figure(100, 72, 0.68); x = 26; y = 30; w = 148; h = 86; }
  if (kind === 'xwide')     { body = figure(100, 76, 0.42) + `<line x1="34" y1="100" x2="166" y2="100" stroke="${GRID}" stroke-width="1"/>`; x = 18; y = 10; w = 164; h = 108; }
  if (kind === 'lowerbody') { y = 74; h = 50; }
  const strips =
    `<rect x="0" y="0" width="${W}" height="${y}" fill="${DIM}"/>
     <rect x="0" y="${y + h}" width="${W}" height="${H - y - h}" fill="${DIM}"/>
     <rect x="0" y="${y}" width="${x}" height="${h}" fill="${DIM}"/>
     <rect x="${x + w}" y="${y}" width="${W - x - w}" height="${h}" fill="${DIM}"/>`;
  return svg(`${body}${strips}<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="4" fill="none" stroke="${RED}" stroke-width="1.8"/>`);
}

/* ================= 2. 垂直机位 ================= */
function vAngleSvg(kind: string): string {
  const ground = `<line x1="12" y1="112" x2="188" y2="112" stroke="${INK}" stroke-width="1.6"/>`;
  const body = figure(112, 62, 0.9);
  const dash = (x1: number, y1: number, x2: number, y2: number): string => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${TXT}" stroke-width="1.2" stroke-dasharray="4 3"/>`;
  let inner = '';
  if (kind === 'eye') {
    inner = ground + body + cam(28, 30, 0) + dash(46, 30, 101, 30) + txt('平视 0° · 机位=眼高', 14, 20);
  } else if (kind === 'shoulder') {
    inner = ground + body + cam(28, 42, -6) + dash(45, 43, 102, 31) + txt('肩高 · 微妙威势', 14, 20);
  } else if (kind === 'high15') {
    inner = ground + body + cam(28, 14, 16) + dash(45, 17, 103, 31) + txt('~15° 俯', 14, 20);
  } else if (kind === 'high30') {
    inner = ground + body + cam(26, 6, 26) + dash(43, 10, 105, 44) + txt('~30° 俯', 14, 20);
  } else if (kind === 'high45') {
    inner = ground + body + cam(26, 12, 35) + dash(42, 14, 100, 66) + txt('~45° 俯', 128, 20);
  } else if (kind === 'low15') {
    inner = ground + body + cam(28, 48, -10) + dash(45, 50, 102, 32) + txt('微仰 ~15°（胸高）', 14, 20);
  } else if (kind === 'hip') {
    inner = ground + body + cam(28, 66, -12) + dash(45, 67, 102, 36) + txt('腰高 · 张力', 14, 20);
  } else if (kind === 'knee') {
    inner = ground + body + cam(28, 88, -17) + dash(45, 88, 102, 44) + txt('膝高 · 控制感', 14, 20);
  } else if (kind === 'ground') {
    inner = ground + body + cam(30, 104, -22) + dash(46, 100, 104, 44) + txt('贴地机位', 14, 20);
  } else if (kind === 'low') {
    inner = ground + body + cam(28, 98, -18) + dash(45, 96, 103, 62) + txt('仰视', 14, 100);
  } else if (kind === 'bird') {
    inner = `<line x1="14" y1="108" x2="96" y2="108" stroke="${INK}" stroke-width="1.4"/>` +
      figure(56, 62, 0.55) + cam(56, 14, 90) + `<line x1="56" y1="26" x2="56" y2="38" stroke="${RED}" stroke-width="1.6" marker-end="url(#arw)"/>` +
      `<circle cx="150" cy="50" r="16" fill="${FILL}" stroke="${INK}" stroke-width="1.8"/>` +
      `<path d="M132 76 Q150 62 168 76 L168 92 Q150 84 132 92 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      `<path d="M146 64 L150 74 L154 64 Z" fill="${INK}" opacity=".55"/>` +
      txt('俯视结果：头顶对镜头', 112, 110);
  } else if (kind === 'worm') {
    inner = `<line x1="14" y1="94" x2="96" y2="94" stroke="${INK}" stroke-width="1.4" stroke-dasharray="5 4"/>` +
      figure(56, 48, 0.55) + cam(56, 118, -90) + `<line x1="56" y1="106" x2="56" y2="98" stroke="${RED}" stroke-width="1.6" marker-end="url(#arw)"/>` +
      `<path d="M136 98 L142 48 M166 98 L160 48" stroke="${INK}" stroke-width="1.6" fill="none"/>` +
      `<ellipse cx="136" cy="100" rx="12" ry="7" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      `<ellipse cx="166" cy="100" rx="12" ry="7" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      txt('仰视结果：鞋底/下巴突出', 106, 20);
  }
  return svg(inner);
}

/* ================= 3. 水平机位（俯视示意） ================= */
function hAngleSvg(kind: string): string {
  const cx = 100, cy = 64, R = 50;
  const head = `<circle cx="${cx}" cy="${cy}" r="14" fill="${FILL}" stroke="${INK}" stroke-width="1.8"/>` +
    `<path d="M${cx - 4} ${cy + 13} L${cx} ${cy + 23} L${cx + 4} ${cy + 13} Z" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>`;
  if (kind === 'ots') {
    return svg(
      `<circle cx="62" cy="116" r="38" fill="#ddd5c5" stroke="${INK}" stroke-width="2"/>` +
      `<circle cx="132" cy="46" r="11" fill="${FILL}" stroke="${INK}" stroke-width="1.8"/>` +
      `<path d="M125 58 Q132 52 139 58 L137 84 L127 84 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      cam(34, 112, -50, 0.9) +
      txt('前景肩/后脑（虚化）→ 主角在前', 96, 116)
    );
  }
  if (kind === 'pov') {
    return svg(
      `<path d="M100 122 L34 18 L166 18 Z" fill="rgba(192,57,43,.06)" stroke="${RED}" stroke-width="1.4" stroke-dasharray="5 4"/>` +
      figure(100, 56, 0.4) +
      txt('机位 = 角色眼睛', 76, 124) + txt('视野锥', 32, 14)
    );
  }
  let px = cx, py = cy + R, rot = -90, label = '正面';
  if (kind === 'threequarter') { px = cx + R * 0.72; py = cy + R * 0.72; rot = -135; label = '3/4 侧'; }
  if (kind === 'profile')      { px = cx + R; py = cy; rot = 180; label = '正侧 90°'; }
  if (kind === 'rear')         { px = cx; py = cy - R; rot = 90; label = '正背面'; }
  if (kind === 'back34')       { px = cx + R * 0.72; py = cy - R * 0.72; rot = 135; label = '背 3/4 · 回眸位'; }
  return svg(
    `<line x1="${px}" y1="${py}" x2="${cx}" y2="${cy}" stroke="${TXT}" stroke-width="1.2" stroke-dasharray="4 3"/>` +
    `<circle cx="${cx}" cy="${cy}" r="${R}" fill="none" stroke="${GRID}" stroke-width="1" stroke-dasharray="3 4"/>` +
    head + cam(px, py, rot) + txt(label + '（俯视示意）', 14, 18)
  );
}

/* ================= 4. 荷兰角 ================= */
function dutchSvg(deg: number): string {
  const rad = deg * Math.PI / 180;
  const cos = Math.cos(rad), sin = Math.sin(rad);
  const hx1 = 100 - 62 * cos, hy1 = 76 - 62 * sin, hx2 = 100 + 62 * cos, hy2 = 76 + 62 * sin;
  const wall = (t: number): string => {
    const bx = 100 + t * 62 * cos, by = 76 + t * 62 * sin;
    const tx = bx + 48 * sin, ty = by - 48 * cos;
    return `<line x1="${bx}" y1="${by}" x2="${tx}" y2="${ty}" stroke="${INK}" stroke-width="1.4" opacity=".6"/>`;
  };
  const fig = `<g transform="rotate(${deg} 100 80)">${figure(100, 52, 0.55)}</g>`;
  return svg(
    `<rect x="40" y="16" width="120" height="96" rx="4" fill="none" stroke="${RED}" stroke-width="1.8"/>` +
    `<line x1="40" y1="76" x2="160" y2="76" stroke="${GRID}" stroke-width="1" stroke-dasharray="4 4"/>` +
    `<line x1="${hx1}" y1="${hy1}" x2="${hx2}" y2="${hy2}" stroke="${INK}" stroke-width="1.6"/>` +
    wall(-0.55) + wall(0.55) + fig +
    txt('虚线 = 真实水平线', 44, 126) + txt('画面旋转 ' + deg + '°', 44, 32)
  );
}

/* ================= 5. 焦段与透视 ================= */
function lensSvg(kind: string): string {
  const frame = `<rect x="34" y="14" width="132" height="102" rx="4" fill="none" stroke="${RED}" stroke-width="1.8"/>`;
  const face = (noseLen: number): string => `<circle cx="84" cy="64" r="26" fill="${FILL}" stroke="${INK}" stroke-width="1.8"/>` +
    `<path d="M108 56 L${108 + noseLen} 66 L108 76" fill="none" stroke="${INK}" stroke-width="1.8" stroke-linejoin="round"/>` +
    `<circle cx="94" cy="56" r="2.2" fill="${INK}"/>`;
  const mm = (t: string): string => txt(t, 40, 26, 10);
  if (kind === 'wide24') {
    return svg(frame +
      `<path d="M54 16 Q44 65 54 114 M78 16 Q72 65 78 114 M122 16 Q128 65 122 114 M146 16 Q156 65 146 114" stroke="${GRID}" stroke-width="1.1" fill="none"/>` +
      `<path d="M34 44 Q100 32 166 44 M34 88 Q100 100 166 88" stroke="${GRID}" stroke-width="1.1" fill="none"/>` +
      face(24) + mm('24mm 广角') + txt('近大远小夸张', 108, 122));
  }
  if (kind === 'std50') {
    return svg(frame +
      `<line x1="54" y1="16" x2="54" y2="114" stroke="${GRID}" stroke-width="1"/><line x1="122" y1="16" x2="122" y2="114" stroke="${GRID}" stroke-width="1"/>` +
      `<line x1="34" y1="42" x2="166" y2="42" stroke="${GRID}" stroke-width="1"/><line x1="34" y1="90" x2="166" y2="90" stroke="${GRID}" stroke-width="1"/>` +
      face(16) + mm('50mm 标准') + txt('接近人眼', 112, 122));
  }
  if (kind === 'portrait85') {
    return svg(frame +
      `<line x1="54" y1="16" x2="54" y2="114" stroke="${GRID}" stroke-width="1" opacity=".45"/><line x1="122" y1="16" x2="122" y2="114" stroke="${GRID}" stroke-width="1" opacity=".45"/>` +
      `<line x1="34" y1="42" x2="166" y2="42" stroke="${GRID}" stroke-width="1" opacity=".45"/><line x1="34" y1="90" x2="166" y2="90" stroke="${GRID}" stroke-width="1" opacity=".45"/>` +
      face(14) + mm('85mm 人像') + txt('脸最讨喜 · 背景微虚', 96, 122));
  }
  if (kind === 'tele135') {
    return svg(frame +
      `<rect x="40" y="28" width="34" height="26" rx="6" fill="${GRID}" opacity=".5"/>` +
      `<rect x="130" y="88" width="30" height="22" rx="6" fill="${GRID}" opacity=".5"/>` +
      `<circle cx="58" cy="96" r="9" fill="${RED}" opacity=".14"/><circle cx="146" cy="40" r="12" fill="${RED}" opacity=".14"/><circle cx="70" cy="34" r="7" fill="${RED}" opacity=".14"/>` +
      face(10) + mm('135mm 长焦') + txt('背景被拉近放大 · 糊成色块', 74, 122));
  }
  if (kind === 'fisheye') {
    return svg(frame +
      `<circle cx="100" cy="64" r="50" fill="none" stroke="${INK}" stroke-width="1.6" opacity=".7"/>` +
      `<path d="M38 84 Q100 46 162 84" stroke="${GRID}" stroke-width="1.2" fill="none"/>` +
      `<path d="M56 20 Q78 64 56 108 M144 20 Q122 64 144 108" stroke="${GRID}" stroke-width="1.2" fill="none"/>` +
      face(20) + mm('鱼眼') + txt('极端畸变 · 漫画感', 96, 122));
  }
  /* foreshortening */
  return svg(
    `<ellipse cx="100" cy="86" rx="25" ry="21" fill="${FILL}" stroke="${INK}" stroke-width="1.8"/>` +
    `<path d="M80 74 Q82 62 92 66 M88 68 Q92 58 100 64 M98 66 Q104 58 110 66" fill="none" stroke="${INK}" stroke-width="1.5"/>` +
    `<path d="M86 104 L96 34 M114 104 L104 34" stroke="${INK}" stroke-width="1.5" fill="none"/>` +
    `<ellipse cx="100" cy="28" rx="13" ry="9" fill="${FILL}" stroke="${INK}" stroke-width="1.5"/>` +
    `<line x1="30" y1="108" x2="68" y2="96" stroke="${RED}" stroke-width="1.6" marker-end="url(#arw)"/>` +
    txt('手伸向镜头（近大远小）', 96, 122) + txt('foreshortening', 12, 22)
  );
}

/* ================= 5d. 景深 ================= */
function dofSvg(kind: string): string {
  const camIcon = cam(28, 64, 0, 0.85);
  if (kind === 'shallow') {
    return svg(camIcon +
      `<circle cx="64" cy="82" r="13" fill="${RED}" opacity=".13"/>` +
      `<line x1="116" y1="20" x2="116" y2="108" stroke="${GRID}" stroke-width="1.2" stroke-dasharray="4 3"/>` +
      figure(116, 70, 0.5) +
      `<circle cx="150" cy="40" r="10" fill="${RED}" opacity=".18"/><circle cx="166" cy="58" r="7" fill="${RED}" opacity=".18"/><circle cx="146" cy="76" r="12" fill="${RED}" opacity=".16"/><circle cx="168" cy="94" r="8" fill="${RED}" opacity=".16"/>` +
      txt('浅景深：主体实 · 前后虚（虚化=指向）', 34, 124));
  }
  if (kind === 'deep') {
    return svg(camIcon +
      `<rect x="120" y="22" width="22" height="86" fill="none" stroke="${GRID}" stroke-width="1.3"/>` +
      `<rect x="146" y="34" width="20" height="74" fill="none" stroke="${GRID}" stroke-width="1.3"/>` +
      `<line x1="40" y1="30" x2="188" y2="30" stroke="${GRID}" stroke-width="1"/>` +
      `<line x1="40" y1="108" x2="188" y2="108" stroke="${GRID}" stroke-width="1"/>` +
      figure(88, 72, 0.48) +
      txt('深景深：远近全清晰（环境叙事）', 36, 124));
  }
  /* bokeh */
  return svg(
    figure(104, 74, 0.4, .5) +
    `<circle cx="66" cy="44" r="16" fill="${RED}" opacity=".16"/>` +
    `<circle cx="104" cy="60" r="22" fill="#e0a05c" opacity=".16"/>` +
    `<circle cx="144" cy="40" r="13" fill="#9db3c8" opacity=".2"/>` +
    `<circle cx="134" cy="88" r="17" fill="${RED}" opacity=".14"/>` +
    `<circle cx="80" cy="96" r="9" fill="#9db3c8" opacity=".18"/>` +
    txt('焦外光斑：光点化成柔圆（bokeh）', 36, 124));
}

/* ================= 5b. 透视体系 ================= */
function perspSvg(kind: string): string {
  const frame = `<rect x="30" y="14" width="140" height="102" rx="4" fill="none" stroke="${RED}" stroke-width="1.8"/>`;
  if (kind === 'onepoint') {
    return svg(frame +
      `<path d="M30 14 L100 56 M170 14 L100 56 M30 116 L100 56 M170 116 L100 56 M62 116 L100 56 M138 116 L100 56" stroke="${GRID}" stroke-width="1.1" fill="none"/>` +
      `<circle cx="100" cy="56" r="3" fill="${RED}"/>` +
      figure(100, 76, 0.42) +
      txt('灭点在画面中（走廊/街道纵深）', 40, 128));
  }
  if (kind === 'twopoint') {
    return svg(frame +
      `<line x1="30" y1="60" x2="170" y2="60" stroke="${GRID}" stroke-width="1" stroke-dasharray="5 4"/>` +
      `<path d="M100 100 L100 30 M100 30 L30 46 M100 30 L170 46 M100 100 L30 84 M100 100 L170 84" stroke="${INK}" stroke-width="1.6" fill="none"/>` +
      `<rect x="82" y="38" width="10" height="10" fill="none" stroke="${INK}" stroke-width="1.2"/><rect x="108" y="38" width="10" height="10" fill="none" stroke="${INK}" stroke-width="1.2"/>` +
      figure(100, 77, 0.45) +
      txt('← 灭点1（框外）', 30, 56) + txt('灭点2（框外）→', 112, 56) + txt('街角双面墙', 82, 128));
  }
  return svg(frame +
    `<path d="M70 112 L88 30 L112 30 L130 112 Z" fill="${FILL}" opacity=".55" stroke="${INK}" stroke-width="1.6"/>` +
    `<path d="M76 92 L124 92 M82 62 L118 62" stroke="${GRID}" stroke-width="1"/>` +
    `<circle cx="100" cy="20" r="3" fill="${RED}"/>` +
    figure(100, 87, 0.5) +
    txt('第三灭点在天顶 · 仰拍高楼', 48, 128));
}

/* ================= 6. 构图法 ================= */
function compSvg(kind: string): string {
  const frame = `<rect x="26" y="12" width="148" height="106" rx="4" fill="none" stroke="${INK}" stroke-width="1.3" opacity=".5"/>`;
  const dline = (a: number, b: number, c: number, d: number, col: string = GRID, dash: string = '4 4'): string => `<line x1="${a}" y1="${b}" x2="${c}" y2="${d}" stroke="${col}" stroke-width="1" stroke-dasharray="${dash}"/>`;
  if (kind === 'thirds') {
    return svg(frame +
      dline(75, 12, 75, 118) + dline(125, 12, 125, 118) + dline(26, 47, 174, 47) + dline(26, 83, 174, 83) +
      `<circle cx="75" cy="47" r="2.4" fill="${RED}"/><circle cx="125" cy="47" r="2.4" fill="${RED}"/><circle cx="75" cy="83" r="2.4" fill="${RED}"/><circle cx="125" cy="83" r="2.4" fill="${RED}"/>` +
      figure(75, 63, 0.4) + txt('眼睛压交点 · 地平线压三分线', 42, 128));
  }
  if (kind === 'triangle') {
    return svg(frame + figure(100, 64, 0.7) +
      `<path d="M100 29 L78 102 L122 102 Z" fill="rgba(192,57,43,.10)" stroke="${RED}" stroke-width="1.4" stroke-dasharray="5 3"/>` +
      txt('正三角=稳 · 倒三角=动', 62, 128));
  }
  if (kind === 'space') {
    return svg(frame +
      `<rect x="96" y="16" width="74" height="98" fill="rgba(122,111,99,.10)"/>` +
      figure(64, 70, 0.55) +
      `<path d="M82 52 L140 52" stroke="${RED}" stroke-width="1.6" marker-end="url(#arw)"/>` +
      txt('视线方向留白 · 不放道具', 102, 70));
  }
  if (kind === 'negative') {
    return svg(frame + figure(100, 86, 0.28) +
      `<path d="M64 46 L136 46" stroke="${GRID}" stroke-width="1" stroke-dasharray="4 4"/>` +
      txt('负空间 = 内容本身', 68, 38) + txt('人物压小压底', 68, 112));
  }
  if (kind === 'leading') {
    return svg(frame +
      `<path d="M26 118 L100 52 M174 118 L100 52 M26 34 L100 52 M174 34 L100 52" stroke="${GRID}" stroke-width="1.2" fill="none"/>` +
      `<circle cx="100" cy="52" r="3" fill="${RED}"/>` +
      figure(100, 61, 0.45) + txt('灭点', 88, 46) + txt('墙角竖缝收束到脸/脑后', 46, 128));
  }
  if (kind === 'symmetric') {
    return svg(frame + dline(100, 12, 100, 118, GRID, '5 4') +
      `<path d="M40 12 L84 118 M160 12 L116 118" stroke="${INK}" stroke-width="1.3" opacity=".55" fill="none"/>` +
      figure(100, 59, 0.5) + txt('两面墙天然对称框', 62, 128));
  }
  if (kind === 'fif') {
    return svg(frame +
      `<rect x="70" y="22" width="60" height="96" fill="none" stroke="${INK}" stroke-width="1.8"/>` +
      figure(100, 59, 0.5) + txt('门框/窗框包住主体', 66, 128));
  }
  if (kind === 'diagonal') {
    return svg(frame +
      `<path d="M40 112 L160 28" stroke="${RED}" stroke-width="2" opacity=".5"/>` +
      figure(96, 48, 0.5) +
      txt('主体沿对角线排布 = 张力', 52, 128));
  }
  if (kind === 'golden') {
    return svg(frame +
      dline(83, 12, 83, 118) + dline(117, 12, 117, 118) + dline(26, 53, 174, 53) + dline(26, 77, 174, 77) +
      `<circle cx="83" cy="53" r="3" fill="${RED}"/>` +
      figure(83, 69, 0.4) +
      txt('黄金分割 0.618 · 比三分更柔', 44, 128));
  }
  if (kind === 'scurve') {
    return svg(frame +
      `<path d="M122 18 Q56 40 108 72 Q156 96 88 120" fill="none" stroke="${RED}" stroke-width="2" opacity=".5"/>` +
      figure(104, 62, 0.5) +
      txt('S 形引导线（道路/身姿/水岸）', 44, 128));
  }
  if (kind === 'fgblock') {
    return svg(frame +
      `<rect x="30" y="14" width="22" height="102" fill="#6b6156" opacity=".85"/>` +
      `<path d="M170 116 L126 116 Q150 96 170 92 Z" fill="#6b6156" opacity=".7"/>` +
      figure(106, 72, 0.5) +
      txt('前景遮挡 = 纵深层次', 62, 128));
  }
  if (kind === 'reflect') {
    return svg(frame +
      `<line x1="30" y1="84" x2="170" y2="84" stroke="${GRID}" stroke-width="1.2" stroke-dasharray="5 4"/>` +
      figure(100, 62, 0.4) +
      `<g opacity=".4" transform="translate(0,168) scale(1,-1)">${figure(100, 62, 0.4)}</g>` +
      txt('水面/镜面倒影 · 信息翻倍', 48, 128));
  }
  if (kind === 'repeat') {
    return svg(frame +
      `<rect x="52" y="24" width="26" height="30" fill="none" stroke="${GRID}" stroke-width="1.2"/>` +
      `<rect x="92" y="24" width="26" height="30" fill="${RED}" opacity=".16" stroke="${GRID}" stroke-width="1.2"/>` +
      `<rect x="132" y="24" width="26" height="30" fill="none" stroke="${GRID}" stroke-width="1.2"/>` +
      `<rect x="52" y="70" width="26" height="30" fill="none" stroke="${GRID}" stroke-width="1.2"/>` +
      `<rect x="92" y="70" width="26" height="30" fill="none" stroke="${GRID}" stroke-width="1.2"/>` +
      `<rect x="132" y="70" width="26" height="30" fill="none" stroke="${GRID}" stroke-width="1.2"/>` +
      txt('重复 = 秩序 · 破一处 = 焦点', 48, 128));
  }
  if (kind === 'twoshot') {
    return svg(frame +
      figure(74, 68, 0.52) + figure(126, 68, 0.52) +
      `<path d="M86 52 L104 52" stroke="${RED}" stroke-width="1.5" marker-end="url(#arw)"/>` +
      `<path d="M114 52 L96 52" stroke="${RED}" stroke-width="1.5" marker-end="url(#arw)"/>` +
      txt('双人镜头 · 对峙/关系', 68, 128));
  }
  if (kind === 'largetosmall') {
    return svg(frame +
      `<circle cx="52" cy="34" r="15" fill="rgba(122,111,99,.28)"/>` +
      `<circle cx="86" cy="56" r="9" fill="rgba(122,111,99,.28)"/>` +
      `<circle cx="112" cy="72" r="5.5" fill="rgba(122,111,99,.28)"/>` +
      `<path d="M60 44 Q96 62 128 80" stroke="${RED}" stroke-width="1.4" fill="none" stroke-dasharray="4 3" marker-end="url(#arw)"/>` +
      figure(138, 84, 0.32) +
      txt('视线从大到小流动，主体在终点', 40, 128));
  }
  if (kind === 'density') {
    let dotsA = '', dotsB = '';
    for (let r = 0; r < 4; r++) for (let c = 0; c < 5; c++) {
      const x = 42 + c * 12, y = 34 + r * 14;
      dotsA += `<circle cx="${x}" cy="${y}" r="2.2" fill="${GRID}"/>`;
      const xb = x + 70, nb = Math.abs(xb - 136) < 12 && Math.abs(y - 62) < 15;
      if (!nb) dotsB += `<circle cx="${xb}" cy="${y}" r="2.2" fill="${GRID}"/>`;
    }
    return svg(frame +
      `<line x1="100" y1="18" x2="100" y2="110" stroke="${GRID}" stroke-width="1" stroke-dasharray="4 4"/>` +
      dotsA + dotsB +
      `<circle cx="136" cy="62" r="3.2" fill="${RED}"/>` +
      txt('均匀=无焦点', 40, 126) + txt('密中留空=焦点', 114, 126));
  }
  if (kind === 'balance') {
    return svg(frame + dline(100, 14, 100, 114, GRID, '5 4') +
      `<circle cx="66" cy="62" r="22" fill="rgba(74,66,56,.5)"/>` +
      `<circle cx="120" cy="44" r="7" fill="${GRID}"/><circle cx="134" cy="56" r="7" fill="${GRID}"/><circle cx="118" cy="70" r="7" fill="${GRID}"/><circle cx="132" cy="82" r="7" fill="${GRID}"/><circle cx="142" cy="66" r="6" fill="${GRID}"/>` +
      txt('大 vs 一组小 = 配平', 46, 128));
  }
  if (kind === 'contrast') {
    return svg(frame +
      `<rect x="30" y="14" width="140" height="100" fill="rgba(74,66,56,.45)"/>` +
      figure(112, 64, 0.5) +
      txt('亮主体压暗底 · 对比即焦点', 42, 128));
  }
  if (kind === 'squeeze') {
    return svg(
      `<rect x="40" y="14" width="120" height="100" rx="4" fill="none" stroke="${RED}" stroke-width="1.8"/>` +
      figure(100, 64, 0.62) +
      `<path d="M26 24 L46 34 M174 24 L154 34 M26 106 L46 96 M174 106 L154 96" stroke="${RED}" stroke-width="1.4" marker-end="url(#arw)"/>` +
      txt('四面切紧贴边 = 窒息/被困', 44, 126));
  }
  if (kind === 'headroom') {
    return svg(frame +
      figure(100, 64, 0.62) +
      `<path d="M60 15 L60 32" stroke="${RED}" stroke-width="1.3"/>` +
      `<path d="M56 15 L64 15 M56 32 L64 32" stroke="${RED}" stroke-width="1.3"/>` +
      txt('头顶空间：留一点，别顶边也别太空', 40, 128));
  }
  if (kind === 'leadroom') {
    return svg(frame +
      `<rect x="98" y="16" width="72" height="98" fill="rgba(122,111,99,.08)"/>` +
      `<path d="M36 94 L124 90" stroke="${GRID}" stroke-width="1.5" stroke-dasharray="5 4"/>` +
      figure(74, 70, 0.5) +
      `<path d="M88 50 L146 46" stroke="${RED}" stroke-width="1.5" marker-end="url(#arw)"/>` +
      txt('运动方向前留空间', 102, 72));
  }
  /* centered */
  return svg(frame + dline(100, 12, 100, 118, GRID, '5 4') + figure(100, 44, 0.6) +
    `<path d="M52 112 L94 112 M106 112 L148 112" stroke="${RED}" stroke-width="1.4"/>` +
    `<path d="M52 112 l6 -3 l0 6 Z M148 112 l-6 -3 l0 6 Z" fill="${RED}"/>` +
    txt('等距留白 · 正面压迫', 72, 126));
}

/* ================= 7. 特殊机位 ================= */
function specialSvg(kind: string): string {
  const frame = `<rect x="26" y="12" width="148" height="106" rx="4" fill="none" stroke="${INK}" stroke-width="1.3" opacity=".5"/>`;
  if (kind === 'cctv') {
    return svg(frame +
      `<path d="M30 116 L100 38 M170 116 L100 38 M64 116 L100 38 M136 116 L100 38" stroke="${GRID}" stroke-width="1" fill="none"/>` +
      `<circle cx="100" cy="38" r="2.6" fill="${RED}"/>` +
      figure(100, 84, 0.4) +
      cam(44, 26, 45, 0.85) +
      txt('监控视角 · 高角广角 · 俯看全场', 46, 128));
  }
  if (kind === 'aerial') {
    return svg(
      `<rect x="30" y="34" width="140" height="80" fill="rgba(122,111,99,.06)"/>` +
      `<rect x="46" y="58" width="22" height="16" fill="${FILL}" stroke="${GRID}" stroke-width="1.2"/>` +
      `<rect x="88" y="48" width="26" height="20" fill="${FILL}" stroke="${GRID}" stroke-width="1.2"/>` +
      `<rect x="134" y="62" width="18" height="14" fill="${FILL}" stroke="${GRID}" stroke-width="1.2"/>` +
      figure(74, 98, 0.2) +
      cam(40, 22, 42, 0.8) +
      `<path d="M52 28 L84 58" stroke="${TXT}" stroke-width="1" stroke-dasharray="4 3"/>` +
      txt('航拍 · 大全景俯视（尺度感）', 42, 126));
  }
  if (kind === 'selfie') {
    return svg(
      `<circle cx="100" cy="42" r="17" fill="${FILL}" stroke="${INK}" stroke-width="1.8"/>` +
      `<circle cx="90" cy="40" r="1.8" fill="${INK}"/><circle cx="110" cy="40" r="1.8" fill="${INK}"/>` +
      `<path d="M92 52 Q100 58 108 52" fill="none" stroke="${INK}" stroke-width="1.5"/>` +
      `<path d="M72 68 Q100 54 128 68 L124 94 L76 94 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      `<rect x="76" y="86" width="48" height="34" rx="7" fill="#fff" stroke="${INK}" stroke-width="1.7"/>` +
      `<circle cx="100" cy="103" r="5" fill="${RED}" opacity=".7"/>` +
      `<path d="M40 130 Q62 100 76 92 M160 130 Q138 100 124 92" stroke="${INK}" stroke-width="1.5" fill="none"/>` +
      txt('自拍 · 手机近大（近大远小）', 58, 128));
  }
  return svg(frame +
    `<rect x="54" y="22" width="92" height="88" fill="none" stroke="${INK}" stroke-width="2"/>` +
    `<line x1="100" y1="22" x2="100" y2="110" stroke="${INK}" stroke-width="1.4"/>` +
    `<line x1="54" y1="72" x2="146" y2="72" stroke="${INK}" stroke-width="1.4"/>` +
    figure(80, 82, 0.42) +
    txt('窗外/门框窥视 · 框内叙事', 50, 128));
}

/* ================= 8. 组合实战图 ================= */
function caseSvg(kind: string): string {
  const frame = `<rect x="30" y="14" width="140" height="100" rx="4" fill="none" stroke="${RED}" stroke-width="1.8"/>`;
  if (kind === 'confront') {
    return svg(
      `<rect x="40" y="16" width="120" height="96" rx="4" fill="none" stroke="${RED}" stroke-width="1.8"/>` +
      `<line x1="44" y1="88" x2="156" y2="58" stroke="${GRID}" stroke-width="1" stroke-dasharray="4 4"/>` +
      `<line x1="104" y1="18" x2="86" y2="110" stroke="${INK}" stroke-width="1.6" opacity=".55"/>` +
      `<path d="M88 108 L52 74 M88 108 L140 64" stroke="${GRID}" stroke-width="1" fill="none"/>` +
      `<path d="M46 112 L92 48 M154 112 L108 48" stroke="${GRID}" stroke-width="1.1" fill="none"/>` +
      `<g transform="rotate(14 100 92)">${figure(100, 62, 0.6)}<rect x="90" y="34" width="20" height="6" fill="#3b3540" opacity=".5"/></g>` +
      cam(34, 22, 32, 0.75) +
      `<path d="M46 30 L80 46" stroke="${TXT}" stroke-width="1" stroke-dasharray="4 3"/>` +
      txt('俯30° + 斜切15° + 半身 + 居中 + 引导线', 34, 124)
    );
  }
  if (kind === 'solitude') {
    return svg(
      frame +
      `<rect x="96" y="18" width="74" height="86" fill="rgba(122,111,99,.08)"/>` +
      `<line x1="30" y1="104" x2="170" y2="104" stroke="${INK}" stroke-width="1.4"/>` +
      figure(62, 88, 0.3) +
      `<path d="M76 74 L126 68" stroke="${RED}" stroke-width="1.4" marker-end="url(#arw)"/>` +
      txt('负空间', 132, 52) + txt('视线留白', 78, 62) +
      txt('远景 + 视线留白 + 负空间', 46, 124)
    );
  }
  if (kind === 'lookback') {
    return svg(
      frame +
      `<path d="M30 20 L92 20 L92 108 L30 108 Z" fill="rgba(122,111,99,.08)"/>` +
      `<path d="M96 56 L46 56" stroke="${RED}" stroke-width="1.4" marker-end="url(#arw)"/>` +
      `<path d="M92 72 Q116 56 142 70 L138 100 L98 100 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      `<circle cx="116" cy="50" r="15" fill="#4a4238" opacity=".85" stroke="${INK}" stroke-width="1.5"/>` +
      `<path d="M104 46 Q102 52 103 58" stroke="${FILL}" stroke-width="5" fill="none"/>` +
      `<circle cx="104" cy="48" r="1.7" fill="${INK}"/>` +
      txt('留白', 44, 40) +
      txt('背 3/4 + 半身 + 视线留白（回眸）', 32, 124)
    );
  }
  if (kind === 'lowlegs') {
    return svg(
      frame +
      `<line x1="30" y1="112" x2="170" y2="112" stroke="${INK}" stroke-width="1.4"/>` +
      `<path d="M46 114 L76 46 M154 114 L124 46" stroke="${GRID}" stroke-width="1" fill="none"/>` +
      `<path d="M84 32 L116 32 L128 56 L72 56 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      `<path d="M90 56 L87 98 M110 56 L113 98" stroke="${INK}" stroke-width="1.6"/>` +
      `<ellipse cx="85" cy="104" rx="16" ry="8" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      `<ellipse cx="115" cy="104" rx="16" ry="8" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      cam(40, 106, -22, 0.75) +
      txt('贴地机位 + 下半身 + 透视缩短', 38, 24)
    );
  }
  if (kind === 'watch') {
    return svg(
      frame +
      `<path d="M40 116 L92 36 M160 116 L108 36 M72 116 L94 36 M128 116 L106 36" stroke="${GRID}" stroke-width="1" fill="none"/>` +
      `<circle cx="100" cy="36" r="2.6" fill="${RED}"/>` +
      figure(100, 84, 0.36) +
      cam(48, 26, 45, 0.75) +
      `<path d="M156 28 Q170 52 154 74" stroke="${GRID}" stroke-width="1" fill="none" stroke-dasharray="4 3"/>` +
      txt('监控视角 + 高角 + 广角（被观察）', 34, 124)
    );
  }
  if (kind === 'corridor') {
    return svg(
      frame +
      `<rect x="88" y="48" width="24" height="20" rx="2" fill="${RED}" opacity=".12"/>` +
      `<path d="M30 116 L96 62 M170 116 L104 62 M30 14 L96 50 M170 14 L104 50" stroke="${GRID}" stroke-width="1.1" fill="none"/>` +
      `<line x1="30" y1="64" x2="96" y2="57" stroke="${GRID}" stroke-width="1"/>` +
      `<line x1="170" y1="64" x2="104" y2="57" stroke="${GRID}" stroke-width="1"/>` +
      `<circle cx="100" cy="56" r="2.6" fill="${RED}"/>` +
      figure(100, 88, 0.42) +
      txt('一点透视 + 引导线 + 全身（纵深）', 40, 124)
    );
  }
  if (kind === 'moonwater') {
    return svg(
      frame +
      `<line x1="30" y1="80" x2="170" y2="80" stroke="${GRID}" stroke-width="1.2" stroke-dasharray="5 4"/>` +
      `<rect x="96" y="18" width="74" height="92" fill="rgba(122,111,99,.08)"/>` +
      figure(64, 64, 0.32) +
      `<g opacity=".4" transform="translate(0,160) scale(1,-1)">${figure(64, 64, 0.32)}</g>` +
      `<path d="M80 52 L124 48" stroke="${RED}" stroke-width="1.4" marker-end="url(#arw)"/>` +
      txt('负空间', 130, 40) +
      txt('远景 + 反射镜像 + 负空间', 48, 124)
    );
  }
  if (kind === 'depth') {
    return svg(frame +
      `<circle cx="52" cy="40" r="9" fill="${RED}" opacity=".12"/><circle cx="86" cy="30" r="12" fill="${RED}" opacity=".12"/><circle cx="128" cy="36" r="10" fill="${RED}" opacity=".12"/><circle cx="156" cy="28" r="8" fill="${RED}" opacity=".12"/>` +
      `<line x1="30" y1="60" x2="170" y2="60" stroke="${GRID}" stroke-width="1" stroke-dasharray="5 4"/>` +
      figure(100, 70, 0.42) +
      `<rect x="30" y="78" width="140" height="9" fill="#8d857a" opacity=".4"/>` +
      `<rect x="30" y="88" width="140" height="7" fill="#8d857a" opacity=".28"/>` +
      txt('前景栏杆虚 · 中景主体实 · 后景光斑堆叠', 34, 124));
  }
  if (kind === 'backlit') {
    return svg(frame +
      `<rect x="60" y="24" width="80" height="70" rx="3" fill="#fbf3dd" stroke="${GRID}" stroke-width="1.4"/>` +
      `<circle cx="76" cy="44" r="1.6" fill="${TXT}"/><circle cx="120" cy="36" r="1.4" fill="${TXT}"/><circle cx="88" cy="30" r="1.2" fill="${TXT}"/><circle cx="132" cy="52" r="1.5" fill="${TXT}"/>` +
      figure(100, 62, 0.52, 1, '#3a3440', '#f3e9d2') +
      `<rect x="30" y="94" width="140" height="20" fill="rgba(58,52,64,.35)"/>` +
      txt('逆光剪影 + 轮光 + 尘粒 + 前景深影', 34, 124));
  }
  if (kind === 'relay') {
    return svg(frame +
      `<circle cx="64" cy="114" r="35" fill="#4a4238" opacity=".75"/>` +
      `<circle cx="128" cy="52" r="13" fill="${FILL}" stroke="${INK}" stroke-width="1.7"/>` +
      `<path d="M119 66 Q128 58 137 66 L135 96 L121 96 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.5"/>` +
      `<circle cx="135" cy="50" r="1.6" fill="${INK}"/>` +
      `<path d="M142 48 L168 44" stroke="${RED}" stroke-width="1.4" stroke-dasharray="4 3" marker-end="url(#arw)"/>` +
      txt('前景肩（虚）+ 中景主体 + 视线留白', 36, 124));
  }
  if (kind === 'mirror2') {
    return svg(frame +
      `<line x1="100" y1="14" x2="100" y2="114" stroke="${GRID}" stroke-width="1" stroke-dasharray="5 4"/>` +
      `<circle cx="76" cy="52" r="14" fill="#4a4238" opacity=".85" stroke="${INK}" stroke-width="1.4"/>` +
      `<path d="M60 74 Q76 58 92 74 L88 100 L64 100 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.5"/>` +
      `<circle cx="128" cy="52" r="14" fill="${FILL}" stroke="${INK}" stroke-width="1.7"/>` +
      `<circle cx="123" cy="50" r="1.7" fill="${INK}"/><circle cx="133" cy="50" r="1.7" fill="${INK}"/>` +
      `<path d="M112 74 Q128 58 144 74 L140 100 L116 100 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.5"/>` +
      txt('镜面两侧：真身背影 ← → 镜中正脸', 36, 124));
  }
  if (kind === 'grounddyn') {
    return svg(frame +
      `<line x1="30" y1="104" x2="170" y2="92" stroke="${GRID}" stroke-width="1" stroke-dasharray="4 4"/>` +
      `<path d="M44 34 L40 50 M58 24 L54 42 M148 28 L144 46 M160 40 L156 58" stroke="${GRID}" stroke-width="2.4" stroke-linecap="round" opacity=".75"/>` +
      `<path d="M70 36 L130 36 L126 46 L74 46 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.4"/>` +
      `<path d="M80 46 L84 82 M120 46 L118 80" stroke="${INK}" stroke-width="1.6" fill="none"/>` +
      `<ellipse cx="86" cy="92" rx="19" ry="10" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      `<ellipse cx="118" cy="86" rx="19" ry="10" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      txt('贴地 + 靴子近大 + 雨痕 + 斜切动势', 36, 124));
  }
  if (kind === 'nested') {
    return svg(frame +
      `<rect x="40" y="20" width="120" height="94" fill="none" stroke="${INK}" stroke-width="2"/>` +
      `<rect x="68" y="34" width="64" height="80" fill="none" stroke="${INK}" stroke-width="1.7"/>` +
      `<rect x="84" y="48" width="32" height="42" rx="2" fill="${RED}" opacity=".12"/>` +
      figure(100, 84, 0.34) +
      txt('门框套门框 + 光池收束 + 远处小人', 36, 124));
  }
  if (kind === 'insert') {
    return svg(frame +
      `<g opacity=".35"><circle cx="100" cy="30" r="10" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/><path d="M90 44 Q100 36 110 44 L108 62 L92 62 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.4"/></g>` +
      `<path d="M60 92 Q56 66 76 60 Q96 56 102 72 L102 94 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.7"/>` +
      `<path d="M68 66 Q78 60 88 64 M70 76 Q80 70 92 74" fill="none" stroke="${INK}" stroke-width="1.3"/>` +
      `<path d="M84 56 L90 96" stroke="${INK}" stroke-width="3" opacity=".55"/>` +
      txt('插入镜头：焦点在手上，人虚在后景', 36, 124));
  }
  if (kind === 'topdown') {
    return svg(frame +
      `<circle cx="66" cy="44" r="12" fill="none" stroke="${GRID}" stroke-width="1.6"/>` +
      `<circle cx="106" cy="44" r="12" fill="none" stroke="${GRID}" stroke-width="1.6"/>` +
      `<circle cx="66" cy="84" r="12" fill="none" stroke="${GRID}" stroke-width="1.6"/>` +
      `<circle cx="106" cy="76" r="12" fill="none" stroke="${RED}" stroke-width="1.7"/>` +
      `<rect x="134" y="36" width="18" height="26" rx="4" fill="none" stroke="${GRID}" stroke-width="1.5"/>` +
      `<path d="M40 60 L58 62 M40 68 L58 70" stroke="${INK}" stroke-width="1.6" fill="none"/>` +
      txt('俯视对称 · 一只歪杯破格', 44, 124));
  }
  /* battle */
  return svg(
    frame +
    `<line x1="36" y1="94" x2="164" y2="70" stroke="${GRID}" stroke-width="1" stroke-dasharray="4 4"/>` +
    `<path d="M40 112 L160 28" stroke="${RED}" stroke-width="2" opacity=".4"/>` +
    `<circle cx="92" cy="40" r="11" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
    `<path d="M85 60 Q92 52 101 60 L99 82 L87 82 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.5"/>` +
    `<path d="M96 66 L114 84 M88 66 L100 88" stroke="${INK}" stroke-width="1.5" fill="none"/>` +
    `<ellipse cx="124" cy="94" rx="21" ry="17" fill="${FILL}" stroke="${INK}" stroke-width="1.8"/>` +
    `<path d="M108 86 Q112 76 120 80 M116 80 Q122 72 130 78 M126 78 Q132 72 138 80" fill="none" stroke="${INK}" stroke-width="1.4"/>` +
    txt('仰视 + 透视缩短 + 对角线', 56, 124)
  );
}

/* ================= 8b. 画幅比例 ================= */
function ratioSvg(kind: string): string {
  const specs: Record<string, number[]> = { p34: [76, 100], p45: [72, 92], p169: [148, 84], p11: [88, 88] };
  const [w, h] = specs[kind];
  const x = 100 - w / 2, y = 64 - h / 2;
  const figScale = (h - 16) / 100 * 0.92;
  const label = kind === 'p169' ? '横：环境与人物同框' : kind === 'p11' ? '方：概念/头像' : '竖：人像主力';
  return svg(
    `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="4" fill="#fff" stroke="${RED}" stroke-width="1.8"/>` +
    figure(100, 64, figScale) +
    txt(label, 46, 126)
  );
}

/* ================= 8c. 镜头语法 ================= */
function gramSvg(kind: string): string {
  if (kind === 'axis') {
    return svg(
      `<line x1="32" y1="58" x2="168" y2="58" stroke="${RED}" stroke-width="1.5" stroke-dasharray="6 4"/>` +
      `<circle cx="70" cy="58" r="11" fill="${FILL}" stroke="${INK}" stroke-width="1.7"/>` +
      `<circle cx="130" cy="58" r="11" fill="${FILL}" stroke="${INK}" stroke-width="1.7"/>` +
      `<path d="M78 54 L88 58 L78 62 Z" fill="${INK}" opacity=".6"/>` +
      `<path d="M122 54 L112 58 L122 62 Z" fill="${INK}" opacity=".6"/>` +
      cam(70, 108, -90, 0.85) + cam(130, 108, -90, 0.85) +
      `<circle cx="100" cy="22" r="13" fill="none" stroke="${RED}" stroke-width="1.5"/>` +
      `<path d="M91 13 L109 31 M109 13 L91 31" stroke="${RED}" stroke-width="1.6"/>` +
      txt('机位全在轴线同一侧 · 越轴=空间乱', 34, 124)
    );
  }
  if (kind === 'reverse') {
    return svg(
      `<circle cx="62" cy="50" r="11" fill="${FILL}" stroke="${INK}" stroke-width="1.7"/>` +
      `<circle cx="138" cy="50" r="11" fill="${FILL}" stroke="${INK}" stroke-width="1.7"/>` +
      `<path d="M72 46 L88 46" stroke="${INK}" stroke-width="1.4" marker-end="url(#arw)"/>` +
      `<path d="M128 54 L112 54" stroke="${INK}" stroke-width="1.4" marker-end="url(#arw)"/>` +
      cam(62, 106, -90, 0.85) + cam(138, 106, -90, 0.85) +
      txt('镜头A', 44, 122) + txt('镜头B', 124, 122) +
      txt('视线互为反向 · 机位同侧', 62, 18)
    );
  }
  if (kind === 'eyeline') {
    return svg(
      `<rect x="30" y="24" width="60" height="76" fill="none" stroke="${GRID}" stroke-width="1.4"/>` +
      `<rect x="110" y="24" width="60" height="76" fill="none" stroke="${GRID}" stroke-width="1.4"/>` +
      `<circle cx="52" cy="52" r="9" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      `<path d="M60 50 L70 52 L60 54 Z" fill="${INK}" opacity=".6"/>` +
      `<path d="M66 62 L92 62" stroke="${RED}" stroke-width="1.3" marker-end="url(#arw)"/>` +
      `<circle cx="148" cy="52" r="9" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      `<path d="M140 50 L130 52 L140 54 Z" fill="${INK}" opacity=".6"/>` +
      `<path d="M134 62 L108 62" stroke="${RED}" stroke-width="1.3" marker-end="url(#arw)"/>` +
      txt('A看画外右', 38, 116) + txt('画外左看回B', 112, 116) +
      txt('视线匹配：方向必须互为反转', 46, 16)
    );
  }
  /* angle30 */
  return svg(
    `<circle cx="100" cy="40" r="12" fill="${FILL}" stroke="${INK}" stroke-width="1.7"/>` +
    `<line x1="100" y1="52" x2="100" y2="112" stroke="${GRID}" stroke-width="1" stroke-dasharray="4 4"/>` +
    cam(72, 100, -60, 0.85) + cam(128, 100, -120, 0.85) +
    `<path d="M86 88 A 34 34 0 0 1 114 88" fill="none" stroke="${RED}" stroke-width="1.5"/>` +
    txt('≥30°', 93, 80) +
    txt('同主体换机位 ≥30° · 否则像重复素材', 34, 124)
  );
}

/* ================= 8d. 光影 ================= */
function lightSvg(kind: string): string {
  const sun = (x: number, y: number, c: string = '#e0a05c'): string => `<circle cx="${x}" cy="${y}" r="9" fill="${c}" opacity=".9"/><path d="M${x-15} ${y} L${x-11} ${y} M${x+11} ${y} L${x+15} ${y} M${x} ${y-15} L${x} ${y-11} M${x} ${y+11} L${x} ${y+15}" stroke="${c}" stroke-width="1.6"/>`;
  const head = `<circle cx="100" cy="56" r="26" fill="${FILL}" stroke="${INK}" stroke-width="1.7"/>`;
  const shoulders = `<path d="M64 118 Q70 88 100 84 Q130 88 136 118 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.7"/>`;
  const dark = 'rgba(58,52,64,.42)';
  if (kind === 'front') {
    return svg(head + shoulders + sun(100, 16) +
      `<path d="M100 30 L100 44" stroke="${TXT}" stroke-width="1.2" stroke-dasharray="3 2" marker-end="url(#arw)"/>` +
      txt('顺光 · 无影平铺（设定图光）', 38, 128));
  }
  if (kind === 'side') {
    return svg(sun(26, 56) + shoulders + head +
      `<path d="M100 30 A 26 26 0 0 1 100 82 Z" fill="${dark}"/>` +
      `<path d="M46 56 L62 56" stroke="${TXT}" stroke-width="1.2" stroke-dasharray="3 2" marker-end="url(#arw)"/>` +
      txt('侧光 · 半亮半暗，立体感最强', 44, 128));
  }
  if (kind === 'rembrandt') {
    return svg(sun(34, 26) + shoulders + head +
      `<path d="M100 30 A 26 26 0 0 1 100 82 Z" fill="${dark}"/>` +
      `<path d="M104 46 L120 58 L104 70 Z" fill="${FILL}"/>` +
      txt('伦勃朗光 · 颊部三角亮斑', 46, 128));
  }
  if (kind === 'back') {
    return svg(
      `<circle cx="100" cy="46" r="34" fill="none" stroke="#f0e2bc" stroke-width="7" opacity=".85"/>` +
      sun(100, 14) + shoulders +
      `<circle cx="100" cy="56" r="26" fill="#4a4238" stroke="${INK}" stroke-width="1.6"/>` +
      txt('逆光 · 剪影/发丝光', 56, 128));
  }
  if (kind === 'rim') {
    return svg(sun(150, 30) + shoulders +
      `<circle cx="100" cy="56" r="26" fill="#4a4238" stroke="${INK}" stroke-width="1.6"/>` +
      `<path d="M124 40 A 26 26 0 0 1 124 72" stroke="#f0e2bc" stroke-width="5" fill="none" opacity=".9"/>` +
      txt('轮廓光 · 勾边，从背景剥离', 44, 128));
  }
  if (kind === 'top') {
    return svg(sun(100, 14) + shoulders + head +
      `<rect x="76" y="50" width="48" height="9" fill="${dark}"/>` +
      `<path d="M100 30 L100 42" stroke="${TXT}" stroke-width="1.2" stroke-dasharray="3 2" marker-end="url(#arw)"/>` +
      txt('顶光 · 眼窝影（压抑/神秘）', 42, 128));
  }
  if (kind === 'bottom') {
    return svg(sun(30, 108) + shoulders + head +
      `<rect x="76" y="30" width="48" height="10" fill="${dark}"/>` +
      `<path d="M44 102 L78 84" stroke="${TXT}" stroke-width="1.2" stroke-dasharray="3 2" marker-end="url(#arw)"/>` +
      txt('底光 · 恐怖/诡异', 68, 26));
  }
  if (kind === 'butterfly') {
    return svg(sun(100, 12) + shoulders + head +
      `<path d="M95 62 Q100 72 105 62 Z" fill="${dark}"/>` +
      txt('蝴蝶光 · 鼻下小蝶影（美人光）', 38, 128));
  }
  if (kind === 'three') {
    return svg(
      sun(26, 34, '#e0a05c') + sun(174, 44, '#c9c2b4') + sun(100, 12, '#9db3c8') +
      shoulders + head +
      `<path d="M46 44 L72 52" stroke="${TXT}" stroke-width="1.2" stroke-dasharray="3 2" marker-end="url(#arw)"/>` +
      `<path d="M152 52 L130 58" stroke="${TXT}" stroke-width="1.2" stroke-dasharray="3 2" marker-end="url(#arw)"/>` +
      txt('主', 12, 58) + txt('补', 166, 66) + txt('轮', 88, 6) +
      txt('三点布光 · 主+补+轮廓', 48, 128));
  }
  if (kind === 'highkey') {
    return svg(
      `<rect x="30" y="14" width="140" height="100" fill="#fbf6ea" stroke="${GRID}" stroke-width="1.2"/>` +
      shoulders + head +
      `<ellipse cx="100" cy="112" rx="44" ry="7" fill="rgba(58,52,64,.12)"/>` +
      txt('高调 · 亮多暗少（清爽/温柔）', 40, 128));
  }
  if (kind === 'lowkey') {
    return svg(
      `<rect x="30" y="14" width="140" height="100" fill="rgba(38,34,44,.85)" stroke="${GRID}" stroke-width="1.2"/>` +
      `<path d="M64 118 Q70 88 100 84 Q130 88 136 118 Z" fill="#6b6156" stroke="${INK}" stroke-width="1.6"/>` +
      `<circle cx="100" cy="56" r="26" fill="#6b6156" stroke="${INK}" stroke-width="1.6"/>` +
      `<path d="M74 46 A 26 26 0 0 1 88 32" stroke="#f0e2bc" stroke-width="4" fill="none" opacity=".9"/>` +
      txt('低调 · 暗多亮少（压抑/电影感）', 38, 128));
  }
  if (kind === 'hardsoft') {
    return svg(
      `<circle cx="68" cy="56" r="24" fill="${FILL}" stroke="${INK}" stroke-width="1.7"/>` +
      `<path d="M68 32 A 24 24 0 0 1 68 80 Z" fill="${dark}"/>` +
      `<circle cx="138" cy="56" r="24" fill="url(#softshade)" stroke="${INK}" stroke-width="1.7"/>` +
      txt('硬光：影缘清晰', 36, 104) + txt('柔光：影缘羽化', 112, 104) +
      txt('影缘越软，人越柔和', 68, 124));
  }
  if (kind === 'volumetric') {
    return svg(
      `<rect x="34" y="18" width="14" height="90" fill="#fbf3dd" stroke="${GRID}" stroke-width="1.2"/>` +
      `<path d="M34 22 L58 22 L94 118 L64 118 Z" fill="#f2e8cd" opacity=".45"/>` +
      `<path d="M34 22 L58 22 L124 118 L94 118 Z" fill="#f2e8cd" opacity=".25"/>` +
      `<circle cx="84" cy="42" r="1.6" fill="${TXT}"/><circle cx="104" cy="58" r="1.4" fill="${TXT}"/><circle cx="96" cy="84" r="1.5" fill="${TXT}"/>` +
      figure(140, 70, 0.4, 1, '#4a4238', '#4a4238') +
      txt('体积光 · 光束穿过空气（丁达尔）', 38, 128));
  }
  if (kind === 'golden') {
    return svg(
      `<circle cx="158" cy="76" r="15" fill="#e8b06a" opacity=".55"/>` +
      `<ellipse cx="64" cy="112" rx="34" ry="6" fill="rgba(58,52,64,.3)"/>` +
      figure(84, 72, 0.5) +
      `<rect x="30" y="14" width="140" height="100" fill="#e8a94f" opacity=".12"/>` +
      txt('黄金时刻 · 低角度暖光+长影', 42, 128));
  }
  if (kind === 'blue') {
    return svg(
      `<circle cx="52" cy="34" r="8" fill="#c8d4e8" opacity=".5"/>` +
      figure(100, 72, 0.52) +
      `<rect x="30" y="14" width="140" height="100" fill="#5a6b8c" opacity=".28"/>` +
      txt('蓝调时刻 · 冷调余光', 62, 128));
  }
  if (kind === 'dapple') {
    return svg(shoulders + head +
      `<ellipse cx="88" cy="42" rx="10" ry="7" fill="#f7edcf" opacity=".7"/>` +
      `<ellipse cx="112" cy="58" rx="8" ry="6" fill="#f7edcf" opacity=".7"/>` +
      `<ellipse cx="92" cy="72" rx="9" ry="5" fill="#f7edcf" opacity=".65"/>` +
      `<ellipse cx="116" cy="96" rx="12" ry="5" fill="#f7edcf" opacity=".55"/>` +
      `<ellipse cx="70" cy="102" rx="10" ry="4" fill="#f7edcf" opacity=".55"/>` +
      txt('斑驳树影 · 叶隙光斑', 64, 128));
  }
  if (kind === 'blind') {
    return svg(
      `<path d="M42 20 L62 20 L42 118 L22 118 Z" fill="#f7edcf" opacity=".5"/>` +
      `<path d="M82 20 L102 20 L82 118 L62 118 Z" fill="#f7edcf" opacity=".5"/>` +
      `<path d="M122 20 L142 20 L122 118 L102 118 Z" fill="#f7edcf" opacity=".5"/>` +
      shoulders + head +
      txt('条纹光 · 百叶窗影', 68, 128));
  }
  if (kind === 'wet') {
    return svg(
      `<line x1="20" y1="96" x2="180" y2="96" stroke="${GRID}" stroke-width="1.2"/>` +
      figure(100, 68, 0.44) +
      `<path d="M64 100 L64 122 M84 100 L84 124 M116 100 L116 124 M136 100 L136 122" stroke="#f0e2bc" stroke-width="3" opacity=".55"/>` +
      txt('湿润地面反光（雨夜街）', 56, 128));
  }
  /* window */
  return svg(
    `<rect x="32" y="20" width="22" height="76" fill="#fbf3dd" stroke="${GRID}" stroke-width="1.4"/>` +
    `<path d="M54 30 L86 44 L86 96 L54 92 Z" fill="#f7edcf" opacity=".4"/>` +
    figure(112, 72, 0.5) +
    `<path d="M60 54 L92 58" stroke="${TXT}" stroke-width="1.2" stroke-dasharray="3 2" marker-end="url(#arw)"/>` +
    txt('窗光 · 单侧柔光（室内主力）', 42, 128));
}

/* ================= 8e. 姿态动作 ================= */
function poseSvg(kind: string): string {
  const L = (d: string, w = 4): string => `<path d="${d}" stroke="${INK}" stroke-width="${w}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
  const H = (x: number, y: number, r = 9): string => `<circle cx="${x}" cy="${y}" r="${r}" fill="${FILL}" stroke="${INK}" stroke-width="2"/>`;
  const G = (x1=30, x2=170, y=118) => `<line x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke="${GRID}" stroke-width="1.2"/>`;
  const A = (d: string): string => `<path d="${d}" stroke="${RED}" stroke-width="1.6" fill="none" stroke-dasharray="4 3" marker-end="url(#arw)"/>`;
  if (kind === 'stand') {
    return svg(H(100,28) + L('M100 37 L100 74',6) + L('M100 46 L90 70') + L('M100 46 L110 70') + L('M100 74 L92 116',5) + L('M100 74 L108 116',5) + G() +
      txt('重心居中 · 肩线水平 · 保形基准', 36, 127));
  }
  if (kind === 'contrapposto') {
    return svg(H(104,28) + L('M104 37 L98 74',6) + L('M104 47 L114 70') + L('M103 47 L93 66 L99 74') + L('M98 74 L100 116',5) + L('M98 74 L86 96 L90 116',5) + G() +
      txt('髋部偏移 · 微 S = 活人感', 52, 127));
  }
  if (kind === 'crossed') {
    return svg(H(100,28) + L('M100 37 L100 74',6) + L('M100 46 L88 52 L113 60') + L('M100 46 L112 52 L87 60') + L('M100 74 L92 116',5) + L('M100 74 L108 116',5) + G() +
      txt('防线感 · 双臂天然成三角', 48, 127));
  }
  if (kind === 'akimbo') {
    return svg(H(100,28) + L('M100 37 L100 74',6) + L('M100 46 L80 56 L89 72') + L('M100 46 L120 56 L111 72') + L('M100 74 L92 116',5) + L('M100 74 L108 116',5) + G() +
      txt('气势 · 手肘外扩占位', 54, 127));
  }
  if (kind === 'pocket') {
    return svg(H(100,28) + L('M100 37 L100 74',6) + L('M100 46 L112 60 L106 76') + L('M100 46 L90 70') + L('M100 74 L92 116',5) + L('M100 74 L108 116',5) + G() +
      txt('单手插兜 · 另手别空着', 54, 127));
  }
  if (kind === 'wall') {
    return svg(
      `<line x1="132" y1="16" x2="132" y2="118" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M132 26 L140 22 M132 44 L140 40 M132 62 L140 58" stroke="${GRID}" stroke-width="1"/>` +
      H(110,30) + L('M110 39 L118 76',6) + L('M110 48 L108 74') + L('M111 48 L116 72') + L('M118 76 L106 116',5) + L('M118 76 L122 112',5) + G(30,132) +
      txt('肩背贴墙 · 重心交给墙', 40, 127));
  }
  if (kind === 'lookback') {
    return svg(H(100,30) + `<path d="M108 26 L115 28 L108 31 Z" fill="${INK}" opacity=".6"/>` + A('M84 20 A 20 20 0 1 1 96 12') +
      L('M100 39 L100 76',6) + L('M100 48 L90 72') + L('M100 48 L110 72') + L('M100 76 L92 116',5) + L('M100 76 L108 116',5) + G() +
      txt('背影+半脸 · 回眸方向留白', 48, 127));
  }
  if (kind === 'walk') {
    return svg(H(102,30) + L('M102 39 L104 76',6) + L('M102 48 L92 62') + L('M102 48 L112 64') + L('M104 76 L116 98 L116 116',5) + L('M104 76 L90 98 L94 116',5) +
      `<path d="M64 56 L78 58 M60 66 L76 68" stroke="${GRID}" stroke-width="2" stroke-linecap="round"/>` + G() +
      txt('日常步态 · 重心微前', 60, 127));
  }
  if (kind === 'run') {
    return svg(H(112,34) + L('M112 43 L94 74',6) + L('M108 50 L124 56 L116 66') + L('M106 50 L90 62') + L('M94 74 L112 90 L114 108',5) + L('M94 74 L76 88 L70 104',5) +
      `<path d="M126 30 L140 26 M128 38 L142 36 M60 50 L74 52" stroke="${GRID}" stroke-width="2" stroke-linecap="round"/>` + G() +
      txt('前倾重心 · 对角四肢 · 发衣后摆', 40, 127));
  }
  if (kind === 'reach') {
    return svg(
      `<path d="M80 84 L68 50 M116 84 L128 50" stroke="${GRID}" stroke-width="1" stroke-dasharray="4 3"/>` +
      H(96,30,8) + L('M96 38 L98 52',5) + L('M96 42 L108 50') +
      L('M98 78 L94 50',5) +
      `<circle cx="100" cy="96" r="16" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M92 82 L90 76 M100 80 L100 74 M108 82 L110 76" stroke="${INK}" stroke-width="2" fill="none"/>` +
      txt('近大远小 · 手大身小', 62, 127));
  }
  if (kind === 'squat') {
    return svg(H(100,50) + L('M100 59 Q106 72 102 86',6) + L('M100 64 L84 78 L96 92') + L('M100 64 L116 78 L104 92') +
      L('M102 86 L80 82 L86 110',5) + L('M102 86 L122 82 L116 110',5) + G(40,160) +
      txt('收缩体态 · 防御/内敛', 62, 127));
  }
  if (kind === 'wariza') {
    return svg(H(100,40) + L('M100 49 L100 78',6) + L('M100 58 L88 74') + L('M100 58 L112 74') +
      L('M100 78 L72 90 L88 112',5) + L('M100 78 L128 90 L112 112',5) + G(30,170,114) +
      txt('二次元经典 · 裙摆最好展示', 48, 127));
  }
  if (kind === 'chair') {
    return svg(
      `<path d="M78 92 L126 92 M78 92 L78 58 M84 92 L84 118 M120 92 L120 118" stroke="${GRID}" stroke-width="3" fill="none" stroke-linecap="round"/>` +
      H(90,32) + L('M90 41 L90 88',6) + L('M90 88 L116 88',5) + L('M116 88 L116 116',5) + L('M90 50 L100 68 L110 84') + L('M90 50 L82 72') +
      txt('膝并拢 · 手放膝上', 60, 127));
  }
  if (kind === 'crossleg') {
    return svg(
      `<path d="M78 92 L126 92 M78 92 L78 58 M84 92 L84 118 M120 92 L120 118" stroke="${GRID}" stroke-width="3" fill="none" stroke-linecap="round"/>` +
      H(90,32) + L('M90 41 L90 88',6) + L('M90 88 L118 88',5) + L('M118 88 L100 108',5) + L('M90 88 L112 94 L110 116',5) + L('M90 50 L102 68 L112 82') +
      txt('翘腿 · 气场坐姿 · 注意交叠透视', 34, 127));
  }
  if (kind === 'kneel') {
    return svg(H(100,32) + L('M100 41 L100 76',6) + L('M100 51 L88 68') + L('M100 51 L112 68') +
      L('M100 76 L114 86 L114 116',5) + L('M100 76 L84 112',5) + L('M84 112 L104 114',5) + G() +
      txt('前脚掌撑地 · 后膝贴地', 52, 127));
  }
  if (kind === 'lying') {
    return svg(H(148,78) + L('M140 84 L92 92',6) + L('M144 86 L136 98 L148 108') + L('M136 88 L120 102') +
      L('M92 92 L60 98 L44 110',5) + L('M92 92 L62 104 L46 114',5) + G(30,170,112) +
      txt('慵懒侧躺 · 头枕手臂 · 双腿微曲', 36, 127));
  }
  if (kind === 'chin') {
    return svg(
      `<line x1="76" y1="92" x2="168" y2="92" stroke="${INK}" stroke-width="2.5"/>` +
      H(96,36) + L('M97 45 L93 88',6) + L('M96 56 L122 86') + L('M97 54 L112 86') + L('M112 86 L104 46') +
      txt('托腮 · 肘撑桌面 · 沉思/休息', 40, 127));
  }
  /* hair */
  return svg(H(100,28) + L('M100 37 L100 74',6) + L('M100 46 L116 40 L110 22') + L('M100 46 L90 70') + L('M100 74 L92 116',5) + L('M100 74 L108 116',5) + G() +
    A('M114 14 A 10 10 0 0 1 124 26') + txt('整理头发 · 手在头侧', 64, 127));
}

/* ================= 8f. 二人互动 ================= */
function pairSvg(kind: string): string {
  const L = (d: string, w = 4): string => `<path d="${d}" stroke="${INK}" stroke-width="${w}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
  const H = (x: number, y: number, r = 9): string => `<circle cx="${x}" cy="${y}" r="${r}" fill="${FILL}" stroke="${INK}" stroke-width="2"/>`;
  const G = (x1=30, x2=170, y=118) => `<line x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke="${GRID}" stroke-width="1.2"/>`;
  const A = (d: string): string => `<path d="${d}" stroke="${RED}" stroke-width="1.6" fill="none" stroke-dasharray="4 3" marker-end="url(#arw)"/>`;
  const DOT = (x: number, y: number): string => `<circle cx="${x}" cy="${y}" r="4" fill="${RED}" opacity=".8"/>`;
  if (kind === 'backtoback') {
    return svg(H(86,32) + L('M86 41 L86 80',6) + L('M86 50 L76 70') + L('M86 80 L80 116',5) + L('M86 80 L92 112',5) +
      H(114,32) + L('M114 41 L114 80',6) + L('M114 50 L124 70') + L('M114 80 L108 112',5) + L('M114 80 L120 116',5) +
      `<line x1="100" y1="38" x2="100" y2="92" stroke="${RED}" stroke-width="1.4" stroke-dasharray="4 3"/>` + G() +
      txt('背对背 · 互为支点', 64, 127));
  }
  if (kind === 'handhold') {
    return svg(H(72,30) + L('M72 39 L76 78',6) + L('M72 48 L96 66') + L('M76 78 L68 116',5) + L('M76 78 L84 116',5) +
      H(128,30) + L('M128 39 L124 78',6) + L('M128 48 L104 66') + L('M124 78 L116 116',5) + L('M124 78 L132 116',5) +
      DOT(100, 66) + G() +
      txt('牵手 · 连接点=手（崩坏高发，可剪影化）', 28, 127));
  }
  if (kind === 'sidebyside') {
    return svg(H(76,30) + L('M76 39 L80 76',6) + L('M76 48 L66 62') + L('M76 48 L86 60') + L('M80 76 L90 98 L90 116',5) + L('M80 76 L68 98 L72 116',5) +
      H(120,30) + L('M120 39 L124 76',6) + L('M120 48 L110 62') + L('M120 48 L130 60') + L('M124 76 L134 98 L134 116',5) + L('M124 76 L112 98 L116 116',5) +
      A('M138 58 L156 56') + G() +
      txt('并肩同行 · 同一方向 + lead room', 40, 127));
  }
  if (kind === 'facing') {
    return svg(H(70,32) + L('M70 41 L70 80',6) + L('M70 50 L82 64') + L('M70 80 L62 116',5) + L('M70 80 L78 116',5) +
      H(130,32) + L('M130 41 L130 80',6) + L('M130 50 L118 64') + L('M130 80 L122 116',5) + L('M130 80 L138 116',5) +
      `<path d="M84 98 L116 98" stroke="${RED}" stroke-width="1.3" stroke-dasharray="4 3"/><path d="M84 94 L84 102 M116 94 L116 102" stroke="${RED}" stroke-width="1.3"/>` + G() +
      txt('对峙 · 距离=关系 · 锁轴线', 52, 127));
  }
  if (kind === 'hug') {
    return svg(H(92,34) + H(112,30) + L('M92 43 L94 80',6) + L('M112 39 L110 80',6) +
      `<path d="M93 52 Q104 62 112 50" stroke="${INK}" stroke-width="4" fill="none" stroke-linecap="round"/>` +
      `<path d="M111 46 Q100 56 92 60" stroke="${INK}" stroke-width="4" fill="none" stroke-linecap="round"/>` +
      L('M94 80 L88 116',5) + L('M94 80 L100 112',5) + L('M110 80 L104 112',5) + L('M110 80 L116 116',5) + G() +
      txt('拥抱 · 写清谁的头在谁肩上', 56, 127));
  }
  if (kind === 'shoulder') {
    return svg(H(84,30) + L('M84 39 L84 80',6) + L('M84 48 L74 70') + L('M84 80 L76 116',5) + L('M84 80 L92 116',5) +
      H(112,34) + L('M112 43 L118 80',6) + L('M118 50 L128 68') + L('M118 80 L110 116',5) + L('M118 80 L126 116',5) +
      DOT(97, 43) + G() +
      txt('靠肩 · 亲密等级=头部接触点', 44, 127));
  }
  if (kind === 'height') {
    return svg(H(78,26) + L('M78 35 L78 80',6) + L('M78 44 L68 66') + L('M78 44 L88 66') + L('M78 80 L70 116',5) + L('M78 80 L86 116',5) +
      H(124,48) + L('M124 57 L124 84',6) + L('M124 66 L114 78') + L('M124 66 L134 78') + L('M124 84 L116 116',5) + L('M124 84 L132 116',5) +
      `<path d="M150 26 L150 48" stroke="${RED}" stroke-width="1.3"/><path d="M146 26 L154 26 M146 48 L154 48" stroke="${RED}" stroke-width="1.3"/>` + G() +
      txt('身高差 · 下巴对头顶 · 写清差值', 40, 127));
  }
  if (kind === 'princess') {
    return svg(H(84,30) + L('M84 39 L86 82',6) + L('M84 50 L98 60') + L('M86 82 L78 116',5) + L('M86 82 L94 116',5) +
      H(58,52,8) + L('M66 55 L100 52',6) + L('M100 52 L112 62',5) + L('M100 52 L110 46',5) +
      DOT(98, 60) + G() +
      txt('公主抱 · 手臂闭环承托（结构复杂预警）', 28, 127));
  }
  if (kind === 'piggyback') {
    return svg(H(90,34) + L('M90 43 L98 78',6) + L('M90 52 L82 70') + L('M98 78 L90 116',5) + L('M98 78 L106 116',5) +
      H(116,26) + L('M116 35 L114 48',5) +
      `<path d="M112 40 L94 48" stroke="${INK}" stroke-width="4" fill="none" stroke-linecap="round"/>` +
      `<path d="M118 40 L100 52" stroke="${INK}" stroke-width="4" fill="none" stroke-linecap="round"/>` +
      `<path d="M113 52 L96 62 L102 74" stroke="${INK}" stroke-width="4" fill="none" stroke-linecap="round"/>` +
      `<path d="M115 54 L100 66 L108 76" stroke="${INK}" stroke-width="4" fill="none" stroke-linecap="round"/>` + G() +
      txt('背负 · 腿环腰 + 手搭肩（复杂预警）', 36, 127));
  }
  /* foreback 前后站位 */
  return svg(
    `<circle cx="66" cy="84" r="15" fill="#4a4238" opacity=".8" stroke="${INK}" stroke-width="1.6"/>` +
    `<path d="M38 130 Q52 112 66 110 Q80 112 94 130 Z" fill="#4a4238" opacity=".8" stroke="${INK}" stroke-width="1.6"/>` +
    H(124,44) + L('M124 53 L124 84',6) + L('M124 62 L114 80') + L('M124 62 L134 80') + L('M124 84 L116 116',5) + L('M124 84 L132 116',5) + G() +
    txt('前后站位 · 前景虚化=层次', 44, 127));
}

/* ================= 8g. 神态表情 ================= */
function exprSvg(kind: string): string {
  const ST = (d: string, w = 2.5, c: string = INK): string => `<path d="${d}" stroke="${c}" stroke-width="${w}" fill="none" stroke-linecap="round"/>`;
  const face = `<circle cx="100" cy="62" r="33" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
    ST('M72 48 Q84 31 100 30 Q116 31 128 48', 2) +
    ST('M82 39 L90 47 M94 35 L100 45 M106 35 L112 45 M118 39 L110 47', 1.6);
  const eyes = `<ellipse cx="86" cy="58" rx="5" ry="6" fill="${INK}"/><ellipse cx="114" cy="58" rx="5" ry="6" fill="${INK}"/>` +
    `<circle cx="84" cy="56" r="1.6" fill="#fff"/><circle cx="112" cy="56" r="1.6" fill="#fff"/>`;
  if (kind === 'blank') {
    return svg(face + eyes + ST('M79 49 L93 49', 2, TXT) + ST('M107 49 L121 49', 2, TXT) + ST('M90 82 L110 82') +
      txt('无表情 · 冷淡基底（远景也读得出）', 34, 127));
  }
  if (kind === 'smile') {
    return svg(face + eyes + ST('M79 49 L93 49', 2, TXT) + ST('M107 49 L121 49', 2, TXT) + ST('M90 82 Q100 89 110 82') +
      txt('微笑 · 嘴角最小改动量', 58, 127));
  }
  if (kind === 'grin') {
    return svg(face + eyes +
      `<path d="M88 80 Q100 93 112 80 Z" fill="#6b5454"/>` + ST('M90 81.5 L110 81.5', 2, '#fff') +
      txt('露齿笑 · 开口形 + 白齿一横', 54, 127));
  }
  if (kind === 'laugh') {
    return svg(face + ST('M79 60 Q86 53 93 60') + ST('M107 60 Q114 53 121 60') +
      `<ellipse cx="100" cy="84" rx="9" ry="7" fill="#6b5454"/>` + `<path d="M94 87 Q100 92 106 87 Z" fill="#c98a8a"/>` +
      txt('大笑 · 眯眼(∩) + 大开口', 62, 127));
  }
  if (kind === 'jitome') {
    return svg(face + ST('M79 58 L93 58', 2.5) + ST('M107 58 L121 58', 2.5) +
      `<circle cx="86" cy="61.5" r="2.5" fill="${INK}"/><circle cx="114" cy="61.5" r="2.5" fill="${INK}"/>` +
      ST('M90 82 L110 82') +
      txt('半眯眼 jitome · 冷淡/嫌弃（booru 50K）', 32, 127));
  }
  if (kind === 'angry') {
    return svg(face + ST('M77 47 L93 53') + ST('M123 47 L107 53') +
      `<ellipse cx="86" cy="59" rx="4.5" ry="5" fill="${INK}"/><ellipse cx="114" cy="59" rx="4.5" ry="5" fill="${INK}"/>` +
      `<circle cx="84" cy="57" r="1.4" fill="#fff"/><circle cx="112" cy="57" r="1.4" fill="#fff"/>` +
      ST('M90 86 Q100 80 110 86') +
      txt('生气 · 眉向内下压是灵魂', 56, 127));
  }
  if (kind === 'pout') {
    return svg(face + eyes + ST('M94 84 Q100 79 106 84') +
      txt('嘟嘴 · 小 ∧ 嘴（傲娇标配）', 58, 127));
  }
  if (kind === 'surprise') {
    return svg(face + ST('M77 45 Q86 41 94 45') + ST('M106 45 Q114 41 123 45') +
      `<ellipse cx="86" cy="58" rx="6" ry="7" fill="${INK}"/><ellipse cx="114" cy="58" rx="6" ry="7" fill="${INK}"/>` +
      `<circle cx="84" cy="55" r="1.8" fill="#fff"/><circle cx="112" cy="55" r="1.8" fill="#fff"/>` +
      `<ellipse cx="100" cy="84" rx="5" ry="6.5" fill="#6b5454"/>` +
      txt('惊讶 · 瞪圆眼 + 抬眉 + O 嘴', 54, 127));
  }
  if (kind === 'blush') {
    return svg(face +
      `<ellipse cx="76" cy="72" rx="8" ry="4.5" fill="#c98a8a" opacity=".45"/><ellipse cx="124" cy="72" rx="8" ry="4.5" fill="#c98a8a" opacity=".45"/>` +
      `<ellipse cx="83" cy="58" rx="5" ry="6" fill="${INK}"/><ellipse cx="113" cy="58" rx="5" ry="6" fill="${INK}"/>` +
      `<circle cx="81" cy="56" r="1.6" fill="#fff"/><circle cx="111" cy="56" r="1.6" fill="#fff"/>` +
      ST('M94 83 Q100 86 106 83') +
      txt('害羞 · 腮红块 + 视线躲闪', 60, 127));
  }
  if (kind === 'teary') {
    return svg(face +
      `<ellipse cx="86" cy="58" rx="6" ry="6.5" fill="${INK}"/><ellipse cx="114" cy="58" rx="6" ry="6.5" fill="${INK}"/>` +
      `<circle cx="84" cy="55" r="2.2" fill="#fff"/><circle cx="112" cy="55" r="2.2" fill="#fff"/>` +
      ST('M79 64 Q86 68 93 64', 2, '#9db3c8') + ST('M107 64 Q114 68 121 64', 2, '#9db3c8') +
      ST('M92 83 Q96 80 100 83 Q104 86 108 83') +
      txt('眼含泪 · 泪池线 + 大高光', 62, 127));
  }
  if (kind === 'cry') {
    return svg(face + ST('M79 60 Q86 66 93 60') + ST('M107 60 Q114 66 121 60') +
      `<path d="M84 63 L82 86 M116 63 L118 86" stroke="#9db3c8" stroke-width="2.5" opacity=".85"/>` +
      `<ellipse cx="100" cy="84" rx="6" ry="5.5" fill="#6b5454"/>` +
      txt('哭泣 · 泪流线 + 张开的嘴', 60, 127));
  }
  if (kind === 'smug') {
    return svg(face + ST('M106 44 Q114 41 122 46') + ST('M78 49 L92 49', 2, TXT) +
      ST('M79 58 L93 58', 2.5) + ST('M107 58 L121 58', 2.5) +
      `<circle cx="86" cy="61.5" r="2.5" fill="${INK}"/><circle cx="114" cy="61.5" r="2.5" fill="${INK}"/>` +
      ST('M92 82 Q100 87 110 79') +
      txt('得意坏笑 · 半眯眼 + 单边挑眉 + 斜嘴', 30, 127));
  }
  if (kind === 'lookdown') {
    return svg(face + ST('M79 57 L93 57', 2.5) + ST('M107 57 L121 57', 2.5) +
      `<circle cx="86" cy="62" r="2.5" fill="${INK}"/><circle cx="114" cy="62" r="2.5" fill="${INK}"/>` +
      ST('M91 85 Q100 82 109 85') +
      txt('睥睨 · 瞳孔下移 + 半帘（配高机位更狠）', 28, 127));
  }
  if (kind === 'glare') {
    return svg(face + ST('M77 47 L93 53') + ST('M123 47 L107 53') +
      `<ellipse cx="86" cy="58" rx="5.5" ry="6.5" fill="${INK}"/><ellipse cx="114" cy="58" rx="5.5" ry="6.5" fill="${INK}"/>` +
      `<circle cx="85" cy="55" r="1.8" fill="#fff"/><circle cx="113" cy="55" r="1.8" fill="#fff"/>` +
      ST('M92 83 L108 83', 3) +
      txt('瞪视 · 收瞳 + 压眉 + 紧嘴（对峙眼）', 34, 127));
  }
  if (kind === 'wink') {
    return svg(face + `<ellipse cx="86" cy="58" rx="5" ry="6" fill="${INK}"/><circle cx="84" cy="56" r="1.6" fill="#fff"/>` +
      ST('M107 59 Q114 53 121 59') + ST('M92 82 Q100 87 108 82') +
      txt('眨眼 · 单眼闭弧 + 小笑', 62, 127));
  }
  if (kind === 'sweat') {
    return svg(face + ST('M79 58 L93 58', 2.5) + ST('M107 58 L121 58', 2.5) +
      `<circle cx="86" cy="61.5" r="2.5" fill="${INK}"/><circle cx="114" cy="61.5" r="2.5" fill="${INK}"/>` +
      ST('M90 82 L110 82') +
      `<path d="M138 28 Q145 40 138 45 Q131 40 138 28 Z" fill="#9db3c8" opacity=".85"/>` +
      txt('汗滴 · 无语/尴尬（booru 329K 符号）', 32, 127));
  }
  if (kind === 'grit') {
    return svg(face + ST('M77 47 L93 53') + ST('M123 47 L107 53') +
      `<ellipse cx="86" cy="59" rx="4.5" ry="5" fill="${INK}"/><ellipse cx="114" cy="59" rx="4.5" ry="5" fill="${INK}"/>` +
      `<rect x="88" y="78" width="24" height="9" rx="2" fill="#fff" stroke="${INK}" stroke-width="1.6"/>` +
      ST('M96 78 L96 87', 1.2) + ST('M104 78 L104 87', 1.2) +
      txt('咬牙切齿 · 牙格 + 压眉', 58, 127));
  }
  /* closed serene */
  return svg(face + ST('M79 60 Q86 54 93 60') + ST('M107 60 Q114 54 121 60') + ST('M92 82 Q100 88 108 82') +
    txt('闭眼 · 平静/享受/回忆', 62, 127));
}

/* ================= 8h. 人物细节 ================= */
function detailSvg(kind: string): string {
  if (kind === 'hairhigh') {
    return svg(
      `<path d="M60 18 Q88 60 74 112 M74 18 Q100 60 88 112 M88 18 Q112 60 102 112" stroke="${INK}" stroke-width="3" fill="none"/>` +
      `<path d="M70 30 Q92 60 82 100" stroke="#f7edcf" stroke-width="6" opacity=".9"/>` +
      `<path d="M124 40 L136 40 M130 34 L130 46" stroke="${RED}" stroke-width="2"/>` +
      txt('发丝高光 · 一条亮带扫过发束', 38, 127));
  }
  if (kind === 'windhair') {
    return svg(
      `<circle cx="56" cy="64" r="20" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M72 50 Q120 36 160 44 M74 62 Q124 54 166 58 M76 74 Q120 72 156 80 M72 86 Q110 88 140 96" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      `<path d="M28 34 L46 36 M28 46 L44 48" stroke="${GRID}" stroke-width="2" stroke-linecap="round"/>` +
      txt('风动发 · 发丝方向一致才可信', 48, 127));
  }
  if (kind === 'wethair') {
    return svg(
      `<path d="M70 24 Q60 64 70 106" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<path d="M70 24 Q86 30 84 52 Q82 70 76 84" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      `<path d="M70 24 Q92 34 96 58" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      `<path d="M78 40 Q82 52 78 64" stroke="#f7edcf" stroke-width="3" opacity=".8"/>` +
      `<path d="M84 88 Q87 93 84 95 Q81 93 84 88 Z" fill="#9db3c8" opacity=".8"/>` +
      `<path d="M96 64 Q99 69 96 71 Q93 69 96 64 Z" fill="#9db3c8" opacity=".8"/>` +
      txt('湿发 · 贴脸束 + 水珠 + 高光', 52, 127));
  }
  if (kind === 'ahoge') {
    return svg(
      `<circle cx="100" cy="68" r="26" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M78 52 Q90 38 100 40 Q112 42 122 52" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<path d="M100 42 Q96 16 112 12 Q126 9 120 22" stroke="${INK}" stroke-width="3" fill="none"/>` +
      `<circle cx="120" cy="22" r="2.5" fill="${RED}"/>` +
      txt('呆毛 · 最便宜的「活」细节（ahoge）', 40, 127));
  }
  if (kind === 'lashes') {
    return svg(
      `<path d="M56 70 Q100 34 144 70" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      `<path d="M56 70 Q100 92 144 70" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<ellipse cx="100" cy="66" rx="15" ry="17" fill="${INK}"/>` +
      `<circle cx="94" cy="58" r="4" fill="#fff"/>` +
      `<path d="M52 68 L44 62 M60 58 L54 50 M72 50 L68 41 M86 44 L84 34 M114 44 L116 34 M128 50 L132 41 M140 58 L146 50 M148 68 L156 62" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      txt('睫毛 · 上浓下疏 · 眼尾加长提神', 48, 127));
  }
  if (kind === 'catchlight') {
    return svg(
      `<ellipse cx="100" cy="64" rx="24" ry="21" fill="${INK}"/>` +
      `<circle cx="100" cy="64" r="14" fill="none" stroke="#7a8fa8" stroke-width="2"/>` +
      `<circle cx="92" cy="55" r="6" fill="#fff"/>` +
      `<circle cx="109" cy="71" r="2.5" fill="#fff" opacity=".8"/>` +
      `<path d="M138 40 L150 40 M144 34 L144 46" stroke="${RED}" stroke-width="2"/>` +
      txt('瞳孔高光 · 大点=有生气 · 缺口=冷淡（shiny eyes）', 26, 127));
  }
  if (kind === 'eyemakeup') {
    return svg(
      `<path d="M56 72 Q100 40 144 72" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      `<path d="M60 64 Q100 32 140 64 Q100 48 60 64 Z" fill="#c98a8a" opacity=".35"/>` +
      `<path d="M144 70 L162 62 L148 78 Z" fill="${INK}"/>` +
      `<ellipse cx="100" cy="68" rx="14" ry="16" fill="${INK}"/>` +
      `<circle cx="95" cy="61" r="3.5" fill="#fff"/>` +
      txt('眼妆 · 眼线尾 + 眼影渐层（成人/编辑感）', 34, 127));
  }
  if (kind === 'fang') {
    return svg(
      `<path d="M62 58 Q100 104 138 58 Z" fill="#6b5454"/>` +
      `<path d="M68 62 L132 62" stroke="#fff" stroke-width="3"/>` +
      `<path d="M84 62 L92 78 L100 62 Z" fill="#fff"/>` +
      `<path d="M110 62 L118 74 L126 62 Z" fill="#fff"/>` +
      txt('虎牙 · 白齿三角（元气/小恶魔）', 56, 127));
  }
  if (kind === 'collarbone') {
    return svg(
      `<path d="M80 26 L80 56 M120 26 L120 56" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M80 56 Q60 66 40 62 M120 56 Q140 66 160 62" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      `<path d="M84 60 Q100 70 116 60" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<path d="M88 66 Q100 74 112 66" stroke="${TXT}" stroke-width="1.6" fill="none"/>` +
      `<circle cx="100" cy="58" r="2.5" fill="${RED}" opacity=".7"/>` +
      txt('锁骨 · 颈肩交界的三条线', 58, 127));
  }
  if (kind === 'nape') {
    return svg(
      `<circle cx="100" cy="46" r="30" fill="${INK}" opacity=".85"/>` +
      `<path d="M100 76 L100 96" stroke="${INK}" stroke-width="2.5"/>` +
      `<path d="M84 78 Q100 88 116 78" stroke="${TXT}" stroke-width="2" fill="none"/>` +
      `<circle cx="100" cy="82" r="3" fill="${RED}" opacity=".7"/>` +
      txt('后颈 · 发际线下的一小段（nape）', 48, 127));
  }
  if (kind === 'sweat') {
    return svg(
      `<path d="M50 40 Q100 70 150 40" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<ellipse cx="80" cy="52" rx="4" ry="6" fill="#9db3c8" opacity=".85"/><circle cx="79" cy="50" r="1.2" fill="#fff"/>` +
      `<ellipse cx="100" cy="58" rx="4" ry="6" fill="#9db3c8" opacity=".85"/><circle cx="99" cy="56" r="1.2" fill="#fff"/>` +
      `<ellipse cx="120" cy="52" rx="4" ry="6" fill="#9db3c8" opacity=".85"/><circle cx="119" cy="50" r="1.2" fill="#fff"/>` +
      `<path d="M120 62 L122 84" stroke="#9db3c8" stroke-width="2" opacity=".6"/>` +
      txt('汗珠 · 圆珠+高光点+下滑痕', 56, 127));
  }
  if (kind === 'hands') {
    return svg(
      `<path d="M66 108 Q60 80 70 62 L74 44 Q76 38 82 40 L84 60 L86 34 Q88 28 94 30 L96 58 L98 32 Q100 26 106 28 L108 56 L110 40 Q112 34 118 38 L118 66 Q122 92 108 108 Z" fill="${FILL}" stroke="${INK}" stroke-width="2" stroke-linejoin="round"/>` +
      `<path d="M80 54 L86 56 M92 52 L98 54 M104 50 L110 52" stroke="${TXT}" stroke-width="1.4"/>` +
      `<path d="M70 62 Q56 60 60 48" stroke="${INK}" stroke-width="2" fill="none"/>` +
      txt('手部结构 · 指节分层（hand focus）', 48, 127));
  }
  if (kind === 'zettai') {
    return svg(
      `<path d="M62 30 L138 30 L150 58 L50 58 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M74 58 L72 96 M88 58 L88 96 M112 58 L112 96 M126 58 L128 96" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<path d="M66 96 Q100 100 134 96" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<path d="M156 58 L156 96" stroke="${RED}" stroke-width="1.5"/><path d="M152 58 L160 58 M152 96 L160 96" stroke="${RED}" stroke-width="1.5"/>` +
      txt('绝对领域 · 裙摆到袜口的一段（170K）', 36, 127));
  }
  if (kind === 'clothmotion') {
    return svg(
      `<path d="M70 26 L130 26 L146 74 Q118 60 100 74 Q82 60 54 74 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M54 74 Q70 90 62 108 M100 74 Q108 92 96 110 M146 74 Q138 94 144 108" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<path d="M36 40 L52 44 M34 54 L50 58" stroke="${GRID}" stroke-width="2" stroke-linecap="round"/>` +
      txt('衣物飘动 · 高光+褶皱同步变形（floating clothes）', 22, 127));
  }
  if (kind === 'folds') {
    return svg(
      `<path d="M40 30 L160 30 L160 106 L40 106 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.8"/>` +
      `<circle cx="120" cy="46" r="4" fill="${RED}" opacity=".7"/>` +
      `<path d="M120 46 Q104 62 96 102 M120 46 Q112 70 116 104 M120 46 Q128 68 126 100 M120 46 Q138 62 146 96" stroke="${TXT}" stroke-width="1.6" fill="none"/>` +
      txt('布料褶皱 · 一切褶子指向受力点', 48, 127));
  }
  if (kind === 'hairflow') {
    return svg(
      `<path d="M70 20 Q60 60 66 104 M84 16 Q76 60 84 106 M100 14 Q96 62 102 108 M116 16 Q122 60 118 106 M130 20 Q140 62 134 104" stroke="${INK}" stroke-width="2.6" fill="none"/>` +
      `<path d="M66 104 Q84 112 102 108 Q118 106 134 104" stroke="${INK}" stroke-width="2.2" fill="none"/>` +
      `<path d="M78 30 Q90 60 86 92" stroke="#f7edcf" stroke-width="5" opacity=".85"/>` +
      txt('长发发流 · 流向一致 + 发尾收弧', 44, 127));
  }
  if (kind === 'hairacc') {
    return svg(
      `<circle cx="100" cy="62" r="28" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M74 46 Q88 30 100 30 Q114 30 126 46" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<path d="M70 40 L86 52 M86 40 L70 52" stroke="${RED}" stroke-width="3" stroke-linecap="round"/>` +
      `<path d="M120 30 L132 22 L132 38 Z M120 30 L110 22 L110 38 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.8"/>` +
      `<circle cx="120" cy="30" r="3" fill="${INK}"/>` +
      txt('发饰 · 发夹/缎带/发箍是女生第一配件', 40, 127));
  }
  if (kind === 'legline') {
    return svg(
      `<path d="M84 20 Q80 52 88 70 Q82 88 86 108" stroke="${INK}" stroke-width="2.4" fill="none"/>` +
      `<path d="M112 20 Q114 52 108 70 Q114 88 110 108" stroke="${INK}" stroke-width="2.4" fill="none"/>` +
      `<path d="M80 76 Q100 82 116 76" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<path d="M86 44 Q100 50 108 44" stroke="${TXT}" stroke-width="1.6" fill="none"/>` +
      `<circle cx="100" cy="70" r="2.5" fill="${TXT}"/>` +
      txt('腿型与袜 · 膝点 + 袜口压痕 + 袜口弧', 40, 127));
  }
  if (kind === 'nails') {
    return svg(
      `<path d="M60 96 Q58 60 66 44 Q72 34 84 40 L90 108 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M92 104 L94 34 Q96 26 106 30 L108 104 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M112 104 L112 44 Q114 36 124 40 L126 102 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M64 52 Q72 44 82 48" stroke="${RED}" stroke-width="2.2" fill="none"/>` +
      `<path d="M94 42 Q100 34 108 40" stroke="${RED}" stroke-width="2.2" fill="none"/>` +
      `<path d="M112 52 Q120 44 128 50" stroke="${RED}" stroke-width="2.2" fill="none"/>` +
      txt('指尖与指甲 · 甲面窄弧 + 甲缘线', 48, 127));
  }
  /* barefoot */
  return svg(
    `<path d="M66 60 L70 96 M94 60 L88 96" stroke="${INK}" stroke-width="2" fill="none"/>` +
    `<path d="M60 96 L78 96 Q92 96 104 88 L136 74 Q148 70 152 78 Q154 86 142 90 L104 102 Q88 108 72 108 L60 108 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
    `<path d="M148 78 Q154 76 156 82 M140 82 Q146 80 148 86" stroke="${INK}" stroke-width="1.6" fill="none"/>` +
    `<path d="M72 106 Q100 94 136 86" stroke="${TXT}" stroke-width="1.4" fill="none"/>` +
    `<circle cx="82" cy="88" r="2.5" fill="${TXT}"/>` +
    txt('裸足 · 脚踝骨点 + 足弓线 + 落地影', 42, 127));
}

/* ================= 8i. 体型体态 ================= */
function bodySvg(kind: string): string {
  const L = (d: string, w = 4): string => `<path d="${d}" stroke="${INK}" stroke-width="${w}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
  const H = (x: number, y: number, r = 9): string => `<circle cx="${x}" cy="${y}" r="${r}" fill="${FILL}" stroke="${INK}" stroke-width="2"/>`;
  const G = `<line x1="30" y1="118" x2="170" y2="118" stroke="${GRID}" stroke-width="1.2"/>`;
  const M = (d: string, w = 1.3): string => `<path d="${d}" stroke="${RED}" stroke-width="${w}" fill="none"/>`;
  if (kind === 'headratio') {
    let ticks = '';
    for (let i = 0; i <= 7; i++) { const y = 18 + i * 14; ticks += `<path d="M144 ${y} L152 ${y}" stroke="${RED}" stroke-width="1.3"/>`; }
    return svg(H(100,26,8) + L('M100 34 L100 72',5) + L('M100 44 L90 66') + L('M100 44 L110 66') +
      L('M100 72 L92 116',4.5) + L('M100 72 L108 116',4.5) + G +
      M('M148 18 L148 116') + ticks +
      txt('头身比 · 少女 6.5-7 头身（fx=7）', 36, 127));
  }
  if (kind === 'legratio') {
    return svg(H(100,26,8) + L('M100 34 L100 68',5) + L('M100 44 L90 64') + L('M100 44 L110 64') +
      L('M100 68 L90 116',4.5) + L('M100 68 L110 116',4.5) + G +
      M('M62 68 L138 68', 1.3) + `<path d="M62 68 L138 68" stroke="${RED}" stroke-width="1.3" stroke-dasharray="4 3"/>` +
      M('M56 18 L56 68') + M('M52 18 L60 18') + M('M52 68 L60 68') +
      M('M56 68 L56 116') + M('M52 116 L60 116') +
      txt('腿身比 · 45-55% = 长腿感来源', 44, 127));
  }
  if (kind === 'shoulderw') {
    return svg(H(100,30,12) + L('M100 42 L100 54',5) +
      `<path d="M76 56 Q100 48 124 56" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      `<path d="M88 18 L88 42 M112 18 L112 42" stroke="${TXT}" stroke-width="1.3" stroke-dasharray="3 2"/>` +
      M('M76 62 L124 62') + M('M76 58 L76 66') + M('M124 58 L124 66') +
      txt('肩宽 ≈ 2 头宽 · 窄肩显轻（fx 削肩）', 38, 127));
  }
  if (kind === 'waisthip') {
    return svg(
      `<path d="M80 36 Q100 30 120 36 L112 66 Q100 70 88 66 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M88 66 Q74 84 78 104 Q100 110 122 104 Q126 84 112 66" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<circle cx="100" cy="66" r="2.5" fill="${RED}"/>` +
      txt('腰胯比 · 曲线=亲和 · 直线=疏离', 48, 127));
  }
  if (kind === 'armratio') {
    return svg(H(100,26,8) + L('M100 34 L100 70',5) + L('M100 44 L88 78 L86 92',4) + L('M100 44 L112 64') +
      L('M100 70 L92 116',4.5) + L('M100 70 L108 116',4.5) + G +
      `<path d="M28 92 L86 92" stroke="${RED}" stroke-width="1.3" stroke-dasharray="4 3"/>` +
      txt('手臂比例 · 指尖垂至大腿中', 48, 127));
  }
  if (kind === 'slim') {
    return svg(H(100,26,8) + L('M100 34 L100 72',4.5) + L('M100 44 L92 68') + L('M100 44 L108 68') +
      L('M100 72 L94 116',4) + L('M100 72 L106 116',4) + G +
      txt('纤细型 · 直线剪影 · 疏离气质首选', 40, 127));
  }
  if (kind === 'curvy') {
    return svg(H(100,28,8) + L('M100 36 L100 70',5) +
      `<path d="M92 40 Q84 52 90 62 M108 40 Q116 52 110 62" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<path d="M90 62 Q76 82 82 104 Q100 112 118 104 Q124 82 110 62" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` + G +
      txt('丰满型 · 圆线剪影 · 亲和成熟', 52, 127));
  }
  if (kind === 'tall') {
    let ticks = '';
    for (let i = 0; i <= 8; i++) { const y = 14 + i * 12.5; ticks += `<path d="M144 ${y} L151 ${y}" stroke="${RED}" stroke-width="1.2"/>`; }
    return svg(H(100,24,7.5) + L('M100 32 L100 62',5) + L('M100 40 L91 60') + L('M100 40 L109 60') +
      L('M100 62 L92 116',4.5) + L('M100 62 L108 116',4.5) + G +
      M('M147 14 L147 114') + ticks +
      txt('高挑型 · 8 头身 + 高腿长占比', 48, 127));
  }
  if (kind === 'petite') {
    let ticks = '';
    for (let i = 0; i <= 6; i++) { const y = 40 + i * 12.5; ticks += `<path d="M144 ${y} L151 ${y}" stroke="${RED}" stroke-width="1.2"/>`; }
    return svg(H(100,48,9) + L('M100 57 L100 84',5) + L('M100 65 L90 82') + L('M100 65 L110 82') +
      L('M100 84 L92 116',4.5) + L('M100 84 L108 116',4.5) + G +
      M('M147 40 L147 114') + ticks +
      txt('娇小型 · 约 6 头身 · 头大身短', 52, 127));
  }
  if (kind === 'slope') {
    return svg(H(100,34,10) + `<path d="M100 46 L100 60" stroke="${INK}" stroke-width="2.5"/>` +
      `<path d="M100 58 Q78 64 64 72 M100 58 Q122 64 136 72" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      `<path d="M64 72 L64 96 M136 72 L136 96" stroke="${INK}" stroke-width="2.2" fill="none"/>` +
      `<path d="M66 70 L134 70" stroke="${RED}" stroke-width="1.2" stroke-dasharray="4 3"/>` +
      txt('削肩 · 肩线向下滑（fx 保形项）', 48, 127));
  }
  if (kind === 'square') {
    return svg(H(100,34,10) + `<path d="M100 46 L100 58" stroke="${INK}" stroke-width="2.5"/>` +
      `<path d="M100 56 L64 52 M100 56 L136 52" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      `<path d="M64 52 L64 96 M136 52 L136 96" stroke="${INK}" stroke-width="2.2" fill="none"/>` +
      `<path d="M64 50 L134 50" stroke="${RED}" stroke-width="1.2" stroke-dasharray="4 3"/>` +
      txt('直角肩 · 肩线水平外扩 · 气场强', 48, 127));
  }
  if (kind === 'upright') {
    return svg(H(100,26,8) +
      M('M100 14 L100 116', 1.3) + `<path d="M100 14 L100 116" stroke="${RED}" stroke-width="1.3" stroke-dasharray="5 4"/>` +
      L('M100 34 L100 72',5) + L('M100 44 L90 66') + L('M100 44 L110 66') +
      L('M100 72 L92 116',4.5) + L('M100 72 L108 116',4.5) + G +
      txt('挺拔 · 耳-肩-髋压一条垂线', 52, 127));
  }
  if (kind === 'slouch') {
    return svg(H(100,30,8) + L('M100 38 Q96 54 104 72',5) + L('M101 46 L92 66') + L('M102 46 L112 64') +
      L('M104 72 L96 116',4.5) + L('M104 72 L112 116',4.5) + G +
      `<path d="M108 18 Q92 50 96 116" stroke="${RED}" stroke-width="1.3" stroke-dasharray="5 4" fill="none"/>` +
      txt('含胸弓背 · 脊柱 C 形 · 内向/疲惫', 44, 127));
  }
  if (kind === 'agetier') {
    const f = (cx: number, cy: number, hr: number, sh: number, ax: number): string =>
      H(cx, cy, hr) +
      L(`M${cx} ${cy + hr} L${cx} 92`, 5) +
      L(`M${cx} ${cy + hr + 8} L${cx - sh} 88`, 3.5) + L(`M${cx} ${cy + hr + 8} L${cx + sh} 88`, 3.5) +
      L(`M${cx} 92 L${cx - 6} 118`, 4) + L(`M${cx} 92 L${cx + 6} 118`, 4) +
      `<path d="M${ax} ${cy - hr} L${ax + 6} ${cy - hr} M${ax} ${cy + hr} L${ax + 6} ${cy + hr}" stroke="${RED}" stroke-width="1.2"/>`;
    return svg(f(48, 50, 9.5, 10, 30) + f(100, 46, 8.5, 9, 82) + f(152, 43, 7.5, 8, 134) + G +
      txt('JS 5~5.5头', 22, 127) + txt('小柄≈6头', 80, 127) + txt('JK 6.5~7头', 134, 127));
  }
  if (kind === 'ageface') {
    const face = (cx: number, cy: number, rx: number, ry: number): string => `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="${FILL}" stroke="${INK}" stroke-width="2"/>`;
    const eyes = (cx: number, cy: number, dx: number, w: number, h: number): string => {
      const one = (sx: number): string => `<ellipse cx="${sx}" cy="${cy}" rx="${w}" ry="${h}" fill="#fff" stroke="${INK}" stroke-width="1.4"/>` +
        `<circle cx="${sx}" cy="${cy}" r="${Math.max(1.6, h * 0.55)}" fill="${INK}"/>`;
      return one(cx - dx) + one(cx + dx);
    };
    return svg(
      face(52, 50, 17, 15.5) + eyes(52, 50, 7.5, 5.4, 5.4) + `<circle cx="52" cy="63" r="1.3" fill="${TXT}"/>` +
      face(100, 48, 14, 16) + eyes(100, 48, 6.5, 5, 4.2) +
      face(148, 47, 12, 16.5) + eyes(148, 47, 5.5, 4.4, 3.1) +
      txt('JS · 整圆脸 · 眼极大且圆', 12, 92, 8.8) +
      txt('小柄 · 圆椭圆 · 眼大略长 · 颌线柔', 12, 105, 8.8) +
      txt('JK · 长椭圆 · 眼狭长 · 颌线清', 12, 118, 8.8));
  }
  /* headfwd */
  return svg(H(108,28,8) + L('M106 36 L100 62',5) + L('M102 44 L92 62') + L('M104 44 L114 62') +
    `<path d="M100 46 L100 112" stroke="${RED}" stroke-width="1.3" stroke-dasharray="5 4"/>` +
    `<circle cx="108" cy="28" r="2.5" fill="${RED}" opacity=".8"/>` + G +
    txt('头颈前倾 · 头落在肩线前方 · 伏案/疲惫', 34, 127));
}

/* ================= 8j. 发型 ================= */
function hairSvg(kind: string): string {
  const face = `<circle cx="100" cy="66" r="26" fill="${FILL}" stroke="${GRID}" stroke-width="1.6"/>`;
  const P = (d: string, w = 3.5): string => `<path d="${d}" stroke="${INK}" stroke-width="${w}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
  if (kind === 'longstraight') {
    return svg(face + P('M68 110 L68 58 Q68 30 100 30 Q132 30 132 58 L132 110') + P('M74 50 Q100 40 126 50', 2.5) +
      txt('长直发 · 侧幕垂到腰 · 齐刘海/长刘海', 36, 127));
  }
  if (kind === 'himecut') {
    return svg(face + P('M68 110 L68 58 Q68 30 100 30 Q132 30 132 58 L132 110') +
      P('M76 62 L74 88 M126 62 L128 88', 3) + P('M72 48 L128 48', 3) +
      txt('姬发式 · 齐刘海+侧发齐+后长（hime cut 32K）', 28, 127));
  }
  if (kind === 'twintails') {
    return svg(face + P('M70 52 Q74 30 100 30 Q126 30 130 52', 3) +
      P('M70 50 Q46 64 48 100 M130 50 Q154 64 152 100', 4) +
      `<circle cx="66" cy="54" r="3.5" fill="${RED}" opacity=".8"/><circle cx="134" cy="54" r="3.5" fill="${RED}" opacity=".8"/>` +
      txt('双马尾 · 对称双尾（twintails）', 56, 127));
  }
  if (kind === 'ponytail') {
    return svg(face + P('M70 52 Q74 30 100 30 Q126 30 130 52', 3) +
      P('M126 44 Q150 58 148 100', 4) + `<circle cx="126" cy="46" r="3.5" fill="${RED}" opacity=".8"/>` +
      txt('单马尾 · 高扎=元气 · 低扎=文静', 48, 127));
  }
  if (kind === 'sidetail') {
    return svg(face + P('M70 52 Q74 30 100 30 Q126 30 130 52', 3) +
      P('M74 48 Q58 72 62 104', 4) + `<circle cx="74" cy="50" r="3.5" fill="${RED}" opacity=".8"/>` +
      txt('侧马尾 · 披肩一侧 · 温柔/邻家', 52, 127));
  }
  if (kind === 'twinbraid') {
    return svg(face + P('M70 52 Q74 30 100 30 Q126 30 130 52', 3) +
      P('M70 52 Q54 70 56 102', 3.5) + P('M56 62 L66 68 M52 74 L64 80 M52 88 L64 94', 2.2) +
      P('M130 52 Q146 70 144 102', 3.5) + P('M134 62 L144 68 M136 74 L148 80 M136 88 L148 94', 2.2) +
      txt('双麻花辫 · 分段编织纹理（braids）', 44, 127));
  }
  if (kind === 'bun') {
    return svg(face + P('M70 52 Q74 30 100 30 Q126 30 130 52', 3) +
      `<circle cx="100" cy="24" r="11" fill="none" stroke="${INK}" stroke-width="3.2"/>` + P('M92 24 Q100 17 108 24', 2) +
      txt('丸子头 · 顶扎圆髻（hair bun）', 56, 127));
  }
  if (kind === 'doublebun') {
    return svg(face + P('M70 52 Q74 30 100 30 Q126 30 130 52', 3) +
      `<circle cx="72" cy="28" r="10" fill="none" stroke="${INK}" stroke-width="3"/><circle cx="128" cy="28" r="10" fill="none" stroke="${INK}" stroke-width="3"/>` +
      txt('双丸子 · 天线对称（double bun 179K）', 40, 127));
  }
  if (kind === 'bob') {
    return svg(face + P('M70 92 Q62 44 100 32 Q138 44 130 92') + P('M70 92 Q84 100 100 100 Q116 100 130 92', 2.5) +
      txt('波波头 · 齐颌弧线（bob cut）', 58, 127));
  }
  if (kind === 'layered') {
    return svg(face + P('M70 76 Q64 38 100 32 Q136 38 130 76') +
      P('M70 76 L64 84 M78 78 L74 88 M92 80 L90 90 M108 80 L110 90 M122 78 L126 88 M130 76 L136 84', 2.4) +
      txt('层次短发 · 发尾碎而不齐（layered）', 44, 127));
  }
  if (kind === 'longcurls') {
    return svg(face + P('M68 100 L68 58 Q68 30 100 30 Q132 30 132 58 L132 100') +
      P('M68 100 Q60 110 70 116 Q80 120 76 110 M132 100 Q140 110 130 116 Q120 120 124 110', 2.6) +
      txt('长卷发 · 发尾螺旋收（curly）', 56, 127));
  }
  if (kind === 'waves') {
    return svg(face + P('M68 58 Q58 74 70 90 Q82 104 68 116 M132 58 Q142 74 130 90 Q118 104 132 116', 3.2) +
      P('M68 58 Q70 30 100 30 Q130 30 132 58', 3.2) +
      txt('大波浪 · S 形帘幕（wavy hair）', 58, 127));
  }
  if (kind === 'halfupdo') {
    return svg(face + P('M118 38 Q134 44 132 64', 3) + `<circle cx="118" cy="40" r="3.5" fill="${RED}" opacity=".8"/>` +
      P('M68 60 L68 106 M132 60 L132 106', 3) +
      txt('半扎发 · 上半扎起下半披（half updo 60K）', 30, 127));
  }
  if (kind === 'blunt') {
    return svg(face + P('M70 44 Q70 28 100 28 Q130 28 130 44', 3) + P('M70 44 L130 44', 7) +
      txt('齐刘海 · 一条硬平线（blunt bangs）', 52, 127));
  }
  if (kind === 'airbangs') {
    return svg(face + P('M70 44 Q70 28 100 28 Q130 28 130 44', 3) +
      `<path d="M70 44 L130 44" stroke="${INK}" stroke-width="4" stroke-dasharray="9 5" fill="none"/>` +
      txt('空气刘海 · 透眉有缝（see-through bangs）', 44, 127));
  }
  if (kind === 'swept') {
    return svg(face + P('M72 34 Q104 30 128 52', 5) + P('M72 34 Q68 44 70 54', 3) +
      txt('斜刘海 · 单向扫过（swept bangs 162K）', 44, 127));
  }
  /* parted 中分 */
  return svg(face + P('M100 30 Q86 42 78 58 M100 30 Q114 42 122 58') +
    P('M100 30 Q70 34 68 60 M100 30 Q130 34 132 60', 3) +
    txt('中分 · 双帘露额（parted bangs 313K）', 44, 127));
}

/* ================= 8k. 服装动态 ================= */
function clothSvg(kind: string): string {
  if (kind === 'runflare') {
    return svg(
      `<path d="M70 32 L130 32 L156 70 Q128 52 100 70 Q72 52 44 70 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M44 70 L40 58 M100 70 L100 56 M156 70 L160 58" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<path d="M34 30 L52 34 M30 44 L48 48" stroke="${GRID}" stroke-width="2" stroke-linecap="round"/>` +
      txt('奔跑裙扬 · 伞形张开 + 速度线', 52, 127));
  }
  if (kind === 'seatedpool') {
    return svg(
      `<path d="M64 44 L136 44 L146 78 L54 78 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M60 78 L140 78" stroke="${INK}" stroke-width="2.5"/>` +
      `<path d="M78 78 Q84 92 80 104 M100 78 Q102 94 100 106 M122 78 Q118 92 122 104" stroke="${TXT}" stroke-width="1.6" fill="none"/>` +
      txt('坐下裙堆 · 沿大腿摊开 + 垂褶', 52, 127));
  }
  if (kind === 'sleeveslip') {
    return svg(
      `<path d="M100 28 L100 96" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>` +
      `<path d="M86 44 L114 44 L110 66 L90 66 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M128 46 L128 62" stroke="${RED}" stroke-width="1.5" marker-end="url(#arw)"/>` +
      txt('抬手袖滑 · 袖子顺重力滑向肘部', 52, 127));
  }
  if (kind === 'collar') {
    return svg(
      `<path d="M70 30 L100 62 L130 30" stroke="${INK}" stroke-width="3" fill="none"/>` +
      `<path d="M70 30 L78 44 M130 30 L122 44" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      `<circle cx="100" cy="70" r="3" fill="${INK}"/><circle cx="100" cy="86" r="3" fill="none" stroke="${TXT}" stroke-width="1.6"/>` +
      txt('领口松脱 · 第一颗扣开着（open collar）', 40, 127));
  }
  if (kind === 'tiefly') {
    return svg(
      `<path d="M88 40 L74 30 L74 50 Z M100 40 L114 30 L114 50 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<circle cx="100" cy="40" r="4" fill="${INK}"/>` +
      `<path d="M96 46 Q80 66 66 78 M104 46 Q122 62 136 70" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      `<path d="M120 24 L138 26 M124 34 L140 36" stroke="${GRID}" stroke-width="2" stroke-linecap="round"/>` +
      txt('领结飘动 · 飘带顺风向（fx 红领结）', 44, 127));
  }
  if (kind === 'jacket') {
    return svg(
      `<path d="M70 40 Q100 26 130 40 L134 70 L66 70 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M70 40 L60 84 L96 92 M130 40 L136 72" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      txt('外套半脱 · 单肩滑落（single off shoulder）', 36, 127));
  }
  if (kind === 'wetcling') {
    return svg(
      `<path d="M84 30 Q100 24 116 30 L120 92 L80 92 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M96 44 Q92 62 98 80 M108 44 Q104 62 110 80" stroke="${TXT}" stroke-width="1.6" fill="none"/>` +
      `<path d="M84 94 Q87 100 84 103 Q81 100 84 94 Z" fill="#9db3c8" opacity=".8"/>` +
      `<path d="M116 94 Q119 100 116 103 Q113 100 116 94 Z" fill="#9db3c8" opacity=".8"/>` +
      txt('湿衣贴身 · 贴出轮廓 + 滴水（wet clothes 62K）', 30, 127));
  }
  if (kind === 'loosesock') {
    return svg(
      `<path d="M84 18 L82 62 M116 18 L118 62" stroke="${INK}" stroke-width="2.2" fill="none"/>` +
      `<path d="M80 58 Q100 64 120 58 L122 106 Q100 112 78 106 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M82 66 Q100 74 118 66 M84 76 Q100 84 116 76" stroke="${TXT}" stroke-width="1.8" fill="none"/>` +
      txt('袜口松垮 · 堆出横向褶（loose socks 22.8K）', 32, 127));
  }
  if (kind === 'skirtlift') {
    return svg(
      `<path d="M64 30 L136 30 L148 66 Q122 50 100 64 Q78 50 52 66 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M52 66 Q74 76 100 64 Q126 76 148 66" stroke="${TXT}" stroke-width="1.6" fill="none"/>` +
      `<path d="M88 100 L92 86 M100 104 L100 88 M112 100 L108 86" stroke="${GRID}" stroke-width="2" stroke-linecap="round"/>` +
      txt('裙摆掀起 · 风从下往上（skirt lift 95K）', 38, 127));
  }
  if (kind === 'hemflip') {
    return svg(
      `<path d="M80 40 L120 40 L124 84 L76 84 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M76 84 Q88 72 100 84 Q112 72 124 84" stroke="${INK}" stroke-width="2.2" fill="none"/>` +
      txt('衣角翻起 · 下摆离体翻卷（untucked）', 44, 127));
  }
  if (kind === 'buttonstrain') {
    return svg(
      `<path d="M86 26 L86 104 M114 26 L114 104" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<circle cx="100" cy="48" r="4" fill="${INK}"/><circle cx="100" cy="70" r="4" fill="${INK}"/>` +
      `<path d="M86 48 L70 44 M114 48 L130 44 M86 70 L68 68 M114 70 L132 68" stroke="${TXT}" stroke-width="1.6" fill="none"/>` +
      txt('纽扣紧绷 · 拉扯横褶（button strain）', 48, 127));
  }
  if (kind === 'pleats') {
    return svg(
      `<path d="M30 30 L70 30 L78 78 L22 78 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M36 30 L34 78 M44 30 L44 78 M52 30 L54 78 M60 30 L64 78" stroke="${TXT}" stroke-width="1.4" fill="none"/>` +
      `<path d="M110 30 L150 30 L166 78 L94 78 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M118 30 L106 78 M126 30 L122 78 M134 30 L138 78 M142 30 L154 78" stroke="${TXT}" stroke-width="1.4" fill="none"/>` +
      txt('褶裙展开 · 走/坐时褶扇开（左闭右开）', 36, 127));
  }
  if (kind === 'longsleeve') {
    return svg(
      `<path d="M84 24 L84 72" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>` +
      `<path d="M70 58 L98 58 L98 96 Q84 102 70 96 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M74 98 L74 106 M82 100 L82 108 M90 98 L90 106" stroke="${INK}" stroke-width="2.2"/>` +
      txt('袖口过长 · 只露指尖（sleeves past wrists）', 32, 127));
  }
  if (kind === 'scarf') {
    return svg(
      `<circle cx="70" cy="52" r="18" fill="${FILL}" stroke="${GRID}" stroke-width="1.6"/>` +
      `<path d="M84 54 Q112 44 146 46 M84 62 Q116 56 150 64 M84 70 Q112 70 142 84" stroke="${INK}" stroke-width="3" fill="none"/>` +
      txt('围巾后飘 · 与运动方向相反', 56, 127));
  }
  /* chain 配饰荡动 */
  return svg(
    `<path d="M60 40 L140 40" stroke="${INK}" stroke-width="2.5"/>` +
    `<path d="M80 40 Q76 74 92 86 M120 40 Q124 74 108 86" stroke="${INK}" stroke-width="2" fill="none"/>` +
    `<circle cx="92" cy="88" r="4" fill="none" stroke="${INK}" stroke-width="2"/><circle cx="108" cy="88" r="4" fill="none" stroke="${INK}" stroke-width="2"/>` +
    `<path d="M92 88 Q104 96 108 88" stroke="${RED}" stroke-width="1.4" stroke-dasharray="3 2" fill="none"/>` +
    txt('配饰荡动 · 垂链/挂饰摆出弧线', 48, 127));
}

/* ================= 8l. 叙事与活感 ================= */
function storySvg(kind: string): string {
  const L = (d: string, w = 4): string => `<path d="${d}" stroke="${INK}" stroke-width="${w}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
  const H = (x: number, y: number, r = 9): string => `<circle cx="${x}" cy="${y}" r="${r}" fill="${FILL}" stroke="${INK}" stroke-width="2"/>`;
  const G = `<line x1="30" y1="118" x2="170" y2="118" stroke="${GRID}" stroke-width="1.2"/>`;
  const A = (d: string): string => `<path d="${d}" stroke="${RED}" stroke-width="1.6" fill="none" stroke-dasharray="4 3" marker-end="url(#arw)"/>`;
  if (kind === 'midmoment') {
    return svg(H(96,32) + L('M96 41 L92 76',6) + L('M92 50 L104 44') + L('M91 50 L80 58') +
      L('M92 76 L104 92 L108 106',5) + L('M92 76 L84 96 L78 88',5) + G +
      `<path d="M64 60 Q56 76 68 92" stroke="${GRID}" stroke-width="2" fill="none" stroke-dasharray="4 3"/>` +
      txt('故事瞬间 · 交叉步进行中（mid-stride）', 40, 127));
  }
  if (kind === 'aftermath') {
    return svg(
      `<path d="M76 76 Q72 100 80 108 L120 108 Q128 100 124 76 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M124 84 Q136 86 130 96" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<path d="M88 66 Q92 56 88 46 M100 66 Q104 54 100 42 M112 66 Q116 56 112 46" stroke="${TXT}" stroke-width="2" fill="none"/>` +
      `<path d="M64 96 Q58 104 66 110" stroke="${RED}" stroke-width="1.5" stroke-dasharray="4 3" fill="none"/>` +
      txt('动作残响 · 杯还在晃 · 热气还在升', 48, 127));
  }
  if (kind === 'offscreen') {
    return svg(H(126,40) + L('M126 49 L122 84',6) + L('M122 58 L112 74') + L('M123 58 L132 72') + L('M122 84 L114 116',5) + L('M122 84 L130 116',5) + G +
      A('M112 36 L40 30') + `<circle cx="30" cy="34" r="6" fill="#f7edcf" opacity=".9"/>` +
      txt('画外暗示 · 她看的东西不在画面里', 40, 127));
  }
  if (kind === 'touch') {
    return svg(
      `<rect x="60" y="24" width="80" height="80" rx="3" fill="none" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M70 30 L68 44 M84 30 L82 46 M100 30 L98 44 M116 30 L114 46 M130 30 L128 44" stroke="#9db3c8" stroke-width="2" opacity=".7"/>` +
      `<path d="M96 104 L96 72 Q96 64 102 64 L102 84 L106 62 Q108 56 113 60 L110 86 L114 68 Q118 62 122 68 L118 92 Q116 104 106 104 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.8"/>` +
      txt('环境互动 · 手心贴上冰玻璃（触感）', 44, 127));
  }
  if (kind === 'micro') {
    return svg(
      `<path d="M62 40 L138 40 L146 84 L54 84 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M120 76 Q128 62 136 72 L138 82" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M146 88 L152 78" stroke="${RED}" stroke-width="1.5" marker-end="url(#arw)"/>` +
      txt('微动作 · 捏裙角/拽袜口/攥包带', 52, 127));
  }
  if (kind === 'contradict') {
    return svg(
      `<circle cx="100" cy="54" r="27" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M88 44 Q93 40 98 44 M102 44 Q107 40 112 44" stroke="${INK}" stroke-width="2.4" fill="none"/>` +
      `<path d="M88 64 Q100 72 112 64" stroke="${INK}" stroke-width="2.5" fill="none"/>` +
      `<path d="M118 60 L120 72" stroke="#9db3c8" stroke-width="2.5"/>` +
      `<path d="M84 92 L84 104 M116 92 L116 104" stroke="${INK}" stroke-width="3" stroke-linecap="round"/>` +
      txt('情绪矛盾 · 笑着流泪 / 咬牙的平静', 48, 127));
  }
  if (kind === 'prop') {
    return svg(
      `<rect x="70" y="54" width="60" height="48" rx="6" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M84 54 Q100 30 116 54" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<rect x="88" y="70" width="18" height="14" fill="none" stroke="${RED}" stroke-width="1.8"/>` +
      `<path d="M86 68 L108 68 M86 86 L108 86 M86 70 L86 84 M106 70 L106 84" stroke="${RED}" stroke-width="1" stroke-dasharray="2 2"/>` +
      `<path d="M74 92 L80 96 M120 60 L124 66" stroke="${TXT}" stroke-width="1.4"/>` +
      txt('道具叙事 · 补丁/磨损/胶带=人生轨迹', 40, 127));
  }
  if (kind === 'imperfect') {
    return svg(
      `<g transform="rotate(9 98 40)"><path d="M92 40 L78 30 L78 50 Z M104 40 L118 30 L118 50 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/><circle cx="98" cy="40" r="4" fill="${INK}"/></g>` +
      `<path d="M124 62 Q134 54 138 66" stroke="${INK}" stroke-width="2" fill="none"/>` +
      `<path d="M62 92 Q72 86 76 96" stroke="${INK}" stroke-width="2" fill="none"/>` +
      txt('不完美 · 歪领结/散出一缕/袜子松', 48, 127));
  }
  if (kind === 'gazelogic') {
    return svg(
      `<circle cx="100" cy="58" r="24" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<circle cx="92" cy="54" r="3" fill="${INK}"/><circle cx="108" cy="54" r="3" fill="${INK}"/>` +
      A('M74 54 L40 46') + A('M100 82 L100 104') + A('M124 60 L156 68') +
      txt('视线逻辑 · 画外=有故事', 62, 124) + txt('镜头=对话', 14, 24) + txt('物件', 152, 96) +
      txt('看镜头=对话 · 看物件=内省', 30, 14));
  }
  if (kind === 'time') {
    return svg(
      `<circle cx="160" cy="52" r="12" fill="#e8b06a" opacity=".6"/>` +
      `<ellipse cx="76" cy="110" rx="40" ry="6" fill="rgba(58,52,64,.3)"/>` +
      figure(92, 74, 0.42) + G +
      `<path d="M120 40 Q126 44 122 50 Q116 46 120 40 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.4"/>` +
      txt('时间痕迹 · 长影/落叶/将尽的黄昏', 40, 127));
  }
  if (kind === 'moodweather') {
    return svg(
      `<path d="M60 56 Q100 28 140 56 Z" fill="${FILL}" stroke="${INK}" stroke-width="2"/>` +
      `<line x1="100" y1="56" x2="100" y2="96" stroke="${INK}" stroke-width="2"/>` +
      `<path d="M52 30 L50 44 M70 22 L68 36 M130 22 L128 36 M148 30 L146 44 M90 16 L88 30 M110 16 L108 30" stroke="#9db3c8" stroke-width="2" opacity=".7"/>` +
      `<circle cx="146" cy="80" r="9" fill="#e8b06a" opacity=".5"/>` +
      txt('环境情绪 · 雨=低气压 · 伞下暖灯=反用', 36, 127));
  }
  if (kind === 'physicstrace') {
    return svg(
      `<ellipse cx="66" cy="92" rx="22" ry="8" fill="none" stroke="#9db3c8" stroke-width="1.6"/>` +
      `<ellipse cx="66" cy="92" rx="12" ry="4" fill="none" stroke="#9db3c8" stroke-width="1.2"/>` +
      `<path d="M112 108 Q116 100 124 104 Q120 112 112 108 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      `<path d="M132 92 Q136 84 144 88 Q140 96 132 92 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.6"/>` +
      txt('物理痕迹 · 脚印/涟漪/压痕=刚经过', 40, 127));
  }
  /* relationship 关系叙事 */
  return svg(
    figure(64, 74, 0.36) + figure(136, 74, 0.36) + G +
    `<path d="M84 108 L116 108" stroke="${RED}" stroke-width="1.3" stroke-dasharray="4 3"/><path d="M84 104 L84 112 M116 104 L116 112" stroke="${RED}" stroke-width="1.3"/>` +
    `<path d="M96 104 Q100 98 104 104 Q100 108 96 104 Z" fill="${FILL}" stroke="${INK}" stroke-width="1.4"/>` +
    txt('关系叙事 · 距离+朝向+中间物=关系说明', 34, 127));
}

/* ================= 数据 ================= */
const SECTIONS: Sec[] = [
  {
    id: 'shot', title: '景别', sub: 'Shot Size',
    tip: '决定"看多少"。STEP2 先定景别再定机位；半身与全身各配防裁切 negative（见页尾工具句）。',
    items: [
      { zh: '大特写', en: 'extreme close-up, face focus', note: '只保留眼/嘴区域。情绪最大化、信息最少；脸眼细节必须写死，崩坏率最高。', dia: shotSvg('ecu') },
      { zh: '特写', en: 'close-up', note: '脸部占满画面。表情优先；必带 entire head in frame with margin above hair 防裁头。', dia: shotSvg('closeup') },
      { zh: '头肩像', en: 'portrait, head and shoulders', note: '头+肩经典肖像景别；介于特写与半身之间，最通用的头像级构图。', dia: shotSvg('portrait') },
      { zh: '半身（裁到胸）', en: 'bust shot cropped at mid-torso', note: '头+胸。半身首选，兼顾表情与手势；本项目半身默认景别。', dia: shotSvg('bust') },
      { zh: '牛仔镜头（裁到大腿）', en: 'cowboy shot', note: 'booru 标准词（85万+作品）。大腿中部以上，能带腰饰与手势，二创最常用。', dia: shotSvg('cowboy') },
      { zh: '全身', en: 'full body', note: '完整交代体型与服装；negative 加 cropped feet 防裁脚。', dia: shotSvg('full') },
      { zh: '远景', en: 'wide shot, full body with empty space', note: '人小环境大；孤独感/交代空间用，配 rule of space。', dia: shotSvg('wide') },
      { zh: '极远景', en: 'extreme wide shot, establishing shot', note: '大环境小人物；开场交代地点/规模，人物占比可低到 10%。', dia: shotSvg('xwide') },
      { zh: '下半身', en: 'lower body focus, thighs to shoes in frame', note: '只拍腰以下：裙摆/丝袜/鞋的重点图；只写裙摆做 context，不写脸/发。', dia: shotSvg('lowerbody') }
    ]
  },
  {
    id: 'vangle', title: '垂直机位', sub: 'Vertical Angle',
    tip: '决定"谁高谁低"的心理。相机越高于眼睛越压迫，越低于眼睛越强势；15°/30° 是建议值。',
    items: [
      { zh: '平视', en: 'eye-level, straight-on, zero tilt zero dutch', note: '中性平等，最稳。机位高度=人物眼睛高度；半身首选，写 zero tilt zero dutch 防自作主张。', dia: vAngleSvg('eye') },
      { zh: '肩高机位', en: 'shoulder-level shot', note: '相机在肩膀高度、略低于眼：微妙的威势感，不压人；对话/桌面对峙常用。', dia: vAngleSvg('shoulder') },
      { zh: '高俯 15°', en: 'from above, high angle looking down ~15°', note: '轻微压迫+交代站位；全身机位不难受的上限。', dia: vAngleSvg('high15') },
      { zh: '高俯 30°', en: 'from above, high angle looking down ~30°', note: '明显压迫/弱小/被堵感；fx A01 用 30°（配斜切 15°）。', dia: vAngleSvg('high30') },
      { zh: '高俯 45°', en: 'from above, high angle looking down ~45°', note: '介于 30° 与鸟瞰之间；俯瞰台阶/桌面/蹲姿，头顶占比明显。', dia: vAngleSvg('high45') },
      { zh: '鸟瞰', en: "from directly above, bird's eye view, top-down", note: '完全俯视，人物像棋子；展示地面布局/孤立感，面部信息基本丢失。', dia: vAngleSvg('bird') },
      { zh: '微仰 15°', en: 'from below, low angle looking up ~15°', note: '相机在胸口高度：自信/轻威，不压迫；比全平视多一口气场。', dia: vAngleSvg('low15') },
      { zh: '腰高机位', en: 'hip-level shot, camera at waist height', note: '情绪张力位：比平视低一档，绷住不说破；对峙与压迫前的静默常用。', dia: vAngleSvg('hip') },
      { zh: '膝高机位', en: 'knee-level shot', note: '尺寸与控制感：对象显大显强，往上带出被压制感；配仰视更狠。', dia: vAngleSvg('knee') },
      { zh: '仰视', en: 'from below, low angle looking up', note: '权力反转/威慑；JK 题材易变味，能用平视就不用仰角。', dia: vAngleSvg('low') },
      { zh: '贴地机位', en: 'ground-level shot, camera on the ground', note: '镜头放地上：巨大感/靴鞋特写；动漫常用"足下机位"。', dia: vAngleSvg('ground') },
      { zh: '仰视极端', en: "from directly below, worm's eye view", note: '极端压迫；配 foreshortening 夸张透视，慎用。', dia: vAngleSvg('worm') }
    ]
  },
  {
    id: 'hangle', title: '水平机位', sub: 'Horizontal Angle',
    tip: '决定"从哪一侧看"。斜睨类表情用正面机位+头转向，不转机位（本项目规则）。',
    items: [
      { zh: '正面', en: 'front view, straight-on', note: '对视/对峙感；正面机位+头转向可做斜睨。', dia: hAngleSvg('front') },
      { zh: '3/4 侧', en: '3/4 view', note: '立体感最强、最常用；脸部微侧不丢五官。', dia: hAngleSvg('threequarter') },
      { zh: '正侧面', en: 'profile, side view', note: '剪影叙事；冷淡/距离感；五官细节最少。', dia: hAngleSvg('profile') },
      { zh: '正背面', en: 'from behind, rear view', note: '距离/未知/跟随感；交代发背与背影服装。', dia: hAngleSvg('rear') },
      { zh: '背 3/4', en: '3/4 back view, from behind at 45°', note: '回眸镜头标配：背影+侧脸同框，信息量最大。', dia: hAngleSvg('back34') },
      { zh: '过肩', en: 'over-the-shoulder', note: '旁观/对话感；前景肩膀压画框，配负空间。', dia: hAngleSvg('ots') },
      { zh: '第一人称', en: 'pov, first-person view', note: '机位=角色眼睛；代入感最强，常配 foreshortening 手部。', dia: hAngleSvg('pov') }
    ]
  },
  {
    id: 'dutch', title: '荷兰角', sub: 'Dutch Angle',
    tip: '画面旋转=失衡/不安。本项目规则：只配俯视用；平视+斜切双叠加脸必歪（实测）。',
    items: [
      { zh: '轻斜切 15°', en: 'dutch angle ~15°', note: '轻微失衡/不安；配 from above ~30° 即 fx A01 组合。', dia: dutchSvg(15) },
      { zh: '强斜切 30-45°', en: 'dutch angle ~30-45°', note: '强烈紧张/混乱/心理崩坏；人脸和背景一起歪，崩坏率高，慎用。', dia: dutchSvg(32) }
    ]
  },
  {
    id: 'lens', title: '焦段与透视', sub: 'Lens & Perspective',
    tip: '广角=冲击+变形，长焦=压缩+糊背景。动漫图常写 mm 数或直接写效果词。',
    items: [
      { zh: '广角 24mm', en: 'wide angle, 24mm, exaggerated perspective', note: '近大远小夸张、纵深强；适合冲击力/空间感；脸会变形。', dia: lensSvg('wide24') },
      { zh: '标准 50mm', en: 'standard lens, 50mm', note: '接近人眼，最中性；拿不准时用它。', dia: lensSvg('std50') },
      { zh: '人像 85mm', en: 'portrait lens, 85mm, shallow depth of field', note: '脸型最讨喜；背景开始虚化。', dia: lensSvg('portrait85') },
      { zh: '长焦 135mm', en: 'telephoto, 135mm, compressed background, blurry background', note: '压缩空间（背景拉近变大）；背景糊成色块。', dia: lensSvg('tele135') },
      { zh: '鱼眼', en: 'fisheye lens', note: '极端畸变；漫画感/特殊视点；慎用。', dia: lensSvg('fisheye') },
      { zh: '透视缩短', en: 'foreshortening', note: '手脚/身体朝镜头伸展的近大远小；booru 标准词（7万+）。伸手向镜头必用。', dia: lensSvg('foreshortening') },
      { zh: '浅景深', en: 'shallow depth of field', note: '只有主体清晰：虚化即指向，把观众眼睛按在焦点上；人像/特写默认。', dia: dofSvg('shallow') },
      { zh: '深景深', en: 'deep focus, everything sharp', note: '远近全清晰：环境参与叙事；场景图/设定图用。', dia: dofSvg('deep') },
      { zh: '焦外光斑', en: 'bokeh, out-of-focus light circles', note: '光点化成柔圆：夜景/节日/窗边；写作时给光源位置就够。', dia: dofSvg('bokeh') }
    ]
  },
  {
    id: 'persp', title: '透视体系', sub: 'Perspective System',
    tip: '空间的数学。一点=正面纵深，两点=街角双墙，三点=高楼仰俯；STEP3 背景必须服从这里的机位。',
    items: [
      { zh: '一点透视', en: 'one-point perspective', note: '灭点在画面中，正面纵深（走廊/街道/教室）；视线直给、庄重。', dia: perspSvg('onepoint') },
      { zh: '两点透视', en: 'two-point perspective', note: '街角双面墙，两灭点在框外左右；墙体收分天然成引导线。', dia: perspSvg('twopoint') },
      { zh: '三点透视', en: 'three-point perspective', note: '垂直线向天顶/地底收束；仰拍高楼压迫感强，慎配俯视人物。', dia: perspSvg('threepoint') }
    ]
  },
  {
    id: 'comp', title: '构图法', sub: 'Composition',
    tip: '三步流程：①定画框（三分格）→ ②定景别 → ③加视线诱导。每次至少用 2 个构图法；只写主体位置不够，必须写清留白里是什么（环境/负空间/引导线）。',
    items: [
      { zh: '三分法', en: 'rule of thirds', note: '眼睛/脸压交点，地平线压三分线；四条交点=四个落点选择。', dia: compSvg('thirds') },
      { zh: '三角构图', en: 'triangle composition', note: '正三角=稳（环胸+双脚撑地天然成三角）；倒三角=动。', dia: compSvg('triangle') },
      { zh: '视线留白', en: 'rule of space, looking into empty space', note: '不直视镜头时，视线方向必须留空且不放道具。', dia: compSvg('space') },
      { zh: '负空间', en: 'negative space, empty space in front', note: '孤独/对峙时负空间就是内容，要写出"空"。', dia: compSvg('negative') },
      { zh: '引导线', en: 'leading lines', note: '墙角竖缝/墙地交线收束到脸或脑后；让眼睛先落地再看脸。', dia: compSvg('leading') },
      { zh: '对称构图', en: 'symmetrical composition', note: '仪式感/端庄/压迫；墙角两面天然对称框，人物压中缝。', dia: compSvg('symmetric') },
      { zh: '画框框', en: 'frame in frame', note: '门框/窗框包住主体；STEP2 只允许一条边，多了是 STEP3 的事。', dia: compSvg('fif') },
      { zh: '对角线构图', en: 'diagonal composition', note: '主元素沿对角线排布=张力/动感；与横平竖直的安定相反。', dia: compSvg('diagonal') },
      { zh: '黄金分割', en: 'golden ratio, golden spiral', note: '1:0.618 落点，比三分法更柔和的偏心构图。', dia: compSvg('golden') },
      { zh: 'S 形构图', en: 'S-curve composition', note: '道路/河流/身姿走 S 线，优雅流动；风景+人物经典。', dia: compSvg('scurve') },
      { zh: '前景遮挡', en: 'foreground occlusion, depth layering', note: '前景物体遮一部分画面=纵深；柱子/栏杆/路人皆可。', dia: compSvg('fgblock') },
      { zh: '反射镜像', en: 'reflection, mirror composition', note: '水面/镜子/玻璃倒影；信息翻倍，自我主题常用。', dia: compSvg('reflect') },
      { zh: '重复与节奏', en: 'repetition, pattern, rhythm', note: '重复元素给秩序感；破一处（异色/残缺）即为焦点。', dia: compSvg('repeat') },
      { zh: '双人镜头', en: 'two-shot', note: '两人同框；对峙/关系/距离一目了然，注意视线方向。', dia: compSvg('twoshot') },
      { zh: '大小递进', en: 'large-to-small flow', note: '视线天然从大物体流向小物体；把主体放在递进终点。', dia: compSvg('largetosmall') },
      { zh: '疏密对比', en: 'density contrast', note: '均匀=无焦点；密中留空或空中加密，视线自动落在反差处。', dia: compSvg('density') },
      { zh: '视觉平衡', en: 'visual balance', note: '大物体 vs 一组小物体配平；失衡=惊险，平衡=安定。', dia: compSvg('balance') },
      { zh: '对比', en: 'contrast', note: '明度/色彩/形状/纹理任一维度反差=焦点制造机；亮主体压暗底最通用。', dia: compSvg('contrast') },
      { zh: '压迫框', en: 'claustrophobic framing, tight crop', note: '四面切紧贴边=窒息/被困；与负空间相反的手段，情绪极端时用。', dia: compSvg('squeeze') },
      { zh: '头顶空间', en: 'headroom', note: '头顶留一点气（不过空）；顶到边或空太多都别扭。半身/全身构图先查头顶。', dia: compSvg('headroom') },
      { zh: '运动空间', en: 'lead room, space in the direction of movement', note: '运动方向前留空间；不留=撞墙感。追击/逃离题材必用。', dia: compSvg('leadroom') },
      { zh: '中心构图', en: 'centered composition, subject on center line', note: '正面压迫/仪式感；压竖缝居中即 fx A01 用法。', dia: compSvg('centered') }
    ]
  },
  {
    id: 'special', title: '特殊机位', sub: 'Special Setups',
    tip: '信息量大的小众视角；开场/转场/情绪切换用，一张图最多出现一次。',
    items: [
      { zh: '监控视角', en: 'surveillance camera view, cctv angle, security camera', note: '高角+广角俯看全场；冷漠/被观察感，可配鱼眼（本项目禁文字水印）。', dia: specialSvg('cctv') },
      { zh: '航拍', en: 'aerial shot, high above the ground', note: '大幅俯视全景：尺度感/渺小感/世界观交代；人可小不可丢。', dia: specialSvg('aerial') },
      { zh: '自拍视角', en: 'selfie, arm extended toward camera', note: '手机靠近镜头近大远小；休闲/日常感，脸变形风险高。', dia: specialSvg('selfie') },
      { zh: '窗外窥视', en: 'view through a window, looking in through the frame', note: '隔一层框偷看框内的人；雨夜/跟踪/私密感题材利器。', dia: specialSvg('window') }
    ]
  },
  {
    id: 'ratio', title: '画幅比例', sub: 'Aspect Ratio',
    tip: '先定画幅再定景别：竖幅装人、横幅装环境、方形装概念。Mage Advanced 里选比例（prompt 不用重复写），但留白方向要按画幅反推。',
    items: [
      { zh: '3:4 竖幅', en: '3:4 portrait aspect ratio', note: '人像主力画幅：全身/立绘，人物占比大；本项目标准人像比例。', dia: ratioSvg('p34') },
      { zh: '4:5 竖幅', en: '4:5 portrait aspect ratio', note: '半身/头像更紧凑，社媒友好；比 3:4 略宽，肩线装得稳。', dia: ratioSvg('p45') },
      { zh: '16:9 横幅', en: '16:9 landscape aspect ratio', note: '场景/叙事画幅：横向留白多，环境与人物同框；STEP3 空间交代用。', dia: ratioSvg('p169') },
      { zh: '1:1 方形', en: '1:1 square aspect ratio', note: '概念图/头像画幅：中心构图天然成立，适合设定图与特写。', dia: ratioSvg('p11') }
    ]
  },
  {
    id: 'grammar', title: '镜头语法', sub: 'Shot Grammar',
    tip: '多图/多镜头时的空间规则（单图也防「越轴」）：轴线决定机位待哪侧、反打决定视线方向、视线匹配决定两张图能不能接。',
    items: [
      { zh: '180 度线（轴线）', en: '180-degree line, keep the camera on one side', note: '两人连线为轴，机位全在同一侧；越轴观众会丢失空间方向。双人 prompt 用「左/右 + 朝向」把轴线写死。', dia: gramSvg('axis') },
      { zh: '正反打', en: 'reverse shot', note: 'A 看 B 与 B 看 A 互为反向的两张图；同一轴线同一侧，视线方向互换。', dia: gramSvg('reverse') },
      { zh: '视线匹配', en: 'eyeline match', note: 'A 看画外右，B 就必须从画外左看回来；方向错=不在同一空间。', dia: gramSvg('eyeline') },
      { zh: '30 度原则', en: '30-degree rule', note: '同一主体换机位至少变 30° 或换景别，否则两张图读起来像重复素材（跳切感）。', dia: gramSvg('angle30') }
    ]
  },
  {
    id: 'pose', title: '姿态动作', sub: 'Pose & Action',
    tip: '动作三件套 = 重心（骨盆位置）+ 动作线（脊柱曲线）+ 联动链（头颈肩胸腰盆腿脚）。动势 = 前倾重心 + 对角四肢 + 飘动布料/头发。手永远有事做（扶/撩/插/握），但手部崩坏高发——别让手抢景别焦点。姿态与机位联动：低机位配伸展、高机位配收缩。保形：转面/动作只许强化不许改型（体型 signature）。',
    items: [
      { zh: '中正站姿', en: 'standing, arms at sides, closed legs', note: '设定图基准：重心居中、肩线水平——一切保形从这里出发。', dia: poseSvg('stand') },
      { zh: 'S 站姿（重心偏移）', en: 'contrapposto, weight on one leg', note: '髋部偏移的微 S：站姿不再僵直；booru 37K+，量产「活人感」。', dia: poseSvg('contrapposto') },
      { zh: '环胸', en: 'crossed arms', note: '防线/不信任/冷；双臂天然成三角，正面构图最稳的「拒绝」肢体语言。', dia: poseSvg('crossed') },
      { zh: '叉腰', en: 'hands on hips', note: '气势/自信；手肘外扩占位，剪影立刻变大。', dia: poseSvg('akimbo') },
      { zh: '单手插兜', en: 'hand in pocket', note: '装酷/日常；另一只手别空着——拿手机/拽包带/扶耳机。', dia: poseSvg('pocket') },
      { zh: '靠墙', en: 'against_wall, leaning back', note: '肩背贴墙、重心交给墙（fx A01 同族）；配 leaning_back / leaning_to_the_side 调倾斜。', dia: poseSvg('wall') },
      { zh: '回眸', en: 'looking back, turning around', note: '背影+半脸同框；回眸方向的视线留白必须写。', dia: poseSvg('lookback') },
      { zh: '行走', en: 'walking', note: '日常步态：重心微前、双臂反摆；配 lead room 才有「走向某处」。', dia: poseSvg('walk') },
      { zh: '奔跑', en: 'running, running towards viewer', note: '前倾重心+对角四肢+飘动发衣；动势三件套同现才「快」。', dia: poseSvg('run') },
      { zh: '伸手向镜头', en: 'reaching towards viewer, outstretched arm, foreshortening', note: '近大远小：手大身小；booru 37K+。手是焦点时手部结构要写死。', dia: poseSvg('reach') },
      { zh: '蹲姿抱膝', en: 'squatting, hugging own legs', note: '收缩体态=防御/内敛/等雨；轮廓变成一个小团，适合负空间构图。', dia: poseSvg('squat') },
      { zh: '鸭子坐', en: 'wariza', note: '二次元经典坐姿（booru 109K+）：裙摆形态最好展示的姿势。', dia: poseSvg('wariza') },
      { zh: '椅子端坐', en: 'sitting on chair, knees together, hands on lap', note: '端庄基准坐姿；膝盖并拢、手放膝上，配中正机位。', dia: poseSvg('chair') },
      { zh: '翘腿坐', en: 'sitting on chair, crossed legs', note: '气场坐姿；注意翘腿交叠处的透视压缩（大腿交叠易崩）。', dia: poseSvg('crossleg') },
      { zh: '单膝跪', en: 'kneeling, one knee down', note: '前脚掌撑实、后膝贴地；战斗/宣誓/系鞋带都成立。', dia: poseSvg('kneel') },
      { zh: '枕臂侧躺', en: 'lying, on side, head on arm', note: '慵懒/私密；身体走横线，配俯视或平视机位。', dia: poseSvg('lying') },
      { zh: '托腮', en: 'hand on cheek, elbow on table', note: '沉思/休息/等人；肘撑桌面反作用力成立，别让手悬空。', dia: poseSvg('chin') },
      { zh: '撩发', en: 'hand in hair, adjusting hair', note: '整理头发：手在头侧=半身构图加分项；手部崩坏高发区，先小图验证。', dia: poseSvg('hair') }
    ]
  },
  {
    id: 'pair', title: '二人互动', sub: 'Two-Person Poses',
    tip: '三条铁律：①连接点写清（手/肩/腰在哪接触——接触点就是崩坏点）②轴线锁死（左右+朝向写全，防越轴，见镜头语法区）③身高差与重心先行（谁高谁低、谁靠谁，决定画面力学）。两人同框手部数量翻倍——能用剪影/遮挡就用。',
    items: [
      { zh: '背对背', en: 'back to back, two people standing', note: '信任/搭档；两人剪影连成一块，注意肩线一致。', dia: pairSvg('backtoback') },
      { zh: '牵手', en: 'holding hands, two people facing each other', note: '连接点=交握的手：崩坏高发，可虚化或只给剪影。', dia: pairSvg('handhold') },
      { zh: '并肩同行', en: 'walking side by side, two people, same direction', note: '同伴感；两人朝同一方向，配 lead room 才有「一起走向哪」。', dia: pairSvg('sidebyside') },
      { zh: '对峙站位', en: 'two people facing each other, distance between them', note: '距离=关系；左右+朝向写死锁轴线，别让两人各看各的。', dia: pairSvg('facing') },
      { zh: '拥抱', en: 'hugging, two people, arms around back', note: '全身贴合；写清「谁的头在谁肩上」，否则手臂变章鱼。', dia: pairSvg('hug') },
      { zh: '靠肩', en: 'head on shoulder, leaning, two people', note: '亲密等级=头部接触点；比拥抱克制，比并肩亲密。', dia: pairSvg('shoulder') },
      { zh: '身高差', en: 'height difference, tall and short, two people', note: '构图利器：下巴对头顶；写清差值（一个头/半个头）。', dia: pairSvg('height') },
      { zh: '公主抱', en: 'princess carry, carrying, two people', note: '手臂闭环承托+重心落在抱者胸前；结构复杂，先小图验证。', dia: pairSvg('princess') },
      { zh: '背负', en: 'piggyback, two people, legs around waist', note: '腿环腰+手搭肩；双人肢体交叉最多，崩坏率最高。', dia: pairSvg('piggyback') },
      { zh: '前后站位', en: 'two people, one in foreground out of focus, one behind', note: '前景虚化=层次（高级镜头配方同款）；只借景别不借脸。', dia: pairSvg('foreback') }
    ]
  },
  {
    id: 'expr', title: '神态表情', sub: 'Expressions',
    tip: '神态三件套：眼（形+瞳+高光）+ 眉（表情一半语义在眉毛上，被刘海遮时靠眼和嘴补）+ 嘴（最省力的情绪开关）。铁律：高光是情绪开关——高光点大=有生气，高光缺失/缺口=冷淡/不屑/黑化；眼神方向单独写（looking at viewer / looking away / looking down）。距离衰减：远景靠眉嘴和轮廓读情绪，眼部细节留给近景。姿态联动：身体先信脸才成立（环胸+浅笑=傲，环胸+瞪=凶）。',
    items: [
      { zh: '无表情', en: 'expressionless, closed mouth', note: '冷淡基底；平嘴+平眉，远景也读得出。', dia: exprSvg('blank') },
      { zh: '微笑', en: 'smile, gentle smile', note: '嘴角最小改动量；配垂眼更温柔。', dia: exprSvg('smile') },
      { zh: '露齿笑', en: 'grin, open mouth, teeth', note: '开口形+白齿一横；元气角色标配。', dia: exprSvg('grin') },
      { zh: '大笑', en: 'laughing, open mouth, closed eyes', note: '眯眼(∩)+大开口；比露齿笑更放。', dia: exprSvg('laugh') },
      { zh: '半眯眼 jitome', en: 'jitome, half-closed eyes', note: '冷淡/嫌弃/就这？（booru 50K）；可加侧瞥。', dia: exprSvg('jitome') },
      { zh: '生气', en: 'angry, frown, furrowed brow', note: '眉向内下压是灵魂；光瞪眼不压眉=无效生气。', dia: exprSvg('angry') },
      { zh: '嘟嘴', en: 'pout', note: '小 ∧ 嘴：傲娇/不满标配。', dia: exprSvg('pout') },
      { zh: '惊讶', en: 'surprised, wide-eyed, open mouth', note: '瞪圆眼+抬眉+O 嘴三件套同现。', dia: exprSvg('surprise') },
      { zh: '害羞', en: 'blush, embarrassed', note: '腮红块+视线躲闪；只涂红不躲眼=假害羞。', dia: exprSvg('blush') },
      { zh: '眼含泪', en: 'teary eyes, tears', note: '泪池线+大高光；比哭泣克制，适合隐忍人设。', dia: exprSvg('teary') },
      { zh: '哭泣', en: 'crying, streaming tears, open mouth', note: '泪流线+张开嘴；配闭眼(∪)。', dia: exprSvg('cry') },
      { zh: '得意坏笑', en: 'smug, smirk, half-closed eyes', note: '半眯眼+单边挑眉+斜嘴；不对称是关键。', dia: exprSvg('smug') },
      { zh: '睥睨', en: 'looking down, jitome, half-closed eyes', note: '瞳孔下移+半帘；配高机位=俯视感拉满。', dia: exprSvg('lookdown') },
      { zh: '瞪视', en: 'glaring, staring, eye contact', note: '收瞳+压眉+紧嘴；对峙镜头专用眼。', dia: exprSvg('glare') },
      { zh: '眨眼', en: 'wink, one eye closed', note: '单眼闭弧+小笑；一张图最多一次。', dia: exprSvg('wink') },
      { zh: '汗滴', en: 'sweatdrop, nervous', note: '无语/尴尬（booru 329K 符号）；喜剧点。', dia: exprSvg('sweat') },
      { zh: '咬牙切齿', en: 'gritted teeth, angry', note: '牙格+压眉；压着火的怒。', dia: exprSvg('grit') },
      { zh: '闭眼', en: 'closed eyes, serene', note: '平静/享受/回忆；常配微笑嘴。', dia: exprSvg('closed') }
    ]
  },
  {
    id: 'detail', title: '人物细节', sub: 'Character Details',
    tip: '默认女生视角。细节有预算：远景/全身只给轮廓+大色块（细节会消失），半身给 2-4 个落点，特写才堆细节。落点优先级：发（高光/风动/湿）→ 眼（高光/睫毛/妆）→ 皮肤（锁骨/后颈/汗）→ 手（结构）→ 衣物（飘动/褶皱）。手部与布料褶皱是崩坏重灾区，先小图验证再上成品。',
    items: [
      { zh: '发丝高光', en: 'shiny hair, hair highlights', note: '一条亮带扫过发束；动漫头发=大色块+单条高光带，别画满。', dia: detailSvg('hairhigh') },
      { zh: '风动发', en: 'windblown hair, floating hair', note: '发丝方向一致才可信；与衣物飘动同向。', dia: detailSvg('windhair') },
      { zh: '湿发', en: 'wet hair, damp hair', note: '贴脸束+水珠+高光；雨戏必备（fx_A01 同族）。', dia: detailSvg('wethair') },
      { zh: '呆毛', en: 'ahoge', note: '一根翘起的识别符；静图里最便宜的「活」细节。', dia: detailSvg('ahoge') },
      { zh: '睫毛', en: 'eyelashes, long eyelashes', note: '上浓下疏、眼尾加长提神；近景才画，远景会糊。', dia: detailSvg('lashes') },
      { zh: '瞳孔高光', en: 'shiny eyes, catchlight', note: '大高光=有生气；缺口/缺失=冷淡/黑化（与神态区联动）。', dia: detailSvg('catchlight') },
      { zh: '眼妆', en: 'eye makeup, eyeliner, eyeshadow', note: '眼线尾+眼影渐层：成人感/编辑感；素颜人设别加。', dia: detailSvg('eyemakeup') },
      { zh: '虎牙', en: 'fang', note: '白齿三角；元气/小恶魔属性；一张图一颗就够。', dia: detailSvg('fang') },
      { zh: '锁骨', en: 'collarbone', note: '颈肩交界三条线；露肩/夏装的特写落点。', dia: detailSvg('collarbone') },
      { zh: '后颈', en: 'nape', note: '发际线下的一小段：冷淡/性感的隐藏落点（nape 4.5K）。', dia: detailSvg('nape') },
      { zh: '汗珠', en: 'sweat', note: '圆珠+高光点+下滑痕；运动/紧张/夏天。', dia: detailSvg('sweat') },
      { zh: '手部结构', en: 'hand focus, detailed hands', note: '指节分层（三节）；手是崩坏重灾区，特写先小图。', dia: detailSvg('hands') },
      { zh: '绝对领域', en: 'zettai_ryouiki', note: '裙摆到袜口之间的一段（170K 大 tag）；裙摆与袜口都要写。', dia: detailSvg('zettai') },
      { zh: '衣物飘动', en: 'floating_clothes, fluttering skirt', note: '高光与褶皱同步变形；与风动发同向（16K）。', dia: detailSvg('clothmotion') },
      { zh: '布料褶皱', en: 'fabric folds, wrinkled clothes', note: '一切褶子指向受力点（肩/腰/肘）；褶子要少而准。', dia: detailSvg('folds') },
      { zh: '裸足', en: 'barefoot', note: '脚踝骨点+足弓线；落地必须有接触阴影。', dia: detailSvg('barefoot') },
      { zh: '长发发流', en: 'long hair flow, flowing strands', note: '女生发型主体：发流方向一致、发尾收弧；高光带顺发流走。', dia: detailSvg('hairflow') },
      { zh: '发饰', en: 'hair ornament, hairclip, hair ribbon', note: '发夹/缎带/发箍是女生第一配件；一件就够，别满头开花。', dia: detailSvg('hairacc') },
      { zh: '腿型与袜', en: 'thigh line, knee, sock top line', note: '膝点+袜口压痕+袜口弧；袜口别画成直线（贴腿才有痕）。', dia: detailSvg('legline') },
      { zh: '指尖与指甲', en: 'fingernails, nail polish', note: '甲面窄弧+甲缘线；裸甲/美甲按人设，手部特写才画。', dia: detailSvg('nails') }
    ]
  },
  {
    id: 'hair', title: '发型', sub: 'Hairstyles',
    tip: '发型是第一识别符（大锚：远距只认剪影）。三件套：轮廓（长短/体积）+ 走向（直/卷/流向）+ 刘海（齐/空气/斜/中分）。prompt 顺序：长短 + 样式 + 刘海 + 发色（long straight hair, blunt bangs, black hair）。剪影测试：纯黑填充、远距必须认得出是谁。与细节区联动（发丝高光/风动/湿发=「活」的加成）。',
    items: [
      { zh: '长直发', en: 'long hair, straight hair', note: '基准发型；侧幕垂到腰，末端平齐或收弧。fx 属此族。', dia: hairSvg('longstraight') },
      { zh: '姬发式', en: 'hime cut', note: '齐刘海+侧发齐（两颊齐颌短束）+后长发；古典/大小姐（32K）。', dia: hairSvg('himecut') },
      { zh: '双马尾', en: 'twintails', note: '对称双尾：元气/傲娇标配；发量要够、尾根位置定气质（高=活泼）。', dia: hairSvg('twintails') },
      { zh: '单马尾', en: 'ponytail, high ponytail', note: '高扎=元气/运动，低扎=文静；尾根一条弧线决定动势。', dia: hairSvg('ponytail') },
      { zh: '侧马尾', en: 'side ponytail, hair over one shoulder', note: '披肩一侧：温柔/邻家；注意与衣领的层次。', dia: hairSvg('sidetail') },
      { zh: '双麻花辫', en: 'twin braids, braid', note: '分段编织纹理（人字交叉）；辫子画「段」不画「线」。', dia: hairSvg('twinbraid') },
      { zh: '丸子头', en: 'hair bun', note: '顶扎圆髻：清爽；配碎发才不呆。', dia: hairSvg('bun') },
      { zh: '双丸子头', en: 'double bun', note: '对称双丸「天线」（179K 大 tag）；可爱/中国风。', dia: hairSvg('doublebun') },
      { zh: '波波头', en: 'bob cut', note: '齐颌弧线；内扣显乖、外翻显俏。', dia: hairSvg('bob') },
      { zh: '层次短发', en: 'short hair, layered hair', note: '发尾碎而不齐：中性/飒；层次方向一致。', dia: hairSvg('layered') },
      { zh: '长卷发', en: 'long hair, curly hair', note: '发尾螺旋收：甜美/大小姐；卷的数量控制，别画成弹簧。', dia: hairSvg('longcurls') },
      { zh: '大波浪', en: 'wavy hair', note: 'S 形帘幕：成熟/浪漫；波浪相位对齐才顺。', dia: hairSvg('waves') },
      { zh: '半扎发', en: 'half updo', note: '上半扎起+下半披（60K）：端庄又轻盈，礼服/日常通吃。', dia: hairSvg('halfupdo') },
      { zh: '齐刘海', en: 'blunt bangs', note: '一条硬平线：厚重/端正如 fx；压眉即压表情语义（注意）。', dia: hairSvg('blunt') },
      { zh: '空气刘海', en: 'see-through bangs', note: '透眉有缝：轻盈/年轻；缝隙均匀，别画成条形码。', dia: hairSvg('airbangs') },
      { zh: '斜刘海', en: 'swept bangs', note: '单向扫过（162K）：柔和/成熟；扫向与脸型互补（圆脸斜扫）。', dia: hairSvg('swept') },
      { zh: '中分', en: 'parted bangs, center part', note: '双帘露额（313K）：端正/成熟；中缝线必须落在鼻梁中线。', dia: hairSvg('parted') }
    ]
  },
  {
    id: 'clothdyn', title: '服装动态', sub: 'Cloth Dynamics',
    tip: '服装是「会动的第二剪影」。三个力：①重力（垂坠/滑落朝下）②风与运动（裙摆/飘带/围巾朝外）③贴体与离体（湿衣贴、坐裙堆）。写 prompt 配动态词：floating / fluttering / clinging / swaying / trailing。与姿态联动：跑=扬、坐=堆、抬手=滑。',
    items: [
      { zh: '奔跑裙扬', en: 'running, skirt flare, pleated skirt', note: '伞形张开+速度线；扬角与速度成正比。', dia: clothSvg('runflare') },
      { zh: '坐下裙堆', en: 'sitting, skirt spread on lap', note: '裙摆沿大腿摊开+垂褶；膝上裙的画法基准。', dia: clothSvg('seatedpool') },
      { zh: '抬手袖滑', en: 'sleeve slipping, arm up', note: '袖子顺重力滑向肘部；抬手必画。', dia: clothSvg('sleeveslip') },
      { zh: '领口松脱', en: 'open collar, unbuttoned shirt', note: '第一颗扣开着：随性/疲惫；仅此一处即可，别全身松。', dia: clothSvg('collar') },
      { zh: '领结飘动', en: 'bowtie, floating ribbon, wind', note: '飘带顺风（fx 红领结的动感版）；两条飘带别对称。', dia: clothSvg('tiefly') },
      { zh: '外套半脱', en: 'jacket off shoulder, single off shoulder', note: '单肩滑落（12.8K）：慵懒/收工感；肩线露一边。', dia: clothSvg('jacket') },
      { zh: '湿衣贴身', en: 'wet clothes, clinging clothes', note: '贴出轮廓+滴水（62K）；fx 端庄铁律：见水就压（不透）。', dia: clothSvg('wetcling') },
      { zh: '袜口松垮', en: 'loose socks', note: '堆出横向褶（22.8K）：生活感；配短裙/运动鞋。', dia: clothSvg('loosesock') },
      { zh: '裙摆掀起', en: 'skirt lift, wind from below', note: '风从下往上（95K）；台阶/天台场景常客。', dia: clothSvg('skirtlift') },
      { zh: '衣角翻起', en: 'untucked shirt, hem flip', note: '下摆离体翻卷：随手塞一半更自然。', dia: clothSvg('hemflip') },
      { zh: '纽扣紧绷', en: 'button strain, tight shirt', note: '拉扯横褶从纽扣放射；张力=真实感。', dia: clothSvg('buttonstrain') },
      { zh: '褶裙展开', en: 'pleated skirt, spread pleats', note: '走/坐时褶扇开（左闭右开对照）；褶数全程一致。', dia: clothSvg('pleats') },
      { zh: '袖口过长', en: 'sleeves past wrists', note: '只露指尖：萌系细节；毛衣/卫衣专属。', dia: clothSvg('longsleeve') },
      { zh: '围巾后飘', en: 'scarf trailing, floating scarf', note: '与运动方向相反拖出；三条飘带为一组。', dia: clothSvg('scarf') },
      { zh: '配饰荡动', en: 'belt chain, swaying accessory', note: '垂链/挂饰摆出弧线：动势的「余震」。', dia: clothSvg('chain') }
    ]
  },
  {
    id: 'body', title: '体型体态', sub: 'Body & Proportions',
    tip: '比例是角色的「骨架宪法」：先定量级（头身比/腿身比/肩宽/腰胯），再谈细节。年龄感先分三档——JS萝莉 / 小柄少女(JC中间档) / JK少女——先定档，再写比例与脸型词。体型语义：曲线=亲和、直线=疏离；体型 signature 立下后转面/动作只许强化不许改型（保形铁律）。比例词写在主体段（7 heads tall, slender, narrow shoulders）。默认二次元女生视角。',
    items: [
      { zh: '头身比', en: 'head-to-body ratio, 7 heads tall', note: '二次元 6-8 头身：少女 6.5-7、成人 7.5-8；fx=7（≈1.7m）。写整数比写「tall」有效。', dia: bodySvg('headratio') },
      { zh: '腿身比', en: 'leg-to-body ratio, long legs', note: '45-55% 决定长腿感；fx≈45% 已审计。要长腿写比例，不写形容词。', dia: bodySvg('legratio') },
      { zh: '肩宽比例', en: 'shoulder width, narrow shoulders', note: '标准 ≈2 头宽；窄肩=轻/少女，宽肩=强/飒。fx 削肩窄。（宽度以头宽为单位写）', dia: bodySvg('shoulderw') },
      { zh: '腰胯比', en: 'waist-hip ratio, narrow waist', note: '曲线（圆）=亲和，直线=疏离（与 character-design 体型语义同条）。', dia: bodySvg('waisthip') },
      { zh: '手臂比例', en: 'arm length, fingertips at mid-thigh', note: '指尖垂至大腿中=标准；手肘≈腰线（画动作时的手肘落点参考）。', dia: bodySvg('armratio') },
      { zh: '纤细型', en: 'slim, slender body', note: '直线剪影：冷淡/病弱/少年感；服装选型配垂坠直线。', dia: bodySvg('slim') },
      { zh: '丰满型', en: 'curvy, full figure', note: '圆线剪影：成熟/亲和；服装火力集中上装剪裁（别叠大裙摆压比例）。', dia: bodySvg('curvy') },
      { zh: '高挑型', en: 'tall, 8 heads tall', note: '8 头身+高腿长占比：气场/模特感；平视偏微低最显高。', dia: bodySvg('tall') },
      { zh: '娇小型', en: 'petite, small stature', note: '约 6 头身：可爱；机位配俯视 15° 内、别用仰视。', dia: bodySvg('petite') },
      { zh: '削肩', en: 'sloping shoulders', note: '肩线下滑：轻、弱、柔；fx 保形项，转面不许改平。', dia: bodySvg('slope') },
      { zh: '直角肩', en: 'straight shoulders, square shoulders', note: '肩线水平外扩：气场强，西装/制服最吃这种肩。', dia: bodySvg('square') },
      { zh: '挺拔', en: 'upright posture, straight back', note: '耳-肩-髋一线：军姿/大小姐；栏杆式站姿的底子。', dia: bodySvg('upright') },
      { zh: '含胸弓背', en: 'slouched posture, rounded back', note: '脊柱 C 形：内向/疲惫/自卑（内向=隐藏逻辑的身体侧）。', dia: bodySvg('slouch') },
      { zh: '头颈前倾', en: 'forward head posture', note: '头落在肩线前方：伏案/手机族/疲惫；配「低头抬眼」极有戏。', dia: bodySvg('headfwd') },
      { zh: '年龄感三档（JS/小柄/JK）', en: 'age feel tiers: loli (JS) / petite teen (JC) / JK', note: '先定档再定细节：JS萝莉 5~5.5头身·肩~1.5头宽；小柄少女（JC≈中间档）≈6头身·肩1.8~2.0·平胸细四肢（成人小柄=此档，如绝区零 千夏 154cm）；JK 6.5~7头身·肩~2.2。头身比写整数最稳，别用模糊形容词硬碰。', dia: bodySvg('agetier') },
      { zh: '小柄少女描述法（中间档）', en: 'petite young woman, youthful but not childlike', note: '自然语言句（偏幼侧校准版）：petite teenage girl with a very youthful JC-like build, about 154cm, 6-head proportions, full soft cheeks with slight baby fat, small rounded chin, short lower face, very large round eyes with tall iris, small flat chest, slim limbs。标签式：petite, flat chest, small breasts, slender。护栏（negative）：child / grade schooler proportions / toddler / tall mature physique / mature face / long face / sharp jawline。偏幼信号：baby fat、small round chin、short lower face、tall iris；偏熟信号（往回收就删）：elongated eyes、gentle chin line、delicate chin。禁写具体角色名——借比例不借特征，防版权脸与配色污染（二创融合铁律）。', dia: bodySvg('ageface') }
    ]
  },
  {
    id: 'light', title: '光影', sub: 'Lighting',
    tip: '光影属 STEP5。此处只画光位与光比示意；色彩搭配查 `palette.html`。写 prompt 铁律：一个主光（+可选辅助），光源位置写清楚（from upper left / from the window），别多主光。',
    items: [
      { zh: '顺光', en: 'front light, flat even lighting', note: '无影平铺、最清晰——设定图/验证结构用；氛围弱，成品图慎单独用。', dia: lightSvg('front') },
      { zh: '侧光', en: 'side light, half-lit face', note: '立体感最强：半亮半暗；脸型缺点会暴露，美女图慎全侧。', dia: lightSvg('side') },
      { zh: '伦勃朗光', en: 'rembrandt lighting, triangle of light on the cheek', note: '人像经典；颊部三角亮斑是关键词，写 triangle of light on the cheek。', dia: lightSvg('rembrandt') },
      { zh: '逆光', en: 'backlight, silhouette, glowing hair rim', note: '剪影+发丝光；想保脸就别全逆，写 backlight with rim light on hair。', dia: lightSvg('back') },
      { zh: '轮廓光', en: 'rim light, edge light separating from background', note: '与逆光的区别：只勾边不翻脸；STEP5 给暗背景主体勾边的关键工具。', dia: lightSvg('rim') },
      { zh: '顶光', en: 'top light, shadowed eye sockets', note: '眼窝影+鼻下影：压抑/神秘；动漫里配「低头抬眼」极凶。', dia: lightSvg('top') },
      { zh: '底光', en: 'bottom light, underlighting', note: '恐怖/诡异/反派光；所有阴影翻面，气氛立刻不对。', dia: lightSvg('bottom') },
      { zh: '蝴蝶光', en: 'butterfly lighting, soft shadow under the nose', note: '高位正面+鼻下小蝶影；美人光，脸蛋显瘦。', dia: lightSvg('butterfly') },
      { zh: '三点布光', en: 'three-point lighting, key light, fill light, rim light', note: '影棚标准：主光定影+补光提暗部+轮廓光剥离；写 prompt 时三者分开写。', dia: lightSvg('three') },
      { zh: '高调', en: 'high key lighting, bright and airy', note: '亮多暗少：清爽/温柔/日常/治愈。', dia: lightSvg('highkey') },
      { zh: '低调', en: 'low key lighting, deep shadows', note: '暗多亮少+小面积亮：压抑/神秘/电影感；必配轮廓光才看得清轮廓。', dia: lightSvg('lowkey') },
      { zh: '硬光 / 柔光', en: 'hard light, crisp shadow edge / soft light, feathered shadow edge', note: '硬光=影缘清晰（戏剧性/硬朗）；柔光=影缘羽化（柔和/人像）。动漫图默认保险=soft light。', dia: lightSvg('hardsoft') },
      { zh: '体积光', en: 'volumetric light, god rays, light shafts through the air', note: '光束穿过空气（窗/雾/尘）氛围神器；写 god rays 或 volumetric light。', dia: lightSvg('volumetric') },
      { zh: '黄金时刻', en: 'golden hour, warm low-angle sunlight, long shadows', note: '低角度暖橙光+长影：温暖/回忆/黄昏；golden hour 是最通用氛围词之一。', dia: lightSvg('golden') },
      { zh: '蓝调时刻', en: 'blue hour, cool ambient twilight', note: '傍晚/清晨的冷蓝余光：安静/忧郁/夜戏开场。', dia: lightSvg('blue') },
      { zh: '窗光', en: 'window light, soft directional light from a window', note: '室内主力光：单侧柔光+窗形光斑；写 soft window light from the left 即得。', dia: lightSvg('window') },
      { zh: '斑驳树影', en: 'dappled light, sunlight through leaves', note: '叶隙光斑：夏日/公园/窗边绿植；光斑落在脸与衣上要写「不遮眼」。', dia: lightSvg('dapple') },
      { zh: '条纹光', en: 'striped light, venetian blind shadows', note: '百叶窗条纹：室内戏剧感/审讯感；条纹横过脸控制在 2-3 条最好。', dia: lightSvg('blind') },
      { zh: '湿润反光', en: 'wet ground reflections, rain reflections', note: '湿地面倒映灯光（雨夜街核心质感）；写 wet asphalt / wet pavement。', dia: lightSvg('wet') }
    ]
  },
  {
    id: 'story', title: '叙事与活感', sub: 'Narrative & Liveness',
    tip: '活感公式 = 动作瞬间 + 一个残响 + 一次环境接触 + 一个画外指向 + 情绪词≤1。死画面=摆拍展示（对称、静止、正确）；活画面=时间中的一帧（进行中、未完成、有痕迹）。三招：①动词换名词（mid-stride 而非 standing）②加残响层（still swaying / steam rising）③情绪写行为不写标签（tearing up but smiling > sad）。',
    items: [
      { zh: '故事瞬间', en: 'mid-action moment, caught in the middle of', note: '动作进行中的一帧（mid-stride/mid-turn）；「正要」比「已经」活。', dia: storySvg('midmoment') },
      { zh: '动作残响', en: 'still swaying, steam still rising, half-open', note: '刚发生的事留下的痕：晃动的杯/未散的热气/半开的门。', dia: storySvg('aftermath') },
      { zh: '画外暗示', en: 'looking at something off-screen, reacting to a sound', note: '故事在画外：看向框外/被看着/画外来光；观众自动补全叙事。', dia: storySvg('offscreen') },
      { zh: '环境接触', en: 'palm against the glass, brushing rain off the sleeve', note: '身体与世界的物理接触（贴玻璃/踩水/掀帘）；接触即真实。', dia: storySvg('touch') },
      { zh: '微动作', en: 'gripping the strap, tugging the sock, holding the skirt hem', note: '小动作=状态翻译器：捏裙角=紧张，攥包带=戒备。', dia: storySvg('micro') },
      { zh: '情绪矛盾', en: 'tearing up but smiling, biting back words', note: '嘴说一套身体说一套：笑着流泪/咬牙的平静；张力=活着。', dia: storySvg('contradict') },
      { zh: '道具叙事', en: 'worn bag, patched strap, rusted charm', note: '道具带「使用痕迹」：补丁/磨损/胶带/旧挂坠=人生轨迹。', dia: storySvg('prop') },
      { zh: '不完美', en: 'crooked bowtie, loose strand, slipping sock', note: '完美=AI 感：歪领结/散出一缕/袜口下滑，一处即可。', dia: storySvg('imperfect') },
      { zh: '视线逻辑', en: 'gaze logic, looking off-screen / at camera / at her own hands', note: '看画外=有故事；看镜头=对话；看物件/手=内省；闭眼=感受。', dia: storySvg('gazelogic') },
      { zh: '时间痕迹', en: 'traces of time, fading light, falling leaf', note: '「这一刻正在流逝」：长影/落叶/将尽的黄昏/蜡烛将熄。', dia: storySvg('time') },
      { zh: '环境情绪', en: 'pathetic fallacy, rain matching her mood', note: '天气与情绪共振（雨=低落）；反用更高级（雨里的一盏暖灯）。', dia: storySvg('moodweather') },
      { zh: '物理痕迹', en: 'footprints, ripples, pressed imprint', note: '脚印/涟漪/压痕=「刚经过」的证据；比人物本身更早讲故事。', dia: storySvg('physicstrace') },
      { zh: '关系叙事', en: 'distance and direction telling the story', note: '距离+朝向+中间物=关系说明（呼应二人互动区）。', dia: storySvg('relationship') }
    ]
  }
];

const QUICK: string[][] = [
  ['压迫 · 被堵 · 弱小', 'from above, high angle looking down ~30° + bust shot', '配眼带影更狠'],
  ['权力反转 · 威慑', 'from below, low angle looking up + close-up', 'JK 题材慎用'],
  ['失衡 · 不安', 'from above ~15-30° + dutch angle ~15°', '平视+斜切禁用'],
  ['平等 · 最稳', 'eye-level, straight-on, zero tilt zero dutch + upper body', '零斜切写死'],
  ['孤独 · 留白', 'wide shot + rule of space + negative space', '留白里写出内容'],
  ['对峙 · 对推', 'eye-level + centered composition + leading lines', '视线留白不放道具'],
  ['旁观 · 代入', 'over-the-shoulder / pov, first-person view', 'POV 配手部透视'],
  ['纵深 · 空间感', 'wide angle + leading lines + foreshortening', '近大远小明确'],
  ['回眸 · 关系', '3/4 back view + bust shot', '背影+侧脸同框'],
  ['巨大感 · 足下', 'ground-level shot, camera on the ground + lower body focus', '靴鞋/裙摆特写'],
  ['被观察 · 冷漠', 'surveillance camera view + high angle looking down ~45°', '配广角更冷']
];

/* 姿态 → 机位速查 */
const POSECAM: string[][] = [
  ['中正站姿', 'eye-level + full body / cowboy shot', '设定图 / 保形基准'],
  ['S 站姿', '3/4 view + eye-level', 'S 线在侧向最立体'],
  ['环胸', 'front view + bust shot', '双臂天然三角'],
  ['叉腰', 'from below ~15° 或 eye-level', '仰一点气势更足'],
  ['靠墙', 'eye-level + 竖缝居中', '墙角=天然框'],
  ['回眸', '3/4 back view + rule of space', '视线留白必写'],
  ['蹲姿抱膝', 'from above ~30-45° + negative space', '收缩体态配俯视'],
  ['鸭子坐', 'eye-level 或 from above ~15°', '俯角展示坐姿全貌'],
  ['椅子端坐 / 翘腿', 'eye-level + 中景', '翘腿注意交叠透视'],
  ['奔跑', 'profile + lead room；或贴地 + 斜切', '两种方案按情绪选'],
  ['伸手向镜头', 'front view + foreshortening', '手大身小'],
  ['枕臂侧躺', "from above ~45° 或 bird's eye", '身体走横线'],
  ['双人对峙', 'two-shot + eye-level + 180 度线', '左右+朝向写死'],
  ['背对背', 'eye-level + 对称 + 双人同框', '剪影连成一块']
];

const TOOLS: string[][] = [
  ['半身防裁切（正句）', 'entire head in frame with margin above hair', '半身/特写必带，防头顶裁切'],
  ['半身防裁切 negative', 'cropped head, cropped chin', '与正句配对使用'],
  ['全身防裁切 negative', 'cropped feet, cut off feet', '全身/远景用'],
  ['斜切保险句', 'zero tilt zero dutch', '平视求稳时写死，防模型自作主张斜切'],
  ['垫图机位锁', 'same camera angle and composition as the reference image', '垫姿态图/透视底时用'],
  ['空房白膜 negative', 'empty room without figure, wrong camera angle, color, detailed bricks, rain, puddle, neon, pipes, doors, furniture, dramatic lighting', '透视底/背景板常驻'],
  ['完整机位句示例', 'from above, high angle looking down ~30°, dutch angle ~15°, bust shot cropped at mid-torso, entire head in frame', 'fx A01 实际组合，可直接套']
];

/* 词表式用例（tag 模型的拼法） */
const EX: Record<string, string> = {
  'extreme close-up, face focus': 'extreme close-up, face focus, eyes brimming with tears',
  'close-up': 'close-up, soft smile, slight blush',
  'portrait, head and shoulders': 'portrait, head and shoulders, gentle gaze',
  'bust shot cropped at mid-torso': 'bust shot cropped at mid-torso, arms crossed, school blazer',
  'cowboy shot': 'cowboy shot, hands in pockets, pleated skirt',
  'full body': 'full body, standing, arms at sides, black loafers',
  'wide shot, full body with empty space': 'wide shot, tiny figure in a vast snowy field',
  'extreme wide shot, establishing shot': 'extreme wide shot, establishing shot, small figure on a ridge',
  'lower body focus, thighs to shoes in frame': 'lower body focus, skirt hem at top of frame, black pantyhose, loafers',
  'eye-level, straight-on, zero tilt zero dutch': 'eye-level, straight-on, zero tilt zero dutch, talking to viewer',
  'from above, high angle looking down ~15°': 'from above, high angle looking down ~15°, standing on the street',
  'from above, high angle looking down ~30°': 'from above, high angle looking down ~30°, looking up at viewer',
  'from above, high angle looking down ~45°': 'from above, high angle looking down ~45°, sitting on the stairs',
  "from directly above, bird's eye view, top-down": "from directly above, bird's eye view, lying on the floor",
  'from below, low angle looking up ~15°': 'from below, low angle looking up ~15°, chest-level camera, confident',
  'from below, low angle looking up': 'from below, low angle looking up, towering presence',
  'ground-level shot, camera on the ground': 'ground-level shot, camera on the ground, boots in the foreground',
  "from directly below, worm's eye view": "from directly below, worm's eye view, towering over the camera",
  'front view, straight-on': 'front view, straight-on, eye contact',
  '3/4 view': '3/4 view, turned slightly, looking at viewer',
  'profile, side view': 'profile, side view, wind blowing through hair',
  'from behind, rear view': 'from behind, rear view, walking away',
  '3/4 back view, from behind at 45°': '3/4 back view, looking back over shoulder',
  'over-the-shoulder': 'over-the-shoulder, foreground shoulder blurred',
  'pov, first-person view': 'pov, first-person view, own hand reaching forward',
  'dutch angle ~15°': 'dutch angle ~15°, uneasy atmosphere',
  'dutch angle ~30-45°': 'dutch angle ~35°, psychological collapse',
  'wide angle, 24mm, exaggerated perspective': 'wide angle, 24mm, exaggerated perspective, room stretching',
  'standard lens, 50mm': 'standard lens, 50mm, natural proportions',
  'portrait lens, 85mm, shallow depth of field': 'portrait lens, 85mm, shallow depth of field, soft bokeh',
  'telephoto, 135mm, compressed background, blurry background': 'telephoto, 135mm, compressed background, blurred city lights',
  'fisheye lens': 'fisheye lens, curved horizon',
  'foreshortening': 'foreshortening, hand reaching toward the camera',
  'one-point perspective': 'one-point perspective, long corridor, vanishing point ahead',
  'two-point perspective': 'two-point perspective, street corner, walls receding both ways',
  'three-point perspective': 'three-point perspective, looking up at a skyscraper',
  'rule of thirds': 'rule of thirds, eyes on the upper-left intersection',
  'triangle composition': 'triangle composition, hands on hips, stable stance',
  'rule of space, looking into empty space': 'rule of space, looking off-screen to the right',
  'negative space, empty space in front': 'negative space, tiny figure, vast empty sky',
  'leading lines': 'leading lines, corner seam converging behind the head',
  'symmetrical composition': 'symmetrical composition, centered between mirrored walls',
  'frame in frame': 'frame in frame, seen through a doorway',
  'centered composition, subject on center line': 'centered composition, subject on the center line, facing viewer',
  'diagonal composition': 'diagonal composition, motion along the diagonal',
  'golden ratio, golden spiral': 'golden ratio, face on the 0.618 point',
  'S-curve composition': 'S-curve composition, winding path leading to the figure',
  'foreground occlusion, depth layering': 'foreground occlusion, blurred railing covering one corner',
  'reflection, mirror composition': 'reflection in the rain puddle, mirrored figure',
  'repetition, pattern, rhythm': 'repetition, rows of windows, one lit differently',
  'two-shot': 'two-shot, two girls facing each other',
  'surveillance camera view, cctv angle, security camera': 'surveillance camera view, cctv angle, wide coverage of the room',
  'selfie, arm extended toward camera': 'selfie, arm extended, phone close to the lens',
  'view through a window, looking in through the frame': 'view through a window, looking in from outside, rain on the glass',
  'shoulder-level shot': 'shoulder-level shot, conversation across a desk',
  'hip-level shot, camera at waist height': 'hip-level shot, camera at waist height, quiet confrontation',
  'knee-level shot': 'knee-level shot, looking up slightly, looming presence',
  'aerial shot, high above the ground': 'aerial shot, high above the ground, the city small below',
  'large-to-small flow': 'large-to-small flow, biggest shape leading toward the subject',
  'density contrast': 'density contrast, one gap inside a dense pattern',
  'visual balance': 'visual balance, large shape offset by a cluster of small ones',
  'contrast': 'contrast, bright subject against a dark field',
  'claustrophobic framing, tight crop': 'claustrophobic framing, the frame closing in on all sides',
  '3:4 portrait aspect ratio': '3:4 portrait aspect ratio, full body',
  '4:5 portrait aspect ratio': '4:5 portrait aspect ratio, bust shot',
  '16:9 landscape aspect ratio': '16:9 landscape aspect ratio, wide scenery',
  '1:1 square aspect ratio': '1:1 square aspect ratio, centered portrait',
  '180-degree line, keep the camera on one side': 'two girls talking, both cameras on one side of the 180-degree line',
  'reverse shot': 'reverse shot, A looking at B, then B looking back',
  'eyeline match': 'eyeline match, gaze off-screen right matched by the reverse',
  '30-degree rule': '30-degree rule, new camera position at least 30 degrees around',
  'headroom': 'headroom, a little air above the hair',
  'lead room, space in the direction of movement': 'lead room, empty space ahead of her running direction',
  'front light, flat even lighting': 'front light, flat even lighting, reference sheet look',
  'side light, half-lit face': 'side light, half-lit face, dramatic contrast',
  'rembrandt lighting, triangle of light on the cheek': 'rembrandt lighting, triangle of light on the cheek',
  'backlight, silhouette, glowing hair rim': 'backlight, silhouette, glowing hair rim',
  'rim light, edge light separating from background': 'rim light, edge light separating her from the background',
  'top light, shadowed eye sockets': 'top light, shadowed eye sockets, oppressive mood',
  'bottom light, underlighting': 'bottom light, underlighting, eerie mood',
  'butterfly lighting, soft shadow under the nose': 'butterfly lighting, soft shadow under the nose',
  'three-point lighting, key light, fill light, rim light': 'three-point lighting, key light, fill light, rim light',
  'high key lighting, bright and airy': 'high key lighting, bright and airy, soft shadows',
  'low key lighting, deep shadows': 'low key lighting, deep shadows, single light source',
  'hard light, crisp shadow edge / soft light, feathered shadow edge': 'soft light, feathered shadow edge',
  'volumetric light, god rays, light shafts through the air': 'volumetric light, god rays through the window dust',
  'golden hour, warm low-angle sunlight, long shadows': 'golden hour, warm low-angle sunlight, long shadows',
  'blue hour, cool ambient twilight': 'blue hour, cool ambient twilight',
  'window light, soft directional light from a window': 'window light, soft directional light from the left',
  'shallow depth of field': 'shallow depth of field, subject in focus, background blurred',
  'deep focus, everything sharp': 'deep focus, foreground and background all sharp',
  'bokeh, out-of-focus light circles': 'bokeh, soft out-of-focus light circles',
  'dappled light, sunlight through leaves': 'dappled light, sunlight through leaves on her face',
  'striped light, venetian blind shadows': 'striped light, venetian blind shadows across the room',
  'wet ground reflections, rain reflections': 'wet ground reflections, city lights mirrored on the pavement',
  'standing, arms at sides, closed legs': 'standing, arms at sides, closed legs, facing viewer',
  'contrapposto, weight on one leg': 'contrapposto, weight on one leg, hand on hip',
  'crossed arms': 'crossed arms, cold gaze',
  'hands on hips': 'hands on hips, confident',
  'hand in pocket': 'hand in pocket, casual',
  'against_wall, leaning back': 'against_wall, leaning back, arms at sides',
  'looking back, turning around': 'looking back, turning around, from behind',
  'walking': 'walking, motion, casual',
  'running, running towards viewer': 'running towards viewer, motion, floating hair',
  'reaching towards viewer, outstretched arm, foreshortening': 'reaching towards viewer, outstretched arm, foreshortening',
  'squatting, hugging own legs': 'squatting, hugging own legs, knees up',
  'wariza': 'wariza, sitting, on floor',
  'sitting on chair, knees together, hands on lap': 'sitting on chair, knees together, hands on lap',
  'sitting on chair, crossed legs': 'sitting on chair, crossed legs, hand on knee',
  'kneeling, one knee down': 'kneeling, one knee down, on one knee',
  'lying, on side, head on arm': 'lying, on side, head on arm, relaxed',
  'hand on cheek, elbow on table': 'hand on cheek, elbow on table',
  'hand in hair, adjusting hair': 'hand in hair, adjusting hair, looking away',
  'back to back, two people standing': 'back to back, two people, standing, trust',
  'holding hands, two people facing each other': 'holding hands, two people facing each other',
  'walking side by side, two people, same direction': 'two people walking side by side, same direction',
  'two people facing each other, distance between them': 'two people facing each other, distance between them',
  'hugging, two people, arms around back': 'hugging, arms around back, head on shoulder',
  'head on shoulder, leaning, two people': 'head on shoulder, two people, leaning',
  'height difference, tall and short, two people': 'height difference, tall and short, two people',
  'princess carry, carrying, two people': 'princess carry, carrying, two people',
  'piggyback, two people, legs around waist': 'piggyback, legs around waist, arms over shoulders',
  'two people, one in foreground out of focus, one behind': 'two people, foreground figure out of focus, subject behind',
  'expressionless, closed mouth': 'expressionless, closed mouth, stoic',
  'smile, gentle smile': 'smile, gentle smile, closed mouth',
  'grin, open mouth, teeth': 'grin, open mouth, teeth, happy',
  'laughing, open mouth, closed eyes': 'laughing, open mouth, closed eyes',
  'jitome, half-closed eyes': 'jitome, half-closed eyes, unimpressed',
  'angry, frown, furrowed brow': 'angry, frown, furrowed brow, glaring',
  'pout': 'pout, blush',
  'surprised, wide-eyed, open mouth': 'surprised, wide-eyed, open mouth',
  'blush, embarrassed': 'blush, embarrassed, averting eyes',
  'teary eyes, tears': 'teary eyes, tears, trembling',
  'crying, streaming tears, open mouth': 'crying, streaming tears, open mouth',
  'smug, smirk, half-closed eyes': 'smug, smirk, half-closed eyes',
  'looking down, jitome, half-closed eyes': 'looking down, jitome, half-closed eyes, condescending',
  'glaring, staring, eye contact': 'glaring, staring, eye contact, serious',
  'wink, one eye closed': 'wink, one eye closed, smile',
  'sweatdrop, nervous': 'sweatdrop, nervous, blank stare',
  'gritted teeth, angry': 'gritted teeth, angry, clenched',
  'closed eyes, serene': 'closed eyes, serene, calm',
  'shiny hair, hair highlights': 'shiny hair, hair highlights, glossy strands',
  'windblown hair, floating hair': 'windblown hair, floating hair, wind',
  'wet hair, damp hair': 'wet hair, damp hair, hair clinging to face',
  'ahoge': 'ahoge, single strand sticking up',
  'eyelashes, long eyelashes': 'long eyelashes, lower lashes, detailed eyes',
  'shiny eyes, catchlight': 'shiny eyes, catchlight, eye highlight',
  'eye makeup, eyeliner, eyeshadow': 'eye makeup, eyeliner, subtle eyeshadow',
  'fang': 'fang, open mouth, grin',
  'collarbone': 'collarbone, bare shoulders',
  'nape': 'nape, hair up, back of neck',
  'sweat': 'sweat, glistening skin, after training',
  'hand focus, detailed hands': 'hand focus, detailed hands, delicate fingers',
  'zettai_ryouiki': 'zettai ryouiki, thighhighs, pleated skirt',
  'floating_clothes, fluttering skirt': 'floating clothes, fluttering skirt, wind',
  'fabric folds, wrinkled clothes': 'fabric folds, clothing wrinkles, tension lines',
  'barefoot': 'barefoot, bare feet, on tiptoes',
  'long hair flow, flowing strands': 'long hair, flowing strands, smooth hair flow',
  'hair ornament, hairclip, hair ribbon': 'hair ribbon, hairclip, hair ornament',
  'thigh line, knee, sock top line': 'thigh line, knee, sock top line, standing',
  'fingernails, nail polish': 'fingernails, nail polish, hand focus',
  'head-to-body ratio, 7 heads tall': '7 heads tall, balanced proportions',
  'leg-to-body ratio, long legs': 'long legs, high leg-to-body ratio',
  'shoulder width, narrow shoulders': 'narrow shoulders, 2 heads wide',
  'waist-hip ratio, narrow waist': 'narrow waist, soft hip curve',
  'arm length, fingertips at mid-thigh': 'fingertips at mid-thigh, natural arm length',
  'slim, slender body': 'slim, slender, straight silhouette',
  'curvy, full figure': 'curvy, full figure, soft curves',
  'tall, 8 heads tall': '8 heads tall, long-legged, tall',
  'petite, small stature': 'petite, small stature, 6 heads tall',
  'sloping shoulders': 'sloping shoulders, soft shoulder line',
  'straight shoulders, square shoulders': 'straight shoulders, square shoulder line',
  'upright posture, straight back': 'upright posture, straight back, poised',
  'slouched posture, rounded back': 'slouched posture, rounded back, tired',
  'forward head posture': 'forward head, looking down, tired',
  'long hair, straight hair': 'long straight hair, black hair, blunt bangs',
  'hime cut': 'hime cut, blunt bangs, sidelocks',
  'twintails': 'twintails, hair ribbon',
  'ponytail, high ponytail': 'high ponytail, hair blowing',
  'side ponytail, hair over one shoulder': 'side ponytail, hair over one shoulder',
  'twin braids, braid': 'twin braids, braided hair',
  'hair bun': 'hair bun, loose strands',
  'double bun': 'double bun, hair rings',
  'bob cut': 'bob cut, chin-length hair',
  'short hair, layered hair': 'short layered hair, choppy ends',
  'long hair, curly hair': 'long curly hair, spiral ends',
  'wavy hair': 'long wavy hair',
  'half updo': 'half updo, hair ribbon',
  'blunt bangs': 'blunt bangs, straight bangs',
  'see-through bangs': 'see-through bangs, thin bangs',
  'swept bangs': 'swept bangs, side bangs',
  'parted bangs, center part': 'parted bangs, center part, forehead exposed',
  'running, skirt flare, pleated skirt': 'running, skirt flare, motion',
  'sitting, skirt spread on lap': 'sitting, skirt spread on lap, knees together',
  'sleeve slipping, arm up': 'arm up, sleeve slipping, reaching',
  'open collar, unbuttoned shirt': 'open collar, unbuttoned shirt, loose necktie',
  'bowtie, floating ribbon, wind': 'bowtie, floating ribbon, wind',
  'jacket off shoulder, single off shoulder': 'jacket off shoulder, blazer slipping',
  'wet clothes, clinging clothes': 'wet clothes, clinging shirt, rain',
  'loose socks': 'loose socks, short skirt, sneakers',
  'skirt lift, wind from below': 'skirt lift, gust of wind',
  'untucked shirt, hem flip': 'untucked shirt, hem flip, casual',
  'button strain, tight shirt': 'button strain, tight shirt',
  'pleated skirt, spread pleats': 'pleated skirt, spread pleats, motion',
  'sleeves past wrists': 'sleeves past wrists, sweater',
  'scarf trailing, floating scarf': 'scarf trailing, floating scarf, wind',
  'belt chain, swaying accessory': 'belt chain, swaying charms',
  'mid-action moment, caught in the middle of': 'caught mid-stride, hair still moving',
  'still swaying, steam still rising, half-open': 'steam still rising, cup still swaying',
  'looking at something off-screen, reacting to a sound': 'reacting to something off-screen',
  'palm against the glass, brushing rain off the sleeve': 'palm pressed against the glass',
  'gripping the strap, tugging the sock, holding the skirt hem': 'gripping the bag strap tightly',
  'tearing up but smiling, biting back words': 'smiling with tears welling up',
  'worn bag, patched strap, rusted charm': 'worn bag with a patched strap',
  'crooked bowtie, loose strand, slipping sock': 'slightly crooked bowtie, one loose strand',
  'gaze logic, looking off-screen / at camera / at her own hands': 'looking off-screen, gaze leading out of frame',
  'traces of time, fading light, falling leaf': 'long shadows, a falling leaf, fading light',
  'pathetic fallacy, rain matching her mood': 'rain matching her low mood, one warm lamp',
  'footprints, ripples, pressed imprint': 'footprints in the wet ground, ripples spreading',
  'distance and direction telling the story': 'a gap between them, an item left between'
};

/* 自然语言式（一句话把画面说出来） */
const NL: Record<string, NlWord> = {
  'extreme close-up, face focus': { en: 'The frame holds only her eyes, nothing else in sight.', cn: '画面里只有她的眼睛，别的什么都不入框。' },
  'close-up': { en: 'Her face fills the whole frame, every expression readable.', cn: '整张脸占满画面，表情一览无余。' },
  'portrait, head and shoulders': { en: 'She is framed from the chest up, head and shoulders inside the picture.', cn: '胸部以上入框，头和肩都在画面里。' },
  'bust shot cropped at mid-torso': { en: 'The image cuts her at the middle of her chest, hands still in frame.', cn: '画面裁到胸口中部，手还在框里。' },
  'cowboy shot': { en: 'She is visible down to the middle of her thighs.', cn: '拍到大腿中部，腰间细节都在框里。' },
  'full body': { en: 'Her whole body is inside the frame, head to shoes.', cn: '从头到脚整个人都在画面里。' },
  'wide shot, full body with empty space': { en: 'She stands small in a wide space, much of the frame left empty.', cn: '人小小地站在开阔空间里，大片画面留空。' },
  'extreme wide shot, establishing shot': { en: 'The landscape dwarfs her and she is a tiny figure far away.', cn: '环境把她衬得很小，人影只是远处的一点。' },
  'lower body focus, thighs to shoes in frame': { en: 'Only her lower half is shown: skirt, legs and shoes.', cn: '只拍她的下半身：裙摆、腿和鞋。' },
  'eye-level, straight-on, zero tilt zero dutch': { en: 'The camera sits at her eye height, looking straight at her.', cn: '镜头和她的眼睛一样高，正对着她。' },
  'from above, high angle looking down ~15°': { en: 'The camera looks down at her from slightly above, a gentle downward tilt.', cn: '镜头略高于她，轻轻向下俯视。' },
  'from above, high angle looking down ~30°': { en: 'The camera is clearly above her, around thirty degrees down.', cn: '镜头明显高于她，约三十度向下看。' },
  'from above, high angle looking down ~45°': { en: 'The camera looks steeply down, almost over the top of her head.', cn: '镜头陡峭地往下看，几乎越过她头顶。' },
  "from directly above, bird's eye view, top-down": { en: 'The camera is directly overhead, looking straight down.', cn: '镜头在正上方，垂直往下拍。' },
  'from below, low angle looking up ~15°': { en: 'The camera sits at her chest height, lifting slightly upward.', cn: '镜头在胸口高度，微微向上仰。' },
  'from below, low angle looking up': { en: 'The camera is below her and looks up.', cn: '镜头在下方，朝上看她。' },
  'ground-level shot, camera on the ground': { en: 'The camera rests on the ground and shoots up from floor level.', cn: '镜头贴在地面上，从地面向上拍。' },
  "from directly below, worm's eye view": { en: 'The camera looks straight up from below her, a towering effect.', cn: '镜头从正下方垂直仰望，压迫感拉满。' },
  'front view, straight-on': { en: 'She faces the camera straight on.', cn: '她正面对着镜头。' },
  '3/4 view': { en: 'She is turned slightly, about forty-five degrees from the camera.', cn: '她侧过一点身子，与镜头约成四十五度。' },
  'profile, side view': { en: 'The camera catches her from the exact side, face in profile.', cn: '镜头从正侧方拍她，只有侧脸轮廓。' },
  'from behind, rear view': { en: 'The camera watches her from behind as she walks away.', cn: '镜头从背后看她离去。' },
  '3/4 back view, from behind at 45°': { en: 'She is seen from behind at an angle, head turning back toward the camera.', cn: '从斜后方看她，头正转回来。' },
  'over-the-shoulder': { en: 'The frame looks past a shoulder in the foreground at her.', cn: '越过前景的肩膀看向她。' },
  'pov, first-person view': { en: 'We see through her own eyes, her hands in front of us.', cn: '视角就是她的眼睛，她的手就在画面里。' },
  'dutch angle ~15°': { en: 'The frame is tilted about fifteen degrees and the horizon runs diagonally.', cn: '画面倾斜约十五度，地平线变成斜线。' },
  'dutch angle ~30-45°': { en: 'The whole image is rotated heavily and the world leans.', cn: '整张图大幅旋转，整个世界都歪了。' },
  'wide angle, 24mm, exaggerated perspective': { en: 'A wide lens stretches the depth: near things grow, far things shrink.', cn: '广角把透视拉开：近处变大，远处缩小。' },
  'standard lens, 50mm': { en: 'The lens sees the scene the way a human eye does.', cn: '镜头所见接近人眼所见。' },
  'portrait lens, 85mm, shallow depth of field': { en: 'The background begins to melt away behind her.', cn: '背景在她身后开始虚化。' },
  'telephoto, 135mm, compressed background, blurry background': { en: 'The background is pulled closer and blurred into color patches.', cn: '背景被拉近、糊成色块。' },
  'fisheye lens': { en: 'Everything bends around the edges, even the horizon curves.', cn: '画面边缘强烈弯曲，连地平线都是弧的。' },
  'foreshortening': { en: 'Her hand reaches toward the lens and looks huge compared with her body.', cn: '她的手伸向镜头，近大远小到夸张。' },
  'one-point perspective': { en: 'All lines run to a single point straight ahead.', cn: '所有线条收束到正前方的一个点。' },
  'two-point perspective': { en: 'Two sets of lines recede left and right from the corner.', cn: '两组线条从墙角分别向左右收。' },
  'three-point perspective': { en: 'As we look up, the verticals of the tower converge overhead.', cn: '仰看时，高塔的垂直线在头顶收束。' },
  'rule of thirds': { en: 'Her eyes sit on the upper intersection and the horizon on the lower third line.', cn: '眼睛压在上方交点，地平线压在下三分线。' },
  'triangle composition': { en: 'Her arms and feet form a stable triangle.', cn: '手臂和双脚构成一个稳定的三角。' },
  'rule of space, looking into empty space': { en: 'Empty space opens in the direction she looks.', cn: '她看的方向留着空白。' },
  'negative space, empty space in front': { en: 'Most of the frame is empty, and that emptiness is the point.', cn: '画面大部分是空的，空本身就是内容。' },
  'leading lines': { en: 'The corner lines guide the eye from the ground up to her face.', cn: '角线把视线从地面一路引到她脸上。' },
  'symmetrical composition': { en: 'The walls mirror each other and she stands dead center.', cn: '两面墙完全对称，她站在正中。' },
  'frame in frame': { en: 'She is seen through a doorway, the frame around her.', cn: '透过一道门框看她，框把人物包住。' },
  'centered composition, subject on center line': { en: 'She is placed exactly on the center line, facing the lens.', cn: '她压在正中线上，正面朝着镜头。' },
  'diagonal composition': { en: 'The action runs along a diagonal and the image is full of tension.', cn: '动作沿对角线展开，画面全是张力。' },
  'golden ratio, golden spiral': { en: 'Her face sits at the golden point, a softer off-center placement.', cn: '脸落在黄金分割点，偏心但不失衡。' },
  'S-curve composition': { en: 'A winding line leads from the corner of the frame to her.', cn: '一条蜿蜒的线从画面角落引向她。' },
  'foreground occlusion, depth layering': { en: 'A dark shape in the foreground cuts across one corner and depth appears.', cn: '前景一件深色物体切过一角，纵深立刻出现。' },
  'reflection, mirror composition': { en: 'Her reflection hangs mirrored in the water below her.', cn: '她的倒影倒挂在下方水面里。' },
  'repetition, pattern, rhythm': { en: 'Rows of windows repeat across the wall, and one of them is different.', cn: '一排排窗户规律重复，只有一格不一样。' },
  'two-shot': { en: 'Two people share the frame, facing each other.', cn: '两个人同框，面对面。' },
  'surveillance camera view, cctv angle, security camera': { en: 'A security camera looks down at the room from a high corner.', cn: '监控从高处的角落俯看整个房间。' },
  'selfie, arm extended toward camera': { en: 'The phone sits close to the lens with the arm stretched into the frame.', cn: '手机贴近镜头，手臂伸进画面。' },
  'view through a window, looking in through the frame': { en: 'We watch her through a window, glass between us and her.', cn: '隔着一扇窗看她，玻璃横在中间。' },
  'shoulder-level shot': { en: 'The camera rests at her shoulder height, level and unthreatening.', cn: '镜头停在肩头高度，平实不压人。' },
  'hip-level shot, camera at waist height': { en: 'The camera sits at her waist, holding the tension low.', cn: '镜头落在她腰间，把张力压住。' },
  'knee-level shot': { en: 'The camera drops to her knees and everything above looms larger.', cn: '镜头降到膝盖高度，上方一切都放大。' },
  'aerial shot, high above the ground': { en: 'The camera flies high above and the whole town shrinks below her.', cn: '镜头飞在高处，整座城镇在她脚下缩小。' },
  'large-to-small flow': { en: 'The eye runs from the biggest shape down to the smallest — the subject.', cn: '视线从最大的形体一路滑到最小的主体。' },
  'density contrast': { en: 'Inside the dense pattern one gap pulls the eye like a magnet.', cn: '密集图案里的那处留空像磁铁吸住视线。' },
  'visual balance': { en: 'One big shape on the left is balanced by a cluster of small ones on the right.', cn: '左边一个大形，靠右边一小簇配平。' },
  'contrast': { en: 'A bright subject sits against a dark field, and the contrast does the focusing.', cn: '亮主体压在暗底上，对比直接造出焦点。' },
  'claustrophobic framing, tight crop': { en: 'The frame closes in from all four sides and she has no room to breathe.', cn: '四面边框一起收紧，她连呼吸的余地都没有。' },
  '3:4 portrait aspect ratio': { en: 'A tall 3:4 frame holds her from head to toe.', cn: '3:4 竖幅画框从头到脚都装得下。' },
  '4:5 portrait aspect ratio': { en: 'A slightly wider 4:5 frame fits the shoulders comfortably.', cn: '稍宽一点的 4:5 画幅正好把肩线装舒服。' },
  '16:9 landscape aspect ratio': { en: 'The wide 16:9 frame spreads the scenery around her.', cn: '16:9 横幅把环境在她两侧铺开。' },
  '1:1 square aspect ratio': { en: 'A square frame makes the centered composition feel natural.', cn: '方形画幅让居中构图天然成立。' },
  '180-degree line, keep the camera on one side': { en: 'Both cameras stay on the same side of the line between them, so the room never flips.', cn: '两台机位都待在两人连线的同一侧，房间方向就永远不会翻。' },
  'reverse shot': { en: 'Shot A watches her, then the reverse shot hands us her answer.', cn: '正打看她，反打把她答回来的视线递给我们。' },
  'eyeline match': { en: 'She looks off to the right, and the next image enters from the left — the eyeline matches.', cn: '她看向画外右侧，下一张从画外左侧进来——视线接上了。' },
  '30-degree rule': { en: 'The second camera moves at least thirty degrees around her, so the cut reads as a new angle, not a repeat.', cn: '第二机位绕着她至少挪三十度，接起来才像换角度而不是重播。' },
  'headroom': { en: 'A little air is left above her hair — enough to breathe, not enough to float.', cn: '头顶留了一点气——够呼吸，但不至于像飘着。' },
  'lead room, space in the direction of movement': { en: 'She runs toward the right, and the space ahead of her stays open.', cn: '她向右跑，前方那片空一直敞开。' },
  'front light, flat even lighting': { en: 'The light comes straight from the camera side, flat and even, with no shadow to hide anything.', cn: '光从镜头这一侧直打过来，平铺无影，什么都藏不住。' },
  'side light, half-lit face': { en: 'Light falls from the side: one half of her face lit, the other sinking into shadow.', cn: '光从侧面来：半张脸亮着，另一半沉进阴影。' },
  'rembrandt lighting, triangle of light on the cheek': { en: 'A small triangle of light sits on her shadow-side cheek — the classic portrait signature.', cn: '暗侧脸颊上留着一小块三角亮斑——人像的经典签名。' },
  'backlight, silhouette, glowing hair rim': { en: 'She is backlit into a silhouette, and her hair edges glow.', cn: '背光把她压成剪影，发缘却亮着一圈。' },
  'rim light, edge light separating from background': { en: 'A rim light traces her outline and peels her off the dark background.', cn: '一圈轮廓光沿着她的边，把人从暗背景上剥出来。' },
  'top light, shadowed eye sockets': { en: 'The light drops from above, and her eye sockets sink into shadow.', cn: '光从正上方落下，眼窝陷进阴影里。' },
  'bottom light, underlighting': { en: 'The light rises from below — every shadow flips and the mood turns wrong.', cn: '光从下方升起——所有阴影翻了个面，气氛立刻不对。' },
  'butterfly lighting, soft shadow under the nose': { en: 'A butterfly-shaped shadow rests just under her nose.', cn: '鼻子下面停着一只蝴蝶形的小影子。' },
  'three-point lighting, key light, fill light, rim light': { en: 'A key light shapes her, a soft fill lifts the shadows, and a rim light cuts her free.', cn: '主光塑形，补光提暗部，轮廓光把人切出来。' },
  'high key lighting, bright and airy': { en: 'The whole frame is bright and airy, with shadows barely there.', cn: '整个画面明亮通透，阴影几乎不存在。' },
  'low key lighting, deep shadows': { en: 'Most of the frame stays dark, and one small light does all the work.', cn: '画面大部分沉在暗里，只有一小片亮在干活。' },
  'hard light, crisp shadow edge / soft light, feathered shadow edge': { en: 'Hard light cuts a crisp shadow edge; soft light feathers it away.', cn: '硬光的影缘是刀切的，柔光的影缘是化开的。' },
  'volumetric light, god rays, light shafts through the air': { en: 'Light shafts hang in the air, made visible by dust.', cn: '光柱悬在空气里，被灰尘照出了形状。' },
  'golden hour, warm low-angle sunlight, long shadows': { en: 'Low warm sun stretches her shadow long across the ground.', cn: '夕阳把她的影子在地上拉得很长。' },
  'blue hour, cool ambient twilight': { en: 'The sky has gone cool blue, and everything sits in quiet twilight.', cn: '天色转成冷蓝，一切泡在安静的余光里。' },
  'window light, soft directional light from a window': { en: 'Soft light from the window falls across her from one side.', cn: '窗来的柔光从一侧铺过她身上。' },
  'shallow depth of field': { en: 'Only she is sharp; everything in front of and behind her melts away.', cn: '只有她是清晰的，身前身后全部化开。' },
  'deep focus, everything sharp': { en: 'Near and far stay equally sharp, so the whole room tells the story.', cn: '远近一样清晰，整个房间都在讲故事。' },
  'bokeh, out-of-focus light circles': { en: 'Distant lights dissolve into soft round bokeh.', cn: '远处的灯化成一枚枚柔圆的光斑。' },
  'dappled light, sunlight through leaves': { en: 'Light filters through the leaves and scatters in soft patches over her.', cn: '光从叶缝里漏下来，在她身上散成一块块软斑。' },
  'striped light, venetian blind shadows': { en: 'Stripes of light fall through the blinds and lie across everything.', cn: '光被百叶窗切成条纹，横在一切上面。' },
  'wet ground reflections, rain reflections': { en: 'The wet pavement mirrors the lights above it.', cn: '湿漉漉的地面把上面的光整片倒映出来。' },
  'standing, arms at sides, closed legs': { en: 'She stands upright with her arms resting at her sides.', cn: '她站得端正，双臂自然垂在身侧。' },
  'contrapposto, weight on one leg': { en: 'Her weight settles onto one leg, and the hip answers with a soft S.', cn: '重心落在一条腿上，胯部让身体轻轻成了一个 S。' },
  'crossed arms': { en: 'Her arms fold across her chest, a quiet line of defense.', cn: '双臂在胸前交叠，是一道安静的防线。' },
  'hands on hips': { en: 'Both hands rest on her hips, elbows pushed out.', cn: '双手叉腰，手肘向外撑开。' },
  'hand in pocket': { en: 'One hand slips into her pocket while the other hangs loose.', cn: '一只手插进兜里，另一只自然垂着。' },
  'against_wall, leaning back': { en: 'Her back meets the wall, and the wall takes her weight.', cn: '背贴上墙，重心交给墙。' },
  'looking back, turning around': { en: 'She is seen from behind as her head turns back over her shoulder.', cn: '从背后看她转头回眸。' },
  'walking': { en: 'She walks with an easy stride, weight drifting slightly forward.', cn: '她步态放松，重心微微向前。' },
  'running, running towards viewer': { en: 'She runs leaning forward, arms and legs pulled into diagonals.', cn: '她前倾奔跑，手臂和腿拉成对角。' },
  'reaching towards viewer, outstretched arm, foreshortening': { en: 'Her hand reaches toward the lens and looms larger than her body.', cn: '她的手伸向镜头，比身体还显大。' },
  'squatting, hugging own legs': { en: 'She folds down into a squat, arms wrapped around her knees.', cn: '她蜷成一团蹲下，双臂抱住膝盖。' },
  'wariza': { en: 'She sits on the floor in a W, knees out to either side.', cn: '她鸭子坐在地板上，两膝朝外。' },
  'sitting on chair, knees together, hands on lap': { en: 'She sits upright with knees together and hands on her lap.', cn: '她端坐在椅子上，膝盖并拢，双手放在膝上。' },
  'sitting on chair, crossed legs': { en: 'She sits back and crosses one leg over the other.', cn: '她靠向椅背，一条腿搭在另一条上。' },
  'kneeling, one knee down': { en: 'One knee touches the ground while the front foot stays planted.', cn: '一只膝盖贴地，前脚掌踩实。' },
  'lying, on side, head on arm': { en: 'She lies on her side, head cushioned on her arm.', cn: '她侧躺着，头枕在自己的手臂上。' },
  'hand on cheek, elbow on table': { en: 'Her cheek rests on one hand, elbow propped on the table.', cn: '脸颊搁在手上，手肘支在桌面。' },
  'hand in hair, adjusting hair': { en: 'One hand rises to her hair and quietly adjusts it.', cn: '一只手抬到发间，轻轻理了一下。' },
  'back to back, two people standing': { en: 'They stand back to back, each holding the other up.', cn: '两人背对背站着，互为支点。' },
  'holding hands, two people facing each other': { en: 'Their hands meet in the middle, fingers laced.', cn: '两只手在中间交握，十指相扣。' },
  'walking side by side, two people, same direction': { en: 'They walk shoulder to shoulder in the same direction.', cn: '两人并肩，朝同一个方向走。' },
  'two people facing each other, distance between them': { en: 'They face each other across the gap, and the distance says everything.', cn: '两人隔着一段距离相望，距离就是关系。' },
  'hugging, two people, arms around back': { en: 'Her arms fold around his back and her head settles on his shoulder.', cn: '她的手臂环过他的背，头落在他肩上。' },
  'head on shoulder, leaning, two people': { en: 'Her head tips onto his shoulder, eyes half closed.', cn: '她的头歪到他肩上，眼睛半闭。' },
  'height difference, tall and short, two people': { en: 'The height gap is written in the frame — his chin at her crown.', cn: '身高差写在画面里——他的下巴正好齐她头顶。' },
  'princess carry, carrying, two people': { en: 'He carries her with both arms looped, her weight settled in.', cn: '他双臂环抱把她抱起，重心稳稳落进臂弯。' },
  'piggyback, two people, legs around waist': { en: 'She rides on his back, arms over his shoulders, legs around his waist.', cn: '她趴在他背上，手搭肩，腿环腰。' },
  'two people, one in foreground out of focus, one behind': { en: 'One figure fills the foreground, blurred; the other stands small and sharp behind.', cn: '一人占满前景虚着，另一人在后方小小地清晰。' },
  'expressionless, closed mouth': { en: 'Her face stays flat — no expression, nothing given away.', cn: '脸上什么也没有，什么都不给。' },
  'smile, gentle smile': { en: 'A small smile just lifts the corners of her mouth.', cn: '嘴角只是轻轻抬了一下。' },
  'grin, open mouth, teeth': { en: 'A grin splits open with teeth showing.', cn: '咧嘴一笑，牙齿露出来。' },
  'laughing, open mouth, closed eyes': { en: 'She laughs with her eyes squeezed shut.', cn: '她笑得眼睛都眯成一条缝。' },
  'jitome, half-closed eyes': { en: 'Her eyes half close into a cool, appraising look.', cn: '眼睛半眯，一个冷淡的打量。' },
  'angry, frown, furrowed brow': { en: 'Her brows press down and her mouth bends into a frown.', cn: '眉头往下压，嘴绷成一条反弧。' },
  'pout': { en: 'Her lips puff into a small pout.', cn: '嘴唇鼓成一个小小的尖。' },
  'surprised, wide-eyed, open mouth': { en: 'Her eyes snap wide and her mouth opens into an O.', cn: '眼睛瞬间瞪圆，嘴张成一个 O。' },
  'blush, embarrassed': { en: 'Pink blooms on her cheeks and her eyes dodge away.', cn: '脸颊泛起红晕，视线躲开。' },
  'teary eyes, tears': { en: 'Tears well up in her eyes but do not fall yet.', cn: '眼泪在眼眶里打转，还没落下来。' },
  'crying, streaming tears, open mouth': { en: 'Tears run straight down as her mouth opens in a sob.', cn: '泪痕直直落下，嘴张开哭出声。' },
  'smug, smirk, half-closed eyes': { en: 'One brow lifts and her mouth curls to one side.', cn: '一边眉毛挑起，嘴角歪出坏笑。' },
  'looking down, jitome, half-closed eyes': { en: 'She looks down at you through half-closed lids.', cn: '她半垂着眼帘，从上往下看你。' },
  'glaring, staring, eye contact': { en: 'Her eyes lock onto yours and refuse to blink.', cn: '目光锁住你，一眨不眨。' },
  'wink, one eye closed': { en: 'One eye closes in a wink while the other stays on you.', cn: '一只眼眨了眨，另一只还盯着你。' },
  'sweatdrop, nervous': { en: 'A single sweatdrop hangs by her head as she stares blankly.', cn: '一脸空白，旁边挂着一滴汗。' },
  'gritted teeth, angry': { en: 'Teeth grind behind a clenched jaw.', cn: '牙关咬紧，怒气压在里面。' },
  'closed eyes, serene': { en: 'Her eyes close softly, and all the tension leaves.', cn: '眼睛轻轻合上，全身的劲都松了。' },
  'shiny hair, hair highlights': { en: 'A single band of light runs down the lock of hair.', cn: '一条亮带顺着发束淌下来。' },
  'windblown hair, floating hair': { en: 'The hair streams in one direction, all strands agreeing.', cn: '发丝朝同一个方向飘，一根也不打架。' },
  'wet hair, damp hair': { en: 'Damp strands cling to her cheek, beads of water at the tips.', cn: '湿发贴在脸颊上，发梢挂着水珠。' },
  'ahoge': { en: 'A single strand springs up from her crown.', cn: '头顶翘着一根不服帖的呆毛。' },
  'eyelashes, long eyelashes': { en: 'Long lashes fan up from the eye, heavier on top.', cn: '长睫毛向上张开，上浓下疏。' },
  'shiny eyes, catchlight': { en: 'A big catchlight sits in each eye, alive and bright.', cn: '每只眼睛里都点着一枚大高光，整个人是活的。' },
  'eye makeup, eyeliner, eyeshadow': { en: 'A winged liner and soft shadow sharpen her gaze.', cn: '眼线尾一挑、眼影一层，眼神立刻利起来。' },
  'fang': { en: 'One small fang flashes in her grin.', cn: '笑起来露出一颗小虎牙。' },
  'collarbone': { en: 'Three clean lines mark the meeting of neck and shoulder.', cn: '颈肩交界处三条干净的线。' },
  'nape': { en: 'A small strip of nape shows below her hairline.', cn: '发际线下露出小小一段后颈。' },
  'sweat': { en: 'Round beads of sweat sit on her skin, one already running.', cn: '汗珠圆圆地挂在皮肤上，有一颗已经滑下。' },
  'hand focus, detailed hands': { en: 'The frame drops to her hands, knuckles layered and clean.', cn: '画面落到手上，指节分层清清楚楚。' },
  'zettai_ryouiki': { en: 'A strip of thigh shows between the skirt hem and the thighhighs.', cn: '裙摆和袜口之间露出一段大腿。' },
  'floating_clothes, fluttering skirt': { en: 'The skirt lifts with the wind, highlights and folds shifting together.', cn: '裙摆被风掀起，高光和褶子一起动。' },
  'fabric folds, wrinkled clothes': { en: 'Every fold points back to the stress point at her shoulder.', cn: '每一道褶子都指回肩上的受力点。' },
  'barefoot': { en: 'Her bare foot presses the ground, ankle bone catching the light.', cn: '赤脚踩在地上，脚踝骨点被光勾了一下。' },
  'long hair flow, flowing strands': { en: 'Her long hair falls in one smooth flow, ends curling gently.', cn: '长发顺着一股流下来，发尾轻轻收了个弧。' },
  'hair ornament, hairclip, hair ribbon': { en: 'A ribbon and a clip sit in her hair like punctuation.', cn: '一根缎带、一枚发夹，像句读一样点在头发上。' },
  'thigh line, knee, sock top line': { en: 'From thigh to ankle the line stays clean, the sock top pressing a soft mark.', cn: '从大腿到脚踝线条干净，袜口压出一道浅痕。' },
  'fingernails, nail polish': { en: 'Short round nails catch a small highlight at the tips.', cn: '短圆甲在指尖收了一小点光。' },
  'head-to-body ratio, 7 heads tall': { en: 'Seven heads tall — tall, balanced, believable.', cn: '七个头高——高挑、匀称、可信。' },
  'leg-to-body ratio, long legs': { en: 'Her legs take nearly half the frame height.', cn: '腿几乎占了画面高度的一半。' },
  'shoulder width, narrow shoulders': { en: 'Her shoulders measure about two head-widths across.', cn: '肩宽大约两个头的宽度。' },
  'waist-hip ratio, narrow waist': { en: 'The waist pinches in, then the hip answers softly.', cn: '腰收进去，胯再轻轻答一声。' },
  'arm length, fingertips at mid-thigh': { en: 'Relaxed arms, fingertips reaching mid-thigh.', cn: '手臂放松，指尖垂到大腿中段。' },
  'slim, slender body': { en: 'She reads as a clean vertical line.', cn: '整个人读起来是一条干净的直线。' },
  'curvy, full figure': { en: 'The silhouette rolls in soft circles.', cn: '剪影是柔和的一串圆。' },
  'tall, 8 heads tall': { en: 'Almost eight heads tall, all legs and poise.', cn: '快八个头高，全是腿和气场。' },
  'petite, small stature': { en: 'Six heads tall, small and light.', cn: '六个头高，小巧轻盈。' },
  'sloping shoulders': { en: 'Her shoulder line slides gently downward.', cn: '肩线轻轻地往下滑。' },
  'straight shoulders, square shoulders': { en: 'The shoulder line runs flat and wide.', cn: '肩线又平又开。' },
  'upright posture, straight back': { en: 'Ear, shoulder and hip stack on one vertical line.', cn: '耳、肩、髋压在同一条垂线上。' },
  'slouched posture, rounded back': { en: 'Her back rounds into a tired C.', cn: '后背弓成一个疲惫的 C。' },
  'forward head posture': { en: 'Her head drifts ahead of her shoulders.', cn: '头探到了肩线前面。' },
  'long hair, straight hair': { en: 'Her hair falls straight past her waist, ends cut flat.', cn: '头发直直垂过腰，发尾平齐。' },
  'hime cut': { en: 'Straight bangs, sidelocks squared at the jaw, the rest long behind.', cn: '齐刘海、两颊齐颌的侧发，后面的长发全都留着。' },
  'twintails': { en: 'Two tails bounce on either side of her head.', cn: '两条马尾在脑袋两侧一弹一弹。' },
  'ponytail, high ponytail': { en: 'One tail springs from high on the back of her head.', cn: '一束马尾从后脑高处甩出来。' },
  'side ponytail, hair over one shoulder': { en: 'The tail slips over one shoulder and rests there.', cn: '马尾滑过一侧肩头，就停在那儿。' },
  'twin braids, braid': { en: 'Two braids hang in a chain of crossing segments.', cn: '两条辫子垂着，一段一段交叉编下来。' },
  'hair bun': { en: 'Her hair gathers into a round bun on top.', cn: '头发在头顶收成一个圆髻。' },
  'double bun': { en: 'Two round buns sit like antennae on her head.', cn: '两个圆丸子像天线一样立在头上。' },
  'bob cut': { en: 'The cut ends in a clean arc at her jaw.', cn: '发尾在颌线处收成一道干净的弧。' },
  'short hair, layered hair': { en: 'Short hair, ends layered and choppy.', cn: '短发，发尾一层层碎着。' },
  'long hair, curly hair': { en: 'Long hair spirals into curls at the ends.', cn: '长发在发尾旋成一圈圈卷。' },
  'wavy hair': { en: 'Long waves roll down in aligned S-curves.', cn: '大波浪一排排 S 形滚下来。' },
  'half updo': { en: 'The top half is gathered back; the rest stays down.', cn: '上半扎起一小束，下半继续披着。' },
  'blunt bangs': { en: 'Bangs cut in one hard horizontal line.', cn: '刘海剪成一条硬邦邦的平线。' },
  'see-through bangs': { en: 'Thin bangs with gaps you can see the brows through.', cn: '薄薄的刘海透着缝，能看见眉毛。' },
  'swept bangs': { en: 'Bangs sweep across the forehead in one direction.', cn: '刘海朝一个方向斜斜扫过额头。' },
  'parted bangs, center part': { en: 'The bangs part in the middle and the forehead shows.', cn: '刘海从中间分开，额头露出来。' },
  'running, skirt flare, pleated skirt': { en: 'The skirt opens into an umbrella behind her stride.', cn: '裙摆在跨步后面撑成一把伞。' },
  'sitting, skirt spread on lap': { en: 'The skirt spreads over her lap and pools in soft folds.', cn: '裙摆摊在膝盖上，堆出柔软的垂褶。' },
  'sleeve slipping, arm up': { en: 'The sleeve slides toward the elbow as her arm rises.', cn: '手臂一抬，袖子顺势滑向手肘。' },
  'open collar, unbuttoned shirt': { en: 'One button is open and the collar sits loose.', cn: '第一颗扣子开着，领口松松的。' },
  'bowtie, floating ribbon, wind': { en: 'The ribbons of the bowtie stream in the wind.', cn: '领结的两条飘带被风扯向一边。' },
  'jacket off shoulder, single off shoulder': { en: 'The jacket has slipped off one shoulder.', cn: '外套从一边肩膀滑了下来。' },
  'wet clothes, clinging clothes': { en: 'The wet shirt clings to her frame and drips.', cn: '湿衬衫贴着身体，还在滴水。' },
  'loose socks': { en: 'The socks slouch in loose rings around her ankles.', cn: '袜子松松垮垮堆在脚踝处。' },
  'skirt lift, wind from below': { en: 'A gust from below lifts the hem.', cn: '一阵风从下面把裙摆掀起来。' },
  'untucked shirt, hem flip': { en: 'The untucked hem flips up at one corner.', cn: '没扎的下摆翘起一角。' },
  'button strain, tight shirt': { en: 'The buttons strain and wrinkles pull sideways.', cn: '扣子绷着，横褶向两边拉。' },
  'pleated skirt, spread pleats': { en: 'The pleats fan open as she moves.', cn: '一动起来，褶就扇开。' },
  'sleeves past wrists': { en: 'The sweater sleeve swallows her hand, only fingertips out.', cn: '毛衣袖子盖住手，只露出指尖。' },
  'scarf trailing, floating scarf': { en: 'The scarf trails behind, opposite the run.', cn: '围巾在身后拖着，和跑的方向相反。' },
  'belt chain, swaying accessory': { en: 'The belt chain swings out a small arc.', cn: '腰链甩出一道小小的弧。' },
  'mid-action moment, caught in the middle of': { en: 'The frame catches her mid-cross-step, weight shifting forward.', cn: '画面抓到她交叉步的中间一帧，重心正往前移。' },
  'still swaying, steam still rising, half-open': { en: 'The cup still sways and the steam still rises — she just left.', cn: '杯子还在晃、热气还在升——她刚离开。' },
  'looking at something off-screen, reacting to a sound': { en: 'Her eyes snap toward something outside the frame.', cn: '她的目光猛地转向画框之外的东西。' },
  'palm against the glass, brushing rain off the sleeve': { en: 'Her palm presses flat against the cold glass, rain running past it.', cn: '掌心贴上冰冷的玻璃，雨水从指边流下去。' },
  'gripping the strap, tugging the sock, holding the skirt hem': { en: 'Her fingers grip the strap a little too hard.', cn: '手指把包带攥得有点太紧。' },
  'tearing up but smiling, biting back words': { en: 'She smiles at him, and the tears are already there.', cn: '她对他笑着，眼泪却已经在了。' },
  'worn bag, patched strap, rusted charm': { en: 'The strap has been stitched three times, and the buckle charm has gone rusty.', cn: '包带缝过三次，扣环上的挂坠已经生锈。' },
  'crooked bowtie, loose strand, slipping sock': { en: 'The bowtie sits a degree crooked and one strand escapes.', cn: '领结歪了一点点，一缕头发逃了出来。' },
  'gaze logic, looking off-screen / at camera / at her own hands': { en: 'She looks past everything, at something we cannot see.', cn: '她越过一切，看向我们看不见的地方。' },
  'traces of time, fading light, falling leaf': { en: 'The light is going, and a leaf lets go in the corner.', cn: '光正在退场，角落里一片叶子离开了枝头。' },
  'pathetic fallacy, rain matching her mood': { en: 'The rain agrees with her mood — except for one warm lamp.', cn: '雨和她的心情一致——除了一盏暖着的灯。' },
  'footprints, ripples, pressed imprint': { en: 'Ripples still spread where her steps just pressed the puddle.', cn: '她刚踩过的水洼里，涟漪还在散。' },
  'distance and direction telling the story': { en: 'The space between them, and the hairpin left on the ground, tell the rest.', cn: '两人之间的空档，连同地上那枚落下的发夹，把故事说完了。' }
};

/* 组合实战（词表版 + 自然语言版成品段落） */
const COMBOS: Combo[] = [
  {
    zh: '对峙压迫（fx A01 五件套）',
    en: 'from above, high angle looking down ~30°, dutch angle ~15°, front view, bust shot cropped at mid-torso, subject centered on the vertical corner seam, leading lines aiming at the eyes, entire head in frame with margin above hair',
    nl: 'The camera hangs above her, looking down at about thirty degrees, and the frame is tilted fifteen degrees to the right. She leans back against the corner of the building, chin lifted, staring straight up into the lens. Only her upper body fills the frame, centered on the vertical corner seam, with the wet street opening empty in front of her. The lines of the corner pull the eye straight to hers.',
    nlc: '镜头悬在她上方约三十度俯视，画面向右斜切十五度。她靠着楼角，下巴微抬，直直盯着镜头。只取上半身，居中压在楼角竖缝上，前方留出空街。角线把视线一路引到她的眼睛。',
    parts: '垂直=俯 30° ｜ 斜切=15° ｜ 景别=半身 ｜ 构图=居中+引导线',
    note: '首图实战组合：压迫来自俯角、失衡来自斜切、对峙来自居中+交汇视线；平视+斜切双叠加脸必歪。',
    dia: caseSvg('confront')
  },
  {
    zh: '孤独留白',
    en: 'eye-level, wide shot, tiny figure, rule of space, negative space in front, empty street',
    nl: 'The camera sits at her eye level, far back. She is a small figure standing in an almost empty street, and the space in front of her is left completely open — that emptiness carries the loneliness.',
    nlc: '镜头拉远、与眼平齐。小小的她站在几乎无人的街上，身前留出一整片空——空本身就是孤独。',
    parts: '垂直=平视 ｜ 景别=远景 ｜ 构图=视线留白+负空间',
    note: '负空间要写出「空」（empty space）而不是不写；视线方向的留白里不放道具。',
    dia: caseSvg('solitude')
  },
  {
    zh: '回眸',
    en: '3/4 back view, from behind at 45°, bust shot cropped at mid-torso, looking back over shoulder, rule of space in the looking direction',
    nl: 'She is seen from behind at an angle, half turned, and the camera catches her face as she looks back over her shoulder. The space in the direction of her gaze stays empty.',
    nlc: '从斜后方看她，她半转身，回眸的一瞬被镜头抓到。她看过去的方向留着空白。',
    parts: '水平=背 3/4 ｜ 景别=半身 ｜ 构图=视线留白',
    note: '背影+侧脸同框信息量最大；回眸方向必须留白。',
    dia: caseSvg('lookback')
  },
  {
    zh: '足下巨大感',
    en: 'ground-level shot, camera on the ground, lower body focus, thighs to shoes in frame, foreshortening',
    nl: 'The camera is set down on the ground and shoots upward. Only her lower half enters the frame — the skirt hem hangs at the top, legs lead to the shoes right in front of the lens, making her feel giant.',
    nlc: '镜头放在地上向上拍。只有下半身入框——裙摆挂在画面上缘，腿一路引到镜头前的鞋，人一下子巨大起来。',
    parts: '垂直=贴地 ｜ 景别=下半身 ｜ 焦段=透视缩短',
    note: '动漫「足下机位」：裙摆压顶、鞋底朝镜头；只写裙摆做 context，不写脸/发。',
    dia: caseSvg('lowlegs')
  },
  {
    zh: '被观察（监控感）',
    en: 'surveillance camera view, cctv angle, high angle looking down ~45°, wide angle, full coverage of the room',
    nl: 'A security camera looks down at her from a high corner of the room, its wide lens covering the whole floor. She is small inside the cold wide view — watched, not watching.',
    nlc: '监控从房间高处的角落俯看她，广角把整个地面收进画面。她在冷冰冰的大景里很小——被看，而不在看。',
    parts: '特殊=监控 ｜ 垂直=俯 45° ｜ 焦段=广角',
    note: '冷漠/被观察感；本项目禁文字水印（时间戳）。',
    dia: caseSvg('watch')
  },
  {
    zh: '走廊纵深',
    en: 'eye-level, one-point perspective, leading lines to the vanishing point, full body, figure mid-corridor',
    nl: 'The camera stands at her eye level in the middle of a long corridor. All the lines of the walls and floor run to one vanishing point ahead, pulling the eye past her into the depth.',
    nlc: '镜头与她平齐站在长走廊中间。墙面和地板的线全部收向前方一个灭点，视线越过她一路被拉进纵深。',
    parts: '垂直=平视 ｜ 透视=一点 ｜ 构图=引导线 ｜ 景别=全身',
    note: '灭点收在人物身上或脑后；STEP3 背景必须服从这个机位。',
    dia: caseSvg('corridor')
  },
  {
    zh: '倒影孤独',
    en: 'wide shot, reflection in the water, negative space, small figure by the shore',
    nl: 'She stands small by the water, and the camera stays far back. Her reflection hangs mirrored in the surface, while a wide stretch of empty space fills the rest of the frame.',
    nlc: '小小的她站在水边，镜头离得很远。水面倒挂着她完整的倒影，其余大片画面空着。',
    parts: '景别=远景 ｜ 构图=反射镜像+负空间',
    note: '水面/镜面倒影信息翻倍；倒影虚一档（更低的 opacity）。',
    dia: caseSvg('moonwater')
  },
  {
    zh: '战斗动态',
    en: 'from below, low angle looking up, foreshortening, fist toward camera, diagonal composition, dutch angle ~10°',
    nl: 'The camera crouches low and looks up as her fist punches toward the lens — foreshortening makes it huge, her body shrinking behind it. The image is tilted slightly and the motion runs along a diagonal.',
    nlc: '镜头低伏仰拍，她的拳头朝镜头打来——近大远小让它变得巨大，身体在后方缩小。画面微斜，动作沿对角线冲出去。',
    parts: '垂直=仰视 ｜ 焦段=透视缩短 ｜ 构图=对角线+斜切',
    note: '拳头近大远小+对角张力；脸崩风险高，表情要写死。',
    dia: caseSvg('battle')
  }
];

/* 高级镜头感（进阶组合：层次 + 光分离 + 收束 + 节奏） */
const PROCOMBOS: Combo[] = [
  {
    zh: '纵深三层·街角',
    en: 'shot past a blurred foreground railing, mid-ground subject in focus, background lights stacked by a telephoto lens, atmospheric haze separating the layers, rim light on her outline',
    nl: 'We shoot past the wet railing in the foreground, blurred and close. She stands in the middle distance, sharp and lit, while the street lights behind her stack into soft circles. Haze separates each layer, and a thin rim light pulls her outline off the background.',
    nlc: '镜头从前景那段模糊的湿栏杆后看过去。她站在中景，清晰、受光；身后的街灯被长焦压成一叠柔圆。空气把每一层分开，一线轮廓光把她的轮廓从背景上剥离。',
    parts: '前景=遮挡虚化 ｜ 中景=主体实 ｜ 后景=长焦压缩+光斑 ｜ 光=轮廓分离',
    note: '第一配方：画面至少读得出三层；前景不写细节，只写「虚」。',
    dia: caseSvg('depth')
  },
  {
    zh: '逆光剪影·窗边',
    en: 'backlit silhouette against a bright window, rim light around the outline, dust floating in the beam, foreground falling into deep shadow',
    nl: 'She stands against a bright window, almost a silhouette. Light spills around her outline and dust floats in the beam, while the near side of the room drops into deep shadow — the brightness gap alone says she is the subject.',
    nlc: '她站在亮窗前面，几乎成了剪影。光顺着轮廓漫出来，光柱里浮着尘；近侧房间沉进深影——光比本身已经在说谁是主角。',
    parts: '光=逆光剪影 ｜ 分离=轮廓光 ｜ 氛围=尘粒光束 ｜ 前景=深影',
    note: '光分离的第二形态：主体暗、背景亮；脸看不清，轮廓反而更响。',
    dia: caseSvg('backlit')
  },
  {
    zh: '视线接力·过肩二段',
    en: 'over-the-shoulder foreground silhouette out of focus, mid-ground subject looking off-frame, rule of space in the gaze direction',
    nl: 'A dark shoulder fills the left foreground, out of focus; she stands beyond it in the middle of the frame, eyes turned off-screen. Her gaze leaves an empty lane, and the shoulder quietly pins the viewer behind her.',
    nlc: '左前景是一段虚焦的深色肩膀；她在中景站定，眼睛看向画外。视线方向留出一条空道，而那段肩膀把观众的站位悄悄按在她身后。',
    parts: '前景=过肩虚焦 ｜ 中景=主体 ｜ 构图=视线留白',
    note: '观众被前景按在「她身后」——这就是代入感；肩膀只写形状不写五官。',
    dia: caseSvg('relay')
  },
  {
    zh: '镜面双打',
    en: 'facing the mirror, reflection meeting her eyes, real and mirrored splitting the frame, the real back soft in the foreground',
    nl: 'She faces the mirror and her reflection faces her. The real back of her head is soft in the foreground while the reflected eyes are sharp — the frame is quietly divided between the two of her.',
    nlc: '她面对镜子，镜中的她也面对她。真身的后脑在前景虚着，镜中那双眼睛却清晰——画面被两个她安静地一分为二。',
    parts: '构图=反射镜像 ｜ 焦点=前虚后实 ｜ 对称=画面对半',
    note: '镜面是最便宜的「双重主体」；真身与倒影清晰度不同，画面立刻高级。',
    dia: caseSvg('mirror2')
  },
  {
    zh: '贴地动势·雨滴前置',
    en: 'ground-level camera, raindrop streaks blurring past the lens, foreshortened stride, ground tilted a few degrees',
    nl: 'The camera lies on the ground as she strides past — raindrop streaks smear across the near lens, foreshortening drives her stride huge, and the ground tilts a few degrees. The frame reads speed before it reads face.',
    nlc: '镜头躺在地上，她跨步经过——近处雨痕在镜头上拖过，近大远小把跨步推得巨大，地面斜了几度。这张图先让人读到「速度」，其次才是脸。',
    parts: '垂直=贴地 ｜ 焦段=透视缩短 ｜ 前景=粒子 ｜ 斜切=约10°',
    note: '动势三件套：低机位 + 近大远小 + 前景粒子；三者同现才「快」。',
    dia: caseSvg('grounddyn')
  },
  {
    zh: '框中框纵深·走廊',
    en: 'two nested doorways, frame within frame, subject small at the far end, light pooling at the end of the corridor',
    nl: 'Two doorways stack into the distance, each framing the next. She stands small in the far light, and every corridor line pulls the eye toward her. The rooms between stay dark so the depth reads.',
    nlc: '两重门框层层套向深处，每一层都框住下一层。她小小的站在远光里，走廊的所有线都把她往前推。中间的房间保持暗，纵深才读得出来。',
    parts: '构图=画框框×2 ｜ 透视=灭点收束 ｜ 光=尽头光池',
    note: '框套框 + 明暗分层 = 免费的纵深；中间层一定压暗。',
    dia: caseSvg('nested')
  },
  {
    zh: '插入特写·手上的戏',
    en: 'close-up insert of her hands gripping the strap, subject blurred behind, shallow focus, story told by the knuckles',
    nl: 'The frame drops to her hands — one knuckle white on the strap — while she stays a soft blur behind. The focus makes the narrative choice: not her face, her grip.',
    nlc: '画面落到她的手上——指节在包带上按得发白——她本人在后方虚成一团。焦点替叙事做了决定：不拍脸，拍那一下用力。',
    parts: '景别=局部特写 ｜ 焦点=浅景深 ｜ 主体=虚化在后景',
    note: '「不拍脸」本身就是高级语法；手、鞋、衣角都能替脸说话。',
    dia: caseSvg('insert')
  },
  {
    zh: '俯瞰对称·破一处',
    en: 'directly overhead, symmetrical layout, one element quietly off-grid, hard light',
    nl: 'The camera looks straight down on a symmetrical table scene — cups and plates all aligned — and one tilted cup quietly breaks the grid. Order everywhere, one rebellion.',
    nlc: '镜头垂直俯看一桌对称的场景——杯盘全部对齐——只有一只歪掉的杯子悄悄破了网格。处处秩序，一处叛逆。',
    parts: '垂直=鸟瞰 ｜ 构图=对称 ｜ 焦点=破格点',
    note: '对称里必留一个「不对」，否则是图案不是画面。',
    dia: caseSvg('topdown')
  }
];

/* 拆解实战（成品段落逐段拆回词条） */
const DISSECTS: Dissect[] = [
  {
    zh: '案例一：雨夜对峙（fx_A01 实战）',
    en: 'The camera hangs above her, looking down at about thirty degrees, and the frame is tilted fifteen degrees to the right. She leans back against the corner of the building, chin lifted, staring straight up into the lens. Only her upper body fills the frame, centered on the vertical corner seam, with the wet street opening empty in front of her. The lines of the corner pull the eye straight to hers, and a cold streetlight rims her hair from behind.',
    cn: '镜头悬在她上方约三十度俯视，画面向右斜切十五度。她靠着楼角，下巴微抬，直直盯着镜头。只取上半身，居中压在楼角竖缝上，前方留出空街。角线把视线一路引到她的眼睛，冷色街灯从身后给她勾出一圈发丝光。',
    tag: 'from above, high angle looking down ~30°, dutch angle ~15°, front view, bust shot cropped at mid-torso, subject centered on the vertical corner seam, leading lines aiming at the eyes, entire head in frame with margin above hair',
    rows: [
      ['The camera hangs above her, looking down at about thirty degrees', '高俯 30°（垂直机位）', '机位即威胁者：俯角制造「被堵」感'],
      ['the frame is tilted fifteen degrees to the right', '荷兰角 15°', '失衡/不安；只配俯视，平视+斜切双叠加脸必歪'],
      ['She leans back against the corner of the building', '街边阳角站位（STEP2 姿态层）', '背有实体、前有退路=对峙舞台'],
      ['chin lifted, staring straight up into the lens', '视线顶进镜头（交锋眼）', '把权力顶回去；高光缺口=不屑成立点'],
      ['Only her upper body fills the frame', '半身 bust shot + 防裁切句', '保表情与手势，防裁头'],
      ['centered on the vertical corner seam', '中心构图 + 竖缝居中', '脊柱压角线=人物最稳最狠'],
      ['The lines of the corner pull the eye straight to hers', '引导线', '视线先落地，再上看她的眼睛'],
      ['a cold streetlight rims her hair from behind', '轮廓光（光影）', '暗调里保住发缘，从背景剥离']
    ]
  },
  {
    zh: '案例二：回眸',
    en: 'She is seen from behind at an angle, half turned, and the camera catches her face as she looks back over her shoulder. The space in the direction of her gaze stays empty.',
    cn: '从斜后方看她，她半转身，回眸的一瞬被镜头抓到。她看过去的方向留着空白。',
    tag: '3/4 back view, from behind at 45°, bust shot cropped at mid-torso, looking back over shoulder, rule of space in the looking direction',
    rows: [
      ['seen from behind at an angle', '背 3/4（水平机位）', '背影+侧脸同框，信息量最大'],
      ['half turned, looks back over her shoulder', '回眸动作（STEP2 动作层）', '转身瞬间=叙事钩子'],
      ['the camera catches her face', '半身 shot（景别）', '脸与肩同框，回眸读得清'],
      ['The space in the direction of her gaze stays empty', '视线留白 rule of space', '目光有去处，情绪有悬念'],
      ['（避雷对照）', '留白里不放道具', '视线方向塞东西=把悬念堵死']
    ]
  },
  {
    zh: '案例三：走廊纵深',
    en: 'The camera stands at her eye level in the middle of a long corridor. All the lines of the walls and floor run to one vanishing point ahead, pulling the eye past her into the depth.',
    cn: '镜头与她平齐站在长走廊中间。墙面和地板的线全部收向前方一个灭点，视线越过她一路被拉进纵深。',
    tag: 'eye-level, one-point perspective, leading lines to the vanishing point, full body, figure mid-corridor',
    rows: [
      ['at her eye level', '平视（垂直机位）', '中性视角，让透视说话'],
      ['in the middle of a long corridor', '一点透视场景（透视体系）', '灭点在画面中，纵深自动生成'],
      ['All the lines run to one vanishing point', '引导线 + 一点透视', '全部线条收束=眼睛被拉进去'],
      ['pulling the eye past her into the depth', '灭点收在人物身上/脑后', '主体与纵深同轴，人在景里'],
      ['stands in the middle', '中心构图', '走廊中轴=人物中轴'],
      ['（STEP3 交接）', 'background perspective must follow STEP2 camera', '背景透视服从机位，不得另起']
    ]
  }
];

/* 同一机位的五种自然语言说法 */
const NLWAYS: NlWay[] = [
  { name: '直述式', en: 'Shot from above at about thirty degrees, tilted fifteen degrees to the right.', cn: '从上方约三十度俯拍，向右斜十五度。' },
  { name: '视角代入式', en: 'We look down on her, and the world tilts.', cn: '我们俯看她，世界微微倾斜。' },
  { name: '相对描述式', en: 'The camera sits well above her eye level, leaning into the tilt.', cn: '镜头明显高于她的眼睛，还带着倾角。' },
  { name: '情绪先行式', en: 'A heavy, off-balance look-down — she is small under it.', cn: '沉甸甸、失衡的俯视——她在底下显得很小。' },
  { name: '指令/垫图式', en: 'same high angle about thirty degrees above eye level, dutch tilt fifteen degrees, bust framing identical to the reference', cn: '与参考一致：高于眼位约三十度俯拍，斜切十五度，半身取景不变。' }
];

/* 公开教程与外链库 */
const RESOURCES: ResItem[] = [
  { lang: '中', t: 'CLIP STUDIO TIPS · 三步骤构图法（Moonlichi）', url: 'https://tips.clip-studio.com/zh-tw/articles/8486', note: '定画框(三分) → 定景别 → 视线引导三公式：大到小流动 / 追踪线条 / 疏密对比' },
  { lang: '中', t: 'CLIP STUDIO TIPS · 角色构图（G-KAi）', url: 'https://tips.clip-studio.com/zh-cn/articles/8535', note: '镜头/景别/视角全表 + 构图法 + 对比四维（颜色/明度/形状/纹理）+ 韵律' },
  { lang: '中', t: 'CLIP STUDIO TIPS · 构图、三分法和黄金比例（Michael88）', url: 'https://tips.clip-studio.com/zh-cn/articles/4086', note: '力量点 / 双兴趣中心对角摆放 / 运动空间：前方留白、被困收紧' },
  { lang: '中', t: 'MediBang · 来思考插画的构图吧', url: 'https://medibangpaint.com/zh_CN/use/2021/07/thinkaboutcomposition', note: '五种构图法 + 画布比例（16:9 / 4:3 / 3:2 / 1:1）+ 错误示范' },
  { lang: 'EN', t: 'StudioBinder · Camera Angles 索引', url: 'https://www.studiobinder.com/camera-shots/camera-angles', note: '肩/腰/膝/贴地高度心理学 + Profile / Aerial；本手册高度阶梯来源' },
  { lang: 'EN', t: 'StudioBinder · 50+ 镜头与角度指南', url: 'https://www.studiobinder.com/blog/ultimate-guide-to-camera-shots', note: '景别/角度/取景/焦段全索引，配电影实例' },
  { lang: 'EN', t: 'Adobe · 镜头与角度', url: 'https://www.adobe.com/ca/creativecloud/video/production/cinematography/camera-shots-and-angles.html', note: '景别与角度基础讲法，含 POV / 反打 / 侧写' },
  { lang: '日', t: 'デジタルハリウッド · レイアウト与构图基础', url: 'https://school.dhw.co.jp/course/3dcg/contents/w_layout.html', note: '构图原则表（三分/黄金比/日の丸/对角/对称/额缘/引导线）+ 视线控制五技' },
  { lang: 'EN', t: 'Sakuga Blog · 动画 Layout 术语', url: 'https://blog.sakugabooru.com/glossary/layouts', note: '动画演出术语库入口：layout / 演出 / 構図' },
  { lang: '日', t: 'アニメ私塾流 作画レイアウトの描き方（书）', url: 'https://www.xknowledge.co.jp/book/9784767835358', note: '目录即学习地图：EL / 消失点 / 视线诱导 / 面分け / 广角望远 / 180度线' },
  { lang: '中', t: 'Wikipedia · 三分法（构图）', url: 'https://zh.wikipedia.org/wiki/%E4%B8%89%E5%88%86%E6%B3%95_(%E6%A7%8B%E5%9C%96)', note: '井字构图法的定义与来历，快速复习' },
  { lang: 'EN', t: 'Wikipedia · Headroom（头顶空间）', url: 'https://en.wikipedia.org/wiki/Headroom_(photographic_framing)', note: '头顶空间的取景规则与常见错误' },
  { lang: 'EN', t: 'Wikipedia · Lead room（运动空间）', url: 'https://en.wikipedia.org/wiki/Lead_room', note: '运动 / 视线方向留白的定义' },
  { lang: 'EN', t: 'fullfrontal.moe · Layout 动画构图史', url: 'https://fullfrontal.moe/animation-fundamentals-a-short-history-of-layout', note: '动画レイアウト制度的起源：宫崎骏与演出体系' },
  { lang: '中', t: 'LocalBanana · AI 提示词里的相机语言', url: 'https://www.localbanana.io/zh/blog/ai-camera-settings-prompts', note: '9,599 条真实提示词词频统计 + 相机块四行模板（本页词频榜来源）' },
  { lang: '中', t: '塔猴 · 风格、构图、光影、色彩的控制', url: 'https://www.tahou.com/article/211665038031266821', note: '光影三要素（方向/光比/色温）+ 权重语法 + 三轮迭代策略' },
  { lang: '中', t: '腾讯新闻 · 7 种景别电影分镜提示词', url: 'https://news.qq.com/rain/a/20250514A08UQJ00', note: '分镜师指令模板：一关键词出 7 景别，锁风格与人物一致性' },
  { lang: '中', t: 'FlowPix · AI 绘画提示词完全指南', url: 'https://www.flowpixai.com/prompt-engineering/ai-art-prompt-writing-complete-guide.html', note: '器材参数技巧（shot on…）与平台差异（MJ / SD / DALL-E）' },
  { lang: '中', t: 'Lovart · 视频反向工程为提示词', url: 'https://www.lovart.ai/zh/blog/reverse-engineer-video-into-prompt', note: '五层拆解法（镜头/光/主体/环境/时长），静态图可借前四层' }
];

const PAIRS: string[][] = [
    ['女孩站在雨中', '她跑到一半停在雨里，手还伸向没收起的伞', 'she stops mid-run in the rain, one hand still reaching for her unopened umbrella', '故事瞬间+残响'],
    ['女孩开心地笑', '她笑着踢飞一颗石子，夕阳把影子拉得很长', 'laughing as she kicks a pebble away, her shadow stretched long by the sunset', '情绪具象化+时间痕迹'],
    ['JK 站在街角', '她刚要转身离开，又回头看了一眼街对面', 'just as she turns to leave, she glances back across the street', '画外暗示'],
    ['安静的教室', '窗开着，卷子被风掀起一角，她的笔停在本子上', 'the window is open, a corner of her test paper lifted by wind, her pen resting mid-line', '动作停留+环境接触'],
    ['女孩看着镜头', '听到喊声回头的半秒——表情还没成型', 'turning at the sound of her name — the half-second before the expression lands', '未完成感'],
    ['她在喝热可可', '双手捧着杯子，热气糊住眼神，指尖烫得微微蜷起', 'both hands wrapped around the cup, steam fogging her gaze, fingertips curling from the heat', '五感细节'],
    ['她生气', '咬着牙不说话，捏皱了手里的成绩单', 'biting back words, the report card crumpled in her fist', '情绪写行为'],
    ['她哭了', '笑着和他说再见，转身的瞬间眼泪才掉下来', 'smiling goodbye, and only after turning away do the tears fall', '情绪矛盾'],
    ['她背着旧书包', '书包带缝过三次，扣环上挂着生锈的小挂坠', 'a bag strap stitched three times, a rusted charm on the buckle', '道具叙事'],
    ['她在图书馆', '额头顶着摊开的书睡着了，风吹动页角', 'asleep with her forehead on an open book, the draft ruffling the page corner', '微动作+环境']
  ]

const JARGON: string[][] = [
    ['怼脸 / 大头照', 'extreme close-up / face focus', '情绪最大、崩脸风险最高；脸眼细节要写死'],
    ['上帝视角', "bird's eye view / top-down", '完全俯视，人物像棋子'],
    ['蚂蚁视角 / 虫视角', "worm's eye view", '极端仰视，常配广角与 foreshortening'],
    ['狗狗 / 猫猫视角', 'low angle', '萌宠视角：主体显大显可爱'],
    ['广角大长腿', 'low angle + wide angle + foreshortening', '社区拉腿公式；注意脸不要一起被拉'],
    ['电影感三件套', 'cinematic lighting + film grain + 2.35:1 letterbox', '宽银幕黑边是点睛项；anamorphic 可加光晕'],
    ['证件照光', 'front light, flat even lighting', '顺光无影——验证结构与设定图用'],
    ['海报感 / 挂画感', 'centered + negative space (upper third for text)', '构图直接给排版让位'],
    ['分镜感', 'establishing + medium + close-up 三连', '一组图做叙事节奏；换机位守 30 度原则'],
    ['立绘感', 'full body, centered, arms at sides', '游戏立绘站姿：中正、对称、无透视夸张'],
    ['杂志封面感', 'headroom + editorial portrait', '头顶留出刊头位；留白必须带位置'],
    ['高级灰', 'low saturation / muted palette', '低饱和+灰调；色值查 palette.html'],
    ['眼神杀', 'close-up + eye contact + catchlight', '高光点=杀气成立点'],
    ['死亡角度', 'extreme low angle', '慎用：脸型与比例易崩，配自检五问用'],
    ['拍立得 / 胶片感', 'film simulation + film grain + faded colors', 'Kodak Portra 400 / Fujifilm Classic Negative']
  ]

const FREQ: string[][] = [
    ['depth of field（景深）', '14.5%', '最常被写的技术词'],
    ['shallow depth of field（浅景深）', '11.1%', '要它的人里 77.6% 没写光圈——写了效果没写原因'],
    ['close-up（特写）', '9.3%', '比任何焦段都高；但太常见，是弱信号'],
    ['bokeh（焦外）', '5.4%', '结果词；换成 f/1.8 + 主体背景距离更准'],
    ['symmetry / symmetrical（对称）', '5.1%', '构图词之王，约束版面最狠'],
    ['85mm', '4.9%', '焦段第一（语料偏人像）'],
    ['35mm', '3.5%', '主体 + 读得出「在哪」的环境'],
    ['full body（全身）', '3.3%', '写全身必须补鞋与地面，否则来什么算什么'],
    ['negative space（留白）', '2.7%', '后接具体位置（upper third）威力最大'],
    ['low angle（低角度）', '2.5%', '权威感；虫视角是其极端端'],
    ['50mm', '2.4%', '中性、接近人眼'],
    ['wide-angle（广角）', '2.4%', '比 24mm 含糊；能报数字就报数字'],
    ['f/1.8', '2.0%', '人像默认光圈'],
    ['medium shot（中景）', '1.8%', '被低估：齐腰、手能入戏、环境可读'],
    ['eye level（平视）', '1.4%', '听着像废话但值得写：不写会漂成「略低英雄机位」'],
    ['f/2.8', '1.3%', '整脸实+背景柔；双人/带手最稳'],
    ['centered composition（居中）', '1.3%', '仪式感'],
    ['24mm', '0.75%', '戏剧性透视拉伸'],
    ['high angle（高角度）', '0.74%', '最被浪费的杠杆：清杂背景极快'],
    ['f/1.4', '0.69%', '极端分离：只留一个平面实'],
    ['fisheye（鱼眼）', '0.59%', '畸变即主题'],
    ['f/4', '0.45%', '全主体通透实'],
    ['telephoto（长焦）', '0.43%', '压缩空间']
  ]

const CHEATS: Cheat[] = [
    { zh: '焚诀·相机块四行（万能尾巴）', en: 'Camera: 85mm, f/1.8, eye level, waist-up framing\nFocus: sharp on the near eye; ears and shoulders already soft\nDistance: subject 1.5m from camera, background 6m behind subject\nComposition: subject on the left third, negative space to the right', note: '贴在提示词末尾、主体与光线之后；四行抵过一串形容词' },
    { zh: '浅景深的正确写法', en: '85mm, f/1.8, sharp on the near eye, background 6m behind fully dissolved into round highlights', note: '把形容词换成四件可执行的事：焦段/光圈/对焦点/距离' },
    { zh: '器材作弊码', en: 'shot on Sony A7R V, 35mm f/1.4 lens, Fujifilm Classic Negative film simulation', note: '模型不模拟光学，但具体器材字符串绑定了一致的观感，比「梦幻虚化」稳' },
    { zh: '光影三要素句', en: 'key light from upper left, high contrast, warm 3200K', note: '方向 + 光比 + 色温，一次写全' },
    { zh: '冷暖结合', en: 'warm amber key light with cool blue rim reflection', note: '全暖全冷都单调；在反射/阴影里塞一抹反色' },
    { zh: '留白定位法', en: 'negative space on the upper third for text', note: '留白必须带位置；模型最不愿意主动把画面留空' },
    { zh: '洗画面负词', en: 'sketch, line art, monochrome, black and white', note: '放 negative，防模型自作主张黑白化' },
    { zh: '平视防漂', en: 'eye level', note: '不指定时机位会漂成「略低英雄感」；要目击感就写死' },
    { zh: '全身补全', en: 'full body, dark loafers on wet pavement', note: '全身=鞋和地面也成了你的问题，主动补上' }
  ]

const TRACE: Cheat[] = [
    { zh: '焚诀·描改五定则', en: '1) Layout, pose, expression, proportion and drawing method follow the original — change nothing, add nothing, remove nothing;\n2) Delete every element of the original character\'s identity; keep ONLY the identity of the character in the reference images;\n3) Identity anchors: exactly the locked ones, never add extra; hands ONLY if the original already shows hands — never draw hands that were not there;\n4) If clothing appears, strictly replace the original costume with the reference outfit and accessories — same garments, same design, same colors;\n5) Keep the existing text area clean and untouched; if the original is black-and-white line art, keep the result black-and-white line art too, using light soft shading for the gradient hair tip colors; re-add captions afterwards.', note: '描改＝换人不换版；原角色身份全删；锚点宁少勿多；原图没手就不画手；黑白线条图别被上色、渐变发尖用淡阴影；梗文案永远后期回贴' },
    { zh: '焚诀·描改主模板（EN · 填身份锚点即用）', en: 'Trace-adjust task: repaint the artwork in image 1 as the character shown in image 2 / image 3.\n\nKeep the original strictly as the layout source: same pose, same gesture, same facial expression, same head-to-body proportion and drawing method (keep it chibi / simple if the original is chibi / simple), same composition, same background, same line flow — do not change, add or remove any layout element. Do not beautify, do not add detail; keep the original rough hand-drawn feel, line weight, flat color blocks and simple shapes.\n\nDelete every element of the original image that belongs to the original character\'s identity — original hairstyle, hair color, eye color, outfit, accessories, identity marks — and keep ONLY the identity of the character in image 2 / image 3. Same character as the reference images: use exactly the locked identity anchors and nothing more, never add extra accessories or marks the character does not have: [IDENTITY ANCHORS — 只列 character.md 已冻结项，如：心形发夹在右、两支一字夹在左、左右耳发不对称配色、渐变发尖、瞳色；出现手部才写美甲色].\n\nHands: if the original artwork shows hands, paint sakura pink nails; if the original shows no hands, do not draw hands at all.\n\nIf clothing appears, strictly replace the original costume with the outfit and accessories from image 2 / image 3 — same garments, same design, same colors.\n\nKeep the existing text area of the original untouched and clean (do not redraw or invent any text); no new text, no watermark. If the original is a black-and-white line-art style, keep the result black-and-white line art in the same style, using light soft shading to represent the gradient hair tip colors. Clean high resolution, same aspect ratio as the original.', note: '槽位：图1 原图放编辑/图生图输入位，图2/3 放参考位；Kontext Dev 约束最强' },
    { zh: '焚诀·描改主模板（中文版）', en: '描改任务：把图 1 的表情包重绘为图 2、图 3 中的角色。\n\n版式严格沿用原表情包：相同的姿态、相同的手势、相同的表情、相同的头身比例与画法（原本是 Q 版就保持 Q 版，原本简笔就保持简笔）、相同的构图、相同的背景、相同的线条走势——不改变、不增加、不删除版式里的任何元素。不许美化、不许加细节，保留原表情包粗糙的手绘感、线宽、平涂色块与简单形状。\n\n删除掉原表情包内代表原角色身份信息的内容（原发型/原发色/原瞳色/原服装/原配饰/原身份标记），只保留图 2 和图 3 参考图中的角色信息；与参考图为同一角色，身份锚点宁少勿多、不得多加：[身份锚点——只列 character.md 已冻结项，如：人物右侧心形发夹、左侧两个一字发夹、左右耳发不对称颜色、渐变发尖、瞳色；出现手部时才写美甲；原图无手则不画手]。\n\n如果出现手部，樱粉色美甲；原表情包内没有手部出现则不画。\n\n如果涉及到出现角色的服饰，严格按照图 2 和图 3 参考角色的服饰和配饰等将原表情包角色服饰做替换——同款、同设计、同配色。\n\n原表情包已有的文字区域保持原样、保持干净（不许重画或编造文字）；不出现新文字、无水印。如果原表情包是黑白线条样式，那么也要遵循同步修正为黑白线条风格，用淡阴影表示渐变的发尖颜色；干净高分辨率，比例与原件一致。', note: '中文版用于 Grok 等多语言模型对照；身份锚点块与 EN 版保持一致' },
    { zh: '焚诀·描改 negative', en: 'photorealistic, 3d render, semi-realistic, changed pose, flipped pose, changed expression, different composition, original character features remaining, original hairstyle kept, original hair color kept, original eye color kept, original outfit kept, extra accessories, added identity marks, missing identity anchors, mirrored accessories, newly drawn hands, extra hands, hands where the original has none, wrong hair color, wrong eye color, changed layout, added elements, extra characters, realistic or adult proportions, beautified, over-detailed rendering, colorized when the original is monochrome line art, garbled text, invented text, watermark, blurry, cropped', note: '三大翻车点：原角色身份残留（发型/服装/配色没删干净）＋锚点多加或丢失＋原图没手却画手；黑白原图被上色' }
  ]

const CONFUSED: string[][] = [
    ['from above', "overhead / bird's eye", '任意高于眼位的俯角 vs 正上方垂直往下', "日常俯写 from above + 度数；完全垂直才写 overhead / bird's eye"],
    ['close-up', 'portrait / bust / upper body', '脸 / 头肩 / 胸 / 腰 的裁切边界', '四选一不叠写；半身主力 bust shot，头像用 portrait'],
    ['dutch angle', 'tilt', '画面旋转（斜）vs 镜头俯仰（上下摆）', '静态图只有 dutch 有效；tilt 是运动术语'],
    ['wide shot', 'full body', '人小环境大 vs 人占满画面高度', '要环境写 wide shot；要人写 full body'],
    ['pov', 'over-the-shoulder', '机位=角色眼睛 vs 越过前景肩膀', '代入感最强 pov；保留旁观感用 OTS，可叠写'],
    ['rule of space', 'negative space', '视线/运动方向留白（功能）vs 空本身是内容（情绪）', '叙事留白用前者、情绪留白用后者，可同时用'],
    ['symmetrical', 'centered', '含环境的镜像对称 vs 仅主体居中', '要仪式感写 symmetrical；单纯居中写 centered'],
    ['one-point perspective', 'two-point perspective', '一个灭点 vs 两个灭点', '正面纵深用一点；街角双墙用两点'],
    ['foreshortening', 'wide angle', '近大远小的现象 vs 造成夸张的镜头属性', '肢体冲镜头写 foreshortening；整幅空间拉深写 wide angle'],
    ['cctv angle', 'high angle', '监控的冷感+广角+高角 vs 普通俯角', '要被观察感写 surveillance / cctv；只要俯视写 high angle']
  ]

const PITFALLS: string[][] = [
    ['from above + eye-level 同写', '机位打架，模型随机选一个', '垂直角只留一个'],
    ['close-up + full body 同写', '裁切混乱', '景别只留一个'],
    ["high angle + from above + bird's eye 三连", '同义堆叠：token 浪费 + 语义打架', '一个角度词 + 度数即可'],
    ['写了构图词但不写留白内容', '模型自由发挥加戏', '留白里写清是什么：empty street / negative space'],
    ['dutch 40°+ 配正脸大特写', '脸必歪（fx 实测）', '日常斜切 ≤15°；极端斜切慎配脸'],
    ['把 tilt 当 dutch 写', '无效果', '静态图写 dutch angle'],
    ['远景里要求眼部/细节描写', '细节要不到', '描述预算按景别分配；要细节就换近景别'],
    ['negative 里写了正向要的词（如 low angle）', '正负打架，效果抵消', '出图前对一遍正负词表'],
    ['垫图句不带锁定词', '机位漂移', '加 same camera angle and composition as the reference'],
    ['双人/多人不写左右与朝向', '空间乱、越轴', '写清「左/右 + 面朝方向」锁轴线']
  ]

const picked = ref<string[]>([])
const query = ref<string>('')
const activeSec = ref<string>('all')
const q = computed<string>(() => query.value.trim().toLowerCase())

interface FlatSecItem extends SecItem {
  secId: string
  secTitle: string
}

interface DetailData {
  secTitle: string
  zh: string
  en: string
  note: string
  dia: string
  parts: string
  nl: string
  nlc: string
  ex: string
  sayEn: string
  sayCn: string
  extra: string
  url: string
  rows: string[][]
}

const detail = ref<DetailData | null>(null)

const openKey = ref<string | null>(null)
const TRAY_LS = 'suli-composition-tray'
let trayInit = true
try { trayInit = localStorage.getItem(TRAY_LS) !== '0' } catch {}
const trayOpen = ref<boolean>(trayInit)
function toggleTray(): void {
  trayOpen.value = !trayOpen.value
  try { localStorage.setItem(TRAY_LS, trayOpen.value ? '1' : '0') } catch {}
}

function isOpen(key: string): boolean {
  return openKey.value === key
}
function toggleDetail(key: string, build?: () => void): void {
  if (openKey.value === key) {
    openKey.value = null
    return
  }
  if (build) build()
  openKey.value = key
}

const secChips = computed<{ id: string; title: string }[]>(() => [
  { id: 'all', title: '全部' },
  ...SECTIONS.map((s: Sec): { id: string; title: string } => ({ id: s.id, title: s.title })),
])

function hit(...fields: string[]): boolean {
  if (!q.value) return true
  return fields.join(' ').toLowerCase().includes(q.value)
}

function exText(en: string): string {
  const e: string = EX[en]
  return e ? '例：' + e : ''
}

function nlWord(en: string): NlWord | undefined {
  const w: NlWord | undefined = NL[en]
  return w
}

function nlEn(en: string): string {
  const w: NlWord | undefined = NL[en]
  return w ? '说法：' + w.en : ''
}

function nlCn(en: string): string {
  const w: NlWord | undefined = NL[en]
  return w ? w.cn : ''
}

const glossary: GlossRow[] = []
for (const sec of SECTIONS) {
  for (const it of sec.items) {
    const w: NlWord | undefined = NL[it.en]
    glossary.push({ zh: it.zh, tag: EX[it.en] || it.en, en: w ? w.en : '', cn: w ? w.cn : '' })
  }
}

const filteredSecs = computed<FlatSecItem[]>(() => {
  const out: FlatSecItem[] = []
  for (const sec of SECTIONS) {
    if (activeSec.value !== 'all' && sec.id !== activeSec.value) continue
    for (const it of sec.items) {
      if (!hit(it.zh, it.en, it.note, sec.title)) continue
      out.push({ ...it, secId: sec.id, secTitle: sec.title })
    }
  }
  return out
})

const filteredCombos = computed<Combo[]>(() =>
  COMBOS.filter((c: Combo): boolean => hit(c.zh, c.en, c.note, c.parts, c.nl)),
)

const filteredProcombos = computed<Combo[]>(() =>
  PROCOMBOS.filter((c: Combo): boolean => hit(c.zh, c.en, c.note, c.parts, c.nl)),
)

const filteredQuick = computed<string[][]>(() =>
  QUICK.filter((r: string[]): boolean => hit(r[0] ?? '', r[1] ?? '', r[2] ?? '')),
)

const filteredPosecam = computed<string[][]>(() =>
  POSECAM.filter((r: string[]): boolean => hit(r[0] ?? '', r[1] ?? '', r[2] ?? '')),
)

const filteredTools = computed<string[][]>(() =>
  TOOLS.filter((r: string[]): boolean => hit(r[0] ?? '', r[1] ?? '', r[2] ?? '')),
)

const filteredJargon = computed<string[][]>(() =>
  JARGON.filter((r: string[]): boolean => hit(r[0] ?? '', r[1] ?? '', r[2] ?? '')),
)

const filteredFreq = computed<string[][]>(() =>
  FREQ.filter((r: string[]): boolean => hit(r[0] ?? '', r[1] ?? '', r[2] ?? '')),
)

const filteredConfused = computed<string[][]>(() =>
  CONFUSED.filter((r: string[]): boolean => hit(r[0] ?? '', r[1] ?? '', r[2] ?? '', r[3] ?? '')),
)

const filteredPitfalls = computed<string[][]>(() =>
  PITFALLS.filter((r: string[]): boolean => hit(r[0] ?? '', r[1] ?? '', r[2] ?? '')),
)

const filteredCheats = computed<Cheat[]>(() =>
  CHEATS.filter((c: Cheat): boolean => hit(c.zh, c.en, c.note)),
)

const filteredTrace = computed<Cheat[]>(() =>
  TRACE.filter((c: Cheat): boolean => hit(c.zh, c.en, c.note)),
)

const filteredNlways = computed<NlWay[]>(() =>
  NLWAYS.filter((w: NlWay): boolean => hit(w.name, w.en, w.cn)),
)

const filteredPairs = computed<string[][]>(() =>
  PAIRS.filter((p: string[]): boolean => hit(p[0] ?? '', p[1] ?? '', p[2] ?? '', p[3] ?? '')),
)

const filteredDissects = computed<Dissect[]>(() =>
  DISSECTS.filter((d: Dissect): boolean => hit(d.zh, d.en, d.cn, d.tag)),
)

const filteredGloss = computed<GlossRow[]>(() =>
  glossary.filter((g: GlossRow): boolean => hit(g.zh, g.tag, g.en, g.cn)),
)

const filteredRes = computed<ResItem[]>(() =>
  RESOURCES.filter((r: ResItem): boolean => hit(r.t, r.url, r.note, r.lang)),
)

const totalCount = computed<number>(
  () =>
    filteredSecs.value.length +
    filteredCombos.value.length +
    filteredProcombos.value.length +
    filteredQuick.value.length +
    filteredPosecam.value.length +
    filteredTools.value.length +
    filteredJargon.value.length +
    filteredFreq.value.length +
    filteredConfused.value.length +
    filteredPitfalls.value.length +
    filteredCheats.value.length +
    filteredTrace.value.length +
    filteredNlways.value.length +
    filteredPairs.value.length +
    filteredDissects.value.length +
    filteredGloss.value.length +
    filteredRes.value.length,
)

function toggleSec(id: string): void {
  if (activeSec.value === id) {
    activeSec.value = 'all'
    return
  }
  activeSec.value = id
}

function clearFilter(): void {
  query.value = ''
  activeSec.value = 'all'
}

function openSec(it: FlatSecItem): void {
  detail.value = {
    secTitle: it.secTitle,
    zh: it.zh,
    en: it.en,
    note: it.note,
    dia: it.dia,
    parts: '',
    nl: '',
    nlc: '',
    ex: exText(it.en),
    sayEn: nlEn(it.en),
    sayCn: nlCn(it.en),
    extra: '',
    url: '',
    rows: [],
  }
}

function openCombo(c: Combo, secTitle: string): void {
  detail.value = {
    secTitle,
    zh: c.zh,
    en: c.en,
    note: c.note,
    dia: c.dia,
    parts: c.parts,
    nl: c.nl,
    nlc: c.nlc,
    ex: '',
    sayEn: '',
    sayCn: '',
    extra: '',
    url: '',
    rows: [],
  }
}

function openRow(zh: string, en: string, note: string, secTitle: string, extra = ''): void {
  detail.value = {
    secTitle,
    zh,
    en,
    note,
    dia: '',
    parts: '',
    nl: '',
    nlc: '',
    ex: '',
    sayEn: '',
    sayCn: '',
    extra,
    url: '',
    rows: [],
  }
}

function openCheat(c: Cheat, secTitle: string): void {
  detail.value = {
    secTitle,
    zh: c.zh,
    en: c.en,
    note: c.note,
    dia: '',
    parts: '',
    nl: '',
    nlc: '',
    ex: '',
    sayEn: '',
    sayCn: '',
    extra: '',
    url: '',
    rows: [],
  }
}

function openNlway(w: NlWay): void {
  detail.value = {
    secTitle: '自然语言法',
    zh: w.name,
    en: w.en,
    note: w.cn,
    dia: '',
    parts: '',
    nl: '',
    nlc: '',
    ex: '',
    sayEn: '',
    sayCn: '',
    extra: '',
    url: '',
    rows: [],
  }
}

function openPair(p: string[]): void {
  detail.value = {
    secTitle: '活感工作台',
    zh: '死：' + (p[0] ?? '') + ' → 活：' + (p[1] ?? ''),
    en: p[2] ?? '',
    note: p[3] ?? '',
    dia: '',
    parts: '',
    nl: '',
    nlc: '',
    ex: '',
    sayEn: '',
    sayCn: '',
    extra: '死句：' + (p[0] ?? '') + ' ｜ 活句：' + (p[1] ?? ''),
    url: '',
    rows: [],
  }
}

function openDissect(d: Dissect): void {
  detail.value = {
    secTitle: '拆解实战',
    zh: d.zh,
    en: d.en,
    note: d.cn,
    dia: '',
    parts: '',
    nl: d.en,
    nlc: d.cn,
    ex: '',
    sayEn: '',
    sayCn: '',
    extra: '词表版：' + d.tag,
    url: '',
    rows: d.rows,
  }
}

function openGloss(g: GlossRow): void {
  detail.value = {
    secTitle: '名词案例',
    zh: g.zh,
    en: g.en || g.tag,
    note: g.cn,
    dia: '',
    parts: '',
    nl: g.en,
    nlc: g.cn,
    ex: '',
    sayEn: '',
    sayCn: '',
    extra: '词表式：' + g.tag,
    url: '',
    rows: [],
  }
}

function openRes(r: ResItem): void {
  detail.value = {
    secTitle: '教学资源',
    zh: r.t,
    en: r.url,
    note: r.note,
    dia: '',
    parts: '',
    nl: '',
    nlc: '',
    ex: '',
    sayEn: '',
    sayCn: '',
    extra: '语言：' + r.lang,
    url: r.url,
    rows: [],
  }
}

async function copyDetailEn(): Promise<void> {
  if (!detail.value) return
  await copyOne(detail.value.en, '已复制：' + detail.value.zh)
}

async function addDetailPick(): Promise<void> {
  if (!detail.value) return
  await addPick(detail.value.en, detail.value.zh)
}

async function copyDetailNl(): Promise<void> {
  if (!detail.value || !detail.value.nl) return
  await copyOne(detail.value.nl, '已复制自然语言版：' + detail.value.zh)
}

function openDetailUrl(): void {
  if (!detail.value || !detail.value.url) return
  window.open(detail.value.url, '_blank', 'noopener')
}

async function copyOne(t: string, msg: string): Promise<void> {
  await copyText(t)
  ElMessage.success(msg)
}

async function addPick(en: string, label: string): Promise<void> {
  await copyText(en)
  ElMessage.success('已复制并加入组合：' + label)
  if (!picked.value.includes(en)) picked.value.push(en)
}

function removePick(i: number): void {
  picked.value.splice(i, 1)
}

function clearAll(): void {
  picked.value = []
}

async function copyAllLine(): Promise<void> {
  if (picked.value.length === 0) {
    ElMessage.warning('组合栏是空的，先点卡片')
    return
  }
  const s: string = picked.value.join(', ')
  await copyText(s)
  ElMessage.success('已复制镜头句：' + s)
}
</script>

<style scoped>
.comp-cam {
  background: #fff;
  color: var(--suli-text);
  padding-bottom: 16px;
  min-width: 0;
}
.tray {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #fff;
  border-bottom: 1px solid var(--suli-border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 10px 16px;
  margin: -8px -8px 12px;
}
.tray-inner {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.tray-label {
  font-size: 13px;
  color: var(--suli-text-2);
  white-space: nowrap;
}
.chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  flex: 1;
  min-height: 28px;
  align-items: center;
}
.empty-hint {
  font-size: 13px;
}
.pick-tag {
  font-family: Consolas, monospace;
  max-width: 100%;
}
.pick-tag :deep(.el-tag__content) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.intro {
  padding: 18px 20px;
  margin-bottom: 16px;
}
.intro h1 {
  font-size: 22px;
  color: var(--suli-text);
  margin: 0 0 8px;
}
.intro p {
  margin: 0;
  color: var(--suli-text);
  font-size: 14px;
  line-height: 1.8;
}
.intro code {
  background: #f4f4f6;
  border: 1px solid var(--suli-border);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: Consolas, monospace;
}
.search {
  max-width: 300px;
}
.tray-search {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--suli-border);
}
.chip {
  cursor: pointer;
}
.count {
  font-size: 12px;
  white-space: nowrap;
}
.comp-cam {
  --suli-primary: #FB7299;
  --suli-border: #e4e4e7;
}
.suli-card {
  background: #fff;
  border: 1px solid var(--suli-border);
  border-radius: 12px;
}
.suli-muted {
  color: #71717a;
  font-size: 13px;
}
pre.suli-pre {
  background: #fafafa;
  border: 1px solid var(--suli-border);
  border-radius: 8px;
  padding: 8px 10px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12.5px;
  margin: 0;
}
.mono {
  font-family: Consolas, monospace;
}
.tip {
  font-size: 13px;
  margin-bottom: 12px;
  line-height: 1.7;
}
.subh {
  font-size: 14px;
  font-weight: 600;
  margin: 18px 0 8px;
  color: var(--suli-text);
}
.block {
  padding: 16px 20px 20px;
  margin-bottom: 16px;
}
.block h2,
.block h3 {
  font-size: 16px;
  margin: 0 0 4px;
  color: var(--suli-text);
}
.block h2 small,
.block h3 small {
  font-weight: 400;
  color: var(--suli-text-2);
  font-size: 12px;
  margin-left: 8px;
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}
.tool-card {
  cursor: pointer;
  overflow: hidden;
  min-width: 0;
  transition: transform 0.12s, box-shadow 0.12s;
}
.tool-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(251, 114, 153, 0.18);
  border-color: var(--suli-primary);
}
.tool-card .cover :deep(.dia) {
  width: 100%;
  height: auto;
  max-height: 240px;
  display: block;
  background: #fff1f4;
  border-bottom: 1px solid var(--suli-border);
}
.tool-card .body {
  padding: 10px 12px 12px;
  min-width: 0;
}
.tool-card .t-zh {
  font-size: 14px;
  font-weight: 700;
  color: var(--suli-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tool-card .t-en {
  font-size: 12px;
  color: #71717a;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tool-card .pills {
  margin-top: 6px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.tool-card .t-note {
  font-size: 12px;
  color: var(--suli-text-2);
  margin-top: 6px;
  line-height: 1.6;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dlg .pills {
  margin-bottom: 10px;
}
.dlg-cover :deep(.dia) {
  width: 100%;
  height: auto;
  display: block;
  background: #fff1f4;
  border: 1px solid var(--suli-border);
  border-radius: 10px;
  margin-bottom: 12px;
}
.dlg .row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  align-items: flex-start;
}
.dlg .k {
  flex: none;
  width: 88px;
  font-size: 12px;
  color: #71717a;
  padding-top: 2px;
}
.dlg .v {
  flex: 1;
  font-size: 13px;
  line-height: 1.7;
  min-width: 0;
  word-break: break-word;
}
.dlg-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}
.drow {
  padding: 8px 0;
  border-top: 1px dashed var(--suli-border);
}
.tool-card.open { grid-column: span 2; border-color: var(--suli-primary,#FB7299); }
.detail-block { margin-top:10px; border-top:1px dashed var(--suli-border); padding-top:10px; }
.detail-cols { display:grid; grid-template-columns:220px 1fr; gap:12px; }
.detail-main { min-width: 0; }
.detail-main:only-child { grid-column: 1 / -1; }
.detail-cover :deep(.dia) {
  width: 100%;
  height: auto;
  display: block;
  background: #fff1f4;
  border: 1px solid var(--suli-border);
  border-radius: 10px;
}
@media (max-width: 640px) {
  .detail-cols { grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); }
}
.foot {
  font-size: 12.5px;
  line-height: 1.8;
  padding: 12px 4px 0;
  margin: 0;
}
@media (max-width: 560px) {
  .card-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 8px;
  }
  .block {
    padding: 12px 12px 14px;
  }
  .intro {
    padding: 14px 12px;
  }
  .tray {
    padding: 8px 10px;
  }
}

@container (max-width: 620px) {
  .card-grid { grid-template-columns: repeat(2, 1fr); }
  .detail-cols { grid-template-columns: 1fr; }
}
@container (max-width: 400px) {
  .card-grid { grid-template-columns: 1fr; }
}
/* pack-slots: backpack face */
.tool-card > .body > .pills, .tool-card > .body > .t-note { display: none; }
.tool-card > .body > .t-zh, .tool-card > .body > .t-en { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tool-card.open { box-shadow: 0 0 0 2px rgba(251,114,153,.45), 0 8px 20px rgba(251,114,153,.25); }</style>
