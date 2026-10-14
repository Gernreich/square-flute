#!/usr/bin/env python3
"""The published page's moving parts, built from the generators' own build()
so the page cannot disagree with the cut files. The writeup itself is
README.md, built into index.html by md2html.py like every page here; this
adds what markdown cannot carry.

    python3 page_assets.py                     # viewer.js and plans/*.svg
    python3 page_assets.py --artifact OUT.html # the whole page, one file

  viewer.js    the 3D view of every build. README.md loads it on the page
               through a page-only line, so GitHub, which runs no script,
               shows a link to the page in its place.
  plans/       the two hole layouts drawn to scale, as plain SVG, so they
               read on GitHub as well as on the page.

--artifact folds index.html and viewer.js into one self-contained file for a
claude.ai artifact: the script inlined, every local image a data URI.

There was a second page, variants.html, until 2026-10-13, when the author
asked for the variants and the writeup to be one document.
"""
import base64
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import square_flute as F                                       # noqa: E402
import plus_flute as P                                         # noqa: E402
M = F.M


def solids(kind, W, D, wall, parts, info):
    """Every part as a flat outline, its holes, and where it stands: a 3x4
    matrix taking the part's own (x, y, extrusion) to the flute's (x along,
    y across, z up), plus the way it moves when the view is exploded.

    Physical outlines, before the kerf: this is the flute, not the sheet."""
    T, PW = F.T, info['PW']
    out = []
    plate = lambda z0: [[1, 0, 0, 0], [0, 1, 0, -PW / 2], [0, 0, 1, z0]]
    k_plug = k_bird = k_side = k_bore = 0
    n_plug = sum(p.name == 'plug disc' for p in parts)
    for p in parts:
        holes = []
        for c in p.cuts:
            if c[0] == 'rect':
                holes.append({'p': [[round(x, 3), round(y, 3)] for x, y in c[1]]})
            else:
                holes.append({'c': [round(c[1], 3), round(c[2], 3), round(c[3], 3)]})
        n = p.name
        if n == 'side wall':
            yo = W / 2 if k_side == 0 else -W / 2 - T
            m = [[1, 0, 0, 0], [0, 0, 1, yo], [0, -1, 0, T + D]]
            e = [0, 1 if k_side == 0 else -1, 0]
            k_side += 1
            g = 'wall'
        elif n == 'plug disc':
            m = [[0, 0, 1, info.get('plug', F.SAC) + k_plug * T], [1, 0, 0, -(W + F.INTERF_ACROSS) / 2], [0, 1, 0, T]]
            # the disc nearest the mouth moves furthest, so the gaps only grow;
            # the other way round they passed through each other at a third
            # of the way out and came apart in reverse order (the author, 2026-10-13)
            e = [-1.2 - 0.25 * (n_plug - 1 - k_plug), 0, 0]
            k_plug += 1
            g = 'plug'
        elif n in ('bottom plate', 'bottom layer'):
            m, e, g = plate(0), [0, 0, -1], 'plate'
        elif n == 'bore layer':
            m = plate(T + k_bore * T)
            e = [0, 0, -0.75 + 0.25 * k_bore]
            k_bore += 1
            g = 'wall'
        elif n.startswith('top'):
            m, e, g = plate(T + D), [0, 0, 1.2], 'plate'
        elif n == 'doubler':
            m, e, g = plate(2 * T + D), [0, 0, 1.8], 'dbl'
        elif n == 'mouthpiece cap':
            ch = p.h - (D + 2 * T)
            m = [[0, 0, 1, -T], [1, 0, 0, -p.w / 2], [0, 1, 0, -ch / 2]]
            e, g = [-2.2, 0, 0], 'bird'
        elif n in ('bird layer', 'block layer'):
            m = plate(2 * T + D + k_bird * T)
            e = [0, 0, 2.6 + 0.4 * k_bird]
            k_bird += 1
            g = 'bird'
            if p.fills:
                # the woodland flue is on this layer's underside, which every
                # view from above hides: exploded, it comes out toward the
                # viewer and turns over, flue up (the author: "the bird flue
                # does not show up in the 3D exploded view", 2026-10-13)
                e = [0, -1.6, 1.6]
        else:
            raise ValueError(f'no place for a {n}')
        o = F.end_notch_outline(p) if getattr(p, 'end_notch', None) else p.outline
        out.append({'o': [[round(x, 3), round(y, 3)] for x, y in o],
                    'h': holes, 'm': [[round(v, 4) for v in r] for r in m],
                    'e': e, 'g': g, 'n': p.num, 'name': n,
                    'f': [[[round(x, 3), round(y, 3)] for x, y in f] for f in p.fills],
                    # which face the flue is engraved on: the top plate's upper
                    # face for a plains (nest) flue, the bird's underside for a
                    # woodland one. Until 2026-10-13 every flue was drawn on the
                    # underside, which hid the nest flue inside the bore and made
                    # each bird-flue build and its nest-flue counterpart look identical
                    'ft': n.startswith('top'),
                    'flip': bool(p.fills) and not n.startswith('top'),
                    'zc': round(m[2][3] + T / 2, 3)})
    return {'parts': out, 'len': round(info['total'], 1), 'W': round(W, 2),
            'D': round(D, 2), 'top': round(2 * T + D + (T if wall > T else 0), 2)}


def plan_svg(L, holes, diams, wall, title):
    """One hole layout from above, to scale, mouth on the left. Fixed colours
    on a white ground, like the previews, so it reads on GitHub and in both of
    the page's themes."""
    wc = F.SAC + F.PLUG + M.WINDOW_L / 2
    total = wc + L + M.FOOT_SPARE
    W, y0 = 26.0, 14.0
    yc, o = y0 + W / 2, W / 2 - 3          # openings and flue: the bore's width
    hx = [wc + h for h in holes]
    s = [f'<rect x="-2" y="0" width="{total + 36:.1f}" height="{y0 + W + 14}" fill="#ffffff"/>',
         f'<rect x="0" y="{y0}" width="{total:.1f}" height="{W}" fill="#e7dcc4" stroke="#1d232b" stroke-width=".4"/>',
         f'<rect x="0" y="{y0}" width="{F.SAC}" height="{W}" fill="#f4eee0"/>',
         f'<rect x="{F.SAC}" y="{y0 + 3}" width="{F.PLUG}" height="{W - 6}" fill="none" '
         f'stroke="#8a7350" stroke-width=".5" stroke-dasharray="1.5 1"/>',
         f'<rect x="{wc + L:.1f}" y="{y0}" width="{M.FOOT_SPARE}" height="{W}" fill="#a85800" fill-opacity=".25"/>']
    if wall > F.T:
        z0, z1 = min(hx) - F.DOUBLER_PAST, max(hx) + F.DOUBLER_PAST
        s.append(f'<rect x="{z0:.1f}" y="{y0 + 1.5}" width="{z1 - z0:.1f}" height="{W - 3}" '
                 f'fill="none" stroke="#1d232b" stroke-width=".5" stroke-dasharray="2 1.5"/>')
    s.append(f'<rect x="{F.SAC}" y="{yc - o}" width="{F.PLUG}" height="{2 * o}" fill="#0000ff" fill-opacity=".45"/>')
    for x0, w in ((F.SAC - F.EXIT_L, F.EXIT_L), (F.SAC + F.PLUG, M.WINDOW_L)):
        s.append(f'<rect x="{x0:.1f}" y="{yc - o}" width="{w}" height="{2 * o}" fill="#ffffff" '
                 f'stroke="#a85800" stroke-width=".6"/>')
    t = 'font-family="Helvetica, Arial, sans-serif" text-anchor="middle"'
    for x, d, n in zip(hx, diams, range(1, 6)):
        s.append(f'<circle cx="{x:.1f}" cy="{yc}" r="{d / 2:.2f}" fill="#ffffff" stroke="#a85800" stroke-width=".6"/>')
        s.append(f'<text x="{x:.1f}" y="{y0 + W + 9}" font-size="6" fill="#1d232b" {t}>{n}</text>')
        s.append(f'<text x="{x:.1f}" y="{y0 - 4}" font-size="5" fill="#5a636d" {t}>ø{d:.1f}</text>')
    s.append(f'<text x="{F.SAC / 2}" y="{yc + 2.5}" font-size="6" fill="#5a636d" {t}>slow air chamber</text>')
    s.append(f'<text x="{(max(hx) + wc + L) / 2:.1f}" y="{yc + 2.5}" font-size="6" fill="#5a636d" {t}>sound chamber</text>')
    s.append(f'<text x="{total + 4:.1f}" y="{yc + 2.5}" font-size="6" fill="#1d232b" '
             f'font-family="Helvetica, Arial, sans-serif">{total:.0f}</text>')
    return (f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 0 {total + 36:.0f} {y0 + W + 14}">\n'
            f'<title>{title}</title>\n'
            f'<desc>Display drawing, not a cut file. Plan view to scale, mouth on the left: the slow '
            f'air chamber, the exit hole, the flue over the plug (blue) and the window, the finger '
            f'holes with their diameters above and their numbers below, and the 15mm trimmed to pitch '
            f'at the foot.</desc>\n' + '\n'.join(s) + '\n</svg>\n')


CSS = '#turn{display:grid;gap:12px;margin:8px 0 24px}\n#turn .vbar{display:flex;flex-wrap:wrap;align-items:center;gap:8px}\n#turn .vbar button:disabled{opacity:.45;cursor:default}\n#turn button{font:500 13px ui-monospace,Menlo,monospace;color:var(--fg);background:var(--card);border:1px solid var(--line);border-radius:4px;padding:6px 10px;cursor:pointer}\n#turn .vbar button[aria-pressed="true"]{border-color:var(--accent);box-shadow:inset 0 -3px 0 var(--accent)}\n#turn button:focus-visible,#turn input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}\n#turn .stage{position:relative;background:var(--card);border:1px solid var(--line);border-radius:6px;overflow:hidden;touch-action:none}\n#turn canvas{display:block;width:100%;cursor:grab}\n#turn .vinfo{position:absolute;left:12px;bottom:10px;margin:0;font:12px ui-monospace,Menlo,monospace;color:var(--mut);pointer-events:none}\n#turn .vctl{display:flex;flex-wrap:wrap;align-items:center;gap:10px 16px;font-size:14px}\n#turn input[type=range]{width:min(260px,60vw);accent-color:var(--accent)}\n#turn .chk{display:inline-flex;gap:6px;align-items:center}\n#turn .note{color:var(--mut);font-size:14px;margin:0}'
MARKUP = '<section class="viewer" id="turn" aria-label="Turn it in 3D">\n  <div class="vbar" role="group" aria-label="Build">__BUTTONS__</div>\n  <div class="vbar" role="group" aria-label="Hole wall" id="vwall"><span class="note">Hole wall</span><button type="button" data-w="3" aria-pressed="true">3mm</button><button type="button" data-w="6" aria-pressed="false">6mm, doubled</button></div>\n  <div class="vbar" role="group" aria-label="Flue" id="vflue"><span class="note">Flue in the</span><button type="button" data-f="bird" aria-pressed="true">bird (woodland)</button><button type="button" data-f="nest" aria-pressed="false">nest (plains)</button><button type="button" data-f="savanna" aria-pressed="false">both (savanna)</button></div>\n  <div class="vbar" role="group" aria-label="Joints" id="vjoint"><span class="note">Joints</span><button type="button" data-j="fingers" aria-pressed="true">finger-jointed</button><button type="button" data-j="flat" aria-pressed="false">flat, glued</button></div>\n  <div class="stage" id="stage"><canvas id="cv" aria-label="The selected variant in 3D. Drag to turn, scroll or pinch to zoom."></canvas>\n    <p class="vinfo" id="vinfo"></p></div>\n  <div class="vctl">\n    <label for="explode">Explode</label><input id="explode" type="range" min="0" max="1" step="0.01" value="0">\n    <button type="button" id="vreset">Reset view</button>\n    <label class="chk"><input type="checkbox" id="xray"> See through the walls</label>\n  </div>\n  <p class="note">Drag to turn, scroll or pinch to zoom. The parts are the generator\'s own outlines before the kerf, so this is the flute as built: the box\'s fingers in their notches, flush to the outside, the four plug discs, the stack\'s six bore layers with the plug left solid, the doubler, and the bird over the exit hole. The hole-wall toggle puts the finger holes in the 3mm top alone or through a 3mm doubler glued over it, 6mm in all. The flue toggle swaps each build for its twin: in the bird, the flue is engraved in the bird\'s underside; in the nest, it is engraved in the top plate over the plug, where the bird covers it; in both, the savanna setting, half its depth is in each. The joints toggle swaps a box for the same box butt-jointed, the sides glued between plain top and bottom plates, as the 2017 flute was built; a stack has no joints to choose. Whichever it is, the flue is drawn blue, and exploded, the bird\'s flue layer comes out toward you and turns over so the flue faces up.</p>\n</section>'
JS = "(function () {\n  const DATA = __DATA__;\n  if (!window.THREE) { document.getElementById('vinfo').textContent = 'The 3D view needs three.js, which did not load.'; return; }\n  const css = getComputedStyle(document.documentElement);\n  const tok = n => new THREE.Color(css.getPropertyValue(n).trim() || '#888');\n  const cv = document.getElementById('cv'), stage = document.getElementById('stage');\n  const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, alpha: true });\n  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));\n  const scene = new THREE.Scene();\n  const camera = new THREE.PerspectiveCamera(32, 2, 1, 5000);\n  camera.up.set(0, 0, 1);\n  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8070, 0.85));\n  const sun = new THREE.DirectionalLight(0xffffff, 0.75); sun.position.set(-300, -500, 700); scene.add(sun);\n  const mats = {};\n  function material(g) {\n    const base = { plate: '#d9c6a0', wall: '#cdb68a', plug: '#a98d5f', dbl: '#e2d2b0', bird: '#b8925c' }[g];\n    return new THREE.MeshStandardMaterial({ color: base, roughness: 0.85, metalness: 0, transparent: true, opacity: 1 });\n  }\n  const flueMat = new THREE.MeshBasicMaterial({ color: 0x2f5bff, side: THREE.DoubleSide });   // two-sided: the bird flue faces into the wood, and one-sided it was culled from every side (the author, 2026-10-13)\n  const edgeMat = new THREE.LineBasicMaterial({ color: 0x3b2f20, transparent: true, opacity: 0.55 });\n  let group = null, meshes = [], cur = null;\n  function shapeOf(o) { const s = new THREE.Shape(); o.forEach((p, i) => i ? s.lineTo(p[0], p[1]) : s.moveTo(p[0], p[1])); s.closePath(); return s; }\n  function build(name) {\n    if (group) { scene.remove(group); group.traverse(o => { if (o.geometry) o.geometry.dispose(); }); }\n    group = new THREE.Group(); meshes = [];\n    const d = DATA[name];\n    d.parts.forEach(p => {\n      const s = shapeOf(p.o);\n      p.h.forEach(h => {\n        const path = new THREE.Path();\n        if (h.c) path.absarc(h.c[0], h.c[1], h.c[2], 0, Math.PI * 2, true);\n        else h.p.forEach((q, i) => i ? path.lineTo(q[0], q[1]) : path.moveTo(q[0], q[1]));\n        s.holes.push(path);\n      });\n      const geo = new THREE.ExtrudeGeometry(s, { depth: 3, bevelEnabled: false, curveSegments: 24 });\n      const mat = mats[p.g] || (mats[p.g] = material(p.g));\n      const mesh = new THREE.Mesh(geo, mat);\n      const holder = new THREE.Group();\n      holder.add(mesh);\n      holder.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo, 30), edgeMat));\n      p.f.forEach(f => {   // the flue, on the face it is engraved into\n        const fg = new THREE.ShapeGeometry(shapeOf(f));\n        const fm = new THREE.Mesh(fg, flueMat); fm.position.z = p.ft ? 3.05 : -0.05; holder.add(fm);\n      });\n      const m = p.m, M = new THREE.Matrix4();\n      M.set(m[0][0], m[0][1], m[0][2], m[0][3], m[1][0], m[1][1], m[1][2], m[1][3], m[2][0], m[2][1], m[2][2], m[2][3], 0, 0, 0, 1);\n      holder.matrixAutoUpdate = false; holder.userData = { M, e: p.e, flip: p.flip, zc: p.zc };\n      group.add(holder); meshes.push(holder);\n    });\n    scene.add(group);\n    cur = d;\n    target.set(d.len / 2, 0, d.top / 2);\n    document.getElementById('vinfo').textContent = name + ' · ' + d.parts.length + ' parts · ' + d.len.toFixed(0) + 'mm · bore ' + d.W.toFixed(2) + ' × ' + d.D.toFixed(2) + 'mm';\n    place(); render();\n  }\n  const target = new THREE.Vector3();\n  let yaw = -0.65, pitch = 0.42, dist = 600;\n  const home = { yaw: -0.65, pitch: 0.42, dist: 600 };\n  const ex = document.getElementById('explode'), xr = document.getElementById('xray');\n  function place() {\n    const k = parseFloat(ex.value) * 28;\n    meshes.forEach(h => {\n      const u = h.userData, T = new THREE.Matrix4().makeTranslation(u.e[0] * k, u.e[1] * k, u.e[2] * k);\n      if (u.flip) {   // turned over about its own long axis as it comes out\n        const c = new THREE.Matrix4().makeTranslation(0, 0, u.zc), ci = new THREE.Matrix4().makeTranslation(0, 0, -u.zc);\n        T.multiply(c).multiply(new THREE.Matrix4().makeRotationX(Math.PI * parseFloat(ex.value))).multiply(ci);\n      }\n      h.matrix.copy(T.multiply(u.M));\n    });\n    Object.entries(mats).forEach(([g, m]) => { m.opacity = xr.checked && (g === 'wall' || g === 'plate' || g === 'dbl') ? 0.28 : 1; m.depthWrite = !(xr.checked && g !== 'plug' && g !== 'bird'); });\n  }\n  function render() {\n    camera.position.set(target.x + dist * Math.cos(pitch) * Math.sin(yaw), target.y - dist * Math.cos(pitch) * Math.cos(yaw), target.z + dist * Math.sin(pitch));\n    camera.lookAt(target);\n    renderer.render(scene, camera);\n  }\n  function size() {\n    const w = stage.clientWidth, h = Math.max(260, Math.min(520, w * 0.55));\n    renderer.setSize(w, h, false); cv.style.height = h + 'px'; camera.aspect = w / h; camera.updateProjectionMatrix(); render();\n  }\n  const pts = new Map(); let pinch0 = 0, dist0 = dist;\n  cv.addEventListener('pointerdown', e => { cv.setPointerCapture(e.pointerId); pts.set(e.pointerId, { x: e.clientX, y: e.clientY }); if (pts.size === 2) { const [a, b] = [...pts.values()]; pinch0 = Math.hypot(a.x - b.x, a.y - b.y); dist0 = dist; } });\n  cv.addEventListener('pointermove', e => {\n    if (!pts.has(e.pointerId)) return;\n    const prev = pts.get(e.pointerId); pts.set(e.pointerId, { x: e.clientX, y: e.clientY });\n    if (pts.size === 1) { yaw += (e.clientX - prev.x) * 0.008; pitch = Math.max(-1.45, Math.min(1.45, pitch + (e.clientY - prev.y) * 0.008)); }\n    else if (pts.size === 2 && pinch0) { const [a, b] = [...pts.values()]; dist = Math.max(120, Math.min(2000, dist0 * pinch0 / Math.hypot(a.x - b.x, a.y - b.y))); }\n    render();\n  });\n  const up = e => { pts.delete(e.pointerId); if (pts.size < 2) pinch0 = 0; };\n  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);\n  cv.addEventListener('wheel', e => { e.preventDefault(); dist = Math.max(120, Math.min(2000, dist * (1 + Math.sign(e.deltaY) * 0.08))); render(); }, { passive: false });\n  ex.addEventListener('input', () => { place(); render(); });\n  xr.addEventListener('change', () => { place(); render(); });\n  document.getElementById('vreset').addEventListener('click', () => { ({ yaw, pitch, dist } = home); ex.value = 0; place(); render(); });\n  // one button per construction, and three toggles: the hole wall, 3mm or\n  // 6mm; the flue, in the bird or the nest; and the joints, finger-jointed\n  // or flat and glued. The key is the build's name -- box-square-3-bird-flue,\n  // with -flat for a flat box; a stack has no joints to choose, so that\n  // toggle stands disabled for it\n  let base = document.querySelector('#turn .vbar button[data-v]').dataset.v, wall = '3', flue = 'bird', joint = 'fingers';\n  const wb = [...document.querySelectorAll('#vwall button')], fb = [...document.querySelectorAll('#vflue button')], jb = [...document.querySelectorAll('#vjoint button')];\n  function pick() {\n    const k = base + '-' + wall + '-' + flue + '-flue', flatOk = !!DATA[k + '-flat'];\n    wb.forEach(x => x.setAttribute('aria-pressed', x.dataset.w === wall));\n    fb.forEach(x => x.setAttribute('aria-pressed', x.dataset.f === flue));\n    jb.forEach(x => { x.disabled = !flatOk; x.setAttribute('aria-pressed', flatOk ? x.dataset.j === joint : x.dataset.j === 'fingers'); });\n    build(flatOk && joint === 'flat' ? k + '-flat' : k);\n  }\n  document.querySelectorAll('#turn .vbar button[data-v]').forEach(b => b.addEventListener('click', () => {\n    document.querySelectorAll('#turn .vbar button[data-v]').forEach(x => x.setAttribute('aria-pressed', x === b));\n    base = b.dataset.v; pick();\n  }));\n  wb.forEach(b => b.addEventListener('click', () => { wall = b.dataset.w; pick(); }));\n  fb.forEach(b => b.addEventListener('click', () => { flue = b.dataset.f; pick(); }));\n  jb.forEach(b => b.addEventListener('click', () => { joint = b.dataset.j; pick(); }));\n  window.addEventListener('resize', size);\n  pick(); size();\n})();\n"


VIEWER_JS = r"""// The 3D view of every build, for index.html. Built by page_assets.py from
// the generators' own parts: do not edit by hand.
(function () {
  var mount = document.getElementById('turn3d');
  if (!mount) return;
  var style = document.createElement('style');
  style.textContent = __CSS__;
  document.head.appendChild(style);
  mount.innerHTML = __MARKUP__;
  var s = document.createElement('script');
  s.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
  s.onload = run;
  s.onerror = function () { document.getElementById('vinfo').textContent = 'The 3D view needs three.js, which did not load.'; };
  document.head.appendChild(s);
  function run() {
__JS__
  }
})();
"""


def build_all():
    """Every build's solids, and one plan per wall."""
    three, plans, designs = {}, {}, {}
    every = ([(n, v, F.build) for n, v in F.VARIANTS.items()]
             + [(n, v, P.build) for n, v in P.VARIANTS.items()])
    for name, (kind, W, D, wall), build in every:
        key = (round(W, 4), round(D, 4), wall)
        if key not in designs:
            designs[key] = F.design(W, D, wall)
        L, holes, diams, cents = designs[key]
        kw = {'savanna': True} if name in P.SAVANNA else {}
        parts, info = build(kind, W, D, wall, L, holes, diams, **kw)
        three[name] = solids(kind, W, D, wall, parts, info)
        if wall not in plans:                      # drawn at the square bore
            plans[wall] = (L, holes, diams)
    return three, plans


def viewer_js(three):
    bases = list(dict.fromkeys(re.sub(r'-[36]-(bird|nest|savanna)-flue(-flat)?$', '', n) for n in three))
    buttons = ''.join(f'<button type="button" data-v="{n}" aria-pressed="{str(i == 0).lower()}">'
                      f'<code>{n}</code></button>' for i, n in enumerate(bases))
    js = JS.replace('__DATA__', json.dumps(three, separators=(',', ':')))
    return (VIEWER_JS.replace('__CSS__', json.dumps(CSS))
            .replace('__MARKUP__', json.dumps(MARKUP.replace('__BUTTONS__', buttons)))
            .replace('__JS__', js))


def artifact(out):
    """index.html with viewer.js inlined and every local image a data URI,
    as one file, without the document skeleton the artifact host supplies."""
    page = open(os.path.join(HERE, 'index.html')).read()
    page = page.replace('<script src="viewer.js"></script>',
                        '<script>' + open(os.path.join(HERE, 'viewer.js')).read() + '</script>')

    def data(m):
        src = m.group(1)
        p = os.path.join(HERE, src)
        if src.startswith(('http', 'data:')) or not os.path.exists(p):
            return m.group(0)
        kind = 'image/svg+xml' if src.endswith('.svg') else 'image/png'
        return (f'src="data:{kind};base64,'
                + base64.b64encode(open(p, 'rb').read()).decode() + '"')
    page = re.sub(r'src="([^"]+\.(?:png|svg))"', data, page)
    page = re.sub(r'(?is)<!doctype[^>]*>|</?html[^>]*>|</?body[^>]*>|</?head>', '', page)
    open(out, 'w').write(page)
    print(f'  wrote {out}: {len(page) // 1024}KB')


def main():
    a = sys.argv[1:]
    if a[:1] == ['--artifact'] and len(a) == 2:
        return artifact(a[1])
    # --viewer-to=FILE and --plans-to=DIR write one asset where .repro asks,
    # so the reproduction gate compares them like any other shipped file
    vt = [x.split('=', 1)[1] for x in a if x.startswith('--viewer-to=')]
    pt = [x.split('=', 1)[1] for x in a if x.startswith('--plans-to=')]
    if len(vt) + len(pt) != len(a):
        raise SystemExit('usage: page_assets.py [--viewer-to=FILE] [--plans-to=DIR] '
                         '| --artifact OUT.html')
    three, plans = build_all()
    if vt or not a:
        open(vt[0] if vt else os.path.join(HERE, 'viewer.js'), 'w').write(viewer_js(three))
    if pt or not a:
        d = pt[0] if pt else os.path.join(HERE, 'plans')
        os.makedirs(d, exist_ok=True)
    for wall, (L, holes, diams) in (plans.items() if (pt or not a) else ()):
        f = os.path.join(d, f'square-flute-A4-holes-{wall:g}mm-wall.svg')
        open(f, 'w').write(plan_svg(L, holes, diams, wall,
                                    f'Holes in {wall:g}mm of wall, sound chamber {L:.1f}mm'))
    print(f'  wrote viewer.js: {len(three)} builds; plans: {", ".join(f"{w:g}mm" for w in plans)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
