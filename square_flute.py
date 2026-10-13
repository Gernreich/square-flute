#!/usr/bin/env python3
"""Cut files for a five-hole minor-pentatonic flute in A4, square or
rectangular bore, in six variants.

    python3 square_flute.py --no-write        # the checks, write nothing
    python3 square_flute.py --out=DIR         # every variant into DIR/<variant>/
    python3 square_flute.py --only=box-square-3 --out=DIR
    python3 square_flute.py --only=box-square-3 --flat --out=DIR   # no subfolder

The acoustics are naf_model.py's: the sound-chamber length and where each
finger hole goes, and how big, for the bore section and the hole wall. This
file only builds what that asks for, in 3mm ply.

THE SIX VARIANTS are every combination of three bores and two hole walls:

  box-square    a finger-jointed box, 19.67 x 19.67mm bore: four plates,
                the sides tabbed into the top and bottom
  box-rect      the same box, 18.43 wide x 21mm deep -- the stack's section,
                built the box's way, so the two constructions can be compared
                at one bore
  stack-rect    a laminated stack, 18.43 x 21mm: a bottom layer, seven bore
                layers with the bore cut out of them, and the top
     -3         the finger holes go through the 3mm top plate alone
     -6         a 3mm doubler is glued over the finger-hole run, so each hole
                has a 6mm chimney, as a wooden flute's wall gives

The stack cannot have a square bore at the reference's area: its depth is a
whole number of layers, 18 or 21mm, and 19.67 is neither. Acoustically the
bore SHAPE hardly matters -- the model puts the square and the 18.43 x 21
holes within 0.1mm of each other -- so the stack keeps the area and gives up
the square.

FROM THE MOUTH END, the same in every variant:

  slow air chamber   SAC long, open at the end you blow into
  exit hole          up through the top, the last EXIT_L of the chamber
  plug               PLUG long, solid: discs in the box, a land left uncut
                     in the stack's bore layers
  window             the true sound hole, right against the plug
  sound chamber      to the foot, cut FOOT_SPARE long: trim it to A4

The block (the bird) sits over the exit hole and the plug, its front edge on
the window's upstream edge, tied on and not glued, so it can be slid to voice
the flute. Its underside carries the flue as a FILL ENGRAVE, FLUE_W wide: the
one feature here a laser draws better than a saw, since its depth -- about
1mm -- is a power setting rather than a cut.

THE SPLITTING EDGE is the window's downstream edge, and it wants a clean
bevel of about 30 degrees that a laser cannot cut. File it by hand. The top
is cut in two, a head plate and a body plate, butted 20mm below the window,
so a spoilt edge costs the short plate and not the long one.

Press-fit throughout, sealed with shellac, except what is laminated: the
doubler, the bird's layers and every layer of the stack are glued.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'trumpet-elbows-allowed', 'parts',
                                'bore', 'concept', 'swept-curve'))
import naf_model as M                                          # noqa: E402
# the stroke font and the path writer, imported and not copied: the same
# numbers every other LaserMadeMusic part engraves
from ribbon_bore import label, path                            # noqa: E402

T = 3.0              # ply
KERF = 0.13          # measured, ribbon_bore's and lyre_harp's figure
# The fit. These are the interferences lyre_harp.py drew at FIT 0.25, the
# friction fit that needs a rubber mallet: along a tab, and across the ply.
INTERF_ALONG, INTERF_ACROSS = 0.19, 0.12
WEB = 2.0            # plate left outboard of a mortice
SIDE = 6.0           # the stack's side walls
TAB, TAB_PITCH, TAB_END = 10.0, 40.0, 15.0

SAC, EXIT_L, PLUG = 110.0, 6.0, 12.0
FLUE_W = M.WINDOW_W
SPLIT_PAST = 20.0    # head plate ends this far past the window
DOUBLER_PAST = 20.0  # doubler runs this far past the outermost holes
BIRD_LAYERS, BIRD_UPSTREAM = 3, 6.0

BED = (600.0, 308.0)
MARGIN, GAP = 5.0, 4.0
MIN_WEB = 1.5        # thinnest ply left between two cuts

BLUE, ORANGE, BLACK = '#0000ff', '#ff8000', '#000000'

SQ = math.sqrt(M.AREA)
RW = M.AREA / 21.0
VARIANTS = {
    'box-square-3': ('box', SQ, SQ, 3.0),
    'box-square-6': ('box', SQ, SQ, 6.0),
    'box-rect-3': ('box', RW, 21.0, 3.0),
    'box-rect-6': ('box', RW, 21.0, 6.0),
    'stack-rect-3': ('stack', RW, 21.0, 3.0),
    'stack-rect-6': ('stack', RW, 21.0, 6.0),
}


# --- geometry ----------------------------------------------------------------

def area2(poly):
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1)
               in zip(poly, poly[1:] + poly[:1]))


def offset(poly, d):
    """A rectilinear polygon grown by d on every side (shrunk if d < 0).

    Each vertex moves along the sum of its two edges' outward normals, which
    for right angles is exactly a parallel offset of both edges, at a convex
    corner and a concave one alike."""
    s = 1 if area2(poly) > 0 else -1
    n = len(poly)
    out = []
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        def normal(a, b):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            # outward for a polygon of sign s, in y-down coordinates
            return (s * dy / L, -s * dx / L)
        na, nb = normal(p0, p1), normal(p1, p2)
        out.append((p1[0] + d * (na[0] + nb[0]), p1[1] + d * (na[1] + nb[1])))
    return out


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def tabs_x(L, avoid=()):
    """Tab centres along a wall of length L, TAB_PITCH apart and TAB_END
    clear of each end, skipping any within a tab's width of a line in
    `avoid` -- the butt joint in the top, where a tab would straddle two
    plates."""
    n = int((L - 2 * TAB_END) // TAB_PITCH) + 1
    span = (n - 1) * TAB_PITCH
    xs = [L / 2 - span / 2 + i * TAB_PITCH for i in range(n)]
    return [x for x in xs if all(abs(x - a) > TAB for a in avoid)]


class Part:
    def __init__(self, name, num, outline, note):
        self.name, self.num, self.note = name, num, note
        self.outline = outline          # physical, before the kerf
        self.cuts = []                  # inner cuts: ('rect', poly) / ('circle', cx, cy, r)
        self.fills = []                 # fill-engraved rectangles
        x = [p[0] for p in outline]
        y = [p[1] for p in outline]
        self.x0, self.y0 = min(x), min(y)
        self.w, self.h = max(x) - self.x0, max(y) - self.y0

    def hole(self, cx, cy, d):
        self.cuts.append(('circle', cx, cy, d / 2))

    def slot(self, x0, y0, x1, y1):
        self.cuts.append(('rect', rect(x0, y0, x1, y1)))


def side_wall(L, D, avoid, n):
    """A wall D tall with tabs up into the top and down into the bottom,
    each tab INTERF_ALONG longer than its mortice."""
    tl = TAB + INTERF_ALONG
    xs = tabs_x(L, avoid)
    top = [(0, 0)]
    for x in xs:
        top += [(x - tl / 2, 0), (x - tl / 2, -T), (x + tl / 2, -T), (x + tl / 2, 0)]
    top.append((L, 0))
    bot = [(L, D)]
    for x in reversed(xs):
        bot += [(x + tl / 2, D), (x + tl / 2, D + T), (x - tl / 2, D + T), (x - tl / 2, D)]
    bot.append((0, D))
    return Part(f'side wall', n, top + bot,
                'tabs up into the top, down into the bottom'), xs


def mortices(p, xs, PW, lo, hi):
    """Slots for the side walls' tabs, both edges, those within [lo, hi]."""
    w = T - INTERF_ACROSS
    for x in xs:
        if lo + TAB / 2 <= x <= hi - TAB / 2:
            for y in (WEB + (T - w) / 2, PW - WEB - T + (T - w) / 2):
                p.slot(x - TAB / 2, y, x + TAB / 2, y + w)


def build(kind, W, D, wall, L, holes, diams):
    """Every part of one variant, in its own flat coordinates: x along the
    flute from the mouth end, y across it."""
    wc = SAC + PLUG + M.WINDOW_L / 2               # window centre
    total = wc + L + M.FOOT_SPARE
    split = SAC + PLUG + M.WINDOW_L + SPLIT_PAST
    hx = [wc + h for h in holes]                   # finger holes, foot-most first
    dz0, dz1 = min(hx) - DOUBLER_PAST, max(hx) + DOUBLER_PAST
    PW = W + 2 * (T + WEB) if kind == 'box' else W + 2 * SIDE
    yc = PW / 2
    parts = []
    num = iter(range(1, 100))

    def top_head():
        p = Part('top, head plate', next(num), rect(0, 0, split, PW),
                 'exit hole and window; file the window\'s far edge to a 30 degree bevel')
        p.slot(SAC - EXIT_L, yc - FLUE_W / 2, SAC, yc + FLUE_W / 2)
        p.slot(SAC + PLUG, yc - M.WINDOW_W / 2, SAC + PLUG + M.WINDOW_L,
               yc + M.WINDOW_W / 2)
        return p

    def top_body():
        p = Part('top, body plate', next(num), rect(split, 0, total, PW),
                 'the five finger holes, butted against the head plate')
        for x, d in zip(hx, diams):
            p.hole(x, yc, d)
        return p

    if kind == 'box':
        sw, xs = side_wall(total, D, (split,), 0)
        h = top_head(); mortices(h, xs, PW, 0, split); parts.append(h)
        b = top_body(); mortices(b, xs, PW, split, total); parts.append(b)
        bot = Part('bottom plate', next(num), rect(0, 0, total, PW), 'plain')
        mortices(bot, xs, PW, 0, total)
        parts.append(bot)
        for k in range(2):
            s, _ = side_wall(total, D, (split,), next(num))
            parts.append(s)
        for k in range(int(PLUG / T)):
            parts.append(Part('plug disc', next(num),
                              rect(0, 0, W + INTERF_ACROSS, D + INTERF_ACROSS),
                              f'{int(PLUG / T)} press-fit into the bore '
                              f'between the exit hole and the window'))
    else:
        parts.append(top_head())
        parts.append(top_body())
        parts.append(Part('bottom layer', next(num), rect(0, 0, total, PW), 'plain'))
        s1, s2 = SIDE, SIDE + W
        bore = [(0, 0), (total, 0), (total, s1), (SAC + PLUG, s1),
                (SAC + PLUG, s2), (total, s2), (total, PW), (0, PW),
                (0, s2), (SAC, s2), (SAC, s1), (0, s1)]
        for k in range(int(round(D / T))):
            parts.append(Part('bore layer', next(num), bore,
                              'the chamber and the bore cut out, the plug left solid'))
    if wall > T:
        p = Part('doubler', next(num), rect(dz0, 0, dz1, PW),
                 'glued over the finger-hole run, holes in line')
        for x, d in zip(hx, diams):
            p.hole(x, yc, d)
        parts.append(p)
    b0 = SAC - EXIT_L - BIRD_UPSTREAM
    for k in range(BIRD_LAYERS):
        p = Part('bird layer', next(num), rect(b0, 0, SAC + PLUG, PW),
                 'the flue fill-engraved in the bottom one, about 1mm deep'
                 if k == 0 else 'glued on the one below')
        if k == 0:
            p.fills.append(rect(SAC - EXIT_L, yc - FLUE_W / 2, SAC + PLUG,
                                yc + FLUE_W / 2))
        parts.append(p)
    return parts, dict(total=total, wc=wc, split=split, PW=PW, hx=hx,
                       doubler=(dz0, dz1) if wall > T else None)


# --- checks -----------------------------------------------------------------

def checks(name, kind, W, D, wall, parts, info, L, holes, diams, cents, sheets):
    out = []

    def note(ok, what, detail):
        out.append((ok, what, detail))
    note(max(abs(c) for c in cents) < 1.0, 'the model hits all six notes',
         f'worst {max(abs(c) for c in cents):.2f} cents')
    note(info['total'] + 2 * MARGIN <= BED[0], 'the longest part fits the bed',
         f'{info["total"]:.1f}mm against {BED[0] - 2 * MARGIN:g}')
    note(max(diams) <= W - 2 * MIN_WEB, 'every finger hole opens inside the bore',
         f'largest {max(diams):.2f}mm in a {W:.2f}mm bore')
    gaps = [holes[i] - holes[i + 1] - (diams[i] + diams[i + 1]) / 2 for i in range(4)]
    note(min(gaps) >= 3.0, 'ply left between neighbouring holes',
         f'narrowest {min(gaps):.1f}mm')
    if kind == 'box':
        hole_edge = info['PW'] / 2 - max(diams) / 2
        mort_in = WEB + T
        note(hole_edge - mort_in >= MIN_WEB, 'ply between a finger hole and a mortice',
             f'{hole_edge - mort_in:.2f}mm against {MIN_WEB:g}')
    near = info['split'] - (SAC + PLUG + M.WINDOW_L)
    note(near >= 10 and min(info['hx']) - info['split'] >= 10,
         'the butt joint clears the window and the top hole',
         f'{near:.0f}mm past the window, {min(info["hx"]) - info["split"]:.0f}mm '
         f'before the top hole')
    if info['doubler']:
        z0, z1 = info['doubler']
        note(z0 >= info['split'] and z1 <= info['total'],
             'the doubler lies on the body plate', f'{z0:.1f} to {z1:.1f}mm')
    note(all(s['w'] <= BED[0] and s['h'] <= BED[1] for s in sheets),
         'every sheet fits the bed',
         f'{len(sheets)} sheet(s), largest '
         f'{max(s["w"] for s in sheets):.0f} x {max(s["h"] for s in sheets):.0f}mm')
    placed = sum(len(s['parts']) for s in sheets)
    note(placed == len(parts), 'every part is on a sheet', f'{placed} of {len(parts)}')
    return out


# --- sheets ------------------------------------------------------------------

def pack(parts):
    """Shelves across the bed, tallest row first; a part goes on the first
    shelf with room, and a new sheet starts when no shelf has any."""
    order = sorted(parts, key=lambda p: (-p.w, -p.h))
    sheets = []
    for p in order:
        pw, ph = p.w + KERF, p.h + KERF
        put = False
        for s in sheets:
            for row in s['rows']:
                if row['x'] + pw <= BED[0] - MARGIN and ph <= row['h']:
                    row['items'].append((p, row['x'], row['y']))
                    row['x'] += pw + GAP
                    put = True
                    break
            if put:
                break
            if s['y'] + ph <= BED[1] - MARGIN:
                s['rows'].append({'x': MARGIN + pw + GAP, 'y': s['y'], 'h': ph,
                                  'items': [(p, MARGIN, s['y'])]})
                s['y'] += ph + GAP
                put = True
                break
        if not put:
            s = {'rows': [], 'y': MARGIN}
            s['rows'].append({'x': MARGIN + pw + GAP, 'y': MARGIN, 'h': ph,
                              'items': [(p, MARGIN, MARGIN)]})
            s['y'] += ph + GAP
            sheets.append(s)
    for s in sheets:
        s['parts'] = [it for r in s['rows'] for it in r['items']]
        s['w'] = max(x + p.w + KERF for p, x, y in s['parts']) + MARGIN
        s['h'] = max(y + p.h + KERF for p, x, y in s['parts']) + MARGIN
    return sheets


def svg_sheet(variant, k, n, s, info, what):
    blue, orange, black = [], [], []
    fills = []
    for p, sx, sy in s['parts']:
        dx, dy = sx - p.x0 + KERF / 2, sy - p.y0 + KERF / 2
        mv = lambda pts: [(x + dx, y + dy) for x, y in pts]
        black.append(path(mv(offset(p.outline, KERF / 2))))
        for c in p.cuts:
            if c[0] == 'rect':
                orange.append(path(mv(offset(c[1], -KERF / 2))))
            else:
                _, cx, cy, r = c
                orange.append(f'<circle cx="{cx + dx:.3f}" cy="{cy + dy:.3f}" '
                              f'r="{r - KERF / 2:.3f}"/>')
        for f in p.fills:
            fills.append(path(mv(f)))
        # the part number, engraved where nothing is cut: past the bore on a
        # plate, in the middle of a disc
        h = min(5.0, p.h * 0.3)
        # the middle of the widest stretch along the part with no inner cut
        # in it: on a plate with holes that is between the hands
        xs = sorted([p.x0 + 6] + [p.x0 + p.w - 6]
                    + [c[1] for c in p.cuts if c[0] == 'circle']
                    + [x for c in p.cuts if c[0] == 'rect' for x, _ in c[1]])
        g0, g1 = max(zip(xs, xs[1:]), key=lambda g: g[1] - g[0])
        lx = (g0 + g1) / 2
        ly = p.y0 + p.h / 2
        if p.name in ('bore layer',):
            ly = p.y0 + SIDE / 2
            h = 3.0
        if p.name == 'bird layer':
            lx, ly = p.x0 + 4, p.y0 + 4
            h = 3.0
        blue += [d for d in label(str(p.num), lx + dx, ly + dy, h)]
    desc = (f'1 user unit = 1mm. Square-bore flute in A4, {variant}, sheet {k} of {n}: '
            f'{what}. 3mm ply, drawn for a {KERF:g}mm kerf, joints {INTERF_ALONG:g}mm '
            f'tight along a tab and {INTERF_ACROSS:g}mm across. Blue {BLUE} engraves '
            f'(the part numbers, and the flue as a fill engrave about 1mm deep -- set '
            f'its depth on scrap first), orange {ORANGE} cuts the holes and slots, '
            f'black {BLACK} frees the parts.')
    g = lambda col, items, fill='none': (
        f'  <g fill="{fill}" stroke="{col}" stroke-width="0.2">\n'
        + ''.join(f'    {i}\n' if i.startswith('<') else f'    <path d="{i}"/>\n'
                  for i in items) + '  </g>\n')
    return (f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{s["w"]:.2f}mm" '
            f'height="{s["h"]:.2f}mm" viewBox="0 0 {s["w"]:.2f} {s["h"]:.2f}">\n'
            f'<title>Square-bore flute in A4, {variant}, sheet {k} of {n}</title>\n'
            f'<desc>{desc}</desc>\n'
            + g(BLUE, blue)
            + (f'  <g fill="{BLUE}" stroke="none">\n'
               + ''.join(f'    <path d="{d}"/>\n' for d in fills) + '  </g>\n'
               if fills else '')
            + g(ORANGE, orange) + g(BLACK, black) + '</svg>\n')


def main():
    a = sys.argv[1:]
    out, only, write, flat = None, None, True, False
    for x in a:
        if x == '--no-write':
            write = False
        elif x == '--flat':
            flat = True
        elif x.startswith('--out='):
            out = x.split('=', 1)[1]
        elif x.startswith('--only='):
            only = x.split('=', 1)[1]
            if only not in VARIANTS:
                raise SystemExit(f'error: {only} is not a variant. They are '
                                 + ', '.join(VARIANTS) + '.')
        else:
            raise SystemExit(f'error: {x} is not a flag this generator reads. '
                             f'It takes --out=, --only=, --flat and --no-write.')
    if write and not out:
        raise SystemExit('error: --out=DIR, or --no-write to run the checks only.')
    designs = {}
    bad = 0
    summary = {}
    for name, (kind, W, D, wall) in VARIANTS.items():
        if only and name != only:
            continue
        b = M.Bore(W, D)
        key = (round(W, 4), round(D, 4), wall)
        if key not in designs:
            designs[key] = M.design(b, wall, even=True)
        L, holes, diams, cents = designs[key]
        parts, info = build(kind, W, D, wall, L, holes, diams)
        sheets = pack(parts)
        print(f'\n{name}: {kind}, bore {W:.2f} x {D:.2f}mm, {wall:g}mm hole wall')
        print(f'  sound chamber {L:.1f}mm from the window centre, cut '
              f'{L + M.FOOT_SPARE:.1f}; flute {info["total"]:.1f}mm long, '
              f'{info["PW"]:.2f}mm wide')
        print('  holes from the window: ' + ', '.join(
            f'{h:.1f}/ø{d:.1f}' for h, d in zip(holes, diams)))
        for ok, what, detail in checks(name, kind, W, D, wall, parts, info,
                                       L, holes, diams, cents, sheets):
            print(f'  {"pass" if ok else "FAIL"}  {what:46} {detail}')
            bad += not ok
        summary[name] = (kind, W, D, wall, L, holes, diams, info, parts, sheets)
        if write and not bad:
            d = out if flat else os.path.join(out, name)
            os.makedirs(d, exist_ok=True)
            for k, s in enumerate(sheets, 1):
                what = ', '.join(sorted({p.name for p, _, _ in s['parts']}))
                f = os.path.join(d, f'square-flute-A4-{name}-sheet{k}-cut-files.svg')
                open(f, 'w').write(svg_sheet(name, k, len(sheets), s, info, what))
                print(f'  wrote {os.path.basename(f)}  {s["w"]:.0f} x {s["h"]:.0f}mm, '
                      f'{len(s["parts"])} parts')
    if bad:
        print(f'\n  {bad} check(s) failed. Nothing written.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
