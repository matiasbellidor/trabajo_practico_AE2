"""Salidas: tablas CSV/XLSX, resultados.json, linaje, informe, resumen, reconciliación y bloque del README."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import jinja2
import numpy as np
import pandas as pd

from . import textos
from .veredicto import decision, ic_texto, num, pval

log = logging.getLogger(__name__)

PLANTILLAS = Path(__file__).parent / "plantillas"
MARCA_INICIO, MARCA_FIN = "<!-- RESULTADOS:INICIO -->", "<!-- RESULTADOS:FIN -->"
MARCA_RESUMEN_INICIO, MARCA_RESUMEN_FIN = "<!-- RESUMEN:INICIO -->", "<!-- RESUMEN:FIN -->"

# Números del borrador previo del grupo (origen no verificado): solo para la reconciliación.
BORRADOR = [
    ("Muestra", "n = 53, 2020-02 a 2024-06", "muestra"),
    ("Media Var PBI (%)", 0.0146, ("estimadores", "var_pbi", "media")),
    ("Media Var bono (%)", -1.5819, ("estimadores", "var_bono", "media")),
    ("Media Var CCL (%)", 3.4405, ("estimadores", "var_ccl", "media")),
    ("S² Var PBI", 5.2839, ("estimadores", "var_pbi", "varianza")),
    ("S² Var bono", 25.2380, ("estimadores", "var_bono", "varianza")),
    ("IC 95 % μ PBI (inferior)", -0.6190, ("intervalos", "media_var_pbi", "inferior")),
    ("IC 95 % μ PBI (superior)", 0.6482, ("intervalos", "media_var_pbi", "superior")),
    ("Shapiro bono: W", 0.9773, ("bondad_ajuste", "var_bono", "shapiro", "estadistico")),
    ("Shapiro bono: p", 0.4074, ("bondad_ajuste", "var_bono", "shapiro", "p_valor")),
    ("Regresión simple: β1", 1.0991, ("hipotesis_principal", "d0", "b1")),
    ("Regresión simple: β0", -1.5980, ("hipotesis_principal", "d0", "b0")),
    ("Regresión simple: R²", 0.253, ("hipotesis_principal", "d0", "r2")),
    ("Regresión simple: t", 4.155, ("hipotesis_principal", "d0", "t_b1")),
    ("Regresión simple: p", 0.000124, ("hipotesis_principal", "d0", "p_b1")),
    ("Múltiple: R²", 0.319, ("regresion_multiple", "r2")),
    ("Múltiple: F", 11.69, ("regresion_multiple", "f")),
    ("Múltiple: p (F)", 0.0000683, ("regresion_multiple", "p_f")),
    ("ANOVA: F", 4.6716, ("anova", "f")),
    ("ANOVA: p", 0.0138, ("anova", "p_valor")),
]


def _entorno() -> jinja2.Environment:
    entorno = jinja2.Environment(loader=jinja2.FileSystemLoader(PLANTILLAS), undefined=jinja2.StrictUndefined,
                                 keep_trailing_newline=True, trim_blocks=False)
    entorno.globals.update(n=num, pv=pval, ic=ic_texto, nombres=textos.NOMBRES)
    return entorno


def escribir_texto(ruta: Path, contenido: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8", newline="\n")


def escribir_json(ruta: Path, objeto) -> None:
    escribir_texto(ruta, json.dumps(objeto, ensure_ascii=False, indent=2) + "\n")


# --- Tablas -------------------------------------------------------------------------------------

def construir_tablas(r: dict, extras: dict) -> dict[str, pd.DataFrame]:
    p0 = extras["principal"]["principal"]
    panel = extras["principal"]["panel"]
    x, y = panel["var_pbi"].to_numpy(), panel["var_bono"].to_numpy()
    cuadro = pd.DataFrame({"periodo": panel.index.astype(str), "x_var_pbi": x, "y_var_al30d": y, "x2": x ** 2,
                           "y2": y ** 2, "xy": x * y, "y_ajustada": p0["_ajustados"], "residuo": p0["_residuos"],
                           "residuo2": p0["_residuos"] ** 2})
    total = cuadro.drop(columns="periodo").sum().to_frame().T
    total.insert(0, "periodo", "TOTAL")
    cuadro = pd.concat([cuadro, total], ignore_index=True)

    estimadores = pd.DataFrame([{"variable": k, **v} for k, v in r["estimadores"].items() if k != "proporcion_suba"])
    intervalos = pd.DataFrame([{"parametro_clave": k, **{c: v[c] for c in ("estimacion", "error_estandar", "cuantil",
                                                                             "inferior", "superior", "confianza")}}
                               for k, v in r["intervalos"].items()])
    clases, resumen_bondad = [], []
    for clave, b in r["bondad_ajuste"].items():
        if b["chi2"]["aplicable"]:
            clases += [{"variable": clave, **c} for c in b["chi2"]["tabla"]]
        resumen_bondad.append({"variable": clave, "chi2": b["chi2"].get("estadistico"), "gl": b["chi2"]["gl"],
                               "p_chi2": b["chi2"].get("p_valor"), "shapiro_w": b["shapiro"]["estadistico"],
                               "p_shapiro": b["shapiro"]["p_valor"], "coinciden": b["coinciden"]})
    simple = pd.DataFrame([{"coeficiente": nombre, "estimacion": p[f"b{i}"], "error_estandar": p[f"ee_b{i}"],
                            "t": p[f"t_b{i}"], "p_valor": p[f"p_b{i}"], "ic_inferior": p[f"ic_b{i}"]["inferior"],
                            "ic_superior": p[f"ic_b{i}"]["superior"], "r2": p["r2"], "f": p["f"], "p_f": p["p_f"],
                            "n": p["n"], "desfase": clave}
                           for clave, p in r["hipotesis_principal"].items() for i, nombre in ((0, "b0"), (1, "b1"))])
    desfases = pd.DataFrame([{**{k: v for k, v in f.items() if k != "ic_b1"}, "ic_inferior": f["ic_b1"]["inferior"],
                              "ic_superior": f["ic_b1"]["superior"]} for f in r["desfases"]])
    m = r["regresion_multiple"]
    multiple = pd.DataFrame([{"coeficiente": c["nombre"], "estimacion": c["coeficiente"],
                              "error_estandar": c["error_estandar"], "t": c["t"], "p_valor": c["p_valor"],
                              "ic_inferior": c["ic"]["inferior"], "ic_superior": c["ic"]["superior"],
                              "p_valor_hac": h["p_valor"], "error_estandar_hac": h["error_estandar"]}
                             for c, h in zip(m["coeficientes"], m["hac"]["coeficientes"])])
    supuestos = []
    for modelo, d in r["diagnosticos"].items():
        supuestos.append({"modelo": modelo, "prueba": "Durbin-Watson", "estadistico": d["durbin_watson"],
                          "gl": None, "p_valor": None})
        for clave, nombre in (("breusch_pagan", "Breusch-Pagan"), ("breusch_godfrey", "Breusch-Godfrey")):
            supuestos.append({"modelo": modelo, "prueba": nombre, "estadistico": d[clave]["estadistico"],
                              "gl": d[clave]["gl"], "p_valor": d[clave]["p_valor"]})
        sw = d["normalidad_residuos"]["shapiro"]
        supuestos.append({"modelo": modelo, "prueba": "Shapiro-Wilk residuos", "estadistico": sw["estadistico"],
                          "gl": None, "p_valor": sw["p_valor"]})
        for v in d.get("vif", []):
            supuestos.append({"modelo": modelo, "prueba": f"VIF {v['variable']}", "estadistico": v["vif"],
                              "gl": None, "p_valor": None})
    tablas = {"cuadro_a_mano": cuadro, "estimadores": estimadores, "intervalos": intervalos,
              "bondad_ajuste_clases": pd.DataFrame(clases), "bondad_ajuste_resumen": pd.DataFrame(resumen_bondad),
              "regresion_simple": simple, "desfases": desfases, "regresion_multiple": multiple,
              "supuestos": pd.DataFrame(supuestos)}
    an = r["anova"]
    if an["aplicable"]:
        tablas["anova"] = pd.DataFrame([
            {"fuente": "entre", "sc": an["sc_entre"], "gl": an["gl_entre"], "cm": an["cm_entre"], "f": an["f"],
             "p_valor": an["p_valor"]},
            {"fuente": "dentro", "sc": an["sc_dentro"], "gl": an["gl_dentro"], "cm": an["cm_dentro"], "f": None,
             "p_valor": None},
            {"fuente": "total", "sc": an["sc_total"], "gl": an["gl_total"], "cm": None, "f": None, "p_valor": None}])
        tablas["anova_grupos"] = pd.DataFrame([{"grupo": g["grupo"], "n": g["n"], "media": g["media"], "desvio": g["desvio"],
                                                "ic_inferior": g["ic"]["inferior"], "ic_superior": g["ic"]["superior"]}
                                               for g in an["grupos"]])
        if an["tukey"]:
            tablas["tukey"] = pd.DataFrame([{"par": t["par"], "diferencia": t["diferencia"], "p_valor": t["p_valor"],
                                             "ic_inferior": t["ic"]["inferior"], "ic_superior": t["ic"]["superior"]}
                                            for t in an["tukey"]])
    c = r["prueba_complementaria"]
    if c["aplicable"]:
        tablas["prueba_complementaria"] = pd.DataFrame([
            {"prueba": "F varianzas", "estadistico": c["prueba_f"]["estadistico"], "gl": str(c["prueba_f"]["gl"]),
             "p_valor": c["prueba_f"]["p_valor"], "diferencia": None, "ic_inferior": None, "ic_superior": None},
            *[{"prueba": f"t {c[k]['tipo']}", "estadistico": c[k]["estadistico"], "gl": c[k]["gl"],
               "p_valor": c[k]["p_valor"], "diferencia": c[k]["diferencia"], "ic_inferior": c[k]["ic"]["inferior"],
               "ic_superior": c[k]["ic"]["superior"]} for k in ("t_agrupada", "t_welch")]])
    tablas["robustez_trimestral"] = pd.DataFrame(r["robustez_trimestral"]["tabla"])
    tablas["influencia_respaldo"] = pd.DataFrame(r["robustez_trimestral"]["influencia"]["filas"])
    tablas["sensibilidades"] = pd.DataFrame(r["sensibilidades"])
    tablas["p_valores"] = pd.DataFrame(r["p_valores"]).assign(gl=lambda d: d["gl"].map(
        lambda g: "; ".join(map(str, g)) if isinstance(g, list) else g))
    pbi = extras["pbi_stl"]
    tablas["pbi_desestacionalizacion"] = pd.DataFrame({
        "trimestre": pbi.index.astype(str), "original": pbi["original"], "nivel_ajustado": pbi["nivel"],
        "factor_estacional": pbi["factor_estacional"]})
    tablas["ex_pago"] = pd.DataFrame(r["datos"]["ex_pago"])
    for clave, df in (("panel_mensual", extras["panel_mensual"]), ("panel_trimestral", extras["panel_trimestral"])):
        tablas[clave] = df.reset_index().assign(periodo=lambda d: d["periodo"].astype(str))
    return tablas


def escribir_tablas(tablas: dict[str, pd.DataFrame], dir_tablas: Path, ruta_xlsx: Path) -> None:
    dir_tablas.mkdir(parents=True, exist_ok=True)
    for nombre, df in tablas.items():
        df.to_csv(dir_tablas / f"{nombre}.csv", index=False, lineterminator="\n", float_format="%.10g",
                  encoding="utf-8")
    with pd.ExcelWriter(ruta_xlsx, engine="openpyxl") as libro:
        for nombre, df in tablas.items():
            df.to_excel(libro, sheet_name=nombre[:31], index=False)


# --- Textos -------------------------------------------------------------------------------------

def leer_conclusion(ruta: Path) -> str | None:
    """Texto de conclusion.md sin su título de primer nivel: cada salida pone el suyo."""
    if not ruta.exists():
        return None
    lineas = ruta.read_text(encoding="utf-8").strip().splitlines()
    if lineas and re.match(r"^#\s", lineas[0]):
        lineas = lineas[1:]
    return "\n".join(lineas).strip() + "\n"


def cuerpo_informe(r: dict, t: dict, conclusion: str | None = None) -> str:
    """Informe completo; sin conclusión, la sección 8 queda como marcador."""
    if conclusion:
        # Los subtítulos de la conclusión quedan un nivel por debajo de "## 8. Conclusión".
        conclusion = re.sub(r"^(#{2,5})(\s)", r"#\1\2", conclusion, flags=re.M)
    return _entorno().get_template("informe.md.j2").render(r=r, t=t, fig="../outputs/figuras/",
                                                            dec=lambda p: decision(p, r["meta"]["alfa"]),
                                                            conclusion=conclusion)


def resumen_para_conclusion(r: dict, t: dict, extras: dict) -> str:
    panel = extras["respaldo"]["panel"]
    filas = [{"periodo": str(p), "var_bono": float(b), "var_pbi": float(x)}
             for p, b, x in zip(panel.index, panel["var_bono"], panel["var_pbi"])]
    return _entorno().get_template("resumen.md.j2").render(r=r, t=t, panel_respaldo=filas,
                                                            tabla_p=textos.tabla_p_valores_md(r))


def _obtener(r: dict, ruta: tuple):
    valor = r
    for clave in ruta:
        if not isinstance(valor, dict) or clave not in valor:
            return None
        valor = valor[clave]
    return valor


def reconciliacion(r: dict, extras: dict) -> str:
    b = extras["borrador"]
    lineas = [
        "# Reconciliación con el borrador previo",
        "",
        "Los números del borrador anterior del grupo tienen origen no verificado. No se reutilizan: se listan junto a "
        "los recalculados para documentar por qué se descartaron.",
        "",
        "## Contra los datos de origen",
        "",
        f"- El AL30D empieza a cotizar el {b['primera_cotizacion']}: no hay precios en febrero de 2020, el inicio "
        "declarado en el borrador.",
        "- Variación del cierre mensual del AL30D en Data912 (serie bruta, sin días ex-pago en esos meses): "
        + "; ".join(f"{p}: {num(v, 2)} %" for p, v in b["var_bruta_2024"].items())
        + ". El borrador reporta −1,99 %, −0,89 % y +0,63 % para esos meses.",
        f"- Media mensual de oct-2021 a jun-2024: {num(b['media_oct2021_jun2024'], 2)} % con desvío "
        f"{num(b['desvio_oct2021_jun2024'], 1)} % (n = {b['n_oct2021_jun2024']}). El borrador reporta una media de −1,5819 % "
        "y un desvío de 5,0237 %.",
        "",
        "## Indicadores del borrador frente a la muestra principal recalculada",
        "",
        f"Muestra recalculada: {r['muestra']['principal']['frecuencia']}, {r['muestra']['principal']['inicio']} a "
        f"{r['muestra']['principal']['fin']}, n = {r['muestra']['principal']['n']}. Las ventanas no coinciden, así que "
        "la comparación es orientativa.",
        "",
        "| Indicador | Borrador | Recalculado |",
        "|---|---|---|",
    ]
    for nombre, valor, ruta in BORRADOR:
        if ruta == "muestra":
            recalculado = f"n = {r['muestra']['principal']['n']}, {r['muestra']['principal']['inicio']} a {r['muestra']['principal']['fin']}"
            lineas.append(f"| {nombre} | {valor} | {recalculado} |")
            continue
        actual = _obtener(r, ruta)
        es_p = nombre.endswith(": p") or nombre.endswith("p (F)")
        original = f"{valor:.7f}".rstrip("0").rstrip(".").replace(".", ",").replace("-", "−")
        recalculado = "—" if actual is None else (pval(actual) if es_p else num(actual))
        lineas.append(f"| {nombre} | {original} | {recalculado} |")
    lineas += ["", "Conclusión de la reconciliación: el borrador no es una referencia válida para este trabajo.", ""]
    return "\n".join(lineas)


def _valores_readme(r: dict) -> dict:
    """Cantidades derivadas que el README explica en palabras (todas salen de resultados.json)."""
    alfa = r["meta"]["alfa"]
    principal = r["muestra"]["principal"]
    d0 = r["hipotesis_principal"]["d0"]
    est = r["estimadores"]
    sx, sy = est["var_pbi"]["desvio"], est["var_bono"]["desvio"]
    extremo_ic = max(abs(d0["ic_b1"]["inferior"]), abs(d0["ic_b1"]["superior"]))
    ic_medias = r["intervalos"]
    resp = r["robustez_trimestral"]
    sens = [s for s in r["sensibilidades"] if s["id"] not in ("base", "e") and s.get("p_valor") is not None]
    q0 = resp["bateria_respaldo"]["hipotesis_principal"]["d0"]
    n_min = r["muestra"]["n_minimo_consigna"]
    cambian = resp["influencia"]["periodos_que_cambian_decision"]
    motivos = []  # por qué la muestra de respaldo no se toma como resultado
    if q0["n"] < n_min:
        motivos.append(f"son menos de las {n_min} observaciones que pide la consigna")
    if cambian:
        motivos.append(("depende de un solo período" if len(cambian) == 1 else "depende de pocos períodos")
                       + f" (sin {', '.join(cambian)}, la decisión se invierte)")
    return {
        "motivos_excepcion": motivos,
        "alfa": alfa,
        "mensual": principal["frecuencia"] == "mensual",
        "unidad": "meses" if principal["frecuencia"] == "mensual" else "trimestres",
        "principal": principal,
        "rechaza": d0["p_b1"] < alfa,
        "veces_mas_volatil": sy / sx,
        "extremo_por_desvio": extremo_ic * sx,
        "ic_bono_con_cero": ic_medias["media_var_bono"]["inferior"] <= 0 <= ic_medias["media_var_bono"]["superior"],
        "ic_pbi_con_cero": ic_medias["media_var_pbi"]["inferior"] <= 0 <= ic_medias["media_var_pbi"]["superior"],
        "ic_prop_con_mitad": ic_medias["proporcion_suba"]["inferior"] <= .5 <= ic_medias["proporcion_suba"]["superior"],
        "exploratorios_signif": [f for f in r["desfases"] if f["etiqueta"] == "exploratoria" and f["p_valor"] < f["umbral"]],
        "n_exploratorios": sum(1 for f in r["desfases"] if f["etiqueta"] == "exploratoria"),
        "respaldo": resp["bateria_respaldo"]["hipotesis_principal"]["d0"],
        "respaldo_frecuencia": resp["muestra_comparada"],
        "influencia": resp["influencia"],
        "sensibilidades": sens,
        "sensibilidades_cambian": [s for s in sens if s["decision"] != r["sensibilidades"][0]["decision"]],
    }


def bloque_resumen_readme(r: dict) -> str:
    texto = _entorno().get_template("readme_resumen.md.j2").render(r=r, v=_valores_readme(r)).strip()
    return "\n".join([MARCA_RESUMEN_INICIO, texto, MARCA_RESUMEN_FIN])


def bloque_readme(r: dict) -> str:
    p0, p1 = r["hipotesis_principal"]["d0"], r["hipotesis_principal"]["d1"]
    comp = r["prueba_complementaria"]
    resp = r["robustez_trimestral"]["bateria_respaldo"]["hipotesis_principal"]["d0"]
    explicacion = _entorno().get_template("readme_resultados.md.j2").render(r=r, v=_valores_readme(r)).strip()
    filas = [
        "| Contraste | Etiqueta | n | Estimación | p-valor | Decisión (α = 0,05) |",
        "|---|---|---|---|---|---|",
        f"| Regresión simple, β1 (d = 0) | principal | {p0['n']} | {num(p0['b1'])} | {pval(p0['p_b1'])} | {decision(p0['p_b1'], 0.05)} |",
        f"| Regresión simple, β1 (d = +1) | extensión | {p1['n']} | {num(p1['b1'])} | {pval(p1['p_b1'])} | {decision(p1['p_b1'], 0.05)} |",
    ]
    if comp["aplicable"]:
        dec = comp["decision"]
        filas.append(f"| Diferencia de medias del PBI (suba − baja) | complementaria | "
                     f"{comp['grupo_1']['n'] + comp['grupo_2']['n']} | {num(dec['diferencia'])} pp | "
                     f"{pval(dec['p_valor'])} | {decision(dec['p_valor'], 0.05)} |")
    an = r["anova"]
    if an["aplicable"]:
        filas.append(f"| ANOVA por terciles del PBI | herramienta | {an['N']} | F = {num(an['f'])} | {pval(an['p_valor'])} | "
                     f"{decision(an['p_valor'], 0.05)} |")
    filas.append(f"| Regresión simple, β1 (muestra {r['robustez_trimestral']['muestra_comparada']}) | robustez | "
                 f"{resp['n']} | {num(resp['b1'])} | {pval(resp['p_b1'])} | {decision(resp['p_b1'], 0.05)} |")
    return "\n".join([
        MARCA_INICIO,
        "<!-- Bloque generado por `python -m tp_ae2.run_all` desde outputs/resultados.json. No editar a mano: los "
        "números y las interpretaciones se recalculan. -->",
        "",
        explicacion,
        "",
        "## 7. Todos los contrastes principales en una tabla",
        "",
        f"Muestra principal: {r['muestra']['principal']['frecuencia']}, {r['muestra']['principal']['inicio']} a "
        f"{r['muestra']['principal']['fin']} (n = {r['muestra']['principal']['n']}). Los p-valores de todos los tests "
        "(diagnósticos y sensibilidades incluidos) están en el anexo de la presentación y en `outputs/tablas/p_valores.csv`.",
        "",
        *filas,
        "",
        MARCA_FIN,
    ])


def inyectar_readme(ruta: Path, bloque: str, marcas: tuple[str, str] = (MARCA_INICIO, MARCA_FIN)) -> None:
    contenido = ruta.read_text(encoding="utf-8")
    patron = re.compile(re.escape(marcas[0]) + r".*?" + re.escape(marcas[1]), re.S)
    if not patron.search(contenido):
        raise ValueError(f"{ruta}: faltan las marcas {marcas[0]} / {marcas[1]}")
    escribir_texto(ruta, patron.sub(lambda _: bloque, contenido))
