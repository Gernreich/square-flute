//! The author's own flute, from 2017: the design in yours/original/
//! measured, and what the model hears in it. It is not redrawn as a build of
//! its own any more (2026-10-13, the author): at the 3/4in bore its redraw
//! was a box-square-3 build with only the nest's half of the flue run, flat
//! or finger-jointed, in all but its holes and block, and the 3D page's joint
//! toggle covers it. Its ideas are in every build.
//!
//!     target/release/your_flute --no-write              # what the model hears in it
//!     target/release/your_flute --out=yours/cut-files   # and the leather tie
//!
//! This also draws the leather tie, cut from leather, not ply, with its own
//! sheet writer (svg). Python (your_flute.py) until 2026-11-07.
//!
//! WHAT WAS MEASURED, from yours/original/NAF_flatjoints.svg (Inkscape's 90
//! units to the inch, 0.28222mm a unit), along the flute from the mouth end:
//!
//!   bore              19.37 wide x 22.44mm deep, 434.7mm^2 -- a 23.5mm round
//!                     bore's area, a little over 15/16in
//!   slow air chamber  123.5mm to the exit hole, which is 6.0 long
//!   plug              11.0mm, its top fill-engraved as the flue, full width
//!   window            6.0 long x 19.37 wide, the whole width of the bore
//!   sound chamber     313.25mm from the window's centre to the foot
//!   finger holes      7.73, 7.87, 7.79, 7.79 and 5.47mm, foot-most first,
//!                     213.9, 185.7, 156.9, 109.5 and 78.0mm from the window
//!   splitting edge    a grey ramp, 19.4 x 9.9mm, engraved beside the window
//!                     to cut the bevel by laser. IT DID NOT WORK: the
//!                     author, on 2026-10-13. It stays in yours/original/ as
//!                     it was, and is in no build
//!   finger holes      each ringed by a soft engraved depression. They
//!                     worked, the author recalls, cut on a Glowforge, whose
//!                     3D engrave reads grey as depth. An xTool P2S's
//!                     Grayscale mode in XCS varies power with pixel
//!                     brightness, which should do the same
//!   mouthpiece        an end cap 25.89 x 28.89mm. Its 9.59mm circle is
//!                     centred 0.33mm inside one long edge, so cutting both
//!                     leaves a half-round NOTCH in that edge, not a hole in
//!                     the middle: the edge goes to the bottom, away from the
//!                     finger holes, and the notch opens through the bottom
//!                     wall into the bore. (Read as a centred breath hole
//!                     until 2026-10-13, when the author pointed it out.)
//!   block             four layers 25mm wide, 25, 19.8, 15.8 and 12.6 long
//!   tie               a leather strip 359.6 x 4.6mm
//!
//! AT ITS OWN SIZE the model reads this flute as a minor pentatonic to
//! within 40 cents and puts it near B-flat 4.
use crate::naf_model as m;
use crate::*;
use lasermade_tools::py;

const W: f64 = 19.37;
const D: f64 = 22.44;
const TOTAL: f64 = 456.70;
const WIN: (f64, f64) = (140.46, 146.45);
const HOLES: [f64; 5] = [357.315, 329.135, 300.375, 252.975, 221.455]; // from the mouth, foot-most first
const DIAMS: [f64; 5] = [7.73, 7.87, 7.79, 7.79, 5.47];
const STRIP: (f64, f64) = (359.64, 4.64);

fn strip_part() -> FPart {
    FPart::new("leather tie", 1, rect(Z, Z, F(STRIP.0), F(STRIP.1)), "cut from leather, not ply")
}

/// The leather tie's sheet. The writer once drew the author's whole flute
/// redrawn, in ply; only the tie is drawn now, so only its branch is here.
fn svg(kind: &str, k: usize, n: usize, sheet: &Sheet, parts: &[FPart], what: &str) -> String {
    let kf = kerf();
    let mut black = vec![];
    for &(i, sx, sy) in &sheet.parts {
        let p = &parts[i];
        let (b, _, _) = drawn(p, sx - p.p.x0 + kf / 2.0, sy - p.p.y0 + kf / 2.0);
        black.push(b);
    }
    let desc = format!("1 user unit = 1mm. The author's 2017 flute, redrawn: {kind}, sheet {k} of {n}: {what}. Cut from leather, not ply; black cuts. ");
    format!(
        "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{w:.2}mm\" height=\"{h:.2}mm\" viewBox=\"0 0 {w:.2} {h:.2}\">\n<title>The author's flute, {kind}, sheet {k} of {n}</title>\n<desc>{desc}</desc>\n{}</svg>\n",
        group(BLACK, &black),
        w = sheet.w,
        h = sheet.h
    )
}

/// What the model hears in the original, at its own window and bore.
fn predict() -> (f64, Vec<f64>, Vec<f64>) {
    let model = m::Model { window_w: W, window_l: WIN.1 - WIN.0, ..m::Model::default() };
    let b = m::Bore::new(Some((W, D)));
    let wc = (WIN.0 + WIN.1) / 2.0;
    let l = TOTAL - wc;
    let holes: Vec<f64> = HOLES.iter().map(|h| h - wc).collect();
    let (mut fs, mut near) = (vec![], 440.0);
    for n in 0..6 {
        let f = model
            .sounding(&b, l, &holes, n, T, if n > 0 { near * 1.19 } else { near }, &DIAMS)
            .unwrap_or_else(|e| lasermade_tools::die(format!("ValueError: {e}")));
        fs.push(f);
        near = f;
    }
    (l, holes, fs)
}

const NAMES: [&str; 12] = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

fn note(f: f64) -> (String, f64) {
    let n = 12.0 * py::log2(f / 440.0) + 69.0;
    let r = py::round(n);
    (format!("{}{}", NAMES[r.rem_euclid(12) as usize], r.div_euclid(12) - 1), 100.0 * (n - r as f64))
}

pub fn main() -> i32 {
    let (mut out, mut write): (Option<String>, bool) = (None, true);
    for x in std::env::args().skip(1) {
        if x == "--no-write" {
            write = false;
        } else if let Some(v) = x.strip_prefix("--out=") {
            out = Some(v.to_string());
        } else if x.starts_with("--kerf=") {
            set_kerf(&x);
        } else {
            lasermade_tools::die(format!("error: {x} is not a flag this generator reads. It takes --out=, --kerf= and --no-write."));
        }
    }
    if write && out.is_none() {
        lasermade_tools::die("error: --out=DIR, or --no-write to print the prediction only.");
    }
    let (l, _, fs) = predict();
    println!("the original, as the model hears it: bore {} x {}mm, sound chamber {l:.2}mm", py::repr(W), py::repr(D));
    for (n, &f) in fs.iter().enumerate() {
        let (nm, c) = note(f);
        println!(
            "  {n} open  {f:6.1}Hz  {nm:3} {c:+4.0}c   {:5.0}c above the fundamental (a minor pentatonic wants {})",
            1200.0 * py::log2(f / fs[0]),
            [0, 300, 500, 700, 1000, 1200][n]
        );
    }
    if write {
        let parts = vec![strip_part()];
        let s = &pack_parts(&parts)[0];
        let o = out.unwrap();
        std::fs::create_dir_all(&o).unwrap_or_else(|e| lasermade_tools::die(format!("{o}: {e}")));
        let f = format!("{}/your-flute-leather-tie-cut-files.svg", o.trim_end_matches('/'));
        std::fs::write(&f, svg("leather", 1, 1, s, &parts, "the tie")).unwrap_or_else(|e| lasermade_tools::die(format!("{f}: {e}")));
        println!("  wrote your-flute-leather-tie-cut-files.svg");
    }
    0
}
