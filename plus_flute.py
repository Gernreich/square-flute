#!/usr/bin/env python3
"""The nest-flue and savanna-flue builds: square_flute's bird-flue builds,
with the flue carved in the nest instead of the bird, or split between them.

    python3 plus_flute.py --no-write              # the checks, write nothing
    python3 plus_flute.py --out=cut-files         # into cut-files/<build>/
    python3 plus_flute.py --only=box-square-3-nest-flue --flat --out=DIR

Every build here shares its bird-flue counterpart's bore, holes, foot,
full-width window and exit hole, mouthpiece cap and finger-hole depressions,
all of which came from the author's 2017 flute (yours/) and now sit in
square_flute.py. What this file changes is only the flue: a fill engrave in
the NEST, the top plate's face over the plug, the plains style, rather than
the bird's underside, the woodland style. The bird is then three plain layers.

THE SAVANNA BUILDS, -savanna-flue (2026-10-13, the author: "where the
woodlands meet the prairie"), split the flue between the two: half its depth
engraved in the nest and half in the bird's underside, about 0.5mm each, so
the airstream runs between the heights a bird flue and a nest flue give it.
The two engraves must line up when the bird goes on.

These were the "-plus" variants until 2026-10-13. They began with five of the
2017 flute's ideas; one by one, at the author's asking, the rest went onto
every build, until the flue was the only difference left, and the author
named them for it.

NOT taken from the original: its engraved splitting edge, which charred and
did not work, so the edge is filed by hand; and its stepped block, whose
outline was for looks only.

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
RING_OF = F.RING_OF                   # the original's depression across its hole

NEST = {k.replace('-bird-flue', '-nest-flue'): v for k, v in F.VARIANTS.items()}
SAVANNA = {k.replace('-bird-flue', '-savanna-flue'): v for k, v in F.VARIANTS.items()}
VARIANTS = {**NEST, **SAVANNA}


def design(W, D, wall):
    return F.design(W, D, wall)


def build(kind, W, D, wall, L, holes, diams, savanna=False):
    wc = F.SAC + F.PLUG + M.WINDOW_L / 2
    total = wc + L + M.FOOT_SPARE
    hx = [wc + h for h in holes]
    PW = W + 2 * T if kind in ('box', 'flat') else W + 2 * F.SIDE
    yc = PW / 2
    exit_ = (F.SAC - F.EXIT_L, F.SAC)
    win = (F.SAC + F.PLUG, F.SAC + F.PLUG + M.WINDOW_L)
    num = iter(range(1, 100))
    parts = []

    # one piece, as square_flute's top is: `head` and `body` below are the
    # same plate, the names kept for which end of it each line is about
    head = Part('top plate', next(num), rect(0, 0, total, PW),
                'full-width exit hole and window, the flue engraved between, the '
                'finger holes in their depressions; file the window\'s far edge to '
                'a bevel before assembly')
    head.slot(exit_[0], yc - W / 2, exit_[1], yc + W / 2)
    head.slot(win[0], yc - W / 2, win[1], yc + W / 2)
    head.fills.append(rect(exit_[1], yc - W / 2, win[0], yc + W / 2))
    body = head
    for x, d in zip(hx, diams):
        body.hole(x, yc, d)
    rings = [d * RING_OF for d in diams]
    body.images = [('ring.png', x - r / 2, yc - r / 2, r, r) for x, r in zip(hx, rings)]

    if kind in ('box', 'flat'):
        # a finger notch beside the exit hole or the window would run straight
        # into it: both reach the bore's inner face, which is the notch's floor
        xs = F.fingers_x(total, (exit_, win)) if kind == 'box' else []
        parts.append(head)
        if xs:
            head.outline = F.notched(0, total, PW, xs)
            parts.append(F.end_notch(Part('bottom plate', next(num), F.notched(0, total, PW, xs),
                                          'a half-round notch in the mouth end')))
            for k in range(2):
                parts.append(F.finger_side(total, D, xs, next(num)))
        else:
            parts.append(F.end_notch(Part('bottom plate', next(num), rect(0, 0, total, PW),
                                          'a half-round notch in the mouth end')))
            for k in range(2):
                parts.append(Part('side wall', next(num), rect(0, 0, total, D),
                                  'glued between the top and the bottom'))
        for k in range(int(F.PLUG / T)):
            parts.append(Part('plug disc', next(num),
                              rect(0, 0, W + F.INTERF_ACROSS, D + F.INTERF_ACROSS),
                              f'{int(F.PLUG / T)} press-fit into the bore under the flue'))
        outside = (PW, D + 2 * T)
    else:
        parts.append(head)
        parts.append(F.end_notch(Part('bottom layer', next(num), rect(0, 0, total, PW),
                                      'a half-round notch in the mouth end')))
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
    parts.append(F.cap_part(next(num), outside[0], outside[1]))
    b0 = exit_[0] - F.BIRD_UPSTREAM
    for k in range(F.BIRD_LAYERS):
        p = Part('bird layer', next(num), rect(b0, 0, win[0], PW),
                 ('the other half of the flue fill-engraved, about 0.5mm deep' if savanna
                  else 'plain: the flue is in the nest') if k == 0 else 'glued on the one below')
        if k == 0 and savanna:
            # the bird flue's own span, as square_flute draws it: from the
            # exit hole's upstream edge to the window
            p.fills.append(rect(exit_[0], yc - W / 2, win[0], yc + W / 2))
        parts.append(p)
    for p in parts:
        if not hasattr(p, 'images'):
            p.images = []
    info = dict(total=total, wc=wc, PW=PW, hx=hx, exit=exit_, win=win,
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
    bots = [p for p in parts if getattr(p, 'end_notch', None)]
    yc_, rn = bots[0].end_notch if bots else (0, 99)
    note(len(bots) == 1 and rn <= W / 2 - 1.0,
         'the bottom\'s end notch opens into the bore, clear of its walls',
         f'{2 * rn:.2f}mm across in a {W:.2f}mm bore')
    birds = [p for p in parts if p.name == 'bird layer' and p.fills]
    if birds:       # a savanna build: the two halves of its flue must line up
        tf = [p for p in parts if p.name.startswith('top')][0].fills[0]
        bf = birds[0].fills[0]
        x0, x1 = max(tf[0][0], bf[0][0]), min(tf[1][0], bf[1][0])
        note(x1 - x0 >= info['win'][0] - info['exit'][1] - 0.01 and tf[0][1] == bf[0][1],
             'both halves of the flue cover the plug, in line',
             f'{x1 - x0:.1f}mm in common, {len(birds)} bird layer engraved')
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
    tops = [p for p in parts if p.name.startswith('top')]
    note(len(tops) == 1 and tops[0].w == info['total'], 'the top is one piece',
         f'{len(tops)} plate, {tops[0].w:.1f}mm long')
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
        parts, info = build(kind, W, D, wall, L, holes, diams, savanna=name in SAVANNA)
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
                                            "Square-bore flute in A4,")
                                   .replace('the flue as a fill engrave about 1mm deep over the plug',
                                            'the flue as a fill engrave about 0.5mm deep over the plug '
                                            'and 0.5mm in the bird\'s underside, to line up'
                                            if name in SAVANNA else
                                            'the flue as a fill engrave about 1mm deep over the plug'))
                print(f'  wrote {os.path.basename(f)}  {s["w"]:.0f} x {s["h"]:.0f}mm, '
                      f'{len(s["parts"])} parts')
    if bad:
        print(f'\n  {bad} check(s) failed. Nothing written.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
