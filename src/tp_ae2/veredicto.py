"""Formato numérico es-AR y textos de veredicto (únicos para web, README, informe y resumen)."""

from __future__ import annotations

import math


def num(x: float | None, decimales: int = 4, signo: bool = False) -> str:
    """Coma decimal y punto de miles: 1234.5678 → '1.234,5678'."""
    if isinstance(x, str) and x in ("inf", "-inf"):
        x = float(x)  # resultados.json guarda los infinitos como texto
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    if isinstance(x, float) and math.isinf(x):
        return ("−∞" if x < 0 else "+∞") if signo or x < 0 else "∞"
    texto = f"{x:{'+' if signo and x != 0 else ''},.{decimales}f}"
    texto = texto.translate(str.maketrans({",": ".", ".": ","}))
    return texto.replace("-", "−")


def pval(p: float) -> str:
    """'0,0123' o '< 0,0001'."""
    return "< 0,0001" if p < 0.0001 else num(p, 4)


def p_texto(p: float) -> str:
    """'p = 0,0123' o 'p < 0,0001'."""
    return "p < 0,0001" if p < 0.0001 else f"p = {num(p, 4)}"


def gl_texto(gl) -> str:
    """Grados de libertad: enteros sin decimales, Welch con dos, pares separados por punto y coma."""
    if gl is None:
        return "—"
    if isinstance(gl, (list, tuple)):
        return "; ".join(gl_texto(g) for g in gl)
    if isinstance(gl, float) and not gl.is_integer():
        return num(gl, 2)
    return str(int(gl)) if isinstance(gl, (int, float)) else str(gl)


def ic_texto(inferior: float, superior: float, decimales: int = 4) -> str:
    return f"[{num(inferior, decimales)} ; {num(superior, decimales)}]"


def decision(p: float, alfa: float) -> str:
    return "Se rechaza H0" if p < alfa else "No se rechaza H0"


def _detalle(b1: float, ic: tuple[float, float], p: float, r2: float) -> str:
    return f"β1 = {num(b1)}; IC 95 % {ic_texto(*ic)}; {p_texto(p)}; R² = {num(r2)}"


def veredicto_principal(b1: float, ic: tuple[float, float], p: float, r2: float, alfa: float,
                        variable_x: str = "la variación mensual del PBI mensualizado") -> str:
    detalle = _detalle(b1, ic, p, r2)
    if p < alfa:
        return (f"SE AFIRMA la hipótesis principal: {variable_x} se asocia de forma "
                f"estadísticamente significativa con la variación del AL30D ({detalle}). "
                "Es una asociación estadística, no una relación causal.")
    return (f"NO HAY EVIDENCIA SUFICIENTE para afirmar la hipótesis principal ({detalle}). "
            "No haber rechazado H0 no prueba que β1 sea cero.")


def veredicto_extension(b1: float, ic: tuple[float, float], p: float, r2: float, alfa: float,
                        variable_x: str = "la variación del PBI mensualizado del mes siguiente") -> str:
    detalle = _detalle(b1, ic, p, r2)
    if p < alfa:
        return (f"SE AFIRMA la extensión temporal (d = +1): {variable_x} se "
                f"asocia de forma estadísticamente significativa con la variación del AL30D ({detalle}). "
                "Es una asociación estadística, no una relación causal.")
    return (f"NO HAY EVIDENCIA SUFICIENTE para afirmar la extensión temporal (d = +1) ({detalle}). "
            "No haber rechazado H0 no prueba que β1 sea cero.")


def interpretacion_pendiente(b1: float, unidad: str = "mensual") -> str:
    sentido = "más" if b1 >= 0 else "menos"
    signo = "positiva" if b1 >= 0 else "negativa"
    return (f"Pendiente {signo}: en la muestra, cada 1 pp adicional de variación {unidad} del PBI se asocia, "
            f"en promedio, con {num(abs(b1))} pp {sentido} de variación {unidad} del AL30D.")


def veredicto_complementaria(diferencia: float, ic: tuple[float, float], p: float, alfa: float) -> str:
    detalle = f"diferencia suba − baja = {num(diferencia)} pp; IC 95 % {ic_texto(*ic)}; {p_texto(p)}"
    if p < alfa:
        return ("SE AFIRMA la hipótesis complementaria: la variación media del PBI difiere entre los períodos de "
                f"suba y de baja del AL30D ({detalle}). Es una asociación estadística, no una relación causal.")
    return (f"NO HAY EVIDENCIA SUFICIENTE para afirmar la hipótesis complementaria ({detalle}). "
            "No haber rechazado H0 no prueba que las medias sean iguales.")
