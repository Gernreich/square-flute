//! Every build as a parametric SolidCraft design (2026-11-08): the rules
//! build() follows, as expressions, so changing one number rebuilds the rest.
//! `square_flute --solidcraft=DIR` writes one script per build;
//! `solidcraft-cli run SCRIPT --save X.sc` makes the design, `--out X.step`
//! the STEP file.
//!
//! The frame is the 3D view's and the STEP files': X along the flute from the
//! mouth end, Y across it, centred on the bore, Z up from the bottom plate's
//! underside.
//!
//! What follows a parameter: the ply (every plate, wall, layer and disc, the
//! fingers and their notches), the bore, the head (the slow air chamber, the
//! exit hole, the plug, the window), the foot's spare, the doubler's run, the
//! bird, the mouthpiece cap's notch and the bottom plate's, the flue's depth,
//! and the side walls' fingers, which re-count along the flute and keep clear
//! of the exit hole and the window as build() keeps them.
//!
//! What does not: the tuning. The chamber length and the five holes'
//! positions and diameters are what naf_model's transmission-matrix solver
//! found for this bore and hole wall, which no expression can redo; they are
//! parameters so a flute tuned by hand can be written back into its design.
//! Change the bore or the ply and they no longer play A4 until the solver is
//! run again. The number of plug discs, bore layers and bird layers is fixed
//! per build (each is a body), so the plug's length and a stack's depth are
//! counts of ply, not parameters of their own.
//!
//! Drawn beyond the 3D view: the flue, as a savanna flue, half engraved in
//! the top plate's outer face and half in the first bird layer's underside
//! (`flue_depth` each). The depressions round the holes are not drawn.

use crate::naf_model as m;
use crate::*;
use lasermade_tools::solidcraft::{n, Script};

/// A box from its ranges along X, Y and Z.
fn bx(s: &mut Script, name: &str, x: (&str, &str), y: (&str, &str), z: (&str, &str), op: &str, targets: &[&str]) {
    s.bx(
        name,
        [x.0.to_string(), y.0.to_string(), z.0.to_string()],
        [format!("({}) - ({})", x.1, x.0), format!("({}) - ({})", y.1, y.0), format!("({}) - ({})", z.1, z.0)],
        op,
        targets,
    );
}

/// What differs between builds at the head and in the tuning: the bore's
/// reference, the slow air chamber, and what the comments say of the key.
pub struct Head {
    pub bore_ref: f64,
    pub bore_comment: String,
    pub sac: f64,
    pub sac_comment: String,
    pub chamber_comment: String,
    pub notes: [String; 5],
}

impl Head {
    /// the six A4 builds
    pub fn a4() -> Head {
        Head {
            bore_ref: m::REF_BORE,
            bore_comment: "the round bore whose area every build keeps (3/4in)".into(),
            sac: SAC,
            sac_comment: "the slow air chamber, from the mouth end to the plug".into(),
            chamber_comment: "the sound chamber, window centre to the foot: naf_model's A4 for this bore and hole wall".into(),
            notes: ["C5", "D5", "E5", "G5", "A5"].map(String::from),
        }
    }
    /// a long build; main() fills in the chamber's comment once the key is known
    pub fn long(lb: &Long) -> Head {
        Head {
            bore_ref: lb.bore_ref,
            bore_comment: format!("the round bore whose area the square bore keeps: wider than the A4 builds' {} mm, so the biggest finger hole keeps 3 mm of ply beside the finger notches", n(m::REF_BORE)),
            sac: lb.sac,
            sac_comment: if lb.sac == SAC { "the slow air chamber, from the mouth end to the plug".into() } else { format!("the slow air chamber, from the mouth end to the plug: {} mm shorter than the A4 builds', the length given to the sound chamber", n(SAC - lb.sac)) },
            chamber_comment: String::new(),
            notes: lb.notes.map(String::from),
        }
    }
}

/// The design of one build: kind is "box", "flat" or "stack", as build().
pub fn script(kind: &str, wall: f64, ds: &m::Design, head: &Head) -> String {
    let boxy = kind == "box" || kind == "flat";
    let dbl = wall > T;
    let mut s = Script::new();
    // the sheet
    s.len("ply", format!("{} mm", n(T)), "sheet thickness: every plate, wall, layer and plug disc");
    // the bore: the reference round bore's area, in a section the ply builds
    s.len("bore_ref", format!("{} mm", n(head.bore_ref)), &head.bore_comment);
    if boxy {
        s.len("bore_w", "sqrt(pi)*bore_ref/2", "read only: the square bore across, the reference's area");
        s.len("bore_d", "bore_w", "read only: and deep");
    } else {
        s.num("bore_layers", n(py::round(18.0 / T) as f64), "bore layers in the stack, each a body");
        s.len("bore_d", "bore_layers*ply", "read only: the bore deep");
        s.len("bore_w", "pi*bore_ref*bore_ref/(4*bore_d)", "read only: the bore across, the reference's area");
        s.len("side", format!("{} mm", n(SIDE)), "the stack's walls, each side of the bore");
    }
    s.len("pw", if boxy { "bore_w + 2*ply" } else { "bore_w + 2*side" }, "read only: the flute across");
    // the head
    s.len("sac", format!("{} mm", n(head.sac)), &head.sac_comment);
    s.len("exit_l", format!("{} mm", n(EXIT_L)), "the exit hole along the flute, just before the plug");
    s.num("plug_discs", n((PLUG / T) as i64 as f64), "the plug's press-fit discs, each a body");
    s.len("plug", "plug_discs*ply", "read only: the plug's length, the flue's run");
    s.len("interf", format!("{} mm", n(INTERF_ACROSS)), "the plug discs' press-fit, over the bore each way");
    s.len("window_l", format!("{} mm", n(m::WINDOW_L)), "the window along the flute (it runs the bore's width)");
    s.len("flue_depth", "0.5 mm", "each half of the flue, engraved in the top's outer face and the bird's underside");
    s.len("wc", "sac + plug + window_l/2", "read only: the window's centre, where the tuning measures from");
    // the tuning, the solver's
    s.len("chamber", format!("{} mm", n(ds.l)), &head.chamber_comment);
    s.len("foot_spare", format!("{} mm", n(m::FOOT_SPARE)), "cut this much long at the foot, trim to pitch");
    let notes = &head.notes;
    for k in 0..5 {
        s.len(&format!("h_{}", k + 1), format!("{} mm", n(ds.holes[k])), &format!("hole {} (opens {}), from the window centre: the solver's", k + 1, notes[k]));
        s.len(&format!("d_{}", k + 1), format!("{} mm", n(ds.diams[k])), &format!("hole {}'s diameter: the solver's", k + 1));
    }
    s.len("total", "wc + chamber + foot_spare", "read only: the flute's length");
    // the doubler, the bird and the cap
    if dbl {
        s.len("doubler_past", format!("{} mm", n(DOUBLER_PAST)), "the doubler runs this far past the outermost holes");
        s.len("dz0", "wc + min(min(min(h_1, h_2), min(h_3, h_4)), h_5) - doubler_past", "read only: where the doubler starts");
        s.len("dz1", "wc + max(max(max(h_1, h_2), max(h_3, h_4)), h_5) + doubler_past", "read only: and ends");
    }
    s.len("bird_upstream", format!("{} mm", n(BIRD_UPSTREAM)), "the bird starts this far before the exit hole");
    s.len("cap_d", format!("{} mm", n(CAP_D)), "the half-round notch in the cap and the bottom plate's mouth end");
    s.len("notch_in", format!("{} mm", n(NOTCH_IN)), "the cap notch's centre, inside its bottom edge");
    // the checks build() makes, as room left: negative fails
    s.len("bed_room", format!("{} mm - 2*{} mm - total", n(BED.0), n(MARGIN)), "read only: bed length left past the longest part (the P2S's 600 mm)");
    s.len("dmax", "max(max(max(d_1, d_2), max(d_3, d_4)), d_5)", "read only: the largest hole");
    s.len("hole_room", format!("bore_w - 2*{} mm - dmax", n(MIN_WEB)), "read only: room left for the largest hole inside the bore");
    s.len(
        "gap_room",
        "min(min(h_1 - h_2 - (d_1 + d_2)/2, h_2 - h_3 - (d_2 + d_3)/2), min(h_3 - h_4 - (d_3 + d_4)/2, h_4 - h_5 - (d_4 + d_5)/2)) - 3 mm",
        "read only: ply left between the closest two holes, past 3 mm",
    );
    if kind == "box" {
        s.len("finger", "2*ply", "a finger's width, and the space between two");
        s.len("finger_end", "2*finger", "the fingers stay this far from each end");
        s.len("finger_clear", format!("{} mm", n(FINGER_CLEAR)), "and this far from the exit hole and the window");
        s.len("notch_room", format!("pw/2 - dmax/2 - ply - {} mm", n(MIN_WEB)), "read only: ply left between a hole and a finger notch");
        // fingers_x(): n at 2*finger pitch centred, less those near the openings
        s.len("pitch", "2*finger", "read only: finger to finger");
        s.num("n_f", "floor((total - 2*finger_end - finger)/pitch) + 1", "read only: finger places along the flute");
        s.len("fx0", "total/2 - (n_f - 1)*pitch/2", "read only: the first finger place");
        s.len("reach", "finger/2 + finger_clear", "read only: a finger's centre keeps this far from an opening");
        s.num("n_a", "max(0, min(n_f, floor((sac - exit_l - reach - fx0)/pitch + 1e-9) + 1))", "read only: fingers before the exit hole");
        s.num("i_m", "max(0, ceil((sac + reach - fx0)/pitch - 1e-9))", "read only: the first finger between the exit hole and the window");
        s.num("n_m", "max(0, min(n_f - 1, floor((sac + plug - reach - fx0)/pitch + 1e-9)) - i_m + 1)", "read only: fingers between them");
        s.num("i_c", "max(0, ceil((sac + plug + window_l + reach - fx0)/pitch - 1e-9))", "read only: the first finger past the window");
        s.num("n_c", "max(0, n_f - i_c)", "read only: fingers past the window");
    }
    let top_z = ("ply + bore_d", "2*ply + bore_d");
    let half = ("-pw/2", "pw/2");
    // the bodies, in build()'s order
    bx(&mut s, "1 top plate", ("0 mm", "total"), half, top_z, "new", &[]);
    let bottom = if boxy { "2 bottom plate" } else { "2 bottom layer" };
    bx(&mut s, bottom, ("0 mm", "total"), half, ("0 mm", "ply"), "new", &[]);
    let mut k = 3;
    let mut walls = vec![];
    let mut layers = vec![];
    if boxy {
        for (j, y) in [("bore_w/2", "bore_w/2 + ply"), ("-bore_w/2 - ply", "-bore_w/2")].into_iter().enumerate() {
            let name = format!("{k} side wall");
            bx(&mut s, &name, ("0 mm", "total"), y, ("ply", "ply + bore_d"), "new", &[]);
            if kind == "box" {
                // each run's first finger, full height (the wall between is
                // there already), repeated; an empty run stays inside the wall
                for (run, first, count) in [("a", "0", "n_a"), ("m", "i_m", "n_m"), ("c", "i_c", "n_c")] {
                    let f = format!("fingers {run}, wall {}", j + 1);
                    let x0 = format!("fx0 + {first}*pitch - finger/2");
                    let x1 = format!("fx0 + {first}*pitch + finger/2");
                    let on = format!("min(1, {count})");
                    bx(&mut s, &f, (&x0, &x1), y, (&format!("(1 - {on})*ply"), &format!("2*ply + bore_d - (1 - {on})*ply")), "join", &[&name]);
                    s.pattern(&f, [1.0, 0.0, 0.0], format!("max(1, {count})"), "pitch");
                }
            }
            walls.push(name);
            k += 1;
        }
        for i in 0..(PLUG / T) as i64 {
            let x0 = format!("sac + {i}*ply");
            let x1 = format!("sac + {}*ply", i + 1);
            bx(&mut s, &format!("{k} plug disc"), (&x0, &x1), ("-(bore_w + interf)/2", "(bore_w + interf)/2"), ("ply", "ply + bore_d + interf"), "new", &[]);
            k += 1;
        }
    } else {
        for i in 0..py::round(18.0 / T) {
            let name = format!("{k} bore layer");
            bx(&mut s, &name, ("0 mm", "total"), half, (&format!("ply + {i}*ply"), &format!("ply + {}*ply", i + 1)), "new", &[]);
            layers.push(name);
            k += 1;
        }
    }
    let doubler = format!("{k} doubler");
    if dbl {
        bx(&mut s, &doubler, ("dz0", "dz1"), half, ("2*ply + bore_d", "3*ply + bore_d"), "new", &[]);
        k += 1;
    }
    let mut birds = vec![];
    for i in 0..BIRD_LAYERS {
        let name = format!("{k} bird layer");
        let z0 = format!("2*ply + bore_d + {i}*ply");
        let z1 = format!("2*ply + bore_d + {}*ply", i + 1);
        bx(&mut s, &name, ("sac - exit_l - bird_upstream", "sac + plug"), half, (&z0, &z1), "new", &[]);
        birds.push(name);
        k += 1;
    }
    let cap = format!("{k} mouthpiece cap");
    bx(&mut s, &cap, ("-ply", "0 mm"), half, ("0 mm", "2*ply + bore_d"), "new", &[]);
    // the joints: the finger walls cut their notches from both plates
    if kind == "box" {
        for plate in ["1 top plate", bottom] {
            let tools = walls.iter().map(|w| q(w)).collect::<Vec<_>>().join(",");
            s.cmd("solid.combine", format!("{{\"target\":{},\"tools\":[{tools}],\"operation\":\"cut\",\"keep_tools\":true,\"name\":{}}}", q(plate), q(&format!("finger notches, {plate}"))));
        }
    }
    // the stack's chamber and bore, cut through every layer
    if !boxy {
        let t: Vec<&str> = layers.iter().map(|x| x.as_str()).collect();
        bx(&mut s, "slow air chamber", ("-1 mm", "sac"), ("-bore_w/2", "bore_w/2"), ("ply", "ply + bore_d"), "cut", &t);
        bx(&mut s, "bore", ("sac + plug", "total + 1 mm"), ("-bore_w/2", "bore_w/2"), ("ply", "ply + bore_d"), "cut", &t);
    }
    // the top: the exit hole, the window, the flue's nest half, the holes
    let through = ("ply + bore_d - 1 mm", "2*ply + bore_d + 1 mm");
    bx(&mut s, "exit hole", ("sac - exit_l", "sac"), ("-bore_w/2", "bore_w/2"), through, "cut", &["1 top plate"]);
    bx(&mut s, "window", ("sac + plug", "sac + plug + window_l"), ("-bore_w/2", "bore_w/2"), through, "cut", &["1 top plate"]);
    bx(&mut s, "flue, nest half", ("sac", "sac + plug"), ("-bore_w/2", "bore_w/2"), ("2*ply + bore_d - flue_depth", "2*ply + bore_d + 1 mm"), "cut", &["1 top plate"]);
    bx(&mut s, "flue, bird half", ("sac - exit_l", "sac + plug"), ("-bore_w/2", "bore_w/2"), ("2*ply + bore_d - 1 mm", "2*ply + bore_d + flue_depth"), "cut", &[&birds[0]]);
    let holed: Vec<&str> = if dbl { vec!["1 top plate", &doubler] } else { vec!["1 top plate"] };
    for i in 1..=5 {
        s.cylinder(&format!("hole {i}"), [format!("wc + h_{i}"), "0 mm".into(), "ply + bore_d - 1 mm".into()], None, &format!("d_{i}"), "2*ply + 2 mm", "cut", &holed);
    }
    // the mouth: the cap's notch, and the bottom plate's at right angles to it
    s.cylinder("cap notch", ["-ply - 1 mm".to_string(), "0 mm".into(), "notch_in".into()], Some([1.0, 0.0, 0.0]), "cap_d", "ply + 2 mm", "cut", &[&cap]);
    s.cylinder("end notch", ["0 mm".to_string(), "0 mm".into(), "-1 mm".into()], None, "cap_d", "ply + 2 mm", "cut", &[bottom]);
    s.measure();
    s.text()
}

fn q(s: &str) -> String {
    lasermade_tools::solidcraft::q(s)
}
