"""Tiny me: a small matted, talking copy of you perched on things in a shot.
The tiny copy sits on a perch line; everything of it below that line is hidden behind the object by
re-drawing the background's own pixels there, so the occlusion always matches the live frame.
Perch lines can be fixed (a desk or screen edge) or tracked from the background's person matte (shoulder, head).
"front": true perches draw the whole copy (a full-body clip sat on the edge, legs dangling) with a soft contact shadow
and a fade-drop entrance instead of rising from behind. "seat_x" = the seat column inside the crop (default: centre).
Normally fx.py writes the config and runs this for you: python tiny.py config.json"""
import json, subprocess, sys
import numpy as np
from scipy import ndimage

W, H, FPS = 1080, 1920, 30
cfg = json.load(open(sys.argv[1]))


def frames(path, gray=False, size=(W, H)):
    c, (w, h) = 1 if gray else 3, size
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'scale={w}:{h},fps={FPS}', '-f', 'rawvideo',
                          '-pix_fmt', 'gray' if gray else 'rgb24', '-'], stdout=subprocess.PIPE)
    while (b := p.stdout.read(w * h * c)) and len(b) == w * h * c:
        yield np.frombuffer(b, np.uint8).reshape(h, w, c) if c == 3 else np.frombuffer(b, np.uint8).reshape(h, w)


def tracked_top(mask, x0, x1, below=0):
    # highest matte row in a column band (top of head / shoulder), searching from row `below`
    rows = np.nonzero((mask[below:, x0:x1] > 128).mean(1) > 0.5)[0]
    return below + rows[0] if len(rows) else None


def cutout(rgb, m, crop, h, real=False):
    # crop -> cream paper edge (or a clean feathered matte when real) -> scale to height h; returns rgb, alpha (float 0-1)
    x, y, cw, ch = crop
    rgb, m = rgb[y:y + ch, x:x + cw].astype(np.float32), m[y:y + ch, x:x + cw].astype(np.float32) / 255
    edge = ndimage.gaussian_filter(ndimage.maximum_filter(m, 17), 1.2).clip(0, 1)
    out = np.where(m[..., None] > 0, rgb * m[..., None] + np.array([255, 246, 238]) * (1 - m[..., None]), [255, 246, 238])
    if real:  # no paper edge: your own pixels, edge pulled in a touch and softened so it sits in the shot
        out, edge = rgb, ndimage.gaussian_filter(ndimage.minimum_filter(m, 3), 1.0).clip(0, 1)
    s = h / ch
    zoom = lambda a: ndimage.zoom(a, (s, s) + (1,) * (a.ndim - 2), order=1)
    return zoom(out), zoom(edge)


def ease(u):
    return 1 - (1 - min(max(u, 0), 1)) ** 3


def main():
    bgs, bgm = frames(cfg['bg']), frames(cfg['bg_mask'], True) if cfg.get('bg_mask') else None
    fs = tuple(cfg.get('fg_size', (W, H)))  # a tight high-res crop of you keeps the tiny copy sharp
    fgs, fgm = frames(cfg['fg'], size=fs), frames(cfg['fg_mask'], True, fs)
    crop, seat = cfg['crop'], cfg['seat']  # seat = the seat row inside the crop
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-map_metadata', '-1', '-movflags', '+faststart', cfg['out']],
                            stdin=subprocess.PIPE)
    smooth = {}
    for n, (bg, fg, fm) in enumerate(zip(bgs, fgs, fgm)):
        t, out = n / FPS, bg.astype(np.float32).copy()
        bm = next(bgm) if bgm is not None else None
        for i, p in enumerate(cfg['perches']):
            if not p['t0'] <= t < p['t1']:
                continue
            if 'track' in p:  # perch line follows the background person's matte, lightly smoothed
                y = tracked_top(bm, *p['track'], p.get('below', 0))
                if y is not None:
                    smooth[i] = y if i not in smooth else 0.6 * smooth[i] + 0.4 * y
                if i not in smooth:  # not found yet: skip this frame rather than guess
                    continue
                line = int(smooth[i]) + p.get('dy', 0)
            else:
                line = p['line']
            rgb, a = cutout(fg, fm, crop, p['h'], p.get('real', False))
            s = p['h'] / crop[3]
            seat_x = cfg.get('seat_x', crop[2] / 2) * s
            left = int(p['x'] - seat_x)
            if p.get('front'):
                vis = min(ease((t - p['t0']) / 0.25), ease((p['t1'] - t) / 0.2))
                top = int(line - seat * s - (1 - vis) * 60)
                bottom = top + rgb.shape[0]
                a = a * vis
                sw = int(rgb.shape[1] * 0.5)  # soft contact shadow under the seat
                yy, xx = np.ogrid[-12:13, -sw:sw + 1]
                sh = np.exp(-(xx / (sw * 0.45)) ** 2 - (yy / 5.0) ** 2) * p.get('shadow', 0.28) * vis
                sy, sx = slice(line - 12, line + 13), slice(int(p['x']) - sw, int(p['x']) + sw + 1)
                if sx.start >= 0 and sx.stop <= W:
                    out[sy, sx] *= (1 - sh[..., None])
            else:
                rise = (1 - ease((t - p['t0']) / 0.35)) + (1 - ease((p['t1'] - t) / 0.25))  # pops up from behind, drops back down
                top = int(line - seat * s + rise * p['h'] * 0.9)
                bottom = line
            ys, xs = slice(max(top, 0), min(top + rgb.shape[0], bottom, H)), slice(max(left, 0), min(left + rgb.shape[1], W))
            if ys.start >= ys.stop:
                continue
            sub = (slice(ys.start - top, ys.stop - top), slice(xs.start - left, xs.stop - left))
            al = a[sub][..., None]
            out[ys, xs] = rgb[sub] * al + out[ys, xs] * (1 - al)
        enc.stdin.write(out.clip(0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    print('frames', n + 1, '->', cfg['out'])


if __name__ == '__main__':
    main()
