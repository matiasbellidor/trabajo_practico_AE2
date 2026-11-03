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

import jinja2
import pandas as pd

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


def _svg_accesible(svg: str, figura_id: str) -> str:
    return svg.replace("<svg ", f'<svg role="img" aria-labelledby="cap-{figura_id}" focusable="false" ', 1)


def renderizar(resultados: dict, figuras: list[dict], svgs: dict[str, str], panel: list[dict],
               conclusion_md: str | None, fecha_entrega: str) -> str:
    entorno = jinja2.Environment(loader=jinja2.FileSystemLoader(WEB), autoescape=True,
                                 undefined=jinja2.StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    figs = {f["id"]: {**f, "svg": _svg_accesible(svgs[f["id"]], f["id"])} for f in figuras}
    return entorno.get_template("plantilla.html.j2").render(
        r=resultados, t=textos.construir(resultados), figs=figs, panel=panel,
        secciones=[{"id": i, "titulo": t} for i, t in SECCIONES],
        css=(WEB / "estilos.css").read_text(encoding="utf-8"), js=(WEB / "navegacion.js").read_text(encoding="utf-8"),
        conclusion_html=markdown_a_html(conclusion_md) if conclusion_md else None,
        mensual=resultados["muestra"]["principal"]["frecuencia"] == "mensual", fecha_entrega=fecha_entrega,
        n=num, pv=pval, ic=ic_texto, p_texto=p_texto, gl=gl_texto, partir=partir_veredicto,
        nombres=textos.NOMBRES,
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
    contenido = renderizar(resultados, figuras, svgs, filas, conclusion, f"{d}/{m}/{y}")
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
