#!/usr/bin/env python3
"""Plantilla de los 20 efectos (estilo del reel de @taki.gpt: fondos negros con brillo azul y naranja, cajas blancas y naranja) para cualquier reel vertical, con Hyperframes.
Sale del reel 20 EFECTOS de @donpablo_ai (v7). Lee config.json en la carpeta del proyecto y escribe index.html
para `npx hyperframes render`. La prepara y la ejecuta Claude Code siguiendo SKILL.md.
Capas: cámara (z1) · fondos y cosas por detrás (z2) · cámara elevada dentro de una interfaz (z3) ·
recorte de la persona (z4) · gráficos delante (z5) · rótulo de arriba (z8) · subtítulos (z9).
Uso (desde la carpeta del proyecto): python3 <ruta de la skill>/plantilla/construir.py"""
import json
import math
import os
import random
import re
import shutil
import subprocess
from string import Template

ROOT = os.getcwd()  # carpeta del proyecto del usuario (donde está config.json)
KIT = os.path.dirname(os.path.abspath(__file__))  # carpeta de la plantilla
CFG = json.load(open(os.path.join(ROOT, "config.json")))
DUR = float(CFG["duracion"])
FX, FY = CFG["cara"]  # centro de la cara en el vídeo de 1080x1920
VID, CUT = CFG.get("video", "assets/toma.mp4"), CFG.get("recorte", "assets/recorte.webm")
EFF = [{"name": e["nombre"], "start": float(e["inicio"]), "dur": float(e["duracion"]), "tipo": e["tipo"]} for e in CFG["efectos"]]
INTRO = CFG.get("intro")
CIERRE = CFG.get("cierre")
T_HUD0 = EFF[0]["start"]
T_HUD1 = float(CIERRE["inicio"]) if CIERRE else DUR
NAMES = [e["name"] for e in EFF]
N = len(EFF)
TITULO = CFG.get("titulo", ["20 efectos de vídeo", "hechos por Claude"])
DX, DY = FX - 566, FY - 900  # desplazamiento respecto a la cara del reel original

OR, PAPER, BLUE, INK = "#FB5222", "#FBF9F5", "#1A57F2", "#111111"  # colores medidos en el vídeo de Taki
SANS = '"Inter", sans-serif'
SHADOW = "0 30px 70px -20px rgba(0,0,0,.6)"

html_back, html_front, html_hud, js, sfx = [], [], [], [], []


def add_sfx(t, name, vol):
    sfx.append((round(t, 3), name, vol))


def bg(img):
    return f'<div class="full" style="background:url(assets/kit/img/{img}) center/cover"></div>'


# ---------------------------------------------------------------- cámara
def place(box, s, target):
    """Caja de la cámara (left, top, w, h) en pantalla; la cara (FX, FY) cae en target (coordenadas de pantalla)."""
    l, t, w, h = box
    x = target[0] - l - FX * s
    y = target[1] - t - FY * s
    return l, t, w, h, s, x, y


def cam(t0, box=(0, 0, 1080, 1920), s=1.0, target=(FX, FY), z=1, radius=0, shadow="none", fg=False, fg_same=True):
    l, tp, w, h, s_, x, y = place(box, s, target)
    js.append(f'tl.set("#cam-box", {{ left: {l}, top: {tp}, width: {w}, height: {h}, zIndex: {z}, borderRadius: {radius}, boxShadow: "{shadow}", x: 0, y: 0, rotation: 0, scale: 1, transformOrigin: "50% 50%" }}, {t0:.3f});')
    js.append(f'tl.set("#cam-plate", {{ opacity: 0 }}, {t0:.3f});')
    js.append(f'tl.set("#cam-inner", {{ x: {x:.1f}, y: {y:.1f}, scale: {s_:.4f} }}, {t0:.3f});')
    js.append(f'tl.set(".cmove, .cpunch, .fmove, .fpunch", {{ scale: 1, x: 0, y: 0, rotation: 0, filter: "none", transformOrigin: "{FX}px {FY}px" }}, {t0:.3f});')
    js.append(f'tl.set("#cam-box", {{ filter: "none" }}, {t0:.3f});')
    if fg_same:
        js.append(f'tl.set("#fg-inner", {{ x: {l + x:.1f}, y: {tp + y:.1f}, scale: {s_:.4f} }}, {t0:.3f});')
    js.append(f'tl.set("#fg-box", {{ opacity: {1 if fg else 0}, x: 0, y: 0, clipPath: "inset(0px 0px 0px 0px)" }}, {t0:.3f});')
    js.append(f'tl.set("#cutout", {{ filter: "none" }}, {t0:.3f});')


def clip(layer, cid, t0, d, inner, z=None, style=""):
    zs = f"z-index:{z};" if z is not None else ""
    el = f'<div id="{cid}" class="clip lay" style="{zs}{style}" data-start="{t0:.3f}" data-duration="{d:.3f}" data-track-index="{2 if layer is html_back else 5}">{inner}</div>'
    layer.append(el)


def video_dup(vid, t0, d, style, src=None):
    """Copia de la toma (o del recorte) sincronizada con el vídeo principal (mismo instante)."""
    src = src or VID
    return f'<video id="{vid}" class="clip dup" src="{src}" data-start="{t0:.3f}" data-duration="{d:.3f}" data-media-start="{t0:.3f}" data-track-index="6" muted playsinline style="{style}"></video>'


FULL = "position:absolute;left:0;top:0;width:1080px;height:1920px;"

# ---------------------------------------------------------------- iconos
ICONS = {
    "play": '<svg viewBox="0 0 48 48"><path d="M17 12 L36 24 L17 36 Z" fill="currentColor"/></svg>',
    "cc": '<svg viewBox="0 0 48 48"><rect x="6" y="11" width="36" height="26" rx="6" fill="none" stroke="currentColor" stroke-width="3.5"/><text x="24" y="30" text-anchor="middle" font-family="Inter" font-weight="800" font-size="14" fill="currentColor">CC</text></svg>',
    "aa": '<svg viewBox="0 0 48 48"><text x="24" y="33" text-anchor="middle" font-family="Inter" font-weight="800" font-size="24" fill="currentColor">Aa</text></svg>',
    "cut": '<svg viewBox="0 0 48 48"><g fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"><circle cx="15" cy="33" r="6"/><circle cx="33" cy="33" r="6"/><path d="M19 29 L35 9 M29 29 L13 9"/></g></svg>',
    "note": '<svg viewBox="0 0 48 48"><path d="M30 8 V31 a6.5 6.5 0 1 1 -4 -6 V14 L38 11 V8 Z" fill="currentColor"/></svg>',
    "spark": '<svg viewBox="0 0 48 48"><path d="M24 5 L28 20 L43 24 L28 28 L24 43 L20 28 L5 24 L20 20 Z" fill="currentColor"/></svg>',
    "wave": '<svg viewBox="0 0 48 48"><g fill="currentColor"><rect x="8" y="20" width="4" height="8" rx="2"/><rect x="15" y="14" width="4" height="20" rx="2"/><rect x="22" y="9" width="4" height="30" rx="2"/><rect x="29" y="15" width="4" height="18" rx="2"/><rect x="36" y="19" width="4" height="10" rx="2"/></g></svg>',
}
SEND = ('<svg viewBox="0 0 24 24"><path d="M12 19 V5 M5.5 11.5 L12 5 L18.5 11.5" fill="none" stroke="#fff" stroke-width="2.6" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>')
TICK = ('<svg viewBox="0 0 16 16"><path d="M3 8.5 L6.5 12 L13 4.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
        'stroke-linejoin="round"/></svg>')
VERIFIED = ('<svg viewBox="0 0 24 24"><path d="M12 1.5l2.6 2.2 3.4-.4.9 3.3 3 1.7-1.1 3.2 1.1 3.2-3 1.7-.9 3.3-3.4-.4L12 22.5l-2.6-2.2-3.4.4-.9-3.3-3-1.7'
            ' 1.1-3.2L2.1 9.3l3-1.7.9-3.3 3.4.4z" fill="#3897F0"/><path d="M7.5 12.2l3 3 6-6.2" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def _path(name):
    s = open(os.path.join(KIT, "assets", "logos", name + ".svg")).read()
    vb = re.search(r'viewBox="([^"]+)"', s).group(1)
    return vb, re.search(r'<path[^>]*\sd="([^"]+)"', s).group(1)


def claude_logo(color="#D97757"):
    vb, dp = _path("claude")
    return f'<svg viewBox="{vb}"><path d="{dp}" fill="{color}" fill-rule="evenodd"/></svg>'


def check_svg(color=OR):
    return f'<svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="18" fill="{color}"/><path d="M12 20.5 L18 26 L28.5 14.5" fill="none" stroke="#fff" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'


SQCHECK = (f'<svg viewBox="0 0 34 34"><rect width="34" height="34" rx="8" fill="{OR}"/><path d="M9 17.5 L14.5 23 L25 11.5" fill="none" stroke="#fff" '
           'stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')


# ---------------------------------------------------------------- INTRO y lista de efectos a los lados (estilo Taki)
def tbox(cls, lines, attrs=""):
    """Texto con fondo por línea, como el texto con fondo de TikTok/Instagram que usa Taki."""
    return f'<div class="tbox {cls}"{attrs}>' + "".join(f"<span>{ln}</span>" for ln in lines) + "</div>"


def side_lists(prefix, t0, d, stagger=0.045, start=0.25, flip=None):
    out = ""
    per = max(1, math.ceil(N / 2))
    for k, n in enumerate(NAMES):
        col, row = k // per, k % per
        side = "left:34px" if col == 0 else "right:34px"
        out += f'<div id="{prefix}-i{k}" class="li" style="{side};top:{708 + row * 50}px"><b>{k + 1:02d}</b>{n}</div>'
        js.append(f'tl.fromTo("#{prefix}-i{k}", {{ opacity: 0, x: {-40 if col == 0 else 40} }}, {{ opacity: 1, x: 0, duration: 0.22, ease: "power3.out" }}, {t0 + start + stagger * k:.3f});')
        if flip is not None:  # se encienden en naranja uno a uno, como en el original
            tf = flip + 0.032 * k
            js.append(f'tl.set("#{prefix}-i{k}", {{ backgroundColor: "{OR}" }}, {tf:.3f}); tl.set("#{prefix}-i{k} b", {{ color: "#FFFFFF" }}, {tf:.3f});')
            js.append(f'tl.fromTo("#{prefix}-i{k}", {{ scale: 1.12 }}, {{ scale: 1, duration: 0.14, ease: "power2.out", immediateRender: false }}, {tf:.3f});')
    clip(html_front, f"{prefix}-lists", t0, d, out)


def intro():
    t0, d = float(INTRO["inicio"]), float(INTRO["duracion"])
    cam(t0)
    inner = f'<div id="in-logo" class="clogo">{claude_logo("#FFFFFF")}</div>' + tbox("big", TITULO, ' id="in-t"')
    clip(html_front, "intro-title", t0, d, inner)
    side_lists("in", t0, d, flip=1.98)
    js.append(f'tl.to("#in-lists .li", {{ opacity: 0, duration: 0.15, ease: "power1.in" }}, {t0 + d - 0.18:.3f});')


# ---------------------------------------------------------------- HUD (logo, rótulo, número + nombre y barra de rayas)
def hud():
    dashes = "".join(f'<i id="hb{k}"></i>' for k in range(N))
    labels = ""
    for k, s in enumerate(EFF):
        labels += (f'<div id="hl{k}" class="clip hl" data-start="{s["start"]:.3f}" data-duration="{s["dur"]:.3f}" data-track-index="8">'
                   f'<span class="hn">{k + 1:02d}</span><span class="ht">{s["name"]}</span></div>')
        js.append(f'tl.set("#hb{k}", {{ backgroundColor: "{OR}" }}, {s["start"]:.3f});')
        js.append(f'tl.fromTo("#hb{k}", {{ scaleY: 1.9 }}, {{ scaleY: 1, duration: 0.25, ease: "power2.out", immediateRender: false }}, {s["start"]:.3f});')
        js.append(f'tl.fromTo("#hl{k} .hn", {{ scale: 0.6 }}, {{ scale: 1, duration: 0.18, ease: "back.out(2.5)" }}, {s["start"]:.3f});')
        js.append(f'tl.fromTo("#hl{k} .ht", {{ opacity: 0, x: -16 }}, {{ opacity: 1, x: 0, duration: 0.16, ease: "power3.out" }}, {s["start"]:.3f});')
    html_hud.append(f'<div id="hud" class="clip" data-start="{T_HUD0:.3f}" data-duration="{T_HUD1 - T_HUD0:.3f}" data-track-index="7">'
                    f'<div id="hud-logo" class="clogo">{claude_logo("#FFFFFF")}</div>'
                    + tbox("small", TITULO, ' id="hud-t"')
                    + f'<div id="hud-bars">{dashes}</div></div>')
    html_hud.append(labels)


# ---------------------------------------------------------------- efectos
ORBIT = [("spark", OR, "#FFFFFF"), ("aa", PAPER, INK), ("cc", INK, "#FFFFFF"), ("wave", BLUE, "#FFFFFF"),
         ("play", PAPER, OR), ("claude", INK, OR), ("cut", INK, "#FFFFFF"), ("note", INK, "#FFFFFF")]


def otile(icon, bgc, fgc):
    svg = claude_logo(fgc) if icon == "claude" else ICONS[icon]
    return f'<div class="otile" style="background:{bgc};color:{fgc}">{svg}</div>'


def e01(t0, d):  # Órbita (como Taki): iconos de edición que giran por una órbita de rayas alrededor de la cabeza y pasan por detrás
    cam(t0, fg=True)
    cx, cy, rx, ry, tilt = FX, FY - 80, 400, 120, -0.18

    def pts(a0):  # media elipse: la de arriba va detrás de la cabeza y la de abajo, delante
        return " ".join(f"{cx + rx * math.cos(a):.1f},{cy + ry * math.sin(a) + tilt * rx * math.cos(a):.1f}" for a in (a0 + math.pi * i / 60 for i in range(61)))
    line = '<svg class="full" viewBox="0 0 1080 1920"><polyline id="{}" points="{}" fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="3" stroke-dasharray="10 12"/></svg>'
    back, front = line.format("op-b", pts(math.pi)), line.format("op-f", pts(0))
    for k, (ic, bgc, fgc) in enumerate(ORBIT):
        back += f'<div id="ob{k}" class="orb">{otile(ic, bgc, fgc)}</div>'
        front += f'<div id="of{k}" class="orb">{otile(ic, bgc, fgc)}</div>'
    clip(html_back, "orb-back", t0, d, back)
    clip(html_front, "orb-front", t0, d, front)
    js.append(f'tl.fromTo("#op-b, #op-f", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25 }}, {t0:.3f});')
    js.append(f'(function () {{ const st = {{ a: 0, k: 0 }}; const n = {len(ORBIT)};'
              f' function draw() {{ for (let i = 0; i < n; i++) {{ const a = st.a + i * 2 * Math.PI / n; const s = Math.sin(a), c = Math.cos(a);'
              f' const x = {cx} + {rx} * c - 52, y = {cy} + {ry} * s + {tilt} * {rx} * c - 52; const sc = (0.8 + 0.26 * (s + 1) / 2) * st.k;'
              f' const front = s > 0; gsap.set("#of" + i, {{ x: x, y: y, scale: sc, opacity: front ? 1 : 0 }}); gsap.set("#ob" + i, {{ x: x, y: y, scale: sc, opacity: front ? 0 : 1 }}); }} }}'
              f' tl.fromTo(st, {{ a: -0.6 }}, {{ a: 3.4, duration: {d:.3f}, ease: "none", onUpdate: draw, immediateRender: false }}, {t0:.3f});'
              f' tl.fromTo(st, {{ k: 0 }}, {{ k: 1, duration: 0.25, ease: "back.out(2)", onUpdate: draw, immediateRender: false }}, {t0:.3f}); }})();')
    add_sfx(t0 + 0.02, "whoosh-short", 0.14)


SPIN = ('<svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="15" fill="none" stroke="#E6E1D6" stroke-width="4"/>'
        '<path d="M20 5 A15 15 0 0 1 35 20" fill="none" stroke="#D97757" stroke-width="4" stroke-linecap="round"/></svg>')


def e02(t0, d):  # Chat a pantalla completa (como Taki): la toma entra en un chat de Claude como vídeo adjunto, Claude marca su lista y la toma vuelve
    VB = (640, 660, 340, 604)
    s = VB[2] / 1080
    cam(t0, box=VB, s=s, target=(VB[0] + FX * s, VB[1] + FY * s), z=3, shadow=SHADOW)
    k0, dx, dy = 3.18, 540 - (VB[0] + VB[2] / 2), 960 - (VB[1] + VB[3] / 2)
    items = CFG.get("chat_lista", ["Quito las pausas", "Subtitulo cada palabra", f"Añado los {N} efectos"])
    rows = "".join(f'<div id="ch-r{j}" class="chr" style="top:{768 + 66 * j}px"><span class="chb">{SPIN}</span><span id="ch-c{j}" class="chc">{check_svg("#D97757")}</span>{t}</div>'
                   for j, t in enumerate(items))
    back = (bg("taki-dark.jpg") + '<div id="ch-ui" class="full" style="transform-origin:540px 900px">'
            '<div class="chcard"></div><div class="chhd"><i style="background:#FF5F57"></i><i style="background:#FEBC2E"></i><i style="background:#28C840"></i>'
            f'<b>{claude_logo()}Claude</b><em>EDITAR VÍDEO</em></div>'
            f'<div id="ch-me" class="chme">{CFG.get("chat_pide", f"Edita este vídeo: quita las pausas, subtitula cada palabra y añade estos {N} efectos")}</div>'
            f'<div class="chslot" style="left:{VB[0]}px;top:{VB[1]}px;width:{VB[2]}px;height:{VB[3]}px"></div>'
            f'<div class="chav">{claude_logo()}</div><div id="ch-dots" class="chdots"><i></i><i></i><i></i></div>'
            f'<div id="ch-ok" class="chok">Vale, me pongo.</div>{rows}'
            f'<div class="chin"><span>Responde a Claude…</span><b>{SEND}</b></div></div>')
    clip(html_back, "chat", t0, d, back)
    clip(html_front, "chat-f", t0, d, f'<div id="ch-tag" class="chtag" style="left:{VB[0] + 14}px;top:{VB[1] + VB[3] - 50}px">{ICONS["play"]}{CFG.get("archivo", "toma.mov")}</div>')
    js.append(f'tl.fromTo("#cam-box", {{ scale: {k0}, x: {dx:.0f}, y: {dy:.0f}, borderRadius: 0 }}, {{ scale: 1, x: 0, y: 0, borderRadius: 18, duration: 0.36, ease: "power3.inOut", immediateRender: false }}, {t0:.3f});')
    js.append(f'tl.fromTo("#ch-ui, #ch-tag", {{ opacity: 0, scale: 0.96 }}, {{ opacity: 1, scale: 1, duration: 0.26, ease: "power2.out", immediateRender: false }}, {t0 + 0.06:.3f});')
    js.append(f'tl.to("#cam-box", {{ scale: {k0}, x: {dx:.0f}, y: {dy:.0f}, borderRadius: 0, duration: 0.34, ease: "power3.inOut" }}, {t0 + d - 0.34:.3f});')
    js.append(f'tl.to("#ch-ui, #ch-tag", {{ opacity: 0, duration: 0.18, ease: "power1.in" }}, {t0 + d - 0.34:.3f});')
    js.append(f'tl.fromTo("#ch-dots", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.08 }}, {t0 + 0.42:.3f});')
    js.append(f'tl.fromTo("#ch-dots i", {{ y: 0 }}, {{ y: -6, duration: 0.14, stagger: 0.07, repeat: 3, yoyo: true, ease: "sine.inOut" }}, {t0 + 0.42:.3f});')
    js.append(f'tl.to("#ch-dots", {{ opacity: 0, duration: 0.06 }}, {t0 + 0.84:.3f});')
    js.append(f'tl.fromTo("#ch-ok", {{ opacity: 0, y: 8 }}, {{ opacity: 1, y: 0, duration: 0.16, ease: "power2.out" }}, {t0 + 0.86:.3f});')
    for j in range(3):
        ta = t0 + 0.98 + 0.2 * j
        js.append(f'tl.fromTo("#ch-r{j}", {{ opacity: 0, x: -14 }}, {{ opacity: 1, x: 0, duration: 0.14, ease: "power2.out" }}, {ta:.3f});')
        js.append(f'tl.fromTo("#ch-r{j} .chb", {{ rotation: 0 }}, {{ rotation: 540, duration: 0.5, ease: "none" }}, {ta:.3f});')
        js.append(f'tl.fromTo("#ch-c{j}", {{ scale: 0 }}, {{ scale: 1, duration: 0.14, ease: "back.out(3)" }}, {ta + 0.15:.3f});')
        add_sfx(ta + 0.15, "click-soft", 0.14)
    add_sfx(t0, "whoosh-short", 0.14)
    add_sfx(t0 + 0.42, "typing", 0.08)
    add_sfx(t0 + d - 0.34, "whoosh-short", 0.12)


MARCO_JS = """(function () {
  const st = { u: 0 };
  const A0 = [0, 0, 1080, 1920], A1 = [34, 34, 1046, 1886], B = [70, $by1, 1010, $by2];
  const cl = function (x) { return Math.max(0, Math.min(1, x)); };
  const io = function (x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
  const mix = function (a, b, p) { return a.map(function (v, i) { return v + (b[i] - v) * p; }); };
  function quad(r, ang, dy) {
    const cx = (r[0] + r[2]) / 2, cy = (r[1] + r[3]) / 2, c = Math.cos(ang), s = Math.sin(ang);
    return [[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]].map(function (q) {
      const x = q[0] - cx, y = q[1] - cy; return [cx + x * c - y * s, cy + dy + x * s + y * c]; });
  }
  function css(P) { return "polygon(" + P.map(function (q) { return q[0].toFixed(1) + "px " + q[1].toFixed(1) + "px"; }).join(", ") + ")"; }
  function draw() {
    const u = st.u, a = io(cl(u / 0.16)), p = io(cl((u - 0.2) / 0.58)), f = Math.max(0, u - 0.78);
    const r = mix(mix(A0, A1, a), B, p), bw = 14 * a;
    const ang = (3.4 * Math.sin(p * Math.PI) - 2.6 * p + 0.6 * Math.sin(f * 4.2)) * Math.PI / 180, dy = 6 * Math.sin(f * 3.3);
    const O = quad(r, ang, dy), W = quad([r[0] + bw, r[1] + bw, r[2] - bw, r[3] - bw], ang, dy);
    document.getElementById("mk-pp").setAttribute("points", O.map(function (q) { return q[0].toFixed(1) + "," + q[1].toFixed(1); }).join(" "));
    gsap.set("#mk-win", { clipPath: css(W) });
    const k = (W[1][1] - W[0][1]) / (W[1][0] - W[0][0]);
    const yl = W[0][1] + (-200 - W[0][0]) * k, yr = W[0][1] + (1280 - W[0][0]) * k;
    gsap.set("#mk-cut", { clipPath: css([[-200, -200], [1280, -200], [1280, yr], W[1], W[2], W[3], W[0], [-200, yl]]) });
  }
  draw();
  tl.fromTo(st, { u: 0 }, { u: $d, duration: $d, ease: "none", onUpdate: draw, immediateRender: false }, $t0);
})();"""


def e03(t0, d):  # Salir del marco (como Taki): la foto se encoge hasta el pecho y la cabeza sale por delante del borde, sobre negro con brillo azul
    cam(t0)
    inner = (bg("taki-head.jpg") +
             '<svg id="mk-paper" class="full" viewBox="0 0 1080 1920"><polygon id="mk-pp" points="0,0 1080,0 1080,1920 0,1920" fill="#FBFAF6"/></svg>'
             f'<div id="mk-win" class="full">{video_dup("mk-v", t0, d, FULL)}</div>'
             f'<div id="mk-cut" class="full">{video_dup("mk-c", t0, d, FULL, src=CUT)}</div>')
    html_front.append(f'<div id="marco" class="lay" style="z-index:5;opacity:0">{inner}</div>')
    js.append(f'tl.set("#marco", {{ opacity: 1 }}, {t0:.3f}); tl.set("#marco", {{ opacity: 0 }}, {t0 + d:.3f});')
    js.append(Template(MARCO_JS).substitute(t0=f"{t0:.3f}", d=f"{d:.3f}", by1=f"{min(FY + 300, 1360)}", by2=f"{min(FY + 822, 1880)}"))
    js.append(f'tl.fromTo("#mk-cut", {{ filter: "drop-shadow(0px 0px 0px rgba(0,0,0,0))" }}, '
              f'{{ filter: "drop-shadow(0px 28px 30px rgba(0,0,0,0.55))", duration: 0.5, ease: "power2.out", immediateRender: false }}, {t0 + 0.25:.3f});')
    add_sfx(t0 + 0.02, "click-soft", 0.14)
    add_sfx(t0 + 0.2, "whoosh-cinematic", 0.14)


def e04(t0, d):  # Zoom de golpe
    cam(t0)
    js.append(f'tl.fromTo(".cpunch", {{ scale: 1, filter: "blur(0px)" }}, {{ scale: 1.36, filter: "blur(3px)", duration: 0.09, ease: "power4.in", immediateRender: false }}, {t0 + 0.08:.3f});')
    js.append(f'tl.to(".cpunch", {{ filter: "blur(0px)", duration: 0.1 }}, {t0 + 0.17:.3f});')
    clip(html_front, "flash04", t0 + 0.12, 0.2, '<div class="flash"></div>')
    js.append(f'tl.fromTo("#flash04 .flash", {{ opacity: 0.35 }}, {{ opacity: 0, duration: 0.18 }}, {t0 + 0.12:.3f});')
    add_sfx(t0 + 0.08, "impact-bass-1", 0.16)


def e05(t0, d):  # Lista que aparece (como Taki): píldoras blancas que salen una a una a la derecha, con chispas naranjas antes
    cam(t0)
    inner = ""
    for k, r in enumerate(["Edición", "Subtítulos", "Efectos"]):
        y = 724 + 96 * k
        inner += f'<div id="ck-s{k}" class="cksp" style="top:{y + 16}px">{claude_logo(OR)}</div>'
        inner += f'<div id="ck-p{k}" class="ckpill" style="top:{y}px"><span class="ckc">{check_svg(OR)}</span>{r}</div>'
    clip(html_front, "check", t0, d, inner)
    for k in range(3):
        js.append(f'tl.fromTo("#ck-s{k}", {{ scale: 0, rotation: -90 }}, {{ scale: 1, rotation: 0, duration: 0.2, ease: "back.out(2)" }}, {t0 + 0.04 + 0.06 * k:.3f});')
        tp = t0 + 0.3 + 0.32 * k
        js.append(f'tl.to("#ck-s{k}", {{ scale: 0, duration: 0.1 }}, {tp:.3f});')
        js.append(f'tl.fromTo("#ck-p{k}", {{ scale: 0.5, opacity: 0, x: 30 }}, {{ scale: 1, opacity: 1, x: 0, duration: 0.24, ease: "back.out(2)" }}, {tp:.3f});')
        add_sfx(tp, "click", 0.15)


_HEADS_POS = [(40, 425, -5, "f", False), (430, 515, 5, "f", False), (-40, 615, 7, "b", True),  # (x, y, giro, detrás/delante, negra)
              (650, 725, -7, "f", False), (-300, 870, 4, "b", False), (-30, 1350, -5, "f", False)]
HEADS = [("ÚLTIMA HORA", "CLAUDE YA EDITA VÍDEO"), ("AHORA", f"{N} EFECTOS. UNA FRASE"), ("ÚLTIMA HORA", "EDITORES, EN ALERTA"),
         ("EXCLUSIVA", "CADA PALABRA, SUBTITULADA"), ("ÚLTIMA HORA", "SIN LÍNEA DE TIEMPO"), ("AHORA", "LO EDITA CLAUDE")]
if CFG.get("titulares"):  # seis pares [etiqueta, titular]
    HEADS = [(str(t[0]).upper(), str(t[1]).upper()) for t in CFG["titulares"][:6]]


def e06(t0, d):  # Lluvia de titulares (como Taki): tiras con etiqueta naranja que entran de lado; unas por detrás de la cabeza y otras delante
    cam(t0, fg=True)
    heads = [(tag, txt, x + DX, y + DY, r, layer, dark) for (tag, txt), (x, y, r, layer, dark) in zip(HEADS, _HEADS_POS)]
    back, front = "", ""
    for k, (tag, txt, x, y, r, layer, dark) in enumerate(heads):
        el = f'<div id="hd{k}" class="hstrip{" dark" if dark else ""}" style="left:{x}px;top:{y}px"><em>{tag}</em><b>{txt}</b></div>'
        if layer == "b":
            back += el
        else:
            front += el
        dx = -1400 if x < 300 else 1400
        js.append(f'tl.fromTo("#hd{k}", {{ x: {dx}, rotation: {r} }}, {{ x: 0, rotation: {r}, duration: 0.3, ease: "power3.out" }}, {t0 + 0.06 * k:.3f});')
    clip(html_back, "heads-b", t0, d, back)
    clip(html_front, "heads-f", t0, d, front)
    for k in range(0, 6, 2):
        add_sfx(t0 + 0.06 * k, "whoosh-short", 0.1)


def e07(t0, d):  # Portal (como Taki): círculo con aro naranja detrás de la cabeza y un plano abierto dentro; la cámara entra sin corte
    cam(t0, fg=True)
    R, s0, s1, K = 165, 0.34, 0.385, 7.2
    cx, cy = max(180, FX - 328), max(520, FY - 200)
    t1, t2 = t0 + 1.0, t0 + 1.42

    def fit(s):  # la cara, en el centro del círculo, a escala s
        return f"x: {R - FX * s:.1f}, y: {R - FY * s:.1f}, scale: {s:.4f}"
    inner = (f'<div id="pt" class="portal" style="left:{cx - R}px;top:{cy - R}px;width:{2 * R}px;height:{2 * R}px">'
             f'<div class="ptmask"><div id="pt-in" class="ptin"><i class="ptfill"></i>{video_dup("portal-v", t0, d, FULL)}</div><i class="ptvig"></i></div></div>')
    html_back.append(f'<div id="portal" class="lay" style="opacity:0">{inner}</div>')
    js.append(f'tl.set("#portal", {{ opacity: 1 }}, {t0:.3f}); tl.set("#portal", {{ opacity: 0 }}, {t2:.3f});')
    js.append(f'tl.set("#pt-in", {{ {fit(s0)} }}, {t0:.3f});')
    js.append(f'tl.fromTo("#pt", {{ scale: 0, x: 0, y: 0 }}, {{ scale: 1, duration: 0.32, ease: "back.out(1.7)" }}, {t0 + 0.02:.3f});')
    js.append(f'tl.fromTo("#pt-in", {{ {fit(s0)} }}, {{ {fit(s1)}, duration: {t1 - t0 - 0.3:.3f}, ease: "sine.inOut", immediateRender: false }}, {t0 + 0.3:.3f});')
    js.append(f'tl.set(".cpunch, .fpunch", {{ transformOrigin: "{cx}px {cy}px" }}, {t1:.3f});')
    js.append(f'tl.to("#pt", {{ x: {FX - cx}, y: {FY - cy}, duration: {t2 - t1:.3f}, ease: "power2.out" }}, {t1:.3f});')
    js.append(f'tl.to("#pt", {{ scale: {K}, duration: {t2 - t1:.3f}, ease: "power2.in" }}, {t1:.3f});')
    js.append(f'tl.to("#pt-in", {{ {fit(1 / K)}, duration: {t2 - t1:.3f}, ease: "power2.in" }}, {t1:.3f});')
    js.append(f'tl.to(".cpunch, .fpunch", {{ scale: 2.4, filter: "blur(10px)", duration: {t2 - t1:.3f}, ease: "power2.in" }}, {t1:.3f});')
    js.append(f'tl.to("#fg-box", {{ opacity: 0, duration: 0.14, ease: "power1.in" }}, {t1:.3f});')
    js.append(f'tl.set(".cpunch, .fpunch", {{ scale: 1, filter: "none", transformOrigin: "{FX}px {FY}px" }}, {t2:.3f});')
    add_sfx(t0 + 0.02, "pop", 0.16)
    add_sfx(t1, "whoosh-cinematic", 0.15)
    add_sfx(t2, "impact-bass-2", 0.08)


CURVE_JS = """(function () {
  const st = { p: 0 }; const path = document.getElementById("cv-p"); const L = path.getTotalLength();
  path.style.strokeDasharray = L + " " + L;
  function draw() {
    path.style.strokeDashoffset = L * (1 - st.p);
    const q = path.getPointAtLength(L * st.p);
    document.getElementById("cv-cr").setAttribute("width", q.x.toFixed(1));
    gsap.set("#cv-tip", { x: q.x - 13, y: q.y - 13 });
    document.getElementById("cv-v").textContent = String(Math.max(1, Math.round(Math.pow(10, st.p))));
  }
  draw();
  tl.fromTo(st, { p: 0 }, { p: 1, duration: $dur, ease: "power1.inOut", onUpdate: draw, immediateRender: false }, $t1);
})();"""


def e08(t0, d):  # Curva de crecimiento (como Taki): panel oscuro con rejilla, «DATOS DE EJEMPLO», curva naranja con relleno azul y contador 1× → 10×
    cam(t0, fg=True)
    P = "M 40 1110 C 220 1100, 330 1060, 450 980 S 760 700, 1010 470"
    inner = (f'<div id="cv-bg" class="full">{bg("taki-curve.jpg")}<div class="cvgrid"></div>'
             '<div class="cvlab"><i></i>DATOS DE EJEMPLO</div>'
             f'<svg class="full" viewBox="0 0 1080 1920"><defs><linearGradient id="cvg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BLUE}" stop-opacity="0.6"/>'
             f'<stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></linearGradient><clipPath id="cvc"><rect id="cv-cr" x="0" y="0" width="0" height="1920"/></clipPath></defs>'
             f'<path d="{P} L 1010 1520 L 40 1520 Z" fill="url(#cvg)" clip-path="url(#cvc)"/>'
             f'<path id="cv-p" d="{P}" fill="none" stroke="{OR}" stroke-width="10" stroke-linecap="round"/></svg>'
             '<div class="cvdot0"></div><div id="cv-tip" class="cvtip"></div>'
             '<div id="cv-n" class="cvbadge"><b><span id="cv-v">1</span>×</b><em>CRECIMIENTO</em></div></div>')
    clip(html_back, "curva", t0, d, inner)
    js.append(f'tl.fromTo("#cv-bg", {{ clipPath: "inset(0% 100% 0% 0%)" }}, {{ clipPath: "inset(0% 0% 0% 0%)", duration: 0.28, ease: "power2.out", immediateRender: false }}, {t0:.3f});')
    js.append(f'tl.fromTo("#cv-n", {{ scale: 0.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.22, ease: "back.out(2)" }}, {t0 + 0.18:.3f});')
    js.append(Template(CURVE_JS).substitute(t1=f"{t0 + 0.12:.3f}", dur=f"{d - 0.3:.3f}"))
    add_sfx(t0, "whoosh-short", 0.12)
    for tt in (0.45, 0.8, 1.1):
        add_sfx(t0 + tt, "ping", 0.08)


def e09(t0, d):  # Plató: la habitación se apaga, se enciende un foco y luego el otro (con parpadeo), luz de contra en la persona y EN DIRECTO
    cam(t0, fg=True)
    random.seed(9)
    motes = ""
    for k in range(16):
        w = random.choice((3, 4, 5, 6))
        motes += f'<i id="pm{k}" style="left:{random.randint(80, 1000)}px;top:{random.randint(520, 1250)}px;width:{w}px;height:{w}px;opacity:{random.uniform(.25, .6):.2f}"></i>'
        js.append(f'tl.fromTo("#pm{k}", {{ x: 0, y: 0 }}, {{ x: {random.uniform(-24, 24):.0f}, y: {-random.uniform(40, 130):.0f}, duration: {d - 0.5:.3f}, ease: "sine.inOut" }}, {t0 + 0.5:.3f});')
    inner = ('<div id="pl-w" class="full" style="opacity:0;transform-origin:540px 900px">'
             '<div class="full plimg" style="background-image:url(assets/kit/img/plato-off.jpg)"></div>'
             '<div id="pl-l" class="full plimg" style="background-image:url(assets/kit/img/plato-left.jpg);opacity:0"></div>'
             '<div id="pl-on" class="full plimg" style="background-image:url(assets/kit/img/plato.jpg);opacity:0"></div>'
             '<i id="pl-bl" class="bloom" style="left:84px;top:584px;width:196px;height:508px"></i>'
             '<i id="pl-br" class="bloom" style="left:812px;top:594px;width:196px;height:522px"></i>'
             '<i id="pl-hz" class="haze"></i>'
             f'<div id="pl-mt" class="motes">{motes}</div></div>'
             '<div id="pl-off" class="onair off">EN DIRECTO</div><div id="pl-sign" class="onair"><i></i>EN DIRECTO</div>')
    clip(html_back, "plato", t0, d, inner)
    off = "brightness(0.13) saturate(0.7)"
    left = "brightness(0.62) drop-shadow(0px 0px 1.5px rgba(255,214,190,0.6))"
    on = "brightness(1.04) contrast(1.06) drop-shadow(0px 0px 1.5px rgba(255,176,140,0.8)) drop-shadow(0px 0px 18px rgba(251,82,34,0.38))"
    js.append(f'tl.fromTo(".cpunch", {{ filter: "brightness(1)" }}, {{ filter: "brightness(0.1)", duration: 0.1, ease: "power2.in", immediateRender: false }}, {t0 + 0.02:.3f});')
    js.append(f'tl.fromTo("#cutout", {{ filter: "brightness(1) saturate(1)" }}, {{ filter: "{off}", duration: 0.1, ease: "power2.in", immediateRender: false }}, {t0 + 0.02:.3f});')
    js.append(f'tl.set("#pl-w", {{ opacity: 1 }}, {t0 + 0.12:.3f});')
    js.append(f'tl.fromTo("#pl-off", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.1 }}, {t0 + 0.12:.3f});')
    steps = [(0.30, 1, 0, "left"), (0.34, 0.2, 0, "off"), (0.37, 1, 0, "left"), (0.52, 1, 1, "on"), (0.56, 1, 0.35, "left"), (0.59, 1, 1, "on")]
    for tt, lv, rv, lit in steps:
        js.append(f'tl.set("#pl-l", {{ opacity: {lv} }}, {t0 + tt:.3f}); tl.set("#pl-bl", {{ opacity: {1 if lv == 1 else 0} }}, {t0 + tt:.3f});')
        js.append(f'tl.set("#pl-on", {{ opacity: {rv} }}, {t0 + tt:.3f}); tl.set("#pl-br", {{ opacity: {1 if rv == 1 else 0} }}, {t0 + tt:.3f});')
        js.append(f'tl.set("#cutout", {{ filter: "{dict(off=off, left=left, on=on)[lit]}" }}, {t0 + tt:.3f});')
    js.append(f'tl.fromTo("#pl-hz, #pl-mt", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "power1.out", immediateRender: false }}, {t0 + 0.52:.3f});')
    js.append(f'tl.fromTo("#pl-hz", {{ x: -40 }}, {{ x: 40, duration: {d - 0.52:.3f}, ease: "sine.inOut", immediateRender: false }}, {t0 + 0.52:.3f});')
    for tt, o in [(0.70, 1), (0.73, 0.15), (0.76, 1)]:
        js.append(f'tl.set("#pl-sign", {{ opacity: {o} }}, {t0 + tt:.3f});')
    js.append(f'tl.fromTo("#pl-sign i", {{ opacity: 1 }}, {{ opacity: 0.25, duration: 0.22, repeat: 3, yoyo: true, ease: "sine.inOut" }}, {t0 + 0.8:.3f});')
    js.append(f'tl.fromTo("#pl-w", {{ scale: 1 }}, {{ scale: 1.06, duration: {d - 0.52:.3f}, ease: "sine.out", immediateRender: false }}, {t0 + 0.52:.3f});')
    js.append(f'tl.fromTo(".fmove", {{ scale: 1 }}, {{ scale: 1.03, duration: {d - 0.52:.3f}, ease: "sine.out", immediateRender: false }}, {t0 + 0.52:.3f});')
    add_sfx(t0 + 0.27, "click", 0.16)
    add_sfx(t0 + 0.30, "impact-bass-2", 0.1)
    add_sfx(t0 + 0.52, "impact-bass-1", 0.12)
    add_sfx(t0 + 0.70, "click-soft", 0.12)


def e10(t0, d):  # Vídeo encima (como Taki): editor claro con la toma en el visor y debajo las pistas grandes; el recurso entra en V2 y sale encima
    PV = (394, 552, 292, 520)
    s = PV[2] / 1080
    cam(t0, box=PV, s=s, target=(PV[0] + FX * s, PV[1] + FY * s), z=3)
    ox, oy = PV[0] + PV[2] // 2, PV[1] + PV[3] // 2
    thumbs = "".join(f'<img src="assets/kit-gen/th{k % 10}.jpg"/>' for k in range(18))
    wave = "".join(f'<i style="height:{4 + int(28 * abs(math.sin(k * 0.37) * math.sin(k * 0.11 + 1.3)))}px"></i>' for k in range(130))
    back = (bg("taki-dark.jpg") + f'<div id="ed-w" class="full" style="transform-origin:{ox}px {oy}px">'
            '<div class="lw"></div><div class="lwbar"><i style="background:#FF5F57"></i><i style="background:#FEBC2E"></i><i style="background:#28C840"></i>'
            '<span>Editor · reel-20-efectos</span><em>Exportar</em></div>'
            '<div class="lwview"></div><div class="lwtag">VÍDEO ENCIMA · EDITOR</div>'
            f'<div class="lwtl"><div class="lwtr" style="top:12px"><b>V1</b><div class="lwstrip">{thumbs}</div></div>'
            f'<div class="lwtr" style="top:88px"><b>A1</b><div class="lwwave">{wave}</div></div><i id="ed-ph1" class="lwph"></i></div>'
            '<div class="bt"></div><div class="btl" style="top:1318px">V2</div><div class="btl" style="top:1388px">V1</div>'
            '<div id="ed-v2" class="btb or" style="left:330px;top:1314px;width:330px">Recurso</div>'
            '<div class="btb bl" style="left:150px;top:1384px;width:860px">Toma</div>'
            '<i id="ed-ph" class="btph"></i></div>')
    clip(html_back, "editor", t0, d, back)
    front = (f'<div id="ed-ov" class="eov" style="left:{PV[0] + 14}px;top:{PV[1] + 300}px;width:264px;height:200px">'
             f'<video id="ed-ovv" class="clip" src="{CFG.get('recurso', 'assets/kit/broll.mp4')}" data-start="{t0 + 0.42:.3f}" data-duration="{d - 0.42:.3f}" data-media-start="0" data-track-index="6" muted playsinline></video></div>')
    html_front.append(f'<div id="edf" class="lay" style="z-index:5;opacity:0;transform-origin:{ox}px {oy}px">{front}</div>')
    js.append(f'tl.set("#edf", {{ opacity: 1 }}, {t0:.3f}); tl.set("#edf", {{ opacity: 0 }}, {t0 + d:.3f});')
    js.append(f'tl.fromTo("#cam-box", {{ scale: 3.7, y: {960 - oy}, borderRadius: 0 }}, {{ scale: 1, y: 0, borderRadius: 10, duration: 0.36, ease: "power3.inOut", immediateRender: false }}, {t0:.3f});')
    js.append(f'tl.fromTo("#ed-w", {{ opacity: 0, scale: 1.05 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "power2.out", immediateRender: false }}, {t0 + 0.04:.3f});')
    js.append(f'tl.fromTo("#ed-ph", {{ x: 0 }}, {{ x: 560, duration: {d:.3f}, ease: "none" }}, {t0:.3f});')
    js.append(f'tl.fromTo("#ed-ph1", {{ x: 0 }}, {{ x: 600, duration: {d:.3f}, ease: "none" }}, {t0:.3f});')
    js.append(f'tl.fromTo("#ed-v2", {{ y: -70, opacity: 0, scale: 0.9 }}, {{ y: 0, opacity: 1, scale: 1, duration: 0.24, ease: "back.out(2)" }}, {t0 + 0.28:.3f});')
    js.append(f'tl.fromTo("#ed-ov", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.26, ease: "back.out(1.6)" }}, {t0 + 0.42:.3f});')
    js.append(f'tl.to("#ed-w, #edf, #cam-box", {{ scale: 1.08, duration: {d - 1.0:.3f}, ease: "sine.inOut" }}, {t0 + 1.0:.3f});')
    add_sfx(t0, "whoosh-short", 0.14)
    add_sfx(t0 + 0.28, "pop", 0.16)
    add_sfx(t0 + 0.42, "click-soft", 0.12)


def e11(t0, d):  # Recortable (como Taki): fondo naranja liso, estrella negra, círculo azul detrás de la cabeza, puntos y bandas; la persona como pegatina
    cam(t0, fg=True)
    star = f'<svg viewBox="0 0 100 100"><path d="M50 4 L62 38 L98 38 L69 59 L80 94 L50 73 L20 94 L31 59 L2 38 L38 38 Z" fill="{INK}"/></svg>'
    back = (f'<div class="full" style="background:{OR}"></div>'
            '<div id="rc-bw" class="rcband" style="left:-160px;top:1150px;width:520px;background:#FFFFFF"></div>'
            f'<div id="rc-bk" class="rcband" style="left:700px;top:1050px;width:600px;background:{INK}"></div>'
            f'<div id="rc-ci" class="rcp" style="left:{660 + DX}px;top:{355 + DY}px;width:400px;height:400px;border-radius:50%;background:{BLUE}"></div>'
            f'<div id="rc-st" class="rcp" style="left:70px;top:486px;width:236px;height:236px">{star}</div>'
            f'<div id="rc-d1" class="rcp" style="left:83px;top:929px;width:56px;height:56px;border-radius:50%;background:{BLUE}"></div>'
            '<div id="rc-d2" class="rcp" style="left:934px;top:936px;width:90px;height:90px;border-radius:50%;background:#FFFFFF"></div>')
    clip(html_back, "recortable", t0, d, back)
    white = "drop-shadow(13px 0px 0px #fff) drop-shadow(-13px 0px 0px #fff) drop-shadow(0px 13px 0px #fff) drop-shadow(0px -13px 0px #fff)"
    js.append(f'tl.fromTo("#cutout", {{ filter: "{white} drop-shadow(0px 46px 34px rgba(40,10,0,0.26))" }}, '
              f'{{ filter: "{white} drop-shadow(0px 14px 18px rgba(40,10,0,0.42))", duration: 0.3, ease: "power2.out", immediateRender: false }}, {t0:.3f});')
    js.append(f'tl.fromTo(".fmove", {{ scale: 1.12, rotation: -4 }}, {{ scale: 1, rotation: 0, duration: 0.3, ease: "back.out(1.4)", immediateRender: false }}, {t0:.3f});')
    js.append(f'tl.fromTo("#rc-ci", {{ scale: 0 }}, {{ scale: 1, duration: 0.3, ease: "back.out(1.7)" }}, {t0 + 0.04:.3f});')
    js.append(f'tl.fromTo("#rc-st", {{ scale: 0, rotation: -60 }}, {{ scale: 1, rotation: 0, duration: 0.3, ease: "back.out(2)" }}, {t0 + 0.1:.3f});')
    js.append(f'tl.fromTo("#rc-d1, #rc-d2", {{ scale: 0 }}, {{ scale: 1, duration: 0.22, ease: "back.out(3)", stagger: 0.06 }}, {t0 + 0.18:.3f});')
    js.append(f'tl.fromTo("#rc-bw", {{ x: -700, rotation: -15 }}, {{ x: 0, rotation: -15, duration: 0.3, ease: "power3.out" }}, {t0 + 0.08:.3f});')
    js.append(f'tl.fromTo("#rc-bk", {{ x: 760, rotation: -15 }}, {{ x: 0, rotation: -15, duration: 0.3, ease: "power3.out" }}, {t0 + 0.12:.3f});')
    add_sfx(t0, "pop", 0.16)
    add_sfx(t0 + 0.1, "click-soft", 0.12)


def e12(t0, d):  # Efecto vértigo: el fondo se acerca y la persona se queda igual
    cam(t0, fg=True)
    clip(html_back, "vertigo", t0, d, '<div id="vt-pl" class="full" style="background:url(assets/kit-gen/plate.jpg) center/cover;transform-origin:566px 900px"></div>')
    js.append(f'tl.fromTo("#vt-pl", {{ scale: 1, filter: "blur(1px)" }}, {{ scale: 1.38, filter: "blur(5px)", duration: {d:.3f}, ease: "power1.inOut" }}, {t0:.3f});')
    js.append(f'tl.fromTo(".fmove", {{ scale: 1 }}, {{ scale: 0.96, duration: {d:.3f}, ease: "power1.inOut", immediateRender: false }}, {t0:.3f});')
    add_sfx(t0, "riser", 0.06)


def e13(t0, d):  # Portada de revista (como Taki): fondo crema, cabecera naranja detrás de la cabeza, «20» grande, titulares a la derecha y código de barras
    cam(t0, fg=True)
    bars = "".join(f'<i style="width:{[3, 1, 2, 1, 4, 1, 2, 3, 1, 2][k % 10]}px"></i>' for k in range(34))
    back = ('<div class="full" style="background:#ECEBE0"></div><div class="grain"></div>'
            '<div id="mg-top" class="mgtop"><span>EL NÚMERO DE LA IA</span><span>Nº 30 · OCT 2026</span></div>'
            f'<div id="mg-mast" class="mast2">{CFG.get("marca", "TU MARCA").upper()}</div>'
            f'<div id="mg-l" class="mgleft"><em>PORTADA</em><b id="mg-20">{N}</b><span><i>Un prompt.</i><i>Sin editor.</i></span></div>')
    front = ('<div id="mg-r" class="mgright"><em>DENTRO</em><b><i>CLAUDE</i><i>EDITA</i><i>VÍDEO</i></b><span><i>Cada palabra,</i><i>subtitulada.</i></span></div>'
             f'<div id="mg-bc" class="barcode2"><div class="bars">{bars}</div><span>0 30 2026 10</span></div>')
    clip(html_back, "rev-b", t0, d, back)
    clip(html_front, "rev-f", t0, d, front)
    js.append(f'tl.fromTo("#mg-mast", {{ y: -70, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.28, ease: "power3.out" }}, {t0:.3f});')
    js.append(f'tl.fromTo("#mg-top", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, {t0 + 0.1:.3f});')
    js.append(f'tl.fromTo("#mg-l", {{ x: -60, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.24, ease: "power3.out" }}, {t0 + 0.22:.3f});')
    js.append(f'tl.fromTo("#mg-r", {{ x: 60, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.24, ease: "power3.out" }}, {t0 + 0.3:.3f});')
    js.append(f'tl.fromTo("#mg-20", {{ scale: 0.5 }}, {{ scale: 1, duration: 0.3, ease: "back.out(2.2)" }}, {t0 + 0.45:.3f});')
    js.append(f'tl.fromTo("#mg-bc", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.2 }}, {t0 + 0.5:.3f});')
    add_sfx(t0, "click", 0.16)
    add_sfx(t0 + 0.45, "pop", 0.14)


def e14(t0, d):  # Cristal líquido (como Taki): una lente pequeña que pasa por la cara y la amplía
    cam(t0)
    R, m = 150, 1.4
    y0 = FY - 40 - R
    vid = video_dup("lens-v", t0, d, "position:absolute;left:0;top:0;width:1080px;height:1920px;transform-origin:0 0;")
    inner = f'<div id="ln" class="lens" style="top:{y0}px;width:{2 * R}px;height:{2 * R}px"><div id="ln-in" class="lnin">{vid}</div><div class="lnhl"></div></div>'
    html_front.append(f'<div id="lens" class="lay" style="z-index:5;opacity:0">{inner}</div>')
    js.append(f'tl.set("#lens", {{ opacity: 1 }}, {t0:.3f}); tl.set("#lens", {{ opacity: 0 }}, {t0 + d:.3f});')
    lx0, lx1 = -2 * R - 40, 1080 + 40
    js.append(f'gsap.set("#ln-in", {{ scale: {m} }});')
    js.append(f'tl.fromTo("#ln", {{ x: {lx0} }}, {{ x: {lx1}, duration: {d:.3f}, ease: "power1.inOut" }}, {t0:.3f});')
    js.append(f'tl.fromTo("#ln-in", {{ x: {R * (1 - m) - m * lx0:.1f}, y: {R * (1 - m) - m * y0:.1f} }}, {{ x: {R * (1 - m) - m * lx1:.1f}, y: {R * (1 - m) - m * y0:.1f}, duration: {d:.3f}, ease: "power1.inOut" }}, {t0:.3f});')
    add_sfx(t0, "whoosh", 0.1)


def e15(t0, d):  # Zoom y corte
    cam(t0)
    js.append(f'tl.fromTo(".cpunch", {{ scale: 1, filter: "blur(0px)" }}, {{ scale: 2.4, filter: "blur(8px)", duration: 0.42, ease: "power3.in", immediateRender: false }}, {t0 + 0.05:.3f});')
    js.append(f'tl.set(".cpunch", {{ scale: 1, filter: "blur(0px)" }}, {t0 + 0.5:.3f});')
    clip(html_front, "flash15", t0 + 0.47, 0.25, '<div class="flash"></div>')
    js.append(f'tl.fromTo("#flash15 .flash", {{ opacity: 0.6 }}, {{ opacity: 0, duration: 0.22 }}, {t0 + 0.47:.3f});')
    add_sfx(t0 + 0.05, "whoosh-cinematic", 0.14)
    add_sfx(t0 + 0.5, "glitch-1", 0.1)


def e16(t0, d):  # Croma (como Taki): fondo de tela verde con pliegues detrás de la persona
    cam(t0, fg=True)
    clip(html_back, "croma", t0, d, '<div id="cr-g" class="full" style="background:url(assets/kit/img/taki-green.jpg) center/cover;transform-origin:540px 900px"></div>')
    js.append(f'tl.fromTo("#cr-g", {{ scale: 1.08 }}, {{ scale: 1, duration: 0.4, ease: "power2.out" }}, {t0:.3f});')
    add_sfx(t0, "whoosh-short", 0.12)


def cracks_svg(px, py):
    """Grietas que salen de un punto: rayos quebrados y dos anillos rotos. Devuelve el SVG y la longitud de cada trazo."""
    random.seed(170)
    paths = []
    for k in range(10):
        ang = k * 2 * math.pi / 10 + random.uniform(-0.25, 0.25)
        x, y, pts, length = px, py, [(px, py)], 0.0
        for _ in range(random.randint(4, 7)):
            step = random.uniform(70, 160)
            ang += random.uniform(-0.35, 0.35)
            x, y = x + step * math.cos(ang), y + step * math.sin(ang)
            pts.append((x, y)); length += step
        paths.append(("M " + " L ".join(f"{a:.0f} {b:.0f}" for a, b in pts), length))
    for r in (70, 150):
        a0 = random.uniform(0, 6.3)
        for j in range(6):
            a, b = a0 + j * 1.05, a0 + j * 1.05 + random.uniform(0.35, 0.7)
            p1 = (px + r * math.cos(a), py + r * math.sin(a)); p2 = (px + r * math.cos(b), py + r * math.sin(b))
            paths.append((f"M {p1[0]:.0f} {p1[1]:.0f} L {p2[0]:.0f} {p2[1]:.0f}", math.dist(p1, p2)))
    body = "".join(f'<path class="crk" d="{dd}" stroke-dasharray="{ln:.0f}" stroke-dashoffset="{ln:.0f}"/>' for dd, ln in paths)
    return f'<svg class="full cracks" viewBox="0 0 1080 1920"><g fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>', [ln for _, ln in paths]


def e17(t0, d):  # Cristal roto (como Taki): ciudad plana al atardecer, grietas por delante de la persona y la imagen entera se rompe en trozos
    cam(t0, fg=True)
    tb = t0 + 0.42  # rotura (assets/kit-gen/roto-still.jpg es la ciudad con la persona en este instante)
    svg, lens = cracks_svg(min(max(765 + DX, 200), 880), min(max(1185 + DY, 600), 1600))
    clip(html_back, "roto", t0, tb - t0, bg("taki-city.jpg"))
    clip(html_front, "roto-cr", t0, tb - t0 + 0.04, svg)
    js.append(f'tl.to("#roto-cr .crk", {{ attr: {{ "stroke-dashoffset": 0 }}, duration: 0.22, ease: "power2.out", stagger: 0.012 }}, {t0 + 0.1:.3f});')
    random.seed(17)
    cols, rows = 3, 4
    pts = {}
    for i in range(cols + 1):
        for j in range(rows + 1):
            x, y = i * 1080 / cols, j * 1920 / rows
            if 0 < i < cols:
                x += random.uniform(-110, 110)
            if 0 < j < rows:
                y += random.uniform(-110, 110)
            pts[(i, j)] = (x, y)
    shards, k = "", 0
    for i in range(cols):
        for j in range(rows):
            a, b, c, dd = pts[(i, j)], pts[(i + 1, j)], pts[(i + 1, j + 1)], pts[(i, j + 1)]
            for tri in ((a, b, c), (a, c, dd)):
                poly = ",".join(f"{p[0]:.0f}px {p[1]:.0f}px" for p in tri)
                cx = sum(p[0] for p in tri) / 3
                cy = sum(p[1] for p in tri) / 3
                shards += f'<div id="sh{k}" class="shard" style="clip-path:polygon({poly});transform-origin:{cx:.0f}px {cy:.0f}px"></div>'
                vx, vy = (cx - 765) * 1.5, (cy - 1185) * 1.2 + 520
                js.append(f'tl.fromTo("#sh{k}", {{ x: 0, y: 0, rotation: 0, opacity: 1 }}, {{ x: {vx:.0f}, y: {vy:.0f}, rotation: {random.uniform(-80, 80):.0f}, opacity: 0, duration: 0.75, ease: "power2.in" }}, {tb + random.uniform(0, 0.1):.3f});')
                k += 1
    clip(html_front, "roto-sh", tb, d - (tb - t0), shards)
    js.append(f'tl.set("#fg-box", {{ opacity: 0 }}, {tb:.3f});')
    clip(html_front, "flash17", tb, 0.22, '<div class="flash"></div>')
    js.append(f'tl.fromTo("#flash17 .flash", {{ opacity: 0.5 }}, {{ opacity: 0, duration: 0.2 }}, {tb:.3f});')
    add_sfx(t0 + 0.1, "click", 0.14)
    add_sfx(tb, "impact-bass-1", 0.18)
    add_sfx(tb + 0.02, "glitch-2", 0.1)


def e18(t0, d):  # Zoom de cámara (como Taki): visor con REC, zoom en una cápsula arriba, marco de enfoque naranja y líneas de barrido
    cam(t0)
    vals = ["1.0×", "1.6×", "2.2×", "2.6×"]
    inner = ('<div id="vf-scan" class="scan"></div><div class="vf2"><i class="c1"></i><i class="c2"></i><i class="c3"></i><i class="c4"></i></div>'
             '<div id="vf-rec" class="rec2"><i></i>REC</div><div class="tc2">00:00:30:12</div>'
             '<div class="zpill">' + "".join(f'<span id="zt{k}">{v}</span>' for k, v in enumerate(vals)) + f'</div><div class="focus2" style="left:{436 + DX}px;top:{785 + DY}px"></div>')
    clip(html_front, "visor", t0, d, inner)
    for k, tt in enumerate((0.0, 0.3, 0.75, 1.15)):
        sc = float(vals[k][:-1])
        js.append(f'tl.to(".cpunch", {{ scale: {sc}, duration: 0.14, ease: "power2.out" }}, {t0 + tt:.3f});')
        if k:
            js.append(f'tl.fromTo(".cpunch", {{ filter: "blur(6px)" }}, {{ filter: "blur(0px)", duration: 0.22, immediateRender: false }}, {t0 + tt:.3f});')
            add_sfx(t0 + tt, "click-soft", 0.14)
        js.append(f'tl.set(".zpill span", {{ opacity: 0 }}, {t0 + tt:.3f}); tl.set("#zt{k}", {{ opacity: 1 }}, {t0 + tt:.3f});')
        js.append(f'tl.fromTo("#zt{k}", {{ scale: 1.25 }}, {{ scale: 1, duration: 0.15, ease: "power2.out", immediateRender: false }}, {t0 + tt:.3f});')
    js.append(f'tl.fromTo("#vf-scan", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, {t0 + 0.3:.3f});')
    js.append(f'tl.fromTo("#vf-rec i", {{ opacity: 1 }}, {{ opacity: 0.2, duration: 0.25, repeat: 5, yoyo: true }}, {t0:.3f});')


IG = {
    "heart": '<svg viewBox="0 0 24 24"><path d="M12 20.5s-7.4-4.5-9.3-9C1.4 8.4 3.3 5 6.8 5c2 0 3.6 1.1 5.2 3.1C13.6 6.1 15.2 5 17.2 5c3.5 0 5.4 3.4 4.1 6.5-1.9 4.5-9.3 9-9.3 9z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>',
    "chat": '<svg viewBox="0 0 24 24"><path d="M20.6 16.2A9 9 0 1 0 17 19.8L21 21z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>',
    "send": '<svg viewBox="0 0 24 24"><path d="M21.5 3 9.6 13.2M21.5 3 15 21l-3.6-7.9L3 9.6z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>',
    "cam": '<svg viewBox="0 0 24 24"><path d="M3 8.5A2.5 2.5 0 0 1 5.5 6H8l1.6-2h4.8L16 6h2.5A2.5 2.5 0 0 1 21 8.5v9a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 17.5z" fill="none" stroke="#fff" stroke-width="2"/><circle cx="12" cy="12.5" r="3.6" fill="none" stroke="#fff" stroke-width="2"/></svg>',
}


def e19(t0, d):  # Dentro del móvil (como Taki): la toma se encoge hasta un móvil con la interfaz de Reels, sobre fondo oscuro
    scr = (262, 450, 556, 988)  # pantalla 9:16: la toma entera, sin recortar los lados (la persona, NUEVE v3)
    s = scr[2] / 1080
    cam(t0, box=scr, s=s, target=(scr[0] + FX * s, scr[1] + FY * s), z=3, radius=54)
    k0, dy = 1080 / scr[2], 960 - (scr[1] + scr[3] / 2)
    ui = (f'<div id="ph-ui" class="phui"><b class="phr">Reels</b><i class="phcam">{IG["cam"]}</i>'
          f'<div class="phside"><i>{IG["heart"]}</i><i>{IG["chat"]}</i><i>{IG["send"]}</i><i class="dots3">•••</i></div>'
          f'<div class="phuser"><img src="assets/kit-gen/avatar.png"/><b>{CFG.get("usuario", "tu_usuario")}</b><em>Seguir</em></div>'
          f'<div class="phcap">{" ".join(TITULO)}</div><div class="phbar"><i id="ph-pg"></i></div></div>')
    clip(html_back, "movil-b", t0, d, bg("taki-dark.jpg"))
    clip(html_front, "movil-f", t0, d, f'<div id="ph" class="phone" style="left:{scr[0] - 20}px;top:{scr[1] - 20}px;width:{scr[2] + 40}px;height:{scr[3] + 40}px">'
                                        f'<i class="island"></i><i class="btn b1"></i><i class="btn b2"></i><i class="btn b3"></i>{ui}</div>')
    for sel in ("#ph", "#cam-box"):
        js.append(f'tl.fromTo("{sel}", {{ scale: {k0:.4f}, y: {dy:.0f}, rotation: 0 }}, {{ scale: 1, y: 0, duration: 0.42, ease: "power3.inOut", immediateRender: false }}, {t0:.3f});')
        js.append(f'tl.to("{sel}", {{ rotation: -2.5, y: -10, duration: {d - 0.42:.3f}, ease: "sine.inOut" }}, {t0 + 0.42:.3f});')
    js.append(f'tl.fromTo("#ph-ui", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2, ease: "power1.out", immediateRender: false }}, {t0 + 0.32:.3f});')
    js.append(f'tl.fromTo("#ph-pg", {{ scaleX: 0.15 }}, {{ scaleX: 0.45, duration: {d:.3f}, ease: "none" }}, {t0:.3f});')
    js.append(f'tl.fromTo("#ph .phside i:first-child", {{ scale: 1 }}, {{ scale: 1.3, duration: 0.12, yoyo: true, repeat: 1, ease: "power2.out", immediateRender: false }}, {t0 + 0.9:.3f});')
    add_sfx(t0, "whoosh-short", 0.15)
    add_sfx(t0 + 0.9, "pop", 0.1)


def e20(t0, d):  # Lista final (como Taki): número naranja grande que sube y las 20 casillas marcándose una a una
    cam(t0)
    rows = ""
    per = max(1, math.ceil(N / 2))
    for k, nm in enumerate(NAMES):
        col, row = k // per, k % per
        rows += f'<div class="lfr2" style="left:{66 + 494 * col}px;top:{660 + 66 * row}px"><span class="lfb2"></span><span id="lf-c{k}" class="lfc2">{SQCHECK}</span>{nm}</div>'
    cnt = "".join(f'<span id="lf-n{k}" class="lfn">{k}</span>' for k in range(N + 1))
    inner = bg("taki-dark.jpg") + f'<div class="lfnum">{cnt}</div><div class="lftx"><b>/ {N} efectos.</b><b>{CFG.get("lista_final", "Todos hechos por Claude.")}</b></div>{rows}'
    clip(html_front, "listafin", t0, d, inner, z=7)
    js.append(f'tl.set(".lfn", {{ display: "none" }}, {t0:.3f});')
    js.append(f'tl.set("#lf-n0", {{ display: "inline-block" }}, {t0:.3f});')
    step = min(0.075, max(0.03, (d - 0.5) / max(1, N)))
    for k in range(N):
        tt = t0 + 0.25 + step * k
        js.append(f'tl.fromTo("#lf-c{k}", {{ scale: 0 }}, {{ scale: 1, duration: 0.12, ease: "back.out(3)" }}, {tt:.3f});')
        js.append(f'tl.set("#lf-n{k}", {{ display: "none" }}, {tt:.3f});')
        js.append(f'tl.set("#lf-n{k + 1}", {{ display: "inline-block" }}, {tt:.3f});')
        if k % 4 == 0:
            add_sfx(tt, "click-soft", 0.1)
    add_sfx(t0 + 0.25 + step * N, "sparkle", 0.16)


# ---------------------------------------------------------------- CTA (como Taki: caja de texto arriba, app a pantalla completa, comentario y perfil)
def ct(k, frac):
    """Momento del cierre: el de config.json o, si falta, un reparto proporcional hasta el final."""
    v = CIERRE.get(k)
    return float(v) if v is not None else float(CIERRE["inicio"]) + frac * (DUR - float(CIERRE["inicio"]))


def cta():
    t0 = float(CIERRE["inicio"])
    t_ed, t_vid, t_pide, t_edita = ct("editor", 0.11), ct("video", 0.29), ct("pide", 0.37), ct("edita", 0.49)
    t2, t_pal, t_env, t3, t_fin = ct("comenta", 0.55), ct("palabra", 0.61), ct("enviado", 0.66), ct("sigueme", 0.73), ct("final", 0.95)
    pal = CFG.get("palabra", "EDITOR")
    cam(t0)
    side_lists("ct", t0, min(1.6, t_ed - t0), stagger=0.02, start=0.0)
    js.append(f'tl.to("#ct-lists .li", {{ opacity: 0, duration: 0.15 }}, {min(t0 + 1.4, t_ed - 0.2):.3f});')
    lines = CFG.get("texto_cierre", [f"Comenta {pal} y te mando", f"los {N} efectos y el", "editor con IA 🚀"])
    clip(html_front, "cta-top", t0, t3 - t0, tbox("cta", lines, ' id="ct-top"'), z=8)
    js.append(f'tl.fromTo("#ct-top", {{ y: -30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(1.6)" }}, {t0 + 0.06:.3f});')

    # Claude Code en la carpeta del vídeo: llega el archivo, se escribe la frase y devuelve el vídeo editado
    frase = CFG.get("frase", f"Edítalo con mi estilo y ponle los {N} efectos")
    spans = "".join(f'<span id="cc-c{k}" class="pc">{c}</span>' for k, c in enumerate(frase))
    archivo = CFG.get("archivo", "toma-en-bruto.mov")
    items = CFG.get("chat_lista", ["Quito las pausas", "Subtitulo cada palabra", f"Añado los {N} efectos"])
    rows = "".join(f'<div id="cc-r{j}" class="ccr" style="top:{900 + 52 * j}px"><span class="chb">{SPIN}</span><span id="cc-c{j}x" class="chc">{check_svg(OR)}</span>{t}</div>'
                   for j, t in enumerate(items))
    inner = (bg("taki-dark.jpg") +
             '<div id="cc-w" class="full" style="transform-origin:540px 990px"><i id="cc-glow" class="ccglow"></i><div class="ccwin"></div>'
             f'<div class="cchd"><i style="background:#FF5F57"></i><i style="background:#FEBC2E"></i><i style="background:#28C840"></i><b>{claude_logo()}Claude Code</b><em>📁 mis-vídeos</em></div>'
             f'<div id="cc-hi" class="cchi">{claude_logo()}<span>¿Qué editamos hoy?</span></div>'
             f'<div id="cc-me" class="ccme"><div class="ccatt"><i>{ICONS["play"]}</i>{archivo}</div><span>{frase}</span></div>'
             f'<div id="cc-av" class="ccav">{claude_logo()}</div><div id="cc-ok" class="ccok">Vale, me pongo.</div>{rows}'
             f'<div id="cc-res" class="ccres"><img src="assets/kit-gen/resultado.jpg"/><div><b>reel-editado.mp4</b><span>{check_svg(OR)}Listo para publicar</span></div></div>'
             f'<div id="cc-file" class="ccfile"><i>{ICONS["play"]}</i><b>{archivo}</b><small>EN BRUTO</small></div>'
             f'<div class="ccin"><span id="cc-ph">Pídele a Claude…</span><span id="cc-tx">{spans}</span><i id="cc-caret" class="caret a"></i><b id="cc-send">{SEND}</b></div></div>')
    clip(html_back, "app", t_ed, t2 - t_ed, inner)
    t_send = max(t_pide + 0.6, t_edita - 0.42)
    step = min(0.06, max(0.01, (t_send - 0.04 - (t_pide + 0.12)) / max(1, len(frase))))
    js.append(f'tl.fromTo("#cc-w", {{ y: 50, opacity: 0, scale: 0.95 }}, {{ y: 0, opacity: 1, scale: 1, duration: 0.34, ease: "back.out(1.5)" }}, {t_ed:.3f});')
    js.append(f'tl.fromTo("#cc-glow", {{ opacity: 0 }}, {{ opacity: 0.8, duration: 0.4 }}, {t_ed + 0.1:.3f});')
    js.append(f'tl.fromTo("#cc-file", {{ x: 360, y: -420, rotation: 14, opacity: 0 }}, {{ x: 0, y: 0, rotation: 0, opacity: 1, duration: 0.42, ease: "power3.out" }}, {t_vid - 0.1:.3f});')
    js.append(f'tl.set("#cc-ph", {{ display: "none" }}, {t_pide + 0.1:.3f});')
    for k in range(len(frase)):
        js.append(f'tl.set("#cc-c{k}", {{ display: "inline" }}, {t_pide + 0.12 + step * k:.3f});')
    js.append(f'tl.fromTo("#cc-caret", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.2, repeat: 6, yoyo: true }}, {t_pide:.3f});')
    js.append(f'tl.fromTo("#cc-send", {{ scale: 1 }}, {{ scale: 0.82, duration: 0.08, yoyo: true, repeat: 1 }}, {t_send:.3f});')
    js.append(f'tl.to("#cc-file, #cc-tx, #cc-caret, #cc-hi", {{ opacity: 0, duration: 0.1 }}, {t_send + 0.04:.3f});')
    js.append(f'tl.fromTo("#cc-me", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.22, ease: "power2.out" }}, {t_send + 0.06:.3f});')
    js.append(f'tl.fromTo("#cc-av, #cc-ok", {{ opacity: 0, y: 8 }}, {{ opacity: 1, y: 0, duration: 0.14, ease: "power2.out" }}, {t_send + 0.22:.3f});')
    for j in range(len(items)):
        ta = t_send + 0.32 + 0.15 * j
        js.append(f'tl.fromTo("#cc-r{j}", {{ opacity: 0, x: -14 }}, {{ opacity: 1, x: 0, duration: 0.12, ease: "power2.out" }}, {ta:.3f});')
        js.append(f'tl.fromTo("#cc-r{j} .chb", {{ rotation: 0 }}, {{ rotation: 360, duration: 0.3, ease: "none" }}, {ta:.3f});')
        js.append(f'tl.fromTo("#cc-c{j}x", {{ scale: 0 }}, {{ scale: 1, duration: 0.12, ease: "back.out(3)" }}, {ta + 0.1:.3f});')
        add_sfx(ta + 0.1, "click-soft", 0.12)
    t_res = t_send + 0.32 + 0.15 * len(items) + 0.05
    js.append(f'tl.fromTo("#cc-res", {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.24, ease: "back.out(1.8)" }}, {t_res:.3f});')
    add_sfx(t_ed, "whoosh-short", 0.14)
    add_sfx(t_vid + 0.02, "pop", 0.16)
    add_sfx(t_pide + 0.12, "typing", 0.12)
    add_sfx(t_send, "click-soft", 0.14)
    add_sfx(t_res, "chime", 0.14)

    # «comenta PALABRA»: caja de comentario encima de la caja de texto
    cam(t2)
    pal_spans = "".join(f'<span id="cm-ch{k}" class="pc">{c}</span>' for k, c in enumerate(pal))
    inner = (f'<div id="cm" class="cbox2"><img src="assets/kit-gen/avatar.png"/><div class="ctx2"><i id="cm-ph">Añade un comentario…</i>{pal_spans}</div>'
             f'<span id="cm-ok" class="aptag2">{TICK}ENVIADO</span><b id="cm-send" class="csend">{SEND}</b></div>')
    clip(html_front, "coment", t2, t3 - t2, inner, z=8)
    js.append(f'tl.fromTo("#cm", {{ opacity: 0, y: -30, scale: 0.92 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.3, ease: "back.out(1.8)" }}, {t2 + 0.02:.3f});')
    js.append(f'tl.set("#cm-ph", {{ display: "none" }}, {t_pal:.3f});')
    for k in range(len(pal)):
        js.append(f'tl.set("#cm-ch{k}", {{ display: "inline" }}, {t_pal + 0.08 * k:.3f});')
    js.append(f'tl.fromTo("#cm-send", {{ scale: 1 }}, {{ scale: 0.8, duration: 0.08, yoyo: true, repeat: 1 }}, {t_env:.3f});')
    js.append(f'tl.fromTo("#cm-ok", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.2, ease: "back.out(2.5)" }}, {t_env + 0.06:.3f});')
    add_sfx(t_pal, "typing", 0.12)
    add_sfx(t_env, "click", 0.16)

    # «sígueme»: la ficha de perfil
    cam(t3)
    usuario, nombre, bio = CFG.get("usuario", "tu_usuario"), CFG.get("nombre", "Tu nombre"), CFG.get("bio", "")
    ver = VERIFIED if CFG.get("verificado") else ""
    sub2 = f"{nombre} · {bio}" if bio else nombre
    inner = (f'<div id="pf" class="prof"><img src="assets/kit-gen/avatar.png"/><div><b>{usuario}{ver}</b>'
             f'<em>{sub2}</em></div><span id="pf-f" class="pfollow">Seguir</span></div>')
    clip(html_front, "perfil", t3, DUR - t3, inner, z=8)
    js.append(f'tl.fromTo("#pf", {{ y: -40, opacity: 0, scale: 0.92 }}, {{ y: 0, opacity: 1, scale: 1, duration: 0.32, ease: "back.out(1.7)" }}, {t3 + 0.1:.3f});')
    js.append(f'tl.fromTo("#pf-f", {{ scale: 1 }}, {{ scale: 1.15, duration: 0.16, yoyo: true, repeat: 1, ease: "power2.out" }}, {t_fin:.3f});')
    add_sfx(t3 + 0.1, "pop", 0.14)
    add_sfx(t_fin, "click-soft", 0.14)


# ---------------------------------------------------------------- subtítulos palabra a palabra (todo el vídeo)
def captions():
    """Una palabra cada vez, en blanco con contorno negro, con los tiempos de whisper.cpp (-ml 1 -sow -ojf)."""
    raw = [w for w in json.load(open(os.path.join(ROOT, CFG.get("palabras", "assets/palabras.json"))))["transcription"] if w["text"].strip()]
    ws = []
    for w in raw:
        txt = re.sub(r"[,.;:¿?¡!…]", "", w["text"].strip())
        if txt:
            ws.append((w["offsets"]["from"] / 1000 + 0.06, txt))  # con --dtw, el inicio llega ~0,1 s antes de que suene
    out = []
    for k, (t, txt) in enumerate(ws):
        a = 0.0 if k == 0 else t - 0.02
        nxt = ws[k + 1][0] - 0.02 if k + 1 < len(ws) else DUR
        b = min(nxt, t + 1.2, DUR)
        if b - a < 0.06:
            continue
        out.append(f'<div id="cp{k}" class="clip cap" data-start="{a:.3f}" data-duration="{b - a:.3f}" data-track-index="9"><span><b>{txt}</b><i>{txt}</i></span></div>')
        if a > 0.01:
            js.append(f'tl.fromTo("#cp{k} span", {{ scale: 0.88 }}, {{ scale: 1, duration: 0.1, ease: "back.out(2.5)" }}, {a:.3f});')
    return "\n".join(out)


def sfx_html():
    mf = os.path.join(ROOT, "assets", "kit", "sfx", "manifest.json")
    if not os.path.exists(mf):  # sin las skills de Hyperframes no hay sonidos; el vídeo sale igual, solo con la voz
        return ""
    man = json.load(open(mf))
    out = []
    for k, (t, name, vol) in enumerate(sorted(sfx)):
        if name not in man:
            continue
        d = min(man[name]["duration"], DUR - t - 0.01, 2.0)
        out.append(f'<audio id="sfx-{k:02d}" src="assets/kit/sfx/{man[name]["file"]}" data-start="{t:.3f}" data-duration="{d:.3f}" data-track-index="{11 + k}" data-volume="{vol}"></audio>')
    return "\n      ".join(out)


# ---------------------------------------------------------------- recursos del kit y los que salen del vídeo del usuario
REG = {"orbita": e01, "chat": e02, "marco": e03, "zoom_golpe": e04, "lista": e05, "titulares": e06, "portal": e07, "curva": e08,
       "plato": e09, "video_encima": e10, "recortable": e11, "vertigo": e12, "revista": e13, "lente": e14, "zoom_corte": e15,
       "croma": e16, "cristal_roto": e17, "zoom_camara": e18, "movil": e19, "lista_final": e20}


def preparar():
    from PIL import Image, ImageDraw, ImageFilter  # la instala la skill editor-reels (Pillow)
    kit_dst = os.path.join(ROOT, "assets", "kit")
    if not os.path.isdir(kit_dst):
        shutil.copytree(os.path.join(KIT, "assets"), kit_dst)
    sfx_dst = os.path.join(kit_dst, "sfx")
    if not os.path.isdir(sfx_dst):  # los sonidos vienen con las skills de Hyperframes (npx skills add heygen-com/hyperframes)
        for cand in (os.path.join(ROOT, ".claude/skills/media-use/audio/assets/sfx"), os.path.join(ROOT, ".agents/skills/media-use/audio/assets/sfx"),
                     "~/.claude/skills/media-use/audio/assets/sfx", "~/.agents/skills/media-use/audio/assets/sfx"):
            if os.path.isdir(os.path.expanduser(cand)):
                shutil.copytree(os.path.expanduser(cand), sfx_dst)
                break
    gen = os.path.join(ROOT, "assets", "kit-gen")
    os.makedirs(gen, exist_ok=True)
    ff = shutil.which("ffmpeg") or "ffmpeg"

    def frame(t, out, src=None, extra=()):
        subprocess.run([ff, "-y", "-v", "error", *extra, "-ss", f"{max(0.0, t):.2f}", "-i", os.path.join(ROOT, src or VID), "-frames:v", "1", out], check=True)
    tmp = os.path.join(gen, "_f.png")
    for k in range(10):
        frame(DUR * (k + 0.5) / 10, tmp)
        Image.open(tmp).convert("RGB").resize((96, 171)).save(os.path.join(gen, f"th{k}.jpg"), quality=85)
    frame(DUR * 0.35, tmp)
    Image.open(tmp).convert("RGB").resize((360, 640)).save(os.path.join(gen, "resultado.jpg"), quality=88)
    frame(0.5, tmp)
    base = Image.open(tmp).convert("RGB").resize((1080, 1920))
    vacio = CFG.get("fondo_vacio")  # foto de la habitación vacía (los 3 s del final de la toma); sin ella, la toma muy desenfocada
    plate = Image.open(os.path.join(ROOT, vacio)).convert("RGB").resize((1080, 1920)) if vacio else base.filter(ImageFilter.GaussianBlur(28))
    plate.save(os.path.join(gen, "plate.jpg"), quality=90)
    base.filter(ImageFilter.GaussianBlur(40)).save(os.path.join(gen, "room-blur.jpg"), quality=88)
    av = CFG.get("avatar")
    if av:
        a = Image.open(os.path.join(ROOT, av)).convert("RGBA")
        s = min(a.size)
        a = a.crop(((a.width - s) // 2, (a.height - s) // 2, (a.width + s) // 2, (a.height + s) // 2)).resize((256, 256))
    else:
        a = Image.new("RGBA", (256, 256), (230, 230, 235, 255))
        ImageDraw.Draw(a).text((128, 128), CFG.get("usuario", "?")[:1].upper(), fill=(60, 60, 70, 255), anchor="mm")
    m = Image.new("L", (256, 256), 0)
    ImageDraw.Draw(m).ellipse((2, 2, 253, 253), fill=255)
    a.putalpha(m)
    a.save(os.path.join(gen, "avatar.png"))
    for e in EFF:  # cristal roto: la rotura lleva dentro la ciudad con la persona en ese instante
        if e["tipo"] == "cristal_roto":
            frame(e["start"] + 0.42, tmp, src=CUT, extra=("-c:v", "libvpx-vp9"))
            g = Image.open(os.path.join(kit_dst, "img", "taki-city.jpg")).convert("RGBA")
            g.alpha_composite(Image.open(tmp).convert("RGBA").resize((1080, 1920)))
            g.convert("RGB").save(os.path.join(gen, "roto-still.jpg"), quality=90)
    if os.path.exists(tmp):
        os.remove(tmp)


CSS = f"""
@font-face {{ font-family: "Inter"; src: url("assets/kit/fonts/Inter.ttf") format("truetype"); font-weight: 100 900; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #0B0B0D; }}
#main-root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #0B0B0D; font-family: {SANS}; }}
#cam-box {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; overflow: hidden; z-index: 1; background: #0B0B0D; }}
#fg-box {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; z-index: 4; opacity: 0; pointer-events: none; }}
.cmove, .cpunch, .fmove, .fpunch {{ position: absolute; inset: 0; transform-origin: {FX}px {FY}px; }}
#cam-inner, #fg-inner {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; transform-origin: 0 0; }}
#aroll, #cutout {{ width: 100%; height: 100%; display: block; }}
#cam-plate {{ position: absolute; inset: 0; background: url(assets/kit-gen/plate.jpg) center/cover; opacity: 0; }}
.lay {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }}
.back > .lay {{ z-index: 2; }} .front > .lay {{ z-index: 5; }}
.full {{ position: absolute; inset: 0; }}
.dup {{ display: block; }}
.flash {{ position: absolute; inset: 0; background: #fff; opacity: 0; }}
.grain {{ position: absolute; inset: 0; opacity: .14; mix-blend-mode: multiply; background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' seed='7'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>"); }}
.pc {{ display: none; white-space: pre; }}
/* rótulos con fondo por línea (estilo Taki) */
.tbox {{ position: absolute; left: 0; width: 1080px; display: flex; flex-direction: column; align-items: center; filter: drop-shadow(0 10px 18px rgba(0,0,0,.22)); }}
.tbox span {{ display: block; background: {PAPER}; color: {INK}; font-weight: 700; white-space: nowrap; }}
.tbox.big {{ top: 306px; }} .tbox.big span {{ font-size: 86px; line-height: 104px; letter-spacing: -2.5px; padding: 0 26px; border-radius: 22px; }} .tbox.big span + span {{ margin-top: -12px; }}
.tbox.small {{ top: 180px; }} .tbox.small span {{ font-size: 44px; line-height: 54px; letter-spacing: -1.2px; padding: 0 16px; border-radius: 13px; }} .tbox.small span + span {{ margin-top: -6px; }}
.tbox.cta {{ top: 262px; }} .tbox.cta span {{ font-size: 62px; line-height: 82px; letter-spacing: -1.6px; padding: 0 24px; border-radius: 20px; font-weight: 800; }} .tbox.cta span + span {{ margin-top: -10px; }}
.tbox.mini {{ top: 40px; width: 100%; filter: none; }} .tbox.mini span {{ font-size: 15px; line-height: 19px; letter-spacing: -.3px; padding: 0 6px; border-radius: 5px; }} .tbox.mini span + span {{ margin-top: -2px; }}
.clogo {{ position: absolute; border-radius: 24%; background: {OR}; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 18px -6px rgba(251,82,34,.6); }}
.clogo svg {{ width: 66%; height: 66%; }}
#in-logo {{ left: 510px; top: 222px; width: 60px; height: 60px; }}
#hud {{ position: absolute; left: 0; top: 0; width: 1080px; height: 420px; z-index: 8; }}
#hud-logo {{ left: 525px; top: 138px; width: 30px; height: 30px; }}
#hud-bars {{ position: absolute; left: 124px; top: 404px; width: 832px; height: 6px; display: flex; gap: 9px; }}
#hud-bars i {{ flex: 1; height: 6px; border-radius: 3px; background: rgba(120,120,120,.55); box-shadow: inset 0 0 0 1px rgba(255,255,255,.2); }}
.hl {{ position: absolute; left: 0; top: 302px; width: 1080px; height: 84px; display: flex; justify-content: center; align-items: center; gap: 12px; z-index: 8; }}
.hn {{ width: 84px; height: 84px; border-radius: 18px; background: {OR}; color: #fff; font-weight: 700; font-size: 44px; display: flex; align-items: center; justify-content: center; font-variant-numeric: tabular-nums; box-shadow: 0 10px 24px -10px rgba(251,82,34,.7); }}
.ht {{ height: 84px; line-height: 84px; padding: 0 28px; border-radius: 18px; background: {PAPER}; color: {INK}; font-weight: 700; font-size: 56px; letter-spacing: -1.4px; white-space: nowrap; box-shadow: 0 10px 24px -12px rgba(0,0,0,.45); }}
.li {{ position: absolute; height: 40px; padding: 0 14px 0 10px; border-radius: 9px; background: rgba(18,18,20,.86); color: #fff; font-weight: 700; font-size: 21px; letter-spacing: -.2px; display: flex; align-items: center; gap: 8px; white-space: nowrap; box-shadow: 0 10px 24px -12px rgba(0,0,0,.5); }}
.li b {{ color: {OR}; font-size: 15px; font-weight: 800; font-variant-numeric: tabular-nums; }}
/* subtítulos palabra a palabra */
.cap {{ position: absolute; left: 0; top: 1500px; width: 1080px; height: 130px; display: flex; justify-content: center; align-items: center; z-index: 9; }}
.cap span {{ position: relative; display: inline-block; font-weight: 800; font-size: 100px; line-height: 1; letter-spacing: -2px; white-space: nowrap; }}
.cap b {{ display: block; color: {INK}; -webkit-text-stroke: 15px {INK}; font-weight: 800; text-shadow: 0 8px 22px rgba(0,0,0,.45); }}
.cap i {{ position: absolute; left: 0; top: 0; font-style: normal; color: #fff; }}
/* 01 órbita */
.orb {{ position: absolute; left: 0; top: 0; width: 104px; height: 104px; }}
.otile {{ position: absolute; inset: 0; border-radius: 24px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(255,255,255,.14); box-shadow: 0 18px 34px -12px rgba(0,0,0,.55); }}
.otile svg {{ width: 56px; height: 56px; }}
/* 02 chat de Claude */
.chcard {{ position: absolute; left: 60px; top: 446px; width: 960px; height: 940px; border-radius: 30px; background: #FAF9F5; box-shadow: 0 50px 90px -30px rgba(0,0,0,.75), inset 0 1px 0 #fff; }}
.chhd {{ position: absolute; left: 60px; top: 446px; width: 960px; height: 66px; display: flex; align-items: center; gap: 9px; padding-left: 26px; border-bottom: 1px solid #ECE8DE; }}
.chhd i {{ width: 13px; height: 13px; border-radius: 50%; }}
.chhd b {{ margin-left: 18px; display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 24px; color: #1F1E1C; }}
.chhd b svg {{ width: 28px; height: 28px; }}
.chhd em {{ margin-left: auto; margin-right: 28px; font-style: normal; font-weight: 700; font-size: 13px; letter-spacing: 2.5px; color: #A39E93; }}
.chme {{ position: absolute; left: 330px; top: 536px; width: 650px; padding: 18px 24px; border-radius: 22px 22px 6px 22px; background: #EFECE4; color: #1F1E1C; font-weight: 500; font-size: 27px; line-height: 1.3; }}
.chslot {{ position: absolute; border-radius: 18px; background: #E9E5DC; }}
.chav {{ position: absolute; left: 100px; top: 686px; width: 46px; height: 46px; border-radius: 12px; background: {INK}; display: flex; align-items: center; justify-content: center; }}
.chav svg {{ width: 28px; height: 28px; }}
.chdots {{ position: absolute; left: 164px; top: 704px; display: flex; gap: 8px; opacity: 0; }}
.chdots i {{ width: 12px; height: 12px; border-radius: 50%; background: #C9C2B4; }}
.chok {{ position: absolute; left: 164px; top: 690px; font-weight: 700; font-size: 31px; color: #1F1E1C; opacity: 0; }}
.chr {{ position: absolute; left: 164px; height: 40px; display: flex; align-items: center; gap: 14px; font-weight: 600; font-size: 26px; color: #3A3835; white-space: nowrap; opacity: 0; }}
.chb {{ position: relative; width: 34px; height: 34px; }} .chb svg {{ width: 34px; height: 34px; display: block; }}
.chc {{ position: absolute; left: 0; top: 3px; width: 34px; height: 34px; }} .chc svg {{ width: 34px; height: 34px; display: block; }}
.chin {{ position: absolute; left: 92px; top: 1294px; width: 896px; height: 66px; border-radius: 33px; background: #FFFFFF; border: 1px solid #E6E1D6; display: flex; align-items: center; padding: 0 10px 0 28px; color: #A39E93; font-weight: 500; font-size: 24px; }}
.chin b {{ margin-left: auto; width: 46px; height: 46px; border-radius: 50%; background: {OR}; display: flex; align-items: center; justify-content: center; }}
.chin b svg {{ width: 24px; height: 24px; }}
.chtag {{ position: absolute; height: 34px; padding: 0 12px 0 8px; border-radius: 17px; background: rgba(0,0,0,.55); color: #FFFFFF; display: flex; align-items: center; gap: 6px; font-weight: 700; font-size: 16px; opacity: 0; }}
.chtag svg {{ width: 20px; height: 20px; }}
/* 03 salir del marco */
#mk-paper {{ filter: drop-shadow(0 34px 40px rgba(0,0,0,.6)); }}
/* 05 lista que aparece */
.ckpill {{ position: absolute; right: 34px; height: 76px; padding: 0 32px 0 14px; border-radius: 38px; background: {PAPER}; display: flex; align-items: center; gap: 14px; font-weight: 700; font-size: 34px; color: {INK}; box-shadow: 0 14px 30px -12px rgba(0,0,0,.45); transform-origin: 100% 50%; opacity: 0; }}
.ckpill .ckc {{ width: 48px; height: 48px; }} .ckpill .ckc svg {{ width: 48px; height: 48px; display: block; }}
.cksp {{ position: absolute; right: 200px; width: 44px; height: 44px; }} .cksp svg {{ width: 100%; height: 100%; display: block; }}
/* 06 titulares */
.hstrip {{ position: absolute; display: flex; align-items: stretch; height: 88px; background: {PAPER}; white-space: nowrap; box-shadow: 0 22px 44px -18px rgba(0,0,0,.6); }}
.hstrip em {{ display: flex; align-items: center; padding: 0 22px; background: {OR}; color: #fff; font-style: normal; font-weight: 800; font-size: 20px; letter-spacing: 3px; }}
.hstrip b {{ display: flex; align-items: center; padding: 0 30px 0 24px; color: {INK}; font-weight: 900; font-size: 52px; letter-spacing: -1px; }}
.hstrip.dark {{ background: {INK}; }} .hstrip.dark b {{ color: #fff; }}
/* 07 portal */
.portal {{ position: absolute; }}
.ptmask {{ position: absolute; inset: 0; border-radius: 50%; overflow: hidden; background: #000; box-shadow: 0 0 0 6px {OR}, 0 0 36px 8px rgba(251,82,34,.45); }}
.ptin, .lnin {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; transform-origin: 0 0; }}
.ptfill {{ position: absolute; left: -1080px; top: -1920px; width: 3240px; height: 5760px; background: url(assets/kit-gen/room-blur.jpg) center/cover; }}
.ptvig {{ position: absolute; inset: 0; border-radius: 50%; box-shadow: inset 0 0 44px 6px rgba(0,0,0,.4); }}
/* 08 curva */
.cvgrid {{ position: absolute; inset: 0; background-image: linear-gradient(rgba(255,255,255,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.07) 1px, transparent 1px); background-size: 72px 72px; background-position: 0 30px; }}
.cvlab {{ position: absolute; left: 60px; top: 436px; display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 17px; letter-spacing: 3px; color: rgba(255,255,255,.55); }}
.cvlab i {{ width: 12px; height: 12px; background: {OR}; }}
.cvdot0 {{ position: absolute; left: 27px; top: 1097px; width: 26px; height: 26px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 6px {OR}; }}
.cvtip {{ position: absolute; left: 0; top: 0; width: 26px; height: 26px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 6px rgba(251,82,34,.9), 0 0 24px 6px rgba(251,82,34,.6); }}
.cvbadge {{ position: absolute; right: 52px; top: 436px; height: 104px; padding: 0 22px; border-radius: 14px; background: {OR}; display: flex; align-items: center; gap: 10px; color: #fff; box-shadow: 0 0 40px 4px rgba(251,82,34,.45); }}
.cvbadge b {{ font-weight: 800; font-size: 62px; letter-spacing: -2px; font-variant-numeric: tabular-nums; }}
.cvbadge em {{ font-style: normal; font-weight: 800; font-size: 15px; letter-spacing: 2.5px; margin-top: 24px; }}
/* 09 plató */
.plimg {{ background-position: center; background-size: cover; }}
.bloom {{ position: absolute; border-radius: 8px; opacity: 0; box-shadow: 0 0 90px 34px rgba(214,232,255,.30), 0 0 26px 6px rgba(255,255,255,.4); }}
.haze {{ position: absolute; left: -200px; top: 280px; width: 1480px; height: 1300px; opacity: 0; background: radial-gradient(50% 45% at 50% 50%, rgba(200,215,235,.17), rgba(200,215,235,0) 70%); }}
.motes {{ position: absolute; inset: 0; opacity: 0; }}
.motes i {{ position: absolute; border-radius: 50%; background: #fff; }}
.onair {{ position: absolute; left: 390px; top: 420px; width: 300px; height: 56px; border-radius: 12px; display: flex; align-items: center; justify-content: center; gap: 12px; opacity: 0; background: {OR}; color: #fff; font-weight: 800; font-size: 27px; letter-spacing: 5px; text-shadow: 0 0 12px rgba(255,255,255,.5); box-shadow: 0 0 46px 10px rgba(251,82,34,.55), inset 0 2px 0 rgba(255,255,255,.3); }}
.onair i {{ width: 11px; height: 11px; border-radius: 50%; background: #fff; box-shadow: 0 0 10px #fff; }}
.onair.off {{ background: #3A1610; color: rgba(255,255,255,.22); text-shadow: none; box-shadow: none; }}
/* 10 vídeo encima: editor claro y pistas grandes */
.lw {{ position: absolute; left: 45px; top: 440px; width: 990px; height: 828px; border-radius: 22px; background: #F3F3F1; border: 1px solid #D9D9D6; box-shadow: 0 50px 90px -30px rgba(0,0,0,.8); }}
.lwbar {{ position: absolute; left: 45px; top: 440px; width: 990px; height: 52px; display: flex; align-items: center; gap: 9px; padding-left: 22px; border-bottom: 1px solid #E0E0DC; }}
.lwbar i {{ width: 13px; height: 13px; border-radius: 50%; }}
.lwbar span {{ position: absolute; left: 0; width: 990px; text-align: center; color: #6B6B6B; font-weight: 600; font-size: 17px; }}
.lwbar em {{ position: absolute; right: 16px; top: 11px; height: 30px; line-height: 30px; padding: 0 14px; border-radius: 8px; background: {OR}; color: #fff; font-style: normal; font-weight: 700; font-size: 14px; }}
.lwview {{ position: absolute; left: 66px; top: 506px; width: 948px; height: 572px; border-radius: 12px; background: #18181B; }}
.lwtag {{ position: absolute; left: 82px; top: 520px; height: 34px; line-height: 34px; padding: 0 14px; border-radius: 6px; background: {OR}; color: #fff; font-weight: 800; font-size: 14px; letter-spacing: 2.5px; z-index: 2; }}
.lwtl {{ position: absolute; left: 66px; top: 1092px; width: 948px; height: 160px; border-radius: 10px; background: #FFFFFF; border: 1px solid #E2E2DF; overflow: hidden; }}
.lwtr {{ position: absolute; left: 0; width: 948px; height: 64px; }}
.lwtr b {{ position: absolute; left: 14px; top: 0; height: 64px; line-height: 64px; color: #8A8A86; font-weight: 700; font-size: 15px; }}
.lwstrip {{ position: absolute; left: 56px; top: 4px; height: 56px; display: flex; gap: 2px; border-radius: 6px; overflow: hidden; }}
.lwstrip img {{ height: 56px; width: auto; display: block; }}
.lwwave {{ position: absolute; left: 56px; right: 14px; top: 8px; height: 44px; display: flex; align-items: center; gap: 3px; background: #E8F6EE; border-radius: 6px; padding: 0 8px; overflow: hidden; }}
.lwwave i {{ flex: none; width: 3px; border-radius: 2px; background: #2FB777; }}
.lwph {{ position: absolute; left: 160px; top: 0; width: 2px; height: 160px; background: {OR}; }}
.bt {{ position: absolute; left: 45px; top: 1296px; width: 990px; height: 168px; border-radius: 16px; background: rgba(14,18,32,.8); border: 1px solid rgba(255,255,255,.09); }}
.btl {{ position: absolute; left: 70px; height: 44px; line-height: 44px; color: rgba(255,255,255,.55); font-weight: 700; font-size: 18px; }}
.btb {{ position: absolute; height: 52px; line-height: 52px; padding-left: 16px; border-radius: 9px; color: #fff; font-weight: 700; font-size: 19px; }}
.btb.or {{ background: {OR}; box-shadow: 0 0 22px -2px rgba(251,82,34,.6); }} .btb.bl {{ background: #2F5BEA; }}
.btph {{ position: absolute; left: 200px; top: 1302px; width: 3px; height: 156px; border-radius: 2px; background: #fff; box-shadow: 0 0 10px rgba(255,255,255,.6); }}
.eov {{ position: absolute; border-radius: 10px; overflow: hidden; border: 3px solid #fff; box-shadow: 0 18px 40px -10px rgba(0,0,0,.75); background: #000; opacity: 0; }}
.eov video {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
/* 11 recortable */
.rcp {{ position: absolute; }} .rcp svg {{ width: 100%; height: 100%; display: block; }}
.rcband {{ position: absolute; height: 84px; }}
/* 13 revista */
.mgtop {{ position: absolute; left: 40px; right: 40px; top: 432px; display: flex; justify-content: space-between; color: {INK}; font-weight: 800; font-size: 16px; letter-spacing: 2.5px; }}
.mast2 {{ position: absolute; left: 0; width: 1080px; top: 470px; text-align: center; color: {OR}; font-weight: 900; font-size: 188px; line-height: 1; letter-spacing: -8px; white-space: nowrap; }}
.mgleft {{ position: absolute; left: 40px; top: 760px; display: flex; flex-direction: column; color: #2A2A2A; }}
.mgleft em {{ font-style: normal; color: {OR}; font-weight: 800; font-size: 16px; letter-spacing: 2.5px; }}
.mgleft b {{ color: {OR}; font-weight: 900; font-size: 150px; line-height: .95; letter-spacing: -6px; transform-origin: 0 50%; }}
.mgleft span i, .mgright span i, .mgright b i {{ display: block; font-style: normal; }}
.mgleft span {{ font-weight: 600; font-size: 22px; line-height: 1.25; }}
.mgright {{ position: absolute; right: 40px; top: 850px; display: flex; flex-direction: column; align-items: flex-end; text-align: right; color: #2A2A2A; }}
.mgright em {{ font-style: normal; color: {OR}; font-weight: 800; font-size: 16px; letter-spacing: 2.5px; margin-bottom: 6px; }}
.mgright b {{ color: {INK}; font-weight: 900; font-size: 54px; line-height: .98; letter-spacing: -1.5px; }}
.mgright span {{ margin-top: 10px; font-weight: 500; font-size: 20px; line-height: 1.3; }}
.barcode2 {{ position: absolute; left: 56px; top: 1318px; padding: 10px 12px 6px; background: #fff; }}
.barcode2 .bars {{ height: 90px; display: flex; gap: 3px; align-items: stretch; }}
.barcode2 .bars i {{ display: block; background: {INK}; }}
.barcode2 span {{ display: block; text-align: center; font-weight: 600; font-size: 13px; letter-spacing: 2px; color: {INK}; margin-top: 4px; }}
/* 14 cristal líquido */
.lens {{ position: absolute; left: 0; border-radius: 50%; overflow: hidden; box-shadow: 0 30px 60px -20px rgba(0,0,0,.55), inset 0 0 0 3px rgba(255,255,255,.75); }}
.lnhl {{ position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(60% 50% at 32% 24%, rgba(255,255,255,.3) 0%, rgba(255,255,255,0) 60%), radial-gradient(circle at 50% 50%, rgba(255,255,255,0) 62%, rgba(180,220,255,.22) 84%, rgba(255,255,255,.6) 100%); }}
/* 17 cristal roto */
.shard {{ position: absolute; inset: 0; background: url(assets/kit-gen/roto-still.jpg) center/cover; }}
.cracks {{ filter: drop-shadow(0 0 2px rgba(0,0,0,.65)); }}
/* 18 zoom de cámara */
.scan {{ position: absolute; inset: 0; opacity: 0; background: repeating-linear-gradient(0deg, rgba(0,0,0,.13) 0px, rgba(0,0,0,.13) 1px, transparent 1px, transparent 4px); }}
.vf2 i {{ position: absolute; width: 96px; height: 96px; border-color: rgba(255,255,255,.92); border-style: solid; }}
.vf2 .c1 {{ left: 63px; top: 430px; border-width: 3px 0 0 3px; }} .vf2 .c2 {{ left: 921px; top: 430px; border-width: 3px 3px 0 0; }}
.vf2 .c3 {{ left: 63px; top: 1390px; border-width: 0 0 3px 3px; }} .vf2 .c4 {{ left: 921px; top: 1390px; border-width: 0 3px 3px 0; }}
.rec2 {{ position: absolute; left: 96px; top: 452px; display: flex; align-items: center; gap: 10px; color: #fff; font-weight: 700; font-size: 22px; letter-spacing: 3px; text-shadow: 0 1px 6px rgba(0,0,0,.5); }}
.rec2 i {{ width: 14px; height: 14px; border-radius: 50%; background: #FF3B30; }}
.tc2 {{ position: absolute; right: 96px; top: 454px; color: rgba(255,255,255,.75); font-weight: 600; font-size: 20px; letter-spacing: 1px; font-variant-numeric: tabular-nums; text-shadow: 0 1px 6px rgba(0,0,0,.5); }}
.zpill {{ position: absolute; left: 470px; top: 440px; width: 140px; height: 52px; border-radius: 26px; background: rgba(28,28,30,.66); }}
.zpill span {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: {OR}; font-weight: 700; font-size: 26px; opacity: 0; }}
.focus2 {{ position: absolute; left: 436px; top: 785px; width: 260px; height: 150px; border: 3px solid {OR}; }}
/* 19 móvil con Reels */
.phone {{ position: absolute; border-radius: 74px; border: 20px solid #141416; box-shadow: 0 0 0 2px #46464C, inset 0 0 0 2px #000, 0 60px 90px -30px rgba(0,0,0,.85); }}
.island {{ position: absolute; left: 50%; top: 16px; width: 140px; height: 38px; margin-left: -70px; border-radius: 19px; background: #000; z-index: 2; }}
.phone .btn {{ position: absolute; width: 6px; border-radius: 3px; background: #2A2A2E; }}
.phone .b1 {{ left: -27px; top: 230px; height: 70px; }} .phone .b2 {{ left: -27px; top: 320px; height: 110px; }} .phone .b3 {{ right: -27px; top: 280px; height: 150px; }}
.phui {{ position: absolute; inset: 0; border-radius: 54px; overflow: hidden; opacity: 0; color: #FFFFFF; }}
.phr {{ position: absolute; left: 28px; top: 66px; font-weight: 800; font-size: 30px; text-shadow: 0 1px 8px rgba(0,0,0,.4); }}
.phcam {{ position: absolute; right: 26px; top: 66px; width: 34px; height: 34px; }} .phcam svg {{ width: 34px; height: 34px; display: block; }}
.phside {{ position: absolute; right: 18px; bottom: 170px; display: flex; flex-direction: column; align-items: center; gap: 28px; }}
.phside i {{ width: 40px; height: 40px; filter: drop-shadow(0 1px 6px rgba(0,0,0,.45)); }} .phside i svg {{ width: 40px; height: 40px; display: block; }}
.phside .dots3 {{ height: 20px; font-style: normal; font-weight: 900; font-size: 22px; letter-spacing: 1px; text-align: center; }}
.phuser {{ position: absolute; left: 24px; bottom: 112px; display: flex; align-items: center; gap: 12px; }}
.phuser img {{ width: 46px; height: 46px; border-radius: 50%; }}
.phuser b {{ font-weight: 800; font-size: 22px; text-shadow: 0 1px 8px rgba(0,0,0,.5); }}
.phuser em {{ font-style: normal; height: 32px; line-height: 30px; padding: 0 14px; border-radius: 9px; border: 1.5px solid rgba(255,255,255,.85); font-weight: 700; font-size: 17px; }}
.phcap {{ position: absolute; left: 24px; right: 80px; bottom: 64px; font-weight: 600; font-size: 20px; line-height: 1.25; text-shadow: 0 1px 8px rgba(0,0,0,.6); }}
.phbar {{ position: absolute; left: 0; right: 0; bottom: 0; height: 5px; background: rgba(255,255,255,.3); }}
.phbar i {{ display: block; width: 100%; height: 100%; background: #FFFFFF; transform-origin: 0 50%; }}
/* 20 lista final */
.lfnum {{ position: absolute; left: 62px; top: 438px; height: 170px; color: {OR}; font-weight: 800; font-size: 168px; line-height: 170px; letter-spacing: -6px; font-variant-numeric: tabular-nums; }}
.lfn {{ display: none; }}
.lftx {{ position: absolute; left: 300px; top: 500px; display: flex; flex-direction: column; color: #fff; font-weight: 700; font-size: 40px; line-height: 48px; letter-spacing: -.5px; }}
.lfr2 {{ position: absolute; display: flex; align-items: center; gap: 16px; height: 40px; font-weight: 600; font-size: 30px; color: rgba(255,255,255,.92); white-space: nowrap; }}
.lfb2 {{ width: 34px; height: 34px; border-radius: 8px; border: 2.5px solid rgba(255,255,255,.35); }}
.lfc2 {{ position: absolute; left: 0; top: 3px; width: 34px; height: 34px; }} .lfc2 svg {{ width: 34px; height: 34px; display: block; }}
/* cierre: app, comentario y perfil */
.apc2 {{ position: absolute; left: 108px; top: 680px; width: 864px; height: 450px; border-radius: 30px; background: linear-gradient(180deg, #121318 0%, #0E1017 62%, #142650 100%); border: 1px solid rgba(255,255,255,.09); box-shadow: 0 50px 90px -30px rgba(0,0,0,.8), inset 0 1px 0 rgba(255,255,255,.06); opacity: 0; }}
.apic3 {{ position: absolute; left: 40px; top: 40px; width: 96px; height: 96px; border-radius: 24px; background: linear-gradient(145deg, #FF7A4A, #E8461E); display: flex; align-items: center; justify-content: center; box-shadow: 0 12px 30px -10px rgba(251,82,34,.85); }}
.apic3 svg {{ width: 58px; height: 58px; }}
.apt2 {{ position: absolute; left: 160px; top: 46px; font-weight: 800; font-size: 44px; letter-spacing: -1px; color: #fff; }}
.aps2 {{ position: absolute; left: 162px; top: 106px; font-style: normal; font-weight: 700; font-size: 15px; letter-spacing: 3.5px; color: rgba(255,255,255,.5); }}
.apon {{ position: absolute; right: 36px; top: 52px; height: 36px; padding: 0 14px; border-radius: 8px; background: {OR}; color: #fff; display: flex; align-items: center; gap: 8px; font-weight: 800; font-size: 15px; letter-spacing: 2px; }}
.apon i {{ width: 8px; height: 8px; border-radius: 50%; background: #fff; }}
.apdiv2 {{ position: absolute; left: 40px; right: 40px; top: 168px; height: 1px; background: rgba(255,255,255,.08); }}
.apch2 {{ position: absolute; left: 40px; right: 40px; top: 196px; display: flex; flex-wrap: wrap; gap: 12px; }}
.apch2 span {{ height: 44px; line-height: 44px; padding: 0 18px; border-radius: 10px; background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.14); color: rgba(255,255,255,.88); font-weight: 700; font-size: 17px; letter-spacing: 2.5px; }}
.apsty {{ position: absolute; left: 40px; right: 40px; top: 342px; height: 64px; border-radius: 14px; background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.08); display: flex; align-items: center; gap: 12px; padding: 0 20px; color: rgba(255,255,255,.85); font-weight: 600; font-size: 22px; opacity: 0; }}
.apsty svg {{ width: 22px; height: 22px; color: {OR}; }}
.apsteps {{ position: absolute; left: 0; width: 1080px; top: 640px; display: flex; justify-content: center; gap: 16px; opacity: 0; }}
.apst2 {{ height: 52px; padding: 0 22px 0 8px; border-radius: 26px; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.14); display: flex; align-items: center; gap: 10px; color: rgba(255,255,255,.65); font-weight: 700; font-size: 22px; }}
.apst2 i {{ width: 36px; height: 36px; border-radius: 50%; background: rgba(255,255,255,.14); display: flex; align-items: center; justify-content: center; font-style: normal; font-weight: 800; font-size: 17px; color: #fff; }}
.apdrop2 {{ position: absolute; left: 142px; top: 740px; width: 796px; height: 440px; border-radius: 24px; border: 3px dashed rgba(160,180,230,.4); display: flex; align-items: center; justify-content: center; opacity: 0; }}
.apdrop2 span {{ display: flex; flex-direction: column; align-items: center; gap: 14px; color: rgba(255,255,255,.75); font-weight: 600; font-size: 32px; }}
.apdrop2 svg {{ width: 44px; height: 44px; }}
.apfile2 {{ position: absolute; left: 310px; top: 905px; width: 460px; height: 110px; border-radius: 18px; background: #FFFFFF; box-shadow: 0 24px 50px -14px rgba(0,0,0,.6); opacity: 0; }}
.apfile2 i {{ position: absolute; left: 18px; top: 18px; width: 74px; height: 74px; border-radius: 16px; background: #2F5BEA; color: #fff; display: flex; align-items: center; justify-content: center; }}
.apfile2 i svg {{ width: 40px; height: 40px; }}
.apfile2 b {{ position: absolute; left: 110px; top: 24px; font-weight: 800; font-size: 28px; color: {INK}; }}
.apfile2 small {{ position: absolute; left: 110px; top: 64px; font-weight: 700; font-size: 15px; letter-spacing: 2px; color: #8B867C; }}
.aptag {{ position: absolute; height: 40px; padding: 0 16px; border-radius: 8px; background: {OR}; color: #fff; display: flex; align-items: center; gap: 8px; font-weight: 800; font-size: 17px; letter-spacing: 2px; white-space: nowrap; opacity: 0; }}
.aptag svg {{ width: 16px; height: 16px; }}
.appr2 {{ position: absolute; left: 90px; top: 910px; width: 900px; height: 100px; border-radius: 50px; background: #FFFFFF; display: flex; align-items: center; padding: 0 14px 0 40px; color: {INK}; font-weight: 600; font-size: 36px; box-shadow: 0 24px 60px -20px rgba(0,0,0,.7); opacity: 0; }}
.appr2 b {{ margin-left: auto; width: 72px; height: 72px; border-radius: 50%; background: {OR}; display: flex; align-items: center; justify-content: center; }}
.appr2 b svg {{ width: 34px; height: 34px; }}
.caret {{ display: inline-block; width: 3px; height: 42px; background: {OR}; margin-left: 4px; }}
.apph {{ position: absolute; left: 372px; top: 776px; width: 336px; height: 566px; border-radius: 48px; background: #0E0E10; border: 20px solid #0E0E10; box-shadow: 0 0 0 2px #3A3A40, 0 50px 80px -30px rgba(0,0,0,.85); opacity: 0; }}
.apscr {{ position: absolute; inset: 0; border-radius: 30px; overflow: hidden; background: #000; }}
.apph .island {{ top: 8px; width: 90px; height: 26px; margin-left: -45px; border-radius: 13px; }}
.cbox2 {{ position: absolute; left: 120px; top: 136px; width: 840px; height: 100px; border-radius: 50px; background: #FFFFFF; display: flex; align-items: center; gap: 18px; padding: 0 14px; box-shadow: 0 24px 50px -20px rgba(0,0,0,.6); }}
.cbox2 img {{ width: 72px; height: 72px; border-radius: 50%; }}
.ctx2 {{ display: flex; align-items: center; font-weight: 800; font-size: 44px; letter-spacing: 1px; color: {INK}; }}
.ctx2 i {{ font-style: normal; font-weight: 500; font-size: 34px; letter-spacing: 0; color: #9A9A9A; }}
.aptag2 {{ margin-left: auto; height: 40px; padding: 0 14px; border-radius: 8px; background: {OR}; color: #fff; display: flex; align-items: center; gap: 6px; font-weight: 800; font-size: 16px; letter-spacing: 1.5px; opacity: 0; }}
.aptag2 svg {{ width: 16px; height: 16px; }}
.csend {{ width: 72px; height: 72px; border-radius: 50%; background: {OR}; display: flex; align-items: center; justify-content: center; flex: none; }}
.csend svg {{ width: 34px; height: 34px; }}
.prof {{ position: absolute; left: 120px; top: 400px; width: 840px; height: 130px; border-radius: 65px; background: rgba(14,14,16,.8); border: 1px solid rgba(255,255,255,.12); display: flex; align-items: center; gap: 20px; padding: 0 22px 0 18px; box-shadow: 0 30px 60px -24px rgba(0,0,0,.7); }}
.prof img {{ width: 94px; height: 94px; border-radius: 50%; flex: none; }}
.prof b {{ display: flex; align-items: center; gap: 8px; color: #fff; font-weight: 700; font-size: 34px; }}
.prof b svg {{ width: 28px; height: 28px; }}
.prof em {{ display: block; margin-top: 6px; font-style: normal; color: rgba(255,255,255,.72); font-weight: 500; font-size: 19px; white-space: nowrap; }}
.pfollow {{ margin-left: auto; height: 56px; line-height: 56px; padding: 0 26px; border-radius: 16px; background: {OR}; color: #fff; font-weight: 800; font-size: 22px; flex: none; }}
/* v7: final con Claude Code, paleta de Taki */
.ccwin {{ position: absolute; left: 70px; top: 540px; width: 940px; height: 900px; border-radius: 30px; background: rgba(255,255,255,.95); border: 1px solid #fff; box-shadow: 0 50px 90px -30px rgba(0,0,0,.7); }}
.ccglow {{ position: absolute; left: 60px; top: 530px; width: 960px; height: 920px; border-radius: 44px; background: linear-gradient(160deg, {OR} 0%, {BLUE} 100%); filter: blur(34px); opacity: 0; }}
.cchd {{ position: absolute; left: 70px; top: 540px; width: 940px; height: 66px; display: flex; align-items: center; gap: 9px; padding-left: 26px; border-bottom: 1px solid #ECE8DE; }}
.cchd i {{ width: 13px; height: 13px; border-radius: 50%; }}
.cchd b {{ margin-left: 16px; display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 24px; color: #1F1E1C; }}
.cchd b svg {{ width: 28px; height: 28px; }}
.cchd em {{ margin-left: auto; margin-right: 22px; height: 36px; line-height: 36px; padding: 0 14px; border-radius: 18px; background: #F2F0EA; font-style: normal; font-weight: 600; font-size: 18px; color: #6E6A60; }}
.ccme {{ position: absolute; left: 330px; top: 640px; width: 650px; padding: 16px 20px 18px; border-radius: 22px 22px 6px 22px; background: #EFECE4; color: #1F1E1C; font-weight: 500; font-size: 27px; line-height: 1.3; opacity: 0; }}
.ccme span {{ display: block; }}
.ccatt {{ display: inline-flex; align-items: center; gap: 10px; height: 46px; padding: 0 14px 0 6px; border-radius: 12px; background: #fff; font-weight: 700; font-size: 19px; margin-bottom: 10px; }}
.ccatt i {{ width: 34px; height: 34px; border-radius: 8px; background: {BLUE}; color: #fff; display: flex; align-items: center; justify-content: center; }} .ccatt i svg {{ width: 20px; height: 20px; }}
.ccav {{ position: absolute; left: 110px; top: 836px; width: 46px; height: 46px; border-radius: 12px; background: #fff; box-shadow: 0 2px 10px rgba(0,0,0,.1); display: flex; align-items: center; justify-content: center; opacity: 0; }}
.ccav svg {{ width: 28px; height: 28px; }}
.ccok {{ position: absolute; left: 174px; top: 840px; font-weight: 700; font-size: 30px; color: #1F1E1C; opacity: 0; }}
.ccr {{ position: absolute; left: 174px; height: 40px; display: flex; align-items: center; gap: 14px; font-weight: 600; font-size: 25px; color: #3A3835; white-space: nowrap; opacity: 0; }}
.ccres {{ position: absolute; left: 174px; top: 1070px; width: 540px; height: 170px; border-radius: 18px; background: #fff; border: 1px solid #ECE8DE; box-shadow: 0 14px 30px -16px rgba(0,0,0,.25); display: flex; align-items: center; gap: 18px; padding: 10px; opacity: 0; }}
.ccres img {{ width: 84px; height: 150px; border-radius: 10px; object-fit: cover; }}
.ccres b {{ display: block; font-weight: 700; font-size: 26px; color: #1F1E1C; }}
.ccres span {{ display: flex; align-items: center; gap: 8px; margin-top: 8px; font-weight: 600; font-size: 20px; color: #6E6A60; }} .ccres span svg {{ width: 26px; height: 26px; }}
.ccfile {{ position: absolute; left: 100px; top: 1258px; width: 420px; height: 66px; border-radius: 16px; background: #fff; border: 1px solid #E6E1D6; box-shadow: 0 14px 30px -14px rgba(0,0,0,.3); opacity: 0; }}
.ccfile i {{ position: absolute; left: 10px; top: 10px; width: 46px; height: 46px; border-radius: 11px; background: {BLUE}; color: #fff; display: flex; align-items: center; justify-content: center; }} .ccfile i svg {{ width: 26px; height: 26px; }}
.ccfile b {{ position: absolute; left: 68px; top: 10px; font-weight: 700; font-size: 21px; color: #1F1E1C; }}
.ccfile small {{ position: absolute; left: 68px; top: 38px; font-weight: 700; font-size: 13px; letter-spacing: 1.5px; color: #8B867C; }}
.ccin {{ position: absolute; left: 100px; top: 1340px; width: 880px; height: 76px; border-radius: 38px; background: #fff; border: 1px solid #E6E1D6; display: flex; align-items: center; padding: 0 10px 0 28px; color: #1F1E1C; font-weight: 500; font-size: 26px; }}
.ccin #cc-ph {{ color: #A39E93; }}
.ccin b {{ margin-left: auto; width: 56px; height: 56px; border-radius: 50%; background: {OR}; display: flex; align-items: center; justify-content: center; flex: none; }} .ccin b svg {{ width: 28px; height: 28px; }}
.cchi {{ position: absolute; left: 70px; top: 880px; width: 940px; display: flex; flex-direction: column; align-items: center; gap: 18px; color: #6E6A60; font-weight: 600; font-size: 34px; letter-spacing: -.5px; }}
.cchi svg {{ width: 64px; height: 64px; }}
"""


def main():
    preparar()
    if INTRO:
        intro()
    hud()
    for e in EFF:
        REG[e["tipo"]](e["start"], e["dur"])
    if CIERRE:
        cta()
    caps = captions()
    index = f"""<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Reel 20 EFECTOS</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>{CSS}</style>
  </head>
  <body>
    <div id="main-root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
      <div id="cam-box"><div class="cmove" data-layout-allow-overflow><div class="cpunch" data-layout-allow-overflow><div id="cam-inner"><video id="aroll" class="clip" src="{VID}" data-start="0" data-duration="{DUR}" data-track-index="0" muted playsinline></video><div id="cam-plate"></div></div></div></div></div>
      <div class="back">{"".join(html_back)}</div>
      <div id="fg-box"><div class="fmove" data-layout-allow-overflow><div class="fpunch" data-layout-allow-overflow><div id="fg-inner"><video id="cutout" class="clip" src="{CUT}" data-start="0" data-duration="{DUR}" data-track-index="3" muted playsinline></video></div></div></div></div>
      <div class="front">{"".join(html_front)}</div>
      {"".join(html_hud)}
      {caps}
      <audio id="voice" src="{VID}" data-start="0" data-duration="{DUR}" data-track-index="10" data-volume="1"></audio>
      {sfx_html()}
    </div>
    <script>
      document.fonts.ready.then(function () {{
        const tl = gsap.timeline({{ paused: true }});
        {chr(10).join("        " + j for j in js).strip()}
        window.__timelines["main"] = tl;
      }});
    </script>
  </body>
</html>
"""
    open(os.path.join(ROOT, "index.html"), "w").write(index)
    print("ok", DUR, len(js), "órdenes,", len(sfx), "sonidos")


if __name__ == "__main__":
    main()
