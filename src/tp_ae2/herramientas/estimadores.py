"""Estimadores puntuales: media, varianza muestral, error estándar, forma y proporción."""

from __future__ import annotations

import numpy as np


def estimar(x) -> dict:
    """x̄ = Σx/n y S² = Σ(x − x̄)²/(n − 1), insesgados y consistentes para μ y σ²."""
    x = np.asarray(x, dtype=float)
    n = x.size
    media = x.sum() / n
    desvios = x - media
    varianza = (desvios ** 2).sum() / (n - 1)
    m2, m3, m4 = ((desvios ** p).mean() for p in (2, 3, 4))
    # Asimetría y curtosis (exceso) con corrección por tamaño de muestra (G1 y G2).
    g1 = m3 / m2 ** 1.5
    g2 = m4 / m2 ** 2 - 3
    asimetria = g1 * np.sqrt(n * (n - 1)) / (n - 2)
    curtosis = ((n + 1) * g2 + 6) * (n - 1) / ((n - 2) * (n - 3))
    return {
        "n": int(n),
        "media": float(media),
        "varianza": float(varianza),
        "desvio": float(np.sqrt(varianza)),
        "error_estandar": float(np.sqrt(varianza / n)),
        "minimo": float(x.min()),
        "maximo": float(x.max()),
        "asimetria": float(asimetria),
        "curtosis_exceso": float(curtosis),
    }


def estimar_proporcion(exitos: int, n: int) -> dict:
    """p̂ = X/n con EE(p̂) = √(p̂(1 − p̂)/n)."""
    p = exitos / n
    return {"n": int(n), "exitos": int(exitos), "proporcion": float(p),
            "error_estandar": float(np.sqrt(p * (1 - p) / n))}
