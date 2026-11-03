"""Regresión lineal simple y múltiple por MCO, y diagnósticos de los supuestos de Gauss-Markov."""

from __future__ import annotations

import numpy as np
import statsmodels.api as sm
from scipy import stats

from .intervalos import ic_coeficiente


def regresion_simple(x, y, confianza: float = 0.95) -> dict:
    """b1 = Sxy/Sxx, b0 = ȳ − b1·x̄; t = b1/EE(b1) con n − 2 gl."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    n = x.size
    x_media, y_media = x.mean(), y.mean()
    sxx = ((x - x_media) ** 2).sum()
    syy = ((y - y_media) ** 2).sum()
    sxy = ((x - x_media) * (y - y_media)).sum()
    b1 = sxy / sxx
    b0 = y_media - b1 * x_media
    ajustados = b0 + b1 * x
    residuos = y - ajustados
    sce = (residuos ** 2).sum()
    scr = b1 * sxy
    gl = n - 2
    s2 = sce / gl
    ee_b1 = np.sqrt(s2 / sxx)
    ee_b0 = np.sqrt(s2 * (1 / n + x_media ** 2 / sxx))
    t_b1, t_b0 = b1 / ee_b1, b0 / ee_b0
    f = scr / s2
    return {
        "n": int(n), "gl": int(gl),
        "b0": float(b0), "b1": float(b1), "ee_b0": float(ee_b0), "ee_b1": float(ee_b1),
        "t_b0": float(t_b0), "t_b1": float(t_b1),
        "p_b0": float(2 * stats.t.sf(abs(t_b0), gl)), "p_b1": float(2 * stats.t.sf(abs(t_b1), gl)),
        "valor_critico_t": float(stats.t.ppf(1 - (1 - confianza) / 2, gl)),
        "ic_b0": ic_coeficiente(b0, ee_b0, gl, confianza), "ic_b1": ic_coeficiente(b1, ee_b1, gl, confianza),
        "r2": float(1 - sce / syy), "r": float(sxy / np.sqrt(sxx * syy)),
        "s2": float(s2), "s": float(np.sqrt(s2)),
        "f": float(f), "gl_f": [1, int(gl)], "p_f": float(stats.f.sf(f, 1, gl)),
        "sce": float(sce), "scr": float(scr), "sct": float(syy),
        "sxx": float(sxx), "syy": float(syy), "sxy": float(sxy),
        "x_media": float(x_media), "y_media": float(y_media),
        "sumas": {"n": int(n), "sum_x": float(x.sum()), "sum_y": float(y.sum()), "sum_x2": float((x ** 2).sum()),
                  "sum_y2": float((y ** 2).sum()), "sum_xy": float((x * y).sum())},
        "_ajustados": ajustados, "_residuos": residuos,
    }


def _con_constante(X) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    X = X.reshape(-1, 1) if X.ndim == 1 else X
    return np.column_stack([np.ones(X.shape[0]), X])


def _r2_auxiliar(y, X_const) -> float:
    beta, *_ = np.linalg.lstsq(X_const, y, rcond=None)
    e = y - X_const @ beta
    return float(1 - (e @ e) / ((y - y.mean()) @ (y - y.mean())))


def regresion_multiple(X, y, nombres: list[str], confianza: float = 0.95) -> dict:
    """β̂ = (X'X)⁻¹X'y, Var(β̂) = S²(X'X)⁻¹, con n − k − 1 gl."""
    y = np.asarray(y, dtype=float)
    Xc = _con_constante(X)
    n, p = Xc.shape
    k = p - 1
    xtx_inv = np.linalg.inv(Xc.T @ Xc)
    beta = xtx_inv @ Xc.T @ y
    ajustados = Xc @ beta
    residuos = y - ajustados
    gl = n - p
    sce = float(residuos @ residuos)
    sct = float(((y - y.mean()) ** 2).sum())
    s2 = sce / gl
    ee = np.sqrt(np.diag(s2 * xtx_inv))
    t = beta / ee
    pvalores = 2 * stats.t.sf(np.abs(t), gl)
    r2 = 1 - sce / sct
    f = ((sct - sce) / k) / s2
    coeficientes = [{"nombre": nom, "coeficiente": float(b), "error_estandar": float(e), "t": float(tt),
                     "p_valor": float(pv), "ic": ic_coeficiente(b, e, gl, confianza)}
                    for nom, b, e, tt, pv in zip(["constante"] + list(nombres), beta, ee, t, pvalores)]
    return {
        "n": int(n), "k": int(k), "gl": int(gl), "coeficientes": coeficientes,
        "r2": float(r2), "r2_ajustado": float(1 - (1 - r2) * (n - 1) / gl),
        "s": float(np.sqrt(s2)), "s2": float(s2), "sce": sce, "sct": sct,
        "f": float(f), "gl_f": [int(k), int(gl)], "p_f": float(stats.f.sf(f, k, gl)),
        "_ajustados": ajustados, "_residuos": residuos, "_X": Xc,
    }


# --- Diagnósticos -------------------------------------------------------------------------------

def durbin_watson(residuos) -> float:
    """DW = Σ(e_t − e_{t−1})² / Σe_t²; cerca de 2 indica ausencia de autocorrelación de orden 1."""
    e = np.asarray(residuos, dtype=float)
    return float((np.diff(e) ** 2).sum() / (e ** 2).sum())


def breusch_pagan(residuos, X_const, alfa: float = 0.05) -> dict:
    """LM = n·R² de regresar e² sobre los regresores (versión de Koenker); χ² con k gl."""
    e2 = np.asarray(residuos, dtype=float) ** 2
    n, p = X_const.shape
    lm = n * _r2_auxiliar(e2, X_const)
    pv = float(stats.chi2.sf(lm, p - 1))
    return {"estadistico": float(lm), "gl": int(p - 1), "p_valor": pv, "rechaza_h0": pv < alfa}


def breusch_godfrey(residuos, X_const, rezagos: int, alfa: float = 0.05) -> dict:
    """LM = n·R² de regresar e_t sobre X y e_{t−1}, …, e_{t−p} (rezagos iniciales en 0); χ² con p gl."""
    e = np.asarray(residuos, dtype=float)
    n = e.size
    rezagados = np.column_stack([np.concatenate([np.zeros(j), e[:-j]]) for j in range(1, rezagos + 1)])
    lm = n * _r2_auxiliar(e, np.column_stack([X_const, rezagados]))
    pv = float(stats.chi2.sf(lm, rezagos))
    return {"estadistico": float(lm), "gl": int(rezagos), "p_valor": pv, "rechaza_h0": pv < alfa}


def vif(X_const, nombres: list[str]) -> list[dict]:
    """VIF_j = 1/(1 − R²_j), con R²_j de regresar X_j sobre los demás regresores."""
    salida = []
    for j, nombre in enumerate(nombres, start=1):
        otros = np.delete(X_const, j, axis=1)
        r2 = _r2_auxiliar(X_const[:, j], otros)
        salida.append({"variable": nombre, "r2_auxiliar": r2, "vif": float(1 / (1 - r2))})
    return salida


def diagnosticos(residuos, X_const, nombres: list[str], rezagos_bg: int, alfa: float = 0.05) -> dict:
    from .bondad_ajuste import normalidad
    salida = {
        "durbin_watson": durbin_watson(residuos),
        "breusch_pagan": breusch_pagan(residuos, X_const, alfa),
        "breusch_godfrey": breusch_godfrey(residuos, X_const, rezagos_bg, alfa),
        "normalidad_residuos": normalidad(residuos, alfa=alfa),
    }
    if len(nombres) > 1:
        salida["vif"] = vif(X_const, nombres)
        salida["correlaciones"] = np.corrcoef(X_const[:, 1:], rowvar=False).tolist()
    return salida


def hac_newey_west(X, y, nombres: list[str], maxlags: int, confianza: float = 0.95) -> dict:
    """Errores estándar HAC (Newey-West, núcleo de Bartlett). Solo como sensibilidad."""
    ajuste = sm.OLS(np.asarray(y, dtype=float), _con_constante(X)).fit(
        cov_type="HAC", cov_kwds={"maxlags": maxlags}, use_t=True)
    ic = ajuste.conf_int(alpha=1 - confianza)
    return {"maxlags": maxlags, "gl": int(ajuste.df_resid), "coeficientes": [
        {"nombre": nom, "coeficiente": float(b), "error_estandar": float(e), "t": float(t), "p_valor": float(p),
         "ic": {"inferior": float(lo), "superior": float(hi)}}
        for nom, b, e, t, p, (lo, hi) in zip(["constante"] + list(nombres), ajuste.params, ajuste.bse,
                                             ajuste.tvalues, ajuste.pvalues, ic)]}
