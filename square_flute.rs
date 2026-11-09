//! The square flute's generator (below, from THE SQUARE FLUTE'S OWN
//! GENERATOR), and first what the ocarinas, the octagonal flute, the panpipes
//! and the chanters borrow from it: the ply, the kerf, the finger joint, the
//! bed and the inks, a part and the shelf packing. Rust since 2026-11-07
//! (square_flute.py until then; the move changed no byte of any file).
use lasermade_tools::turn3d::{Num, Pt, F, I};
use std::sync::atomic::{AtomicU64, Ordering};

pub const T: f64 = 3.0; // ply
pub const INTERF_ACROSS: f64 = 0.12; // the plug discs' press-fit, across the ply
pub const FINGER: f64 = 2.0 * T; // finger width, and the space between fingers
pub const FINGER_PLAY: f64 = 0.0;
pub const FINGER_END: f64 = 2.0 * FINGER; // clear of each end
pub const FINGER_CLEAR: f64 = 3.0;
pub const BED: (f64, f64) = (600.0, 305.0); // xTool P2S, tested 2026-10-19
pub const MARGIN: f64 = 5.0;
pub const GAP: f64 = 4.0;
pub const MIN_WEB: f64 = 1.5;
pub const BLUE: &str = "#0000ff";
pub const ORANGE: &str = "#ff8000";
pub const BLACK: &str = "#000000";

/// naf_model.rs's speed of sound, m/s: air at T_C, warm from the breath.
pub const T_C: f64 = 25.0;
pub fn c() -> f64 {
    331.3 * (1.0 + T_C / 273.15).sqrt()
}
pub const RHO: f64 = 1.184;

static KERF: AtomicU64 = AtomicU64::new(0x3fc0a3d70a3d70a4); // 0.13, measured

pub fn kerf() -> f64 {
    f64::from_bits(KERF.load(Ordering::Relaxed))
}

/// --kerf=MM: the laser's real kerf; every outline is offset by half of it
/// when the sheet is written.
pub fn set_kerf(arg: &str) -> f64 {
    let v = arg.split_once('=').map(|x| x.1).unwrap_or("");
    let k = lasermade_tools::py::float(v)
        .unwrap_or_else(|| lasermade_tools::die(format!("error: {arg} is not a kerf in mm, e.g. --kerf=0.15.")));
    if !(0.0..=0.5).contains(&k) {
        lasermade_tools::die(format!("error: a {}mm kerf is outside 0 to 0.5mm.", lasermade_tools::py::g(k)));
    }
    KERF.store(k.to_bits(), Ordering::Relaxed);
    k
}

pub fn rect(x0: Num, y0: Num, x1: Num, y1: Num) -> Vec<Pt> {
    vec![[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
}

/// Where the side walls' fingers go along L: FINGER wide, FINGER apart,
/// centred, FINGER_END clear of each end, none within FINGER_CLEAR of an
/// interval in `clear`.
pub fn fingers_x(l: f64, clear: &[(f64, f64)]) -> Vec<f64> {
    let pitch = 2.0 * FINGER;
    let n = ((l - 2.0 * FINGER_END - FINGER) / pitch).floor() as i64 + 1;
    let span = (n - 1) as f64 * pitch;
    let reach = FINGER / 2.0 + FINGER_CLEAR;
    (0..n.max(0))
        .map(|i| l / 2.0 - span / 2.0 + i as f64 * pitch)
        .filter(|&x| !clear.iter().any(|&(a, b)| a - reach < x && x < b + reach))
        .collect()
}

/// An inner cut: a polygon (the flute's 'rect' and 'poly' alike) or a circle.
#[derive(Clone, Debug)]
pub enum Cut {
    Poly(Vec<Pt>),
    Circle(f64, f64, f64),
}

#[derive(Clone, Debug)]
pub struct Part {
    pub name: String,
    pub num: usize,
    pub note: String,
    pub outline: Vec<Pt>, // physical, before the kerf
    pub cuts: Vec<Cut>,
    pub x0: f64,
    pub y0: f64,
    pub w: f64,
    pub h: f64,
}

impl Part {
    pub fn new(name: &str, num: usize, outline: Vec<Pt>, note: &str) -> Part {
        let mut p = Part { name: name.into(), num, note: note.into(), outline, cuts: vec![], x0: 0.0, y0: 0.0, w: 0.0, h: 0.0 };
        p.bounds();
        p
    }
    /// x0, y0, w, h from the outline, as the constructor sets them
    pub fn bounds(&mut self) {
        let xs: Vec<f64> = self.outline.iter().map(|q| q[0].f()).collect();
        let ys: Vec<f64> = self.outline.iter().map(|q| q[1].f()).collect();
        let (x0, y0) = (fmin(&xs), fmin(&ys));
        self.x0 = x0;
        self.y0 = y0;
        self.w = fmax(&xs) - x0;
        self.h = fmax(&ys) - y0;
    }
    pub fn of(&self) -> Vec<(f64, f64)> {
        self.outline.iter().map(|q| (q[0].f(), q[1].f())).collect()
    }
}

/// Python's max() and min() of floats: the first of equals.
pub fn fmax(v: &[f64]) -> f64 {
    v[1..].iter().fold(v[0], |a, &b| if b > a { b } else { a })
}
pub fn fmin(v: &[f64]) -> f64 {
    v[1..].iter().fold(v[0], |a, &b| if b < a { b } else { a })
}

pub fn f(x: f64) -> Num {
    F(x)
}
pub const Z: Num = I(0);

/// A side wall D tall whose fingers stand T proud, up into the top and down
/// into the bottom, flush with their outside faces.
pub fn finger_side(l: f64, d: f64, xs: &[f64], n: usize) -> Part {
    let fw = FINGER + FINGER_PLAY;
    let mut o: Vec<Pt> = vec![[Z, Z]];
    for &x in xs {
        o.extend([[F(x - fw / 2.0), Z], [F(x - fw / 2.0), F(-T)], [F(x + fw / 2.0), F(-T)], [F(x + fw / 2.0), Z]]);
    }
    o.push([F(l), Z]);
    o.push([F(l), F(d)]);
    for &x in xs.iter().rev() {
        o.extend([[F(x + fw / 2.0), F(d)], [F(x + fw / 2.0), F(d + T)], [F(x - fw / 2.0), F(d + T)], [F(x - fw / 2.0), F(d)]]);
    }
    o.push([Z, F(d)]);
    Part::new("side wall", n, o, "fingers into the top and the bottom")
}

/// One sheet: the parts on it by index, with where each sits, and its size.
#[derive(Clone, Debug)]
pub struct Sheet {
    pub parts: Vec<(usize, f64, f64)>,
    pub w: f64,
    pub h: f64,
}

/// Shelves across the bed, tallest row first; a part goes on the first shelf
/// with room, and a new sheet starts when no shelf has any. `sizes` is each
/// part's (w, h); the sheets name parts by their index in it.
pub fn pack(sizes: &[(f64, f64)]) -> Vec<Sheet> {
    struct Row {
        x: f64,
        y: f64,
        h: f64,
        items: Vec<(usize, f64, f64)>,
    }
    struct Sh {
        rows: Vec<Row>,
        y: f64,
    }
    let k = kerf();
    let mut order: Vec<usize> = (0..sizes.len()).collect();
    // sorted() by (-w, -h): stable
    order.sort_by(|&a, &b| {
        let (pa, pb) = (sizes[a], sizes[b]);
        (-pa.0).partial_cmp(&-pb.0).unwrap().then((-pa.1).partial_cmp(&-pb.1).unwrap())
    });
    let mut sheets: Vec<Sh> = vec![];
    for i in order {
        let (pw, ph) = (sizes[i].0 + k, sizes[i].1 + k);
        let mut put = false;
        for s in sheets.iter_mut() {
            for row in s.rows.iter_mut() {
                if row.x + pw <= BED.0 - MARGIN && ph <= row.h {
                    row.items.push((i, row.x, row.y));
                    row.x += pw + GAP;
                    put = true;
                    break;
                }
            }
            if put {
                break;
            }
            if s.y + ph <= BED.1 - MARGIN {
                s.rows.push(Row { x: MARGIN + pw + GAP, y: s.y, h: ph, items: vec![(i, MARGIN, s.y)] });
                s.y += ph + GAP;
                put = true;
                break;
            }
        }
        if !put {
            let mut s = Sh { rows: vec![], y: MARGIN };
            s.rows.push(Row { x: MARGIN + pw + GAP, y: MARGIN, h: ph, items: vec![(i, MARGIN, MARGIN)] });
            s.y += ph + GAP;
            sheets.push(s);
        }
    }
    sheets
        .into_iter()
        .map(|s| {
            let parts: Vec<(usize, f64, f64)> = s.rows.into_iter().flat_map(|r| r.items).collect();
            let w = fmax(&parts.iter().map(|&(i, x, _)| x + sizes[i].0 + k).collect::<Vec<_>>()) + MARGIN;
            let h = fmax(&parts.iter().map(|&(i, _, y)| y + sizes[i].1 + k).collect::<Vec<_>>()) + MARGIN;
            Sheet { parts, w, h }
        })
        .collect()
}

// =============================================================================
// THE SQUARE FLUTE'S OWN GENERATOR, Rust since 2026-11-07 (square_flute.py
// until then; the move changed no byte of any cut file or page).
// =============================================================================
//
// Cut files for a five-hole minor-pentatonic flute in A4, square or
// rectangular bore: six builds, each with a savanna flue in two inks.
//
//     target/release/square_flute --no-write        # the checks, write nothing
//     target/release/square_flute --out=DIR         # every variant into DIR/<variant>/
//     target/release/square_flute --only=box-square-3 --out=DIR
//     target/release/square_flute --only=box-square-3 --flat --out=DIR   # no subfolder
//
// The acoustics are naf_model.rs's: the sound-chamber length and where each
// finger hole goes, and how big, for the bore section and the hole wall. This
// only builds what that asks for, in 3mm ply.
//
// THE SIX BUILDS here are two constructions and two hole walls, the boxes
// finger-jointed or flat:
//
//   box-square    a finger-jointed box, 16.88 x 16.88mm bore: four plates,
//                 the sides' fingers in notches in the top and bottom, flush
//                 with the outside faces
//      -flat      the same box butt-jointed: plain plates, the sides glued
//                 between the top and the bottom
//   stack-rect    a laminated stack, 15.83 x 18mm: a bottom layer, six bore
//                 layers with the bore cut out of them, and the top
//      -3         the finger holes go through the 3mm top plate alone
//      -6         a 3mm doubler is glued over the finger-hole run, so each
//                 hole has a 6mm chimney, as a wooden flute's wall gives
//
// The stack cannot have a square bore at the reference's area: its depth is a
// whole number of layers, 15 or 18mm, and 16.88 is neither. Acoustically the
// bore SHAPE hardly matters -- at one window width the model puts the
// square's and the 15.83 x 18's holes within 0.1mm of each other; with each
// one's own full-width window, within 1.2mm -- so the stack keeps the area
// and gives up the square.
//
// FROM THE MOUTH END, the same in every variant:
//
//   slow air chamber   SAC long, open at the end you blow into
//   exit hole          up through the top, the last EXIT_L of the chamber
//   plug               PLUG long, solid: discs in the box, a land left uncut
//                      in the stack's bore layers
//   window             the true sound hole, right against the plug
//   sound chamber      to the foot, cut FOOT_SPARE long: trim it to A4
//
// The block (the bird) sits over the exit hole and the plug, its front edge
// on the window's upstream edge, tied on and not glued, so it can be slid to
// voice the flute. The flue is a FILL ENGRAVE, the bore's width: the one
// feature here a laser draws better than a saw, since its depth is a power
// setting rather than a cut. It is drawn as a SAVANNA flue, half in the
// bird's underside and half in the nest, the top plate's face over the plug,
// each half in an ink of its own (BIRD_INK, NEST_INK), so either or both can
// be run: a woodland (bird) or plains (nest) flue about 1mm deep, or a
// savanna one at about 0.5mm each. Until 2026-10-18 each was a build of its
// own, eighteen in all, the nest and savanna ones from a plus_flute.py.
//
// THE SPLITTING EDGE is the window's downstream edge, and it wants a clean
// bevel of about 30 degrees that a laser cannot cut. File it by hand, before
// assembly. The top is ONE piece. It was cut as a head plate and a body plate
// until 2026-10-13, so that a spoilt edge cost only the short one; the author
// saw no point in it, and it bought little for what it cost: one strip of ply
// saved, against a seam 20mm past the window to seal and a gap in the finger
// joints at the place the bird is tied on.
//
// Over the mouth end goes the author's 2017 mouthpiece cap, with its
// half-round notch in the bottom edge (CAP_D, NOTCH_IN below), and the bottom
// plate has the same circle cut half-round into its mouth end (end_notch), at
// right angles.
//
// Press-fit throughout, sealed with shellac, except what is laminated or
// cannot be press-fit: the doubler, the bird's layers, every layer of the
// stack and the mouthpiece cap are glued.

pub mod naf_model;
pub mod page_assets;
pub mod solidcraft;
pub mod your_flute;

use lasermade_tools::py;
use naf_model as m;
// the path writer, borrowed and not copied: the same one every other
// LaserMadeMusic part is written with
use ribbon_bore::path as rb_path;

pub const SIDE: f64 = 6.0; // the stack's side walls
pub const SAC: f64 = 110.0;
pub const EXIT_L: f64 = 6.0;
pub const PLUG: f64 = 12.0;
pub const DOUBLER_PAST: f64 = 20.0; // doubler runs this far past the outermost holes
pub const BIRD_LAYERS: usize = 3;
pub const BIRD_UPSTREAM: f64 = 6.0;
// The mouthpiece cap, the author's from 2017 (yours/original/Mouthpiece.svg):
// a plate over the mouth end, the flute's outside in size, whose bottom edge
// carries a half-round notch -- a 9.59mm circle centred NOTCH_IN inside the
// edge -- that opens through the bottom wall into the slow air chamber. On
// every variant since 2026-10-13, at the author's asking.
pub const CAP_D: f64 = 9.59;
pub const NOTCH_IN: f64 = 0.33;
// The finger-hole depression, also the author's: yours/original/ring.png, a
// soft dark halo engraved round each hole for the finger to find. Kept in the
// original's proportion to its hole, 12.14mm round a 7.75mm hole. On every
// variant since 2026-10-13, at the author's asking; on a 6mm variant it goes
// on the doubler, which is what the finger meets.
pub const RING_OF: f64 = 12.14 / 7.75;
pub fn here() -> &'static str {
    env!("CARGO_MANIFEST_DIR")
}
// The flue's two halves, an ink each so the laser runs either or both. The
// house order has one engrave ink, blue, which the depressions keep, and
// green and cyan are cut stages, so these two are new (2026-10-18; the
// four-hole ocarinas' duct uses them too).
pub const BIRD_INK: &str = "#ff0000";
pub const NEST_INK: &str = "#ff00ff";
// no part numbers: the 3D view shows where every part goes (the author,
// 2026-10-13), so nothing but the flue and the depressions is engraved

/// The builds, named for the construction and the hole wall: kind, bore
/// across, bore deep, hole wall. In order as three binary choices,
/// box/stack, 3/6 and fingers/flat, counted 000 to 111 with the flat stacks
/// (101, 111) left out, as the author asked (2026-10-18). A -flat box is
/// butt-jointed: plain plates, the sides glued between the top and the
/// bottom, as the author's 2017 flute was built.
pub fn variants() -> Vec<(&'static str, &'static str, f64, f64, f64)> {
    let sq = m::area().sqrt();
    let rw = m::area() / 18.0;
    vec![
        ("box-square-3", "box", sq, sq, 3.0),
        ("box-square-3-flat", "flat", sq, sq, 3.0),
        ("box-square-6", "box", sq, sq, 6.0),
        ("box-square-6-flat", "flat", sq, sq, 6.0),
        ("stack-rect-3", "stack", rw, 18.0, 3.0),
        ("stack-rect-6", "stack", rw, 18.0, 6.0),
    ]
}

/// The two long builds (2026-11-08, at the author's asking): box-square-3
/// made as long as the bed allows, the key whatever that length sounds:
/// 589.5 mm overall, the 600 mm bed less MARGIN each end and room for a
/// kerf up to 0.5 mm (at 590 the sheet came out 600.13 mm wide). Named
/// -590 all the same. The bore is
/// wider, a 22.23 mm round bore's area in a 19.70 mm square, so the
/// biggest finger hole keeps 3 mm of ply beside the finger notches (the
/// 19.05 mm reference left 1.7 mm), and the hands are 31 mm apart, so
/// hole 3 stays near 10 mm where large fingers seal it. F4 keeps the
/// 110 mm slow air chamber; E4 takes 30 mm from it and gives them to the
/// sound chamber, a semitone lower in the same length. The slow air
/// chamber is outside the acoustics (the plug seals it), so that changes
/// the key and not how the flute speaks.
pub const LONG_TOTAL: f64 = 589.5;
pub struct Long {
    pub key: &'static str,
    pub notes: [&'static str; 5],
    pub bore_ref: f64,
    pub sac: f64,
    pub spacing: f64,
}

pub fn long_builds() -> Vec<Long> {
    vec![
        Long { key: "F4", notes: ["Ab4", "Bb4", "C5", "Eb5", "F5"], bore_ref: 22.23, sac: 110.0, spacing: 31.0 },
        Long { key: "E4", notes: ["G4", "A4", "B4", "D5", "E5"], bore_ref: 22.23, sac: 80.0, spacing: 31.0 },
    ]
}

impl Long {
    pub fn name(&self) -> String {
        format!("box-square-3-{}-590", self.key)
    }
    /// the square bore across, the round bore's area
    pub fn w(&self) -> f64 {
        (std::f64::consts::PI * py::powf(self.bore_ref / 2.0, 2.0)).sqrt()
    }
    pub fn chamber(&self) -> f64 {
        LONG_TOTAL - (self.sac + PLUG + m::WINDOW_L / 2.0) - m::FOOT_SPARE
    }
    pub fn design(&self) -> m::Design {
        let w = self.w();
        let model = m::Model { window_w: w, spacing: self.spacing, ..m::Model::default() };
        model.design_held(&m::Bore::new(Some((w, w))), T, self.chamber()).unwrap_or_else(|e| lasermade_tools::die(format!("ValueError: {e}")))
    }
}

/// A note's name and how far off it, from its frequency.
pub fn note_of(f: f64) -> (String, f64) {
    let x = 12.0 * py::log2(f / m::A4) + 57.0;
    let r = x.round();
    let names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    (format!("{}{}", names[(r as i64).rem_euclid(12) as usize], (r as i64).div_euclid(12)), (x - r) * 100.0)
}

// --- geometry ----------------------------------------------------------------

fn area2(poly: &[Pt]) -> f64 {
    let n = poly.len();
    let mut s = 0.0;
    for i in 0..n {
        let (a, b) = (poly[i], poly[(i + 1) % n]);
        s += (a[0] * b[1] - b[0] * a[1]).f();
    }
    s
}

/// A rectilinear polygon grown by d on every side (shrunk if d < 0).
///
/// Each vertex moves along the sum of its two edges' outward normals, which
/// for right angles is exactly a parallel offset of both edges, at a convex
/// corner and a concave one alike.
pub fn offset(poly: &[Pt], d: f64) -> Vec<(f64, f64)> {
    let s = if area2(poly) > 0.0 { I(1) } else { I(-1) };
    let n = poly.len();
    // outward for a polygon of sign s, in y-down coordinates
    let normal = |a: Pt, b: Pt| {
        let (dx, dy) = (b[0] - a[0], b[1] - a[1]);
        let l = py::hypot(dx.f(), dy.f());
        ((s * dy).f() / l, ((-s) * dx).f() / l)
    };
    (0..n)
        .map(|i| {
            let (p0, p1, p2) = (poly[(i + n - 1) % n], poly[i], poly[(i + 1) % n]);
            let (na, nb) = (normal(p0, p1), normal(p1, p2));
            (p1[0].f() + d * (na.0 + nb.0), p1[1].f() + d * (na.1 + nb.1))
        })
        .collect()
}

pub fn rectf(x0: f64, y0: f64, x1: f64, y1: f64) -> Vec<Pt> {
    rect(F(x0), F(y0), F(x1), F(y1))
}

/// A flute part: the shared Part, and what the flute adds to it.
#[derive(Clone, Debug)]
pub struct FPart {
    pub p: Part,
    pub fills: Vec<Vec<Pt>>, // fill-engraved rectangles
    pub images: Vec<(f64, f64, f64, f64)>, // ring.png at x, y, w, h
    pub ink: Option<&'static str>,
    pub notch: Option<(f64, f64, f64)>, // the cap's: cx, cy, r
    pub end_notch: Option<(f64, f64)>, // a bottom plate's: yc, r
}

impl FPart {
    pub fn new(name: &str, num: usize, outline: Vec<Pt>, note: &str) -> FPart {
        FPart { p: Part::new(name, num, outline, note), fills: vec![], images: vec![], ink: None, notch: None, end_notch: None }
    }
    pub fn hole(&mut self, cx: f64, cy: f64, d: f64) {
        self.p.cuts.push(Cut::Circle(cx, cy, d / 2.0));
    }
    pub fn slot(&mut self, x0: f64, y0: f64, x1: f64, y1: f64) {
        self.p.cuts.push(Cut::Poly(rectf(x0, y0, x1, y1)));
    }
}

/// The mouthpiece cap: a plate w across and h tall whose bottom edge, y = 0,
/// carries a half-round notch -- the original's circle, d across, centred
/// `inset` inside the edge. It is drawn as part of the outline: as a
/// separate circle it would run 4.5mm past the cap and cut the next part on
/// the sheet, which the 4mm gap between parts does not clear.
pub fn cap_part(num: usize, w: f64, h: f64, d: f64, inset: f64) -> FPart {
    let (cx, r) = (w / 2.0, d / 2.0);
    let a = (inset / r).asin();
    let mut o: Vec<Pt> = vec![[Z, Z]];
    for i in 0..33 {
        let t = std::f64::consts::PI + a - (std::f64::consts::PI + 2.0 * a) * i as f64 / 32.0;
        o.push([F(cx + r * py::mcos(t)), F(inset + r * py::msin(t))]);
    }
    o.extend([[F(w), Z], [F(w), F(h)], [Z, F(h)]]);
    let mut p = FPart::new("mouthpiece cap", num, o, "glued over the mouth end, the notched edge at the bottom");
    p.notch = Some((cx, inset, r));
    p
}

/// The cap's outline grown by the kerf: the rectangle out by e, the notch's
/// arc, which bounds material lying outside it, in by e.
pub fn cap_path(p: &FPart, dx: f64, dy: f64, e: f64) -> String {
    let (cx, cy, r) = p.notch.unwrap();
    let (w, h) = (p.p.w, p.p.h);
    let r2 = r - e;
    let hx = (r2 * r2 - py::powf(cy + e, 2.0)).sqrt();
    let x = |v: f64| format!("{:.3}", v + dx);
    let y = |v: f64| format!("{:.3}", v + dy);
    format!(
        "M {},{} L {},{} A {r2:.3} {r2:.3} 0 1 0 {},{} L {},{} L {},{} L {},{} Z",
        x(-e), y(-e), x(cx - hx), y(-e), x(cx + hx), y(-e), x(w + e), y(-e), x(w + e), y(h + e), x(-e), y(h + e)
    )
}

/// Give a bottom plate the half-round notch in its mouth end: the cap's
/// circle, CAP_D across, centred on the end edge midway across, so with the
/// cap's own notch, at right angles to it in the end face, it makes one
/// rounded opening at the bottom corner (the author, 2026-10-13). Kept off
/// the outline, which offset() can grow only while it is rectilinear; the
/// sheet writers and the 3D view put the arc in.
pub fn end_notch(mut p: FPart) -> FPart {
    p.end_notch = Some((p.p.h / 2.0, CAP_D / 2.0));
    p
}

/// The outline with the notch's arc in it, before the kerf: for the 3D view.
/// The outline closes along its mouth end, x = 0.
pub fn end_notch_outline(p: &FPart) -> Vec<Pt> {
    let n = 24;
    let (yc, r) = p.end_notch.unwrap();
    let o = &p.p.outline;
    assert!(o[0][0].f() == 0.0 && o[o.len() - 1][0].f() == 0.0, "the outline must close along x = 0");
    let mut out = o.clone();
    for i in 0..=n {
        let t = std::f64::consts::PI * i as f64 / n as f64;
        out.push([F(r * py::msin(t)), F(yc + r * py::mcos(t))]);
    }
    out
}

/// The outline grown by the kerf with the notch's arc, which bounds material
/// outside it, in by e: the circle about (0, yc) of radius r - e, met where
/// the grown end edge, x = -e, crosses it.
pub fn end_notch_path(p: &FPart, dx: f64, dy: f64, e: f64) -> String {
    let (yc, r) = p.end_notch.unwrap();
    let o = offset(&p.p.outline, e);
    let r2 = r - e;
    let h = (r2 * r2 - e * e).sqrt();
    let pts: Vec<String> = o.iter().map(|(x, y)| format!("{:.3},{:.3}", x + dx, y + dy)).collect();
    format!(
        "M {} L {:.3},{:.3} A {r2:.3} {r2:.3} 0 1 0 {:.3},{:.3} Z",
        pts.join(" L "), -e + dx, yc + h + dy, -e + dx, yc - h + dy
    )
}

/// A plate's outline from x0 to x1, PW wide, notched T deep along both long
/// edges wherever a side wall's finger comes in. The plate's own fingers are
/// the material left between.
fn notched(x1: f64, pw: f64, xs: &[f64]) -> Vec<Pt> {
    let xs: Vec<f64> = xs.iter().copied().filter(|&x| 0.0 < x && x < x1).collect();
    let h = FINGER / 2.0;
    let mut o: Vec<Pt> = vec![[Z, Z]];
    for &x in &xs {
        o.extend([[F(x - h), Z], [F(x - h), F(T)], [F(x + h), F(T)], [F(x + h), Z]]);
    }
    o.push([F(x1), Z]);
    o.push([F(x1), F(pw)]);
    for &x in xs.iter().rev() {
        o.extend([[F(x + h), F(pw)], [F(x + h), F(pw - T)], [F(x - h), F(pw - T)], [F(x - h), F(pw)]]);
    }
    o.push([Z, F(pw)]);
    o
}

/// The model's hole layout for a bore W x D with the holes in `wall`, the
/// window the bore's full width, as every build here has had since
/// 2026-10-13: the author's 2017 flute's window, on all of them.
pub fn design(w: f64, d: f64, wall: f64) -> m::Design {
    let model = m::Model { window_w: w, ..m::Model::default() };
    model.design(&m::Bore::new(Some((w, d))), wall, true).unwrap_or_else(|e| lasermade_tools::die(format!("ValueError: {e}")))
}

/// What build() says about the flute beside its parts.
#[derive(Clone, Debug)]
pub struct Info {
    pub total: f64,
    pub wc: f64,
    pub pw: f64,
    pub hx: Vec<f64>,
    pub fingers: Vec<f64>,
    pub exit: (f64, f64),
    pub win: (f64, f64),
    pub doubler: Option<(f64, f64)>,
}

/// Every part of one variant, in its own flat coordinates: x along the
/// flute from the mouth end, y across it.
pub fn build(kind: &str, w: f64, d: f64, wall: f64, l: f64, holes: &[f64], diams: &[f64], sac: f64) -> (Vec<FPart>, Info) {
    let wc = sac + PLUG + m::WINDOW_L / 2.0; // window centre
    let total = wc + l + m::FOOT_SPARE;
    let hx: Vec<f64> = holes.iter().map(|h| wc + h).collect(); // finger holes, foot-most first
    let (dz0, dz1) = (fmin(&hx) - DOUBLER_PAST, fmax(&hx) + DOUBLER_PAST);
    let boxy = kind == "box" || kind == "flat";
    let pw = if boxy { w + 2.0 * T } else { w + 2.0 * SIDE };
    let yc = pw / 2.0;
    let mut parts: Vec<FPart> = vec![];
    let mut num = 0usize;
    let mut next = || {
        num += 1;
        num
    };
    let mut top = FPart::new(
        "top plate", next(), rect(Z, Z, F(total), F(pw)),
        "exit hole, window and the five finger holes, and the nest's half of the flue fill-engraved over the plug; file the window's far edge to a 30 degree bevel before assembly",
    );
    // the exit hole and the window both run the bore's full width
    top.slot(sac - EXIT_L, yc - w / 2.0, sac, yc + w / 2.0);
    top.slot(sac + PLUG, yc - w / 2.0, sac + PLUG + m::WINDOW_L, yc + w / 2.0);
    // the nest's half of the flue, between the two: the plug's span
    top.fills.push(rectf(sac, yc - w / 2.0, sac + PLUG, yc + w / 2.0));
    top.ink = Some(NEST_INK);
    for (&x, &dd) in hx.iter().zip(diams) {
        top.hole(x, yc, dd);
        let r = dd * RING_OF;
        top.images.push((x - r / 2.0, yc - r / 2.0, r, r));
    }
    let mut xs: Vec<f64> = vec![];
    let mut rest: Vec<FPart> = vec![];
    if boxy {
        if kind == "box" {
            // both full-width openings reach the bore's inner face, the floor
            // of every finger notch, so no finger may stand beside either
            xs = fingers_x(total, &[(sac - EXIT_L, sac), (sac + PLUG, sac + PLUG + m::WINDOW_L)]);
            top.p.outline = notched(total, pw, &xs);
            rest.push(end_notch(FPart::new("bottom plate", next(), notched(total, pw, &xs), "a half-round notch in the mouth end")));
            for _ in 0..2 {
                let s = finger_side(total, d, &xs, next());
                rest.push(FPart { p: s, fills: vec![], images: vec![], ink: None, notch: None, end_notch: None });
            }
        } else {
            rest.push(end_notch(FPart::new("bottom plate", next(), rect(Z, Z, F(total), F(pw)), "a half-round notch in the mouth end")));
            for _ in 0..2 {
                rest.push(FPart::new("side wall", next(), rect(Z, Z, F(total), F(d)), "glued between the top and the bottom"));
            }
        }
        let n = (PLUG / T) as i64;
        for _ in 0..n {
            rest.push(FPart::new(
                "plug disc", next(), rect(Z, Z, F(w + INTERF_ACROSS), F(d + INTERF_ACROSS)),
                &format!("{n} press-fit into the bore between the exit hole and the window"),
            ));
        }
    } else {
        rest.push(end_notch(FPart::new("bottom layer", next(), rect(Z, Z, F(total), F(pw)), "a half-round notch in the mouth end")));
        let (s1, s2) = (F(SIDE), F(SIDE + w));
        let (t, sp, sa) = (F(total), F(sac + PLUG), F(sac));
        let bore = vec![[Z, Z], [t, Z], [t, s1], [sp, s1], [sp, s2], [t, s2], [t, F(pw)], [Z, F(pw)], [Z, s2], [sa, s2], [sa, s1], [Z, s1]];
        for _ in 0..py::round(d / T) {
            rest.push(FPart::new("bore layer", next(), bore.clone(), "the chamber and the bore cut out, the plug left solid"));
        }
    }
    if wall > T {
        let mut p = FPart::new("doubler", next(), rect(F(dz0), Z, F(dz1), F(pw)), "glued over the finger-hole run, holes in line");
        for (&x, &dd) in hx.iter().zip(diams) {
            p.hole(x, yc, dd);
        }
        // the finger meets the doubler, not the top, so the depressions move
        p.images = std::mem::take(&mut top.images);
        rest.push(p);
    }
    let b0 = sac - EXIT_L - BIRD_UPSTREAM;
    for k in 0..BIRD_LAYERS {
        let mut p = FPart::new(
            "bird layer", next(), rect(F(b0), Z, F(sac + PLUG), F(pw)),
            if k == 0 { "the bird's half of the flue fill-engraved in its underside" } else { "glued on the one below" },
        );
        if k == 0 {
            // from the exit hole's upstream edge to the window
            p.fills.push(rectf(sac - EXIT_L, yc - w / 2.0, sac + PLUG, yc + w / 2.0));
            p.ink = Some(BIRD_INK);
        }
        rest.push(p);
    }
    // last, so every part number the variants had before it is unchanged
    rest.push(cap_part(next(), pw, d + 2.0 * T, CAP_D, NOTCH_IN));
    parts.push(top);
    parts.extend(rest);
    let info = Info {
        total, wc, pw, hx,
        fingers: if kind == "box" { xs } else { vec![] },
        exit: (sac - EXIT_L, sac),
        win: (sac + PLUG, sac + PLUG + m::WINDOW_L),
        doubler: if wall > T { Some((dz0, dz1)) } else { None },
    };
    (parts, info)
}

// --- checks -----------------------------------------------------------------

#[allow(clippy::too_many_arguments)]
pub fn checks(kind: &str, w: f64, d: f64, parts: &[FPart], info: &Info, holes: &[f64], diams: &[f64], cents: &[f64], sheets: &[Sheet]) -> Vec<(bool, String, String)> {
    let mut out = vec![];
    let mut note = |ok: bool, what: &str, detail: String| out.push((ok, what.to_string(), detail));
    let worst = cents.iter().fold(cents[0].abs(), |a, c| py::max(a, c.abs()));
    note(worst < 1.0, "the model hits all six notes", format!("worst {worst:.2} cents"));
    note(info.total + 2.0 * MARGIN <= BED.0, "the longest part fits the bed", format!("{:.1}mm against {}", info.total, py::g(BED.0 - 2.0 * MARGIN)));
    let dmax = fmax(diams);
    note(dmax <= w - 2.0 * MIN_WEB, "every finger hole opens inside the bore", format!("largest {dmax:.2}mm in a {w:.2}mm bore"));
    let gaps: Vec<f64> = (0..4).map(|i| holes[i] - holes[i + 1] - (diams[i] + diams[i + 1]) / 2.0).collect();
    note(fmin(&gaps) >= 3.0, "ply left between neighbouring holes", format!("narrowest {:.1}mm", fmin(&gaps)));
    if kind == "box" {
        let hole_edge = info.pw / 2.0 - dmax / 2.0;
        note(hole_edge - T >= MIN_WEB, "ply between a finger hole and a finger notch", format!("{:.2}mm against {}", hole_edge - T, py::g(MIN_WEB)));
        let sides: Vec<&FPart> = parts.iter().filter(|p| p.p.name == "side wall").collect();
        let y0 = fmin(&sides.iter().map(|p| p.p.y0).collect::<Vec<_>>());
        let y1 = fmax(&sides.iter().map(|p| p.p.y0 + p.p.h).collect::<Vec<_>>());
        note(y0 == -T && y1 == d + T, "the fingers run to the outside faces", format!("{}mm proud each way, nothing outboard of them", py::g(T)));
    }
    let bots: Vec<&FPart> = parts.iter().filter(|p| p.end_notch.is_some()).collect();
    let (_, rn) = bots.first().map_or((0.0, 99.0), |p| p.end_notch.unwrap());
    note(bots.len() == 1 && rn <= w / 2.0 - 1.0, "the bottom's end notch opens into the bore, clear of its walls", format!("{:.2}mm across in a {w:.2}mm bore", 2.0 * rn));
    let rings: Vec<f64> = diams.iter().map(|d| d * RING_OF).collect();
    let gaps: Vec<f64> = (0..4).map(|i| holes[i] - holes[i + 1] - (rings[i] + rings[i + 1]) / 2.0).collect();
    note(fmin(&gaps) >= 0.0, "the depressions do not run into each other", format!("closest {:.1}mm apart", fmin(&gaps)));
    let edge = if kind == "box" || kind == "flat" { T } else { 1.0 };
    let rmax = fmax(&rings);
    note(rmax / 2.0 <= info.pw / 2.0 - edge, "each depression clears the plate's edge joints", format!("{:.1}mm to spare", info.pw / 2.0 - edge - rmax / 2.0));
    let tf = &parts.iter().find(|p| p.p.name.starts_with("top")).unwrap().fills;
    let bf: Vec<&Vec<Vec<Pt>>> = parts.iter().filter(|p| p.p.name == "bird layer" && !p.fills.is_empty()).map(|p| &p.fills).collect();
    let (ok, x0, x1) = if !tf.is_empty() && bf.len() == 1 {
        let x0 = py::max(tf[0][0][0].f(), bf[0][0][0][0].f());
        let x1 = py::min(tf[0][1][0].f(), bf[0][0][1][0].f());
        (x1 - x0 >= info.win.0 - info.exit.1 - 0.01 && tf[0][0][1].f() == bf[0][0][0][1].f(), x0, x1)
    } else {
        (false, 0.0, 0.0)
    };
    note(ok, "both halves of the flue cover the plug, in line", format!("{:.1}mm in common, nest and bird", x1 - x0));
    if kind == "box" {
        let mut near: Option<f64> = None;
        for &x in &info.fingers {
            for (a, b) in [info.exit, info.win] {
                let v = py::min((x - a).abs(), (x - b).abs()) - FINGER / 2.0;
                near = Some(near.map_or(v, |n| py::min(n, v)));
            }
        }
        let near = near.unwrap_or(99.0);
        note(near >= FINGER_CLEAR, "no finger notch beside a full-width opening", format!("{} fingers a side, nearest {near:.1}mm from one", info.fingers.len()));
    }
    let tops: Vec<&FPart> = parts.iter().filter(|p| p.p.name.starts_with("top")).collect();
    note(tops.len() == 1 && tops[0].p.w == info.total, "the top is one piece", format!("{} plate, {:.1}mm long", tops.len(), tops[0].p.w));
    if let Some((z0, z1)) = info.doubler {
        let clear = z0 - info.win.1;
        note(clear >= 10.0 && z1 <= info.total, "the doubler stays clear of the window", format!("{clear:.0}mm past it, {z0:.1} to {z1:.1}mm"));
    }
    note(
        sheets.iter().all(|s| s.w <= BED.0 && s.h <= BED.1),
        "every sheet fits the bed",
        format!("{} sheet(s), largest {:.0} x {:.0}mm", sheets.len(), fmax(&sheets.iter().map(|s| s.w).collect::<Vec<_>>()), fmax(&sheets.iter().map(|s| s.h).collect::<Vec<_>>())),
    );
    let cap = parts.iter().find(|p| p.p.name == "mouthpiece cap").unwrap();
    let (_, cy, r) = cap.notch.unwrap();
    let into = cy + r - T - (cap.p.h - (d + 2.0 * T)) / 2.0;
    note(into > 0.0, "the cap's notch opens into the bore", format!("{:.2}mm deep, {into:.2}mm past the bottom wall", cy + r));
    let placed: usize = sheets.iter().map(|s| s.parts.len()).sum();
    note(placed == parts.len(), "every part is on a sheet", format!("{placed} of {}", parts.len()));
    out
}

// --- sheets ------------------------------------------------------------------

/// pack() for flute parts: the shared shelf packer, on each part's size.
pub fn pack_parts(parts: &[FPart]) -> Vec<Sheet> {
    pack(&parts.iter().map(|p| (p.p.w, p.p.h)).collect::<Vec<_>>())
}

pub fn ring_data() -> String {
    let b = std::fs::read(format!("{}/yours/original/ring.png", here())).unwrap_or_else(|e| lasermade_tools::die(format!("ring.png: {e}")));
    format!("data:image/png;base64,{}", py::b64(&b))
}

fn mv(pts: &[(f64, f64)], dx: f64, dy: f64) -> Vec<(f64, f64)> {
    pts.iter().map(|(x, y)| (x + dx, y + dy)).collect()
}

/// path() of points given as Nums
pub fn path_of(pts: &[Pt], dx: f64, dy: f64) -> String {
    rb_path(&pts.iter().map(|q| (q[0].f() + dx, q[1].f() + dy)).collect::<Vec<_>>(), true)
}

/// The outline, the inner cuts and the fills of one placed part, as the
/// sheet writers draw them: (black, orange, fills by ink).
pub fn drawn(p: &FPart, dx: f64, dy: f64) -> (String, Vec<String>, Vec<String>) {
    let k = kerf();
    let black = if p.notch.is_some() {
        cap_path(p, dx, dy, k / 2.0)
    } else if p.end_notch.is_some() {
        end_notch_path(p, dx, dy, k / 2.0)
    } else {
        rb_path(&mv(&offset(&p.p.outline, k / 2.0), dx, dy), true)
    };
    let orange = p
        .p
        .cuts
        .iter()
        .map(|c| match c {
            Cut::Poly(q) => rb_path(&mv(&offset(q, -k / 2.0), dx, dy), true),
            Cut::Circle(cx, cy, r) => format!("<circle cx=\"{:.3}\" cy=\"{:.3}\" r=\"{:.3}\"/>", cx + dx, cy + dy, r - k / 2.0),
        })
        .collect();
    let fills = p.fills.iter().map(|f| path_of(f, dx, dy)).collect();
    (black, orange, fills)
}

/// A group of strokes: a path for each d, an element as it is.
pub fn group(col: &str, items: &[String]) -> String {
    let mut s = format!("  <g fill=\"none\" stroke=\"{col}\" stroke-width=\"0.2\">\n");
    for i in items {
        if i.starts_with('<') {
            s += &format!("    {i}\n");
        } else {
            s += &format!("    <path d=\"{i}\"/>\n");
        }
    }
    s + "  </g>\n"
}

pub fn svg_sheet(key: &str, variant: &str, k: usize, n: usize, s: &Sheet, parts: &[FPart], what: &str) -> String {
    let kf = kerf();
    let (mut orange, mut black, mut imgs) = (vec![], vec![], vec![]);
    let mut fills: Vec<(&str, Vec<String>)> = vec![(BIRD_INK, vec![]), (NEST_INK, vec![])];
    let ring = ring_data();
    for &(i, sx, sy) in &s.parts {
        let p = &parts[i];
        let (dx, dy) = (sx - p.p.x0 + kf / 2.0, sy - p.p.y0 + kf / 2.0);
        let (b, o, f) = drawn(p, dx, dy);
        black.push(b);
        orange.extend(o);
        if !f.is_empty() {
            fills.iter_mut().find(|e| Some(e.0) == p.ink).unwrap().1.extend(f);
        }
        for &(x, y, w, h) in &p.images {
            imgs.push(format!("<image x=\"{:.3}\" y=\"{:.3}\" width=\"{w:.3}\" height=\"{h:.3}\" preserveAspectRatio=\"none\" href=\"{ring}\"/>", x + dx, y + dy));
        }
    }
    let desc = format!(
        "1 user unit = 1mm. Square-bore flute in {key}, {variant}, sheet {k} of {n}: {what}. 3mm ply, drawn for a {}mm kerf. Finger joints as the trumpet bores cut them: {}mm fingers and spaces, no play, the fit from the kerf. Engraves first. The flue is a fill engrave in two inks, run either or both: red {BIRD_INK} in the bird's underside, magenta {NEST_INK} in the top over the plug; one alone about 1mm deep, both about 0.5mm each. Blue {BLUE} engraves the depression round each finger hole, a greyscale image engrave, Grayscale mode in xTool Creative Space. Set every depth on scrap first. Then the cuts: orange {ORANGE} cuts the holes and slots, and black {BLACK} frees the parts.",
        py::g(kf), py::g(FINGER)
    );
    let mut out = format!(
        "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{w:.2}mm\" height=\"{h:.2}mm\" viewBox=\"0 0 {w:.2} {h:.2}\">\n<title>Square-bore flute in {key}, {variant}, sheet {k} of {n}</title>\n<desc>{desc}</desc>\n",
        w = s.w, h = s.h
    );
    if !imgs.is_empty() {
        out += "  <g id=\"images\">\n";
        for i in &imgs {
            out += &format!("    {i}\n");
        }
        out += "  </g>\n";
    }
    for (ink, ds) in &fills {
        if !ds.is_empty() {
            out += &format!("  <g fill=\"{ink}\" stroke=\"none\">\n");
            for d in ds {
                out += &format!("    <path d=\"{d}\"/>\n");
            }
            out += "  </g>\n";
        }
    }
    out + &group(ORANGE, &orange) + &group(BLACK, &black) + "</svg>\n"
}

/// Each build's design, once per bore and wall, as the Python cached it.
pub fn designs() -> Vec<(&'static str, &'static str, f64, f64, f64, m::Design)> {
    let mut cache: Vec<((u64, u64, u64), m::Design)> = vec![];
    let mut out = vec![];
    for (name, kind, w, d, wall) in variants() {
        let key = (py::round_dp(w, 4).to_bits(), py::round_dp(d, 4).to_bits(), wall.to_bits());
        if !cache.iter().any(|c| c.0 == key) {
            cache.push((key, design(w, d, wall)));
        }
        let ds = cache.iter().find(|c| c.0 == key).unwrap().1.clone();
        out.push((name, kind, w, d, wall, ds));
    }
    out
}

pub fn main() -> i32 {
    let (mut out, mut only, mut write, mut flat): (Option<String>, Option<String>, bool, bool) = (None, None, true, false);
    let mut scdir: Option<String> = None;
    let longs: Vec<String> = long_builds().iter().map(|l| l.name()).collect();
    let names: Vec<&str> = variants().iter().map(|v| v.0).chain(longs.iter().map(|s| s.as_str())).collect();
    for x in std::env::args().skip(1) {
        if x == "--no-write" {
            write = false;
        } else if x == "--flat" {
            flat = true;
        } else if let Some(v) = x.strip_prefix("--out=") {
            out = Some(v.to_string());
        } else if let Some(v) = x.strip_prefix("--only=") {
            if !names.contains(&v) {
                lasermade_tools::die(format!("error: {v} is not a variant. They are {}.", names.join(", ")));
            }
            only = Some(v.to_string());
        } else if x.starts_with("--kerf=") {
            set_kerf(&x);
        } else if let Some(v) = x.strip_prefix("--solidcraft=") {
            scdir = Some(v.to_string());
        } else {
            lasermade_tools::die(format!("error: {x} is not a flag this generator reads. It takes --out=, --only=, --kerf=, --solidcraft=, --flat and --no-write."));
        }
    }
    if write && out.is_none() {
        lasermade_tools::die("error: --out=DIR, or --no-write to run the checks only.");
    }
    let mut bad = 0;
    let mut cache: Vec<((u64, u64, u64), m::Design)> = vec![];
    // (name, kind, bore across, deep, wall, slow air chamber, key, the file names' stem, the design's head)
    let mut jobs: Vec<(String, &str, f64, f64, f64, f64, String, String, solidcraft::Head)> = vec![];
    for (name, kind, w, d, wall) in variants() {
        jobs.push((name.to_string(), kind, w, d, wall, SAC, "A4".to_string(), format!("square-flute-A4-{name}"), solidcraft::Head::a4()));
    }
    for lb in long_builds() {
        let stem = format!("square-flute-{}-box-square-3-590", lb.key);
        jobs.push((lb.name(), "box", lb.w(), lb.w(), T, lb.sac, lb.key.to_string(), stem, solidcraft::Head::long(&lb)));
    }
    for (name, kind, w, d, wall, sac, key, stem, mut head) in jobs {
        let name = name.as_str();
        if only.as_deref().is_some_and(|o| o != name) {
            continue;
        }
        let ds = if let Some(lb) = long_builds().into_iter().find(|l| l.name() == name) {
            let ds = lb.design();
            let (nn, c) = note_of(ds.key);
            if nn != lb.key {
                lasermade_tools::die(format!("error: {name} sounds {nn} ({:.2}Hz), not {}", ds.key, lb.key));
            }
            head.chamber_comment = format!(
                "the sound chamber, window centre to the foot: held so the flute is {} mm overall, the bed's length less its margins and a kerf; naf_model's design_held() puts this bore and hole wall in {nn} ({:.2} Hz, {c:+.0} cents) at it",
                py::g(LONG_TOTAL), ds.key
            );
            ds
        } else {
            let key = (py::round_dp(w, 4).to_bits(), py::round_dp(d, 4).to_bits(), wall.to_bits());
            if !cache.iter().any(|c| c.0 == key) {
                cache.push((key, design(w, d, wall)));
            }
            cache.iter().find(|c| c.0 == key).unwrap().1.clone()
        };
        let (parts, info) = build(kind, w, d, wall, ds.l, &ds.holes, &ds.diams, sac);
        let sheets = pack_parts(&parts);
        if let Some(dir) = &scdir {
            // the parametric design: written whatever the checks say, as the
            // design carries its own room readouts
            std::fs::create_dir_all(dir).unwrap_or_else(|e| lasermade_tools::die(format!("{dir}: {e}")));
            let f = format!("{}/square-flute-{name}.solidcraft.json", dir.trim_end_matches('/'));
            std::fs::write(&f, solidcraft::script(kind, wall, &ds, &head)).unwrap_or_else(|e| lasermade_tools::die(format!("{f}: {e}")));
        }
        println!("\n{name}: {kind}, bore {w:.2} x {d:.2}mm, {}mm hole wall", py::g(wall));
        if key != "A4" {
            let (nn, c) = note_of(ds.key);
            println!("  in {nn} {c:+.1} cents ({:.2}Hz) closed, a {}mm slow air chamber, hands {}mm apart", ds.key, py::g(sac), py::g(long_builds().iter().find(|l| l.name() == name).unwrap().spacing));
        }
        println!(
            "  sound chamber {:.1}mm from the window centre, cut {:.1}; flute {:.1}mm long, {:.2}mm wide",
            ds.l, ds.l + m::FOOT_SPARE, info.total, info.pw
        );
        println!(
            "  holes from the window: {}",
            ds.holes.iter().zip(&ds.diams).map(|(h, dd)| format!("{h:.1}/ø{dd:.1}")).collect::<Vec<_>>().join(", ")
        );
        for (ok, what, detail) in checks(kind, w, d, &parts, &info, &ds.holes, &ds.diams, &ds.cents, &sheets) {
            println!("  {}  {what:46} {detail}", if ok { "pass" } else { "FAIL" });
            bad += !ok as usize;
        }
        if write && bad == 0 {
            let o = out.as_deref().unwrap();
            let dir = if flat { o.to_string() } else { format!("{}/{name}", o.trim_end_matches('/')) };
            std::fs::create_dir_all(&dir).unwrap_or_else(|e| lasermade_tools::die(format!("{dir}: {e}")));
            for (k, s) in sheets.iter().enumerate() {
                let mut ns: Vec<&str> = s.parts.iter().map(|&(i, _, _)| parts[i].p.name.as_str()).collect();
                ns.sort();
                ns.dedup();
                let fname = format!("{stem}-sheet{}-cut-files.svg", k + 1);
                let f = format!("{}/{fname}", dir.trim_end_matches('/'));
                std::fs::write(&f, svg_sheet(&key, name, k + 1, sheets.len(), s, &parts, &ns.join(", "))).unwrap_or_else(|e| lasermade_tools::die(format!("{f}: {e}")));
                println!("  wrote {fname}  {:.0} x {:.0}mm, {} parts", s.w, s.h, s.parts.len());
            }
        }
    }
    if bad > 0 {
        println!("\n  {bad} check(s) failed. Nothing written.");
        return 1;
    }
    0
}
