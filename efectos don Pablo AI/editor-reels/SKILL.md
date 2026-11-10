---
name: editor-reels
description: Edita reels verticales grabados con el móvil: transcribe, corta silencios, muletillas y repeticiones, enseña el storyboard antes de montar, pone subtítulos y títulos con la marca, aplica los cambios que se le piden con una frase (color, títulos, ritmo, subtítulos, quitar a la persona, iconos e imágenes) y revisa el resultado antes de entregarlo. Úsala cuando el usuario pase un vídeo en bruto para editar.
---
# Editor de reels
1. Comprueba que hay ffmpeg, whisper.cpp (`whisper-cli` con el modelo `ggml-small.bin`) y Python con Pillow. Si falta algo, pide permiso e instálalo.
2. Lee marca.md (colores, letras, logo, palabra para comentar). Si no existe, pídeme los datos y créalo. Si la palabra para comentar de marca.md no es la que digo en el vídeo, usa la del vídeo y avísame.
3. Transcribe palabra por palabra con el alineado fino: `whisper-cli -m <modelo> -l es -ml 1 -sow --dtw small -ojf`, sobre el audio a 16 kHz mono. Sin `--dtw`, los tiempos fallan hasta 3 s cerca de las pausas. Comprueba los silencios con `ffmpeg -af silencedetect=noise=-45dB:d=0.25` antes de cortar. Corrige a mano los nombres que la transcripción escribe mal: Claude, ChatGPT, nombres de marcas y de personas.
4. Decide los cortes:
   - de cada frase, la última toma completa;
   - fuera los arranques fallidos, las frases repetidas y las muletillas;
   - las pausas de más de 0,4 s se dejan en unos 0,2 s;
   - corta en el punto más silencioso entre frases (por debajo de −55 dB), con 0,1 s de aire, nunca a mitad de palabra.
   Apunta cada corte con sus segundos en cortes.md. Si no hay muletillas, dilo.
5. Antes de montar nada, ni siquiera una prueba, enséñame un storyboard: una hoja con un dibujo por plano. Un plano es cada tramo que se queda entre dos cortes; su dibujo es un fotograma de ese tramo con el título, el subtítulo y el logo encima, y al lado su segundo y qué pasa. No montes nada hasta que te diga que sí.
6. Monta con ffmpeg a 1080×1920 y 30 fps:
   - pon `fps=30` antes de cortar por fotogramas;
   - respeta el giro que trae el vídeo del móvil;
   - quita los datos del archivo con `-map_metadata -1`, porque si no el vídeo publicado lleva el GPS del sitio donde grabaste;
   - si el iPhone grabó en HDR (HLG o Dolby Vision), pásalo a SDR con tonemap: `zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p`. Sin tonemap, los colores salen lavados o quemados.
   No cambies el color salvo que te lo pida («más cálido», «más oscuro»): entonces aplícalo al plano entero y enséñame un antes y un después.
7. Subtítulos:
   - de 3 a 6 palabras por bloque, en dos líneas como mucho, a la altura del pecho;
   - la palabra fuerte de cada bloque (el sustantivo, la cifra o el verbo clave), destacada según marca.md;
   - si la letra es variable (Inter, por ejemplo), dibuja los textos con Pillow y ponlos encima, porque drawtext y ASS no eligen su grosor;
   - deja algo más de aire entre palabras si el texto lleva contorno.
8. Gancho: en los 3 primeros segundos, un título grande de dos líneas con lo que promete el vídeo. La llamada a la acción va en la misma caja que el título, mientras digo la frase de comentar. Títulos, gráficos y llamada a la acción, con las letras y los colores de marca.md. Ningún texto tapa la cara ni se pisa con otro.
9. Cambios que te pida con una frase:
   - «Más alegre» = colores más cálidos, con un antes y un después.
   - «Más oscuro» = baja el color y el brillo y enciende los subtítulos.
   - «Mis mejores vídeos» = sus portadas dando vueltas arriba, sin tapar la cara.
   - «Títulos de revista» = nombre grande con serifa detrás de la cabeza.
   - «Cortes muy rápidos» = alterna plano normal y plano cerrado justo en los saltos de la toma, nunca al lado de uno. «Muy lento» = un acercamiento suave.
   - «Subtítulos grandes» o «pequeños» = cambia su tamaño.
   - «Que desaparezca» = recorta a la persona y bórrala poco a poco sobre la toma de la habitación vacía del final. Pide permiso para instalar lo que haga falta, por ejemplo rembg, MediaPipe o `npx hyperframes remove-background`.
   - «Iconos» = los logos oficiales de lo que nombro, en su palabra. «Imágenes» = un dibujo sencillo del concepto.
   - Para los efectos del vídeo de los 20 efectos, usa la skill efectos-reels.
   Nada tapa la cara.
10. Revisión obligatoria:
    - transcribe el vídeo terminado y busca palabras o frases repetidas;
    - mide las pausas con silencedetect, no con los tiempos de la transcripción;
    - corrige y repite hasta que no quede ninguna repetición ni ninguna pausa de más de 0,4 s dentro de una frase;
    - después saca una hoja con un fotograma por segundo y comprueba que nada tapa la cara ni se pisa.
11. Entrega un MP4 H.264 (CRF 20-23, `-movflags +faststart`) con el audio a −14 LUFS y el pico real por debajo de −1,5 dB. Con la voz de un móvil, `loudnorm` solo no llega: usa `acompressor=threshold=0.0316:ratio=2:attack=5:release=100:knee=4,volume=<ganancia>dB,alimiter=limit=0.75:attack=3:release=50:level=disabled`. Mide con `ebur128=peak=true` y ajusta la ganancia hasta −14 ±0,3. Junto al vídeo, un resumen de lo que has cortado y por qué. Dime también lo que no has podido comprobar (por ejemplo, el audio no lo oyes) y cualquier choque con marca.md.
