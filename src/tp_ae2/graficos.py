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


REZAGOS_FAC = 12  # rezagos de la función de autocorrelación de los residuos (figura 6)
SENSIBILIDADES_ROBUSTEZ = ("a", "b", "d", "h")  # sensibilidades que muestra la figura 8


def _gids_barras(barras, etiqueta: str, valores=None) -> None:
    """gid m-<etiqueta>-<k>-pos|neg por barra: la web la hace crecer desde la línea de base (abajo o arriba)."""
    valores = None if valores is None else np.asarray(valores)
    for k, barra in enumerate(barras):
        signo = "neg" if valores is not None and valores[k] < 0 else "pos"
        barra.set_gid(f"m-{etiqueta}-{k}-{signo}")


# --- Figuras ------------------------------------------------------------------------------------

def fig_series(r: dict, e: dict, t: dict):
    panel = e["principal"]["panel"]
    fechas = _fechas(panel.index)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 5.8), sharex=True)
    colores = np.where(panel["var_bono"] >= 0, t["s1"], t["s2"])
    barras = a1.bar(fechas, panel["var_bono"], width=20, color=colores)
    _gids_barras(barras, "barras", panel["var_bono"])
    a1.patch.set_gid("m-ejes-0")
    a2.patch.set_gid("m-ejes-1")
    a1.axhline(0, color=t["eje"], linewidth=1)
    a1.set_title("Variación mensual del AL30D (ajustada por días ex-pago)")
    a1.set_ylabel("%")
    a2.plot(fechas, panel["var_pbi"], color=t["s1"], gid="m-pbi")
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
    ax.patch.set_gid("m-ejes-0")
    ax.plot(fechas_q, stl["original"] / 1000, color=t["s2"], linewidth=1.5, marker="o", markersize=4,
            label="Original trimestral (con estacionalidad)", gid="m-orig")
    ax.plot(_fechas(spline.index), spline / 1000, color=t["s1"], linewidth=2, label="Spline mensual sobre la serie SA",
            gid="m-spline")
    ax.plot(fechas_q, stl["nivel"] / 1000, linestyle="none", marker="o", markersize=7, color=t["s1"],
            markeredgecolor=t["fondo"], markeredgewidth=1.5, label="Desestacionalizada (STL), en el mes central",
            gid="m-stl")
    ax.set_title("PBI a precios de 2004: original, desestacionalizado y mensualizado")
    ax.set_ylabel("Miles de millones de $ de 2004")
    ax.yaxis.set_major_formatter(_fmt(0))
    ax.legend(loc="lower right").set_gid("m-leyenda")
    fig.tight_layout()
    return fig


def fig_histogramas(r: dict, e: dict, t: dict):
    panel = e["principal"]["panel"]
    series = [("Var AL30D (%)", panel["var_bono"].to_numpy()), ("Var PBI (%)", panel["var_pbi"].to_numpy()),
              ("Residuos de la regresión principal (pp)", e["principal"]["principal"]["_residuos"])]
    fig, ejes = plt.subplots(1, 3, figsize=(11, 3.8))
    for p, (ax, (titulo, x)) in enumerate(zip(ejes, series)):
        _, _, barras = ax.hist(x, bins="fd", density=True, color=t["s1"], alpha=0.35, edgecolor=t["s1"], linewidth=0.8)
        _gids_barras(barras, f"h{p}")
        grilla = np.linspace(x.min() - x.std(), x.max() + x.std(), 300)
        ax.plot(grilla, stats.norm.pdf(grilla, x.mean(), x.std(ddof=1)), color=t["s2"], linewidth=2, gid=f"m-n{p}")
        ax.set_title(titulo, fontsize=10.5)
        ax.set_ylabel("Densidad")
        ax.xaxis.set_major_formatter(_fmt())
        ax.yaxis.set_major_formatter(_fmt())
    ejes[1].legend(["Normal ajustada N(x̄, S)", "Histograma"], loc="upper left", fontsize=8.5).set_gid("m-leyenda")
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
                    label="IC 95 % de la media condicional").set_gid("m-banda")
    ax.plot(grilla, ajuste, color=t["s1"], linewidth=2, label="Recta de MCO", gid="m-recta")
    # Los puntos quedan en orden cronológico: la web los hace caer uno por uno en ese orden.
    puntos = ax.scatter(x, y, s=46, color=t["s2"], edgecolors=t["fondo"], linewidths=1.5, zorder=3,
                        label="Meses (oct-2021 a may-2026)")
    puntos.set_gid("m-puntos")
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
    for k, (di, f, c) in enumerate(zip(d, filas, colores)):
        # El desfase exploratorio que pasa el umbral lleva un anillo en la web.
        anillo = "-anillo" if f["etiqueta"] == "exploratoria" and f["significativo"] else ""
        a1.plot([di, di], [f["ic_b1"]["inferior"], f["ic_b1"]["superior"]], color=c, linewidth=2, gid=f"m-ic-{k}")
        a1.plot(di, f["b1"], "o", color=c, markersize=8, markeredgecolor=t["fondo"], markeredgewidth=1.5,
                gid=f"m-b1-{k}{anillo}")
        a2.plot(di, f["p_valor"], "o", color=c, markersize=9, markeredgecolor=t["fondo"], markeredgewidth=1.5,
                gid=f"m-p-{k}{anillo}")
    a1.axhline(0, color=t["eje"], linewidth=1, gid="m-ref-0")
    a1.set_title("β1 e IC 95 % por desfase d")
    a1.set_ylabel("pp de AL30D por pp de PBI")
    a2.set_yscale("log")
    a2.axhline(0.05, color=t["tinta2"], linewidth=1, gid="m-ref-1")
    a2.axhline(0.01, color=t["tinta2"], linewidth=1, gid="m-ref-2")
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
    a1.scatter(aj, res, s=40, color=t["s1"], edgecolors=t["fondo"], linewidths=1.5).set_gid("m-puntos")
    a1.axhline(0, color=t["eje"], linewidth=1)
    a1.set_title("Residuos vs. valores ajustados")
    a1.set_xlabel("Ŷ (Var AL30D ajustada, %)")
    a1.set_ylabel("Residuo (pp)")
    rezagos = np.arange(1, REZAGOS_FAC + 1)
    d = res - res.mean()
    acf = np.array([(d[k:] * d[:-k]).sum() / (d ** 2).sum() for k in rezagos])
    banda = 1.96 / np.sqrt(len(res))
    _gids_barras(a2.bar(rezagos, acf, width=0.5, color=t["s1"]), "fac", acf)
    a2.axhline(banda, color=t["tinta2"], linewidth=1, gid="m-banda-0")
    a2.axhline(-banda, color=t["tinta2"], linewidth=1, gid="m-banda-1")
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
                   linewidths=0, zorder=2).set_gid(f"m-pt{i}")
        ax.plot([i, i], [g["ic"]["inferior"], g["ic"]["superior"]], color=t["s1"], linewidth=2.5, zorder=3,
                gid=f"m-ic-{i}")
        ax.plot(i, g["media"], "o", color=t["s1"], markersize=10, markeredgecolor=t["fondo"], markeredgewidth=2, zorder=4,
                gid=f"m-media-{i}")
        ax.text(i + 0.18, g["media"], f"x̄ = {V.num(g['media'], 2)} %\nn = {g['n']}", va="center", fontsize=9,
                color=t["tinta2"], gid=f"m-rot-{i}")
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
        if s["id"] in SENSIBILIDADES_ROBUSTEZ:
            filas.append((s["especificacion"].split(") ", 1)[1], {"b1": s["coeficiente"], "n": s["n"], "p_b1": s["p_valor"],
                          "ic_b1": {"inferior": s["ic_inferior"], "superior": s["ic_superior"]}}, t["neutro"]))
    fig, ax = plt.subplots(figsize=(10, 0.55 * len(filas) + 1.4))
    for i, (nombre, reg, color) in enumerate(filas):
        yy = len(filas) - 1 - i
        ax.plot([reg["ic_b1"]["inferior"], reg["ic_b1"]["superior"]], [yy, yy], color=color, linewidth=2.5,
                gid=f"m-ic-{i}")
        ax.plot(reg["b1"], yy, "o", color=color, markersize=9, markeredgecolor=t["fondo"], markeredgewidth=1.5,
                gid=f"m-b1-{i}")
    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels([f"{n}  ·  n = {reg['n']}, {V.p_texto(reg['p_b1'])}" for n, reg, _ in reversed(filas)],
                       fontsize=9.5)
    ax.axvline(0, color=t["tinta2"], linewidth=1, gid="m-cero")
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
    # Cada caja (caja, bigotes, topes y mediana) lleva el índice de su grupo: en la web crece desde la mediana.
    for j in range(len(datos)):
        caja["boxes"][j].set_gid(f"m-caja-{j}-box")
        caja["medians"][j].set_gid(f"m-caja-{j}-med")
        for parte in ("whiskers", "caps"):
            for s, artista in enumerate(caja[parte][2 * j:2 * j + 2]):
                artista.set_gid(f"m-caja-{j}-{parte[0]}{s}")
    for i, (valores, color, grupo) in enumerate(zip(datos, (t["s1"], t["s2"]), ("suba", "baja"))):
        ax.scatter(i + rng.uniform(-0.14, 0.14, valores.size), valores, s=30, color=color,
                   edgecolors=t["fondo"], linewidths=1.2, zorder=3).set_gid(f"m-{grupo}")
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


# --- Motion de las figuras web ------------------------------------------------------------------
# Cada figura se arma en la web a partir de sus datos (barras que crecen, puntos que caen en orden, líneas que se
# trazan). Las figuras marcan sus artistas con gid "m-<etiqueta>[-k][-sufijo]"; _Motion lee la geometría del SVG
# final y deja en cada elemento class="m m--<tipo> f<fase>" y style="--i:<orden>". La figura recibe los tiempos de
# cada fase (--f<n>-t0, --f<n>-paso, --f<n>-dur); estilos.css hace el resto y navegacion.js solo decide cuándo.

TOPE_MS = 2400       # duración máxima de la coreografía de una figura
TANDA_MS = 1200      # una serie de N elementos escalonados termina de arrancar en este tiempo como mucho
PASO_MAX_MS = 25.0   # separación máxima entre elementos escalonados
_G = re.compile(r"<g[ >]|</g>")
_PATH = re.compile(r"<path\b[^>]*>")
_USO = re.compile(r"<use\b[^>]*?/>|<use\b[^>]*>.*?</use>", re.S)


def _paso(n: int, preferido: float = PASO_MAX_MS) -> float:
    return min(preferido, PASO_MAX_MS, TANDA_MS / max(n, 1))


def _sincronia(v: np.ndarray, ancho: float) -> str | None:
    """Easing linear() para que la punta de un trazo (que avanza por longitud de arco) quede bajo un cursor que
    avanza parejo en x. Devuelve None si la diferencia no llega al 2 % del ancho del panel."""
    x, y = v[:, 0], v[:, 1]
    arco = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(y)))]
    s, u = arco / arco[-1], (x - x[0]) / (x[-1] - x[0])
    grilla = np.linspace(0, 1, 501)
    desvio = np.max(np.abs(np.interp(grilla, s, x) - (x[0] + grilla * (x[-1] - x[0])))) / ancho
    if desvio <= 0.02:
        return None
    return "linear(" + ", ".join(f"{a:.4f} {b * 100:.2f}%" for a, b in zip(s, u)) + ")"


class _Motion:
    def __init__(self, svg: str, prefijo: str):
        self.svg, self.p = svg, prefijo
        self.fases: list[tuple[float, float, float, int]] = []
        self.conteo: dict[str, int] = {}
        self.extra: dict = {}
        caja = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
        self.ancho, self.alto = float(caja.group(1)), float(caja.group(2))

    def _bloques(self, etiqueta: str) -> list[tuple[int, int, int, int | None, str | None]]:
        """(inicio, fin de la etiqueta de apertura, fin del bloque, k, sufijo) de cada <g> con ese gid."""
        patron = re.compile(rf'<g id="{re.escape(self.p)}-m-{re.escape(etiqueta)}(?:-(\d+))?(?:-([a-z0-9]+))?">')
        bloques = []
        for mt in patron.finditer(self.svg):
            profundidad = 0
            for g in _G.finditer(self.svg, mt.start()):
                profundidad += -1 if g.group() == "</g>" else 1
                if profundidad == 0:
                    break
            k = None if mt.group(1) is None else int(mt.group(1))
            bloques.append((mt.start(), mt.end(), g.end(), k, mt.group(2)))
        if not bloques:
            raise ValueError(f"Figura {self.p}: no hay elementos m-{etiqueta} para animar")
        return bloques

    def _cambiar(self, cambios: list[tuple[int, int, str]]) -> None:
        for inicio, fin, texto in sorted(cambios, reverse=True):
            self.svg = self.svg[:inicio] + texto + self.svg[fin:]

    # Geometría, en las coordenadas del SVG final
    def vertices(self, etiqueta: str, k: int | None = None, sufijo: str | None = None) -> np.ndarray:
        for inicio, _, fin, kk, ss in self._bloques(etiqueta):
            if (k is None or kk == k) and (sufijo is None or ss == sufijo):
                d = re.search(r'<path\b[^>]*?\bd="([^"]+)"', self.svg[inicio:fin]).group(1)
                return np.array(re.findall(r"[ML] ([-\d.e]+) ([-\d.e]+)", d), dtype=float)
        raise ValueError(f"Figura {self.p}: falta m-{etiqueta}-{k}-{sufijo}")

    def ejes(self, k: int = 0) -> tuple[float, float, float, float]:
        v = self.vertices("ejes", k)
        return v[:, 0].min(), v[:, 0].max(), v[:, 1].min(), v[:, 1].max()

    def centros(self, etiqueta: str) -> np.ndarray:
        return np.array([self.vertices(etiqueta, k)[:, 0].mean() for *_, k, _ in self._bloques(etiqueta)])

    def usos(self, etiqueta: str) -> int:
        return sum(len(_USO.findall(self.svg[a:b])) for _, a, b, _, _ in self._bloques(etiqueta))

    # Marcas
    def fase(self, etiqueta: str, tipo: str, modo: str, t0: float, paso: float, dur: float, *,
             sinc: str | None = None, estilo=None, deco: bool = False) -> int:
        """modo "grupo": la clase va en el <g> del artista (--i = k del gid); "usos": cada marcador del artista,
        en orden (--i corrido); "trazo": el <path> de la línea, con pathLength="1" para dibujarla."""
        clase = f"m m--{tipo}{' m--deco' if deco else ''} f{len(self.fases) + 1}"
        cambios, n, i_max = [], 0, 0
        for inicio, fin_abre, fin, k, sufijo in self._bloques(etiqueta):
            i = n if k is None else k
            if modo == "grupo":
                marca = f" m--{sufijo}" if sufijo in ("pos", "neg") else ""
                extra = f";{estilo(k)}" if estilo else ""
                cambios.append((inicio, fin_abre, f'<g class="{clase}{marca}" style="--i:{i}{extra}">'))
                n, i_max = n + 1, max(i_max, i)
            elif modo == "usos":
                def envolver(mt):
                    nonlocal n
                    n += 1
                    return f'<g class="{clase}" style="--i:{n - 1}">{mt.group(0)}</g>'
                cambios.append((fin_abre, fin, _USO.sub(envolver, self.svg[fin_abre:fin])))
                i_max = n - 1
            elif modo == "trazo":
                mt = _PATH.search(self.svg, fin_abre, fin)
                variables = f"--i:{i};" + (f"--sinc:{sinc};" if sinc else "")
                etiqueta_path = mt.group(0).replace(
                    "<path ", f'<path pathLength="1" class="{clase}{" m--sinc" if sinc else ""}" ', 1)
                etiqueta_path = etiqueta_path.replace('style="', f'style="{variables}', 1)
                cambios.append((mt.start(), mt.end(), etiqueta_path))
                n, i_max = n + 1, max(i_max, i)
        self._cambiar(cambios)
        self._registrar(tipo, n, t0, paso, dur, i_max)
        return n

    def cursor(self, x: float, arriba: float, abajo: float, recorrido: float, dur: float) -> None:
        """Línea vertical que barre el panel: --dx es el recorrido en unidades del SVG."""
        linea = (f'<line class="m m--cursor m--deco f{len(self.fases) + 1}" x1="{x:.2f}" y1="{arriba:.2f}" '
                 f'x2="{x:.2f}" y2="{abajo:.2f}" style="--dx:{recorrido:.2f}px"/>\n')
        fin = self.svg.rindex("</svg>")
        self.svg = self.svg[:fin] + linea + self.svg[fin:]
        self._registrar("cursor", 1, 0, 0, dur, 0)

    def anillos(self, etiquetas: tuple[str, ...], t0: float, dur: float, radio: float = 5.5) -> None:
        """Anillo que se expande una vez sobre los marcadores con sufijo "anillo", con el color del marcador."""
        f, cambios = len(self.fases) + 1, []
        for etiqueta in etiquetas:
            for inicio, _, fin, _, sufijo in self._bloques(etiqueta):
                if sufijo != "anillo":
                    continue
                uso = re.search(r'<use [^>]*?x="([-\d.]+)" y="([-\d.]+)"[^>]*?style="fill: (var\(--fig-[a-z0-9]+\))',
                                self.svg[inicio:fin])
                cambios.append((fin, fin, f'<circle class="m m--anillo m--deco f{f}" cx="{uso.group(1)}" '
                                          f'cy="{uso.group(2)}" r="{radio}" style="stroke: {uso.group(3)}"/>'))
        if cambios:
            self._cambiar(cambios)
            self._registrar("anillo", len(cambios), t0, 0, dur, 0)

    def _registrar(self, tipo, n, t0, paso, dur, i_max) -> None:
        self.conteo[tipo] = self.conteo.get(tipo, 0) + n
        self.fases.append((round(t0), round(paso, 1), round(dur), i_max))

    def resultado(self) -> tuple[str, dict]:
        svg = re.sub(rf' id="{re.escape(self.p)}-m-[^"]*"', "", self.svg)
        duracion = max(t0 + i * paso + dur for t0, paso, dur, i in self.fases)
        if duracion > TOPE_MS:
            raise ValueError(f"Figura {self.p}: la coreografía dura {duracion:.0f} ms (tope {TOPE_MS} ms)")
        estilo = ";".join(f"--f{n}-t0:{t0}ms;--f{n}-paso:{paso}ms;--f{n}-dur:{dur}ms"
                          for n, (t0, paso, dur, _) in enumerate(self.fases, 1))
        return svg, {"estilo": estilo, "duracion": round(duracion), "conteo": self.conteo, **self.extra}


def _motion_series(m: _Motion, r: dict, e: dict) -> None:
    """Un cursor barre los dos paneles; cada barra crece cuando llega su mes y la línea del PBI se traza debajo."""
    x0, x1, arriba, _ = m.ejes(0)
    abajo = m.ejes(1)[3]
    ancho, barrido = x1 - x0, 2000.0
    m.cursor(x0, arriba, abajo, ancho, barrido / 0.92)  # el cursor llega al final al 92 % y se apaga
    c = m.centros("barras")
    m.fase("barras", "barra", "grupo", barrido * (c[0] - x0) / ancho, barrido * (c[-1] - c[0]) / ((len(c) - 1) * ancho), 380)
    v = m.vertices("pbi")
    m.fase("pbi", "trazo", "trazo", barrido * (v[0, 0] - x0) / ancho, 0, barrido * (v[-1, 0] - v[0, 0]) / ancho,
           sinc=_sincronia(v, ancho))
    panel = e["principal"]["panel"]
    m.extra["lecturas"] = [f"{p} · AL30D {V.num(b, 1, signo=True)} % · PBI {V.num(x, 1, signo=True)} %"
                           for p, b, x in zip(panel.index.astype(str), panel["var_bono"], panel["var_pbi"])]


def _motion_pbi(m: _Motion, r: dict, e: dict) -> None:
    """La serie original se traza y cada trimestre aparece al llegar la punta; después los puntos STL y el spline."""
    x0, x1, _, _ = m.ejes(0)
    v, dur = m.vertices("orig"), 1100
    m.fase("orig", "trazo", "trazo", 0, 0, dur, sinc=_sincronia(v, x1 - x0))
    m.fase("orig", "punto", "usos", 0, dur / (len(v) - 1), 320)
    m.fase("stl", "punto", "usos", 950, _paso(m.usos("stl"), 600 / m.usos("stl")), 360)
    m.fase("spline", "trazo", "trazo", 1250, 0, 650)
    m.fase("leyenda", "aparece", "grupo", 1900, 0, 400)


def _motion_histogramas(m: _Motion, r: dict, e: dict) -> None:
    for p in range(3):
        m.fase(f"h{p}", "barra", "grupo", 150 * p, _paso(len(m._bloques(f"h{p}")), 500 / len(m._bloques(f"h{p}"))), 420)
    for p in range(3):
        m.fase(f"n{p}", "trazo", "trazo", 650 + 150 * p, 0, 750)
    m.fase("leyenda", "aparece", "grupo", 1700, 0, 400)


def _motion_dispersion(m: _Motion, r: dict, e: dict) -> None:
    """Los meses caen uno por uno en orden cronológico; después la recta de MCO y la banda del IC."""
    n = m.usos("puntos")
    paso = _paso(n, 18)
    m.fase("puntos", "punto", "usos", 0, paso, 380)
    fin = (n - 1) * paso + 380
    m.fase("recta", "trazo", "trazo", fin - 250, 0, 600)
    m.fase("banda", "aparece", "grupo", fin + 250, 0, 450)


def _motion_desfases(m: _Motion, r: dict, e: dict) -> None:
    m.anillos(("b1", "p"), 1500, 700)
    m.fase("ref", "trazo", "trazo", 0, 70, 450)
    m.fase("ic", "ic", "grupo", 300, 110, 380)
    m.fase("b1", "punto", "grupo", 430, 110, 380)
    m.fase("p", "cae", "grupo", 380, 110, 420)


def _motion_residuos(m: _Motion, r: dict, e: dict) -> None:
    m.fase("puntos", "punto", "usos", 0, _paso(m.usos("puntos"), 16), 360)
    m.fase("fac", "barra", "grupo", 450, 55, 400)
    m.fase("banda", "trazo", "trazo", 1400, 90, 500)


def _motion_anova(m: _Motion, r: dict, e: dict) -> None:
    """Por tercil, en orden: los meses, después el IC desde su centro y la media."""
    bloque = 650
    for i in range(len(r["anova"]["grupos"])):
        n = m.usos(f"pt{i}")
        m.fase(f"pt{i}", "punto", "usos", i * bloque, _paso(n, 300 / n), 340)
    m.fase("ic", "ic", "grupo", 300, bloque, 380)
    m.fase("media", "punto", "grupo", 470, bloque, 380)
    m.fase("rot", "aparece", "grupo", 560, bloque, 350)


def _motion_robustez(m: _Motion, r: dict, e: dict) -> None:
    """Fila por fila, de arriba abajo: el IC crece desde β1 (el IC t es simétrico) y después aparece β1."""
    m.fase("cero", "trazo", "trazo", 0, 0, 450)
    m.fase("ic", "icx", "grupo", 200, 95, 420)
    m.fase("b1", "punto", "grupo", 380, 95, 380)


def _motion_complementaria(m: _Motion, r: dict, e: dict) -> None:
    n1, n2 = m.usos("suba"), m.usos("baja")
    paso = _paso(n1 + n2, 20)
    m.fase("suba", "punto", "usos", 0, paso, 360)
    m.fase("baja", "punto", "usos", n1 * paso, paso, 360)
    medianas = {j: m.vertices("caja", j, "med")[0, 1] for j in range(2)}
    m.fase("caja", "caja", "grupo", (n1 + n2 - 1) * paso + 160, 180, 500,
           estilo=lambda k: f"transform-origin:0 {medianas[k]:.2f}px;transform-box:view-box")


RECETAS = {"series": _motion_series, "pbi": _motion_pbi, "histogramas": _motion_histogramas,
           "dispersion": _motion_dispersion, "desfases": _motion_desfases, "residuos": _motion_residuos,
           "anova": _motion_anova, "robustez": _motion_robustez, "complementaria": _motion_complementaria}


def animar(svg: str, nombre: str, resultados: dict, extras: dict) -> tuple[str, dict]:
    m = _Motion(svg, nombre)
    RECETAS[nombre](m, resultados, extras)
    return m.resultado()


# --- Generación ---------------------------------------------------------------------------------

def _tooltips(extras: dict) -> dict[str, dict[str, list[str]]]:
    panel = extras["principal"]["panel"]
    return {"dispersion": {"m-puntos": [
        f"{p}: PBI {V.num(x, 2, signo=True)} %, AL30D {V.num(y, 2, signo=True)} %"
        for p, x, y in zip(panel.index.astype(str), panel["var_pbi"], panel["var_bono"])]}}


def figura_web(nombre: str, resultados: dict, extras: dict) -> tuple[str, dict]:
    """SVG de la web (colores ligados a variables CSS, ids únicos, tooltips) con su coreografía."""
    funcion = next(f for n, _, f in FIGURAS if n == nombre)
    _estilo(WEB, True)
    fig = funcion(resultados, extras, WEB)
    svg = _svg_para_web(fig, nombre, _tooltips(extras).get(nombre))
    plt.close(fig)
    return animar(svg, nombre, resultados, extras)


def generar(resultados: dict, extras: dict, dir_png: Path, dir_svg: Path) -> list[dict]:
    dir_png.mkdir(parents=True, exist_ok=True)
    dir_svg.mkdir(parents=True, exist_ok=True)
    alts = _alt(resultados)
    salida = []
    for nombre, titulo, funcion in FIGURAS:
        _estilo(CLARO, False)
        fig = funcion(resultados, extras, CLARO)
        fig.savefig(dir_png / f"{nombre}.png", dpi=200, bbox_inches="tight")
        plt.close(fig)
        svg, anim = figura_web(nombre, resultados, extras)
        (dir_svg / f"{nombre}.svg").write_text(svg, encoding="utf-8", newline="\n")
        salida.append({"id": nombre, "titulo": titulo, "alt": alts[nombre], "png": f"{nombre}.png",
                       "svg": f"{nombre}.svg", "anim": anim})
        log.info("Figura %s generada", nombre)
    return salida
