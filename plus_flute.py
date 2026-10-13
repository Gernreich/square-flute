#!/usr/bin/env python3
"""The six variants again, each with the author's ideas folded in: the
"-plus" variants.

    python3 plus_flute.py --no-write              # the checks, write nothing
    python3 plus_flute.py --out=cut-files         # into cut-files/<variant>-plus/
    python3 plus_flute.py --only=box-square-3-plus --flat --out=DIR

square_flute.py is not edited by this file, and its six variants cannot move:
the author asked that they stay as they were. This builds its own parts from
square_flute's helpers and the model's own design().

WHAT EACH -plus VARIANT TAKES FROM THE AUTHOR'S 2017 FLUTE (yours/):

  1. The window runs the whole width of the bore, as the original's does,
     rather than 10mm of it. The model is rerun at that window, because a
     wider window carries a smaller end correction, which moves the foot and
     every hole.
  2. The exit hole runs the whole width too, and the flue is a fill engrave
     in the NEST -- the top of the head plate over the plug -- rather than in
     the bird. The bird is then plain layers, and the flue is on the part that
     stays put.
  3. A mouthpiece cap over the mouth end -- on every variant since, the six
     included, through square_flute.cap_part -- the size of the flute's outside,
     with the original's half-round notch in its bottom edge: a 9.59mm circle
     centred 0.33mm inside the edge, so the notch opens through the bottom
     wall into the bore, away from the finger holes. Glued, like the bird's
     layers.
  4. A soft engraved depression round every finger hole: the original's own
     ring.png, scaled to each hole as the original scaled it, 1.57 times the
     hole across.

NOT taken: the original's engraved splitting edge, which charred and did not
work, so the edge is still filed by hand and the top still split; and its
stepped block, whose outline was for looks only, the author says. The bird is
three plain layers as in the six, and with the flue in the nest it carries
none.

A full-width window or exit hole reaches the bore's inner faces, which in the
box is the floor of every finger notch. So no finger may stand beside either;
the box keeps them clear the way the original's finger joints are.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import square_flute as F                                       # noqa: E402
import your_flute as Y                                         # noqa: E402
from square_flute import Part, rect, pack                      # noqa: E402
M = F.M

T = F.T
RING_OF = 12.14 / 7.75                # the original's depression across its hole

VARIANTS = {k + '-plus': v for k, v in F.VARIANTS.items()}


class wide_window:
    """The model's window, made the bore's width for the length of a with
    block, then put back: compare_page.py runs the six in the same process."""

    def __init__(self, W):
        self.W = W

    def __enter__(self):
        self.saved = M.WINDOW_W
        M.WINDOW_W = self.W

    def __exit__(self, *a):
        M.WINDOW_W = self.saved


def design(W, D, wall):
    with wide_window(W):
        return M.design(M.Bore(W, D), wall, even=True)


def build(kind, W, D, wall, L, holes, diams):
    wc = F.SAC + F.PLUG + M.WINDOW_L / 2
    total = wc + L + M.FOOT_SPARE
    split = F.SAC + F.PLUG + M.WINDOW_L + F.SPLIT_PAST
    hx = [wc + h for h in holes]
    PW = W + 2 * T if kind == 'box' else W + 2 * F.SIDE
    yc = PW / 2
    exit_ = (F.SAC - F.EXIT_L, F.SAC)
    win = (F.SAC + F.PLUG, F.SAC + F.PLUG + M.WINDOW_L)
    num = iter(range(1, 100))
    parts = []

    head = Part('top, head plate', next(num), rect(0, 0, split, PW),
                'full-width exit hole and window, the flue engraved between; '
                'file the window\'s far edge to a bevel')
    head.slot(exit_[0], yc - W / 2, exit_[1], yc + W / 2)
    head.slot(win[0], yc - W / 2, win[1], yc + W / 2)
    head.fills.append(rect(exit_[1], yc - W / 2, win[0], yc + W / 2))
    body = Part('top, body plate', next(num), rect(split, 0, total, PW),
                'the finger holes, each in its depression')
    for x, d in zip(hx, diams):
        body.hole(x, yc, d)
    rings = [d * RING_OF for d in diams]
    body.images = [('ring.png', x - r / 2, yc - r / 2, r, r) for x, r in zip(hx, rings)]

    if kind == 'box':
        # a finger notch beside the exit hole or the window would run straight
        # into it: both reach the bore's inner face, which is the notch's floor
        xs = F.fingers_x(total, ((split, split), exit_, win))
        head.outline = F.notched(0, split, PW, xs)
        body.outline = F.notched(split, total, PW, xs)
        parts += [head, body]
        parts.append(Part('bottom plate', next(num), F.notched(0, total, PW, xs), 'plain'))
        for k in range(2):
            parts.append(F.finger_side(total, D, xs, next(num)))
        for k in range(int(F.PLUG / T)):
            parts.append(Part('plug disc', next(num),
                              rect(0, 0, W + F.INTERF_ACROSS, D + F.INTERF_ACROSS),
                              f'{int(F.PLUG / T)} press-fit into the bore under the flue'))
        outside = (PW, D + 2 * T)
    else:
        parts += [head, body]
        parts.append(Part('bottom layer', next(num), rect(0, 0, total, PW), 'plain'))
        s1, s2 = F.SIDE, F.SIDE + W
        bore = [(0, 0), (total, 0), (total, s1), (F.SAC + F.PLUG, s1),
                (F.SAC + F.PLUG, s2), (total, s2), (total, PW), (0, PW),
                (0, s2), (F.SAC, s2), (F.SAC, s1), (0, s1)]
        for k in range(int(round(D / T))):
            parts.append(Part('bore layer', next(num), bore,
                              'the chamber and the bore cut out, the plug left solid'))
        outside = (PW, D + 2 * T)
    if wall > T:
        z0, z1 = min(hx) - F.DOUBLER_PAST, max(hx) + F.DOUBLER_PAST
        p = Part('doubler', next(num), rect(z0, 0, z1, PW),
                 'glued over the finger-hole run, holes and depressions in line')
        for x, d in zip(hx, diams):
            p.hole(x, yc, d)
        # the finger meets the doubler, not the plate, so the depressions go here
        p.images, body.images = body.images, []
        parts.append(p)
    parts.append(Y.cap_part(next(num), outside[0], outside[1]))
    b0 = exit_[0] - F.BIRD_UPSTREAM
    for k in range(F.BIRD_LAYERS):
        parts.append(Part('bird layer', next(num), rect(b0, 0, win[0], PW),
                          'plain: the flue is in the nest' if k == 0 else 'glued on the one below'))
    for p in parts:
        if not hasattr(p, 'images'):
            p.images = []
    info = dict(total=total, wc=wc, split=split, PW=PW, hx=hx, exit=exit_, win=win,
                fingers=xs if kind == 'box' else [], rings=rings,
                doubler=(min(hx) - F.DOUBLER_PAST, max(hx) + F.DOUBLER_PAST) if wall > T else None)
    return parts, info


def checks(kind, W, D, wall, parts, info, L, holes, diams, cents, sheets):
    out = []
    note = lambda ok, what, detail: out.append((ok, what, detail))
    note(max(abs(c) for c in cents) < 1.0, 'the model hits all six notes',
         f'worst {max(abs(c) for c in cents):.2f} cents, window {W:.2f} wide')
    note(info['total'] + 2 * F.MARGIN <= F.BED[0], 'the longest part fits the bed',
         f'{info["total"]:.1f}mm')
    note(max(diams) <= W - 2 * F.MIN_WEB, 'every finger hole opens inside the bore',
         f'largest {max(diams):.2f}mm')
    cap = [p for p in parts if p.name == 'mouthpiece cap'][0]
    cx, cy, r = cap.notch
    into = cy + r - T - (cap.h - (D + 2 * T)) / 2
    note(into > 0, 'the cap\'s notch opens into the bore',
          f'{cy + r:.2f}mm deep, {into:.2f}mm past the bottom wall')
    gaps = [holes[i] - holes[i + 1] - (info['rings'][i] + info['rings'][i + 1]) / 2
            for i in range(4)]
    note(min(gaps) >= 0, 'the depressions do not run into each other',
         f'closest {min(gaps):.1f}mm apart')
    note(max(info['rings']) <= info['PW'] - 2, 'each depression stays on the plate',
         f'{max(info["rings"]):.1f}mm on {info["PW"]:.2f}')
    if kind == 'box':
        near = min((min(abs(x - a), abs(x - b)) - F.FINGER / 2
                    for x in info['fingers'] for a, b in (info['exit'], info['win'])),
                   default=99)
        note(near >= F.FINGER_CLEAR, 'no finger notch beside a full-width opening',
             f'{len(info["fingers"])} fingers a side, nearest {near:.1f}mm from one')
        note(max(info['rings']) / 2 <= info['PW'] / 2 - T,
             'each depression clears the finger notches',
             f'{info["PW"] / 2 - T - max(info["rings"]) / 2:.1f}mm to spare')
    near = info['split'] - info['win'][1]
    top_ring = min(info['hx']) - max(info['rings']) / 2 - info['split']
    note(near >= 10 and top_ring >= 10, 'the butt joint clears the window and the top hole',
         f'{near:.0f}mm past the window, {top_ring:.0f}mm before the top depression')
    note(all(s['w'] <= F.BED[0] and s['h'] <= F.BED[1] for s in sheets),
         'every sheet fits the bed', f'{len(sheets)} sheet(s), largest '
         f'{max(s["w"] for s in sheets):.0f} x {max(s["h"] for s in sheets):.0f}mm')
    placed = sum(len(s['parts']) for s in sheets)
    note(placed == len(parts), 'every part is on a sheet', f'{placed} of {len(parts)}')
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
            if only not in VARIANTS:
                raise SystemExit(f'error: {only} is not a variant. They are '
                                 + ', '.join(VARIANTS) + '.')
        else:
            raise SystemExit(f'error: {x} is not a flag this generator reads. '
                             f'It takes --out=, --only=, --flat and --no-write.')
    if write and not out:
        raise SystemExit('error: --out=DIR, or --no-write to run the checks only.')
    designs, bad = {}, 0
    for name, (kind, W, D, wall) in VARIANTS.items():
        if only and name != only:
            continue
        key = (round(W, 4), round(D, 4), wall)
        if key not in designs:
            designs[key] = design(W, D, wall)
        L, holes, diams, cents = designs[key]
        parts, info = build(kind, W, D, wall, L, holes, diams)
        sheets = pack(parts)
        print(f'\n{name}: {kind}, bore {W:.2f} x {D:.2f}mm, {wall:g}mm hole wall, '
              f'window {W:.2f} x {M.WINDOW_L:g}mm')
        print(f'  sound chamber {L:.1f}mm from the window centre; holes ' + ', '.join(
            f'{h:.1f}/ø{d:.1f}' for h, d in zip(holes, diams)))
        for ok, what, detail in checks(kind, W, D, wall, parts, info, L, holes, diams,
                                       cents, sheets):
            print(f'  {"pass" if ok else "FAIL"}  {what:46} {detail}')
            bad += not ok
        if write and not bad:
            d = out if flat else os.path.join(out, name)
            os.makedirs(d, exist_ok=True)
            for k, s in enumerate(sheets, 1):
                what = ', '.join(sorted({p.name for p, _, _ in s['parts']}))
                f = os.path.join(d, f'square-flute-A4-{name}-sheet{k}-cut-files.svg')
                open(f, 'w').write(Y.svg(name, k, len(sheets), s, what)
                                   .replace("The author's 2017 flute, redrawn",
                                            "Square-bore flute in A4 with the 2017 flute's ideas")
                                   .replace("The author's flute,",
                                            "Square-bore flute in A4,"))
                print(f'  wrote {os.path.basename(f)}  {s["w"]:.0f} x {s["h"]:.0f}mm, '
                      f'{len(s["parts"])} parts')
    if bad:
        print(f'\n  {bad} check(s) failed. Nothing written.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
