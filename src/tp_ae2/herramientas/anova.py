"""ANOVA de un factor, supuestos (Shapiro por grupo, Levene) y comparaciones de Tukey."""

from __future__ import annotations

import numpy as np
from scipy import stats

from .intervalos import ic_media


def anova_un_factor(y, grupos, orden: list[str], confianza: float = 0.95) -> dict:
    """F = CM entre / CM dentro, con k − 1 y N − k gl; η² = SC entre / SC total."""
    y, grupos = np.asarray(y, dtype=float), np.asarray(grupos)
    muestras = [y[grupos == g] for g in orden]
    N, k = y.size, len(orden)
    gran_media = y.mean()
    sc_entre = sum(m.size * (m.mean() - gran_media) ** 2 for m in muestras)
    sc_dentro = sum(((m - m.mean()) ** 2).sum() for m in muestras)
    sc_total = ((y - gran_media) ** 2).sum()
    gl_entre, gl_dentro = k - 1, N - k
    cm_entre, cm_dentro = sc_entre / gl_entre, sc_dentro / gl_dentro
    f = cm_entre / cm_dentro
    p = float(stats.f.sf(f, gl_entre, gl_dentro))
    return {
        "N": int(N), "k": int(k), "gran_media": float(gran_media),
        "grupos": [{"grupo": g, "n": int(m.size), "media": float(m.mean()), "desvio": float(m.std(ddof=1)),
                    "ic": ic_media(m, confianza)} for g, m in zip(orden, muestras)],
        "sc_entre": float(sc_entre), "sc_dentro": float(sc_dentro), "sc_total": float(sc_total),
        "gl_entre": int(gl_entre), "gl_dentro": int(gl_dentro), "gl_total": int(N - 1),
        "cm_entre": float(cm_entre), "cm_dentro": float(cm_dentro),
        "f": float(f), "valor_critico": float(stats.f.ppf(confianza, gl_entre, gl_dentro)),
        "p_valor": p, "eta2": float(sc_entre / sc_total),
    }


def supuestos_anova(y, grupos, orden: list[str], alfa: float = 0.05) -> dict:
    y, grupos = np.asarray(y, dtype=float), np.asarray(grupos)
    muestras = [y[grupos == g] for g in orden]
    shapiro = []
    for g, m in zip(orden, muestras):
        w, p = stats.shapiro(m)
        shapiro.append({"grupo": g, "n": int(m.size), "estadistico": float(w), "p_valor": float(p),
                        "rechaza_h0": bool(p < alfa)})
    lev, p_lev = stats.levene(*muestras, center="mean")
    return {"shapiro_por_grupo": shapiro,
            "levene": {"estadistico": float(lev), "gl": [len(orden) - 1, int(y.size - len(orden))],
                       "p_valor": float(p_lev), "rechaza_h0": bool(p_lev < alfa)}}


def tukey_hsd(y, grupos, orden: list[str], confianza: float = 0.95) -> list[dict]:
    y, grupos = np.asarray(y, dtype=float), np.asarray(grupos)
    resultado = stats.tukey_hsd(*[y[grupos == g] for g in orden])
    ic = resultado.confidence_interval(confidence_level=confianza)
    pares = []
    for i in range(len(orden)):
        for j in range(i + 1, len(orden)):
            pares.append({"par": f"{orden[i]} − {orden[j]}", "diferencia": float(resultado.statistic[i, j]),
                          "p_valor": float(resultado.pvalue[i, j]),
                          "ic": {"inferior": float(ic.low[i, j]), "superior": float(ic.high[i, j])}})
    return pares
