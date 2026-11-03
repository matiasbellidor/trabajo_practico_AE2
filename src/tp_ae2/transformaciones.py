"""Series de trabajo: bono con ajuste ex-pago, PBI desestacionalizado y mensualizado, CCL implícito y paneles."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from statsmodels.tsa.seasonal import STL

from . import io_datos
from .config import Config

log = logging.getLogger(__name__)

DESFASES = range(-3, 4)


@dataclass
class DatosBase:
    bono: pd.DataFrame
    retornos: pd.DataFrame
    pbi: pd.Series
    huecos: pd.DataFrame
    ccl: pd.Series | None = None
    ccl_operado: pd.Series | None = None
    ccl_info: dict = field(default_factory=dict)
    pbi_desest_indec: pd.Series | None = None


def cargar_base(cfg: Config) -> DatosBase:
    io_datos.verificar_obligatorios(cfg)
    bono = io_datos.leer_bono(cfg.ruta("al30d"))
    retornos = log_retornos_diarios(bono["c"], cfg["bono"]["dias_ex_pago"])
    pbi = io_datos.leer_pbi(cfg.ruta("pbi"))
    huecos = io_datos.huecos(bono.index, cfg["bono"]["hueco_maximo_dias"])
    base = DatosBase(bono=bono, retornos=retornos, pbi=pbi, huecos=huecos)
    if cfg.ruta("pbi_indec_desest").exists():
        base.pbi_desest_indec = io_datos.leer_pbi_desest_indec(cfg.ruta("pbi_indec_desest"))

    usar_ccl = cfg["regresion_multiple"]["control_preferido"] == "ccl"
    if usar_ccl and cfg.ruta("al30").exists() and cfg.ruta("al30c").exists():
        pesos = io_datos.leer_bono(cfg.ruta("al30"))["c"]
        cable_df = io_datos.leer_bono(cfg.ruta("al30c"))
        cable = cable_df["c"]
        base.ccl = ccl_implicito(pesos, cable)
        operado = cable_df.index[cable_df["v"] > 0]
        base.ccl_operado = base.ccl.loc[base.ccl.index.intersection(operado)]
        sin_volumen = cable_df["v"] <= 0
        base.ccl_info = {
            "ruedas_al30": len(pesos),
            "ruedas_al30c": len(cable),
            "ruedas_comunes": len(base.ccl),
            "ruedas_al30_sin_al30c": int(len(pesos.index.difference(cable.index))),
            "ruedas_al30c_sin_al30": int(len(cable.index.difference(pesos.index))),
            "al30c_share_sin_volumen_por_anio": {str(a): round(float(v), 3) for a, v in
                                                 sin_volumen.groupby(cable_df.index.year).mean().items()},
        }
    else:
        base.ccl_info = {"motivo": "No están al30.json y al30c.json, o el control preferido no es el CCL."}
    return base


# --- Bono ---------------------------------------------------------------------------------------

def log_retornos_diarios(cierres: pd.Series, dias_ex_pago: Iterable[str]) -> pd.DataFrame:
    """Log-retornos diarios brutos y ajustados (retorno 0 en los días ex-pago)."""
    bruto = np.log(cierres).diff().iloc[1:]
    ex_pago = pd.DatetimeIndex(pd.to_datetime(list(dias_ex_pago)))
    faltan = ex_pago.difference(bruto.index)
    if len(faltan):
        raise ValueError(f"Días ex-pago sin cotización: {[d.date().isoformat() for d in faltan]}")
    ajustado = bruto.copy()
    ajustado.loc[ex_pago] = 0.0
    return pd.DataFrame({"bruto": bruto, "ajustado": ajustado})


def variacion_por_periodo(log_ret: pd.Series, freq: str) -> pd.Series:
    """(exp(Σ log-retornos del período) − 1)·100; descarta el período inicial, que es parcial."""
    periodos = log_ret.index.to_period(freq)
    var = (np.exp(log_ret.groupby(periodos).sum()) - 1) * 100
    return var[var.index > periodos[0]]


def resumen_bono(bono: pd.DataFrame, retornos: pd.DataFrame, freq: str,
                 dias_ex_pago: Iterable[str]) -> pd.DataFrame:
    """Variación por período del AL30D con los datos crudos que la originan (trazabilidad)."""
    periodos = bono.index.to_period(freq)
    ultimo = bono.groupby(periodos).tail(1)
    ex_pago = pd.to_datetime(list(dias_ex_pago))
    ex_por_periodo = pd.Series(ex_pago, index=ex_pago.to_period(freq)).dt.strftime("%Y-%m-%d")
    df = pd.DataFrame({
        "fecha_ultimo_cierre": ultimo.index.strftime("%Y-%m-%d"),
        "cierre_al30d": ultimo["c"].to_numpy(),
        "ruedas": bono.groupby(periodos).size().to_numpy(),
    }, index=ultimo.index.to_period(freq))
    df["dias_ex_pago"] = ex_por_periodo.groupby(level=0).agg(" ".join).reindex(df.index).fillna("")
    df["var_bono"] = variacion_por_periodo(retornos["ajustado"], freq)
    df["var_bono_bruto"] = variacion_por_periodo(retornos["bruto"], freq)
    return df


# --- PBI ----------------------------------------------------------------------------------------

def desestacionalizar(nivel_q: pd.Series, metodo: str, periodo: int = 4, robusto: bool = True) -> pd.DataFrame:
    """STL sobre el log del nivel; SA = exp(log y − componente estacional)."""
    log_y = np.log(nivel_q)
    df = pd.DataFrame({"original": nivel_q, "log_original": log_y}, index=nivel_q.index)
    if metodo == "ninguna":
        df["estacional"] = 0.0
        df["nivel"] = nivel_q
    else:
        ajuste = STL(log_y.to_numpy(), period=periodo, robust=robusto).fit()
        df["tendencia"] = ajuste.trend
        df["estacional"] = ajuste.seasonal
        df["resto"] = ajuste.resid
        df["nivel"] = np.exp(log_y - df["estacional"])
    df["factor_estacional"] = np.exp(df["estacional"])
    return df


def mensualizar_spline(nivel_q: pd.Series, bc_type: str = "natural", desplazamiento: int = 1) -> pd.Series:
    """Spline cúbico por los niveles ubicados en el mes central de cada trimestre, sin extrapolar."""
    meses_centrales = nivel_q.index.asfreq("M", how="start") + desplazamiento
    spline = CubicSpline(meses_centrales.asi8, nivel_q.to_numpy(float), bc_type=bc_type)
    meses = pd.period_range(meses_centrales[0], meses_centrales[-1], freq="M")
    return pd.Series(spline(meses.asi8), index=meses, name="nivel_pbi")


def variacion_pct(serie: pd.Series) -> pd.Series:
    return (serie / serie.shift(1) - 1) * 100


def autocorrelacion(x: Iterable[float], rezago: int = 1) -> float:
    """Autocorrelación muestral: Σ(x_t − x̄)(x_{t−k} − x̄) / Σ(x_t − x̄)²."""
    x = np.asarray(list(x), dtype=float)
    d = x - x.mean()
    return float((d[rezago:] * d[:-rezago]).sum() / (d ** 2).sum())


# --- CCL implícito ------------------------------------------------------------------------------

def ccl_implicito(al30_pesos: pd.Series, al30_cable: pd.Series) -> pd.Series:
    """Cierre AL30 (ARS) / cierre AL30C (USD cable) en las ruedas comunes."""
    comunes = al30_pesos.index.intersection(al30_cable.index)
    return (al30_pesos.loc[comunes] / al30_cable.loc[comunes]).rename("ccl")


def ultimo_por_periodo(serie_diaria: pd.Series, freq: str) -> pd.Series:
    return serie_diaria.groupby(serie_diaria.index.to_period(freq)).last()


# --- Paneles ------------------------------------------------------------------------------------

def _agregar_grupos(panel: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    k = cfg["prueba_complementaria"]["umbral_k"]
    panel["grupo_bono"] = np.select([panel["var_bono"] > k, panel["var_bono"] < k], ["suba", "baja"], "sin cambio")
    etiquetas = cfg["anova"]["etiquetas"]
    panel["tercil_pbi"] = pd.qcut(panel["var_pbi"], 3, labels=etiquetas).astype(str)
    bajo, alto = cfg["anova"]["umbrales_sensibilidad"]
    panel["grupo_umbral"] = np.select([panel["var_pbi"] < bajo, panel["var_pbi"] > alto], etiquetas[::2], etiquetas[1])
    return panel


def construir_panel(base: DatosBase, cfg: Config, frecuencia: str) -> pd.DataFrame:
    """Panel con variación del bono, variación del PBI, desfases, CCL y grupos para los tests."""
    freq = "M" if frecuencia == "mensual" else "Q"
    ventana = cfg["ventana_mensual" if freq == "M" else "ventana_trimestral"]
    indice = pd.period_range(ventana["inicio"], ventana["fin"], freq=freq)

    panel = resumen_bono(base.bono, base.retornos, freq, cfg["bono"]["dias_ex_pago"]).reindex(indice)
    if cfg["pbi"]["desestacionalizar"] == "indec":
        if base.pbi_desest_indec is None:
            raise ValueError("pbi.desestacionalizar = indec requiere el archivo de rutas.pbi_indec_desest")
        pbi = pd.DataFrame({"nivel": base.pbi_desest_indec})
    else:
        pbi = desestacionalizar(base.pbi, cfg["pbi"]["desestacionalizar"], cfg["pbi"]["stl_periodo"],
                                cfg["pbi"]["stl_robusto"])
    if freq == "M":
        nivel = mensualizar_spline(pbi["nivel"], cfg["pbi"]["spline_bc"], cfg["pbi"]["desplazamiento_mes_central"])
    else:
        nivel = pbi["nivel"]
    var_pbi = variacion_pct(nivel)
    panel["nivel_pbi"] = nivel.reindex(indice)
    panel["var_pbi"] = var_pbi.reindex(indice)
    for d in DESFASES:
        # Las series son regulares, así que desplazar posiciones equivale a desplazar períodos.
        panel[f"var_pbi_d{d:+d}"] = var_pbi.shift(-d).reindex(indice)

    if base.ccl is not None:
        ccl = ultimo_por_periodo(base.ccl, freq)
        panel["ccl_implicito"] = ccl.reindex(indice)
        panel["var_ccl"] = variacion_pct(ccl).reindex(indice)
        if panel["var_ccl"].isna().any():
            log.warning("El CCL implícito no cubre toda la ventana %s: se omite como control.", frecuencia)
            panel = panel.drop(columns=["ccl_implicito", "var_ccl"])
        elif base.ccl_operado is not None:
            # Meses sin ninguna rueda operada quedan NaN, y también la variación del mes siguiente.
            todos = pd.period_range(ccl.index[0], ccl.index[-1], freq=freq)
            operado = ultimo_por_periodo(base.ccl_operado, freq).reindex(todos)
            panel["var_ccl_operado"] = variacion_pct(operado).reindex(indice)
            ultimo_cable = base.ccl.groupby(base.ccl.index.to_period(freq)).tail(1).index
            ultimo_operado = base.ccl_operado.index
            panel["cierre_ccl_sin_volumen"] = (pd.Series(~ultimo_cable.isin(ultimo_operado),
                                                         index=ultimo_cable.to_period(freq)).reindex(indice))

    for columna in ("var_bono", "var_pbi"):
        if panel[columna].isna().any():
            faltan = [str(p) for p in panel.index[panel[columna].isna()]]
            raise ValueError(f"Panel {frecuencia}: faltan valores de {columna} en {faltan}")
    panel = _agregar_grupos(panel, cfg)
    panel.index.name = "periodo"
    return panel
