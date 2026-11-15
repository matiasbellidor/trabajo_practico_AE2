"""Lectura y armado del deck: el export es un solo HTML (React + Plotly empaquetados con Vite), sin el código fuente.

No se toca nada adentro del bundle salvo el orden de las diapositivas (un array literal fácil de ubicar). Todo lo
demás entra como una capa aparte: un <style> antes de </head> y un <script> clásico al final del <body>, que corre
antes que el módulo de la app (los módulos se ejecutan diferidos) y por eso alcanza a envolver history.replaceState.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path

AQUI = Path(__file__).parent
MARCA = "tp-ae2-pitch"  # marca de lo inyectado: permite verificar y no inyectar dos veces

# Orden de la exposición. Respecto del export, la Figura 4 (dispersión con la recta) pasa a ir después de la
# hipótesis: el guion le asigna a Luka "mostrar la regresión" en el primer bloque, y es la única diapositiva que la
# muestra. Para volver al orden del export, poner ORDEN = None.
ORDEN: list[str] | None = [
    "portada", "hipotesis", "figura-4", "fuentes", "figura-1", "descriptiva", "mco", "sensibilidad", "agregacion",
    "limitaciones", "conclusiones", "futuro",
]

# Correcciones de contenido contra el informe (README 5.3 y 5.4). Cada una debe aparecer exactamente una vez en el
# export; si un export nuevo ya las trae corregidas, construir falla y avisa en vez de seguir de largo.
CORRECCIONES: list[tuple[str, str, str]] = [
    ("Diferencia de medias (PBI positivo vs. negativo)",
     "Diferencia de medias (PBI con el bono en suba vs. en baja)",
     "la prueba separa los meses por lo que hizo el bono y compara el PBI, no al revés"),
    ("Las pruebas econométricas y no paramétricas adicionales confirman la falta de significatividad mensual.",
     "Las pruebas adicionales confirman la falta de significatividad mensual.",
     "el ANOVA y el test t de diferencia de medias son pruebas paramétricas"),
]

# Velocidad de los gráficos (Plotly). Medido con Playwright, de la tecla → a "el gráfico dejó de moverse": 2,2 s en una
# compu normal y 3,9 s con la CPU 4× más lenta. La demora era sobre todo esperar la animación de entrada de la
# diapositiva antes de empezar a dibujar. Mismo control que CORRECCIONES: cada texto, exactamente una vez.
OPTIMIZACIONES: list[tuple[str, str, str]] = [
    ("let{fs:o}=am(),{entered:s}=sm(),c=ep()", "let{fs:o}=am(),{started:s}=sm(),c=ep()",
     "el gráfico se dibuja al montar la diapositiva (en el celular, al entrar en pantalla), no al terminar su entrada"),
    ("vm={duration:1300,easing:`cubic-in-out`}", "vm={duration:700,easing:`cubic-in-out`}",
     "la animación de armado del gráfico pasa de 1,3 s a 0,7 s"),
    ("new ResizeObserver(()=>{u.current&&d.current&&u.current.Plots.resize(e)})",
     "new ResizeObserver(()=>{u.current&&d.current&&e.offsetParent&&u.current.Plots.resize(e).catch(()=>{})})",
     "con el gráfico dibujado antes, pasar rápido de diapositiva pedía redimensionar uno que ya salía (error de consola)"),
    ("window.requestIdleCallback?window.requestIdleCallback(()=>rm()):setTimeout(rm,1500)",
     "window.requestIdleCallback?window.requestIdleCallback(()=>rm().then(__pitchCalentar),{timeout:500}):"
     "setTimeout(()=>rm().then(__pitchCalentar),300)",
     "Plotly se inicializa a más tardar a los 0,5 s de cargar y dibuja una vez un gráfico invisible (lo que la primera "
     "figura pagaba al aparecer); __pitchCalentar está en la capa (deck_mejoras.js)"),
]

_ARRAY = re.compile(r"=\[(\{id:`portada`.*?\})\];", re.S)
_ENTRADA = re.compile(
    r"\{id:`(?P<id>[^`]+)`,cls:`(?P<cls>[^`]*)`,C:(?P<comp>[\w$]+),(?:num:!1,)?"
    r"kicker:`(?P<kicker>[^`]*)`,title:`(?P<titulo>[^`]*)`\}")


@dataclass(frozen=True)
class Diapositiva:
    id: str
    clase: str
    kicker: str
    titulo: str
    numerada: bool


class DeckInvalido(RuntimeError):
    pass


def diapositivas(fuente: str) -> list[Diapositiva]:
    """Las diapositivas en el orden en que figuran en el bundle."""
    m = _ARRAY.search(fuente)
    if not m:
        raise DeckInvalido("No encontré el array de diapositivas (¿cambió el export del pitch?)")
    salida = []
    for e in re.finditer(r"\{id:`[^`]+`.*?\}(?=,\{id:|$)", m.group(1), re.S):
        d = _ENTRADA.fullmatch(e.group(0))
        if not d:
            raise DeckInvalido(f"Entrada de diapositiva con formato inesperado: {e.group(0)[:120]}")
        salida.append(Diapositiva(d["id"], d["cls"], d["kicker"], d["titulo"], "num:!1" not in e.group(0)))
    return salida


def reordenar(fuente: str, orden: list[str] | None) -> str:
    """Reordena el array de diapositivas. Exige que el orden nuevo tenga exactamente las mismas diapositivas."""
    if not orden:
        return fuente
    m = _ARRAY.search(fuente)
    if not m:
        raise DeckInvalido("No encontré el array de diapositivas")
    entradas = {}
    for e in re.finditer(r"\{id:`([^`]+)`.*?\}(?=,\{id:|$)", m.group(1), re.S):
        entradas[e.group(1)] = e.group(0)
    if sorted(entradas) != sorted(orden):
        raise DeckInvalido(f"ORDEN no coincide con las diapositivas del export: {sorted(entradas)} ≠ {sorted(orden)}")
    nuevo = ",".join(entradas[i] for i in orden)
    return fuente[:m.start(1)] + nuevo + fuente[m.end(1):]


def corregir(fuente: str, correcciones: list[tuple[str, str, str]] = CORRECCIONES) -> str:
    for viejo, nuevo, motivo in correcciones:
        veces = fuente.count(viejo)
        if veces != 1:
            raise DeckInvalido(f"Corrección «{viejo[:50]}…» ({motivo}): aparece {veces} veces en el export, se esperaba 1")
        fuente = fuente.replace(viejo, nuevo)
    return fuente


def _leer(nombre: str) -> str:
    return (AQUI / nombre).read_text(encoding="utf-8")


def inyectar(fuente: str, diapos: list[Diapositiva], config: dict) -> str:
    """Agrega la capa de mejoras: estilos, capa de fondo (luces, barrido y video), herramientas y script."""
    if MARCA in fuente:
        raise DeckInvalido("El HTML ya tiene la capa de mejoras: usar el export original como fuente")
    datos = {"diapositivas": [{"id": d.id, "titulo": d.titulo, "kicker": d.kicker} for d in diapos], **config}
    estilo = f'<style id="{MARCA}-estilos">\n{_leer("deck_mejoras.css")}\n</style>\n'
    poster = html.escape(config["video"]["poster"])
    fuente_video = html.escape(config["video"]["webm"])
    pdf = html.escape(config["pdf"]["ruta"])
    capa = (
        f'<div class="fx" id="{MARCA}-fondo" aria-hidden="true">'
        '<div class="fx__luz fx__luz--azul"></div><div class="fx__luz fx__luz--naranja"></div>'
        '<div class="fx__luz fx__luz--celeste"></div><div class="fx__barrido"></div>'
        '<div class="fx__horizonte">'
        # Sin autoplay: el script lo reproduce solo si no hay "reducir movimiento" ni ahorro de datos.
        f'<video class="fx__video" muted loop playsinline preload="metadata" poster="{poster}" tabindex="-1" '
        f'disablepictureinpicture disableremoteplayback><source src="{fuente_video}" type="video/webm"></video>'
        '</div></div>\n'
    )
    inicio = html.escape(config["informe"])
    herramientas = (
        f'<div class="pitch-herramientas" id="{MARCA}-herramientas">'
        # Volver a la web del trabajo (la portada), desde donde se entra a la presentación. Para la diapositiva 1
        # está la tecla Inicio del deck.
        f'<a class="pitch-boton" href="{inicio}" data-pitch-inicio title="Volver a la web del trabajo">'
        '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M10 6l-6 6 6 6M4 12h16"/></svg>'
        '<span>Volver al inicio</span></a>'
        f'<a class="pitch-boton" href="{pdf}" download data-pitch-pdf aria-label="Descargar la presentación en PDF">'
        '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 4v11m0 0-4.5-4.5M12 15l4.5-4.5'
        'M5 19h14"/></svg><span>PDF</span></a>'
        '<button class="pitch-boton" type="button" data-pitch-fondo aria-pressed="false" '
        'aria-label="Pausar el video de fondo (V)"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
        '<path class="pitch-icono-pausa" d="M9 6v12M15 6v12"/><path class="pitch-icono-play" d="M8 5.5v13l10-6.5z"/>'
        '</svg><span data-pitch-fondo-texto>Fondo</span></button>'
        '</div>\n'
        '<p class="pitch-aviso" role="status" data-pitch-aviso hidden></p>\n'
    )
    config_js = f'<script id="{MARCA}-config">window.__PITCH__ = {json.dumps(datos, ensure_ascii=False)};</script>\n'
    script = f'<script id="{MARCA}-script">\n{_leer("deck_mejoras.js")}\n</script>\n'

    if fuente.count("</head>") != 1 or fuente.count("<body>") != 1 or fuente.count("</body>") != 1:
        raise DeckInvalido("El export no tiene un único <head>/<body>")
    salida = fuente.replace("</head>", estilo + "</head>", 1)
    salida = salida.replace("<body>", "<body>\n" + capa, 1)
    salida = salida.replace("</body>", herramientas + config_js + script + "</body>", 1)
    return salida
