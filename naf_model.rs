//! A five-hole minor-pentatonic flute in the Native American style, as a
//! transmission-matrix model: where the foot and the five finger holes go for
//! a given bore section and hole-wall thickness.
//!
//!     target/release/naf_model --bores        # the designs, for bore-tmm
//!     target/release/naf_model                 # every variant, side by side
//!     target/release/naf_model --hole=7.5      # another finger-hole diameter
//!     target/release/naf_model --mouth=1.0     # scale the window's end correction
//!
//! The reference is a round-bore flute in A4: 3/4in (19.05mm) bore, A4 =
//! 440Hz with every hole closed, and the minor pentatonic above it -- C5, D5,
//! E5, G5 and A5 as the holes open from the foot up. Each variant keeps that
//! bore's AREA, 285mm^2, in a section the plywood can build. 3/4in is the
//! bore Flutopedia's bore table gives for A4.
//!
//! The model, from the foot up:
//!
//!   * the bore is a lossy tube. Its wave impedance comes from its area; its
//!     viscothermal loss from its hydraulic radius 2A/P, which is what a
//!     square or a rectangle changes even at the same area (the square's is
//!     8.44mm against the round bore's 9.53, so it loses a little more);
//!   * the foot radiates as an unflanged open end of the same area;
//!   * each finger hole is Keefe's (1990) tone hole -- a shunt and two series
//!     halves -- open or closed. Its chimney is the WALL THICKNESS, 3 or 6mm,
//!     and nothing else, because a flat plate has no curvature for the hole
//!     to cut through. That is the one place the variants differ most;
//!   * at the top, the true sound hole (the window) opens into the bore with
//!     a short closed stub above it to the plug. The jet drives the window,
//!     so the flute sounds where the reactance of the window and the bore in
//!     series passes through zero.
//!
//! The arithmetic of that reactance and its search is bore-tmm's jet kernel
//! (bore-tmm/src/models.rs), which gives the bits this model's Python gave;
//! this file builds what it is handed. Rust since 2026-11-07: the move
//! changed no byte of any cut file or page.
//!
//! THE WINDOW IS THE UNCALIBRATED PART. Its end correction is physics-based
//! but not measured, and it moves the foot by more than any other term: each
//! 1mm of window correction is about 3.7mm of sound chamber at the 10mm
//! window, 2.3mm at a full-width one. So the foot is cut LONG (FOOT_SPARE)
//! and trimmed to pitch, and --mouth= is the knob to set once a real flute
//! has been measured. The holes move with it ALMOST AS FAR -- a 10% error
//! moves the foot 2.3 to 2.9mm and the holes 2.1 to 2.7mm -- so trimming the
//! foot does not put them right: each is tuned. (This said 5.5mm and "the
//! holes depend on it far less" until 2026-10-13, from an area ratio never
//! run through the model. Both were wrong.)
use bore_tmm::models::{scan, Jet};
use lasermade_tools::py;
use std::f64::consts::PI;

// --- air, warm from the breath ----------------------------------------------
pub const T_C: f64 = 25.0;
pub fn c() -> f64 {
    331.3 * (1.0 + T_C / 273.15).sqrt() // 346.1 m/s
}
pub const RHO: f64 = 1.184;

// --- the tune ----------------------------------------------------------------
pub const A4: f64 = 440.0;
pub const NOTES: [&str; 6] = ["A4", "C5", "D5", "E5", "G5", "A5"];
pub const SEMIS: [i32; 6] = [0, 3, 5, 7, 10, 12];
pub fn targets() -> [f64; 6] {
    SEMIS.map(|s| A4 * py::powf(2.0, s as f64 / 12.0))
}

// --- the head, the same for every variant (mm) ------------------------------
pub const WINDOW_W: f64 = 10.0; // true sound hole: across
pub const WINDOW_L: f64 = 7.0; // and along the bore
pub const WINDOW_T: f64 = 3.0; // it is always in a single 3mm plate
pub const FOOT_SPARE: f64 = 15.0; // cut this much long, trim to pitch
pub const ANCHOR_D: f64 = 8.0; // holes 2 and 4, whose positions are solved
pub const D_MIN: f64 = 4.0; // what a finger and the bore allow
pub const D_MAX: f64 = 11.0;

pub const REF_BORE: f64 = 19.05; // 3/4in
pub fn area() -> f64 {
    PI * py::powf(REF_BORE / 2.0, 2.0)
}

/// What the Python kept as module globals, and changed for a while: the
/// window's size, the mouth scale, the equal hole and the hand spacing.
#[derive(Clone, Copy, Debug)]
pub struct Model {
    pub window_w: f64,
    pub window_l: f64,
    pub mouth: f64,
    pub hole_d: f64,
    pub spacing: f64,
}

impl Default for Model {
    fn default() -> Model {
        Model { window_w: WINDOW_W, window_l: WINDOW_L, mouth: 1.0, hole_d: 8.0, spacing: 25.0 }
    }
}

/// A section: its area, its equivalent radius and its loss radius (m).
#[derive(Clone, Copy, Debug)]
pub struct Bore {
    pub area: f64,
    pub rh: f64,
    pub a: f64,
}

impl Bore {
    /// Bore(wide, deep), mm; None is the round reference.
    pub fn new(wd: Option<(f64, f64)>) -> Bore {
        let (area, rh) = match wd {
            None => {
                let r = REF_BORE / 2000.0;
                (PI * r * r, r)
            }
            Some((wide, deep)) => {
                let (w, d) = (wide / 1000.0, deep / 1000.0);
                (w * d, 2.0 * w * d / (2.0 * (w + d)))
            }
        };
        Bore { area, rh, a: (area / PI).sqrt() }
    }
}

impl Model {
    /// The true sound hole as a neck: its area (m^2), equivalent radius and
    /// effective length (m). Its correction is a rectangle's equivalent
    /// radius, flanged both sides (0.82 a each), scaled by the mouth.
    pub fn window_neck(&self) -> (f64, f64, f64) {
        let aw_ = self.window_w * self.window_l / 1e6;
        let aw = (aw_ / PI).sqrt();
        (aw_, aw, WINDOW_T / 1000.0 + self.mouth * 2.0 * 0.82 * aw)
    }

    /// The playing frequency nearest `near`: a zero crossing of the
    /// reactance, rising through zero, found by scanning then bisecting.
    /// L mm from the window centre to the foot, holes from the window,
    /// foot-most first, the lowest n_open of them open.
    pub fn sounding(&self, b: &Bore, l: f64, holes: &[f64], n_open: usize, wall: f64, near: f64, diams: &[f64]) -> Result<f64, String> {
        // the chain from the foot to the window, then walked from the window
        let mut chain: Vec<(u8, f64, f64, u8)> = vec![];
        let mut pos = l;
        for (i, &x) in holes.iter().enumerate() {
            chain.push((0, (pos - x) / 1000.0, 0.0, 0));
            chain.push((1, 0.0, diams[i] / 2000.0, (i < n_open) as u8));
            pos = x;
        }
        chain.push((0, pos / 1000.0, 0.0, 0));
        chain.reverse();
        let kind: Vec<u8> = chain.iter().map(|c| c.0).collect();
        let len: Vec<f64> = chain.iter().map(|c| c.1).collect();
        let r: Vec<f64> = chain.iter().map(|c| c.2).collect();
        let op: Vec<u8> = chain.iter().map(|c| c.3).collect();
        let (neck_area, neck_a, leff) = self.window_neck();
        let jet = Jet {
            c: c(), rho: RHO, rh: b.rh, area: b.area, a: b.a,
            kind: &kind, len: &len, r: &r, open: &op, t: wall,
            stub: self.window_l / 2000.0, neck_area, neck_a, leff,
        };
        let root = scan(near, 1.4, 80, 40, |x| jet.y(x));
        if root.is_nan() {
            return Err(format!("no resonance within 40% of {near:.1}Hz"));
        }
        Ok(root)
    }

    /// Sound-chamber length, five hole positions and five diameters, all
    /// positions from the window centre and foot-most first, iterated until
    /// each closed hole's effect on the others settles.
    ///
    /// Equal holes (even=false): every hole hole_d, positions solved.
    ///
    /// Laid out for the hands (even=true): the lower hand covers holes 1-3
    /// and the upper hand 4-5, each hand's holes `spacing` apart. Holes 2
    /// and 4 are ANCHOR_D and their positions are solved, which settles where
    /// each hand sits; holes 1, 3 and 5 stand `spacing` from their anchor and
    /// their DIAMETERS are solved. The lower hand is anchored on its MIDDLE
    /// hole: its natural gaps are 27 and 30mm, and anchored on hole 1 the
    /// third hole had to be bigger than the bore allows to reach E5. The gap
    /// between the hands is whatever the scale makes it. Spacing all five
    /// evenly cannot work: the natural gaps run about 27, 30, 46 and 12mm,
    /// because a minor third and a whole tone are not the same distance apart.
    pub fn design(&self, b: &Bore, wall: f64, even: bool) -> Result<Design, String> {
        let tg = targets();
        // a start near where these flutes land, as fractions of the chamber;
        // the solver keeps the holes in order, so a start that is far off can
        // trap a hole between two neighbours that cannot reach its note
        const FRAC: [f64; 5] = [0.69, 0.61, 0.52, 0.37, 0.33];
        let mut l = 330.0;
        let mut holes: Vec<f64> = FRAC.iter().map(|r| l * r).collect();
        let mut diams = vec![if even { ANCHOR_D } else { self.hole_d }; 5];
        for it in 0..6 {
            l = bisect(|x| self.sounding(b, x, &holes, 0, wall, A4, &diams), A4, 250.0, 420.0, false)?;
            if it == 0 {
                // the start again, at the chamber's real length: left at
                // 330mm, a 3/4in bore's 357mm chamber had hole 1 so high that
                // it shrank to 4.3mm to reach C5, and hole 2 could not get
                // below it
                holes = FRAC.iter().map(|r| l * r).collect();
                l = bisect(|x| self.sounding(b, x, &holes, 0, wall, A4, &diams), A4, 250.0, 420.0, false)?;
            }
            for n in 1..6 {
                let i = n - 1;
                if !even || n == 2 || n == 4 {
                    // only ORDER is enforced here; whether a finger fits
                    // between two holes is reported, not imposed, or a poor
                    // start traps a hole short of its note. When a hole
                    // cannot reach its note the fence above it is moved back,
                    // 20mm at a time, to 30mm from the window (at --mouth=0.8
                    // hole 5 was fenced out of its note). Not straight to 30:
                    // that far up the scan meets another resonance and hole 1
                    // failed instead. At the default window the first try
                    // always lands, so nothing shipped moves.
                    let mut lo = if n < 5 { holes[i + 1] + 0.5 } else { 30.0 };
                    let hi = if n > 1 { holes[i - 1] - 0.5 } else { l - 15.0 };
                    loop {
                        let f_pos = |x: f64| {
                            let mut hs = holes.clone();
                            hs[i] = x;
                            self.sounding(b, l, &hs, n, wall, tg[n], &diams)
                        };
                        match bisect(f_pos, tg[n], lo, hi, false) {
                            Ok(x) => {
                                holes[i] = x;
                                break;
                            }
                            Err(e) => {
                                if lo <= 30.0 {
                                    return Err(e);
                                }
                                lo = py::max(30.0, lo - 20.0);
                            }
                        }
                    }
                    if even && n == 2 {
                        holes[0] = holes[1] + self.spacing;
                        holes[2] = holes[1] - self.spacing;
                    }
                    if even && n == 4 {
                        holes[4] = holes[3] - self.spacing;
                    }
                } else {
                    let f_dia = |d: f64| {
                        let mut ds = diams.clone();
                        ds[i] = d;
                        self.sounding(b, l, &holes, n, wall, tg[n], &ds)
                    };
                    diams[i] = bisect(f_dia, tg[n], D_MIN, D_MAX, true)?;
                }
            }
        }
        let mut cents = vec![];
        for n in 0..6 {
            cents.push(1200.0 * py::log2(self.sounding(b, l, &holes, n, wall, tg[n], &diams)? / tg[n]));
        }
        Ok(Design { l, holes, diams, cents, key: A4 })
    }

    /// design() the other way round (2026-11-08): the sound chamber held at
    /// `l` mm, and the flute in whatever key that length sounds. The closed
    /// note is found first, the five holes are laid out for the minor
    /// pentatonic on it as design() lays them out for A4 (holes 2 and 4
    /// ANCHOR_D and placed, 1, 3 and 5 `spacing` from them and sized), and
    /// the two are iterated until neither moves. For a build the bed's length
    /// sets, not a note.
    pub fn design_held(&self, b: &Bore, wall: f64, l: f64) -> Result<Design, String> {
        const FRAC: [f64; 5] = [0.69, 0.61, 0.52, 0.37, 0.33];
        let mut holes: Vec<f64> = FRAC.iter().map(|r| l * r).collect();
        let mut diams = vec![ANCHOR_D; 5];
        let mut key = 0.0;
        let pent = |k: f64| -> Vec<f64> { SEMIS.iter().map(|s| k * py::powf(2.0, *s as f64 / 12.0)).collect() };
        for _ in 0..8 {
            key = self.sounding(b, l, &holes, 0, wall, 380.0, &diams)?;
            let tg = pent(key);
            for n in 1..6 {
                let i = n - 1;
                if n == 2 || n == 4 {
                    let mut lo = if n < 5 { holes[i + 1] + 0.5 } else { 30.0 };
                    let hi = if n > 1 { holes[i - 1] - 0.5 } else { l - 15.0 };
                    loop {
                        let f_pos = |x: f64| {
                            let mut hs = holes.clone();
                            hs[i] = x;
                            self.sounding(b, l, &hs, n, wall, tg[n], &diams)
                        };
                        match bisect(f_pos, tg[n], lo, hi, false) {
                            Ok(x) => {
                                holes[i] = x;
                                break;
                            }
                            Err(e) => {
                                if lo <= 30.0 {
                                    return Err(e);
                                }
                                lo = py::max(30.0, lo - 20.0);
                            }
                        }
                    }
                    if n == 2 {
                        holes[0] = holes[1] + self.spacing;
                        holes[2] = holes[1] - self.spacing;
                    }
                    if n == 4 {
                        holes[4] = holes[3] - self.spacing;
                    }
                } else {
                    let f_dia = |d: f64| {
                        let mut ds = diams.clone();
                        ds[i] = d;
                        self.sounding(b, l, &holes, n, wall, tg[n], &ds)
                    };
                    diams[i] = bisect(f_dia, tg[n], D_MIN, D_MAX, true)?;
                }
            }
        }
        let tg = pent(key);
        let mut cents = vec![];
        for n in 0..6 {
            cents.push(1200.0 * py::log2(self.sounding(b, l, &holes, n, wall, tg[n], &diams)? / tg[n]));
        }
        Ok(Design { l, holes, diams, cents, key })
    }
}

/// What design() returns: the sound chamber, the holes and their diameters
/// (foot-most first), and each note's error in cents.
#[derive(Clone, Debug)]
pub struct Design {
    pub l: f64,
    pub holes: Vec<f64>,
    pub diams: Vec<f64>,
    pub cents: Vec<f64>,
    /// the closed note, Hz: A4 for design(), what the length gives for design_held()
    pub key: f64,
}

/// x in [lo, hi] with fn(x) == target. fn falls as x grows, unless rising.
/// An error when the target is outside what the interval can reach, rather
/// than an endpoint as if it were an answer.
pub fn bisect(func: impl Fn(f64) -> Result<f64, String>, target: f64, lo: f64, hi: f64, rising: bool) -> Result<f64, String> {
    let (mut lo, mut hi) = (lo, hi);
    let (mut flo, mut fhi) = (func(lo)?, func(hi)?);
    let mut target = target;
    if rising {
        flo = -flo;
        fhi = -fhi;
        target = -target;
    }
    if !(fhi <= target && target <= flo) {
        return Err(format!("out of reach between {lo:.1} and {hi:.1}"));
    }
    for _ in 0..40 {
        let mid = (lo + hi) / 2.0;
        let g = func(mid)?;
        let g = if rising { -g } else { g };
        if g > target {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    Ok((lo + hi) / 2.0)
}

/// The command line: every variant, side by side, for equal holes and for
/// holes laid out for the hands.
/// The flutes as bore-tmm reads them, one JSON object on stdout: "models",
/// each variant's design laid out for the hands with what this model says
/// every note plays (bore-tmm's tools/export_models.py writes them to
/// bores/models/), and "reader", what tools/read_cut_files.py needs beside
/// the cut files it measures: the air, the window's depth and correction,
/// the foot left to trim, the notes, and each variant's section.
pub fn bores() -> String {
    use lasermade_tools::turn3d::{Num::F, J};
    let n = |x: f64| J::N(F(x));
    let s = |x: &str| J::S(x.to_string());
    let names: Vec<String> = (0..5).map(|i| format!("h{}", i + 1)).collect();
    // one design as bore-tmm reads it: tg the six notes' targets, nn their names
    let model_json = |label: &str, source: &str, w: f64, wall: f64, b: &Bore, model: &Model, ds: &Design, tg: &[f64], nn: &[String]| -> J {
        let hz: Vec<f64> = (0..6)
            .map(|k| model.sounding(b, ds.l, &ds.holes, k, wall, tg[k], &ds.diams).unwrap_or_else(|e| lasermade_tools::die(format!("ValueError: {e}"))))
            .collect();
        J::obj(vec![
            ("name", s(label)),
            ("source", s(source)),
            ("temp_c", n(T_C)),
            (
                "drive",
                J::obj(vec![
                    ("kind", s("jet")),
                    ("area_mm2", n(w * WINDOW_L)),
                    ("chimney_mm", n(WINDOW_T)),
                    ("mouth", n(model.mouth)),
                    ("stub_mm", n(WINDOW_L / 2.0)),
                ]),
            ),
            ("bore", J::A(vec![J::obj(vec![("len_mm", n(ds.l)), ("d_mm", n(2000.0 * b.a)), ("loss_ratio", n(b.rh / b.a))])])),
            ("end", s("unflanged")),
            (
                "holes",
                J::A((0..5).map(|i| J::obj(vec![("name", s(&names[i])), ("at_mm", n(ds.holes[i])), ("d_mm", n(ds.diams[i])), ("chimney_mm", n(wall))])).collect()),
            ),
            (
                "notes",
                J::A(
                    (0..6)
                        .map(|k| {
                            J::obj(vec![
                                ("name", s(&nn[k])),
                                ("hz", n(tg[k])),
                                ("open", J::A(names[..k].iter().map(|x| s(x)).collect())),
                                ("span", n(1.4)),
                                ("model_hz", n(hz[k])),
                            ])
                        })
                        .collect(),
                ),
            ),
        ])
    };
    let tg = targets();
    let a4: Vec<String> = NOTES.iter().map(|x| x.to_string()).collect();
    let (ar, mut models, mut variants) = (area(), vec![], vec![]);
    let sq = ar.sqrt();
    for (name, w, d, wall) in [
        ("box-square-3", sq, sq, 3.0),
        ("box-square-6", sq, sq, 6.0),
        ("stack-rect-3", ar / 18.0, 18.0, 3.0),
        ("stack-rect-6", ar / 18.0, 18.0, 6.0),
    ] {
        let b = Bore::new(Some((w, d)));
        variants.push((name.to_string(), J::obj(vec![("wall", n(wall)), ("d_mm", n(2000.0 * b.a)), ("loss_ratio", n(b.rh / b.a))])));
        let model = Model { window_w: w, ..Model::default() };
        let ds = model.design(&b, wall, true).unwrap_or_else(|e| lasermade_tools::die(format!("ValueError: {e}")));
        let label = format!("square-bore flute {name}, naf_model.rs design (laid out for the hands)");
        models.push((format!("square-flute-{name}"), model_json(&label, "square-flute/naf_model.rs design(even=true)", w, wall, &b, &model, &ds, &tg, &a4)));
    }
    // the long builds (2026-11-08): their own key, so their own notes, which
    // the reader takes in place of the A4 list
    for lb in crate::long_builds() {
        let (name, w, wall) = (lb.name(), lb.w(), crate::T);
        let b = Bore::new(Some((w, w)));
        let model = Model { window_w: w, spacing: lb.spacing, ..Model::default() };
        let ds = lb.design();
        let ltg: Vec<f64> = SEMIS.iter().map(|k| ds.key * py::powf(2.0, *k as f64 / 12.0)).collect();
        let nn: Vec<String> = std::iter::once(lb.key.to_string()).chain(lb.notes.iter().map(|x| x.to_string())).collect();
        variants.push((
            name.clone(),
            J::obj(vec![
                ("wall", n(wall)),
                ("d_mm", n(2000.0 * b.a)),
                ("loss_ratio", n(b.rh / b.a)),
                ("notes", J::A((0..6).map(|k| J::A(vec![s(&nn[k]), n(ltg[k])])).collect())),
            ]),
        ));
        let label = format!("square-bore flute {name}, naf_model.rs design_held ({} mm overall, in {})", py::g(crate::LONG_TOTAL), lb.key);
        models.push((format!("square-flute-{name}"), model_json(&label, "square-flute/naf_model.rs design_held(), square_flute.rs long_builds()", w, wall, &b, &model, &ds, &ltg, &nn)));
    }
    let reader = J::obj(vec![
        ("temp_c", n(T_C)),
        ("mouth", n(Model::default().mouth)),
        ("window_t", n(WINDOW_T)),
        ("foot_spare", n(FOOT_SPARE)),
        ("notes", J::A((0..6).map(|k| J::A(vec![s(NOTES[k]), n(tg[k])])).collect())),
        ("variants", J::O(variants)),
    ]);
    let mut out = String::new();
    J::O(vec![("models".into(), J::O(models)), ("reader".into(), reader)]).dump(&mut out);
    out
}

pub fn main() -> i32 {
    if std::env::args().nth(1).as_deref() == Some("--bores") {
        println!("{}", bores());
        return 0;
    }
    let mut m = Model::default();
    for x in std::env::args().skip(1) {
        let v = || {
            let t = x.split_once('=').map(|p| p.1).unwrap_or("");
            py::float(t).unwrap_or_else(|| lasermade_tools::die(format!("ValueError: could not convert string to float: {}", py::str_repr(t))))
        };
        if x.starts_with("--hole=") {
            m.hole_d = v();
        } else if x.starts_with("--mouth=") {
            m.mouth = v();
        } else if x.starts_with("--spacing=") {
            m.spacing = v();
        } else {
            lasermade_tools::die(format!("error: {x} is not a flag this model reads. It takes --hole=, --mouth= and --spacing=."));
        }
    }
    let ar = area();
    let sq = ar.sqrt();
    // name, bore across x deep (None: the round reference), hole wall
    let variants: [(&str, Option<(f64, f64)>, f64); 5] = [
        ("round reference", None, 5.0),
        ("box-square-3", Some((sq, sq)), 3.0),
        ("box-square-6", Some((sq, sq)), 6.0),
        ("stack-rect-3", Some((ar / 18.0, 18.0)), 3.0),
        ("stack-rect-6", Some((ar / 18.0, 18.0)), 6.0),
    ];
    println!(
        "A4 = {}Hz, air at {}C ({:.1} m/s), area {:.1}mm^2, window the bore's full width x {}mm ({}mm wide on the round reference), mouth x{}",
        py::g(A4), py::g(T_C), c(), ar, py::g(WINDOW_L), py::g(WINDOW_W), py::g(m.mouth)
    );
    println!("distances from the window centre, mm; holes numbered from the foot");
    for even in [false, true] {
        println!(
            "\n{}",
            if even {
                format!("LAID OUT FOR THE HANDS, 3 + 2 holes {}mm apart, holes 2 and 4 {}mm, the rest sized to pitch", py::g(m.spacing), py::g(ANCHOR_D))
            } else {
                format!("EQUAL HOLES, all {}mm, positions solved", py::g(m.hole_d))
            }
        );
        println!(
            "{:16} {:>12} {:>4} {:>6} {}  worst",
            "variant", "bore", "wall", "foot",
            (1..6).map(|i| format!("{:>11}", format!("h{i}"))).collect::<Vec<_>>().join(" ")
        );
        let mut seen: Vec<((i64, i64, u64, u64), Result<Design, String>)> = vec![];
        for (name, wd, wall) in variants {
            let b = Bore::new(wd);
            let ww = wd.map_or(WINDOW_W, |p| p.0);
            let key = (py::round(b.area * 1e9), py::round(b.rh * 1e6), wall.to_bits(), ww.to_bits());
            if !seen.iter().any(|s| s.0 == key) {
                // equal holes can have no layout at all: at --mouth=0.8 with
                // a 6mm wall, hole 5 would have to sit on hole 4. That is a
                // finding about equal holes, not a crash, so it is printed
                let mw = Model { window_w: ww, ..m };
                seen.push((key, mw.design(&b, wall, even)));
            }
            let sec = match wd {
                None => format!("ø{REF_BORE:.2}"),
                Some((w, d)) => format!("{w:.2}x{d:.2}"),
            };
            match &seen.iter().find(|s| s.0 == key).unwrap().1 {
                Err(e) => println!("{name:16} {sec:>12} {:>4}   no layout: {e}", py::g(wall)),
                Ok(d) => println!(
                    "{name:16} {sec:>12} {:>4} {:6.1} {}  {:.2}c",
                    py::g(wall), d.l,
                    d.holes.iter().zip(&d.diams).map(|(h, dd)| format!("{h:6.1}/{dd:<4.1}")).collect::<Vec<_>>().join(" "),
                    d.cents.iter().fold(0.0f64, |a, c| py::max(a, c.abs()))
                ),
            }
        }
    }
    0
}
