#!/usr/bin/env python3
"""The author's own flute, from 2017: the design in yours/original/ measured,
and what the model hears in it. It is not redrawn as a build of its own any
more (2026-10-13, the author): at the 3/4in bore its redraw was a box-square-3
nest-flue build, flat or finger-jointed, in all but its holes and block, and
the 3D page's joint toggle covers it. Its ideas are in every build.

    python3 your_flute.py --no-write          # what the model hears in it
    python3 your_flute.py --out=yours/cut-files   # and the leather tie

This file also holds the sheet writer plus_flute.py uses (svg), and draws
the leather tie, cut from leather, not ply.

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
                    in no build
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

AT ITS OWN SIZE the model reads this flute as a minor pentatonic to within
40 cents and puts it near B-flat 4.
"""
import base64
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import square_flute as F                                       # noqa: E402
from square_flute import Part, rect, offset, pack, path         # noqa: E402
from square_flute import cap_path                                # noqa: E402
M = F.M

T = F.T
W, D = 19.37, 22.44
TOTAL = 456.70
WIN = (140.46, 146.45)
WC = (WIN[0] + WIN[1]) / 2
HOLES = [357.315, 329.135, 300.375, 252.975, 221.455]    # from the mouth, foot-most first
DIAMS = [7.73, 7.87, 7.79, 7.79, 5.47]
STRIP = (359.64, 4.64)

IMG = os.path.join(HERE, 'yours', 'original')


def png(name):
    return 'data:image/png;base64,' + base64.b64encode(
        open(os.path.join(IMG, name), 'rb').read()).decode()


def strip_part():
    p = Part('leather tie', 1, rect(0, 0, STRIP[0], STRIP[1]), 'cut from leather, not ply')
    p.images = []
    return p


def svg(kind, k, n, sheet, what, leather=False):
    orange, black, fills, imgs = [], [], [], []
    cache = {}
    for p, sx, sy in sheet['parts']:
        dx, dy = sx - p.x0 + F.KERF / 2, sy - p.y0 + F.KERF / 2
        mv = lambda pts: [(x + dx, y + dy) for x, y in pts]
        if getattr(p, 'notch', None):
            black.append(cap_path(p, dx, dy, F.KERF / 2))
        elif getattr(p, 'end_notch', None):
            black.append(F.end_notch_path(p, dx, dy, F.KERF / 2))
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
    desc = (f'1 user unit = 1mm. The author\'s 2017 flute, redrawn: {kind}, sheet {k} of {n}: '
            f'{what}. ' + ('Cut from leather, not ply; black cuts. ' if leather else
            f'3mm ply, drawn for a {F.KERF:g}mm kerf. Blue {F.BLUE} engraves: '
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


def main():
    out, write = None, True
    for x in sys.argv[1:]:
        if x == '--no-write':
            write = False
        elif x.startswith('--out='):
            out = x.split('=', 1)[1]
        elif x.startswith('--kerf='):
            F.set_kerf(x)
        else:
            raise SystemExit(f'error: {x} is not a flag this generator reads. '
                             f'It takes --out=, --kerf= and --no-write.')
    if write and not out:
        raise SystemExit('error: --out=DIR, or --no-write to print the prediction only.')
    L, holes, fs = predict()
    print(f'the original, as the model hears it: bore {W} x {D}mm, sound chamber {L:.2f}mm')
    for n, f in enumerate(fs):
        nm, c = note(f)
        print(f'  {n} open  {f:6.1f}Hz  {nm:3} {c:+4.0f}c   {1200 * math.log2(f / fs[0]):5.0f}c '
              f'above the fundamental (a minor pentatonic wants {[0, 300, 500, 700, 1000, 1200][n]})')
    if write:
        s = pack([strip_part()])[0]
        os.makedirs(out, exist_ok=True)
        f = os.path.join(out, 'your-flute-leather-tie-cut-files.svg')
        open(f, 'w').write(svg('leather', 1, 1, s, 'the tie', leather=True))
        print(f'  wrote {os.path.basename(f)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
