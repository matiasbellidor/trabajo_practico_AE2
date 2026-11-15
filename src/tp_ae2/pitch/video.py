"""Video del horizonte del pitch: el recorrido real del AL30D (azul) y del PBI (naranja), en índices base 100 y en la
misma escala, con una luz que barre los meses de izquierda a derecha. Fondo negro: en la página se suma con
mix-blend-mode: screen, así el negro no tapa el fondo y solo se ven las líneas.

Los cuadros se dibujan con Pillow y se codifican en VP9 (WebM) con el ffmpeg que instala Playwright, que no trae
H.264 pero sí libvpx-vp9 y un demuxer de JPEG por tubería. No hace falta instalar nada más.
"""

from __future__ import annotations

import math
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ANCHO, ALTO = 1920, 360
FPS, SEGUNDOS = 24, 10
AZUL, NARANJA = (59, 139, 235), (232, 97, 44)
MARGEN_ARRIBA, MARGEN_ABAJO = 70, 26


def indices(variaciones: list[float]) -> list[float]:
    valores = [100.0]
    for v in variaciones:
        valores.append(valores[-1] * (1 + v / 100))
    return valores


def _catmull_rom(puntos: list[tuple[float, float]], pasos: int = 10) -> list[tuple[float, float]]:
    """Curva suave que pasa por todos los puntos (Catmull-Rom centrípeta simplificada)."""
    if len(puntos) < 3:
        return puntos
    ext = [puntos[0]] + puntos + [puntos[-1]]
    salida = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(pasos):
            t = k / pasos
            t2, t3 = t * t, t * t * t
            salida.append(tuple(
                0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                       + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    salida.append(puntos[-1])
    return salida


def _escala(serie_a: list[float], serie_b: list[float]):
    bajo, alto = min(serie_a + serie_b), max(serie_a + serie_b)
    util = ALTO - MARGEN_ARRIBA - MARGEN_ABAJO

    def a_puntos(valores: list[float]) -> list[tuple[float, float]]:
        paso = ANCHO / (len(valores) - 1)
        return [(i * paso, MARGEN_ARRIBA + util * (1 - (v - bajo) / ((alto - bajo) or 1))) for i, v in enumerate(valores)]
    return a_puntos


def _capa_estatica(bono: list[tuple[float, float]], pbi: list[tuple[float, float]]) -> Image.Image:
    escala = 2  # se dibuja al doble y se reduce: líneas suaves sin depender del antialias de Pillow
    W, H = ANCHO * escala, ALTO * escala
    base = Image.new("RGB", (W, H), (0, 0, 0))

    # Área bajo la curva del bono: degradé vertical que se apaga hacia abajo
    mascara = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mascara).polygon([(x * escala, y * escala) for x, y in bono] + [(W, H), (0, H)], fill=255)
    degrade = Image.new("L", (1, H))
    for y in range(H):
        degrade.putpixel((0, y), int(46 * max(0.0, 1 - y / H) ** 1.4))
    degrade = degrade.resize((W, H))
    relleno = Image.new("RGB", (W, H), AZUL)
    base.paste(relleno, (0, 0), Image.composite(degrade, Image.new("L", (W, H), 0), mascara))

    def linea(img: Image.Image, pts, color, grosor, alfa=255):
        capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(capa).line([(x * escala, y * escala) for x, y in pts], fill=color + (alfa,), width=grosor * escala,
                                  joint="curve")
        return capa

    for pts, color, grosor, brillo in ((pbi, NARANJA, 2, 110), (bono, AZUL, 3, 150)):
        resplandor = linea(base, pts, color, grosor * 4, brillo).filter(ImageFilter.GaussianBlur(9 * escala))
        base.paste(resplandor, (0, 0), resplandor)
        trazo = linea(base, pts, color, grosor, 235)
        base.paste(trazo, (0, 0), trazo)
    return base.resize((ANCHO, ALTO), Image.LANCZOS)


def _sprite(radio: int, color: tuple[int, int, int]) -> Image.Image:
    """Cabeza de la luz: núcleo blanco y halo del color de la serie."""
    lado = radio * 2 + 1
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    px = img.load()
    for y in range(lado):
        for x in range(lado):
            d = math.hypot(x - radio, y - radio) / radio
            if d >= 1:
                continue
            halo = (1 - d) ** 1.7
            nucleo = max(0.0, 1 - d * 4.5)
            r = int(min(255, color[0] * halo + 255 * nucleo))
            g = int(min(255, color[1] * halo + 255 * nucleo))
            b = int(min(255, color[2] * halo + 255 * nucleo))
            px[x, y] = (r, g, b, int(255 * min(1.0, halo * 1.1 + nucleo)))
    return img


def _punto_en(curva: list[tuple[float, float]], x: float) -> tuple[float, float]:
    """Punto de la curva en la abscisa x (la curva avanza en x de forma monótona)."""
    lo, hi = 0, len(curva) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if curva[m][0] <= x:
            lo = m
        else:
            hi = m
    (x0, y0), (x1, y1) = curva[lo], curva[hi]
    t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
    return x, y0 + (y1 - y0) * t


def cuadros(var_bono: list[float], var_pbi: list[float]):
    """Genera los cuadros del loop (imágenes RGB) y el póster (la escena sin la luz)."""
    a_puntos = _escala(indices(var_bono), indices(var_pbi))
    bono = _catmull_rom(a_puntos(indices(var_bono)))
    pbi = _catmull_rom(a_puntos(indices(var_pbi)))
    estatica = _capa_estatica(bono, pbi)
    cabeza_bono, cabeza_pbi = _sprite(30, AZUL), _sprite(20, NARANJA)
    total = FPS * SEGUNDOS
    for k in range(total):
        t = k / total                      # 0 → 1 (el último cuadro no repite el primero: loop sin salto)
        x = t * ANCHO
        alfa = min(1.0, t / 0.06, (1 - t) / 0.06)
        alfa = alfa * alfa * (3 - 2 * alfa)  # suavizado en los extremos
        cuadro = estatica.copy()
        if alfa > 0.01:
            capa = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
            dib = ImageDraw.Draw(capa)
            # Cursor vertical tenue en el mes que se recorre (como el de la Figura 1 de la web)
            for y in range(MARGEN_ARRIBA - 20, ALTO, 2):
                a = int(34 * alfa * (y - MARGEN_ARRIBA + 20) / (ALTO - MARGEN_ARRIBA + 20))
                dib.point((int(x), y), fill=(150, 200, 255, a))
            # Estela: el tramo recorrido recientemente, más brillante y que se apaga hacia atrás
            for curva, color, largo in ((bono, (150, 200, 255), 0.07), (pbi, (255, 170, 120), 0.05)):
                x0 = max(0.0, x - largo * ANCHO)
                tramo = [p for p in curva if x0 <= p[0] <= x]
                for i in range(1, len(tramo)):
                    f = i / len(tramo)
                    dib.line([tramo[i - 1], tramo[i]], fill=color + (int(230 * f * alfa),), width=4)
            for curva, sprite in ((bono, cabeza_bono), (pbi, cabeza_pbi)):
                px, py = _punto_en(curva, x)
                s = sprite.copy()
                s.putalpha(s.getchannel("A").point(lambda v, a=alfa: int(v * a)))
                capa.alpha_composite(s, (int(px - s.width / 2), int(py - s.height / 2)))
            cuadro.paste(capa, (0, 0), capa)
        yield cuadro
    return estatica


def ffmpeg_de_playwright() -> Path:
    """El ffmpeg que descarga `playwright install` (trae libvpx-vp9 y lectura de JPEG por tubería)."""
    raiz = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or Path.home() / "AppData/Local/ms-playwright")
    for candidato in sorted(raiz.glob("ffmpeg-*/ffmpeg*"), reverse=True):
        if candidato.suffix in (".exe", ""):
            return candidato
    raise FileNotFoundError("No encontré el ffmpeg de Playwright: correr `python -m playwright install ffmpeg`")


def generar(var_bono: list[float], var_pbi: list[float], destino_webm: Path, destino_poster: Path) -> None:
    destino_webm.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino_webm.with_suffix(".tmp.webm")
    comando = [str(ffmpeg_de_playwright()), "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS),
               "-c:v", "mjpeg", "-i", "pipe:0", "-an", "-c:v", "libvpx-vp9", "-pix_fmt", "yuv420p", "-b:v", "0",
               "-crf", "38", "-row-mt", "1", "-deadline", "good", "-cpu-used", "2", "-g", str(FPS * SEGUNDOS), str(tmp)]
    proc = subprocess.Popen(comando, stdin=subprocess.PIPE)
    generador = cuadros(var_bono, var_pbi)
    try:
        for cuadro in generador:
            cuadro.save(proc.stdin, "JPEG", quality=94, subsampling=0)
    finally:
        proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg no pudo codificar el video del horizonte")
    tmp.replace(destino_webm)
    # Póster: la escena sin la luz (lo que se ve con "reducir movimiento", con ahorro de datos o sin VP9)
    a_puntos = _escala(indices(var_bono), indices(var_pbi))
    estatica = _capa_estatica(_catmull_rom(a_puntos(indices(var_bono))), _catmull_rom(a_puntos(indices(var_pbi))))
    estatica.save(destino_poster, "WEBP", quality=82, method=6)
