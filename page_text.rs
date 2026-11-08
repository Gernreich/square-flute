// The page's fixed text, copied from page_assets.py when it moved to Rust
// (2026-11-07): the viewer's style, its markup, its script and the 3D page.
// viewer.js and turn.html are these with the builds' data put in.

pub const CSS: &str = r#"#turn{display:grid;gap:12px;margin:8px 0 24px}
#turn .vbar{display:flex;flex-wrap:wrap;align-items:center;gap:8px}
#turn .vbar button:disabled{opacity:.45;cursor:default}
#turn button{font:500 13px ui-monospace,Menlo,monospace;color:var(--fg);background:var(--card);border:1px solid var(--line);border-radius:4px;padding:6px 10px;cursor:pointer}
#turn .vbar button[aria-pressed="true"]{border-color:var(--accent);box-shadow:inset 0 -3px 0 var(--accent)}
#turn button:focus-visible,#turn input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
#turn .stage{position:relative;background:var(--card);border:1px solid var(--line);border-radius:6px;overflow:hidden;touch-action:none}
#turn canvas{display:block;width:100%;cursor:grab}
#turn .vinfo{position:absolute;left:12px;bottom:10px;margin:0;font:12px ui-monospace,Menlo,monospace;color:var(--mut);pointer-events:none}
#turn .vctl{display:flex;flex-wrap:wrap;align-items:center;gap:10px 16px;font-size:14px}
#turn input[type=range]{width:min(260px,60vw);accent-color:var(--accent)}
#turn .chk{display:inline-flex;gap:6px;align-items:center}
#turn .note{color:var(--mut);font-size:14px;margin:0}
#turn .vhow summary{cursor:pointer;width:max-content;max-width:100%}
#turn .vhow p{margin:6px 0 0}"#;

pub const MARKUP: &str = r#"<section class="viewer" id="turn" aria-label="Turn it in 3D">
  <div class="vbar" role="group" aria-label="Build">__BUTTONS__</div>
  <div class="vbar" role="group" aria-label="Hole wall" id="vwall"><span class="note">Hole wall</span><button type="button" data-w="3" aria-pressed="true">3mm</button><button type="button" data-w="6" aria-pressed="false">6mm, doubled</button></div>
  <div class="vbar" role="group" aria-label="Joints" id="vjoint"><span class="note">Joints</span><button type="button" data-j="fingers" aria-pressed="true">finger-jointed</button><button type="button" data-j="flat" aria-pressed="false">flat, glued</button></div>
  <div class="stage" id="stage"><canvas id="cv" aria-label="The selected variant in 3D. Drag to turn; right-drag, shift-drag or two fingers to pan; scroll or pinch to zoom; double-click a part to turn round it."></canvas>
    <p class="vinfo" id="vinfo"></p></div>
  <div class="vctl">
    <label for="explode">Explode</label><input id="explode" type="range" min="0" max="1" step="0.01" value="0">
    <button type="button" id="vreset">Reset view</button>
    <label class="chk"><input type="checkbox" id="xray"> See through the walls</label>
  </div>
  <details class="note vhow"><summary>How to use this view</summary><p>Drag to turn; right-drag, shift-drag or move two fingers to slide the view; scroll or pinch to zoom in on whatever is under the pointer; double-click a part to turn round it, and Reset view to go back. The parts are the generator's own outlines before the kerf, so this is the flute as built: the box's fingers in their notches, flush to the outside, the four plug discs, the stack's six bore layers with the plug left solid, the doubler, and the bird over the exit hole. The hole-wall toggle puts the finger holes in the 3mm top alone or through a 3mm doubler glued over it, 6mm in all. The joints toggle swaps a box for the same box butt-jointed, the sides glued between plain top and bottom plates, as the 2017 flute was built; a stack has no joints to choose. The flue is drawn in both its halves, the inks of the cut file: red in the bird's underside, magenta in the top plate over the plug, where the bird covers it. Cut either or both. Exploded, the bird's flue layer comes out toward you and turns over so its half faces up.</p></details>
</section>"#;

pub const JS: &str = r#"(function () {
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
  const flueMat = new THREE.MeshBasicMaterial({ color: 0x2f5bff, side: THREE.DoubleSide });   // two-sided: the bird flue faces into the wood, and one-sided it was culled from every side (the author, 2026-10-13)
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
      p.f.forEach(f => {   // the flue, on the face it is engraved into
        const fg = new THREE.ShapeGeometry(shapeOf(f));
        const fm = new THREE.Mesh(fg, p.fc ? new THREE.MeshBasicMaterial({ color: p.fc, side: THREE.DoubleSide }) : flueMat); fm.position.z = p.ft ? 3.05 : -0.05; holder.add(fm);
      });
      const m = p.m, M = new THREE.Matrix4();
      M.set(m[0][0], m[0][1], m[0][2], m[0][3], m[1][0], m[1][1], m[1][2], m[1][3], m[2][0], m[2][1], m[2][2], m[2][3], 0, 0, 0, 1);
      holder.matrixAutoUpdate = false; holder.userData = { M, e: p.e, flip: p.flip, zc: p.zc };
      group.add(holder); meshes.push(holder);
    });
    scene.add(group);
    cur = d;
    target.set(d.len / 2, 0, d.top / 2); homeT.copy(target);
    document.getElementById('vinfo').textContent = name + ' · ' + d.parts.length + ' parts · ' + d.len.toFixed(0) + 'mm · bore ' + d.W.toFixed(2) + ' × ' + d.D.toFixed(2) + 'mm';
    place(); render();
  }
  const target = new THREE.Vector3(), homeT = new THREE.Vector3();
  let yaw = -0.65, pitch = 0.42, dist = 600;
  const home = { yaw: -0.65, pitch: 0.42, dist: 600 };
  const ex = document.getElementById('explode'), xr = document.getElementById('xray');
  function place() {
    const k = parseFloat(ex.value) * 28;
    meshes.forEach(h => {
      const u = h.userData, T = new THREE.Matrix4().makeTranslation(u.e[0] * k, u.e[1] * k, u.e[2] * k);
      if (u.flip) {   // turned over about its own long axis as it comes out
        const c = new THREE.Matrix4().makeTranslation(0, 0, u.zc), ci = new THREE.Matrix4().makeTranslation(0, 0, -u.zc);
        T.multiply(c).multiply(new THREE.Matrix4().makeRotationX(Math.PI * parseFloat(ex.value))).multiply(ci);
      }
      h.matrix.copy(T.multiply(u.M));
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
  const pts = new Map(); let pinch0 = 0, mid0 = null, panning = false;
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
  function under(cx, cy, partOnly) {   // the part under the pointer, else where its ray meets the plane through the target
    const b = cv.getBoundingClientRect();
    ndc.set((cx - b.left) / b.width * 2 - 1, -(cy - b.top) / b.height * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const hit = ray.intersectObjects(meshes, true).find(h => h.object.isMesh);
    if (hit || partOnly) return hit ? hit.point : null;
    const n = camera.getWorldDirection(new THREE.Vector3());
    return ray.ray.intersectPlane(new THREE.Plane().setFromNormalAndCoplanarPoint(n, target), new THREE.Vector3());
  }
  function pan(dx, dy) {   // the model follows the pointer
    const k = 2 * dist * Math.tan(camera.fov * Math.PI / 360) / Math.max(cv.clientHeight, 1);
    target.addScaledVector(new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0), -dx * k)
          .addScaledVector(new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1), dy * k);
  }
  function zoom(s, cx, cy) {   // scale the view about the point under the pointer, which stays where it is on screen
    const nd = Math.max(10, Math.min(2000, dist * s)), p = under(cx, cy);
    if (p) target.sub(p).multiplyScalar(nd / dist).add(p);
    dist = nd;
  }
  const two = () => { const [a, b] = [...pts.values()]; return { h: Math.hypot(a.x - b.x, a.y - b.y), x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }; };
  cv.addEventListener('contextmenu', e => e.preventDefault());
  cv.addEventListener('pointerdown', e => {
    cv.setPointerCapture(e.pointerId); pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
    panning = e.button === 1 || e.button === 2 || e.shiftKey;
    if (pts.size === 2) { mid0 = two(); pinch0 = mid0.h; }
  });
  cv.addEventListener('pointermove', e => {
    if (!pts.has(e.pointerId)) return;
    const prev = pts.get(e.pointerId); pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
    const dx = e.clientX - prev.x, dy = e.clientY - prev.y;
    if (pts.size === 1) {
      if (panning) pan(dx, dy);
      else { yaw += dx * 0.008; pitch = Math.max(-1.45, Math.min(1.45, pitch + dy * 0.008)); }
    } else if (pts.size === 2 && pinch0) {   // two fingers: pinch to zoom, move together to pan
      const m = two(); pan(m.x - mid0.x, m.y - mid0.y); render();
      if (m.h) zoom(pinch0 / m.h, m.x, m.y); mid0 = m; pinch0 = m.h;
    }
    render();
  });
  const up = e => { pts.delete(e.pointerId); if (pts.size < 2) pinch0 = 0; };
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
  cv.addEventListener('wheel', e => { e.preventDefault(); zoom(1 + Math.sign(e.deltaY) * 0.08, e.clientX, e.clientY); render(); }, { passive: false });
  cv.addEventListener('dblclick', e => {   // turn round the part under the pointer from now on
    const p = under(e.clientX, e.clientY, true); if (!p) return;
    const a = target.clone(), t0 = performance.now();
    const step = t => { const k = Math.min(1, (t - t0) / 300); target.lerpVectors(a, p, k * (2 - k)); render(); if (k < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  });
  ex.addEventListener('input', () => { place(); render(); });
  xr.addEventListener('change', () => { place(); render(); });
  document.getElementById('vreset').addEventListener('click', () => { ({ yaw, pitch, dist } = home); target.copy(homeT); ex.value = 0; place(); render(); });
  // one button per construction, and two toggles: the hole wall, 3mm or
  // 6mm, and the joints, finger-jointed or flat and glued. The key is the
  // build's name -- box-square-3,
  // with -flat for a flat box; a stack has no joints to choose, so that
  // toggle stands disabled for it
  let base = document.querySelector('#turn .vbar button[data-v]').dataset.v, wall = '3', joint = 'fingers';
  const wb = [...document.querySelectorAll('#vwall button')], jb = [...document.querySelectorAll('#vjoint button')];
  function pick() {
    const k = base + '-' + wall, flatOk = !!DATA[k + '-flat'];
    wb.forEach(x => x.setAttribute('aria-pressed', x.dataset.w === wall));
    jb.forEach(x => { x.disabled = !flatOk; x.setAttribute('aria-pressed', flatOk ? x.dataset.j === joint : x.dataset.j === 'fingers'); });
    build(flatOk && joint === 'flat' ? k + '-flat' : k);
  }
  document.querySelectorAll('#turn .vbar button[data-v]').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('#turn .vbar button[data-v]').forEach(x => x.setAttribute('aria-pressed', x === b));
    base = b.dataset.v; pick();
  }));
  wb.forEach(b => b.addEventListener('click', () => { wall = b.dataset.w; pick(); }));
  jb.forEach(b => b.addEventListener('click', () => { joint = b.dataset.j; pick(); }));
  window.addEventListener('resize', size);
  pick(); size();
})();
"#;

pub const VIEWER_JS: &str = r#"// The 3D view of every build, for index.html. Built by page_assets.rs from
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
"#;

pub const TURN_PAGE: &str = r#"<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Square-bore flute in 3D</title>
<!-- Written by page_assets.rs: do not edit by hand. -->
<style>
:root{--bg:#fbfbfa;--fg:#1a1c1e;--mut:#5b6067;--line:#e2e4e7;--card:#fff;--accent:#1d4ed8}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#15171a;--fg:#e6e8ea;--mut:#9aa1a9;
--line:#2b2f34;--card:#1b1e22;--accent:#7aa2f7}}
:root[data-theme=dark]{--bg:#15171a;--fg:#e6e8ea;--mut:#9aa1a9;--line:#2b2f34;--card:#1b1e22;--accent:#7aa2f7}
body{margin:0;padding:12px 14px;background:var(--bg);color:var(--fg);
font:14px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
</style>
<script>
/* Follow the theme the site's pages store, so this page matches the hub that frames it. */
(function () {
  var r = document.documentElement;
  function apply() { var t = null; try { t = localStorage.getItem('ctg-theme'); } catch (e) {}
    if (t === 'light' || t === 'dark') r.setAttribute('data-theme', t); else r.removeAttribute('data-theme'); }
  apply(); addEventListener('storage', function (e) { if (e.key === 'ctg-theme') apply(); });
})();
</script>
</head>
<body>
<div id="turn3d"></div><script src="viewer.js"></script>
</body>
</html>
"#;

