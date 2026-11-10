# 51 Free Video Effects for Claude

Free viral video effects for Instagram Reels, TikTok and YouTube Shorts, made inside Claude Code. Drop your video into Claude, type `/effects` and the name of an effect. That's the whole edit.

Made by [@vibha.in.progress](https://instagram.com/vibha.in.progress) 💛

> **Want the full studio?** These are the free starter versions from **[Hop Studio, my AI video editing studio inside Claude](https://vibha.is/ai-video-studio?source=effects-repo)**: 220+ video effects, 30+ caption styles and 150 sound effects, with sound design and hand-tuned timing. It runs on the Claude plan you already have.

![The first 45 effects](assets/preview.jpg)

## Install (one line)

Open the Terminal app (or the terminal inside Claude Code) and paste:

```bash
git clone https://github.com/Vibha-Ramprakash/claude-video-effects ~/.claude/skills/effects
```

On Windows (PowerShell), use `$HOME\.claude\skills\effects` instead of `~/.claude/skills/effects`.

Then restart Claude Code. That's it.

> Not sure how? Open Claude Code and paste: **"Install the skill from github.com/Vibha-Ramprakash/claude-video-effects into ~/.claude/skills/effects"**. Claude will do it for you.

## Use it

1. Open Claude Code (the app or the terminal).
2. Drag your video into the chat.
3. Type the effect you want:

```
/effects orbit from 3 to 6 seconds
/effects spotlight when I say "kill the lights", with the word Claudit behind me
/effects comment-box at the end, typing CLAUDE
/effects glass-widgets for the first 3 seconds
```

The very first time, Claude sets itself up (about 2 minutes). It needs `ffmpeg` and Python, and it installs them for you if they're missing.

Claude checks a few frames first, fixes anything that covers your face, then renders `yourvideo_effects.mp4` right next to your original. Your audio stays as it was.

You can stack effects in one go: *"Add locked-on from 6 to 10s, then orbit from 10 to 13s, then a reject stamp on 'no'."*

| # | Tipo | Qué hace |
|---|---|---|
| 1 | `noise` | Los reels se amontonan detrás de tu cabeza |
| 2 | `lineup` | Mosaicos numerados se abren en abanico sobre tu cabeza |
| 3 | `locked-on` | Los corchetes se fijan a tu cara y la cámara te sigue |
| 4 | `orbit` | Tus reels giran alrededor de tu cabeza, detrás de ti en la parte superior |
| 5 | `lean-in` | Un acercamiento rápido (zoom) en una sola palabra |
| 6 | `backdrop-word` | Una palabra gigante cae detrás de ti |
| 7 | `spotlight` | Apaga las luces y te mantiene iluminado |
| 8 | `the-bill` | Tus instrucciones se imprimen como un ticket de compra |
| 9 | `moody` | Una gradación de color cinematográfica y apagada |
| 10 | `swipe` | Un control deslizante de antes y después |
| 11 | `todo` | Una lista de tareas junto a tu cabeza que se marca a medida que hablas |
| 12 | `comment-box` | Un comentario de Instagram se escribe solo y se publica |
| 13 | `tap` | Un botón de Seguir cambia a Siguiendo |
| 14 | `pause-point` | Fotograma congelado con una flecha dibujada a mano |
| 15 | `uninstall` | Una barra de desinstalación con fallos (glitch) rompe el fotograma |
| 16 | `reel-frame` | Tu vídeo se encoge dentro de una tarjeta de reel |
| 17 | `shortcut-rain` | Teclas de teclado llueven detrás de ti |
| 18 | `reject-stamp` | Un gran sello rojo cae con fuerza |
| 19 | `countdown-flip` | Un reloj de cuenta atrás de 3, 2, 1 sobre tu cabeza |
| 20 | `rabbit-hole` | La habitación se aleja formando un túnel detrás de ti |
| 21 | `cover-star` | Te conviertes en la portada de una revista |
| 22 | `scribble` | Garabatos de rotulador se dibujan solos a tu alrededor |
| 23 | `glass-widgets` | Widgets de vidrio esmerilado y mini elementos flotan alrededor de tu cabeza |
| 24 | `red-collage` | Tú en blanco y negro, una palabra gigante roja detrás y tres líneas que impactan |
| 25 | `split-headline` | Una tarjeta de titular baja deslizándose y te empuja hacia la mitad inferior |
| 26 | `pastel-word` | Habitación lavanda, una palabra gigante detrás de ti y una tarjeta de perfil recibe un seguimiento |
| 27 | `check-pills` | Habitación con papel cuadriculado, tus reels anidados detrás y se hace clic en píldoras azules |
| 28 | `timeline` | Un aspecto de película roja oscura con una línea de tiempo de edición y un cabezal de reproducción brillante |
| 29 | `headline-box` | Un acercamiento con un titular limpio de dos líneas |
| 30 | `profile-wall` | Tu cuadrícula de reels llena la pared mientras un contador aumenta |
| 31 | `tier-list` | Una lista de clasificación (tier list) cae y Claude vuela al nivel S |
| 32 | `broll-split` | Vídeo de apoyo (B-roll) arriba con una pegatina de precio, tú abajo |
| 33 | `phone-fan` | Tus reels se despliegan en abanico como una mano de teléfonos |
| 34 | `dot-reveal` | Tu plano se forma a partir de puntos brillantes y luego se enfoca de golpe |
| 35 | `headline-wall` | Tus titulares se acumulan detrás de tu cabeza y luego aparece un total al frente |
| 36 | `checklist` | Una lista de tareas de Claude bajo tu barbilla, cada paso se marca en verde |
| 37 | `liquid-glass-graph` | Una tarjeta de vidrio líquido con un gráfico que asciende y un número que cuenta hacia arriba |
| 38 | `carousel-spin` | Tus reels giran a tu alrededor en un carrusel 3D |
| 39 | `match-cut` | Páginas de noticias cortadas en una palabra, fijadas en su lugar detrás de tu cabeza |
| 40 | `apple-toggles` | Los interruptores de iPhone se encienden bajo tu barbilla, una línea a la vez |
| 41 | `led-sign` | Las luces bajan y un letrero LED brillante se escribe solo detrás de ti |
| 42 | `slow-push` | Un acercamiento cinematográfico lento mientras la habitación se desenfoca |
| 43 | `over-the-shoulder-zoom` | Se acerca a una esquina con un gráfico de vidrio líquido junto a tu cabeza, y luego a la otra esquina con un segundo gráfico |
| 44 | `messages` | Las notificaciones de iMessage aparecen una tras otra con un brillo suave |
| 45 | `place-in-grid` | Te reduces al centro de tu cuadrícula de perfil de 3x3, tus reels aparecen alrededor con sus recuentos de visualizaciones |
| 46 | `tape-label` | Una tira de cinta amarilla con tu frase aterriza en tu pecho |
| 47 | `select-resize` | Un cuadro de selección azul agarra tu número y un cursor lo arrastra para hacerlo más grande |
| 48 | `wave-trim` | Las partes silenciosas de tu voz se recortan en pantalla hasta que solo quedan tus palabras |
| 49 | `huge-strike` | Una palabra con serifa enorme llena la pared detrás de ti y una línea roja la tacha |
| 50 | `crayon-write` | Un crayón rojo escribe tu palabra detrás de tu cabeza y la subraya |
| 51 | `fan-build` | Las portadas de tus reels se reparten en abanico detrás de tu cabeza, una tarjeta a la vez |
| 52 | `clothespin` | Cuelga una cuerda con pinzas de madera detrás de ti; las cosas entran sujetas a ella y un grand word se sitúa detrás de la línea. |
| **53** | `light-trail` | Una línea fina blanca con un suave resplandor traza tu contorno. |
| **54** | `text-behind` | Una palabra grande se sitúa detrás de ti, de modo que la cabeza cubre parte de ella. |
| **55** | `reel-wall` | Azulejos de cristal esmerolado de tus reels anteriores flotan subiendo y bajando detrás de ti. |
| **56** | `tiny-me` | Una copa pequeña y real de té se posa en tu propio hombro y habla a lo largo del vídeo. |
| **57** | `reel-fan` | Un libro abierto de tus reels anteriores pasa sus páginas por encima de tu clip. |
| **58** | `iphone` | Tu clip se reproduce en un iPhone que se encoge hacia un lado mientras se dibuja un wireframe a mano. |
| **59** | `iconos-en-orbita` | Los íconos de tus apps dan vueltas alrededor de tu cabeza en una elipse inclinada, pasando por delante y por detrás. |
| **60** | `dentro-del-chat-de-claude` | Tu vídeo se encoge y entra como archivo adjunto en una interfaz realista de Claude mientras se escriben tu mensaje y la respuesta. |
| **61** | `me-salgo-del-cuadro` | Tu vídeo se convierte en una tarjeta y tú creces para salirte del marco por arriba y los lados, mostrando el cuarto vacío debajo. |
| **62** | `zoom-de-camara` | Se superpone un visor de cámara con cuadrícula y se realizan tres zooms sucesivos y cortos con sonido de enfoque siguiendo tu cara. |
| **63** | `mi-video-en-un-telefono-en-3d` | Tu vídeo se reproduce en un iPhone 3D con interfaz de Reels que gira suavemente y entra desde el lateral. |
| **64** | `checklist-de-vidrio` | Una tarjeta de vidrio oscuro translúcido muestra una lista de tres pasos que se van tachando interactivamente con un visto y sonido de ding. |
| **65** | `pared-de-posters` | El fondo se vuelve una pared beige y aparecen cuatro pósters con diferentes tipografías y frases pegados con cinta alrededor de tu cabeza. |
| **66** | `zoom-con-corte` | Un zoom rápido con desenfoque hacia tu cara que culmina en un corte seco de vuelta a tu encuadre con una palabra gigante y parpadeante. |
| **67** | `dibujos-a-mano` | Te conviertes en sticker con un trazo punteado alrededor y dibujos animados (corazones, corona, estrellas) que se dibujan solos temblando estilo stop-motion. |
| **68** | `grafica-que-sube` | Una tarjeta de vidrio translúcido con un número grande que cuenta de 0 al valor real y barras verticales que crecen con una línea de tendencia verde. |
| **69** | `portada-de-revista` | El fondo adopta textura de papel beige, tu nombre gigante de marca en Bodoni Moda queda por detrás de tu cabeza y se añaden titulares, número y código de barras. |
| **70** | `poster-de-vidrio` | Tu fondo se ve a través de vidrio acanalado y emerge un póster de vidrio esmerilado en 3D con un título cromado y brillante. |
| **71** | `la-camara-se-aleja` | Tu vídeo se encoge hasta convertirse en una tarjeta central dentro de una pared de 13 tarjetas en bucle con los efectos anteriores. |
| **72** | `ponme-en-otro-lugar` | Te saca de tu cuarto para ubicarte en un escenario fotorrealista generado por IA (como un penthouse), integrando iluminación de ventanas, sombras y grano uniforme. |

```

Bonus looks: `/effects glitter-spotlight` (golden rays and sparkles), `cover-star look=editorial` (a classic magazine cover) and `liquid-glass-graph look=bento` (a glass dashboard around you).

Every effect follows your face. Anything that would cover your face goes behind your head instead.

**Tips**
- Vertical phone videos with you in frame work best.
- Say the timing in plain words ("when I say 'watch'"). Claude finds the exact second.
- Want your own reels in `orbit`, `noise`, `phone-fan` or `profile-wall`? Give Claude a folder of screenshots.
- Charts, counters and headlines should use your real numbers. Tell Claude what they are.
- It renders in 1080p. Ask for 4K if you want it (slower).

## Honest notes
- These are **starter versions**. They won't match the exact edit in my reel, which also has sound design and hand-tuned timing.
- It drafts, you approve. Watch the result before you post.
- No sounds or captions are added. Add those in CapCut.
- My full edit style (sound design, captions, grade) lives in **[Hop Studio](https://vibha.is/ai-video-studio?source=effects-repo)**, the AI video editing studio that runs inside Claude.

## If something goes wrong
Just tell Claude what you see ("the word covers my face", "it's too fast"). It will fix the plan and render again.

## More free tools for editing videos with Claude

- **[7 free caption styles for Claude](https://github.com/Vibha-Ramprakash/claude-caption-styles)**: animated captions timed to your voice. Type `/captions pop-sticker`.
- **[Hop Studio · AI video editing studio](https://vibha.is/ai-video-studio?source=effects-repo)**: 220+ effects, 30+ caption styles, 150 sound effects and a free masterclass.
- New effects every week on Instagram: [@vibha.in.progress](https://instagram.com/vibha.in.progress)

## Credits
Face tracking: [OpenCV YuNet](https://github.com/opencv/opencv_zoo) (MIT). Person cut-out: [MediaPipe Selfie Segmenter](https://ai.google.dev/edge/mediapipe/solutions/vision/image_segmenter) (Apache 2.0). Fonts: Archivo Black, Instrument Serif, Space Mono, Inter, Anton, Montserrat (SIL OFL) and Permanent Marker (Apache 2.0); licences are in `fonts/`. Everything else: MIT, see `LICENSE`.
