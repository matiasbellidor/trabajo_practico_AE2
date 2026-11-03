"""Figuras: PNG (dpi 200) para el documento impreso y SVG para la web con colores ligados a variables CSS."""

from __future__ import annotations

import io
import logging
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter, MaxNLocator  # noqa: E402
from scipy import stats  # noqa: E402

from . import veredicto as V  # noqa: E402

log = logging.getLogger(__name__)

# Paleta validada (dataviz): tres series categóricas aptas para daltónicos sobre el fondo claro y el oscuro.
CLARO = {"fondo": "#fbfaf7", "tinta": "#1b2230", "tinta2": "#4a5263", "tenue": "#7d828c", "grilla": "#e4e2db",
         "eje": "#c4c1b6", "s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a", "neutro": "#9aa0aa"}
# En la web cada color es un centinela que después se reemplaza por var(--fig-<rol>), así el SVG sigue el tema.
WEB = {rol: f"#fe00{i:02x}" for i, rol in enumerate(CLARO, start=1)}
_CENTINELAS = {hexa: f"var(--fig-{rol})" for rol, hexa in WEB.items()}


def _estilo(t: dict, web: bool) -> None:
    fondo = "none" if web else t["fondo"]
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10.5, "text.color": t["tinta"],
        "axes.facecolor": fondo, "figure.facecolor": fondo, "savefig.facecolor": fondo,
        "axes.edgecolor": t["eje"], "axes.labelcolor": t["tinta2"], "axes.titlecolor": t["tinta"],
        "axes.titlesize": 11.5, "axes.titlelocation": "left", "axes.titlepad": 10, "axes.labelsize": 10,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.grid.axis": "y",
        "axes.axisbelow": True, "grid.color": t["grilla"], "grid.linewidth": 0.8,
        "xtick.color": t["eje"], "ytick.color": t["eje"], "xtick.labelcolor": t["tinta2"],
        "ytick.labelcolor": t["tinta2"], "legend.frameon": False, "legend.labelcolor": t["tinta2"],
        "legend.fontsize": 9.5, "lines.linewidth": 2, "svg.fonttype": "none", "svg.hashsalt": "tp_ae2",
        "axes.unicode_minus": True,
    })


def _fmt(decimales: int | None = None, sufijo: str = "") -> FuncFormatter:
    def formatear(valor, _pos):
        if decimales is None:
            texto = f"{valor:g}".replace("-", "−").replace(".", ",")
        else:
            texto = V.num(valor, decimales)
        return texto + sufijo
    return FuncFormatter(formatear)


def _fechas(indice: pd.PeriodIndex) -> pd.DatetimeIndex:
    return indice.to_timestamp(how="start")


# --- Figuras ------------------------------------------------------------------------------------

def fig_series(r: dict, e: dict, t: dict):
    panel = e["principal"]["panel"]
    fechas = _fechas(panel.index)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 5.8), sharex=True)
    colores = np.where(panel["var_bono"] >= 0, t["s1"], t["s2"])
    a1.bar(fechas, panel["var_bono"], width=20, color=colores)
    a1.axhline(0, color=t["eje"], linewidth=1)
    a1.set_title("Variación mensual del AL30D (ajustada por días ex-pago)")
    a1.set_ylabel("%")
    a2.plot(fechas, panel["var_pbi"], color=t["s1"])
    a2.axhline(0, color=t["eje"], linewidth=1)
    a2.set_title("Variación mensual del PBI desestacionalizado y mensualizado")
    a2.set_ylabel("%")
    for ax in (a1, a2):
        ax.yaxis.set_major_formatter(_fmt())
    a1.text(0.995, 0.97, "Barras azules: suba · naranjas: baja", transform=a1.transAxes, ha="right", va="top",
            fontsize=9, color=t["tinta2"])
    fig.tight_layout()
    return fig


def fig_pbi(r: dict, e: dict, t: dict):
    stl = e["pbi_stl"].loc["2019Q1":]
    spline = e["pbi_spline"].loc["2019-02":]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    fechas_q = stl.index.asfreq("M", how="start").to_timestamp() + pd.DateOffset(months=1)
    ax.plot(fechas_q, stl["original"] / 1000, color=t["s2"], linewidth=1.5, marker="o", markersize=4,
            label="Original trimestral (con estacionalidad)")
    ax.plot(_fechas(spline.index), spline / 1000, color=t["s1"], linewidth=2, label="Spline mensual sobre la serie SA")
    ax.plot(fechas_q, stl["nivel"] / 1000, linestyle="none", marker="o", markersize=7, color=t["s1"],
            markeredgecolor=t["fondo"], markeredgewidth=1.5, label="Desestacionalizada (STL), en el mes central")
    ax.set_title("PBI a precios de 2004: original, desestacionalizado y mensualizado")
    ax.set_ylabel("Miles de millones de $ de 2004")
    ax.yaxis.set_major_formatter(_fmt(0))
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig


def fig_histogramas(r: dict, e: dict, t: dict):
    panel = e["principal"]["panel"]
    series = [("Var AL30D (%)", panel["var_bono"].to_numpy()), ("Var PBI (%)", panel["var_pbi"].to_numpy()),
              ("Residuos de la regresión principal (pp)", e["principal"]["principal"]["_residuos"])]
    fig, ejes = plt.subplots(1, 3, figsize=(11, 3.8))
    for ax, (titulo, x) in zip(ejes, series):
        ax.hist(x, bins="fd", density=True, color=t["s1"], alpha=0.35, edgecolor=t["s1"], linewidth=0.8)
        grilla = np.linspace(x.min() - x.std(), x.max() + x.std(), 300)
        ax.plot(grilla, stats.norm.pdf(grilla, x.mean(), x.std(ddof=1)), color=t["s2"], linewidth=2)
        ax.set_title(titulo, fontsize=10.5)
        ax.set_ylabel("Densidad")
        ax.xaxis.set_major_formatter(_fmt())
        ax.yaxis.set_major_formatter(_fmt())
    ejes[1].legend(["Normal ajustada N(x̄, S)", "Histograma"], loc="upper left", fontsize=8.5)
    fig.tight_layout()
    return fig


def fig_dispersion(r: dict, e: dict, t: dict):
    panel = e["principal"]["panel"]
    reg = e["principal"]["principal"]
    x, y = panel["var_pbi"].to_numpy(), panel["var_bono"].to_numpy()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    grilla = np.linspace(x.min(), x.max(), 200)
    ajuste = reg["b0"] + reg["b1"] * grilla
    margen = reg["valor_critico_t"] * reg["s"] * np.sqrt(1 / reg["n"] + (grilla - reg["x_media"]) ** 2 / reg["sxx"])
    ax.fill_between(grilla, ajuste - margen, ajuste + margen, color=t["s1"], alpha=0.15, linewidth=0,
                    label="IC 95 % de la media condicional")
    ax.plot(grilla, ajuste, color=t["s1"], linewidth=2, label="Recta de MCO")
    puntos = ax.scatter(x, y, s=46, color=t["s2"], edgecolors=t["fondo"], linewidths=1.5, zorder=3,
                        label="Meses (oct-2021 a may-2026)")
    puntos.set_gid("puntos-dispersion")
    ax.axhline(0, color=t["eje"], linewidth=1, zorder=1)
    ax.axvline(0, color=t["eje"], linewidth=1, zorder=1)
    ax.set_xlabel("Variación mensual del PBI mensualizado (%)")
    ax.set_ylabel("Variación mensual del AL30D (%)")
    ax.set_title(f"β1 = {V.num(reg['b1'])} · {V.p_texto(reg['p_b1'])} · R² = {V.num(reg['r2'])} · n = {reg['n']}")
    ax.xaxis.set_major_formatter(_fmt())
    ax.yaxis.set_major_formatter(_fmt())
    ax.grid(True, axis="both")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3)
    fig.tight_layout()
    return fig


def fig_desfases(r: dict, e: dict, t: dict):
    filas = r["desfases"]
    d = np.array([f["d"] for f in filas])
    colores = [t["s1"] if f["etiqueta"] == "principal" else t["s2"] if f["etiqueta"] == "extensión" else t["neutro"]
               for f in filas]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    for di, f, c in zip(d, filas, colores):
        a1.plot([di, di], [f["ic_b1"]["inferior"], f["ic_b1"]["superior"]], color=c, linewidth=2)
        a1.plot(di, f["b1"], "o", color=c, markersize=8, markeredgecolor=t["fondo"], markeredgewidth=1.5)
        a2.plot(di, f["p_valor"], "o", color=c, markersize=9, markeredgecolor=t["fondo"], markeredgewidth=1.5)
    a1.axhline(0, color=t["eje"], linewidth=1)
    a1.set_title("β1 e IC 95 % por desfase d")
    a1.set_ylabel("pp de AL30D por pp de PBI")
    a2.set_yscale("log")
    a2.axhline(0.05, color=t["tinta2"], linewidth=1)
    a2.axhline(0.01, color=t["tinta2"], linewidth=1)
    a2.text(-3.5, 0.05 * 1.12, "α = 0,05", va="bottom", fontsize=9, color=t["tinta2"])
    a2.text(-3.5, 0.01 * 1.12, "α/5 = 0,01 (exploratorios)", va="bottom", fontsize=9, color=t["tinta2"])
    a2.set_title("p-valor de β1 por desfase d (escala log)")
    a2.set_ylabel("p-valor")
    a2.yaxis.set_major_locator(FixedLocator([0.001, 0.01, 0.05, 0.1, 0.5, 1]))
    a2.yaxis.set_minor_locator(FixedLocator([]))
    a2.yaxis.set_major_formatter(_fmt())
    a2.set_ylim(min(0.0005, min(f["p_valor"] for f in filas) / 2), 1.3)
    for ax in (a1, a2):
        ax.set_xticks(d)
        ax.set_xticklabels([f"{v:+d}".replace("-", "−").replace("+0", "0") for v in d])
        ax.set_xlabel("d (meses): X = Var PBI en t + d")
        ax.set_xlim(-3.6, 3.9)
    a1.yaxis.set_major_formatter(_fmt())
    from matplotlib.lines import Line2D
    marcas = [Line2D([], [], marker="o", linestyle="none", color=c, markersize=8, label=l)
              for c, l in ((t["s1"], "principal (d = 0)"), (t["s2"], "extensión (d = +1)"), (t["neutro"], "exploratorio"))]
    a1.legend(handles=marcas, loc="upper left", fontsize=8.5)
    fig.tight_layout()
    return fig


def fig_residuos(r: dict, e: dict, t: dict):
    reg = e["principal"]["principal"]
    res, aj = reg["_residuos"], reg["_ajustados"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    a1.scatter(aj, res, s=40, color=t["s1"], edgecolors=t["fondo"], linewidths=1.5)
    a1.axhline(0, color=t["eje"], linewidth=1)
    a1.set_title("Residuos vs. valores ajustados")
    a1.set_xlabel("Ŷ (Var AL30D ajustada, %)")
    a1.set_ylabel("Residuo (pp)")
    rezagos = np.arange(1, 13)
    d = res - res.mean()
    acf = np.array([(d[k:] * d[:-k]).sum() / (d ** 2).sum() for k in rezagos])
    banda = 1.96 / np.sqrt(len(res))
    a2.bar(rezagos, acf, width=0.5, color=t["s1"])
    a2.axhline(banda, color=t["tinta2"], linewidth=1)
    a2.axhline(-banda, color=t["tinta2"], linewidth=1)
    a2.axhline(0, color=t["eje"], linewidth=1)
    a2.text(12.6, banda, " ±1,96/√n", va="bottom", fontsize=9, color=t["tinta2"])
    a2.set_title("Autocorrelación de los residuos (FAC)")
    a2.set_xlabel("Rezago (meses)")
    a2.set_xticks(rezagos)
    a1.xaxis.set_major_formatter(_fmt())
    for ax in (a1, a2):
        ax.yaxis.set_major_formatter(_fmt())
    fig.tight_layout()
    return fig


def fig_anova(r: dict, e: dict, t: dict):
    panel = e["principal"]["panel"]
    grupos = r["anova"]["grupos"]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    rng = np.random.default_rng(7)
    for i, g in enumerate(grupos):
        valores = panel.loc[panel["tercil_pbi"] == g["grupo"], "var_bono"].to_numpy()
        ax.scatter(i + rng.uniform(-0.12, 0.12, valores.size), valores, s=22, color=t["neutro"], alpha=0.7,
                   linewidths=0, zorder=2)
        ax.plot([i, i], [g["ic"]["inferior"], g["ic"]["superior"]], color=t["s1"], linewidth=2.5, zorder=3)
        ax.plot(i, g["media"], "o", color=t["s1"], markersize=10, markeredgecolor=t["fondo"], markeredgewidth=2, zorder=4)
        ax.text(i + 0.18, g["media"], f"x̄ = {V.num(g['media'], 2)} %\nn = {g['n']}", va="center", fontsize=9,
                color=t["tinta2"])
    ax.axhline(0, color=t["eje"], linewidth=1)
    limites = r["anova"].get("limites_terciles", {})
    ax.set_xticks(range(len(grupos)))
    ax.set_xticklabels([f"{g['grupo'].capitalize()}\n[{V.num(limites[g['grupo']][0], 2)} ; {V.num(limites[g['grupo']][1], 2)}] %"
                        if g["grupo"] in limites else g["grupo"] for g in grupos])
    ax.set_xlim(-0.5, len(grupos) - 0.2)
    ax.set_title(f"Var AL30D por tercil de la Var PBI: media e IC 95 % · F = {V.num(r['anova']['f'])} · "
                 f"{V.p_texto(r['anova']['p_valor'])}")
    ax.set_ylabel("Var AL30D (%)")
    ax.yaxis.set_major_formatter(_fmt())
    fig.tight_layout()
    return fig


def fig_robustez(r: dict, e: dict, t: dict):
    resp = r["robustez_trimestral"]["bateria_respaldo"]
    principal_frec = r["muestra"]["principal"]["frecuencia"]
    filas = [
        (f"{principal_frec.capitalize()}, d = 0 (principal)", r["hipotesis_principal"]["d0"], t["s1"]),
        (f"{principal_frec.capitalize()}, d = +1 (extensión)", r["hipotesis_principal"]["d1"], t["s1"]),
        (f"{resp['frecuencia'].capitalize()}, d = 0", resp["hipotesis_principal"]["d0"], t["s2"]),
        (f"{resp['frecuencia'].capitalize()}, d = +1", resp["hipotesis_principal"]["d1"], t["s2"]),
    ]
    for s in r["sensibilidades"]:
        if s["id"] in ("a", "b", "d", "h"):
            filas.append((s["especificacion"].split(") ", 1)[1], {"b1": s["coeficiente"], "n": s["n"], "p_b1": s["p_valor"],
                          "ic_b1": {"inferior": s["ic_inferior"], "superior": s["ic_superior"]}}, t["neutro"]))
    fig, ax = plt.subplots(figsize=(10, 0.55 * len(filas) + 1.4))
    for i, (nombre, reg, color) in enumerate(filas):
        yy = len(filas) - 1 - i
        ax.plot([reg["ic_b1"]["inferior"], reg["ic_b1"]["superior"]], [yy, yy], color=color, linewidth=2.5)
        ax.plot(reg["b1"], yy, "o", color=color, markersize=9, markeredgecolor=t["fondo"], markeredgewidth=1.5)
    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels([f"{n}  ·  n = {reg['n']}, {V.p_texto(reg['p_b1'])}" for n, reg, _ in reversed(filas)],
                       fontsize=9.5)
    ax.axvline(0, color=t["tinta2"], linewidth=1)
    ax.grid(True, axis="x")
    ax.grid(False, axis="y")
    ax.set_xlabel("β1: pp de variación del AL30D por pp de variación del PBI (IC 95 %)")
    ax.set_title("Coeficiente de la regresión simple según muestra y especificación")
    ax.xaxis.set_major_formatter(_fmt())
    fig.tight_layout()
    return fig


def fig_complementaria(r: dict, e: dict, t: dict):
    panel = e["principal"]["panel"]
    comp = r["prueba_complementaria"]
    fig, ax = plt.subplots(figsize=(10, 4.4))
    rng = np.random.default_rng(11)
    datos = [panel.loc[panel["grupo_bono"] == g, "var_pbi"].to_numpy() for g in ("suba", "baja")]
    caja = ax.boxplot(datos, positions=[0, 1], widths=0.4, patch_artist=True, showfliers=False,
                      medianprops={"color": t["tinta"], "linewidth": 2},
                      boxprops={"facecolor": "none", "edgecolor": t["tinta2"], "linewidth": 1.2},
                      whiskerprops={"color": t["tinta2"], "linewidth": 1.2}, capprops={"color": t["tinta2"]})
    del caja
    for i, (valores, color) in enumerate(zip(datos, (t["s1"], t["s2"]))):
        ax.scatter(i + rng.uniform(-0.14, 0.14, valores.size), valores, s=30, color=color,
                   edgecolors=t["fondo"], linewidths=1.2, zorder=3)
    ax.axhline(0, color=t["eje"], linewidth=1)
    ax.set_xticks([0, 1])
    ax.set_xticklabels([f"Meses de suba del AL30D (n = {datos[0].size})", f"Meses de baja del AL30D (n = {datos[1].size})"])
    if comp.get("aplicable"):
        dec = comp["decision"]
        ax.set_title(f"Var PBI por signo de la variación del bono · diferencia = {V.num(dec['diferencia'])} pp · "
                     f"{V.p_texto(dec['p_valor'])}")
    ax.set_ylabel("Var PBI mensualizado (%)")
    ax.yaxis.set_major_formatter(_fmt())
    fig.tight_layout()
    return fig


# --- Metadatos y exportación --------------------------------------------------------------------

def _alt(r: dict) -> dict[str, str]:
    p0 = r["hipotesis_principal"]["d0"]
    n = r["muestra"]["principal"]["n"]
    resp = r["robustez_trimestral"]["bateria_respaldo"]["hipotesis_principal"]["d0"]
    exploratorios = ", ".join(f"d = {V.num(f['d'], 0, signo=True)}" for f in r["desfases"]
                              if f["etiqueta"] == "exploratoria" and f["significativo"])
    return {
        "series": f"Dos paneles con las {n} variaciones mensuales del AL30D (barras) y del PBI mensualizado (línea) "
                  f"entre {r['muestra']['principal']['inicio']} y {r['muestra']['principal']['fin']}. El bono oscila "
                  f"con amplitud mucho mayor que el PBI.",
        "pbi": "Nivel del PBI desde 2019: la serie original muestra el pico de cada segundo trimestre; la serie "
               "desestacionalizada y el spline mensual pasan por los niveles ajustados.",
        "histogramas": "Tres histogramas con la densidad Normal ajustada superpuesta: variación del AL30D, variación "
                       "del PBI y residuos de la regresión principal.",
        "dispersion": f"Dispersión de {n} meses: variación del PBI en el eje horizontal y del AL30D en el vertical. "
                      f"La recta de MCO tiene pendiente {V.num(p0['b1'])} ({V.p_texto(p0['p_b1'])}) y la banda de "
                      f"confianza al 95 % contiene la recta horizontal.",
        "desfases": "Coeficiente β1 con su intervalo al 95 % y p-valor para cada desfase d entre −3 y +3. "
                    + (f"Desfases exploratorios con p menor a 0,01: {exploratorios}."
                       if exploratorios else "Ningún desfase exploratorio tiene p menor a 0,01."),
        "residuos": f"Residuos contra valores ajustados y su función de autocorrelación hasta 12 rezagos. "
                    f"Durbin-Watson = {V.num(r['diagnosticos']['regresion_simple']['durbin_watson'], 2)}.",
        "anova": "Media de la variación del AL30D con su IC 95 % en cada tercil de la variación del PBI, con los "
                 "meses individuales detrás.",
        "robustez": f"Intervalos de β1 por muestra: mensual {V.num(p0['b1'])} ({V.p_texto(p0['p_b1'])}) y trimestral "
                    f"{V.num(resp['b1'])} ({V.p_texto(resp['p_b1'])}), más las sensibilidades de la serie mensual.",
        "complementaria": "Diagrama de caja de la variación del PBI en los meses de suba y en los de baja del AL30D, "
                          "con cada mes como punto.",
    }


FIGURAS = [
    ("series", "Figura 1. Variaciones mensuales del AL30D y del PBI", fig_series),
    ("pbi", "Figura 2. PBI original, desestacionalizado (STL) y mensualizado (spline)", fig_pbi),
    ("histogramas", "Figura 3. Distribuciones y Normal ajustada", fig_histogramas),
    ("dispersion", "Figura 4. Var AL30D vs. Var PBI con recta de regresión y banda de confianza", fig_dispersion),
    ("desfases", "Figura 5. Coeficiente y p-valor por desfase", fig_desfases),
    ("residuos", "Figura 6. Diagnóstico de residuos de la regresión principal", fig_residuos),
    ("anova", "Figura 7. Medias del AL30D por tercil del PBI", fig_anova),
    ("robustez", "Figura 8. Robustez: coeficiente e IC por muestra y especificación", fig_robustez),
    ("complementaria", "Figura 9. Var PBI en meses de suba y de baja del bono", fig_complementaria),
]


def _svg_para_web(fig, prefijo: str, tooltips: dict[str, list[str]] | None = None) -> str:
    buffer = io.StringIO()
    fig.savefig(buffer, format="svg", bbox_inches="tight", metadata={"Date": None})
    svg = buffer.getvalue()
    svg = svg[svg.index("<svg"):]
    svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.S)
    for hexa, variable in _CENTINELAS.items():
        svg = svg.replace(hexa, variable)
    if re.search(r"#fe00[0-9a-f]{2}", svg):
        raise ValueError(f"Quedó un color centinela sin reemplazar en la figura {prefijo}")
    svg = re.sub(r"font-family:[^;\"]*", "font-family: var(--fig-fuente)", svg)
    # IDs únicos por figura: varias figuras conviven en el mismo HTML.
    svg = re.sub(r'id="([^"]+)"', rf'id="{prefijo}-\1"', svg)
    svg = re.sub(r'href="#([^"]+)"', rf'href="#{prefijo}-\1"', svg)
    svg = re.sub(r"url\(#([^)]+)\)", rf"url(#{prefijo}-\1)", svg)
    svg = re.sub(r'<svg ([^>]*?)width="[^"]+" height="[^"]+"', r'<svg \1', svg, count=1)
    for gid, textos in (tooltips or {}).items():
        svg = _agregar_titulos(svg, f"{prefijo}-{gid}", textos)
    return svg.strip()


def _agregar_titulos(svg: str, gid: str, textos: list[str]) -> str:
    """Agrega <title> (tooltip nativo) a cada punto del grupo, en el orden de los datos."""
    inicio = svg.index(f'id="{gid}"')
    fin = svg.index("</g>", svg.index("</g>", inicio) + 1)
    bloque = svg[inicio:fin]
    usos = re.findall(r"<use [^>]*?/>", bloque)
    if len(usos) != len(textos):
        raise ValueError(f"{gid}: {len(usos)} puntos en el SVG y {len(textos)} textos")
    iterador = iter(textos)
    bloque = re.sub(r"<use ([^>]*?)/>", lambda m: f"<use {m.group(1)}><title>{next(iterador)}</title></use>", bloque)
    return svg[:inicio] + bloque + svg[fin:]


def generar(resultados: dict, extras: dict, dir_png: Path, dir_svg: Path) -> list[dict]:
    dir_png.mkdir(parents=True, exist_ok=True)
    dir_svg.mkdir(parents=True, exist_ok=True)
    alts = _alt(resultados)
    panel = extras["principal"]["panel"]
    tooltips = {"dispersion": {"puntos-dispersion": [
        f"{p}: PBI {V.num(x, 2, signo=True)} %, AL30D {V.num(y, 2, signo=True)} %"
        for p, x, y in zip(panel.index.astype(str), panel["var_pbi"], panel["var_bono"])]}}
    salida = []
    for nombre, titulo, funcion in FIGURAS:
        for web, tema in ((False, CLARO), (True, WEB)):
            _estilo(tema, web)
            fig = funcion(resultados, extras, tema)
            if web:
                (dir_svg / f"{nombre}.svg").write_text(_svg_para_web(fig, nombre, tooltips.get(nombre)),
                                                      encoding="utf-8", newline="\n")
            else:
                fig.savefig(dir_png / f"{nombre}.png", dpi=200, bbox_inches="tight")
            plt.close(fig)
        salida.append({"id": nombre, "titulo": titulo, "alt": alts[nombre], "png": f"{nombre}.png",
                       "svg": f"{nombre}.svg"})
        log.info("Figura %s generada", nombre)
    return salida
