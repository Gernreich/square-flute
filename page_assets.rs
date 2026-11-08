//! The published page's moving parts, built from the generator's own build()
//! so the page cannot disagree with the cut files. The writeup itself is
//! README.md, built into index.html by md2html like every page here; this
//! adds what markdown cannot carry.
//!
//!     target/release/page_assets                      # viewer.js, turn.html and plans/*.svg
//!     target/release/page_assets --artifact OUT.html  # the whole page, one file
//!
//!   viewer.js    the 3D view of every build. README.md loads it on the page
//!                through a page-only line, so GitHub, which runs no script,
//!                shows a link to the page in its place.
//!   turn.html    viewer.js on a page of its own, nothing else on it, so the
//!                hub at gernreich.github.io can frame the 3D view the way it
//!                frames the bores' and the lyre-harp's.
//!   plans/       the two hole layouts drawn to scale, as plain SVG, so they
//!                read on GitHub as well as on the page.
//!
//! --artifact folds index.html and viewer.js into one self-contained file for
//! a claude.ai artifact: the script inlined, every local image a data URI.
//!
//! There was a second page, variants.html, until 2026-10-13, when the author
//! asked for the variants and the writeup to be one document. Python
//! (page_assets.py) until 2026-11-07.
use crate::naf_model as m;
use crate::*;
use lasermade_tools::py;
use lasermade_tools::turn3d::{dump_str, J};

#[path = "page_text.rs"]
pub mod text;
use text::*;

fn n3(x: Num) -> J {
    J::N(x.round(3))
}
fn f3(x: f64) -> J {
    J::N(F(py::round_dp(x, 3)))
}
fn pts3(o: &[Pt]) -> J {
    J::A(o.iter().map(|q| J::A(vec![n3(q[0]), n3(q[1])])).collect())
}
fn nums(v: &[Num]) -> J {
    J::A(v.iter().map(|&x| J::N(x)).collect())
}

/// Every part as a flat outline, its holes, and where it stands: a 3x4
/// matrix taking the part's own (x, y, extrusion) to the flute's (x along,
/// y across, z up), plus the way it moves when the view is exploded.
///
/// Physical outlines, before the kerf: this is the flute, not the sheet.
pub fn solids(w: f64, d: f64, wall: f64, parts: &[FPart], info: &Info) -> J {
    let pw = info.pw;
    let plate = |z0: Num| vec![vec![I(1), I(0), I(0), I(0)], vec![I(0), I(1), I(0), F(-pw / 2.0)], vec![I(0), I(0), I(1), z0]];
    let (mut k_plug, mut k_bird, mut k_side, mut k_bore) = (0i64, 0i64, 0i64, 0i64);
    let n_plug = parts.iter().filter(|p| p.p.name == "plug disc").count() as i64;
    let mut out = vec![];
    for p in parts {
        let holes: Vec<J> = p
            .p
            .cuts
            .iter()
            .map(|c| match c {
                Cut::Poly(q) => J::obj(vec![("p", pts3(q))]),
                Cut::Circle(cx, cy, r) => J::obj(vec![("c", J::A(vec![f3(*cx), f3(*cy), f3(*r)]))]),
            })
            .collect();
        let n = p.p.name.as_str();
        let (m, mut e, g): (Vec<Vec<Num>>, Vec<Num>, &str);
        if n == "side wall" {
            let yo = if k_side == 0 { w / 2.0 } else { -w / 2.0 - T };
            m = vec![vec![I(1), I(0), I(0), I(0)], vec![I(0), I(0), I(1), F(yo)], vec![I(0), I(-1), I(0), F(T + d)]];
            e = vec![I(0), I(if k_side == 0 { 1 } else { -1 }), I(0)];
            k_side += 1;
            g = "wall";
        } else if n == "plug disc" {
            m = vec![
                vec![I(0), I(0), I(1), F(SAC + k_plug as f64 * T)],
                vec![I(1), I(0), I(0), F(-(w + INTERF_ACROSS) / 2.0)],
                vec![I(0), I(1), I(0), F(T)],
            ];
            // the disc nearest the mouth moves furthest, so the gaps only
            // grow; the other way round they passed through each other at a
            // third of the way out and came apart in reverse order (the
            // author, 2026-10-13)
            e = vec![F(-1.2 - 0.25 * (n_plug - 1 - k_plug) as f64), I(0), I(0)];
            k_plug += 1;
            g = "plug";
        } else if n == "bottom plate" || n == "bottom layer" {
            m = plate(I(0));
            e = vec![I(0), I(0), I(-1)];
            g = "plate";
        } else if n == "bore layer" {
            m = plate(F(T + k_bore as f64 * T));
            e = vec![I(0), I(0), F(-0.75 + 0.25 * k_bore as f64)];
            k_bore += 1;
            g = "wall";
        } else if n.starts_with("top") {
            m = plate(F(T + d));
            e = vec![I(0), I(0), F(1.2)];
            g = "plate";
        } else if n == "doubler" {
            m = plate(F(2.0 * T + d));
            e = vec![I(0), I(0), F(1.8)];
            g = "dbl";
        } else if n == "mouthpiece cap" {
            let ch = p.p.h - (d + 2.0 * T);
            m = vec![vec![I(0), I(0), I(1), F(-T)], vec![I(1), I(0), I(0), F(-p.p.w / 2.0)], vec![I(0), I(1), I(0), F(-ch / 2.0)]];
            e = vec![F(-2.2), I(0), I(0)];
            g = "bird";
        } else if n == "bird layer" || n == "block layer" {
            m = plate(F(2.0 * T + d + k_bird as f64 * T));
            e = vec![I(0), I(0), F(2.6 + 0.4 * k_bird as f64)];
            k_bird += 1;
            g = "bird";
        } else {
            lasermade_tools::die(format!("ValueError: no place for a {n}"));
        }
        if g == "bird" && n != "mouthpiece cap" && !p.fills.is_empty() {
            // the woodland flue is on this layer's underside, which every
            // view from above hides: exploded, it comes out toward the viewer
            // and turns over, flue up (the author: "the bird flue does not
            // show up in the 3D exploded view", 2026-10-13)
            e = vec![I(0), F(-1.6), F(1.6)];
        }
        let o = if p.end_notch.is_some() { end_notch_outline(p) } else { p.p.outline.clone() };
        let top = n.starts_with("top");
        out.push(J::obj(vec![
            ("o", pts3(&o)),
            ("h", J::A(holes)),
            ("m", J::A(m.iter().map(|r| J::A(r.iter().map(|v| J::N(v.round(4))).collect())).collect())),
            ("e", nums(&e)),
            ("g", J::S(g.into())),
            ("n", J::N(I(p.p.num as i64))),
            ("name", J::S(n.into())),
            ("f", J::A(p.fills.iter().map(|f| pts3(f)).collect())),
            // which face the flue is engraved on: the top plate's upper face
            // for a plains (nest) flue, the bird's underside for a woodland
            // one. Until 2026-10-13 every flue was drawn on the underside,
            // which hid the nest flue inside the bore and made each bird-flue
            // build and its nest-flue counterpart look identical
            ("fc", p.ink.map_or(J::Null, |s| J::S(s.into()))),
            ("ft", J::B(top)),
            ("flip", J::B(!p.fills.is_empty() && !top)),
            ("zc", f3((m[2][3] + F(T / 2.0)).f())),
        ]));
    }
    J::obj(vec![
        ("parts", J::A(out)),
        ("len", J::N(F(py::round_dp(info.total, 1)))),
        ("W", J::N(F(py::round_dp(w, 2)))),
        ("D", J::N(F(py::round_dp(d, 2)))),
        ("top", J::N(F(py::round_dp(2.0 * T + d + if wall > T { T } else { 0.0 }, 2)))),
    ])
}

/// One hole layout from above, to scale, mouth on the left. Fixed colours on
/// a white ground, like the previews, so it reads on GitHub and in both of
/// the page's themes.
pub fn plan_svg(l: f64, holes: &[f64], diams: &[f64], wall: f64, title: &str) -> String {
    let r = py::repr;
    let wc = SAC + PLUG + m::WINDOW_L / 2.0;
    let total = wc + l + m::FOOT_SPARE;
    let (w, y0) = (26.0f64, 14.0f64);
    let (yc, o) = (y0 + w / 2.0, w / 2.0 - 3.0); // openings and flue: the bore's width
    let hx: Vec<f64> = holes.iter().map(|h| wc + h).collect();
    let mut s = vec![
        format!("<rect x=\"-2\" y=\"0\" width=\"{:.1}\" height=\"{}\" fill=\"#ffffff\"/>", total + 36.0, r(y0 + w + 14.0)),
        format!("<rect x=\"0\" y=\"{}\" width=\"{total:.1}\" height=\"{}\" fill=\"#e7dcc4\" stroke=\"#1d232b\" stroke-width=\".4\"/>", r(y0), r(w)),
        format!("<rect x=\"0\" y=\"{}\" width=\"{}\" height=\"{}\" fill=\"#f4eee0\"/>", r(y0), r(SAC), r(w)),
        format!(
            "<rect x=\"{}\" y=\"{}\" width=\"{}\" height=\"{}\" fill=\"none\" stroke=\"#8a7350\" stroke-width=\".5\" stroke-dasharray=\"1.5 1\"/>",
            r(SAC), r(y0 + 3.0), r(PLUG), r(w - 6.0)
        ),
        format!("<rect x=\"{:.1}\" y=\"{}\" width=\"{}\" height=\"{}\" fill=\"#a85800\" fill-opacity=\".25\"/>", wc + l, r(y0), r(m::FOOT_SPARE), r(w)),
    ];
    if wall > T {
        let (z0, z1) = (fmin(&hx) - DOUBLER_PAST, fmax(&hx) + DOUBLER_PAST);
        s.push(format!(
            "<rect x=\"{z0:.1}\" y=\"{}\" width=\"{:.1}\" height=\"{}\" fill=\"none\" stroke=\"#1d232b\" stroke-width=\".5\" stroke-dasharray=\"2 1.5\"/>",
            r(y0 + 1.5), z1 - z0, r(w - 3.0)
        ));
    }
    s.push(format!("<rect x=\"{}\" y=\"{}\" width=\"{}\" height=\"{}\" fill=\"#0000ff\" fill-opacity=\".45\"/>", r(SAC), r(yc - o), r(PLUG), r(2.0 * o)));
    for (x0, ww) in [(SAC - EXIT_L, EXIT_L), (SAC + PLUG, m::WINDOW_L)] {
        s.push(format!(
            "<rect x=\"{x0:.1}\" y=\"{}\" width=\"{}\" height=\"{}\" fill=\"#ffffff\" stroke=\"#a85800\" stroke-width=\".6\"/>",
            r(yc - o), r(ww), r(2.0 * o)
        ));
    }
    let t = "font-family=\"Helvetica, Arial, sans-serif\" text-anchor=\"middle\"";
    for (i, (x, d)) in hx.iter().zip(diams).enumerate() {
        s.push(format!("<circle cx=\"{x:.1}\" cy=\"{}\" r=\"{:.2}\" fill=\"#ffffff\" stroke=\"#a85800\" stroke-width=\".6\"/>", r(yc), d / 2.0));
        s.push(format!("<text x=\"{x:.1}\" y=\"{}\" font-size=\"6\" fill=\"#1d232b\" {t}>{}</text>", r(y0 + w + 9.0), i + 1));
        s.push(format!("<text x=\"{x:.1}\" y=\"{}\" font-size=\"5\" fill=\"#5a636d\" {t}>ø{d:.1}</text>", r(y0 - 4.0)));
    }
    s.push(format!("<text x=\"{}\" y=\"{}\" font-size=\"6\" fill=\"#5a636d\" {t}>slow air chamber</text>", r(SAC / 2.0), r(yc + 2.5)));
    s.push(format!(
        "<text x=\"{:.1}\" y=\"{}\" font-size=\"6\" fill=\"#5a636d\" {t}>sound chamber</text>",
        (fmax(&hx) + wc + l) / 2.0, r(yc + 2.5)
    ));
    s.push(format!(
        "<text x=\"{:.1}\" y=\"{}\" font-size=\"6\" fill=\"#1d232b\" font-family=\"Helvetica, Arial, sans-serif\">{total:.0}</text>",
        total + 4.0, r(yc + 2.5)
    ));
    format!(
        "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"-2 0 {:.0} {}\">\n<title>{title}</title>\n<desc>Display drawing, not a cut file. Plan view to scale, mouth on the left: the slow air chamber, the exit hole, the flue over the plug (blue) and the window, the finger holes with their diameters above and their numbers below, and the 15mm trimmed to pitch at the foot.</desc>\n{}\n</svg>\n",
        total + 36.0, r(y0 + w + 14.0), s.join("\n")
    )
}

/// Every build's solids, and one plan per wall: (wall, L, holes, diams).
pub fn build_all() -> (Vec<(String, J)>, Vec<(f64, m::Design)>) {
    let (mut three, mut plans): (Vec<(String, J)>, Vec<(f64, m::Design)>) = (vec![], vec![]);
    for (name, kind, w, d, wall, ds) in designs() {
        let (parts, info) = build(kind, w, d, wall, ds.l, &ds.holes, &ds.diams);
        three.push((name.to_string(), solids(w, d, wall, &parts, &info)));
        if !plans.iter().any(|p| p.0 == wall) {
            // drawn at the square bore
            plans.push((wall, ds));
        }
    }
    (three, plans)
}

fn jstr(s: &str) -> String {
    let mut o = String::new();
    dump_str(s, &mut o);
    o
}

pub fn viewer_js(three: &[(String, J)]) -> String {
    let mut bases: Vec<String> = vec![];
    for (n, _) in three {
        let mut b = n.as_str();
        b = b.strip_suffix("-flat").unwrap_or(b);
        let b = b.strip_suffix("-3").or_else(|| b.strip_suffix("-6")).map(|x| x.to_string());
        let b = b.unwrap_or_else(|| n.clone());
        if !bases.contains(&b) {
            bases.push(b);
        }
    }
    let buttons: String = bases
        .iter()
        .enumerate()
        .map(|(i, n)| format!("<button type=\"button\" data-v=\"{n}\" aria-pressed=\"{}\"><code>{n}</code></button>", i == 0))
        .collect();
    let mut data = String::new();
    J::O(three.to_vec()).dump(&mut data);
    let js = JS.replace("__DATA__", &data);
    VIEWER_JS
        .replace("__CSS__", &jstr(CSS))
        .replace("__MARKUP__", &jstr(&MARKUP.replace("__BUTTONS__", &buttons)))
        .replace("__JS__", &js)
}

/// index.html with viewer.js inlined and every local image a data URI, as
/// one file, without the document skeleton the artifact host supplies.
fn artifact(out: &str) {
    let h = here();
    let read = |p: &str| std::fs::read_to_string(format!("{h}/{p}")).unwrap_or_else(|e| lasermade_tools::die(format!("{p}: {e}")));
    let mut page = read("index.html").replace("<script src=\"viewer.js\"></script>", &format!("<script>{}</script>", read("viewer.js")));
    let src = lasermade_tools::re::rx(r#"src="([^"]+\.(?:png|svg))""#);
    page = lasermade_tools::re::sub(&src, &page, |c| {
        let s = &c[1];
        let p = format!("{h}/{s}");
        if s.starts_with("http") || s.starts_with("data:") || !std::path::Path::new(&p).exists() {
            return c[0].to_string();
        }
        let kind = if s.ends_with(".svg") { "image/svg+xml" } else { "image/png" };
        format!("src=\"data:{kind};base64,{}\"", py::b64(&std::fs::read(&p).unwrap()))
    });
    let skel = lasermade_tools::re::rx(r"(?is)<!doctype[^>]*>|</?html[^>]*>|</?body[^>]*>|</?head>");
    page = lasermade_tools::re::sub_str(&skel, &page, "");
    std::fs::write(out, &page).unwrap_or_else(|e| lasermade_tools::die(format!("{out}: {e}")));
    println!("  wrote {out}: {}KB", page.chars().count() / 1024);
}

pub fn main() -> i32 {
    let a: Vec<String> = std::env::args().skip(1).collect();
    if a.len() == 2 && a[0] == "--artifact" {
        artifact(&a[1]);
        return 0;
    }
    // --viewer-to=FILE and --plans-to=DIR write one asset where .repro asks,
    // so the reproduction gate compares them like any other shipped file
    let pick = |k: &str| -> Vec<String> { a.iter().filter_map(|x| x.strip_prefix(k).map(String::from)).collect() };
    let (vt, pt, tt) = (pick("--viewer-to="), pick("--plans-to="), pick("--turn-to="));
    if vt.len() + pt.len() + tt.len() != a.len() {
        lasermade_tools::die("usage: page_assets [--viewer-to=FILE] [--plans-to=DIR] [--turn-to=FILE] | --artifact OUT.html");
    }
    let h = here();
    let write = |f: &str, s: &str| std::fs::write(f, s).unwrap_or_else(|e| lasermade_tools::die(format!("{f}: {e}")));
    if !tt.is_empty() || a.is_empty() {
        write(&tt.first().cloned().unwrap_or(format!("{h}/turn.html")), TURN_PAGE);
    }
    if !tt.is_empty() && tt.len() == a.len() {
        return 0;
    }
    let (three, plans) = build_all();
    if !vt.is_empty() || a.is_empty() {
        write(&vt.first().cloned().unwrap_or(format!("{h}/viewer.js")), &viewer_js(&three));
    }
    if !pt.is_empty() || a.is_empty() {
        let d = pt.first().cloned().unwrap_or(format!("{h}/plans"));
        std::fs::create_dir_all(&d).unwrap_or_else(|e| lasermade_tools::die(format!("{d}: {e}")));
        for (wall, ds) in &plans {
            let f = format!("{}/square-flute-A4-holes-{}mm-wall.svg", d.trim_end_matches('/'), py::g(*wall));
            write(&f, &plan_svg(ds.l, &ds.holes, &ds.diams, *wall, &format!("Holes in {}mm of wall, sound chamber {:.1}mm", py::g(*wall), ds.l)));
        }
    }
    println!(
        "  wrote viewer.js: {} builds; plans: {}",
        three.len(),
        plans.iter().map(|p| format!("{}mm", py::g(p.0))).collect::<Vec<_>>().join(", ")
    );
    0
}
