---
name: reel-effects
description: Add one of seven premium effects to a short piece of someone's own talking-head clip and render it as a 1080x1920 mp4. clothesline (twine line, wooden pegs, items hanging, text behind the person, optional item pulled off), light trail (fine white line with a glow tracing their outline), text behind (big word behind the person), reel wall (frosted tiles of past reels drifting behind them), tiny me (a small real copy of them on their own shoulder), reel fan (open-book flipbook of past reels over their clip), iphone (clip inside a real iPhone that shrinks while a hand-drawn Excalidraw wireframe draws on). Use when someone says "/effects", names any of these effects, or asks for a text-behind-me, cut-out, outline glow, tiny me, flipbook, clothesline or phone mockup effect on their video.
---

# Reel effects

One script does all seven: `scripts/fx.py`. Run it, don't rewrite it. Each run cuts a short segment from the clip (default 2.4 s, iphone 3.6 s), cuts the person out with rembg where the effect needs it, builds the graphics as a HyperFrames page, and layers it all with ffmpeg. Output: `<clip>-<effect>.mp4`, 1080x1920, 30 fps, no audio, no metadata.

## Before the first run

Check these, and fix anything missing:
- `ffmpeg` with vp9 (`brew install ffmpeg`), `node` / `npx`.
- The python environment: `~/.reel-effects-venv/bin/python`. If it's missing:
  ```bash
  python3 -m venv ~/.reel-effects-venv && ~/.reel-effects-venv/bin/pip install pillow numpy scipy "rembg[cpu]==2.0.85"
  ```
Always run the script as `~/.reel-effects-venv/bin/python <skill dir>/scripts/fx.py ...` from the folder where the person wants the output. The first cut-out downloads a ~170 MB model. HyperFrames is fetched by `npx` on the first render.

## Pick the moment

Ask which effect and which bit of the clip. If they don't know, look at a few frames (`ffmpeg -ss <t> -i clip -frames:v 1 f.jpg`) and pick a moment where they're facing camera with their head and shoulders in frame. Pass it as `--start`.

Their clip is theirs: never upload it anywhere. Work only on their machine.

## The effects

| effect | command | what they can bring |
|---|---|---|
| clothesline | `fx.py clothesline clip.mp4 --items myitems --big create --pull 3 --pull-at 1.5` (`--small` sets the small text, with a pipe character between lines) | cut-out PNGs of their things, left to right. `--pull N` yanks item N off the line at `--pull-at` seconds, so time it to their hand reaching up (look at frames). `--line-y` moves the line. |
| trail | `fx.py trail clip.mp4 --color "#ED84B0"` | a glow colour |
| word (text behind) | `fx.py word clip.mp4 --text "one take." --label "NO RESHOOTS"` | the word, `--top` and `--size` to place it so their head covers part of it |
| wall | `fx.py wall clip.mp4 --tiles myreels` | a folder of screenshots of their reels (9:16 looks best, 7+ is plenty) |
| tiny | `fx.py tiny clip.mp4 --side right` | nothing. `--h`, `--x`, `--seat` fine-tune it. It also writes `reel-effects-work/tiny/tiny.json`: edit that and rerun `scripts/tiny.py` on it to adjust without re-cutting |
| fan | `fx.py fan clip.mp4 --tiles myreels --label "the archive" --handle "@me"` | reel screenshots (3 to 21). `--face-y` slides their clip up or down in its window |
| iphone | `fx.py iphone clip.mp4 --wireframe mysketch.svg` | an Excalidraw SVG (see below) |

Shared options: `--start`, `--dur`, `--out`, `--color`, `--tint` (soft background colour), `--model birefnet-general` (cleaner hair, much slower).

No items or tiles yet? `fx.py placeholders` writes plain stand-ins to `./reel-effects-demo/`, which are the defaults, so every effect runs straight away.

### Their own items for the clothesline
They need transparent PNG cut-outs. From a photo: `~/.reel-effects-venv/bin/rembg i photo.jpg item.png`. Tall thin things (a pencil, a lipstick) and stickers of themselves work best. A sticker of their own face makes the best "pull" item.

### Their own wireframe for the iphone
1. Open excalidraw.com.
2. Draw a 1080 x 1920 rectangle and set its stroke to transparent. That's the frame.
3. Draw the sketch in the right half (the phone shrinks into the left half).
4. Export: select all, Export image, SVG, turn background OFF, and keep "embed scene" off.
Strokes draw on in the order they were made, and text writes itself left to right.

## Check before you hand it over

Pull 3 frames (`-ss 0.3`, `1.2`, `2.2`) into one contact sheet and look at it:
- Is the person cleanly cut out, with no halo and no missing hands?
- Does the text sit behind their head, not over their face?
- For clothesline `--pull`: does the item leave when their hand is there?

Fix with the options above and rerun. Then tell them where the mp4 is.
