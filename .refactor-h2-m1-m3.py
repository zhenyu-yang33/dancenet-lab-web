#!/usr/bin/env python3
"""Apply H2 (dnc rAF), M3 (PAGE_HOOKS + showPage), M1 (hydrateStaticAssetUrls)."""
from pathlib import Path

p = Path(__file__).resolve().parent / "index.html"
t = p.read_text(encoding="utf-8")

ANCHOR = """    return new URL(relPath.replace(/^\\//, ''), u.origin + path).href;
}

/** 实验 01 封面视频播放速率（1 = 原速，越小越慢） */
"""

INSERT = """    return new URL(relPath.replace(/^\\//, ''), u.origin + path).href;
}

/** 当前 SPA 路由（与 `showPage('…')` / `#page-…` 一致）。 */
let __dncActivePage = 'home';

/**
 * 装饰性 canvas 循环：离页时不再链式 requestAnimationFrame，回页时统一 kick。
 * （实验台 exp1AnimateLoop / exp1 导出 / 模态动画等仍自行管理 rAF。）
 */
const __dncDecorLoops = new Map();
function dncRegisterDecorLoop(id, pageId, tick) {
    const st = { raf: 0, pageId, tick };
    function step() {
        st.raf = 0;
        if (__dncActivePage !== st.pageId) return;
        st.tick();
        st.raf = requestAnimationFrame(step);
    }
    function kick() {
        if (st.raf) return;
        if (__dncActivePage !== st.pageId) return;
        st.raf = requestAnimationFrame(step);
    }
    __dncDecorLoops.set(id, kick);
    kick();
}
function dncNotifyDecorLoops() {
    for (const kick of __dncDecorLoops.values()) kick();
}

/**
 * 将静态 HTML 里 `src` / `poster` 指向的 `assets/…` 改写成与 resolveMediaUrl 一致的绝对 URL，
 * 修复 GitHub Pages 子路径、无尾斜杠等场景下 video/img 与 JS 加载不一致的问题。
 */
function hydrateStaticAssetUrls(root) {
    const R = root || document;
    R.querySelectorAll('[src], [poster]').forEach((el) => {
        ['src', 'poster'].forEach((attr) => {
            if (!el.hasAttribute(attr)) return;
            const raw = el.getAttribute(attr);
            if (!raw || /^(data:|https?:|blob:|#)/i.test(raw)) return;
            const rel = raw.replace(/^\\.\\//, '');
            if (rel.startsWith('assets/')) el.setAttribute(attr, resolveMediaUrl(rel));
        });
    });
}

/** 实验 01 封面视频播放速率（1 = 原速，越小越慢） */
"""

if ANCHOR not in t:
    raise SystemExit("anchor after resolveMediaUrl not found")
t = t.replace(ANCHOR, INSERT, 1)

# --- PAGE_HOOKS + showPage ---
OLD_SHOW = """/* ─────────── Page router ─────────── */
function showPage(name) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.getElementById('page-' + name).classList.add('active');
    const navEl = document.getElementById('nav-' + name);
    if (navEl) navEl.classList.add('active');
    // art-flow 子页：让顶栏「光影为媒」继续高亮
    if (name === 'art-flow') document.getElementById('nav-art')?.classList.add('active');
    window.scrollTo({ top: 0 });
    // Lazy init canvases on demand
    requestAnimationFrame(() => {
        if (name === 'home') initHomeCanvases();
        if (name === 'agent') initAgentHero();
        if (name === 'art') initArtCanvases();
        if (name === 'art-flow') initArtFlowPage();
        if (name === 'mr') initMRCanvas();
        if (name === 'aigc') initAIGCCanvas();
        if (name === 'exp1') initExp1Page();
        if (name === 'exp2') initExp2Page();
    });
    // art hero 视频：进入时播放，离开时暂停节省资源
    const artVid = document.getElementById('art-cover-video');
    if (artVid) { name === 'art' ? artVid.play().catch(()=>{}) : artVid.pause(); }
    // 图版 III · 智能觉醒（未「否」封印前为动态视频）：进入光影为媒播放，离开暂停；已封印则仅静止图
    const awakenPlate = document.getElementById('plate-awaken');
    const plateVid = document.getElementById('plate-awaken-video');
    if (plateVid) {
        if (awakenPlate && awakenPlate.classList.contains('ex-plate-sealed')) plateVid.pause();
        else if (name === 'art') schedulePlateAwakenVideoPlay();
        else plateVid.pause();
    }
    const plateIntVid = document.getElementById('plate-interactive-video');
    if (plateIntVid) plateIntVid.pause();
    // exp2: 切走时若摄像头/音乐还开着，先暂停以省资源
    if (name !== 'exp2' && typeof exp2Pause === 'function') exp2Pause();
    // exp1: 切走时停掉动画播放与录制
    if (name !== 'exp1' && typeof exp1Pause === 'function') exp1Pause();
    if (name !== 'exp1') exp1PauseCoverVideo();
    if (name === 'exp1' && _initialized.has('exp1')) {
        requestAnimationFrame(() => requestAnimationFrame(() => exp1ResumeCoverVideo()));
    }
}
"""

NEW_SHOW = """/* ─────────── Page router ─────────── */
const PAGE_HOOKS = {
    art: {
        onEnter() {
            document.getElementById('art-cover-video')?.play().catch(() => {});
            const awakenPlate = document.getElementById('plate-awaken');
            const plateVid = document.getElementById('plate-awaken-video');
            if (plateVid) {
                if (awakenPlate && awakenPlate.classList.contains('ex-plate-sealed')) plateVid.pause();
                else schedulePlateAwakenVideoPlay();
            }
        },
        onLeave() {
            document.getElementById('art-cover-video')?.pause();
            document.getElementById('plate-awaken-video')?.pause();
            document.getElementById('plate-interactive-video')?.pause();
        },
    },
    exp1: {
        onEnter() {
            if (_initialized.has('exp1')) {
                requestAnimationFrame(() => requestAnimationFrame(() => exp1ResumeCoverVideo()));
            }
        },
        onLeave() {
            if (typeof exp1Pause === 'function') exp1Pause();
            exp1PauseCoverVideo();
        },
    },
    exp2: {
        onLeave() {
            if (typeof exp2Pause === 'function') exp2Pause();
        },
    },
};

function showPage(name) {
    const pageEl = document.getElementById('page-' + name);
    if (!pageEl) return;

    const prev = __dncActivePage;
    PAGE_HOOKS[prev]?.onLeave?.(prev, name);

    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    pageEl.classList.add('active');
    const navEl = document.getElementById('nav-' + name);
    if (navEl) navEl.classList.add('active');
    if (name === 'art-flow') document.getElementById('nav-art')?.classList.add('active');

    __dncActivePage = name;

    window.scrollTo({ top: 0 });

    requestAnimationFrame(() => {
        if (name === 'home') initHomeCanvases();
        if (name === 'agent') initAgentHero();
        if (name === 'art') initArtCanvases();
        if (name === 'art-flow') initArtFlowPage();
        if (name === 'mr') initMRCanvas();
        if (name === 'aigc') initAIGCCanvas();
        if (name === 'exp1') initExp1Page();
        if (name === 'exp2') initExp2Page();
    });

    PAGE_HOOKS[name]?.onEnter?.(name, prev);
    dncNotifyDecorLoops();
}
"""

if OLD_SHOW not in t:
    raise SystemExit("old showPage block not found")
t = t.replace(OLD_SHOW, NEW_SHOW, 1)

INIT_MARKER = """/* ─────────── Initial init ─────────── */
bindInteractivePlateHover();
"""

INIT_NEW = """/* ─────────── Initial init ─────────── */
hydrateStaticAssetUrls();
bindInteractivePlateHover();
"""

if INIT_MARKER not in t:
    raise SystemExit("initial init marker not found")
t = t.replace(INIT_MARKER, INIT_NEW, 1)

p.write_text(t, encoding="utf-8")
print("OK: inserted dnc helpers, PAGE_HOOKS, showPage, hydrateStaticAssetUrls()")
