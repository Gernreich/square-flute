#!/usr/bin/env python3
"""The author's own flute, from 2017, redrawn: the design in yours/original/
measured, kept where it was played, and tweaked only where a laser or a fit
asked for it.

    python3 your_flute.py --no-write          # the prediction and the checks
    python3 your_flute.py --out=yours/cut-files
    python3 your_flute.py --only=flat --flat --out=DIR

square_flute.py is not touched by any of this, so its builds cannot move:
this file imports its helpers and builds its own parts.

WHAT WAS MEASURED, from yours/original/NAF_flatjoints.svg (Inkscape's 90 units
to the inch, 0.28222mm a unit), along the flute from the mouth end:

  bore              19.37 wide x 22.44mm deep, 434.7mm^2 -- a 23.5mm round
                    bore's area, a little over 15/16in
  slow air chamber  123.5mm to the exit hole, which is 6.0 long
  plug              11.0mm, its top fill-engraved as the flue, full width
  window            6.0 long x 19.37 wide, the whole width of the bore
  sound chamber     313.25mm from the window's centre to the foot
  finger holes      7.73, 7.87, 7.79, 7.79 and 5.47mm, foot-most first,
                    213.9, 185.7, 156.9, 109.5 and 78.0mm from the window
  splitting edge    a grey ramp, 19.4 x 9.9mm, engraved beside the window to
                    cut the bevel by laser. IT DID NOT WORK: the author, on
                    2026-10-13. It stays in yours/original/ as it was, and is
                    not in the redraw
  finger holes      each ringed by a soft engraved depression. They worked,
                    the author recalls, cut on a Glowforge, whose 3D engrave
                    reads grey as depth. An xTool P2S's Grayscale mode in XCS
                    varies power with pixel brightness, which should do the same
  mouthpiece        an end cap 25.89 x 28.89mm. Its 9.59mm circle is centred
                    0.33mm inside one long edge, so cutting both leaves a
                    half-round NOTCH in that edge, not a hole in the middle:
                    the edge goes to the bottom, away from the finger holes,
                    and the notch opens through the bottom wall into the bore.
                    (Read as a centred breath hole until 2026-10-13, when the
                    author pointed it out.)
  block             four layers 25mm wide, 25, 19.8, 15.8 and 12.6 long
  tie               a leather strip 359.6 x 4.6mm

THE TWEAKS, each because something asked for it:

  1. Millimetre-true, the house cut-order colours, kerf-compensated, every
     part numbered. The originals are 1/90in units, colours chosen per job,
     and drawn at size with no kerf.
  2. The plug is four 3mm discs, 12mm, where the original's land was 11: ply
     comes in 3mm. The exit hole moves 1mm toward the mouth to make room;
     the window, every finger hole and the foot stay exactly where they were.
  3. FINGERS: the top is finger-jointed to the sides as the bottom already
     was, so it press-fits instead of being glued. Since 2026-10-13 the joint
     is the trumpet bores' -- 6mm fingers and spaces, no play -- in place of
     the original's 10mm fingers at a mallet fit.
  4. The rings are the original's own image, each kept in the original's
     proportion to its hole, so they follow the re-solved holes. The ramp is left out, because the engraved bevel did not work.
  5. So the splitting edge is filed by hand, before assembly. The top is one
     piece: it was a head plate and a body plate for a while, so a spoilt
     edge would cost only the short one, until the author saw no point in it
     (2026-10-13). The seam it put 20mm past the window cost more than it saved.

AT ITS OWN SIZE the model reads this flute as a minor pentatonic to within
40 cents and puts it near B-flat 4. The builds here are not at its own size.

MATCHED TO box-square-3 (flat-A4 and fingers-A4, matched(), 2026-10-13, at
the author's asking: "the bore length to be the same and the cross section
area the same"). Until then they were the original scaled by 1.0705 to A4,
which left them a bigger bore than every other build here and shorter. Now:

  area      the round reference bore's, 285.0mm^2 at 3/4in, as every build here
            has, in the original's own proportion: 15.69 wide x 18.17mm deep
  length    box-square-3's, end to end: its 354.3mm sound chamber, its window
            centre, and its 15mm to trim at the foot, so 494.8mm overall. The
            slow air chamber comes out 104.0mm, the original's 123.5 shortened
            so the window lands where box-square-3's does
  holes     kept where the original had them, as fractions of the sound
            chamber, so each moves along by 354.3 / 313.25

The length may not move, so solve() sets the WINDOW LENGTH, 7.01mm against
box-square-3's 7.0, for A4 = 440Hz with every hole closed, and bisects each
hole diameter, foot-most first, until its note lands on equal temperament.
They come out 5.24, 4.66, 4.56, 5.11 and 4.87mm, smaller than the original's
7.7s, since a narrower bore needs a smaller hole for the same step. Each
depression keeps the original's proportion to its hole.
"""
import contextlib
import base64
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import square_flute as F                                       # noqa: E402
from square_flute import Part, rect, offset, pack, path, label  # noqa: E402
from square_flute import cap_part, cap_path                      # noqa: E402
M = F.M

T = F.T
W, D = 19.37, 22.44
PW = W + 2 * T                       # 25.37, the original's plate width
TOTAL = 456.70
EXIT = (122.48, 128.48)              # tweak 2: was 123.48 - 129.47
PLUG = (128.48, 140.46)              # four discs, 11.98 = 4 x 3 at the kerf
WIN = (140.46, 146.45)
WC = (WIN[0] + WIN[1]) / 2
HOLES = [357.315, 329.135, 300.375, 252.975, 221.455]    # from the mouth, foot-most first
DIAMS = [7.73, 7.87, 7.79, 7.79, 5.47]
RING = [12.14, 12.14, 12.14, 12.14, 8.56]                # depression image, across
CAP = (25.89, 28.89, 9.59)
NOTCH_IN = F.NOTCH_IN                # the circle's centre, inside the cap's bottom edge
BIRD = [25.0, 19.8, 15.8, 12.6]
STRIP = (359.64, 4.64)

IMG = os.path.join(HERE, 'yours', 'original')


def png(name):
    return 'data:image/png;base64,' + base64.b64encode(
        open(os.path.join(IMG, name), 'rb').read()).decode()


A4_HZ = 440.0
SPARE = 0.0                          # cut this much long at the foot; the original had none
_BASE = dict(W=W, D=D, WIN=WIN, HOLES=HOLES, DIAMS=DIAMS, RING=RING, TOTAL=TOTAL)


def twin():
    """The build of square_flute's this one is matched to: the box, square
    bore, 3mm hole wall -- the same wall and joint as the original. Its
    sound chamber, its window centre and its overall length, foot spare
    included."""
    L, _, _, _ = F.design(F.SQ, F.SQ, T)
    wc = F.SAC + F.PLUG + M.WINDOW_L / 2
    return L, wc, wc + L + M.FOOT_SPARE


def solve(W, D, L, holes, d, wl):
    """The window length and the five hole diameters that put the flute on
    A4 = 440Hz all closed and on C5, D5, E5, G5 and A5 in equal temperament,
    the bore, the sound chamber and the hole positions held. The window sets
    the fundamental, since the length may not move; each hole is bisected
    foot-most first. Five passes, because a closed hole still nudges every
    note below it and the window every note."""
    tg = [A4_HZ * 2 ** (s / 12) for s in M.SEMIS]
    saved = M.WINDOW_W, M.WINDOW_L
    M.WINDOW_W = W
    b = M.Bore(W, D)
    d = list(d)
    try:
        for _ in range(5):
            def g(x):
                M.WINDOW_L = x
                return M.sounding(b, L, holes, 0, T, A4_HZ, d)
            wl = M.bisect(g, A4_HZ, 4.0, 12.0, rising=True)
            M.WINDOW_L = wl
            for n in range(1, 6):
                def f(x, i=n - 1, n=n):
                    ds = d[:]
                    ds[i] = x
                    return M.sounding(b, L, holes, n, T, tg[n], ds)
                d[n - 1] = M.bisect(f, tg[n], 2.0, W - 3.0, rising=True)
        cents = [1200 * math.log2(M.sounding(b, L, holes, n, T, tg[n], d) / tg[n])
                 for n in range(6)]
    finally:
        M.WINDOW_W, M.WINDOW_L = saved
    return wl, d, cents


@contextlib.contextmanager
def matched():
    """The flute redrawn at the bore of square_flute's box-square-3 builds:
    the same cross-section area, the 3/4in round bore's, in the original's
    own proportion of width to depth; and the same length end to end -- the
    same sound chamber, window centre and foot spare, so the same overall
    length. The holes keep their places as fractions of the sound chamber.
    Then the window length and the hole diameters are solved for A4 in equal
    temperament (solve), and each depression kept in the original's
    proportion to its hole. Outside the with block the original stands."""
    g = globals()
    b = _BASE
    wc0 = (b['WIN'][0] + b['WIN'][1]) / 2
    L, wc, total = twin()
    w = math.sqrt(M.AREA * b['W'] / b['D'])
    d_ = M.AREA / w
    s = L / (b['TOTAL'] - wc0)
    holes = [(h - wc0) * s for h in b['HOLES']]
    wl, diams, cents = solve(w, d_, L, holes, b['DIAMS'], M.WINDOW_L)
    win = (wc - wl / 2, wc + wl / 2)
    plug = (win[0] - 4 * T, win[0])
    new = dict(W=w, D=d_, WIN=win, WC=wc, PLUG=plug, EXIT=(plug[0] - F.EXIT_L, plug[0]),
               HOLES=[wc + h for h in holes], DIAMS=diams,
               RING=[x * r0 / d0 for x, r0, d0 in zip(diams, b['RING'], b['DIAMS'])],
               TOTAL=total, SPARE=M.FOOT_SPARE, ET_CENTS=cents, STRETCH=s)
    new['PW'] = new['W'] + 2 * T
    # the cap keeps the original's allowance over the flute's outside
    new['CAP'] = (new['PW'] + (CAP[0] - (b['W'] + 2 * T)),
                  new['D'] + 2 * T + (CAP[1] - (b['D'] + 2 * T)), CAP[2])
    saved = {n: g[n] for n in new if n in g}
    g.update(new)
    try:
        yield
    finally:
        for n in new:
            if n in saved:
                g[n] = saved[n]
            else:
                del g[n]


def fingers_x():
    """square_flute's finger layout, the trumpet bores' joint, kept clear of
    the full-width exit hole and window."""
    return F.fingers_x(TOTAL, (EXIT, WIN))


def plate_with_notches(name, num, note, x0=0.0, x1=None):
    return Part(name, num, F.notched(x0, TOTAL if x1 is None else x1, PW, fingers_x()), note)


def side_with_fingers(num):
    return F.finger_side(TOTAL, D, fingers_x(), num)


def build(kind):
    """Every part, in the flute's own flat coordinates: x from the mouth end,
    y across."""
    num = iter(range(1, 100))
    parts = []
    tn = ('exit hole, window, flue and the finger holes in their depressions; file '
          'the far edge of the window to a bevel before assembly')
    # one piece: `head` and `body` are the same plate, named for its two ends
    if kind == 'fingers':
        head = plate_with_notches('top plate', next(num), tn)
    else:
        head = Part('top plate', next(num), rect(0, 0, TOTAL, PW), tn)
    body = head
    yc = PW / 2
    head.slot(EXIT[0], yc - W / 2, EXIT[1], yc + W / 2)
    head.slot(WIN[0], yc - W / 2, WIN[1], yc + W / 2)
    head.fills.append(rect(PLUG[0], yc - W / 2, PLUG[1], yc + W / 2))   # the flue
    for x, d in zip(HOLES, DIAMS):
        body.hole(x, yc, d)
    body.images = [('ring.png', x - r / 2, yc - r / 2, r, r) for x, r in zip(HOLES, RING)]
    parts.append(head)
    if kind == 'fingers':
        parts.append(plate_with_notches('bottom plate', next(num), 'plain'))
        for k in range(2):
            parts.append(side_with_fingers(next(num)))
    else:
        parts.append(Part('bottom plate', next(num), rect(0, 0, TOTAL, PW), 'plain'))
        for k in range(2):
            parts.append(Part('side wall', next(num), rect(0, 0, TOTAL, D),
                              'glued between the top and the bottom'))
    for k in range(4):
        parts.append(Part('plug disc', next(num),
                          rect(0, 0, W + F.INTERF_ACROSS, D + F.INTERF_ACROSS),
                          'four, press-fit under the flue'))
    parts.append(cap_part(next(num), CAP[0], CAP[1]))
    for k, L in enumerate(BIRD):
        parts.append(Part('block layer', next(num), rect(PLUG[1] - L, 0, PLUG[1], PW),
                          'stepped, front edges together on the window'))
    for p in parts:
        if not hasattr(p, 'images'):
            p.images = []
    return parts


def strip_part():
    p = Part('leather tie', 1, rect(0, 0, STRIP[0], STRIP[1]), 'cut from leather, not ply')
    p.images = []
    return p


def svg(kind, k, n, sheet, what, leather=False):
    blue, orange, black, fills, imgs = [], [], [], [], []
    cache = {}
    for p, sx, sy in sheet['parts']:
        dx, dy = sx - p.x0 + F.KERF / 2, sy - p.y0 + F.KERF / 2
        mv = lambda pts: [(x + dx, y + dy) for x, y in pts]
        if getattr(p, 'notch', None):
            black.append(cap_path(p, dx, dy, F.KERF / 2))
        else:
            black.append(path(mv(offset(p.outline, F.KERF / 2))))
        for c in p.cuts:
            if c[0] == 'rect':
                orange.append(path(mv(offset(c[1], -F.KERF / 2))))
            else:
                orange.append(f'<circle cx="{c[1] + dx:.3f}" cy="{c[2] + dy:.3f}" '
                              f'r="{c[3] - F.KERF / 2:.3f}"/>')
        for f in p.fills:
            fills.append(path(mv(f)))
        for name, x, y, w, h in p.images:
            if name not in cache:
                cache[name] = png(name)
            imgs.append(f'<image x="{x + dx:.3f}" y="{y + dy:.3f}" width="{w:.3f}" '
                        f'height="{h:.3f}" preserveAspectRatio="none" href="{cache[name]}"/>')
        if not leather:
            xs = sorted([p.x0 + 6, p.x0 + p.w - 6]
                        + [c[1] for c in p.cuts if c[0] == 'circle']
                        + [x for c in p.cuts if c[0] == 'rect' for x, _ in c[1]]
                        + [im[1] for im in p.images] + [im[1] + im[3] for im in p.images])
            g0, g1 = max(zip(xs, xs[1:]), key=lambda g: g[1] - g[0])
            h = min(5.0, p.h * 0.3)
            lx, ly = (g0 + g1) / 2, p.y0 + p.h / 2
            if p.name == 'mouthpiece cap':      # clear of the notch, in a top corner
                lx, ly, h = p.x0 + 5, p.y0 + p.h - 4, 3.0
            blue += label(str(p.num), lx + dx, ly + dy, h)
    desc = (f'1 user unit = 1mm. The author\'s 2017 flute, redrawn: {kind}, sheet {k} of {n}: '
            f'{what}. ' + ('Cut from leather, not ply; black cuts. ' if leather else
            f'3mm ply, drawn for a {F.KERF:g}mm kerf. Blue {F.BLUE} engraves: the part numbers, '
            f'the flue as a fill engrave about 1mm deep over the plug, and the depression round '
            f'each finger hole, a greyscale image engrave to set to depth on scrap. File the '
            f'window\'s far edge to a bevel by hand. Orange {F.ORANGE} '
            f'cuts the holes and the window, black {F.BLACK} frees the parts.'))
    g = lambda col, items: (f'  <g fill="none" stroke="{col}" stroke-width="0.2">\n'
                            + ''.join(f'    {i}\n' if i.startswith('<') else f'    <path d="{i}"/>\n'
                                      for i in items) + '  </g>\n')
    return (f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{sheet["w"]:.2f}mm" '
            f'height="{sheet["h"]:.2f}mm" viewBox="0 0 {sheet["w"]:.2f} {sheet["h"]:.2f}">\n'
            f'<title>The author\'s flute, {kind}, sheet {k} of {n}</title>\n<desc>{desc}</desc>\n'
            + (f'  <g id="images">\n' + ''.join(f'    {i}\n' for i in imgs) + '  </g>\n' if imgs else '')
            + (g(F.BLUE, blue) if blue else '')
            + (f'  <g fill="{F.BLUE}" stroke="none">\n'
               + ''.join(f'    <path d="{d}"/>\n' for d in fills) + '  </g>\n' if fills else '')
            + (g(F.ORANGE, orange) if orange else '') + g(F.BLACK, black) + '</svg>\n')


def predict():
    """What the model hears in the original, at its own window and bore.

    The window is the module's global; it is put back afterwards, because
    page_assets.py runs this in the same process as square_flute's builds."""
    saved = M.WINDOW_W, M.WINDOW_L
    M.WINDOW_W, M.WINDOW_L = W, WIN[1] - WIN[0]
    try:
        b = M.Bore(W, D)
        L = TOTAL - WC - SPARE
        holes = [h - WC for h in HOLES]
        fs, near = [], 440.0
        for n in range(6):
            f = M.sounding(b, L, holes, n, T, near * (1.19 if n else 1), DIAMS)
            fs.append(f)
            near = f
    finally:
        M.WINDOW_W, M.WINDOW_L = saved
    return L, holes, fs


NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def note(f):
    n = 12 * math.log2(f / 440) + 69
    r = round(n)
    return f'{NAMES[r % 12]}{r // 12 - 1}', 100 * (n - r)


def checks(kind, parts, sheets):
    out = []
    note_ = lambda ok, what, detail: out.append((ok, what, detail))
    note_(TOTAL + 2 * F.MARGIN <= F.BED[0], 'the longest part fits the bed', f'{TOTAL:.1f}mm')
    note_(abs((PLUG[1] - PLUG[0]) - 4 * T) < 0.05, 'four discs fill the plug land',
          f'{PLUG[1] - PLUG[0]:.2f}mm for 4 x {T:g}')
    note_(PLUG[1] == WIN[0] and EXIT[1] == PLUG[0], 'exit hole, plug and window meet edge to edge',
          f'{EXIT[1]:.2f} / {PLUG[0]:.2f}, {PLUG[1]:.2f} / {WIN[0]:.2f}')
    tops = [p for p in parts if p.name.startswith('top')]
    note_(len(tops) == 1 and tops[0].w == TOTAL, 'the top is one piece',
          f'{len(tops)} plate, {tops[0].w:.1f}mm long')
    cap = [p for p in parts if p.name == 'mouthpiece cap'][0]
    cx, cy, r = cap.notch
    into = cy + r - T - (cap.h - (D + 2 * T)) / 2
    note_(into > 0, 'the cap\'s notch opens into the bore',
          f'{cy + r:.2f}mm deep, {into:.2f}mm past the bottom wall')
    gaps = [HOLES[i] - HOLES[i + 1] - (RING[i] + RING[i + 1]) / 2 for i in range(4)]
    note_(min(gaps) >= 0, 'the depressions do not run into each other',
          f'closest {min(gaps):.1f}mm apart')
    note_(max(RING) <= PW - 2, 'each depression stays on the plate',
          f'{max(RING):.2f}mm on a {PW:.2f}mm plate')
    if kind == 'fingers':
        xs = fingers_x()
        clear = min(min(abs(x - a), abs(x - b)) - F.FINGER / 2 for x in xs for a, b in (EXIT, WIN)
                    if not (a <= x <= b))
        note_(clear >= 3.0, 'no finger notch beside the exit hole or the window',
              f'{len(xs)} fingers a side, nearest {clear:.1f}mm from either')
    note_(all(s['w'] <= F.BED[0] and s['h'] <= F.BED[1] for s in sheets), 'every sheet fits the bed',
          f'{len(sheets)} sheet(s), largest {max(s["w"] for s in sheets):.0f} x '
          f'{max(s["h"] for s in sheets):.0f}mm')
    placed = sum(len(s['parts']) for s in sheets)
    note_(placed == len(parts), 'every part is on a sheet', f'{placed} of {len(parts)}')
    return out


def main():
    out, only, write, flat = None, None, True, False
    for x in sys.argv[1:]:
        if x == '--no-write':
            write = False
        elif x == '--flat':
            flat = True
        elif x.startswith('--out='):
            out = x.split('=', 1)[1]
        elif x.startswith('--only='):
            only = x.split('=', 1)[1]
            if only not in ('flat-A4', 'fingers-A4', 'leather'):
                raise SystemExit('error: --only= takes flat-A4, fingers-A4 or leather.')
        else:
            raise SystemExit(f'error: {x} is not a flag this generator reads. '
                             f'It takes --out=, --only=, --flat and --no-write.')
    if write and not out:
        raise SystemExit('error: --out=DIR, or --no-write to run the checks only.')
    L, holes, fs = predict()
    print(f'the original, as the model hears it: bore {W} x {D}mm, sound chamber {L:.2f}mm')
    for n, f in enumerate(fs):
        nm, c = note(f)
        print(f'  {n} open  {f:6.1f}Hz  {nm:3} {c:+4.0f}c   {1200 * math.log2(f / fs[0]):5.0f}c '
              f'above the fundamental (a minor pentatonic wants {[0, 300, 500, 700, 1000, 1200][n]})')
    bad = 0
    with matched():
        L4, _, f4 = predict()
        tL, _, tT = twin()
        print(f'\nmatched to box-square-3: bore {W:.2f} x {D:.2f}mm, {W * D:.1f}mm^2 against '
              f'{M.AREA:.1f}; sound chamber {L4:.1f}mm against {tL:.1f}; {TOTAL:.1f}mm long '
              f'against {tT:.1f}, {SPARE:g} of it to trim at the foot')
        print(f'  holes moved along by {STRETCH:.4f}, window solved to {WIN[1] - WIN[0]:.2f}mm, '
              f'holes to ' + ', '.join(f'{x:.2f}' for x in DIAMS)
              + 'mm; off equal temperament by ' + ', '.join(f'{c:+.2f}' for c in ET_CENTS)
              + ' cents')
        same = abs(W * D - M.AREA) < 0.01 and abs(L4 - tL) < 0.01 and abs(TOTAL - tT) < 0.01
        print(f'  {"pass" if same else "FAIL"}  the same bore area and length as box-square-3')
        worst = max(abs(c) for c in ET_CENTS)
        print(f'  {"pass" if worst < 1 else "FAIL"}  every note within a cent of equal '
              f'temperament   worst {worst:.2f} cents')
        bad += (worst >= 1) + (not same)
    for kind in ('flat-A4', 'fingers-A4'):
        if only and only != kind:
            continue
        with matched():
            parts = build(kind.split('-')[0])
            sheets = pack(parts)
            print(f'\n{kind}: {len(parts)} parts')
            for ok, what, detail in checks(kind.split('-')[0], parts, sheets):
                print(f'  {"pass" if ok else "FAIL"}  {what:46} {detail}')
                bad += not ok
        if write and not bad:
            d = out if flat else os.path.join(out, kind)
            os.makedirs(d, exist_ok=True)
            for k, s in enumerate(sheets, 1):
                what = ', '.join(sorted({p.name for p, _, _ in s['parts']}))
                f = os.path.join(d, f'your-flute-{kind}-sheet{k}-cut-files.svg')
                open(f, 'w').write(svg(kind, k, len(sheets), s, what))
                print(f'  wrote {os.path.basename(f)}  {s["w"]:.0f} x {s["h"]:.0f}mm, '
                      f'{len(s["parts"])} parts')
    if write and not bad and (not only or only == 'leather'):
        s = pack([strip_part()])[0]
        d = out
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, 'your-flute-leather-tie-cut-files.svg')
        open(f, 'w').write(svg('leather', 1, 1, s, 'the tie', leather=True))
        print(f'  wrote {os.path.basename(f)}')
    if bad:
        print(f'\n  {bad} check(s) failed. Nothing written.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
