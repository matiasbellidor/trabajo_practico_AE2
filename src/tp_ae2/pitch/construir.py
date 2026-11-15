"""Arma docs/presentacion/ a partir del export del pitch.

    docs/presentacion/index.html                 el deck con la capa de mejoras (fondo por diapositiva, video, PDF)
    docs/presentacion/presentacion-tp-ae2.pdf    una página por diapositiva (capturas a 2880 × 1620)
    docs/presentacion/media/                     video del horizonte, su póster y miniaturas de cada diapositiva
    docs/presentacion/recursos/index.html        código de 3 casillas + guion de cada orador, cifrado

Uso: python -m tp_ae2.pitch [--config config.yaml] [--sin-video] [--sin-capturas]

Necesita Playwright con Chromium (las capturas, el PDF y el cifrado se hacen en el navegador, con la misma
WebCrypto que después descifra). El guion se lee de guion/guion.yaml, que no está en el repo: sin ese archivo se
arman el deck y el PDF, y Recursos queda como estaba.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import functools
import hashlib
import http.server
import json
import logging
import threading
import time
from pathlib import Path

import jinja2
import pandas as pd
from PIL import Image

from ..config import Config, cargar_config
from . import deck, guion, pdf, video

log = logging.getLogger(__name__)
AQUI = Path(__file__).parent
CARPETA, MEDIA = "presentacion", "media"
PDF_NOMBRE = "presentacion-tp-ae2.pdf"
VIEWPORT, ESCALA = {"width": 1920, "height": 1080}, 1.5
ITERACIONES = 250_000  # PBKDF2: ~0,2 s en un celular; frena un poco a quien pruebe las 1000 combinaciones a mano


def peso_legible(n: int) -> str:
    return f"{n / 1_048_576:.1f} MB".replace(".", ",") if n >= 1_048_576 else f"{round(n / 1024)} KB"


class _Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # sin una línea por pedido
        pass


@contextlib.contextmanager
def servidor(raiz: Path):
    """Servidor HTTP local (las capturas y el cifrado necesitan un origen http://, no file://)."""
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Silencioso, directory=str(raiz)))
    hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
    hilo.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def _marcas_por_diapositiva(armado: dict | None) -> dict[str, list[dict]]:
    salida: dict[str, list[dict]] = {}
    for p in (armado or {}).get("pasos", []):
        salida.setdefault(p["diapositiva"], []).extend(p["marcas"])
    return salida


_MEDIR = """([sel, x, y]) => {
  const d = document.querySelector('.deck').getBoundingClientRect();
  const el = document.querySelector(sel);  // en modo diapositivas hay una sola montada a la vez
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return {x: (r.left + r.width * x - d.left) / d.width * 100, y: (r.top + r.height * y - d.top) / d.height * 100};
}"""

_CIFRAR = """async ({texto, codigo, iteraciones, sal, iv}) => {
  const enc = new TextEncoder();
  const deB64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
  const aB64 = (u8) => { let s = ''; for (let i = 0; i < u8.length; i += 32768) s += String.fromCharCode.apply(null, u8.subarray(i, i + 32768)); return btoa(s); };
  const base = await crypto.subtle.importKey('raw', enc.encode(codigo), 'PBKDF2', false, ['deriveKey']);
  const clave = await crypto.subtle.deriveKey({name: 'PBKDF2', salt: deB64(sal), iterations: iteraciones, hash: 'SHA-256'},
    base, {name: 'AES-GCM', length: 256}, false, ['encrypt']);
  const datos = new Uint8Array(await crypto.subtle.encrypt({name: 'AES-GCM', iv: deB64(iv)}, clave, enc.encode(texto)));
  return aB64(datos);
}"""


def texto_del_guion(armado: dict) -> str:
    return json.dumps(armado, ensure_ascii=False, separators=(",", ":"))


def sal_e_iv(texto: str) -> tuple[bytes, bytes]:
    """Sal e IV derivados del contenido: el mismo guion da el mismo cifrado (git no ve cambios si no los hay) y un
    guion distinto nunca repite el IV."""
    huella = hashlib.sha256(texto.encode("utf-8")).digest()
    return hashlib.sha256(b"sal|" + huella).digest()[:16], hashlib.sha256(b"iv|" + huella).digest()[:12]


def capturar(docs: Path, diapos: list[deck.Diapositiva], marcas: dict[str, list[dict]], salida: Path,
             cifrar: tuple[str, str] | None) -> tuple[list[Path], dict[str, list[dict]], dict | None]:
    """Captura cada diapositiva (para el PDF y las miniaturas), mide dónde va cada marca y cifra el guion."""
    from playwright.sync_api import sync_playwright

    salida.mkdir(parents=True, exist_ok=True)
    jpegs, posiciones, errores = [], {}, []
    with servidor(docs) as base, sync_playwright() as p:
        navegador = p.chromium.launch()
        contexto = navegador.new_context(viewport=VIEWPORT, device_scale_factor=ESCALA, reduced_motion="reduce")
        pagina = contexto.new_page()
        pagina.on("pageerror", lambda e: errores.append(str(e)))
        pagina.goto(f"{base}/{CARPETA}/?captura=1#1", wait_until="load")
        pagina.wait_for_selector("#diapo-1", timeout=30_000)
        pagina.evaluate("document.fonts.ready")
        for i, d in enumerate(diapos, start=1):
            if i > 1:
                pagina.evaluate(f"location.hash = '#{i}'")
            pagina.wait_for_function(
                f"document.getElementById('diapo-{i}') && document.querySelectorAll('.slide').length === 1",
                timeout=15_000)
            if pagina.locator(f"#diapo-{i} .plot").count():
                pagina.wait_for_selector(f"#diapo-{i} .plot .main-svg", timeout=30_000)
            pagina.wait_for_timeout(1400)  # entradas con opacidad de la app y la escena de fondo ya quietas
            ruta = salida / f"diapo-{i:02d}.jpg"
            pagina.screenshot(path=str(ruta), type="jpeg", quality=88)
            jpegs.append(ruta)
            for m in marcas.get(d.id, []):
                pos = pagina.evaluate(_MEDIR, [m["sel"], m.get("x", 0), m.get("y", 0)])
                if pos is None:
                    raise deck.DeckInvalido(f"La marca {m['num']} de «{d.id}» no encuentra {m['sel']!r} en la diapositiva")
                posiciones.setdefault(d.id, []).append({"num": m["num"], "x": round(pos["x"], 2), "y": round(pos["y"], 2),
                                                         "centro": m.get("ancla") == "centro"})
        cifrado = None
        if cifrar:
            texto, codigo = cifrar
            sal, iv = sal_e_iv(texto)
            datos = pagina.evaluate(_CIFRAR, {"texto": texto, "codigo": codigo, "iteraciones": ITERACIONES,
                                              "sal": base64.b64encode(sal).decode(), "iv": base64.b64encode(iv).decode()})
            cifrado = {"v": 1, "kdf": "PBKDF2-SHA256", "iteraciones": ITERACIONES, "cifrado": "AES-GCM-256",
                       "sal": base64.b64encode(sal).decode(), "iv": base64.b64encode(iv).decode(), "datos": datos}
        navegador.close()
    if errores:
        raise RuntimeError("Errores de JavaScript en el deck durante la captura: " + " | ".join(errores[:3]))
    return jpegs, posiciones, cifrado


def miniaturas(jpegs: list[Path], destino: Path) -> list[str]:
    nombres = []
    for ruta in jpegs:
        nombre = ruta.stem + ".webp"
        with Image.open(ruta) as im:
            im.convert("RGB").resize((1280, 720), Image.LANCZOS).save(destino / nombre, "WEBP", quality=80, method=6)
        nombres.append(nombre)
    return nombres


def construir(cfg: Config, con_video: bool = True, con_capturas: bool = True) -> dict:
    docs = cfg.ruta("docs")
    destino = docs / CARPETA
    media = destino / MEDIA
    media.mkdir(parents=True, exist_ok=True)
    resultados = json.loads((cfg.ruta("salidas") / "resultados.json").read_text(encoding="utf-8"))

    fuente = deck.corregir(deck.reordenar(cfg.ruta("pitch").read_text(encoding="utf-8"), deck.ORDEN))
    diapos = deck.diapositivas(fuente)
    ids, titulos = [d.id for d in diapos], {d.id: d.titulo for d in diapos}

    # 1. Video del horizonte (se regenera solo si falta o si se pide)
    webm, poster = media / "horizonte.webm", media / "horizonte.webp"
    if con_video or not webm.exists():
        panel = pd.read_csv(cfg.ruta("salidas") / "tablas" / "panel_mensual.csv")
        video.generar(panel["var_bono"].astype(float).tolist(), panel["var_pbi"].astype(float).tolist(), webm, poster)
        log.info("Video del horizonte: %s (%s)", webm.name, peso_legible(webm.stat().st_size))

    # 2. Deck con la capa de mejoras
    config_deck = {"video": {"webm": f"{MEDIA}/horizonte.webm", "poster": f"{MEDIA}/horizonte.webp"},
                   "pdf": {"ruta": PDF_NOMBRE}, "informe": "../"}
    (destino / "index.html").write_text(deck.inyectar(fuente, diapos, config_deck), encoding="utf-8", newline="\n")
    log.info("Deck: %s (%d diapositivas, orden %s)", destino / "index.html", len(diapos),
             "del guion" if deck.ORDEN else "del export")

    # 3. Guion (si está el archivo local)
    ruta_guion = cfg.ruta("guion")
    armado, fuente_guion = None, None
    if ruta_guion.exists():
        fuente_guion = guion.cargar(ruta_guion)
        armado = guion.armar(fuente_guion, resultados, ids, titulos)
    else:
        log.warning("No está %s: Recursos queda como estaba (el guion no se publica en el repo)", ruta_guion)

    if not con_capturas:
        return {"diapositivas": len(diapos)}

    # 4. Capturas → PDF y miniaturas; posiciones de las marcas; cifrado del guion
    tmp = destino / ".capturas"
    marcas = _marcas_por_diapositiva(armado)
    texto = texto_del_guion(armado) if armado else None
    jpegs, posiciones, cifrado = capturar(docs, diapos, marcas, tmp,
                                          (texto, str(fuente_guion["codigo"])) if armado else None)
    pdf.escribir(jpegs, destino / PDF_NOMBRE, titulo=f"{resultados['meta']['titulo']} · Presentación",
                 autor=f"{resultados['meta']['grupo']} · " + ", ".join(resultados["meta"]["integrantes"]),
                 asunto=f"{resultados['meta']['materia']} · Cátedra {resultados['meta']['catedra']} · "
                        f"{resultados['meta']['facultad']}")
    imagenes = miniaturas(jpegs, media)
    for j in jpegs:
        j.unlink()
    tmp.rmdir()
    log.info("PDF: %s (%s, %d páginas)", PDF_NOMBRE, peso_legible((destino / PDF_NOMBRE).stat().st_size), len(jpegs))

    # 5. Recursos
    if cifrado:
        publico = {"diapositivas": [{"id": d.id, "titulo": d.titulo, "imagen": f"../{MEDIA}/{img}",
                                     "marcas": posiciones.get(d.id, [])} for d, img in zip(diapos, imagenes)],
                   "deck": "../", "pdf": f"../{PDF_NOMBRE}"}
        escribir_recursos(destino / "recursos", cifrado, publico, resultados)
        log.info("Recursos: guion de %s cifrado (%d pasos, %s)", armado["duracion_texto"], len(armado["pasos"]),
                 ", ".join(b["etiqueta"] for b in armado["bloques"]))
    return {"diapositivas": len(diapos), "pdf": destino / PDF_NOMBRE}


def escribir_recursos(carpeta: Path, cifrado: dict, publico: dict, resultados: dict) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    entorno = jinja2.Environment(loader=jinja2.FileSystemLoader(AQUI), autoescape=True,
                                 undefined=jinja2.StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    contenido = entorno.get_template("recursos.html.j2").render(
        r=resultados, css=(AQUI / "recursos.css").read_text(encoding="utf-8"),
        js=(AQUI / "recursos.js").read_text(encoding="utf-8"),
        # "</" escapado: un texto con "</script>" no puede cortar el bloque de datos
        cifrado=json.dumps(cifrado, separators=(",", ":")).replace("</", r"<\/"),
        publico=json.dumps(publico, ensure_ascii=False).replace("</", r"<\/"))
    ruta = carpeta / "index.html"
    ruta.write_text(contenido, encoding="utf-8", newline="\n")
    return ruta


def main() -> None:
    parser = argparse.ArgumentParser(description="Publica el pitch en docs/presentacion/ (deck, video, PDF y Recursos)")
    parser.add_argument("--config", default=None, help="Ruta a config.yaml")
    parser.add_argument("--sin-video", action="store_true", help="No regenerar el video si ya existe")
    parser.add_argument("--sin-capturas", action="store_true", help="Solo el deck: sin PDF, miniaturas ni Recursos")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    inicio = time.time()
    construir(cargar_config(args.config), con_video=not args.sin_video, con_capturas=not args.sin_capturas)
    log.info("Listo en %.0f s", time.time() - inicio)


if __name__ == "__main__":
    main()
