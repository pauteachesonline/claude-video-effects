---
name: efectos-reels
description: Pone a un reel vertical los efectos del vídeo «20 efectos de vídeo hechos por Claude» de @donpablo_ai (órbita, chat, salir del marco, portal, plató, recortable, revista, cristal roto, móvil, lista final…), con Hyperframes y una plantilla ya hecha. Úsala cuando el usuario pida efectos para su vídeo, «ponle estos efectos» o una frase de la lista de efectos.md.
---
# Efectos para tu reel

La plantilla `plantilla/construir.py` ya trae los 20 efectos con su animación, sus fondos y su estilo (el del reel de @taki.gpt: fondos negros con brillo azul y naranja, cajas blancas, naranja y subtítulos blancos palabra a palabra). Tú no los programas: preparas el vídeo, rellenas `config.json` y la plantilla escribe la composición de Hyperframes.

Trabaja siempre en la carpeta del vídeo del usuario. Explícale cada paso en una frase, sin jerga.

## 1. Comprueba lo que hace falta
- Node 18 o superior (`node -v`), ffmpeg, whisper.cpp (`whisper-cli`) con el modelo `ggml-small.bin` y Python con Pillow. Si falta algo, pide permiso e instálalo (la skill editor-reels instala casi todo).
- Hyperframes: `npx hyperframes --version`. La primera vez lo descarga solo. Si el usuario no ha instalado sus skills (no existe `~/.claude/skills/media-use`), pídele permiso y ejecuta `npx skills add heygen-com/hyperframes -g -a claude-code -s '*' -y` (traen los sonidos de los efectos; sin `-y` se queda esperando respuestas).

## 2. Prepara el vídeo
1. Si el usuario ya editó el vídeo con editor-reels, usa ese MP4 (cortes y pausas ya hechos). Si no, avísale de que los efectos van mejor sobre un vídeo ya cortado.
2. Pásalo a 1080×1920, 30 fps, en `assets/toma.mp4`. Si es HDR de iPhone (`ffprobe` dice `arib-std-b67` o `smpte2084`), conviértelo a SDR con tonemap; si no, solo escala y recorta al centro.
3. Transcribe palabra por palabra con el alineado fino (es el que deja los subtítulos en su sitio aunque haya pausas):
   `ffmpeg -i assets/toma.mp4 -ac 1 -ar 16000 assets/audio16k.wav`
   `whisper-cli -m <ruta>/ggml-small.bin -l es -ml 1 -sow --dtw small -ojf -of assets/palabras -f assets/audio16k.wav`
4. Recorta a la persona del fondo (lo necesitan los efectos en los que sale por delante):
   `npx hyperframes remove-background assets/toma.mp4 -o assets/recorte.webm --quality best`
   La primera vez descarga un modelo de unos 168 MB. Tarda unos minutos.
5. Saca un fotograma (`ffmpeg -ss 1 -i assets/toma.mp4 -frames:v 1 cara.png`), míralo y apunta el centro de la cara en píxeles (x, y) sobre 1080×1920.
6. Si al final de la toma hay unos segundos de la habitación vacía, saca un fotograma de ahí a `assets/vacio.jpg`: es el fondo del efecto vértigo.

## 3. Decide con el usuario qué efecto va dónde
- Enséñale la lista de `efectos.md` (nombre y qué hace). Puede elegir los que quiera, no hace falta usar los 20.
- Cada efecto va en una palabra concreta: búscala en `assets/palabras.json` y usa su inicio. Dura entre 1,2 y 2 s y nunca se pisa con el siguiente.
- Si el usuario dice «ponlos donde mejor queden», propón tú el reparto y enséñaselo en una tabla (palabra, segundo, efecto) antes de seguir.

## 4. Rellena config.json
En la carpeta del vídeo. Ejemplo completo:

```json
{
  "video": "assets/toma.mp4", "recorte": "assets/recorte.webm", "palabras": "assets/palabras.json",
  "duracion": 48.5, "cara": [560, 880],
  "titulo": ["5 efectos de vídeo", "hechos por Claude"],
  "intro": {"inicio": 0, "duracion": 2.8},
  "efectos": [
    {"tipo": "orbita", "nombre": "Órbita", "inicio": 3.1, "duracion": 1.6},
    {"tipo": "zoom_golpe", "nombre": "Zoom de golpe", "inicio": 5.0, "duracion": 1.4}
  ],
  "marca": "Tu Marca", "usuario": "tu_usuario", "nombre": "Tu Nombre", "bio": "Lo que pone tu perfil",
  "avatar": "assets/avatar.jpg", "fondo_vacio": "assets/vacio.jpg",
  "cierre": {"inicio": 36.3, "comenta": 43.8, "sigueme": 46.3}, "palabra": "EDITOR"
}
```

- `duracion`: la del vídeo, en segundos (`ffprobe`).
- `tipo`: uno de la lista de `efectos.md`. `nombre`: lo que sale escrito arriba.
- `titulo`: las dos líneas del rótulo de arriba.
- `intro` y `cierre` son opcionales. El cierre es para un vídeo que acaba pidiendo comentar una palabra. Puedes afinar sus momentos con `editor`, `video`, `pide`, `edita`, `palabra`, `enviado` y `final`, usando el segundo de la palabra que se dice en cada uno. Si faltan, se reparten solos.
- `recurso`: el clip que entra encima en «vídeo encima», si el usuario te pasa uno (ruta dentro de la carpeta). Sin él, sale un clip de ejemplo del kit.
- Textos opcionales: `titulares` (seis pares [etiqueta, titular]), `chat_pide` y `chat_lista` (el chat), `marca` (la revista), `lista_final`, `texto_cierre` (las tres líneas de la caja del cierre), `frase` (lo que se escribe en Claude Code al final) y `archivo` (el nombre del archivo que cae).

## 5. Construye y revisa
1. Desde la carpeta del vídeo: `python3 <carpeta de esta skill>/plantilla/construir.py` (normalmente `~/.claude/skills/efectos-reels/plantilla/construir.py`). Escribe `index.html` y prepara `assets/kit/` y `assets/kit-gen/`.
2. `npx hyperframes lint`: tiene que dar 0 errores. Los avisos de estructura son normales.
3. `npx hyperframes snapshot --at "<un segundo por efecto>" --no-end` y mira cada fotograma:
   - nada tapa la cara;
   - el recorte de la persona encaja con el vídeo;
   - los textos se leen;
   - el subtítulo es la palabra que se oye.
4. Enséñale los fotogramas al usuario. Si algo no le gusta, cambia `config.json` (o el CSS de la plantilla para colores y letras) y vuelve a construir.

## 6. Exporta
- `npx hyperframes render -o reel-con-efectos.mp4 --fps 30`.
- Normaliza el audio a −14 LUFS con ffmpeg (`loudnorm`) y entrega el MP4.
- Dile qué efectos lleva y en qué segundo, y avísale de lo que conviene revisar a mano (por ejemplo, un brazo que el recorte se coma).

## Lo que conviene saber
- La primera vez no sale perfecto. Lo normal es dar dos o tres vueltas de cambios.
- Los efectos con la persona por delante (órbita, salir del marco, titulares, portal, curva, plató, recortable, vértigo, revista, croma y cristal roto) dependen del recorte. Si la persona sostiene algo o se mueve mucho, revisa esos efectos.
- Sin las skills de Hyperframes no hay efectos de sonido: el vídeo sale igual, solo con la voz.
- No publiques nada: entrega el MP4 y lo sube el usuario.
