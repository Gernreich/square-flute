//! What the panpipes and the chanters borrow from square_flute.py, in Rust:
//! the ply, the kerf, the finger joint, the bed and the inks, a part and the
//! shelf packing. square_flute.py keeps its own copy for the flutes; the two
//! give the same numbers, which the borrowers' .repro gates prove.
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

/// naf_model.py's speed of sound, m/s: air at T_C, warm from the breath.
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
