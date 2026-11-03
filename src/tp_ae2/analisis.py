"""Batería de herramientas sobre un panel, robustez entre muestras, sensibilidades y tabla de p-valores."""

from __future__ import annotations

import logging
import platform
from importlib.metadata import version

import numpy as np
import pandas as pd

from . import transformaciones as T
from . import veredicto as V
from .config import Config, con_cambios
from .herramientas.anova import anova_un_factor, supuestos_anova, tukey_hsd
from .herramientas.bondad_ajuste import normalidad
from .herramientas.diferencia_medias import prueba_complementaria
from .herramientas.estimadores import estimar, estimar_proporcion
from .herramientas.intervalos import ic_media, ic_proporcion_wald
from .herramientas.regresion import (diagnosticos, hac_newey_west, regresion_multiple, regresion_simple)
from .textos import NOMBRES

log = logging.getLogger(__name__)


def etiqueta_desfase(d: int, cfg: Config) -> tuple[str, float]:
    if d == cfg["desfases"]["principal"]:
        return "principal", cfg.alfa
    if d == cfg["desfases"]["extension"]:
        return "extensión", cfg.alfa
    return "exploratoria", float(cfg["desfases"]["alfa_exploratorio"])


def _tamanios_ok(*muestras, minimo: int = 3) -> bool:
    return all(len(m) >= minimo for m in muestras)


def _anova_completo(y, grupos, cfg: Config) -> dict:
    orden = list(cfg["anova"]["etiquetas"])
    tamanios = {g: int((np.asarray(grupos) == g).sum()) for g in orden}
    if min(tamanios.values()) < 3:
        return {"aplicable": False, "tamanios": tamanios, "motivo": "Algún grupo tiene menos de 3 observaciones."}
    resultado = anova_un_factor(y, grupos, orden, cfg.confianza)
    resultado["aplicable"] = True
    resultado["supuestos"] = supuestos_anova(y, grupos, orden, cfg.alfa)
    resultado["tukey"] = tukey_hsd(y, grupos, orden, cfg.confianza) if resultado["p_valor"] < cfg.alfa else None
    resultado["grupos_chicos"] = [g for g, n in tamanios.items() if n < cfg["anova"]["n_minimo_grupo"]]
    return resultado


def bateria(panel: pd.DataFrame, cfg: Config, frecuencia: str) -> tuple[dict, dict]:
    """Estimador, IC, bondad de ajuste, regresión simple y múltiple, ANOVA y prueba complementaria."""
    alfa, conf = cfg.alfa, cfg.confianza
    y = panel["var_bono"].to_numpy(float)
    x = panel["var_pbi"].to_numpy(float)
    n = len(panel)
    k = cfg["prueba_complementaria"]["umbral_k"]
    bondad_kw = {"max_clases": cfg["bondad_ajuste"]["max_clases"],
                 "esperada_minima": cfg["bondad_ajuste"]["esperada_minima"], "alfa": alfa}
    rezagos_bg = cfg["regresion_multiple"]["breusch_godfrey_nlags"]

    estimadores = {"var_bono": estimar(y), "var_pbi": estimar(x),
                   "proporcion_suba": estimar_proporcion(int((y > k).sum()), n)}
    if "var_ccl" in panel:
        estimadores["var_ccl"] = estimar(panel["var_ccl"])
    autocorrelaciones = {"var_bono": T.autocorrelacion(y), "var_pbi": T.autocorrelacion(x)}
    intervalos = {"media_var_bono": ic_media(y, conf), "media_var_pbi": ic_media(x, conf),
                  "proporcion_suba": ic_proporcion_wald(int((y > k).sum()), n, conf)}

    # Regresión simple para cada desfase d: X_t = Var PBI_{t+d}.
    desfases, regresiones = [], {}
    for d in T.DESFASES:
        columna = f"var_pbi_d{d:+d}"
        filas = panel[columna].notna()
        reg = regresion_simple(panel.loc[filas, columna], panel.loc[filas, "var_bono"], conf)
        etiqueta, umbral = etiqueta_desfase(d, cfg)
        regresiones[d] = reg
        desfases.append({"d": d, "etiqueta": etiqueta, "n": reg["n"], "b1": reg["b1"], "ee_b1": reg["ee_b1"],
                         "t": reg["t_b1"], "gl": reg["gl"], "p_valor": reg["p_b1"], "ic_b1": reg["ic_b1"],
                         "r2": reg["r2"], "umbral": umbral, "significativo": reg["p_b1"] < umbral,
                         "periodo_inicio": str(panel.index[filas][0]), "periodo_fin": str(panel.index[filas][-1])})
    principal, extension = regresiones[cfg["desfases"]["principal"]], regresiones[cfg["desfases"]["extension"]]
    X_simple = np.column_stack([np.ones(n), x])
    diag_simple = diagnosticos(principal["_residuos"], X_simple, ["var_pbi"], rezagos_bg, alfa)

    bondad = {"var_bono": normalidad(y, **bondad_kw), "var_pbi": normalidad(x, **bondad_kw),
              "residuos_principal": normalidad(principal["_residuos"], **bondad_kw)}

    # Regresión múltiple: CCL implícito como control si existe; si no, PBI adelantado.
    if "var_ccl" in panel:
        modo, nombres, filas = "ccl", ["var_pbi", "var_ccl"], np.ones(n, dtype=bool)
    else:
        modo, nombres = "pbi_adelantado", ["var_pbi", "var_pbi_d+1"]
        filas = panel["var_pbi_d+1"].notna().to_numpy()
    Xm = panel.loc[filas, nombres].to_numpy(float)
    ym = y[filas]
    multiple = regresion_multiple(Xm, ym, nombres, conf)
    multiple["modo"] = modo
    multiple["periodo_inicio"], multiple["periodo_fin"] = str(panel.index[filas][0]), str(panel.index[filas][-1])
    diag_multiple = diagnosticos(multiple["_residuos"], multiple["_X"], nombres, rezagos_bg, alfa)
    hac = hac_newey_west(Xm, ym, nombres, cfg["regresion_multiple"]["hac_maxlags"], conf)

    anova = _anova_completo(y, panel["tercil_pbi"].to_numpy(), cfg)
    anova["factor"] = "terciles de la variación del PBI"
    if anova["aplicable"]:
        limites = panel.groupby("tercil_pbi")["var_pbi"].agg(["min", "max"])
        anova["limites_terciles"] = {g: [float(limites.loc[g, "min"]), float(limites.loc[g, "max"])]
                                     for g in cfg["anova"]["etiquetas"]}
    anova_umbral = _anova_completo(y, panel["grupo_umbral"].to_numpy(), cfg)
    anova_umbral["factor"] = "umbrales fijos de ±0,5 % en la variación del PBI"

    suba = x[panel["grupo_bono"].to_numpy() == "suba"]
    baja = x[panel["grupo_bono"].to_numpy() == "baja"]
    if _tamanios_ok(suba, baja, minimo=3):
        complementaria = prueba_complementaria(suba, baja, alfa, cfg["prueba_complementaria"]["potencia"])
        complementaria["aplicable"] = True
        complementaria["normalidad"] = {"suba": normalidad(suba, **bondad_kw)["shapiro"],
                                        "baja": normalidad(baja, **bondad_kw)["shapiro"]}
        complementaria["autocorrelacion_var_pbi"] = autocorrelaciones["var_pbi"]
    else:
        complementaria = {"aplicable": False, "motivo": "Algún grupo tiene menos de 3 observaciones."}
    complementaria["sin_cambio"] = int((panel["grupo_bono"] == "sin cambio").sum())

    mensual = frecuencia == "mensual"
    ic_p = (principal["ic_b1"]["inferior"], principal["ic_b1"]["superior"])
    ic_e = (extension["ic_b1"]["inferior"], extension["ic_b1"]["superior"])
    veredictos = {
        "hipotesis_principal": V.veredicto_principal(
            principal["b1"], ic_p, principal["p_b1"], principal["r2"], alfa,
            "la variación mensual del PBI mensualizado" if mensual
            else "la variación trimestral del PBI desestacionalizado"),
        "interpretacion_pendiente": V.interpretacion_pendiente(principal["b1"], "mensual" if mensual else "trimestral"),
        "extension_d1": V.veredicto_extension(
            extension["b1"], ic_e, extension["p_b1"], extension["r2"], alfa,
            "la variación del PBI mensualizado del mes siguiente" if mensual
            else "la variación del PBI del trimestre siguiente"),
        "principal_rechaza_h0": principal["p_b1"] < alfa,
        "extension_rechaza_h0": extension["p_b1"] < alfa,
    }
    if complementaria["aplicable"]:
        dec = complementaria["decision"]
        veredictos["prueba_complementaria"] = V.veredicto_complementaria(
            dec["diferencia"], (dec["ic"]["inferior"], dec["ic"]["superior"]), dec["p_valor"], alfa)
        veredictos["complementaria_rechaza_h0"] = dec["p_valor"] < alfa

    resultados = {
        "frecuencia": frecuencia, "n": n, "periodo_inicio": str(panel.index[0]), "periodo_fin": str(panel.index[-1]),
        "estimadores": estimadores, "autocorrelaciones": autocorrelaciones, "intervalos": intervalos,
        "bondad_ajuste": bondad,
        "hipotesis_principal": {"d0": principal, "d1": extension},
        "desfases": desfases,
        "regresion_multiple": {**multiple, "hac": hac},
        "anova": anova, "anova_umbral": anova_umbral,
        "prueba_complementaria": complementaria,
        "diagnosticos": {"regresion_simple": diag_simple, "regresion_multiple": diag_multiple},
        "veredictos": veredictos,
    }
    extras = {"panel": panel, "principal": principal, "multiple": multiple, "regresiones": regresiones,
              "suba": suba, "baja": baja}
    return resultados, extras


# --- Robustez y sensibilidades ------------------------------------------------------------------

def _fila_reg(especificacion: str, reg: dict, alfa: float, herramienta: str = "Regresión simple (t de β1)") -> dict:
    return {"especificacion": especificacion, "herramienta": herramienta, "n": reg["n"],
            "nombre_estadistico": "t", "estadistico": reg["t_b1"], "gl": reg["gl"], "coeficiente": reg["b1"],
            "ic_inferior": reg["ic_b1"]["inferior"], "ic_superior": reg["ic_b1"]["superior"],
            "p_valor": reg["p_b1"], "decision": V.decision(reg["p_b1"], alfa)}


def tabla_robustez(res_p: dict, res_r: dict, alfa: float) -> list[dict]:
    """Mismos contrastes en la muestra principal y en la de respaldo."""
    filas = []
    for clave, titulo in (("d0", "Hipótesis principal: β1 (d = 0)"), ("d1", "Extensión: β1 (d = +1)")):
        for res in (res_p, res_r):
            reg = res["hipotesis_principal"][clave]
            fila = _fila_reg(titulo, reg, alfa)
            fila.update({"muestra": res["frecuencia"], "r2": reg["r2"]})
            filas.append(fila)
    for res in (res_p, res_r):
        coef = res["regresion_multiple"]["coeficientes"][1]
        filas.append({"especificacion": "Múltiple: β de Var PBI", "herramienta": "Regresión múltiple (t)",
                      "muestra": res["frecuencia"], "n": res["regresion_multiple"]["n"], "nombre_estadistico": "t",
                      "estadistico": coef["t"], "gl": res["regresion_multiple"]["gl"],
                      "coeficiente": coef["coeficiente"], "ic_inferior": coef["ic"]["inferior"],
                      "ic_superior": coef["ic"]["superior"], "p_valor": coef["p_valor"],
                      "r2": res["regresion_multiple"]["r2"], "decision": V.decision(coef["p_valor"], alfa)})
    for res in (res_p, res_r):
        an = res["anova"]
        if an["aplicable"]:
            filas.append({"especificacion": "ANOVA por terciles del PBI", "herramienta": "ANOVA (F)",
                          "muestra": res["frecuencia"], "n": an["N"], "nombre_estadistico": "F",
                          "estadistico": an["f"], "gl": f"{an['gl_entre']}; {an['gl_dentro']}",
                          "coeficiente": None, "ic_inferior": None, "ic_superior": None, "p_valor": an["p_valor"],
                          "r2": an["eta2"], "decision": V.decision(an["p_valor"], alfa)})
    for res in (res_p, res_r):
        comp = res["prueba_complementaria"]
        if comp["aplicable"]:
            dec = comp["decision"]
            filas.append({"especificacion": "Complementaria: μ suba − μ baja (Var PBI)",
                          "herramienta": f"t ({dec['tipo']})", "muestra": res["frecuencia"],
                          "n": comp["grupo_1"]["n"] + comp["grupo_2"]["n"], "nombre_estadistico": "t",
                          "estadistico": dec["estadistico"], "gl": dec["gl"], "coeficiente": dec["diferencia"],
                          "ic_inferior": dec["ic"]["inferior"], "ic_superior": dec["ic"]["superior"],
                          "p_valor": dec["p_valor"], "r2": None, "decision": V.decision(dec["p_valor"], alfa)})
    return filas


def sensibilidades(base: T.DatosBase, cfg: Config, panel: pd.DataFrame, res_p: dict, res_r: dict,
                   frecuencia: str) -> list[dict]:
    alfa = cfg.alfa
    filas = []
    principal = res_p["hipotesis_principal"]["d0"]
    filas.append({"id": "base", **_fila_reg("Especificación principal (referencia)", principal, alfa)})

    bruto = regresion_simple(panel["var_pbi"], panel["var_bono_bruto"], cfg.confianza)
    filas.append({"id": "a", **_fila_reg("(a) Bono sin ajuste ex-pago (serie bruta)", bruto, alfa)})

    panel_sin_sa = T.construir_panel(base, con_cambios(cfg, {"pbi": {"desestacionalizar": "ninguna"}}), frecuencia)
    sin_sa = regresion_simple(panel_sin_sa["var_pbi"], panel_sin_sa["var_bono"], cfg.confianza)
    filas.append({"id": "b", **_fila_reg("(b) PBI sin desestacionalizar", sin_sa, alfa)})

    an = res_p["anova_umbral"]
    if an["aplicable"]:
        tamanios = "/".join(str(g["n"]) for g in an["grupos"])
        aviso = f" — grupos con n < {cfg['anova']['n_minimo_grupo']}" if an["grupos_chicos"] else ""
        filas.append({"id": "c", "especificacion": f"(c) ANOVA con umbrales ±0,5 % (n por grupo {tamanios}){aviso}",
                      "herramienta": "ANOVA (F)", "n": an["N"], "nombre_estadistico": "F", "estadistico": an["f"],
                      "gl": f"{an['gl_entre']}; {an['gl_dentro']}", "coeficiente": None, "ic_inferior": None,
                      "ic_superior": None, "p_valor": an["p_valor"], "decision": V.decision(an["p_valor"], alfa)})
    else:
        filas.append({"id": "c", "especificacion": "(c) ANOVA con umbrales ±0,5 %: no aplicable (" + an["motivo"] + ")",
                      "herramienta": "ANOVA (F)", "n": None, "p_valor": None, "decision": "No aplicable"})

    if frecuencia == "mensual":
        panel_nak = T.construir_panel(base, con_cambios(cfg, {"pbi": {"spline_bc": "not-a-knot"}}), frecuencia)
        nak = regresion_simple(panel_nak["var_pbi"], panel_nak["var_bono"], cfg.confianza)
        filas.append({"id": "d", **_fila_reg("(d) Spline con condición de borde not-a-knot", nak, alfa)})

    otra = res_r["hipotesis_principal"]["d0"]
    filas.append({"id": "e", **_fila_reg(f"(e) Muestra {res_r['frecuencia']} (n = {otra['n']})", otra, alfa)})

    hac_pbi = res_p["regresion_multiple"]["hac"]["coeficientes"][1]
    filas.append({"id": "f", "especificacion": f"(f) Múltiple con errores HAC (Newey-West, {cfg['regresion_multiple']['hac_maxlags']} rezagos): β de Var PBI",
                  "herramienta": "Regresión múltiple (t HAC)", "n": res_p["regresion_multiple"]["n"],
                  "nombre_estadistico": "t", "estadistico": hac_pbi["t"], "gl": res_p["regresion_multiple"]["hac"]["gl"],
                  "coeficiente": hac_pbi["coeficiente"], "ic_inferior": hac_pbi["ic"]["inferior"],
                  "ic_superior": hac_pbi["ic"]["superior"], "p_valor": hac_pbi["p_valor"],
                  "decision": V.decision(hac_pbi["p_valor"], alfa)})

    if cfg["regresion_multiple"].get("sensibilidad_ccl_operado") and "var_ccl_operado" in panel:
        filas_ok = panel["var_ccl_operado"].notna().to_numpy()
        reg = regresion_multiple(panel.loc[filas_ok, ["var_pbi", "var_ccl_operado"]].to_numpy(float),
                                 panel.loc[filas_ok, "var_bono"].to_numpy(float), ["var_pbi", "var_ccl_operado"],
                                 cfg.confianza)
        for idx, nombre in ((1, "Var PBI"), (2, "Var CCL")):
            coef = reg["coeficientes"][idx]
            filas.append({"id": f"g{idx}", "especificacion": f"(g) Múltiple con CCL de cierres operados (AL30C con volumen > 0): β de {nombre}",
                          "herramienta": "Regresión múltiple (t)", "n": reg["n"], "nombre_estadistico": "t",
                          "estadistico": coef["t"], "gl": reg["gl"], "coeficiente": coef["coeficiente"],
                          "ic_inferior": coef["ic"]["inferior"], "ic_superior": coef["ic"]["superior"],
                          "p_valor": coef["p_valor"], "decision": V.decision(coef["p_valor"], alfa)})

    if base.pbi_desest_indec is not None:
        panel_indec = T.construir_panel(base, con_cambios(cfg, {"pbi": {"desestacionalizar": "indec"}}), frecuencia)
        indec = regresion_simple(panel_indec["var_pbi"], panel_indec["var_bono"], cfg.confianza)
        filas.append({"id": "h", **_fila_reg("(h) PBI desestacionalizado por el INDEC (en lugar de STL)", indec, alfa)})

    referencia = filas[0]["decision"]
    for fila in filas:
        if fila["herramienta"].startswith("Regresión simple") and fila["id"] != "base":
            fila["coincide_con_principal"] = fila["decision"] == referencia
    return filas


def influencia(panel: pd.DataFrame, cfg: Config, frecuencia: str) -> dict:
    """Diagnóstico posterior (no pre-registrado) de la regresión simple con d = 0: distancia de Cook y
    leave-one-out. Responde si el veredicto depende de un solo período."""
    x, y = panel["var_pbi"].to_numpy(float), panel["var_bono"].to_numpy(float)
    completa = regresion_simple(x, y, cfg.confianza)
    # Palanca h_ii = 1/n + (x_i − x̄)²/Sxx; Cook D_i = e_i² / (p·s²) · h_ii / (1 − h_ii)², con p = 2 parámetros.
    h = 1 / len(x) + (x - x.mean()) ** 2 / completa["sxx"]
    cook = completa["_residuos"] ** 2 / (2 * completa["s2"]) * h / (1 - h) ** 2
    decision = V.decision(completa["p_b1"], cfg.alfa)
    filas = []
    for i, periodo in enumerate(panel.index):
        sin = regresion_simple(np.delete(x, i), np.delete(y, i), cfg.confianza)
        filas.append({"periodo": str(periodo), "var_bono": y[i], "var_pbi": x[i], "palanca": h[i], "cook": cook[i],
                      "b1_sin": sin["b1"], "p_sin": sin["p_b1"], "decision_sin": V.decision(sin["p_b1"], cfg.alfa)})
    return {
        "frecuencia": frecuencia, "n": len(x), "b1": completa["b1"], "p_b1": completa["p_b1"], "decision": decision,
        "umbral_cook": 4 / len(x), "filas": filas,
        "periodos_que_cambian_decision": [f["periodo"] for f in filas if f["decision_sin"] != decision],
        "p_sin_min": min(f["p_sin"] for f in filas), "p_sin_max": max(f["p_sin"] for f in filas),
        "signos": {"pbi_baja": int((x < 0).sum()), "pbi_baja_bono_sube": int(((x < 0) & (y > 0)).sum()),
                   "pbi_sube": int((x > 0).sum()), "pbi_sube_bono_sube": int(((x > 0) & (y > 0)).sum())},
    }


# --- Tabla de p-valores -------------------------------------------------------------------------

def _p(prueba: str, etiqueta: str, estadistico, gl, p: float, umbral: float) -> dict:
    return {"prueba": prueba, "etiqueta": etiqueta, "estadistico": estadistico, "gl": gl, "p_valor": p,
            "umbral": umbral, "decision": "Se rechaza H0" if p < umbral else "No se rechaza H0"}


def tabla_p_valores(res: dict, robustez: list[dict], sens: list[dict], cfg: Config) -> list[dict]:
    a = cfg.alfa
    filas = []
    for fila in res["desfases"]:
        filas.append(_p(f"Regresión simple, β1 con d = {V.num(fila['d'], 0, signo=True)}", fila["etiqueta"],
                        fila["t"], fila["gl"], fila["p_valor"], fila["umbral"]))
    p0 = res["hipotesis_principal"]["d0"]
    filas.append(_p("Regresión simple, F global (d = 0)", "herramienta", p0["f"], p0["gl_f"], p0["p_f"], a))
    nombres = {"var_bono": "Var AL30D", "var_pbi": "Var PBI", "residuos_principal": "residuos de la regresión principal"}
    for clave, nombre in nombres.items():
        b = res["bondad_ajuste"][clave]
        if b["chi2"]["aplicable"]:
            filas.append(_p(f"Bondad de ajuste χ² a la Normal: {nombre}", "herramienta", b["chi2"]["estadistico"],
                            b["chi2"]["gl"], b["chi2"]["p_valor"], a))
        filas.append(_p(f"Shapiro-Wilk: {nombre}", "herramienta", b["shapiro"]["estadistico"], None,
                        b["shapiro"]["p_valor"], a))
    m = res["regresion_multiple"]
    filas.append(_p("Regresión múltiple, F global", "herramienta", m["f"], m["gl_f"], m["p_f"], a))
    for coef in m["coeficientes"]:
        filas.append(_p(f"Regresión múltiple, t de {NOMBRES.get(coef['nombre'], coef['nombre'])}", "herramienta",
                        coef["t"], m["gl"], coef["p_valor"], a))
    for modelo, titulo in (("regresion_simple", "simple"), ("regresion_multiple", "múltiple")):
        d = res["diagnosticos"][modelo]
        filas.append(_p(f"Breusch-Pagan (regresión {titulo})", "diagnóstico", d["breusch_pagan"]["estadistico"],
                        d["breusch_pagan"]["gl"], d["breusch_pagan"]["p_valor"], a))
        filas.append(_p(f"Breusch-Godfrey (regresión {titulo})", "diagnóstico", d["breusch_godfrey"]["estadistico"],
                        d["breusch_godfrey"]["gl"], d["breusch_godfrey"]["p_valor"], a))
        sw = d["normalidad_residuos"]["shapiro"]
        filas.append(_p(f"Shapiro-Wilk de residuos (regresión {titulo})", "diagnóstico", sw["estadistico"], None,
                        sw["p_valor"], a))
    an = res["anova"]
    if an["aplicable"]:
        filas.append(_p("ANOVA de un factor (terciles del PBI)", "herramienta", an["f"],
                        [an["gl_entre"], an["gl_dentro"]], an["p_valor"], a))
        lev = an["supuestos"]["levene"]
        filas.append(_p("Levene (ANOVA)", "diagnóstico", lev["estadistico"], lev["gl"], lev["p_valor"], a))
        for g in an["supuestos"]["shapiro_por_grupo"]:
            filas.append(_p(f"Shapiro-Wilk grupo {g['grupo']} (ANOVA)", "diagnóstico", g["estadistico"], None,
                            g["p_valor"], a))
        for par in an["tukey"] or []:
            filas.append(_p(f"Tukey HSD {par['par']}", "herramienta", par["diferencia"], None, par["p_valor"], a))
    comp = res["prueba_complementaria"]
    if comp["aplicable"]:
        f = comp["prueba_f"]
        filas.append(_p("F de igualdad de varianzas (complementaria)", "complementaria", f["estadistico"], f["gl"],
                        f["p_valor"], a))
        for clave in ("t_agrupada", "t_welch"):
            t = comp[clave]
            usada = " — decisión" if t["tipo"] == comp["test_de_decision"] else ""
            filas.append(_p(f"t {t['tipo']} (complementaria){usada}", "complementaria", t["estadistico"], t["gl"],
                            t["p_valor"], a))
    for fila in robustez:
        if fila["muestra"] != res["frecuencia"]:
            filas.append(_p(f"{fila['especificacion']} — muestra {fila['muestra']}", "robustez", fila["estadistico"],
                            fila["gl"], fila["p_valor"], a))
    for fila in sens:
        if fila["id"] in ("base", "e") or fila.get("p_valor") is None:
            continue
        filas.append(_p(fila["especificacion"], "sensibilidad", fila["estadistico"], fila["gl"], fila["p_valor"], a))
    return filas


# --- Reconciliación con el borrador previo ------------------------------------------------------

def chequeos_borrador(base: T.DatosBase, cfg: Config) -> dict:
    """Datos de Data912 para contrastar la discrepancia conocida del borrador (abr–jun 2024)."""
    mensual = T.resumen_bono(base.bono, base.retornos, "M", cfg["bono"]["dias_ex_pago"])
    tramo = mensual.loc["2021-10":"2024-06", "var_bono_bruto"]
    return {
        "var_bruta_2024": {str(p): float(v) for p, v in mensual.loc["2024-04":"2024-06", "var_bono_bruto"].items()},
        "media_oct2021_jun2024": float(tramo.mean()), "desvio_oct2021_jun2024": float(tramo.std(ddof=1)),
        "n_oct2021_jun2024": int(tramo.size), "primera_cotizacion": base.bono.index[0].strftime("%Y-%m-%d"),
    }


# --- Orquestación -------------------------------------------------------------------------------

def _a_json(obj):
    """Quita claves privadas (prefijo _), convierte tipos numpy y redondea a 12 cifras significativas."""
    if isinstance(obj, dict):
        return {str(k): _a_json(v) for k, v in obj.items() if not str(k).startswith("_")}
    if isinstance(obj, (list, tuple)):
        return [_a_json(v) for v in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        valor = float(obj)
        if np.isnan(valor):
            return None
        if np.isinf(valor):
            return "inf" if valor > 0 else "-inf"
        return float(f"{valor:.12g}")
    if isinstance(obj, np.ndarray):
        return _a_json(obj.tolist())
    return obj


def ejecutar(cfg: Config, linaje: list[dict] | None = None) -> tuple[dict, dict]:
    log.info("Fase 1 · datos: lectura, ajuste ex-pago, desestacionalización y spline")
    base = T.cargar_base(cfg)
    panel_m = T.construir_panel(base, cfg, "mensual")
    panel_t = T.construir_panel(base, cfg, "trimestral")
    frec_p, frec_r = ("mensual", "trimestral") if cfg.principal_mensual else ("trimestral", "mensual")
    panel_p, panel_r = (panel_m, panel_t) if cfg.principal_mensual else (panel_t, panel_m)
    n_min = cfg["n_minimo"]
    if cfg.principal_mensual and len(panel_p) < n_min:
        raise ValueError(f"La muestra principal mensual tiene n = {len(panel_p)} < {n_min}: no cumple la consigna.")
    log.info("Muestra principal %s: n = %d (%s a %s)", frec_p, len(panel_p), panel_p.index[0], panel_p.index[-1])

    log.info("Fase 2 · herramientas sobre la muestra principal y la de respaldo")
    res_p, ext_p = bateria(panel_p, cfg, frec_p)
    res_r, ext_r = bateria(panel_r, cfg, frec_r)
    robustez = tabla_robustez(res_p, res_r, cfg.alfa)
    sens = sensibilidades(base, cfg, panel_p, res_p, res_r, frec_p)
    p_valores = tabla_p_valores(res_p, robustez, sens, cfg)

    pbi = T.desestacionalizar(base.pbi, "stl", cfg["pbi"]["stl_periodo"], cfg["pbi"]["stl_robusto"])
    factores = pbi.groupby(pbi.index.quarter)["factor_estacional"].mean()
    pbi_cfg = T.desestacionalizar(base.pbi, cfg["pbi"]["desestacionalizar"], cfg["pbi"]["stl_periodo"],
                                  cfg["pbi"]["stl_robusto"])
    pbi_spline = T.mensualizar_spline(pbi_cfg["nivel"], cfg["pbi"]["spline_bc"],
                                      cfg["pbi"]["desplazamiento_mes_central"])
    caidas = base.retornos.loc[pd.to_datetime(cfg["bono"]["dias_ex_pago"]), "bruto"]

    resultados = {
        "meta": {
            "titulo": cfg["proyecto"]["titulo"], "materia": cfg["proyecto"]["materia"],
            "catedra": cfg["proyecto"]["catedra"], "facultad": cfg["proyecto"]["facultad"],
            "cuatrimestre": cfg["proyecto"]["cuatrimestre"], "grupo": cfg["proyecto"].get("grupo"),
            "integrantes": cfg["proyecto"].get("integrantes", [cfg["proyecto"]["autor"]]),
            "repositorio": cfg["proyecto"]["repositorio"], "alfa": cfg.alfa, "confianza": cfg.confianza,
            "muestra_principal": cfg["muestra_principal"], "decisiones_pre_registradas": "config.yaml",
            "versiones": {"python": platform.python_version(),
                          **{p: version(p) for p in ("numpy", "pandas", "scipy", "statsmodels")}},
        },
        "muestra": {
            "principal": {"frecuencia": frec_p, "n": len(panel_p), "inicio": str(panel_p.index[0]),
                          "fin": str(panel_p.index[-1]), "cumple_minimo_50": len(panel_p) >= n_min},
            "respaldo": {"frecuencia": frec_r, "n": len(panel_r), "inicio": str(panel_r.index[0]),
                         "fin": str(panel_r.index[-1]), "cumple_minimo_50": len(panel_r) >= n_min},
            "n_minimo_consigna": n_min,
        },
        "datos": {
            "linaje": linaje or [], "huecos_bono": base.huecos.to_dict(orient="records"),
            "ruedas_al30d": len(base.bono), "ccl": base.ccl_info, "control_multiple": res_p["regresion_multiple"]["modo"],
            "ex_pago": [{"fecha": f.strftime("%Y-%m-%d"), "log_retorno": float(r), "variacion_pct": float(np.expm1(r) * 100)}
                        for f, r in caidas.items()],
            "factores_estacionales_stl": {f"T{q}": float(v) for q, v in factores.items()},
            "factores_estacionales_indec": (
                {f"T{q}": float(v) for q, v in
                 (base.pbi / base.pbi_desest_indec).groupby(base.pbi.index.quarter).mean().items()}
                if base.pbi_desest_indec is not None else None),
            "autocorrelacion_var_pbi_mensual": T.autocorrelacion(panel_m["var_pbi"]),
            "autocorrelacion_var_pbi_trimestral": T.autocorrelacion(panel_t["var_pbi"]),
            "trimestres_pbi_en_ventana": int(len(base.pbi.loc["2021Q3":"2026Q2"])),
        },
        "estimadores": res_p["estimadores"], "autocorrelaciones": res_p["autocorrelaciones"],
        "intervalos": res_p["intervalos"], "bondad_ajuste": res_p["bondad_ajuste"],
        "hipotesis_principal": res_p["hipotesis_principal"], "desfases": res_p["desfases"],
        "regresion_multiple": res_p["regresion_multiple"], "anova": res_p["anova"],
        "anova_umbral": res_p["anova_umbral"], "prueba_complementaria": res_p["prueba_complementaria"],
        "diagnosticos": res_p["diagnosticos"],
        "robustez_trimestral": {"muestra_comparada": frec_r, "tabla": robustez, "bateria_respaldo": res_r,
                                "influencia": influencia(panel_r, cfg, frec_r)},
        "sensibilidades": sens, "p_valores": p_valores, "veredictos": res_p["veredictos"],
    }
    extras = {"base": base, "pbi_stl": pbi_cfg, "pbi_spline": pbi_spline, "panel_mensual": panel_m,
              "panel_trimestral": panel_t,
              "principal": ext_p, "respaldo": ext_r, "borrador": chequeos_borrador(base, cfg)}
    return _a_json(resultados), extras
