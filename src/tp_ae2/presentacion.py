"""Genera docs/index.html: presentación autocontenida (CSS, JS y figuras SVG inline, sin pedidos externos).

Uso: python -m tp_ae2.presentacion [--config config.yaml]  (lee lo que dejó run_all en outputs/)
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import re
from pathlib import Path

from urllib.parse import quote

import jinja2
import pandas as pd
from markupsafe import Markup

from . import reporte, textos
from .config import Config, cargar_config
from .veredicto import gl_texto, ic_texto, num, p_texto, pval

log = logging.getLogger(__name__)

WEB = Path(__file__).parent / "web"
LEADS = ("NO HAY EVIDENCIA SUFICIENTE", "SE AFIRMA")
SECCIONES = [
    ("portada", "Portada"), ("hipotesis", "Pregunta e hipótesis"), ("datos", "Datos y metodología"),
    ("resultado", "Resultado principal"), ("estimador", "Estimador e IC"), ("bondad", "Bondad de ajuste"),
    ("regresion", "Regresión simple y desfases"), ("multiple", "Regresión múltiple"), ("anova", "ANOVA"),
    ("complementaria", "Prueba complementaria"), ("robustez", "Robustez"), ("limitaciones", "Limitaciones"),
    ("conclusion", "Conclusión"), ("anexo", "Anexo: p-valores"),
]


def partir_veredicto(texto: str) -> tuple[str, str]:
    for lead in LEADS:
        if texto.startswith(lead):
            return lead, texto[len(lead):].lstrip(" :")
    return "", texto


def markdown_a_html(texto: str) -> str:
    """Conversión mínima (títulos, párrafos, listas, negrita, cursiva, código) para conclusion.md."""
    def en_linea(s: str) -> str:
        s = html.escape(s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        return re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", s)

    bloques, lista, parrafo = [], [], []

    def cerrar():
        if parrafo:
            bloques.append(f"<p>{en_linea(' '.join(parrafo))}</p>")
            parrafo.clear()
        if lista:
            bloques.append("<ul>" + "".join(f"<li>{en_linea(i)}</li>" for i in lista) + "</ul>")
            lista.clear()

    for linea in texto.splitlines():
        linea = linea.rstrip()
        titulo = re.match(r"^(#{1,4})\s+(.*)", linea)
        item = re.match(r"^\s*[-*]\s+(.*)", linea)
        if not linea.strip():
            cerrar()
        elif titulo:
            cerrar()
            # La diapositiva ya tiene su h2: "##" de la conclusión pasa a h3.
            nivel = min(len(titulo.group(1)) + 1, 6)
            bloques.append(f"<h{nivel}>{en_linea(titulo.group(2))}</h{nivel}>")
        elif item:
            if parrafo:
                cerrar()
            lista.append(item.group(1))
        else:
            if lista:
                cerrar()
            parrafo.append(linea.strip())
    cerrar()
    return "\n".join(bloques)


def trazo_portada(panel: list[dict], ancho: int = 600, alto: int = 220) -> dict:
    """Recorrido acumulado (base 100 en el período previo al primero) del AL30D y del PBI, para la portada.

    Cada serie se escala a su propio rango: la figura muestra forma, no magnitudes comparables.
    """
    margen = 8

    def indice(variaciones: list[float]) -> list[float]:
        valores = [100.0]
        for v in variaciones:
            valores.append(valores[-1] * (1 + v / 100))
        return valores

    def puntos(valores: list[float]) -> list[tuple[float, float]]:
        bajo, alto_v = min(valores), max(valores)
        rango = (alto_v - bajo) or 1.0
        paso = (ancho - 2 * margen) / (len(valores) - 1)
        return [(margen + i * paso, margen + (alto - 2 * margen) * (1 - (v - bajo) / rango))
                for i, v in enumerate(valores)]

    def camino(pts: list[tuple[float, float]]) -> str:
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    bono = indice([float(f["var_bono"]) for f in panel])
    pbi = indice([float(f["var_pbi"]) for f in panel])
    pb, pp = puntos(bono), puntos(pbi)
    return {"ancho": ancho, "alto": alto, "bono": camino(pb), "pbi": camino(pp), "fin_bono": pb[-1],
            "fin_pbi": pp[-1], "bono_final": bono[-1], "pbi_final": pbi[-1],
            "inicio": str(panel[0]["periodo"]), "fin": str(panel[-1]["periodo"])}


def palabras(texto: str) -> Markup:
    """Envuelve cada palabra en <span class="pal" style="--i:N"> para que el título entre escalonado. Los espacios
    quedan fuera de los span: el texto del elemento no cambia (lectores de pantalla, buscadores, tests)."""
    return Markup(" ".join(f'<span class="pal" style="--i:{i}">{html.escape(p)}</span>'
                           for i, p in enumerate(texto.split(" "))))


def icono(panel: list[dict], puntos: int = 8) -> str:
    """Ícono de la pestaña: el recorrido real del AL30D (azul) y del PBI (naranja), en índices base 100 y en la misma
    escala, sobre el azul noche de la portada: el bono sube mucho y el PBI casi no se mueve, que es lo que muestra el
    trabajo. Pocos puntos y trazo grueso para que se lea a 16 px. Devuelve un data URI (sin pedidos externos)."""
    def indice(variaciones: list[float]) -> list[float]:
        valores = [100.0]
        for v in variaciones:
            valores.append(valores[-1] * (1 + v / 100))
        paso = (len(valores) - 1) / (puntos - 1)
        return [valores[round(k * paso)] for k in range(puntos)]

    bono_i, pbi_i = indice([float(f["var_bono"]) for f in panel]), indice([float(f["var_pbi"]) for f in panel])
    bajo, alto = min(bono_i + pbi_i), max(bono_i + pbi_i)

    def camino(muestra: list[float]) -> list[tuple[float, float]]:
        return [(5 + 21 * k / (puntos - 1), 25 - 17 * (v - bajo) / ((alto - bajo) or 1)) for k, v in enumerate(muestra)]

    def linea(pts: list[tuple[float, float]], color: str, grosor: float) -> str:
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{grosor}" stroke-linecap="round" '
                f'stroke-linejoin="round"/>')

    bono, pbi = camino(bono_i), camino(pbi_i)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#142036"/>'
           + linea(pbi, "#f08a55", 2.6) + linea(bono, "#5b9cf0", 3)
           + f'<circle cx="{bono[-1][0]:.1f}" cy="{bono[-1][1]:.1f}" r="2.7" fill="#5b9cf0"/></svg>')
    return "data:image/svg+xml," + quote(svg)


def _svg_accesible(svg: str, figura_id: str) -> str:
    return svg.replace("<svg ", f'<svg role="img" aria-labelledby="cap-{figura_id}" focusable="false" ', 1)


def renderizar(resultados: dict, figuras: list[dict], svgs: dict[str, str], panel: list[dict],
               conclusion_md: str | None, fecha_entrega: str, linkedin: dict[str, str] | None = None) -> str:
    entorno = jinja2.Environment(loader=jinja2.FileSystemLoader(WEB), autoescape=True,
                                 undefined=jinja2.StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    entorno.filters["palabras"] = palabras
    figs ={f["id"]: {**f, "svg": _svg_accesible(svgs[f["id"]], f["id"])} for f in figuras}
    return entorno.get_template("plantilla.html.j2").render(
        r=resultados, t=textos.construir(resultados), figs=figs, panel=panel, trazo=trazo_portada(panel), icono=icono(panel),
        secciones=[{"id": i, "titulo": t} for i, t in SECCIONES],
        css=(WEB / "estilos.css").read_text(encoding="utf-8"), js=(WEB / "navegacion.js").read_text(encoding="utf-8"),
        conclusion_html=markdown_a_html(conclusion_md) if conclusion_md else None,
        mensual=resultados["muestra"]["principal"]["frecuencia"] == "mensual", fecha_entrega=fecha_entrega,
        n=num, pv=pval, ic=ic_texto, p_texto=p_texto, gl=gl_texto, partir=partir_veredicto,
        nombres=textos.NOMBRES, linkedin=linkedin or {},
    )


def generar(cfg: Config) -> Path:
    salidas = cfg.ruta("salidas")
    resultados = json.loads((salidas / "resultados.json").read_text(encoding="utf-8"))
    figuras = json.loads((salidas / "figuras" / "figuras.json").read_text(encoding="utf-8"))
    svgs = {f["id"]: (salidas / "figuras" / "web" / f["svg"]).read_text(encoding="utf-8") for f in figuras}
    frecuencia = resultados["muestra"]["principal"]["frecuencia"]
    panel = pd.read_csv(salidas / "tablas" / f"panel_{frecuencia}.csv")
    filas = panel[["periodo", "var_pbi", "var_bono", "grupo_bono", "tercil_pbi"]].to_dict(orient="records")
    conclusion = reporte.leer_conclusion(cfg.ruta("conclusion"))
    y, m, d = cfg["proyecto"]["fecha_entrega"].split("-")
    contenido = renderizar(resultados, figuras, svgs, filas, conclusion, f"{d}/{m}/{y}",
                           cfg["proyecto"].get("linkedin") or {})
    docs = cfg.ruta("docs")
    docs.mkdir(parents=True, exist_ok=True)
    destino = docs / "index.html"
    destino.write_text(contenido, encoding="utf-8", newline="\n")
    (docs / ".nojekyll").write_text("", encoding="utf-8")
    log.info("Presentación web: %s (%d KB)%s", destino, destino.stat().st_size // 1024,
             "" if conclusion else " — conclusión pendiente")
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera la presentación web en docs/index.html")
    parser.add_argument("--config", default=None, help="Ruta a config.yaml")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    generar(cargar_config(args.config))


if __name__ == "__main__":
    main()
