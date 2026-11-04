"""(10) Motion de las figuras web: cada figura se arma con sus propios datos, dentro del tope de tiempo, y solo anima
propiedades que no traban el scroll. Si una actualización de matplotlib cambia el SVG y la coreografía se pierde,
estos tests fallan."""

import json
import re
from collections import Counter

import numpy as np
import pytest

from tp_ae2 import graficos, presentacion
from tp_ae2.config import RAIZ_REPO

from test_web_y_textos import _renderizar

CSS = (RAIZ_REPO / "src" / "tp_ae2" / "web" / "estilos.css").read_text(encoding="utf-8")
PERMITIDAS = {"transform", "opacity", "stroke-dashoffset", "offset-distance"}


@pytest.fixture(scope="module")
def figuras_web(corrida):
    resultados, extras = corrida
    return {nombre: graficos.figura_web(nombre, resultados, extras) for nombre, _, _ in graficos.FIGURAS}


def _tipos(svg: str) -> Counter:
    return Counter(re.findall(r'class="m m--([a-z]+)', svg))


def _esperados(resultados: dict, extras: dict) -> dict[str, dict[str, int]]:
    """Cuántos elementos tiene que animar cada figura, contados desde los datos (nunca a mano)."""
    n = resultados["muestra"]["principal"]["n"]
    panel = extras["principal"]["panel"]
    trimestres = len(extras["pbi_stl"].loc["2019Q1":])
    series_hist = (panel["var_bono"].to_numpy(), panel["var_pbi"].to_numpy(), extras["principal"]["principal"]["_residuos"])
    clases = sum(len(np.histogram_bin_edges(x, bins="fd")) - 1 for x in series_hist)
    desfases = len(resultados["desfases"])
    anillos = 2 * sum(f["etiqueta"] == "exploratoria" and f["significativo"] for f in resultados["desfases"])
    grupos = len(resultados["anova"]["grupos"])
    filas = 2 * 2 + sum(s["id"] in graficos.SENSIBILIDADES_ROBUSTEZ for s in resultados["sensibilidades"])
    return {
        "series": {"cursor": 1, "barra": n, "trazo": 1},
        "pbi": {"trazo": 2, "punto": 2 * trimestres, "aparece": 1},
        "histogramas": {"barra": clases, "trazo": 3, "aparece": 1},
        "dispersion": {"punto": n, "trazo": 1, "aparece": 1},
        "desfases": {"trazo": 3, "ic": desfases, "punto": desfases, "cae": desfases, **({"anillo": anillos} if anillos else {})},
        "residuos": {"punto": n, "barra": graficos.REZAGOS_FAC, "trazo": 2},
        "anova": {"punto": n + grupos, "ic": grupos, "aparece": grupos},
        "robustez": {"trazo": 1, "icx": filas, "punto": filas},
        # Dos grupos (suba y baja); cada caja: caja, dos bigotes, dos topes y la mediana.
        "complementaria": {"punto": n, "caja": 2 * 6},
    }


def test_cada_figura_tiene_coreografia():
    publicadas = [f["id"] for f in json.loads((RAIZ_REPO / "outputs" / "figuras" / "figuras.json").read_text(encoding="utf-8"))]
    assert set(publicadas) == set(graficos.RECETAS) == {n for n, _, _ in graficos.FIGURAS}


def test_elementos_animados_salen_de_los_datos(corrida, figuras_web):
    esperados = _esperados(*corrida)
    for nombre, (svg, anim) in figuras_web.items():
        assert dict(_tipos(svg)) == esperados[nombre], nombre
        assert anim["conteo"] == esperados[nombre], nombre


def test_orden_y_linea_de_base(corrida, figuras_web):
    resultados, extras = corrida
    panel = extras["principal"]["panel"]
    # Dispersión: los puntos caen en orden cronológico (el tooltip de cada punto dice su mes).
    svg = figuras_web["dispersion"][0]
    meses = re.findall(r'style="--i:(\d+)"><use [^>]*><title>(\d{4}-\d{2}):', svg)
    assert [int(i) for i, _ in meses] == list(range(len(panel)))
    assert [m for _, m in meses] == list(panel.index.astype(str))
    # Serie: cada barra crece desde el cero, hacia arriba o hacia abajo según su signo.
    svg = figuras_web["series"][0]
    assert len(re.findall(r'class="m m--barra f\d m--neg"', svg)) == int((panel["var_bono"] < 0).sum())
    assert len(re.findall(r'class="m m--barra f\d m--pos"', svg)) == int((panel["var_bono"] >= 0).sum())
    # La lectura del cursor tiene un texto por mes, formateado en Python.
    lecturas = figuras_web["series"][1]["lecturas"]
    assert len(lecturas) == len(panel) and lecturas[0].startswith(str(panel.index[0]))


def test_coreografia_dentro_del_tope(figuras_web):
    for nombre, (svg, anim) in figuras_web.items():
        assert 0 < anim["duracion"] <= graficos.TOPE_MS, nombre
        trazos = re.findall(r'<path pathLength="1" class="m m--trazo[^"]*"', svg)
        assert len(trazos) == svg.count('class="m m--trazo'), nombre
        fases = len(re.findall(r"--f(\d+)-t0", anim["estilo"]))
        assert fases <= 8 and f".f{fases} " in CSS, nombre  # estilos.css define hasta .f8
        assert ' id="' + nombre + '-m-' not in svg, nombre  # los gid de trabajo no quedan en el HTML


def test_keyframes_solo_animan_propiedades_baratas():
    bloques = re.findall(r"@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\})*)\s*\}", CSS)
    assert bloques
    for nombre, cuerpo in bloques:
        propiedades = set(re.findall(r"([a-z-]+)\s*:", cuerpo))
        assert propiedades <= PERMITIDAS, (nombre, propiedades - PERMITIDAS)
    assert not re.search(r"transition\s*:\s*all\b", CSS)
    # Todo el motion nuevo vive detrás de la preferencia de movimiento y fuera de la impresión.
    assert "@media screen and (prefers-reduced-motion: no-preference)" in CSS


def test_html_con_figuras_animadas(corrida, figuras_web):
    resultados, extras = corrida
    figuras = [{"id": n, "titulo": t, "alt": "texto", "svg": f"{n}.svg", "anim": figuras_web[n][1]}
               for n, t, _ in graficos.FIGURAS]
    panel = extras["principal"]["panel"].reset_index().assign(periodo=lambda d: d["periodo"].astype(str))
    filas = panel[["periodo", "var_pbi", "var_bono", "grupo_bono", "tercil_pbi"]].to_dict(orient="records")
    html = presentacion.renderizar(resultados, figuras, {n: s for n, (s, _) in figuras_web.items()}, filas, None,
                                   "12/11/2026")
    assert len(re.findall(r'<figure class="figura revela" id="fig-\w+" data-anim="\w+" data-dur="\d+" style="--f1-t0', html)) == 9
    assert html.count('aria-label="Repetir la animación de la figura"') == 9
    lecturas = re.search(r"data-lecturas='(\[[^']+\])'", html)
    assert lecturas and len(json.loads(lecturas.group(1))) == resultados["muestra"]["principal"]["n"]
    assert html.count('<output class="lectura" aria-hidden="true">') == 1


def test_portada_titulo_y_recorrido(corrida):
    resultados, _ = corrida
    html = _renderizar(corrida)
    titulo = re.search(r'<h1 id="t-portada">(.*?)</h1>', html, re.S).group(1)
    assert re.sub(r"<[^>]+>", "", titulo) == "Variación del PBI real argentino y variación del bono AL30D"
    assert titulo.count('class="pal"') == 10
    # El punto de cada serie recorre el mismo camino que su línea (mismo d en offset-path).
    for serie in ("pbi", "bono"):
        d = re.search(rf'class="trazo__linea trazo__linea--{serie}" d="(M[^"]+)"', html).group(1)
        assert f"--ruta: path('{d}')" in html
    # Los números que cuentan desde 100 llegan al mismo texto que renderiza el servidor.
    cuentas = re.findall(r'data-cuenta="([\d.]+)" data-demora="\d+">([^<]+)<', html)
    assert len(cuentas) == 2
    assert all(texto == presentacion.num(float(valor), 1) for valor, texto in cuentas)
