#!/usr/bin/env python3
"""Cut files for a five-hole minor-pentatonic flute in A4, square or
rectangular bore, in four builds with the flue in the bird.

    python3 square_flute.py --no-write        # the checks, write nothing
    python3 square_flute.py --out=DIR         # every variant into DIR/<variant>/
    python3 square_flute.py --only=box-square-3 --out=DIR
    python3 square_flute.py --only=box-square-3 --flat --out=DIR   # no subfolder

The acoustics are naf_model.py's: the sound-chamber length and where each
finger hole goes, and how big, for the bore section and the hole wall. This
file only builds what that asks for, in 3mm ply.

THE FOUR BUILDS here are two bores and two hole walls (plus_flute.py makes
the same four with the flue in the nest):

  box-square    a finger-jointed box, 16.88 x 16.88mm bore: four plates,
                the sides tabbed into the top and bottom
  stack-rect    a laminated stack, 15.83 x 18mm: a bottom layer, six bore
                layers with the bore cut out of them, and the top
     -3         the finger holes go through the 3mm top plate alone
     -6         a 3mm doubler is glued over the finger-hole run, so each hole
                has a 6mm chimney, as a wooden flute's wall gives

The stack cannot have a square bore at the reference's area: its depth is a
whole number of layers, 15 or 18mm, and 16.88 is neither. Acoustically the
bore SHAPE hardly matters -- the model puts the square and the 15.83 x 18
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
the flute. Its underside carries the flue as a FILL ENGRAVE, the bore's width: the
one feature here a laser draws better than a saw, since its depth -- about
1mm -- is a power setting rather than a cut.

THE SPLITTING EDGE is the window's downstream edge, and it wants a clean
bevel of about 30 degrees that a laser cannot cut. File it by hand, before
assembly. The top is ONE piece. It was cut as a head plate and a body plate
until 2026-10-13, so that a spoilt edge cost only the short one; the author
saw no point in it, and it bought little for what it cost: one strip of ply
saved, against a seam 20mm past the window to seal and a gap in the finger
joints at the place the bird is tied on.

Over the mouth end goes the author's 2017 mouthpiece cap, with its half-round
notch in the bottom edge (CAP_D, NOTCH_IN below).

Press-fit throughout, sealed with shellac, except what is laminated or cannot
be press-fit: the doubler, the bird's layers, every layer of the stack and the
mouthpiece cap are glued.
"""
import base64
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
# The plug discs' press-fit, across the ply: lyre_harp.py's mallet fit.
INTERF_ACROSS = 0.12
# THE FINGER JOINT, since 2026-10-13: the trumpet bores' own. tools/bore_split.py
# hands Boxes.py's snakeboxvar.py the default FingerJointSettings -- fingers and
# spaces each two sheets wide, no play, the fit left to the kerf -- and the
# fingers run out to the outside face, with no plate outboard of them. Until
# then the box was tabs in mortices with 2mm of plate outside each mortice,
# which the author called faux finger joints: the sliver showed.
FINGER = 2 * T       # finger width, and the space between fingers
FINGER_PLAY = 0.0    # Boxes.py's default; the kerf compensation is the fit
FINGER_END = 2 * FINGER   # Boxes.py's surroundingspaces: clear of each end
FINGER_CLEAR = 3.0   # ply between a finger notch and an opening
SIDE = 6.0           # the stack's side walls

SAC, EXIT_L, PLUG = 110.0, 6.0, 12.0
DOUBLER_PAST = 20.0  # doubler runs this far past the outermost holes
BIRD_LAYERS, BIRD_UPSTREAM = 3, 6.0
# The mouthpiece cap, the author's from 2017 (yours/original/Mouthpiece.svg):
# a plate over the mouth end, the flute's outside in size, whose bottom edge
# carries a half-round notch -- a 9.59mm circle centred NOTCH_IN inside the
# edge -- that opens through the bottom wall into the slow air chamber. On
# every variant since 2026-10-13, at the author's asking.
CAP_D, NOTCH_IN = 9.59, 0.33
# The finger-hole depression, also the author's: yours/original/ring.png, a
# soft dark halo engraved round each hole for the finger to find. Kept in the
# original's proportion to its hole, 12.14mm round a 7.75mm hole. On every
# variant since 2026-10-13, at the author's asking; on a 6mm variant it goes
# on the doubler, which is what the finger meets.
RING_OF = 12.14 / 7.75
RING_PNG = os.path.join(HERE, 'yours', 'original', 'ring.png')

BED = (600.0, 308.0)
MARGIN, GAP = 5.0, 4.0
MIN_WEB = 1.5        # thinnest ply left between two cuts

BLUE, ORANGE, BLACK = '#0000ff', '#ff8000', '#000000'

SQ = math.sqrt(M.AREA)
RW = M.AREA / 18.0
# Named for where the flue is carved, since that is the one thing a build and
# its counterpart in plus_flute.py differ in: -bird-flue here (the woodland
# style), -nest-flue there (the plains style). Until 2026-10-13 these were
# box-square-3 ... and their -plus versions. A box is square; a stack is as
# square as 3mm layers allow.
VARIANTS = {
    'box-square-3-bird-flue': ('box', SQ, SQ, 3.0),
    'box-square-6-bird-flue': ('box', SQ, SQ, 6.0),
    # the same boxes butt-jointed: plain plates, the sides glued between the
    # top and the bottom, as the author's 2017 flute was built
    'box-square-3-bird-flue-flat': ('flat', SQ, SQ, 3.0),
    'box-square-6-bird-flue-flat': ('flat', SQ, SQ, 6.0),
    'stack-rect-3-bird-flue': ('stack', RW, 18.0, 3.0),
    'stack-rect-6-bird-flue': ('stack', RW, 18.0, 6.0),
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


def fingers_x(L, clear=()):
    """Where the side walls' fingers go along a flute L long: FINGER wide,
    FINGER apart, centred, FINGER_END clear of each end, and none within
    FINGER_CLEAR of an interval in `clear`: any opening that runs to the
    bore's inner face, where a notch would cut straight into it."""
    pitch = 2 * FINGER
    n = int((L - 2 * FINGER_END - FINGER) // pitch) + 1
    span = (n - 1) * pitch
    xs = [L / 2 - span / 2 + i * pitch for i in range(n)]
    reach = FINGER / 2 + FINGER_CLEAR
    return [x for x in xs if not any(a - reach < x < b + reach for a, b in clear)]


class Part:
    def __init__(self, name, num, outline, note):
        self.name, self.num, self.note = name, num, note
        self.outline = outline          # physical, before the kerf
        self.cuts = []                  # inner cuts: ('rect', poly) / ('circle', cx, cy, r)
        self.fills = []                 # fill-engraved rectangles
        self.images = []                # (png, x, y, w, h): greyscale image engraves
        x = [p[0] for p in outline]
        y = [p[1] for p in outline]
        self.x0, self.y0 = min(x), min(y)
        self.w, self.h = max(x) - self.x0, max(y) - self.y0

    def hole(self, cx, cy, d):
        self.cuts.append(('circle', cx, cy, d / 2))

    def slot(self, x0, y0, x1, y1):
        self.cuts.append(('rect', rect(x0, y0, x1, y1)))


def cap_part(num, w, h, d=CAP_D, inset=NOTCH_IN):
    """The mouthpiece cap: a plate w across and h tall whose bottom edge,
    y = 0, carries a half-round notch -- the original's circle, d across,
    centred `inset` inside the edge. It is drawn as part of the outline: as a
    separate circle it would run 4.5mm past the cap and cut the next part on
    the sheet, which the 4mm gap between parts does not clear."""
    cx, r = w / 2, d / 2
    a = math.asin(inset / r)
    arc = [(cx + r * math.cos(t), inset + r * math.sin(t))
           for t in [math.pi + a - (math.pi + 2 * a) * i / 32 for i in range(33)]]
    p = Part('mouthpiece cap', num, [(0, 0)] + arc + [(w, 0), (w, h), (0, h)],
             'glued over the mouth end, the notched edge at the bottom')
    p.notch = (cx, inset, r)
    p.images = []           # your_flute's sheet writer reads it; nothing here does
    return p


def cap_path(p, dx, dy, e):
    """The cap's outline grown by the kerf: the rectangle out by e, the
    notch's arc, which bounds material lying outside it, in by e."""
    cx, cy, r = p.notch
    w, h = p.w, p.h
    r2 = r - e
    hx = math.sqrt(r2 * r2 - (cy + e) ** 2)
    X = lambda x: f'{x + dx:.3f}'
    Yy = lambda y: f'{y + dy:.3f}'
    return (f'M {X(-e)},{Yy(-e)} L {X(cx - hx)},{Yy(-e)} '
            f'A {r2:.3f} {r2:.3f} 0 1 0 {X(cx + hx)},{Yy(-e)} '
            f'L {X(w + e)},{Yy(-e)} L {X(w + e)},{Yy(h + e)} L {X(-e)},{Yy(h + e)} Z')


def end_notch(p):
    """Give a bottom plate the half-round notch in its mouth end: the cap's
    circle, CAP_D across, centred on the end edge midway across, so with the
    cap's own notch, at right angles to it in the end face, it makes one
    rounded opening at the bottom corner (the author, 2026-10-13). Kept off
    the outline, which offset() can grow only while it is rectilinear; the
    sheet writers and the 3D view put the arc in."""
    p.end_notch = (p.h / 2, CAP_D / 2)
    return p


def end_notch_outline(p, n=24):
    """The outline with the notch's arc in it, before the kerf: for the 3D
    view. The outline closes along its mouth end, x = 0."""
    yc, r = p.end_notch
    o = p.outline
    assert o[0][0] == 0 and o[-1][0] == 0, 'the outline must close along x = 0'
    arc = [(r * math.sin(math.pi * i / n), yc + r * math.cos(math.pi * i / n))
           for i in range(n + 1)]
    return o + arc


def end_notch_path(p, dx, dy, e):
    """The outline grown by the kerf with the notch's arc, which bounds
    material outside it, in by e: the circle about (0, yc) of radius r - e,
    met where the grown end edge, x = -e, crosses it."""
    yc, r = p.end_notch
    o = offset(p.outline, e)
    r2 = r - e
    h = math.sqrt(r2 * r2 - e * e)
    pts = ' L '.join(f'{x + dx:.3f},{y + dy:.3f}' for x, y in o)
    return (f'M {pts} L {-e + dx:.3f},{yc + h + dy:.3f} '
            f'A {r2:.3f} {r2:.3f} 0 1 0 {-e + dx:.3f},{yc - h + dy:.3f} Z')


def finger_side(L, D, xs, n):
    """A side wall D tall whose fingers stand T proud, up into the top and
    down into the bottom, flush with their outside faces."""
    fw = FINGER + FINGER_PLAY
    top = [(0, 0)]
    for x in xs:
        top += [(x - fw / 2, 0), (x - fw / 2, -T), (x + fw / 2, -T), (x + fw / 2, 0)]
    top.append((L, 0))
    bot = [(L, D)]
    for x in reversed(xs):
        bot += [(x + fw / 2, D), (x + fw / 2, D + T), (x - fw / 2, D + T), (x - fw / 2, D)]
    bot.append((0, D))
    return Part('side wall', n, top + bot, 'fingers into the top and the bottom')


def notched(x0, x1, PW, xs):
    """A plate's outline from x0 to x1, PW wide, notched T deep along both
    long edges wherever a side wall's finger comes in. The plate's own
    fingers are the material left between."""
    xs = [x for x in xs if x0 < x < x1]
    top = [(x0, 0)]
    for x in xs:
        top += [(x - FINGER / 2, 0), (x - FINGER / 2, T), (x + FINGER / 2, T), (x + FINGER / 2, 0)]
    top.append((x1, 0))
    bot = [(x1, PW)]
    for x in reversed(xs):
        bot += [(x + FINGER / 2, PW), (x + FINGER / 2, PW - T), (x - FINGER / 2, PW - T),
                (x - FINGER / 2, PW)]
    bot.append((x0, PW))
    return top + bot


def design(W, D, wall):
    """The model's hole layout for a bore W x D with the holes in `wall`,
    the window the bore's full width, as every build here has had since
    2026-10-13: the author's 2017 flute's window, on all of them."""
    with M.window(W):
        return M.design(M.Bore(W, D), wall, even=True)


def build(kind, W, D, wall, L, holes, diams):
    """Every part of one variant, in its own flat coordinates: x along the
    flute from the mouth end, y across it."""
    wc = SAC + PLUG + M.WINDOW_L / 2               # window centre
    total = wc + L + M.FOOT_SPARE
    hx = [wc + h for h in holes]                   # finger holes, foot-most first
    dz0, dz1 = min(hx) - DOUBLER_PAST, max(hx) + DOUBLER_PAST
    PW = W + 2 * T if kind in ('box', 'flat') else W + 2 * SIDE
    yc = PW / 2
    parts = []
    num = iter(range(1, 100))

    def top_plate():
        p = Part('top plate', next(num), rect(0, 0, total, PW),
                 'exit hole, window and the five finger holes; file the window\'s '
                 'far edge to a 30 degree bevel before assembly')
        # the exit hole and the window both run the bore's full width
        p.slot(SAC - EXIT_L, yc - W / 2, SAC, yc + W / 2)
        p.slot(SAC + PLUG, yc - W / 2, SAC + PLUG + M.WINDOW_L, yc + W / 2)
        for x, d in zip(hx, diams):
            p.hole(x, yc, d)
            r = d * RING_OF
            p.images.append(('ring.png', x - r / 2, yc - r / 2, r, r))
        return p

    if kind in ('box', 'flat'):
        top = top_plate()
        parts.append(top)
        if kind == 'box':
            # both full-width openings reach the bore's inner face, the floor of
            # every finger notch, so no finger may stand beside either
            xs = fingers_x(total, ((SAC - EXIT_L, SAC), (SAC + PLUG, SAC + PLUG + M.WINDOW_L)))
            top.outline = notched(0, total, PW, xs)
            parts.append(end_notch(Part('bottom plate', next(num), notched(0, total, PW, xs),
                                        'a half-round notch in the mouth end')))
            for k in range(2):
                parts.append(finger_side(total, D, xs, next(num)))
        else:
            parts.append(end_notch(Part('bottom plate', next(num), rect(0, 0, total, PW),
                                        'a half-round notch in the mouth end')))
            for k in range(2):
                parts.append(Part('side wall', next(num), rect(0, 0, total, D),
                                  'glued between the top and the bottom'))
        for k in range(int(PLUG / T)):
            parts.append(Part('plug disc', next(num),
                              rect(0, 0, W + INTERF_ACROSS, D + INTERF_ACROSS),
                              f'{int(PLUG / T)} press-fit into the bore '
                              f'between the exit hole and the window'))
    else:
        top = top_plate()
        parts.append(top)
        parts.append(end_notch(Part('bottom layer', next(num), rect(0, 0, total, PW),
                                    'a half-round notch in the mouth end')))
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
        # the finger meets the doubler, not the top, so the depressions move
        p.images, top.images = top.images, []
        parts.append(p)
    b0 = SAC - EXIT_L - BIRD_UPSTREAM
    for k in range(BIRD_LAYERS):
        p = Part('bird layer', next(num), rect(b0, 0, SAC + PLUG, PW),
                 'the flue fill-engraved in the bottom one, about 1mm deep'
                 if k == 0 else 'glued on the one below')
        if k == 0:
            p.fills.append(rect(SAC - EXIT_L, yc - W / 2, SAC + PLUG, yc + W / 2))
        parts.append(p)
    # last, so every part number the variants had before it is unchanged
    parts.append(cap_part(next(num), PW, D + 2 * T))
    return parts, dict(total=total, wc=wc, PW=PW, hx=hx,
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
        note(hole_edge - T >= MIN_WEB, 'ply between a finger hole and a finger notch',
             f'{hole_edge - T:.2f}mm against {MIN_WEB:g}')
        sides = [p for p in parts if p.name == 'side wall']
        note(min(p.y0 for p in sides) == -T and max(p.y0 + p.h for p in sides) == D + T,
             'the fingers run to the outside faces',
             f'{T:g}mm proud each way, nothing outboard of them')
    bots = [p for p in parts if getattr(p, 'end_notch', None)]
    yc_, rn = bots[0].end_notch if bots else (0, 99)
    note(len(bots) == 1 and rn <= W / 2 - 1.0,
         'the bottom\'s end notch opens into the bore, clear of its walls',
         f'{2 * rn:.2f}mm across in a {W:.2f}mm bore')
    rings = [d * RING_OF for d in diams]
    gaps = [holes[i] - holes[i + 1] - (rings[i] + rings[i + 1]) / 2 for i in range(4)]
    note(min(gaps) >= 0, 'the depressions do not run into each other',
         f'closest {min(gaps):.1f}mm apart')
    edge = T if kind in ('box', 'flat') else 1.0
    note(max(rings) / 2 <= info['PW'] / 2 - edge, 'each depression clears the plate\'s edge joints',
         f'{info["PW"] / 2 - edge - max(rings) / 2:.1f}mm to spare')
    tops = [p for p in parts if p.name.startswith('top')]
    note(len(tops) == 1 and tops[0].w == info['total'], 'the top is one piece',
         f'{len(tops)} plate, {tops[0].w:.1f}mm long')
    if info['doubler']:
        z0, z1 = info['doubler']
        clear = z0 - (SAC + PLUG + M.WINDOW_L)
        note(clear >= 10 and z1 <= info['total'],
             'the doubler stays clear of the window', f'{clear:.0f}mm past it, '
             f'{z0:.1f} to {z1:.1f}mm')
    note(all(s['w'] <= BED[0] and s['h'] <= BED[1] for s in sheets),
         'every sheet fits the bed',
         f'{len(sheets)} sheet(s), largest '
         f'{max(s["w"] for s in sheets):.0f} x {max(s["h"] for s in sheets):.0f}mm')
    cap = [p for p in parts if p.name == 'mouthpiece cap'][0]
    cx, cy, r = cap.notch
    into = cy + r - T - (cap.h - (D + 2 * T)) / 2
    note(into > 0, 'the cap\'s notch opens into the bore',
         f'{cy + r:.2f}mm deep, {into:.2f}mm past the bottom wall')
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


def ring_data():
    return 'data:image/png;base64,' + base64.b64encode(open(RING_PNG, 'rb').read()).decode()


def svg_sheet(variant, k, n, s, info, what):
    blue, orange, black = [], [], []
    fills, imgs = [], []
    for p, sx, sy in s['parts']:
        dx, dy = sx - p.x0 + KERF / 2, sy - p.y0 + KERF / 2
        mv = lambda pts: [(x + dx, y + dy) for x, y in pts]
        if getattr(p, 'notch', None):
            black.append(cap_path(p, dx, dy, KERF / 2))
        elif getattr(p, 'end_notch', None):
            black.append(end_notch_path(p, dx, dy, KERF / 2))
        else:
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
        for name, x, y, w, h in p.images:
            imgs.append(f'<image x="{x + dx:.3f}" y="{y + dy:.3f}" width="{w:.3f}" '
                        f'height="{h:.3f}" preserveAspectRatio="none" href="{ring_data()}"/>')
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
            f'{what}. 3mm ply, drawn for a {KERF:g}mm kerf. Finger joints as the trumpet '
            f'bores cut them: {FINGER:g}mm fingers and spaces, no play, the fit from the '
            f'kerf. Blue {BLUE} engraves '
            f'(the part numbers; the flue as a fill engrave about 1mm deep; and the '
            f'depression round each finger hole, a greyscale image engrave, Grayscale '
            f'mode in xTool Creative Space -- set both depths on scrap first), orange '
            f'{ORANGE} cuts the holes and slots, '
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
            + (f'  <g id="images">\n' + ''.join(f'    {i}\n' for i in imgs) + '  </g>\n'
               if imgs else '')
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
            designs[key] = design(W, D, wall)
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
