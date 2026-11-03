"""Diferencia de medias entre dos grupos: F de varianzas, t agrupada, Welch, d de Cohen y potencia."""

from __future__ import annotations

import numpy as np
from scipy import stats
from statsmodels.stats.power import TTestIndPower

from .estimadores import estimar
from .intervalos import ic_diferencia_medias


def prueba_f_varianzas(a, b, alfa: float = 0.05) -> dict:
    """F = S₁²/S₂² con (n₁ − 1, n₂ − 1) gl; p bilateral = 2·min(P(F ≤ f), P(F ≥ f))."""
    ea, eb = estimar(a), estimar(b)
    f = ea["varianza"] / eb["varianza"]
    gl1, gl2 = ea["n"] - 1, eb["n"] - 1
    p = float(min(1.0, 2 * min(stats.f.cdf(f, gl1, gl2), stats.f.sf(f, gl1, gl2))))
    return {"estadistico": float(f), "gl": [gl1, gl2], "p_valor": p, "rechaza_h0": p < alfa}


def prueba_t(a, b, varianzas_iguales: bool, confianza: float = 0.95) -> dict:
    """t = (x̄₁ − x̄₂)/EE, con varianza agrupada (n₁ + n₂ − 2 gl) o Welch (gl de Satterthwaite)."""
    ic = ic_diferencia_medias(a, b, confianza, varianzas_iguales)
    t = ic["estimacion"] / ic["error_estandar"]
    p = float(2 * stats.t.sf(abs(t), ic["gl"]))
    return {"tipo": "varianza agrupada" if varianzas_iguales else "Welch", "diferencia": ic["estimacion"],
            "error_estandar": ic["error_estandar"], "estadistico": float(t), "gl": float(ic["gl"]),
            "p_valor": p, "rechaza_h0": p < 1 - confianza, "ic": ic}


def desvio_agrupado(a, b) -> float:
    ea, eb = estimar(a), estimar(b)
    n1, n2 = ea["n"], eb["n"]
    return float(np.sqrt(((n1 - 1) * ea["varianza"] + (n2 - 1) * eb["varianza"]) / (n1 + n2 - 2)))


def d_cohen(a, b) -> float:
    """d = (x̄₁ − x̄₂)/Sp."""
    return float((np.mean(a) - np.mean(b)) / desvio_agrupado(a, b))


def diferencia_minima_detectable(n1: int, n2: int, sp: float, alfa: float = 0.05, potencia: float = 0.8) -> dict:
    """Efecto estandarizado que el test bilateral detecta con la potencia pedida, expresado en unidades de Y."""
    efecto = TTestIndPower().solve_power(effect_size=None, nobs1=n1, alpha=alfa, power=potencia,
                                         ratio=n2 / n1, alternative="two-sided")
    return {"d": float(efecto), "en_unidades": float(efecto * sp), "potencia": potencia}


def prueba_complementaria(a, b, alfa: float = 0.05, potencia: float = 0.8) -> dict:
    """Regla de la cátedra: F primero; si no rechaza, t agrupada; si rechaza, Welch."""
    confianza = 1 - alfa
    f = prueba_f_varianzas(a, b, alfa)
    agrupada = prueba_t(a, b, True, confianza)
    welch = prueba_t(a, b, False, confianza)
    decision = welch if f["rechaza_h0"] else agrupada
    sp = desvio_agrupado(a, b)
    return {
        "grupo_1": estimar(a), "grupo_2": estimar(b),
        "prueba_f": f, "t_agrupada": agrupada, "t_welch": welch,
        "test_de_decision": decision["tipo"], "decision": decision,
        "d_cohen": d_cohen(a, b), "desvio_agrupado": sp,
        "diferencia_minima_detectable": diferencia_minima_detectable(len(a), len(b), sp, alfa, potencia),
    }
