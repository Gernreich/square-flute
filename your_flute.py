#!/usr/bin/env python3
"""The author's own flute, from 2017, redrawn: the design in yours/original/
measured, kept where it was played, and tweaked only where a laser or a fit
asked for it.

    python3 your_flute.py --no-write          # the prediction and the checks
    python3 your_flute.py --out=yours/cut-files
    python3 your_flute.py --only=flat --flat --out=DIR

square_flute.py is not touched by any of this, so its six variants cannot
move: this file imports its helpers and builds its own parts.

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
                    reads grey as depth; whether an xTool does the same is
                    not known here
  mouthpiece        an end cap 25.89 x 28.89mm with a 9.59mm breath hole
  block             four layers 25mm wide, 25, 19.8, 15.8 and 12.6 long
  tie               a leather strip 359.6 x 4.6mm

THE TWEAKS, each because something asked for it:

  1. Millimetre-true, the house cut-order colours, kerf-compensated, every
     part numbered. The originals are 1/90in units, colours chosen per job,
     and drawn at size with no kerf.
  2. The plug is four 3mm discs, 12mm, where the original's land was 11: ply
     comes in 3mm. The exit hole moves 1mm toward the mouth to make room;
     the window, every finger hole and the foot stay exactly where they were.
  3. FINGERS: the top is box-jointed to the sides as the bottom already was,
     tabs INTERF_ALONG tight, so it press-fits instead of being glued.
  4. The rings are the original's own image, re-embedded at its original
     size. The ramp is left out, because the engraved bevel did not work.
  5. So the splitting edge is filed by hand, and the top is cut as a head
     plate and a body plate butted SPLIT_PAST beyond the window, as
     square_flute's are: a spoilt edge then costs the short plate. A first
     redraw kept the top in one piece on the strength of the ramp, before the
     author said the ramp had failed.

NOTHING ACOUSTIC IS TWEAKED. The model reads this flute as a minor pentatonic
to within 40 cents and puts it near B-flat 4; the author has played it and
the model has not, so the holes stay where the author put them.
"""
import base64
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import square_flute as F                                       # noqa: E402
from square_flute import Part, rect, offset, pack, path, label  # noqa: E402
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
SPLIT = WIN[1] + 20.0                # the head plate ends here
CAP = (25.89, 28.89, 9.59)
BIRD = [25.0, 19.8, 15.8, 12.6]
STRIP = (359.64, 4.64)
FINGER, FPITCH = 10.0, 20.0

IMG = os.path.join(HERE, 'yours', 'original')


def png(name):
    return 'data:image/png;base64,' + base64.b64encode(
        open(os.path.join(IMG, name), 'rb').read()).decode()


def fingers_x():
    """Finger centres along a long edge, FPITCH apart, clear of both ends,
    and of the exit hole and the window: both run the full width of the bore,
    so a notch beside either would cut straight into it. And clear of the
    butt joint in the top, where a finger would straddle two plates."""
    n = int((TOTAL - 2 * FINGER) // FPITCH)
    span = (n - 1) * FPITCH
    xs = [TOTAL / 2 - span / 2 + i * FPITCH for i in range(n)]
    keep = FINGER / 2 + 3.0
    return [x for x in xs if not any(a - keep < x < b + keep
                                     for a, b in (EXIT, WIN, (SPLIT, SPLIT)))]


def plate_with_notches(name, num, note, x0=0.0, x1=TOTAL):
    """A plate PW wide from x0 to x1 whose long edges are notched T deep
    wherever a side wall's finger comes in: a box joint, the plate's own
    fingers being the material left between."""
    xs = [x for x in fingers_x() if x0 < x < x1]
    top = [(x0, 0)]
    for x in xs:
        top += [(x - FINGER / 2, 0), (x - FINGER / 2, T), (x + FINGER / 2, T), (x + FINGER / 2, 0)]
    top.append((x1, 0))
    bot = [(x1, PW)]
    for x in reversed(xs):
        bot += [(x + FINGER / 2, PW), (x + FINGER / 2, PW - T), (x - FINGER / 2, PW - T), (x - FINGER / 2, PW)]
    bot.append((x0, PW))
    return Part(name, num, top + bot, note)


def side_with_fingers(num):
    """A side D tall with fingers T long into the top and the bottom, each
    INTERF_ALONG longer than its notch."""
    fl = FINGER + F.INTERF_ALONG
    xs = fingers_x()
    top = [(0, 0)]
    for x in xs:
        top += [(x - fl / 2, 0), (x - fl / 2, -T), (x + fl / 2, -T), (x + fl / 2, 0)]
    top.append((TOTAL, 0))
    bot = [(TOTAL, D)]
    for x in reversed(xs):
        bot += [(x + fl / 2, D), (x + fl / 2, D + T), (x - fl / 2, D + T), (x - fl / 2, D)]
    bot.append((0, D))
    return Part('side wall', num, top + bot, 'fingers into the top and the bottom')


def build(kind):
    """Every part, in the flute's own flat coordinates: x from the mouth end,
    y across."""
    num = iter(range(1, 100))
    parts = []
    hn = 'exit hole, window and flue; file the far edge of the window to a bevel'
    bn = 'the finger holes, each in its depression'
    if kind == 'fingers':
        head = plate_with_notches('top, head plate', next(num), hn, 0.0, SPLIT)
        body = plate_with_notches('top, body plate', next(num), bn, SPLIT, TOTAL)
    else:
        head = Part('top, head plate', next(num), rect(0, 0, SPLIT, PW), hn)
        body = Part('top, body plate', next(num), rect(SPLIT, 0, TOTAL, PW), bn)
    yc = PW / 2
    head.slot(EXIT[0], yc - W / 2, EXIT[1], yc + W / 2)
    head.slot(WIN[0], yc - W / 2, WIN[1], yc + W / 2)
    head.fills.append(rect(PLUG[0], yc - W / 2, PLUG[1], yc + W / 2))   # the flue
    for x, d in zip(HOLES, DIAMS):
        body.hole(x, yc, d)
    body.images = [('ring.png', x - r / 2, yc - r / 2, r, r) for x, r in zip(HOLES, RING)]
    parts += [head, body]
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
    cap = Part('mouthpiece cap', next(num), rect(0, 0, CAP[0], CAP[1]), 'glued over the mouth end')
    cap.hole(CAP[0] / 2, CAP[1] / 2, CAP[2])
    parts.append(cap)
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
            if p.name == 'mouthpiece cap':      # the breath hole has the middle
                lx, ly, h = p.x0 + 5, p.y0 + 4, 3.0
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
    compare_page.py runs this in the same process as square_flute's six."""
    saved = M.WINDOW_W, M.WINDOW_L
    M.WINDOW_W, M.WINDOW_L = W, WIN[1] - WIN[0]
    try:
        b = M.Bore(W, D)
        L = TOTAL - WC
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
    note_(SPLIT - WIN[1] >= 10 and min(HOLES) - max(RING) / 2 - SPLIT >= 10,
          'the butt joint clears the window and the top hole',
          f'{SPLIT - WIN[1]:.0f}mm past the window, '
          f'{min(HOLES) - max(RING) / 2 - SPLIT:.0f}mm before the top depression')
    gaps = [HOLES[i] - HOLES[i + 1] - (RING[i] + RING[i + 1]) / 2 for i in range(4)]
    note_(min(gaps) >= 0, 'the depressions do not run into each other',
          f'closest {min(gaps):.1f}mm apart')
    note_(max(RING) <= PW - 2, 'each depression stays on the plate',
          f'{max(RING):.2f}mm on a {PW:.2f}mm plate')
    if kind == 'fingers':
        xs = fingers_x()
        clear = min(min(abs(x - a), abs(x - b)) - FINGER / 2 for x in xs for a, b in (EXIT, WIN)
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
            if only not in ('flat', 'fingers', 'leather'):
                raise SystemExit('error: --only= takes flat, fingers or leather.')
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
    for kind in ('flat', 'fingers'):
        if only and only != kind:
            continue
        parts = build(kind)
        sheets = pack(parts)
        print(f'\n{kind}: {len(parts)} parts')
        for ok, what, detail in checks(kind, parts, sheets):
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
