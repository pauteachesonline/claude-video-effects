"""Seven reel effects from one talking clip. Each effect cuts a short segment, cuts you out of it
(rembg person matte), builds the graphics as a HyperFrames page, then layers it all with ffmpeg.

  python fx.py <effect> <clip> [options]      effects: clothesline trail word wall tiny fan iphone
  python fx.py placeholders                   writes demo items/tiles to ./reel-effects-demo

Output is a 1080x1920 30 fps mp4 (no audio, no metadata) next to where you ran it."""
import argparse, glob, html, json, os, re, shutil, subprocess, sys
import numpy as np

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, '..', 'assets')
HF = ['npx', '--yes', 'hyperframes@0.8.217']
GSAP = '<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>'
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Urbanist:wght@500;900'
         '&family=Space+Mono&display=block">')
IMG = ('*.png', '*.jpg', '*.jpeg', '*.webp')


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'failed: {" ".join(cmd[:4])} ...\n{r.stderr[-1500:]}')


def ff(*args):
    run(['ffmpeg', '-v', 'error', '-y', *args])


def images(folder):
    return sorted(f for p in IMG for f in glob.glob(os.path.join(folder, p)))


def page(dur, css, body, js, bg='transparent'):
    return f'''<!doctype html><html lang="en" data-resolution="portrait"><head><meta charset="UTF-8">
<meta name="viewport" content="width=1080, height=1920">{FONTS}{GSAP}<style>
*{{margin:0;padding:0;box-sizing:border-box}} html,body{{width:1080px;height:1920px;overflow:hidden;background:{bg}}}
#root{{position:relative;width:100%;height:100%;overflow:hidden}}
{css}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.2f}" data-width="1080" data-height="1920">
{body}</div>
<script>const tl=gsap.timeline({{paused:true}});
{js}
window.__timelines["main"]=tl;</script></body></html>'''


def render(work, name, doc, files=(), alpha=False):
    """Writes a HyperFrames project to work/name, copies files (src, dest-name) into its assets/, renders it."""
    d = os.path.join(work, name)
    os.makedirs(os.path.join(d, 'assets'), exist_ok=True)
    json.dump({'paths': {'assets': 'assets'}}, open(os.path.join(d, 'hyperframes.json'), 'w'))
    json.dump({'name': name, 'private': True, 'type': 'module'}, open(os.path.join(d, 'package.json'), 'w'))
    json.dump({'id': name, 'name': name}, open(os.path.join(d, 'meta.json'), 'w'))
    for src, dst in files:
        shutil.copy(src, os.path.join(d, 'assets', dst))
    open(os.path.join(d, 'index.html'), 'w').write(doc)
    out = os.path.join(d, 'gfx.mov' if alpha else 'gfx.mp4')
    r = subprocess.run(HF + ['render', *(['--format', 'mov'] if alpha else []), '-o', os.path.basename(out), '--quiet'],
                       cwd=d, capture_output=True, text=True)
    if r.returncode or not os.path.exists(out):
        sys.exit(f'hyperframes render failed in {d}\n{(r.stderr or r.stdout)[-1500:]}')
    return out


def cut(clip, work, start, dur):
    """Trims to the segment, fills 1080x1920 (scale + centre crop), 30 fps, no audio."""
    seg = os.path.join(work, 'seg.mp4')
    ff('-ss', str(start), '-i', clip, '-t', str(dur), '-an',
       '-vf', f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}',
       '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', seg)
    n = subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v', '-show_entries', 'stream=nb_read_packets',
                        '-of', 'csv=p=0', seg], capture_output=True, text=True).stdout.strip()
    if not n.isdigit() or int(n) < FPS // 2:
        sys.exit(f'the clip has (almost) no video after {start}s: try a smaller --start')
    return seg


def matte(seg, model):
    """Person matte per frame -> seg-mask.mp4 (rembg at half size, light flicker damping, biggest blob only)."""
    from PIL import Image
    from rembg import new_session, remove
    from scipy import ndimage
    out, w, h = seg.replace('.mp4', '-mask.mp4'), W // 2, H // 2
    sess = new_session(model)
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', seg, '-vf', f'scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{w}x{h}', '-r', str(FPS), '-i', '-',
                            '-vf', f'scale={W}:{H}:flags=bicubic', '-c:v', 'libx264', '-crf', '12', '-pix_fmt', 'yuv420p', out],
                           stdin=subprocess.PIPE)
    prev, n = None, 0
    while (buf := dec.stdout.read(w * h * 3)) and len(buf) == w * h * 3:
        m = np.asarray(remove(Image.frombytes('RGB', (w, h), buf), session=sess, only_mask=True), np.float32)
        m = m if prev is None else 0.65 * m + 0.35 * prev
        prev = m
        lab, k = ndimage.label(m > 60)
        if k > 1:
            sizes = ndimage.sum(np.ones_like(lab), lab, range(1, k + 1))
            m[~ndimage.binary_dilation(lab == np.argmax(sizes) + 1, iterations=4)] = 0
        enc.stdin.write(m.clip(0, 255).astype(np.uint8).tobytes())
        n += 1
        print(f'\r  cutting you out: frame {n}', end='', flush=True)
    print()
    enc.stdin.close(); enc.wait(); dec.wait()
    if not n:
        sys.exit('no frames decoded: check the clip path and --start')
    return out


def behind(seg, mask, gfx, out, blur=1, replace_bg=False):
    """Graphics go behind you: clip, then gfx, then you (clip through the matte) on top.
    replace_bg: gfx is a full background, so the original background is dropped."""
    base = '[0]' if replace_bg else '[v2][0]overlay[b];[b]'
    ff('-i', gfx, '-i', seg, '-i', mask, '-filter_complex',
       f'[1]{"null[v1]" if replace_bg else "split[v1][v2]"};[2]format=gray,boxblur={blur}[m];[v1][m]alphamerge[fg];{base}[fg]overlay,format=yuv420p',
       '-shortest', '-c:v', 'libx264', '-crf', '16', '-map_metadata', '-1', '-movflags', '+faststart', out)


# ---------------------------------------------------------------- effects

def fx_trail(a, seg, mask, work):
    """Fine white line with a soft glow traces your outline: sweeps on, then a bright comet keeps circling."""
    from scipy import ndimage
    def rd(path, c):
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'gray' if c == 1 else 'rgb24', '-'],
                             stdout=subprocess.PIPE)
        while (b := p.stdout.read(W * H * c)) and len(b) == W * H * c:
            yield np.frombuffer(b, np.uint8).reshape(H, W, c).astype(np.float32)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-map_metadata', '-1', '-movflags', '+faststart', a.out],
                           stdin=subprocess.PIPE)
    yy, xx = np.mgrid[0:H, 0:W]
    glow_rgb = np.array([int(a.color[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
    ang = None
    for i, (f, m) in enumerate(zip(rd(seg, 3), rd(mask, 1))):
        m = ndimage.gaussian_filter(m[..., 0], 3) > 128
        if ang is None:
            cy, cx = ndimage.center_of_mass(m) if m.any() else (H / 2, W / 2)
            ang = (np.arctan2(yy - cy, xx - cx) + np.pi / 2) % (2 * np.pi)  # 0 at the top of the head, clockwise
        band = ndimage.binary_dilation(m, iterations=7) & ~ndimage.binary_dilation(m, iterations=3)
        t = i / FPS
        sweep = min(1, max(0, (t - 0.15) / 0.9)) * 2 * np.pi
        on = band & (ang <= sweep)
        head = (sweep + (t - 1.05) * 4.0 if t > 1.05 else sweep) % (2 * np.pi)
        d = np.minimum(np.abs(ang - head), 2 * np.pi - np.abs(ang - head))
        core = on.astype(np.float32) * 0.9 + band * np.clip(1 - d / 0.5, 0, 1) ** 2
        glow = ndimage.gaussian_filter(core, 14) * 3.0 + ndimage.gaussian_filter(core, 40) * 2.0
        a_glow = np.clip(glow, 0, 0.85)[..., None]
        out = f * (1 - a_glow) + glow_rgb * a_glow
        a_core = np.clip(ndimage.gaussian_filter(core, 1.2), 0, 1)[..., None]
        out = out * (1 - a_core) + 255 * a_core
        enc.stdin.write(out.clip(0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()


def fx_word(a, seg, mask, work):
    """A big word behind you, words fading up one at a time, with an optional small label under it."""
    words = ' '.join(f'<span>{html.escape(w)}</span>' for w in a.text.split())
    css = (f'#w{{position:absolute;left:0;right:0;top:{a.top}px;text-align:center;font-family:Urbanist;font-weight:500;'
           f'font-size:{a.size}px;letter-spacing:-{a.size // 32}px;color:{a.color};line-height:1;text-shadow:0 0 60px {a.glow}73}}'
           '#w span{display:inline-block;opacity:0}'
           f'#lab{{position:absolute;left:0;right:0;top:{a.top + int(a.size * 1.15)}px;text-align:center;font-family:"Space Mono";'
           f'font-size:26px;letter-spacing:8px;color:{a.color};opacity:0}}')
    js = ("tl.fromTo('#w span',{opacity:0,y:30},{opacity:1,y:0,duration:.4,ease:'power2.out',stagger:.25},.15);"
          f"tl.fromTo('#w',{{scale:1}},{{scale:1.04,duration:{a.dur},ease:'none'}},0);"
          "tl.fromTo('#lab',{opacity:0},{opacity:.9,duration:.4},.7);")
    gfx = render(work, 'word', page(a.dur, css, f'<div id="w">{words}</div><div id="lab">{html.escape(a.label)}</div>', js), alpha=True)
    behind(seg, mask, gfx, a.out)


def fx_wall(a, seg, mask, work):
    """Frosted glass tiles of your past reels drift behind you in three columns."""
    tiles = images(a.tiles)
    if not tiles:
        sys.exit(f'no images in {a.tiles}: add screenshots of your reels (or run: python fx.py placeholders)')
    files = [(t, f't{i:02d}{os.path.splitext(t)[1].lower()}') for i, t in enumerate(tiles)]
    cols = ''
    for c in range(3):
        cells = ''.join(f'<div class="t"><img src="assets/{files[(c * 7 + r) % len(files)][1]}"></div>' for r in range(7))
        cols += f'<div class="col" id="c{c}" style="left:{40 + c * 340}px">{cells}</div>'
    css = (f'#root{{background:radial-gradient(110% 70% at 50% 35%,#FFFFFF,{a.tint} 70%)}}'
           '.col{position:absolute;top:-600px;width:320px;display:flex;flex-direction:column;gap:20px}'
           '.t{width:320px;height:569px;border-radius:30px;overflow:hidden;position:relative}'
           '.t img{width:100%;height:100%;object-fit:cover;display:block}'
           ".t::after{content:'';position:absolute;inset:0;border-radius:30px;background:linear-gradient(160deg,rgba(255,255,255,.38),"
           'rgba(255,255,255,.08) 45%,rgba(255,255,255,.2));box-shadow:inset 0 0 0 1.5px rgba(255,255,255,.7)}'
           f'#veil{{position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,{a.tint}8c)}}')
    d = a.dur
    js = (f"tl.fromTo('#c0',{{y:0}},{{y:-260,duration:{d},ease:'none'}},0);"
          f"tl.fromTo('#c1',{{y:-380}},{{y:-60,duration:{d},ease:'none'}},0);"
          f"tl.fromTo('#c2',{{y:-40}},{{y:-340,duration:{d},ease:'none'}},0);"
          "tl.fromTo('.col',{opacity:0,scale:1.06},{opacity:1,scale:1,duration:.5,ease:'power2.out'},0);")
    gfx = render(work, 'wall', page(d, css, cols + '<div id="veil"></div>', js), files)
    behind(seg, mask, gfx, a.out, blur=2, replace_bg=True)


def fx_clothesline(a, seg, mask, work):
    """Twine line with wooden pegs, your items hanging off it, a big word behind the line, all behind you.
    --pull N makes item N get yanked off the line (time it to your hand reaching up)."""
    from PIL import Image
    items = images(a.items)
    if not items:
        sys.exit(f'no images in {a.items}: add cut-out PNGs of your things (or run: python fx.py placeholders)')
    X0, X1, Y0, SAG = -40, 1120, a.line_y, 34
    line_y = lambda x: Y0 + SAG * 4 * ((x - X0) / (X1 - X0)) * (1 - (x - X0) / (X1 - X0))
    slot = 940 / len(items)
    files, els, js = [('%s/peg.png' % ASSETS, 'peg.png')], [], []
    for k, f in enumerate(items):
        name = f'i{k}{os.path.splitext(f)[1].lower()}'
        files.append((f, name))
        w, h = Image.open(f).size
        hh = min(a.item_h, (slot - 16) * h / w)  # fit the slot so neighbours never overlap
        wd, x = w * hh / h, 70 + slot * (k + 0.5)
        y = line_y(x)
        els.append(f'<div class="it" id="it{k}" style="left:{x - wd / 2:.0f}px;top:{y - 14:.0f}px;width:{wd:.0f}px;height:{hh:.0f}px">'
                   f'<img src="assets/{name}"></div><img class="peg" id="pg{k}" src="assets/peg.png" style="left:{x - 16:.0f}px;top:{y - 64:.0f}px">')
        if k + 1 == a.pull:  # reach up, tug, and it follows your hand down and out of frame
            t = a.pull_at
            js.append(f"tl.to('#it{k}',{{y:-18,rotation:-6,duration:.12,ease:'power2.out'}},{t:.2f});"
                      f"tl.to('#it{k}',{{x:-150,y:360,rotation:20,duration:.42,ease:'power1.inOut'}},{t + .12:.2f});"
                      f"tl.to('#it{k}',{{opacity:0,duration:.18}},{t + .48:.2f});"
                      f"tl.fromTo('#pg{k}',{{rotation:0}},{{rotation:6,duration:.3,ease:'elastic.out(1,.3)',transformOrigin:'50% 50%'}},{t + .12:.2f});")
        else:
            js.append(f"tl.fromTo('#it{k}',{{rotation:{(-1) ** k * 2.5}}},{{rotation:{(-1) ** k * -2.5},duration:{1.1 + k * .13:.2f},"
                      "ease:'sine.inOut',yoyo:true,repeat:3},0);")
    pts = ' '.join(f'{x},{line_y(x):.1f}' for x in range(X0, X1 + 1, 20))
    css = (f'#sm{{position:absolute;left:70px;top:860px;font-family:Urbanist;font-weight:500;font-size:120px;line-height:.95;letter-spacing:-4px;color:{a.color}}}'
           f'#big{{position:absolute;left:0;right:0;top:{Y0 - 230}px;text-align:center;font-family:Urbanist;font-weight:500;font-size:290px;'
           f'letter-spacing:-11px;color:{a.color};line-height:1}}'
           'svg{position:absolute;left:0;top:0}'
           '.it{position:absolute;transform-origin:50% 0;filter:drop-shadow(0 10px 14px rgba(60,40,30,.18))}'
           '.it img{width:100%;height:100%;display:block}'
           '.peg{position:absolute;width:32px;height:125px;z-index:5;filter:drop-shadow(0 3px 4px rgba(60,40,20,.25))}')
    body = (f'<div id="sm">{"<br>".join(html.escape(s) for s in a.small.split("|"))}</div><div id="big">{html.escape(a.big)}</div>'
            f'<svg width="1080" height="{Y0 + 140}"><polyline points="{pts}" fill="none" stroke="#9C7A55" stroke-width="5"/>'
            f'<polyline points="{pts}" fill="none" stroke="#C9A77E" stroke-width="3" stroke-dasharray="6 7"/></svg>' + ''.join(els))
    js = ("tl.fromTo('#sm',{opacity:0,y:30},{opacity:1,y:0,duration:.4,ease:'power2.out'},.05);"
          "tl.fromTo('#big',{opacity:0,y:30},{opacity:1,y:0,duration:.4,ease:'power2.out'},.75);" + ''.join(js))
    gfx = render(work, 'clothesline', page(a.dur, css, body, js), files, alpha=True)
    behind(seg, mask, gfx, a.out)


def fx_fan(a, seg, mask, work):
    """Open-book flipbook of your past reels on the top half, your clip underneath."""
    pages = images(a.tiles)
    if len(pages) < 3:
        sys.exit(f'need at least 3 images in {a.tiles} (or run: python fx.py placeholders)')
    pages = pages[:21]
    files = [(p, f'p{i:02d}{os.path.splitext(p)[1].lower()}') for i, p in enumerate(pages)] + [(seg, 'me.mp4')]
    P = [f'assets/{n}' for _, n in files[:-1]]
    PW, PH, X0, Y0, STEP, TURN, D = 360, 640, 540, 150, 0.15, 0.5, a.dur
    N = (len(P) - 1) // 2  # turning leaves (front + back); the last page is the base
    leaves = ''.join(f'<div class="lf" id="lf{k}" style="z-index:{100 - k}"><div class="f"><img src="{P[2 * k]}"><i class="sh"></i></div>'
                     f'<div class="f b"><img src="{P[2 * k + 1]}"><i class="sh"></i></div></div>' for k in range(N))
    js = (f"tl.fromTo('#book',{{x:-{PW // 2},rotationX:18,y:30,opacity:0}},{{x:0,rotationX:8,y:0,opacity:1,duration:.45,ease:'power3.out'}},0);"
          f"tl.to('#book',{{rotationX:4,duration:{D - 0.45:.2f},ease:'none'}},.45);")
    for k in range(N):
        t = 0.2 + k * STEP
        js += (f"tl.to('#lf{k}',{{rotationY:-180,duration:{TURN},ease:'power2.inOut'}},{t:.2f});"
               f"tl.set('#lf{k}',{{zIndex:{200 + k}}},{t + TURN / 2:.2f});"
               f"tl.fromTo('#lf{k} .f:not(.b) .sh',{{opacity:0}},{{opacity:.55,duration:{TURN / 2},ease:'power1.in'}},{t:.2f});"
               f"tl.fromTo('#lf{k} .b .sh',{{opacity:.55}},{{opacity:0,duration:{TURN / 2},ease:'power1.out'}},{t + TURN / 2:.2f});")
    css = (f'#root{{background:radial-gradient(120% 60% at 50% 28%,#FFFFFF 0%,{a.tint} 62%)}}'
           '#lab{position:absolute;left:60px;right:60px;top:64px;display:flex;justify-content:space-between;font-family:"Space Mono";'
           'font-size:24px;letter-spacing:5px;color:#141414;opacity:.55;text-transform:uppercase}'
           f'#book{{position:absolute;left:{X0}px;top:{Y0}px;width:{PW}px;height:{PH}px;perspective:3000px;transform-style:preserve-3d}}'
           f'#floor{{position:absolute;left:{X0 - PW - 20}px;top:{Y0 + PH + 4}px;width:{2 * PW + 40}px;height:40px;border-radius:50%;'
           'background:radial-gradient(closest-side,rgba(20,20,20,.16),rgba(20,20,20,0))}'
           f'.lf,.base{{position:absolute;left:0;top:0;width:{PW}px;height:{PH}px;transform-origin:0 50%;transform-style:preserve-3d}}'
           '.f{position:absolute;inset:0;border-radius:4px 30px 30px 4px;overflow:hidden;backface-visibility:hidden;background:#fff}'
           '.f.b{transform:rotateY(180deg);border-radius:30px 4px 4px 30px}.f img{width:100%;height:100%;object-fit:cover;display:block}'
           ".f::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,rgba(20,20,20,.14),rgba(20,20,20,0) 9%)}"
           '.f.b::after{background:linear-gradient(270deg,rgba(20,20,20,.14),rgba(20,20,20,0) 9%)}'
           '.sh{position:absolute;inset:0;background:linear-gradient(90deg,rgba(20,20,20,0),rgba(20,20,20,.5));opacity:0}.base{z-index:1}'
           f'#left{{position:absolute;left:{-PW}px;top:0;width:{PW}px;height:{PH}px;border-radius:30px 4px 4px 30px;background:#fff}}'
           '#me{position:absolute;left:40px;top:900px;width:1000px;height:980px;border-radius:48px;overflow:hidden;outline:1px solid rgba(20,20,20,.06)}'
           f'#me video{{width:1000px;height:1778px;object-fit:cover;margin-top:-{a.face_y}px;display:block}}')
    body = (f'<div id="lab"><span>{html.escape(a.label)}</span><span>{html.escape(a.handle)}</span></div><div id="floor"></div>'
            f'<div id="book"><div id="left"></div><div class="base"><div class="f"><img src="{P[2 * N]}"></div></div>{leaves}</div>'
            f'<div id="me"><video class="clip" src="assets/me.mp4" muted playsinline data-start="0" data-duration="{D:.2f}" data-track-index="2"></video></div>')
    gfx = render(work, 'fan', page(D, css, body, js, bg=a.tint), files)
    ff('-i', gfx, '-c:v', 'libx264', '-crf', '16', '-map_metadata', '-1', '-movflags', '+faststart', a.out)


def fx_iphone(a, seg, mask, work):
    """Your clip plays in a real iPhone, which shrinks to the left while a hand-drawn wireframe draws itself on."""
    phone, pmask = os.path.join(ASSETS, 'iphone.png'), os.path.join(ASSETS, 'iphone-mask.png')
    webm = os.path.join(work, 'phone.webm')
    ff('-loop', '1', '-i', phone, '-i', seg, '-loop', '1', '-i', phone, '-loop', '1', '-i', pmask, '-filter_complex',
       '[1]scale=574:1254:force_original_aspect_ratio=increase,crop=574:1254[v];[0][v]overlay=252:321[b];'
       '[2]colorkey=0x00FF00:0.32:0.08,despill=type=green[k];[b][k]overlay[p];[3]format=gray[m];[p][m]alphamerge,crop=620:1320:230:290',
       '-frames:v', str(round(a.dur * FPS)), '-r', str(FPS), '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '6M', '-auto-alt-ref', '0', webm)
    svg = clean_svg(a.wireframe).replace('<svg ', '<svg id="wf" style="position:absolute;left:-10px;top:-10px" ', 1)
    css = (f'#root{{background:radial-gradient(90% 60% at 50% 42%,#FFFFFF,{a.tint} 72%)}}'
           '#ph{position:absolute;left:230px;top:290px;width:620px;height:1320px;transform-origin:310px 660px;'
           'filter:drop-shadow(0 30px 40px rgba(120,60,80,.18))}#ph video{width:100%;height:100%;display:block}')
    body = (f'<div id="ph"><video class="clip" src="assets/phone.webm" muted playsinline data-start="0" data-duration="{a.dur:.2f}" '
            f'data-track-index="1"></video></div>{svg}')
    js = """tl.fromTo('#ph',{scale:1.22},{scale:1.22,duration:0.4},0);
tl.to('#ph',{scale:0.6,x:-255,y:20,duration:0.5,ease:'power3.inOut'},0.4);
const gs=Array.from(document.querySelectorAll('#wf > g')).filter(g=>g.getBBox().width>2);
gs.forEach((g,i)=>{
  const t=0.8+i*0.08;
  if(g.querySelector('text')){  // words are written left to right like a pen
    tl.fromTo(g,{clipPath:'inset(-20% 100% -20% 0)'},{clipPath:'inset(-20% 0% -20% 0)',duration:0.4,ease:'none'},t);
  }
  g.querySelectorAll('path').forEach(p=>{
    const s=p.getAttribute('stroke'), f=p.getAttribute('fill');
    if(!p.getAttribute('stroke-dasharray') && s && s!=='none' && s!=='transparent' && (!f || f==='none')){
      const L=Math.ceil(p.getTotalLength())+2; p.style.strokeDasharray=L;
      tl.fromTo(p,{strokeDashoffset:L},{strokeDashoffset:0,duration:0.38,ease:'power1.inOut'},t);
    }
  });
  tl.fromTo(g,{opacity:0},{opacity:1,duration:0.15},t);
});"""
    gfx = render(work, 'iphone', page(a.dur, css, body, js, bg=a.tint), [(webm, 'phone.webm')])
    ff('-i', gfx, '-c:v', 'libx264', '-crf', '16', '-map_metadata', '-1', '-movflags', '+faststart', a.out)


def fx_tiny(a, seg, mask, work):
    """A small, real copy of you perched on your own shoulder, talking along (same clip, cut out and shrunk)."""
    from PIL import Image
    m = np.asarray(Image.open(_first(mask, work)))
    ys, xs = np.nonzero(m > 128)
    if not len(ys):
        sys.exit('could not find you in the first frame, try a different --start')
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    head_x = int(xs[ys < y0 + 120].mean())  # middle of the top of your head
    side = -1 if a.side == 'left' else 1
    band_x = int(np.clip(head_x + side * 0.2 * W, 40, W - 40))
    cfg = {'bg': seg, 'bg_mask': mask, 'fg': seg, 'fg_mask': mask, 'fg_size': [W, H],
           'crop': [int(x0), int(y0), int(x1 - x0), int(y1 - y0)], 'seat': int((y1 - y0) * a.seat), 'out': a.out,
           'perches': [{'t0': 0.1, 't1': a.dur - 0.1, 'track': [band_x - 18, band_x + 18], 'below': int(y0) + 60, 'x': a.x or band_x,
                        'h': a.h, 'front': True, 'dy': 10, 'real': True, 'shadow': 0.45}]}
    cfg_path = os.path.join(work, 'tiny.json')
    json.dump(cfg, open(cfg_path, 'w'), indent=1)
    print(f'  tiny config: {cfg_path} (edit it and run tiny.py on it to fine-tune)')
    run([sys.executable, os.path.join(HERE, 'tiny.py'), cfg_path])


SVG_OK = {'svg', 'g', 'path', 'text', 'tspan', 'defs', 'style', 'rect', 'ellipse', 'circle', 'line', 'polyline', 'polygon', 'mask'}


def clean_svg(path):
    """The wireframe is pasted into the render page, so keep only drawing elements: no scripts, handlers or outside links."""
    import xml.etree.ElementTree as ET
    NS = '{http://www.w3.org/2000/svg}'
    ET.register_namespace('', NS[1:-1])
    root = ET.parse(path).getroot()
    if root.tag != NS + 'svg':
        sys.exit(f'{path} is not an svg')
    def scrub(el):
        for child in list(el):
            if not child.tag.startswith(NS) or child.tag[len(NS):] not in SVG_OK:
                el.remove(child)
            else:
                scrub(child)
        for k in list(el.attrib):
            v = el.attrib[k].strip().lower()
            if k.lower().startswith('on') or ('href' in k.lower() and not v.startswith('data:')) or v.startswith('javascript:'):
                del el.attrib[k]
    scrub(root)
    return ET.tostring(root, encoding='unicode')


def _first(video, work):
    png = os.path.join(work, 'first.png')
    ff('-i', video, '-frames:v', '1', '-pix_fmt', 'gray', png)
    return png


# ---------------------------------------------------------------- demo assets

def placeholders(out='reel-effects-demo'):
    """Plain stand-ins so every effect runs before you have your own: tiles for wall/fan, tags for the clothesline."""
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 90)
    except OSError:
        font = ImageFont.load_default()
    pal = ['#ED84B0', '#F6C1D6', '#FFD9A8', '#BFE3D0', '#C9D7F8', '#E5D4F7', '#FCE9A6']
    os.makedirs(f'{out}/tiles', exist_ok=True); os.makedirs(f'{out}/items', exist_ok=True)
    for i in range(14):
        im = Image.new('RGB', (540, 960), pal[i % len(pal)])
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((60, 600, 480, 640), 20, fill='white'); d.rounded_rectangle((60, 670, 380, 710), 20, fill='white')
        d.text((60, 120), f'reel {i + 1:02d}', font=font, fill='white')
        im.save(f'{out}/tiles/{i + 1:02d}.jpg', quality=90)
    for i, (w, h) in enumerate([(160, 520), (300, 420), (380, 380), (300, 460), (220, 520)]):
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), 24, fill=pal[i])
        im.save(f'{out}/items/{i + 1}.png')
    print(f'demo tiles + items in ./{out}/')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('effect', choices=['clothesline', 'trail', 'word', 'wall', 'tiny', 'fan', 'iphone', 'placeholders'])
    ap.add_argument('clip', nargs='?', help='your talking clip (any size, vertical works best)')
    ap.add_argument('--start', type=float, default=0, help='where in the clip the effect starts, seconds')
    ap.add_argument('--dur', type=float, default=None, help='length in seconds (default 2.4, iphone 3.6)')
    ap.add_argument('--out', help='output mp4 (default <clip>-<effect>.mp4)')
    ap.add_argument('--model', default='u2net', help='rembg model: u2net (fast) or birefnet-general (cleaner hair, slower)')
    ap.add_argument('--color', default=None, help='main colour, hex (default #ED84B0, word default #FFFFFF)')
    ap.add_argument('--tint', default='#FFEEF5', help='soft background tint for wall/fan/iphone, hex')
    ap.add_argument('--text', default='one take.', help='word: the big word(s)')
    ap.add_argument('--label', default='', help='word: small caps line under it | fan: top-left label')
    ap.add_argument('--top', type=int, default=560, help='word: distance from the top, px')
    ap.add_argument('--size', type=int, default=250, help='word: font size, px')
    ap.add_argument('--tiles', default='reel-effects-demo/tiles', help='wall/fan: folder of reel screenshots')
    ap.add_argument('--handle', default='', help='fan: top-right label, e.g. your @')
    ap.add_argument('--face-y', type=int, default=540, help='fan: how far to slide your clip up inside its window, px')
    ap.add_argument('--items', default='reel-effects-demo/items', help='clothesline: folder of cut-out PNGs (left to right)')
    ap.add_argument('--small', default='everything|i use to', help='clothesline: small text, | for a new line')
    ap.add_argument('--big', default='create', help='clothesline: big word behind the line')
    ap.add_argument('--line-y', type=int, default=380, help='clothesline: height of the line, px from the top')
    ap.add_argument('--item-h', type=int, default=330, help='clothesline: max item height, px')
    ap.add_argument('--pull', type=int, default=0, help='clothesline: item number you pull off the line (0 = none)')
    ap.add_argument('--pull-at', type=float, default=1.5, help='clothesline: second your hand grabs it')
    ap.add_argument('--wireframe', default=os.path.join(ASSETS, 'wireframe.svg'), help='iphone: Excalidraw SVG export')
    ap.add_argument('--side', choices=['left', 'right'], default='right', help='tiny: which shoulder (as you look at the screen)')
    ap.add_argument('--h', type=int, default=330, help='tiny: height of the tiny you, px')
    ap.add_argument('--x', type=int, default=0, help='tiny: override where it sits, px from the left')
    ap.add_argument('--seat', type=float, default=0.55, help='tiny: seat line as a fraction of your height in frame')
    a = ap.parse_args()
    if a.effect == 'placeholders':
        return placeholders()
    if not a.clip or not os.path.isfile(a.clip):
        sys.exit('give me a clip: python fx.py <effect> path/to/clip.mp4')
    for tool in ('ffmpeg', 'npx'):
        if not shutil.which(tool):
            sys.exit(f'{tool} not found: run setup.sh first')
    a.dur = a.dur or (3.6 if a.effect == 'iphone' else 2.4)
    a.color = a.color or ('#FFFFFF' if a.effect == 'word' else '#ED84B0')
    a.glow = '#ED84B0'
    for c in (a.color, a.tint):  # these go straight into CSS
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', c):
            sys.exit(f'colours are 6-digit hex like #ED84B0, got {c}')
    a.out = os.path.abspath(a.out or f'{os.path.splitext(os.path.basename(a.clip))[0]}-{a.effect}.mp4')
    work = os.path.abspath(os.path.join('reel-effects-work', a.effect))
    shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
    print(f'{a.effect}: cutting {a.dur}s from {a.start}s')
    seg = cut(a.clip, work, a.start, a.dur)
    mask = matte(seg, a.model) if a.effect in ('trail', 'word', 'wall', 'clothesline', 'tiny') else None
    globals()[f'fx_{a.effect}'](a, seg, mask, work)
    print(f'done: {a.out}')


if __name__ == '__main__':
    main()
