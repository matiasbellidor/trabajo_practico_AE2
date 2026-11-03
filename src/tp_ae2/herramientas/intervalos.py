"""Intervalos de confianza: media, proporción (Wald), coeficientes y diferencia de medias."""

from __future__ import annotations

import numpy as np
from scipy import stats

from .estimadores import estimar


def _cuantil_t(confianza: float, gl: float) -> float:
    return float(stats.t.ppf(1 - (1 - confianza) / 2, gl))


def ic_media(x, confianza: float = 0.95) -> dict:
    """x̄ ± t(α/2; n−1)·S/√n."""
    est = estimar(x)
    t = _cuantil_t(confianza, est["n"] - 1)
    margen = t * est["error_estandar"]
    return {"parametro": "media", "estimacion": est["media"], "error_estandar": est["error_estandar"],
            "gl": est["n"] - 1, "cuantil": t, "margen": margen,
            "inferior": est["media"] - margen, "superior": est["media"] + margen, "confianza": confianza}


def ic_proporcion_wald(exitos: int, n: int, confianza: float = 0.95) -> dict:
    """p̂ ± z(α/2)·√(p̂(1 − p̂)/n)."""
    p = exitos / n
    z = float(stats.norm.ppf(1 - (1 - confianza) / 2))
    ee = np.sqrt(p * (1 - p) / n)
    return {"parametro": "proporcion", "estimacion": p, "error_estandar": float(ee), "cuantil": z,
            "margen": float(z * ee), "inferior": float(p - z * ee), "superior": float(p + z * ee),
            "confianza": confianza}


def ic_coeficiente(b: float, ee: float, gl: float, confianza: float = 0.95) -> dict:
    """b ± t(α/2; gl)·EE(b)."""
    t = _cuantil_t(confianza, gl)
    return {"estimacion": float(b), "error_estandar": float(ee), "gl": gl, "cuantil": t,
            "inferior": float(b - t * ee), "superior": float(b + t * ee), "confianza": confianza}


def ic_diferencia_medias(a, b, confianza: float = 0.95, varianzas_iguales: bool = True) -> dict:
    """(x̄₁ − x̄₂) ± t·EE, con varianza agrupada o con la aproximación de Welch."""
    ea, eb = estimar(a), estimar(b)
    n1, n2, v1, v2 = ea["n"], eb["n"], ea["varianza"], eb["varianza"]
    diferencia = ea["media"] - eb["media"]
    if varianzas_iguales:
        sp2 = ((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2)
        ee = np.sqrt(sp2 * (1 / n1 + 1 / n2))
        gl = n1 + n2 - 2
    else:
        ee = np.sqrt(v1 / n1 + v2 / n2)
        # Grados de libertad de Welch-Satterthwaite.
        gl = (v1 / n1 + v2 / n2) ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
    resultado = ic_coeficiente(diferencia, ee, gl, confianza)
    resultado["parametro"] = "diferencia de medias"
    return resultado
