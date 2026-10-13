#!/usr/bin/env python3
"""The comparison page: every variant's numbers, a to-scale plan of each hole
layout, and every sheet's preview, built from square_flute.py's own build()
so the page cannot disagree with the cut files.

    python3 compare_page.py OUT.html               # for an artifact: no <head>
    python3 compare_page.py --standalone OUT.html  # a whole page, for GitHub Pages

Both need the previews to exist, since it inlines them.
"""
import html
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import square_flute as F                                       # noqa: E402
import your_flute as Y                                         # noqa: E402
import plus_flute as P                                         # noqa: E402
M = F.M


def plan(L, holes, diams, wall, label, plus=False):
    """The flute from above, to scale: mouth at the left."""
    wc = F.SAC + F.PLUG + M.WINDOW_L / 2
    total = wc + L + M.FOOT_SPARE
    W, y0 = 26.0, 14.0
    yc = y0 + W / 2
    s = []
    s.append(f'<rect class="body" x="0" y="{y0}" width="{total:.1f}" height="{W}"/>')
    s.append(f'<rect class="sac" x="0" y="{y0}" width="{F.SAC}" height="{W}"/>')
    s.append(f'<rect class="plug" x="{F.SAC}" y="{y0}" width="{F.PLUG}" height="{W}"/>')
    s.append(f'<rect class="trim" x="{wc + L:.1f}" y="{y0}" width="{M.FOOT_SPARE}" height="{W}"/>')
    hx = [wc + h for h in holes]
    if wall > F.T:
        z0, z1 = min(hx) - F.DOUBLER_PAST, max(hx) + F.DOUBLER_PAST
        s.append(f'<rect class="dbl" x="{z0:.1f}" y="{y0 + 1.5}" width="{z1 - z0:.1f}" '
                 f'height="{W - 3}"/>')
    o = W / 2 - 3 if plus else 5          # -plus: exit hole and window the bore's width
    s.append(f'<rect class="cut" x="{F.SAC - F.EXIT_L}" y="{yc - o}" width="{F.EXIT_L}" height="{2 * o}"/>')
    s.append(f'<rect class="cut" x="{F.SAC + F.PLUG}" y="{yc - o}" width="{M.WINDOW_L}" height="{2 * o}"/>')
    for x, d, n in zip(hx, diams, range(1, 6)):
        s.append(f'<circle class="cut" cx="{x:.1f}" cy="{yc}" r="{d / 2:.2f}"/>')
        s.append(f'<text class="num" x="{x:.1f}" y="{y0 + W + 9}">{n}</text>')
        s.append(f'<text class="dia" x="{x:.1f}" y="{y0 - 4}">ø{d:.1f}</text>')
    s.append(f'<text class="tag" x="{F.SAC / 2}" y="{yc + 2.5}">slow air chamber</text>')
    # between the foot-most hole and the trim, the one clear stretch of the
    # sound chamber the holes do not crowd
    s.append(f'<text class="tag" x="{(max(hx) + wc + L) / 2:.1f}" y="{yc + 2.5}">sound chamber</text>')
    s.append(f'<text class="end" x="{total + 4:.1f}" y="{yc + 2.5}">{total:.0f}</text>')
    return (f'<figure class="plan"><figcaption>{html.escape(label)}</figcaption>'
            f'<div class="scroll"><svg viewBox="-2 0 {total + 34:.0f} {y0 + W + 14}" '
            f'role="img" aria-label="{html.escape(label)}: plan view to scale, holes '
            f'{", ".join(f"{h:.0f}" for h in holes)}mm from the window">'
            + ''.join(s) + '</svg></div></figure>')


def inline_svg(path):
    s = open(path).read()
    s = re.sub(r'<\?xml[^>]*>\s*', '', s)
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    s = re.sub(r'(<svg[^>]*?)\swidth="[^"]*"\sheight="[^"]*"', r'\1', s, count=1)
    return s



def solids(kind, W, D, wall, parts, info):
    """Every part as a flat outline, its holes, and where it stands: a 3x4
    matrix taking the part's own (x, y, extrusion) to the flute's (x along,
    y across, z up), plus the way it moves when the view is exploded.

    Physical outlines, before the kerf: this is the flute, not the sheet."""
    T, PW = F.T, info['PW']
    out = []
    plate = lambda z0: [[1, 0, 0, 0], [0, 1, 0, -PW / 2], [0, 0, 1, z0]]
    k_plug = k_bird = k_side = k_bore = 0
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
            e = [-1.2 - 0.25 * k_plug, 0, 0]
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
        else:
            raise ValueError(f'no place for a {n}')
        out.append({'o': [[round(x, 3), round(y, 3)] for x, y in p.outline],
                    'h': holes, 'm': [[round(v, 4) for v in r] for r in m],
                    'e': e, 'g': g, 'n': p.num, 'name': n,
                    'f': [[[round(x, 3), round(y, 3)] for x, y in f] for f in p.fills]})
    return {'parts': out, 'len': round(info['total'], 1), 'W': round(W, 2),
            'D': round(D, 2), 'top': round(2 * T + D + (T if wall > T else 0), 2)}


VIEWER = r"""
<section class="viewer" id="turn" aria-label="Turn it in 3D">
  <h2>Turn it in 3D</h2>
  <div class="vbar" role="group" aria-label="Variant">__BUTTONS__</div>
  <div class="stage" id="stage"><canvas id="cv" aria-label="The selected variant in 3D. Drag to turn, scroll or pinch to zoom."></canvas>
    <p class="vinfo" id="vinfo"></p></div>
  <div class="vctl">
    <label for="explode">Explode</label><input id="explode" type="range" min="0" max="1" step="0.01" value="0">
    <button type="button" id="vreset">Reset view</button>
    <label class="chk"><input type="checkbox" id="xray"> See through the walls</label>
  </div>
  <p class="note">Drag to turn, scroll or pinch to zoom. The parts are the generator's own outlines before the kerf, so this is the flute as built: the box's fingers in their notches, flush to the outside, the four plug discs, the stack's seven bore layers with the plug left solid, the doubler, and the bird over the exit hole. In the first six the flue is engraved in the bird's underside, shown blue; in the <code>-plus</code> variants and the 2017 flute it is engraved in the top plate over the plug, where the bird covers it.</p>
</section>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function () {
  const DATA = __DATA__;
  if (!window.THREE) { document.getElementById('vinfo').textContent = 'The 3D view needs three.js, which did not load.'; return; }
  const css = getComputedStyle(document.documentElement);
  const tok = n => new THREE.Color(css.getPropertyValue(n).trim() || '#888');
  const cv = document.getElementById('cv'), stage = document.getElementById('stage');
  const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(32, 2, 1, 5000);
  camera.up.set(0, 0, 1);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8070, 0.85));
  const sun = new THREE.DirectionalLight(0xffffff, 0.75); sun.position.set(-300, -500, 700); scene.add(sun);
  const mats = {};
  function material(g) {
    const base = { plate: '#d9c6a0', wall: '#cdb68a', plug: '#a98d5f', dbl: '#e2d2b0', bird: '#b8925c' }[g];
    return new THREE.MeshStandardMaterial({ color: base, roughness: 0.85, metalness: 0, transparent: true, opacity: 1 });
  }
  const flueMat = new THREE.MeshBasicMaterial({ color: 0x2f5bff });
  const edgeMat = new THREE.LineBasicMaterial({ color: 0x3b2f20, transparent: true, opacity: 0.55 });
  let group = null, meshes = [], cur = null;
  function shapeOf(o) { const s = new THREE.Shape(); o.forEach((p, i) => i ? s.lineTo(p[0], p[1]) : s.moveTo(p[0], p[1])); s.closePath(); return s; }
  function build(name) {
    if (group) { scene.remove(group); group.traverse(o => { if (o.geometry) o.geometry.dispose(); }); }
    group = new THREE.Group(); meshes = [];
    const d = DATA[name];
    d.parts.forEach(p => {
      const s = shapeOf(p.o);
      p.h.forEach(h => {
        const path = new THREE.Path();
        if (h.c) path.absarc(h.c[0], h.c[1], h.c[2], 0, Math.PI * 2, true);
        else h.p.forEach((q, i) => i ? path.lineTo(q[0], q[1]) : path.moveTo(q[0], q[1]));
        s.holes.push(path);
      });
      const geo = new THREE.ExtrudeGeometry(s, { depth: 3, bevelEnabled: false, curveSegments: 24 });
      const mat = mats[p.g] || (mats[p.g] = material(p.g));
      const mesh = new THREE.Mesh(geo, mat);
      const holder = new THREE.Group();
      holder.add(mesh);
      holder.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo, 30), edgeMat));
      p.f.forEach(f => {   // the flue, drawn on the face the bird lies on
        const fg = new THREE.ShapeGeometry(shapeOf(f));
        const fm = new THREE.Mesh(fg, flueMat); fm.position.z = -0.05; holder.add(fm);
      });
      const m = p.m, M = new THREE.Matrix4();
      M.set(m[0][0], m[0][1], m[0][2], m[0][3], m[1][0], m[1][1], m[1][2], m[1][3], m[2][0], m[2][1], m[2][2], m[2][3], 0, 0, 0, 1);
      holder.matrixAutoUpdate = false; holder.userData = { M, e: p.e };
      group.add(holder); meshes.push(holder);
    });
    scene.add(group);
    cur = d;
    target.set(d.len / 2, 0, d.top / 2);
    document.getElementById('vinfo').textContent = name + ' · ' + d.parts.length + ' parts · ' + d.len.toFixed(0) + 'mm · bore ' + d.W.toFixed(2) + ' × ' + d.D.toFixed(2) + 'mm';
    place(); render();
  }
  const target = new THREE.Vector3();
  let yaw = -0.65, pitch = 0.42, dist = 600;
  const home = { yaw: -0.65, pitch: 0.42, dist: 600 };
  const ex = document.getElementById('explode'), xr = document.getElementById('xray');
  function place() {
    const k = parseFloat(ex.value) * 28;
    meshes.forEach(h => {
      const T = new THREE.Matrix4().makeTranslation(h.userData.e[0] * k, h.userData.e[1] * k, h.userData.e[2] * k);
      h.matrix.copy(T.multiply(h.userData.M));
    });
    Object.entries(mats).forEach(([g, m]) => { m.opacity = xr.checked && (g === 'wall' || g === 'plate' || g === 'dbl') ? 0.28 : 1; m.depthWrite = !(xr.checked && g !== 'plug' && g !== 'bird'); });
  }
  function render() {
    camera.position.set(target.x + dist * Math.cos(pitch) * Math.sin(yaw), target.y - dist * Math.cos(pitch) * Math.cos(yaw), target.z + dist * Math.sin(pitch));
    camera.lookAt(target);
    renderer.render(scene, camera);
  }
  function size() {
    const w = stage.clientWidth, h = Math.max(260, Math.min(520, w * 0.55));
    renderer.setSize(w, h, false); cv.style.height = h + 'px'; camera.aspect = w / h; camera.updateProjectionMatrix(); render();
  }
  const pts = new Map(); let pinch0 = 0, dist0 = dist;
  cv.addEventListener('pointerdown', e => { cv.setPointerCapture(e.pointerId); pts.set(e.pointerId, { x: e.clientX, y: e.clientY }); if (pts.size === 2) { const [a, b] = [...pts.values()]; pinch0 = Math.hypot(a.x - b.x, a.y - b.y); dist0 = dist; } });
  cv.addEventListener('pointermove', e => {
    if (!pts.has(e.pointerId)) return;
    const prev = pts.get(e.pointerId); pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pts.size === 1) { yaw += (e.clientX - prev.x) * 0.008; pitch = Math.max(-1.45, Math.min(1.45, pitch + (e.clientY - prev.y) * 0.008)); }
    else if (pts.size === 2 && pinch0) { const [a, b] = [...pts.values()]; dist = Math.max(120, Math.min(2000, dist0 * pinch0 / Math.hypot(a.x - b.x, a.y - b.y))); }
    render();
  });
  const up = e => { pts.delete(e.pointerId); if (pts.size < 2) pinch0 = 0; };
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
  cv.addEventListener('wheel', e => { e.preventDefault(); dist = Math.max(120, Math.min(2000, dist * (1 + Math.sign(e.deltaY) * 0.08))); render(); }, { passive: false });
  ex.addEventListener('input', () => { place(); render(); });
  xr.addEventListener('change', () => { place(); render(); });
  document.getElementById('vreset').addEventListener('click', () => { ({ yaw, pitch, dist } = home); ex.value = 0; place(); render(); });
  document.querySelectorAll('.vbar button').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.vbar button').forEach(x => x.setAttribute('aria-pressed', x === b));
    build(b.dataset.v);
  }));
  window.addEventListener('resize', size);
  build(Object.keys(DATA)[0]); size();
})();
</script>
"""

def main(out, standalone=False):
    designs = {}
    rows, cards, plans = [], [], []
    three, yours_cards = {}, []
    done_plans = set()
    every = ([(n, v, False) for n, v in F.VARIANTS.items()]
             + [(n, v, True) for n, v in P.VARIANTS.items()])
    for name, (kind, W, D, wall), plus in every:
        key = (round(W, 4), round(D, 4), wall, plus)
        if key not in designs:
            designs[key] = (P.design(W, D, wall) if plus
                            else M.design(M.Bore(W, D), wall, even=True))
        L, holes, diams, cents = designs[key]
        parts, info = (P.build if plus else F.build)(kind, W, D, wall, L, holes, diams)
        sheets = F.pack(parts)
        three[name] = solids(kind, W, D, wall, parts, info)
        if (wall, plus) not in done_plans:
            done_plans.add((wall, plus))
            plans.append((wall, L, holes, diams, plus))
        how = {'box': 'Finger-jointed box', 'stack': 'Laminated stack'}[kind]
        if plus:
            glued = ('doubler, cap and bird glued; the rest press-fit' if kind == 'box' and wall > 3
                     else 'cap and bird glued; the rest press-fit' if kind == 'box'
                     else 'every layer and the cap glued')
        else:
            glued = ('doubler, bird and cap glued; the rest press-fit' if kind == 'box' and wall > 3
                     else 'bird and cap glued; the rest press-fit' if kind == 'box'
                     else 'every layer and the cap glued')
        rows.append(f'<tr><th scope="row"><code>{name}</code></th><td>{how}</td>'
                    f'<td class="n">{W:.2f} × {D:.2f}</td><td class="n">{wall:g}</td>'
                    f'<td class="n">{L:.1f}</td><td class="n">{info["total"]:.0f} × {info["PW"]:.1f}</td>'
                    f'<td class="n">{len(parts)}</td><td class="n">{len(sheets)}</td>'
                    f'<td>{glued}</td></tr>')
        counts = {}
        for p in parts:
            counts[p.name] = counts.get(p.name, 0) + 1
        plist = ', '.join(f'{n} {k}' if n == 1 else f'{n} × {k}' for k, n in counts.items())
        imgs = []
        for k in range(1, len(sheets) + 1):
            f = os.path.join(HERE, 'previews', name,
                             f'square-flute-A4-{name}-sheet{k}-cut-files.svg')
            imgs.append(f'<div class="sheet">{inline_svg(f)}'
                        f'<p class="cap">sheet {k} of {len(sheets)} · '
                        f'{sheets[k - 1]["w"]:.0f} × {sheets[k - 1]["h"]:.0f}mm</p></div>')
        cards.append(f'<section class="variant" id="{name}"><h3><code>{name}</code></h3>'
                     f'<p class="meta">{how} · bore {W:.2f} × {D:.2f}mm · holes in '
                     f'{wall:g}mm of wall · {glued}</p><p class="parts">{plist}</p>'
                     + ''.join(imgs) + '</section>')
    for kind in ('flat', 'fingers'):
        parts = Y.build(kind)
        three['yours-' + kind] = solids('yours', Y.W, Y.D, Y.T, parts,
                                        {'PW': Y.PW, 'total': Y.TOTAL, 'plug': Y.PLUG[0]})
        imgs = []
        sheets = Y.pack(parts)
        for k in range(1, len(sheets) + 1):
            f = os.path.join(HERE, 'yours', 'previews', kind,
                             f'your-flute-{kind}-sheet{k}-cut-files.svg')
            imgs.append(f'<div class="sheet">{inline_svg(f)}<p class="cap">your flute, {kind}, '
                        f'sheet {k} of {len(sheets)} · {sheets[k - 1]["w"]:.0f} × '
                        f'{sheets[k - 1]["h"]:.0f}mm</p></div>')
        yours_cards.append(''.join(imgs))
    yL, yholes, yfs = Y.predict()
    want = [0, 300, 500, 700, 1000, 1200]
    JUST = [(1, 1), (6, 5), (4, 3), (3, 2), (9, 5), (2, 1)]
    yrows = ''.join(
        f'<tr><th scope="row">{n} open</th><td class="n">{f:.0f}Hz</td>'
        f'<td class="n">{Y.note(f)[0]} {Y.note(f)[1]:+.0f}c</td>'
        f'<td class="n">{1200 * math.log2(f / yfs[0]):.0f}c</td><td class="n">{want[n]}c</td>'
        f'<td class="n">{JUST[n][0]}:{JUST[n][1]}, {1200 * math.log2(JUST[n][0] / JUST[n][1]):.1f}c</td></tr>'
        for n, f in enumerate(yfs))
    ref = M.design(M.Bore(), 5.0, even=True)
    plan_html = ''.join(plan(L, h, d, w, f'Holes in {w:g}mm of wall'
                             + (', full-width window (-plus)' if pl else '')
                             + f' — sound chamber {L:.1f}mm, cut {L + M.FOOT_SPARE:.1f}', pl)
                        for w, L, h, d, pl in plans)
    hole_rows = []
    labels = [f'{w:g}mm wall' + (', -plus' if pl else '') for w, L, h, d, pl in plans]
    for (w, L, h, d, pl), lab in zip(plans + [(5.0,) + ref[:3] + (False,)],
                                     labels + ['round reference, 5mm wall']):
        hole_rows.append(f'<tr><th scope="row">{lab}</th><td class="n">{L:.1f}</td>'
                         + ''.join(f'<td class="n">{x:.1f}<span>ø{dd:.1f}</span></td>'
                                   for x, dd in zip(h, d)) + '</tr>')
    page = TEMPLATE.format(rows=''.join(rows), cards=''.join(cards), plans=plan_html,
                           yrows=yrows, ysheets=''.join(yours_cards), yL=yL,
                           holes=''.join(hole_rows), sq=F.SQ, rw=F.RW, area=M.AREA,
                           spacing=M.SPACING, spare=M.FOOT_SPARE)
    import json
    buttons = ''.join(f'<button type="button" data-v="{n}" aria-pressed="{str(i == 0).lower()}">'
                      f'<code>{n}</code></button>' for i, n in enumerate(three))
    viewer = VIEWER.replace('__BUTTONS__', buttons).replace(
        '__DATA__', json.dumps(three, separators=(',', ':')))
    page = page.replace('<!--VIEWER-->', viewer)
    if standalone:
        page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                + page.replace('<main>', '</head>\n<body>\n<main>', 1)
                + '</body>\n</html>\n')
    open(out, 'w').write(page)
    print(f'  wrote {out}: {len(rows)} variants, {len(plans)} layouts')


TEMPLATE = '''<title>Square-Bore A4 Flute</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700&family=IBM+Plex+Sans:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* layout: one reading column, drawings and tables break out wider and scroll on their own */
:root {{
  --bg: #f6f7f4; --fg: #1d232b; --muted: #5a636d; --rule: #d6dad3;
  --panel: #ffffff; --accent: #a85800; --ink: #0000ff; --birch: #e7dcc4; --plug: #b9a37a;
  --display: "Barlow Semi Condensed", "Arial Narrow", sans-serif;
  --body: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #15191e; --fg: #e6e9ec; --muted: #9aa4ad; --rule: #2c333b;
  --panel: #1d232a; --accent: #f0a04b; --ink: #8fa8ff; --birch: #4a4234; --plug: #7d6c4c;
  color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --bg: #15191e; --fg: #e6e9ec; --muted: #9aa4ad; --rule: #2c333b;
  --panel: #1d232a; --accent: #f0a04b; --ink: #8fa8ff; --birch: #4a4234; --plug: #7d6c4c;
  color-scheme: dark; }}
body {{ margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.6 var(--body); }}
main {{ max-width: 1080px; margin: 0 auto; padding-inline: 20px; padding-block: 32px 64px;
  display: grid; gap: 40px; }}
.col {{ max-width: 68ch; display: grid; gap: 14px; }}
h1, h2, h3 {{ font-family: var(--display); line-height: 1.1; text-wrap: balance; margin: 0; }}
h1 {{ font-size: clamp(34px, 6vw, 56px); font-weight: 700; letter-spacing: -0.01em; }}
h2 {{ font-size: 28px; font-weight: 600; }}
h3 {{ font-size: 20px; font-weight: 600; }}
p {{ margin: 0; }}
.eyebrow {{ font: 500 13px var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }}
.lede {{ font-size: 19px; }}
code {{ font-family: var(--mono); font-size: .9em; }}
.findings {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }}
.finding {{ border-top: 3px solid var(--accent); padding-top: 10px; display: grid; gap: 6px; min-width: 0; }}
.finding b {{ font-family: var(--display); font-size: 19px; font-weight: 600; }}
.scroll {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--rule); vertical-align: top; }}
thead th {{ font: 500 12px var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }}
th code {{ white-space: nowrap; }}
td.n {{ font-variant-numeric: tabular-nums; font-family: var(--mono); white-space: nowrap; }}
td.n span {{ display: block; color: var(--muted); font-size: 12px; }}
.plan {{ margin: 0; display: grid; gap: 6px; }}
.plan figcaption {{ font: 500 13px var(--mono); color: var(--muted); }}
.plan svg {{ width: 100%; min-width: 760px; display: block; }}
.plan .body {{ fill: var(--birch); stroke: var(--fg); stroke-width: .4; }}
.plan .sac {{ fill: var(--panel); opacity: .55; }}
.plan .plug {{ fill: var(--plug); }}
.plan .trim {{ fill: var(--accent); opacity: .25; }}
.plan .dbl {{ fill: none; stroke: var(--fg); stroke-width: .5; stroke-dasharray: 2 1.5; }}
.plan .cut {{ fill: var(--bg); stroke: var(--accent); stroke-width: .6; }}
.plan text {{ fill: var(--fg); font-family: var(--mono); text-anchor: middle; }}
.plan .num {{ font-size: 6px; }}
.plan .dia {{ font-size: 5px; fill: var(--muted); }}
.plan .tag {{ font-size: 6px; fill: var(--muted); }}
.plan .end {{ font-size: 6px; text-anchor: start; }}
.key {{ display: flex; flex-wrap: wrap; gap: 8px 20px; font-size: 13px; color: var(--muted); }}
.key i {{ display: inline-block; width: 14px; height: 10px; margin-right: 6px; vertical-align: -1px; border: 1px solid var(--fg); }}
.variants {{ display: grid; gap: 36px; }}
.variant {{ display: grid; gap: 10px; min-width: 0; }}
.meta {{ color: var(--muted); font-size: 14px; }}
.parts {{ font-size: 14px; }}
.sheet {{ background: #ffffff; border: 1px solid var(--rule); border-radius: 4px; padding: 10px; display: grid; gap: 6px; }}
.sheet svg {{ width: 100%; height: auto; display: block; }}
.sheet .cap {{ font: 12px var(--mono); color: #5a636d; }}
ol, ul {{ margin: 0; padding-left: 1.3em; display: grid; gap: 6px; }}
.viewer {{ display: grid; gap: 12px; min-width: 0; }}
.vbar {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.vbar button, .vctl button {{ font: 500 13px var(--mono); color: var(--fg); background: var(--panel); border: 1px solid var(--rule); border-radius: 4px; padding: 6px 10px; cursor: pointer; }}
.vbar button[aria-pressed="true"] {{ border-color: var(--accent); box-shadow: inset 0 -3px 0 var(--accent); }}
.vbar button:focus-visible, .vctl button:focus-visible, .vctl input:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
.stage {{ position: relative; background: var(--panel); border: 1px solid var(--rule); border-radius: 6px; overflow: hidden; touch-action: none; }}
.stage canvas {{ display: block; width: 100%; cursor: grab; }}
.vinfo {{ position: absolute; left: 12px; bottom: 10px; font: 12px var(--mono); color: var(--muted); pointer-events: none; }}
.vctl {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px 16px; font-size: 14px; }}
.vctl input[type=range] {{ width: min(260px, 60vw); accent-color: var(--accent); }}
.vctl .chk {{ display: inline-flex; gap: 6px; align-items: center; }}
.note {{ border-left: 3px solid var(--rule); padding-left: 14px; color: var(--muted); font-size: 15px; }}
</style>
<main>
<header class="col">
  <p class="eyebrow">LaserMadeMusic · design study</p>
  <h1>Square-Bore A4 Flute</h1>
  <p class="lede">A five-hole minor-pentatonic flute in A4, in the Native American style, rebuilt in 3mm ply with
  the bore area of a 7/8in round-bore flute: {area:.0f}mm², the same air column in a section a laser can build.
  Six variants from one acoustic model, the same six again with the ideas of the 2017 flute folded in, and that flute
  itself, redrawn.</p>
</header>

<section class="findings" aria-label="What the model says">
  <div class="finding"><b>Bore shape barely matters</b><p>A {sq:.2f}mm square and an {rw:.2f} × 21mm rectangle of the same
  area put every hole within 0.1mm of each other. Box or stack is a building choice, not an acoustic one.</p></div>
  <div class="finding"><b>Wall thickness matters most</b><p>Moving the holes from 3mm of wall to 6mm moves every one of them
  10–16mm toward the window, because a hole's chimney is part of its length.</p></div>
  <div class="finding"><b>Lay it out for the hands</b><p>Equal holes land 27, 30, 46 and 12mm apart. Holes 3 + 2, {spacing:.0f}mm
  apart within each hand, with each hole sized to its note, puts the gap between the hands where it belongs.</p></div>
</section>

<!--VIEWER-->

<section class="col" style="max-width:none">
  <h2>The hole layouts</h2>
  <p class="col">Plan view to scale, mouth on the left. Distances are from the window centre. The shaded end is the
  {spare:.0f}mm cut long to trim to pitch.</p>
  {plans}
  <div class="key"><span><i style="background:var(--plug)"></i>plug</span><span><i style="background:var(--accent);opacity:.4"></i>trim to pitch</span><span><i style="border-style:dashed;background:none"></i>doubler, 6mm wall</span><span>numbers below: holes from the foot · above: diameter</span></div>
  <div class="scroll"><table>
    <thead><tr><th>Note</th><th>Interval from A4</th><th>Ratio from A4</th><th>Step from the note below</th><th>Just, cents</th><th>Tuned to, cents</th></tr></thead>
    <tbody>
      <tr><th scope="row">A4</th><td>unison</td><td class="n">1:1</td><td></td><td class="n">0</td><td class="n">0</td></tr>
      <tr><th scope="row">C5</th><td>minor third</td><td class="n">6:5</td><td>6:5, a minor third</td><td class="n">315.6</td><td class="n">300</td></tr>
      <tr><th scope="row">D5</th><td>perfect fourth</td><td class="n">4:3</td><td>10:9, a minor whole tone</td><td class="n">498.0</td><td class="n">500</td></tr>
      <tr><th scope="row">E5</th><td>perfect fifth</td><td class="n">3:2</td><td>9:8, a major whole tone</td><td class="n">702.0</td><td class="n">700</td></tr>
      <tr><th scope="row">G5</th><td>minor seventh</td><td class="n">9:5</td><td>6:5, a minor third</td><td class="n">1017.6</td><td class="n">1000</td></tr>
      <tr><th scope="row">A5</th><td>octave</td><td class="n">2:1</td><td>10:9, a minor whole tone</td><td class="n">1200.0</td><td class="n">1200</td></tr>
    </tbody>
  </table></div>
  <p class="col">The scale as ratios: steps of 6:5, 10:9, 9:8, 6:5 and 10:9, two minor thirds and three whole tones and no
  semitone anywhere. The
  model tunes to equal temperament, the last column, within 18 cents of every just ratio; the minor seventh can also be
  taken as 16:9 (996.1 cents) or the harmonic 7:4 (968.8).</p>
  <div class="scroll"><table>
    <thead><tr><th>Holes in</th><th>Sound chamber</th><th>Hole 1 (C5)</th><th>Hole 2 (D5)</th><th>Hole 3 (E5)</th><th>Hole 4 (G5)</th><th>Hole 5 (A5)</th></tr></thead>
    <tbody>{holes}</tbody>
  </table></div>
</section>

<section class="col" style="max-width:none">
  <h2>All twelve variants</h2>
  <p class="col">Every variant carries the 2017 flute's mouthpiece cap, with its half-round notch in the bottom edge.
  Each <code>-plus</code> variant is the one above it with three more of that flute's ideas: a window and an exit hole
  the whole width of the bore, the flue engraved in the nest rather than the bird, and a soft depression round every
  finger hole. The wider window has the
  smaller end correction, so the model puts the foot 16.5–18mm further down. The 2017 flute's engraved splitting edge
  is not among them, since it charred, and nor is its stepped block, which was for looks only.</p>
  <div class="scroll"><table>
    <thead><tr><th>Variant</th><th>Construction</th><th>Bore, mm</th><th>Hole wall</th><th>Sound chamber</th><th>Flute, mm</th><th>Parts</th><th>Sheets</th><th>Joints</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <p class="note">A laminated square bore is missing on purpose. A stack's depth is a whole number of 3mm layers, 18 or
  21mm, and {sq:.2f} is neither, so the stack keeps the area and gives up the square.</p>
</section>

<section class="col">
  <h2>Building any of them</h2>
  <ol>
    <li><b>Flue.</b> The bottom bird layer carries the flue as a 10mm-wide fill engrave. Set its depth to about 1mm on scrap
    first; it is the one dimension here that is a power setting rather than a cut.</li>
    <li><b>Splitting edge.</b> File the window's downstream edge to a bevel of about 30°. The top is cut as a short head
    plate and a long body plate, so a spoilt edge costs the short one.</li>
    <li><b>Assemble.</b> Box: press-fit, then shellac every seam. Stack: glue the layers in order against a straightedge.
    The doubler and the bird are glued in both.</li>
    <li><b>Tune the fundamental.</b> With every hole closed, trim the foot until it sounds A4.</li>
    <li><b>Tune the holes.</b> Work up from hole 1, opening each hole slightly with a file if it is flat. Each hole nudges
    the ones above it.</li>
  </ol>
  <p class="note">The window's end correction is the uncalibrated term: each 1mm of it moves the foot about 4.5mm, or 2.6mm
  with a full-width window. That is why the foot is cut long. The holes move with it almost as far, 2.3–3.0mm for the
  foot's 3.5mm, so trimming the foot does not tune them: each is tuned in turn, and only a flat hole can be fixed. The
  first build to be cut and played will set the term for the rest. Flutopedia's bore table also puts A4
  nearer a 3/4in bore than 7/8in, so this reference is on the large side for its key.</p>
</section>

<section class="col" style="max-width:none" id="yours">
  <h2>The author's flute</h2>
  <p class="col">Designed, cut and played in 2017, and kept here as it was in <code>yours/original/</code>. Its bore is
  19.37 × 22.44mm, 435mm², and its window runs the whole width of the bore. It tried an engraved splitting edge, a
  greyscale ramp beside the window meant to let the laser cut the bevel; that did not work, so the edge is filed by
  hand here as in every variant above. Each finger hole also sits in a soft engraved depression for the finger.</p>
  <p class="col">Redrawn as <code>yours-flat</code> and <code>yours-fingers</code> in the 3D view, with the window, every
  hole and the foot where they were. Millimetre-true, kerf-compensated, in the house colours and numbered; the plug made
  four 3mm discs, 12mm, by moving the exit hole 1mm toward the mouth; the ramp left out and the top cut as a head plate
  and a body plate, so a spoilt edge costs the short one; and in the fingers build the top finger-jointed like the bottom,
  so it press-fits.</p>
  <div class="scroll"><table>
    <thead><tr><th>Holes open</th><th>Model</th><th>Note</th><th>Above the fundamental</th><th>Minor pentatonic</th><th>Just ratio</th></tr></thead>
    <tbody>{yrows}</tbody>
  </table></div>
  <p class="note">What the model hears in it, sound chamber {yL:.1f}mm. The shape of the scale agrees to within 40 cents
  at every hole. The pitch, near B♭4, uses the same uncalibrated window term as everything else here. The 2017 flutes have
  all been given away, so none can be measured: the first of these builds to be cut and played will set that term.</p>
  {ysheets}
</section>

<section class="variants" aria-label="Cut sheets">
  <h2>Every cut sheet</h2>
  {cards}
</section>
</main>
'''

if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if x != '--standalone']
    if len(a) != 1:
        raise SystemExit('usage: compare_page.py [--standalone] OUT.html')
    sys.exit(main(a[0], standalone='--standalone' in sys.argv))
