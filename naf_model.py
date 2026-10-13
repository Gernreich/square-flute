#!/usr/bin/env python3
"""A five-hole minor-pentatonic flute in the Native American style, as a
transmission-matrix model: where the foot and the five finger holes go for a
given bore section and hole-wall thickness.

    python3 naf_model.py                 # every variant, side by side
    python3 naf_model.py --hole=7.5      # another finger-hole diameter
    python3 naf_model.py --mouth=1.0     # scale the window's end correction

The reference is a round-bore flute in A4: 7/8in (22.2mm) bore, A4 = 440Hz
with every hole closed, and the minor pentatonic above it -- C5, D5, E5, G5 and
A5 as the holes open from the foot up. Each variant keeps that bore's AREA,
387mm^2, in a section the plywood can build.

The model, from the foot up:

  * the bore is a lossy tube. Its wave impedance comes from its area; its
    viscothermal loss from its hydraulic radius 2A/P, which is what a square
    or a rectangle changes even at the same area (the square's is 9.83mm
    against the round bore's 11.1, so it loses a little more);
  * the foot radiates as an unflanged open end of the same area;
  * each finger hole is Keefe's (1990) tone hole -- a shunt and two series
    halves -- open or closed. Its chimney is the WALL THICKNESS, 3 or 6mm,
    and nothing else, because a flat plate has no curvature for the hole to
    cut through. That is the one place the variants differ most;
  * at the top, the true sound hole (the window) opens into the bore with a
    short closed stub above it to the plug. The jet drives the window, so the
    flute sounds where the reactance of the window and the bore in series
    passes through zero.

THE WINDOW IS THE UNCALIBRATED PART. Its end correction is physics-based but
not measured, and it moves the foot by more than any other term: each 1mm of
window correction is about 4.5mm of sound chamber at the 10mm window, 2.6mm at
a full-width one. So the foot is cut LONG (FOOT_SPARE) and trimmed to pitch,
and --mouth= is the knob to set once a real flute has been measured. The holes
move with it ALMOST AS FAR -- a 10% error moves the foot 3.5mm and the holes
2.3 to 3.0mm -- so trimming the foot does not put them right: each is tuned.
(This said 5.5mm and "the holes depend on it far less" until 2026-10-13,
from an area ratio never run through the model. Both were wrong.)
"""
import cmath
import math
import sys

# --- air, warm from the breath ----------------------------------------------
T_C = 25.0
C = 331.3 * math.sqrt(1 + T_C / 273.15)          # 346.1 m/s
RHO = 1.184

# --- the tune ----------------------------------------------------------------
A4 = 440.0
NOTES = ['A4', 'C5', 'D5', 'E5', 'G5', 'A5']
SEMIS = [0, 3, 5, 7, 10, 12]
TARGETS = [A4 * 2 ** (s / 12) for s in SEMIS]

# --- the head, the same for every variant (mm) ------------------------------
WINDOW_W, WINDOW_L = 10.0, 7.0     # true sound hole: across x along the bore
WINDOW_T = 3.0                     # it is always in a single 3mm plate
MOUTH = 1.0                        # scales the window's end correction
FOOT_SPARE = 15.0                  # cut this much long, trim to pitch
HOLE_D = 8.0                       # finger-hole diameter, equal-hole mode
SPACING = 25.0                     # centre to centre within a hand
ANCHOR_D = 8.0                     # holes 2 and 4, whose positions are solved
D_MIN, D_MAX = 4.0, 11.0           # what a finger and the bore allow

REF_BORE = 22.2                    # 7/8in
AREA = math.pi * (REF_BORE / 2) ** 2

# name, bore across, bore deep, hole wall, how it is built
VARIANTS = [
    ('round reference', None, None, 5.0, 'turned wood, for comparison'),
    ('box-square-3', math.sqrt(AREA), math.sqrt(AREA), 3.0, 'finger-jointed box'),
    ('box-square-6', math.sqrt(AREA), math.sqrt(AREA), 6.0, 'finger-jointed box, doubled top'),
    ('box-rect-3', AREA / 21.0, 21.0, 3.0, 'finger-jointed box'),
    ('box-rect-6', AREA / 21.0, 21.0, 6.0, 'finger-jointed box, doubled top'),
    ('stack-rect-3', AREA / 21.0, 21.0, 3.0, 'laminated stack, 7 bore layers'),
    ('stack-rect-6', AREA / 21.0, 21.0, 6.0, 'laminated stack, two top layers'),
]


class Bore:
    """A section: its area, its equivalent radius and its loss radius (m)."""

    def __init__(self, wide=None, deep=None):
        if wide is None:
            r = REF_BORE / 2000
            self.A, self.rh = math.pi * r * r, r
        else:
            w, d = wide / 1000, deep / 1000
            self.A, self.rh = w * d, 2 * w * d / (2 * (w + d))
        self.a = math.sqrt(self.A / math.pi)

    def k(self, f):
        # Benade's wall loss, alpha = 3.0e-5 sqrt(f) / r per metre, on the
        # hydraulic radius: the part of the loss a corner changes
        return 2 * math.pi * f / C - 1j * 3.0e-5 * math.sqrt(f) / self.rh

    def z0(self):
        return RHO * C / self.A


def tube(b, f, L):
    k, z = b.k(f), b.z0()
    c, s = cmath.cos(k * L), cmath.sin(k * L)
    return ((c, 1j * z * s), (1j * s / z, c))


def mul(m, n):
    return ((m[0][0] * n[0][0] + m[0][1] * n[1][0], m[0][0] * n[0][1] + m[0][1] * n[1][1]),
            (m[1][0] * n[0][0] + m[1][1] * n[1][0], m[1][0] * n[0][1] + m[1][1] * n[1][1]))


def hole(b, f, d, t, is_open):
    """Keefe's tone hole: series half, shunt, series half."""
    k = 2 * math.pi * f / C
    r, a = d / 2000, b.a
    t = t / 1000
    dl = r / a
    zh = RHO * C / (math.pi * r * r)
    if is_open:
        te = ((1 / k) * math.tan(k * t) + r * (1.40 - 0.58 * dl ** 2)) / \
             (1 - 0.61 * k * r * math.tan(k * t))
        zs = zh * (1j * k * te + 0.25 * (k * r) ** 2)
        ta = 0.47 * r * dl ** 4 / (math.tanh(1.84 * t / r) + 0.62 * dl ** 2 + 0.64 * dl)
    else:
        tc = t + r * dl * (1 + 0.207 * dl ** 3) / 8
        zs = -1j * zh / math.tan(k * tc)
        ta = 0.47 * r * dl ** 4 / (1 / math.tanh(1.84 * t / r) + 0.62 * dl ** 2 + 0.64 * dl)
    za = -1j * zh * k * ta
    half = ((1, za / 2), (0, 1))
    return mul(mul(half, ((1, 0), (1 / zs, 1))), half)


def window_z(f):
    """The true sound hole as a short neck of its own area into open air.
    Its correction is a rectangle's equivalent radius, flanged both sides
    (0.82 a each), scaled by MOUTH."""
    w = 2 * math.pi * f
    Aw = WINDOW_W * WINDOW_L / 1e6
    aw = math.sqrt(Aw / math.pi)
    leff = WINDOW_T / 1000 + MOUTH * 2 * 0.82 * aw
    k = w / C
    return RHO * C / Aw * (0.5 * (k * aw) ** 2) + 1j * w * RHO * leff / Aw


def reactance(b, f, L, holes, n_open, wall, diams):
    """Im(Z) the jet sees, for a sound chamber of L mm (window centre to
    foot) with holes at their distances from the window, the lowest n_open of
    them open."""
    k, z = b.k(f), b.z0()
    ka = 2 * math.pi * f / C * b.a
    zr = z * (0.25 * ka ** 2 + 1j * 0.6133 * ka)
    # walk from the foot to the window: segments between holes
    # holes and diams are foot-most first: holes[0] is hole 1
    xs = holes
    pos, m = L, ((1, 0), (0, 1))
    chain = []
    for i, x in enumerate(xs):
        chain.append(('tube', pos - x))
        # holes are numbered from the foot: the foot-most is hole 1
        chain.append(('hole', (i < n_open, diams[i])))
        pos = x
    chain.append(('tube', pos))
    for kind, v in reversed(chain):
        if kind == 'tube':
            m = mul(m, tube(b, f, v / 1000))
        else:
            m = mul(m, hole(b, f, v[1], wall, v[0]))
    zin = (m[0][0] * zr + m[0][1]) / (m[1][0] * zr + m[1][1])
    # the closed stub between the window centre and the plug
    stub = -1j * z / cmath.tan(k * (WINDOW_L / 2000))
    zb = 1 / (1 / zin + 1 / stub)
    return (window_z(f) + zb).imag


def sounding(b, L, holes, n_open, wall, near, diams):
    """The playing frequency nearest `near`: a zero crossing of the
    reactance, rising through zero, found by scanning then bisecting."""
    lo, hi = near / 1.4, near * 1.4
    n = 80
    X = lambda f: reactance(b, f, L, holes, n_open, wall, diams)
    prev_f, prev_x = lo, X(lo)
    best = None
    for i in range(1, n + 1):
        f = lo + (hi - lo) * i / n
        x = X(f)
        if prev_x < 0 <= x:
            a, c = prev_f, f
            for _ in range(40):
                mid = (a + c) / 2
                if X(mid) < 0:
                    a = mid
                else:
                    c = mid
            root = (a + c) / 2
            if best is None or abs(root - near) < abs(best - near):
                best = root
        prev_f, prev_x = f, x
    if best is None:
        raise ValueError(f'no resonance within 40% of {near:.1f}Hz')
    return best


def bisect(fn, target, lo, hi, rising=False, n=40):
    """x in [lo, hi] with fn(x) == target. fn falls as x grows, unless
    rising. Raises when the target is outside what the interval can reach,
    rather than returning an endpoint as if it were an answer."""
    flo, fhi = fn(lo), fn(hi)
    if rising:
        flo, fhi = -flo, -fhi
        target = -target
        g = lambda x: -fn(x)
    else:
        g = fn
    if not (fhi <= target <= flo):
        raise ValueError(f'out of reach between {lo:.1f} and {hi:.1f}')
    for _ in range(n):
        mid = (lo + hi) / 2
        if g(mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def design(b, wall, even=False):
    """Sound-chamber length, five hole positions and five diameters, all
    positions from the window centre and foot-most first, iterated until each
    closed hole's effect on the others settles.

    Equal holes (even=False): every hole HOLE_D, positions solved.

    Laid out for the hands (even=True): the lower hand covers holes 1-3 and
    the upper hand 4-5, each hand's holes SPACING apart. Holes 2 and 4 are
    ANCHOR_D and their positions are solved, which settles where each hand
    sits; holes 1, 3 and 5 stand SPACING from their anchor and their
    DIAMETERS are solved. The lower hand is anchored on its MIDDLE hole: its
    natural gaps are 27 and 30mm, and anchored on hole 1 the third hole had to
    be bigger than the bore allows to reach E5. The gap between the hands is whatever the scale
    makes it. Spacing all five evenly cannot work: the natural gaps run about
    27, 30, 46 and 12mm, because a minor third and a whole tone are not the
    same distance apart."""
    L = 330.0
    # a start near where these flutes land, as fractions of the chamber; the
    # solver keeps the holes in order, so a start that is far off can trap a
    # hole between two neighbours that cannot reach its note
    holes = [L * r for r in (0.69, 0.61, 0.52, 0.37, 0.33)]
    diams = [ANCHOR_D if even else HOLE_D] * 5
    for it in range(6):
        L = bisect(lambda x: sounding(b, x, holes, 0, wall, A4, diams),
                   A4, 250, 420)
        for n in range(1, 6):
            i = n - 1
            def f_pos(x, i=i, n=n):
                hs = holes[:]; hs[i] = x
                return sounding(b, L, hs, n, wall, TARGETS[n], diams)
            def f_dia(d, i=i, n=n):
                ds = diams[:]; ds[i] = d
                return sounding(b, L, holes, n, wall, TARGETS[n], ds)
            if not even or n in (2, 4):
                # only ORDER is enforced here; whether a finger fits between
                # two holes is reported, not imposed, or a poor start traps a
                # hole short of its note. The hole ABOVE still stands where
                # the last pass, or the starting guess, put it, and at
                # --mouth=0.8 -- the very command the README gives for
                # recalibrating -- that fenced hole 5 out of its note ("out
                # of reach between 30.0 and 117.4"). So when a hole cannot
                # reach its note the fence above it is moved back, 20mm at a
                # time, to 30mm from the window. Not straight to 30: that far
                # up the scan meets another resonance and hole 1 failed
                # instead. At the default window the first try always lands,
                # so nothing shipped moves.
                lo = holes[i + 1] + 0.5 if n < 5 else 30.0
                hi = holes[i - 1] - 0.5 if n > 1 else L - 15
                while True:
                    try:
                        holes[i] = bisect(f_pos, TARGETS[n], lo, hi)
                        break
                    except ValueError:
                        if lo <= 30.0:
                            raise
                        lo = max(30.0, lo - 20.0)
                if even and n == 2:
                    holes[0], holes[2] = holes[1] + SPACING, holes[1] - SPACING
                if even and n == 4:
                    holes[4] = holes[3] - SPACING
            else:
                diams[i] = bisect(f_dia, TARGETS[n], D_MIN, D_MAX, rising=True)
    cents = [1200 * math.log2(sounding(b, L, holes, n, wall, TARGETS[n], diams)
                              / TARGETS[n]) for n in range(6)]
    return L, holes, diams, cents


def main():
    global HOLE_D, MOUTH, SPACING
    for x in sys.argv[1:]:
        if x.startswith('--hole='):
            HOLE_D = float(x.split('=', 1)[1])
        elif x.startswith('--mouth='):
            MOUTH = float(x.split('=', 1)[1])
        elif x.startswith('--spacing='):
            SPACING = float(x.split('=', 1)[1])
        else:
            raise SystemExit(f'error: {x} is not a flag this model reads. '
                             f'It takes --hole=, --mouth= and --spacing=.')
    print(f'A4 = {A4:g}Hz, air at {T_C:g}C ({C:.1f} m/s), area {AREA:.1f}mm^2, '
          f'window {WINDOW_W:g} x {WINDOW_L:g}mm, mouth x{MOUTH:g}')
    print('distances from the window centre, mm; holes numbered from the foot')
    for even in (False, True):
        print('\n' + (f'LAID OUT FOR THE HANDS, 3 + 2 holes {SPACING:g}mm apart, holes 2 and 4 '
                      f'{ANCHOR_D:g}mm, the rest sized to pitch' if even else
                      f'EQUAL HOLES, all {HOLE_D:g}mm, positions solved'))
        print(f'{"variant":16} {"bore":>12} {"wall":>4} {"foot":>6} '
              + ' '.join(f'{"h" + str(i):>11}' for i in range(1, 6))
              + '  worst')
        seen = {}
        for name, w, d, wall, how in VARIANTS:
            b = Bore(w, d)
            key = (round(b.A * 1e9), round(b.rh * 1e6), wall)
            if key not in seen:
                # equal holes can have no layout at all: at --mouth=0.8 with a
                # 6mm wall, hole 5 would have to sit on hole 4. That is a
                # finding about equal holes, not a crash, so it is printed
                try:
                    seen[key] = design(b, wall, even)
                except ValueError as e:
                    seen[key] = str(e)
            sec = 'ø22.20' if w is None else f'{w:.2f}x{d:.2f}'
            if isinstance(seen[key], str):
                print(f'{name:16} {sec:>12} {wall:4g}   no layout: {seen[key]}')
                continue
            L, holes, diams, cents = seen[key]
            print(f'{name:16} {sec:>12} {wall:4g} {L:6.1f} '
                  + ' '.join(f'{h:6.1f}/{dd:<4.1f}' for h, dd in zip(holes, diams))
                  + f'  {max(abs(c) for c in cents):.2f}c')
    return 0


if __name__ == '__main__':
    sys.exit(main())
