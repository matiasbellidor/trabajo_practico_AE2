"""Bondad de ajuste a la Normal: χ² con clases equiprobables y Shapiro-Wilk como complemento."""

from __future__ import annotations

import numpy as np
from scipy import stats

PARAMETROS_ESTIMADOS = 2  # μ y σ se estiman con x̄ y S


def chi2_normal(x, max_clases: int = 8, esperada_minima: int = 5, alfa: float = 0.05) -> dict:
    """χ² = Σ(O − E)²/E con k clases equiprobables bajo N(x̄, S); gl = k − 1 − 2."""
    x = np.asarray(x, dtype=float)
    n = x.size
    k = min(max_clases, n // esperada_minima)
    gl = k - 1 - PARAMETROS_ESTIMADOS
    if gl < 1:
        return {"aplicable": False, "n": int(n), "k": int(k), "gl": int(gl),
                "motivo": f"Con n = {n} solo se pueden formar {k} clases con esperada ≥ {esperada_minima}: "
                          f"gl = {gl} < 1. Se usa Shapiro-Wilk."}
    media, desvio = x.mean(), x.std(ddof=1)
    limites = stats.norm.ppf(np.arange(1, k) / k, media, desvio)
    observadas = np.bincount(np.searchsorted(limites, x, side="right"), minlength=k)
    esperadas = np.full(k, n / k)
    contribucion = (observadas - esperadas) ** 2 / esperadas
    estadistico = float(contribucion.sum())
    p = float(stats.chi2.sf(estadistico, gl))
    bordes = np.concatenate(([-np.inf], limites, [np.inf]))
    tabla = [{"clase": i + 1, "limite_inferior": float(bordes[i]), "limite_superior": float(bordes[i + 1]),
              "observada": int(observadas[i]), "esperada": float(esperadas[i]),
              "contribucion": float(contribucion[i])} for i in range(k)]
    return {"aplicable": True, "n": int(n), "k": int(k), "gl": int(gl), "media": float(media),
            "desvio": float(desvio), "estadistico": estadistico,
            "valor_critico": float(stats.chi2.ppf(1 - alfa, gl)), "p_valor": p,
            "rechaza_h0": p < alfa, "tabla": tabla}


def shapiro_wilk(x, alfa: float = 0.05) -> dict:
    w, p = stats.shapiro(np.asarray(x, dtype=float))
    return {"n": int(len(x)), "estadistico": float(w), "p_valor": float(p), "rechaza_h0": bool(p < alfa)}


def normalidad(x, max_clases: int = 8, esperada_minima: int = 5, alfa: float = 0.05) -> dict:
    """Ambos tests y si coinciden en la decisión."""
    chi2 = chi2_normal(x, max_clases, esperada_minima, alfa)
    shapiro = shapiro_wilk(x, alfa)
    coinciden = None if not chi2["aplicable"] else chi2["rechaza_h0"] == shapiro["rechaza_h0"]
    return {"chi2": chi2, "shapiro": shapiro, "coinciden": coinciden}
