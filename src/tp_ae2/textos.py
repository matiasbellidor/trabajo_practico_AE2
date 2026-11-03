"""Textos de justificación e interpretación generados desde resultados.json (los usa la web, el informe y el resumen)."""

from __future__ import annotations

from .veredicto import gl_texto, ic_texto, num, p_texto, pval

NOMBRES = {"var_bono": "Var AL30D", "var_pbi": "Var PBI", "residuos_principal": "residuos de la regresión principal",
           "var_ccl": "Var CCL implícito", "var_pbi_d+1": "Var PBI (t + 1)", "constante": "constante"}


def _rechaza(p: float, alfa: float) -> str:
    return "se rechaza H0" if p < alfa else "no se rechaza H0"


def _contiene(inf: float, sup: float, valor: float = 0.0) -> bool:
    return inf <= valor <= sup


def _normalidad(clave: str, b: dict, alfa: float) -> str:
    sw = b["shapiro"]
    sw_txt = f"Shapiro-Wilk W = {num(sw['estadistico'])}, {p_texto(sw['p_valor'])} ({_rechaza(sw['p_valor'], alfa)})"
    if not b["chi2"]["aplicable"]:
        return f"{NOMBRES[clave]}: χ² no aplicable ({b['chi2']['motivo']}). {sw_txt}."
    c = b["chi2"]
    texto = (f"{NOMBRES[clave]}: χ² = {num(c['estadistico'])} con {c['gl']} gl, {p_texto(c['p_valor'])} "
             f"({_rechaza(c['p_valor'], alfa)}); {sw_txt}.")
    if b["coinciden"] is False:
        texto += (" Los dos tests discrepan: con pocas clases el χ² tiene poca potencia, así que el resultado de "
                  "Shapiro-Wilk es el más informativo sobre la forma de la distribución.")
    return texto


def construir(r: dict) -> dict:
    """Devuelve, por sección, el porqué de la herramienta y su interpretación (listas de párrafos)."""
    a = r["meta"]["alfa"]
    m = r["muestra"]["principal"]
    mensual = m["frecuencia"] == "mensual"
    unidad = "mensual" if mensual else "trimestral"
    e = r["estimadores"]
    ic = r["intervalos"]
    p0, p1 = r["hipotesis_principal"]["d0"], r["hipotesis_principal"]["d1"]
    resp = r["robustez_trimestral"]["bateria_respaldo"]
    q0 = resp["hipotesis_principal"]["d0"]
    s = {}

    s["pregunta"] = [
        f"¿La variación {unidad} del PBI real argentino se asocia con la variación {unidad} del precio del bono "
        "soberano AL30D? El trabajo contrasta esa asociación con una regresión lineal simple y la acompaña con las "
        "demás herramientas de la consigna.",
    ]
    s["bilateral"] = [
        "El contraste es bilateral porque no hay una dirección establecida antes de mirar los datos: un PBI más alto "
        "puede ir junto con bonos más firmes (mejor capacidad de pago) o con bonos más débiles (por ejemplo, si el "
        "crecimiento coincide con más inflación o más presión cambiaria). Un contraste unilateral habría fijado el "
        "signo de antemano sin fundamento suficiente.",
        "En una regresión simple el p-valor de β1 coincide con el del coeficiente de correlación r. Por eso invertir "
        "cuál variable es la explicada no cambia el p-valor: cambia la interpretación del modelo (pp de bono por pp "
        "de PBI, o al revés) y los supuestos que se exigen a los residuos.",
    ]

    ac = r["autocorrelaciones"]
    ratio = e["var_bono"]["desvio"] / e["var_pbi"]["desvio"]
    s["estimador"] = {
        "porque": ["x̄ y S² son estimadores insesgados de μ y σ² (E[x̄] = μ, E[S²] = σ²) y consistentes: su varianza "
                   "tiende a cero cuando n crece. Describen cada variable antes de relacionarlas y alimentan el resto "
                   "de los contrastes."],
        "interpretacion": [
            f"La variación {unidad} media del AL30D fue {num(e['var_bono']['media'])} % (S = {num(e['var_bono']['desvio'])} %) "
            f"y la del PBI, {num(e['var_pbi']['media'])} % (S = {num(e['var_pbi']['desvio'])} %): el bono es "
            f"{num(ratio, 1)} veces más volátil que el PBI.",
            f"El AL30D subió en {e['proporcion_suba']['exitos']} de {e['proporcion_suba']['n']} períodos "
            f"(p̂ = {num(e['proporcion_suba']['proporcion'])}, EE = {num(e['proporcion_suba']['error_estandar'])}).",
            f"Autocorrelación de orden 1: {num(ac['var_pbi'])} en la Var PBI y {num(ac['var_bono'])} en la Var AL30D."
            + (" La del PBI es alta por construcción: el spline reparte cada cambio trimestral en meses contiguos."
               if mensual else ""),
        ],
    }

    mb, mp, pr = ic["media_var_bono"], ic["media_var_pbi"], ic["proporcion_suba"]
    s["ic"] = {
        "porque": ["El intervalo acota cada parámetro con 95 % de confianza. Como σ es desconocida, la media usa la t de "
                   "Student con n − 1 gl; la proporción usa la aproximación Normal (Wald), válida con n·p̂ y n·(1 − p̂) "
                   "mayores a 5."],
        "interpretacion": [
            f"μ de la Var AL30D: {ic_texto(mb['inferior'], mb['superior'])} %. "
            + ("Contiene el 0: no se puede descartar una variación media nula del bono."
               if _contiene(mb["inferior"], mb["superior"]) else "No contiene el 0: la variación media del bono es distinta de cero."),
            f"μ de la Var PBI: {ic_texto(mp['inferior'], mp['superior'])} %. "
            + ("Contiene el 0." if _contiene(mp["inferior"], mp["superior"]) else "No contiene el 0: el PBI creció en promedio en la ventana."),
            f"Proporción de períodos de suba: {ic_texto(pr['inferior'], pr['superior'])}. "
            + ("Contiene 0,5: subas y bajas son compatibles con igual frecuencia."
               if _contiene(pr["inferior"], pr["superior"], 0.5) else "No contiene 0,5."),
            f"β1 (hipótesis principal): {ic_texto(p0['ic_b1']['inferior'], p0['ic_b1']['superior'])}. "
            + ("Contiene el 0, en línea con el veredicto." if _contiene(p0["ic_b1"]["inferior"], p0["ic_b1"]["superior"])
               else "No contiene el 0, en línea con el veredicto."),
        ],
    }

    s["bondad"] = {
        "porque": ["La inferencia de la regresión (t y F exactas) supone errores normales. El χ² compara las frecuencias "
                   "observadas con las esperadas bajo N(x̄, S) en k clases equiprobables (esperada ≥ 5, gl = k − 1 − 2 "
                   "porque se estiman μ y σ). Shapiro-Wilk se suma como complemento porque, con pocas clases, el χ² "
                   "pierde potencia."],
        "interpretacion": [_normalidad(k, r["bondad_ajuste"][k], a) for k in ("var_bono", "var_pbi", "residuos_principal")],
    }

    s["simple"] = {
        "porque": ["Es la herramienta que responde la pregunta: estima cuánto cambia en promedio la variación del bono por "
                   "cada punto porcentual de variación del PBI, y el estadístico t de β1 contrasta H0: β1 = 0 con n − 2 gl."],
        # El R² y el F se explican desde la tabla de sumas de cuadrados (s["sumas_cuadrados"]).
        "interpretacion": [
            r["veredictos"]["hipotesis_principal"],
            r["veredictos"]["interpretacion_pendiente"],
        ],
    }

    exploratorios = [f for f in r["desfases"] if f["etiqueta"] == "exploratoria"]
    signif = [f for f in exploratorios if f["significativo"]]
    texto_expl = (
        "Ningún desfase exploratorio tiene p < 0,01." if not signif else
        "Desfases exploratorios con p < 0,01: " + "; ".join(
            f"d = {num(f['d'], 0, signo=True)} (β1 = {num(f['b1'])}, {p_texto(f['p_valor'])})" for f in signif)
        + ". Al ser exploratorios no confirman nada por sí solos: señalan una relación a contrastar con datos nuevos, "
          "y comparten la limitación del spline (la Var PBI mensual de meses vecinos está muy correlacionada).")
    s["desfases"] = {
        "porque": ["Los docentes sugirieron mirar la dimensión temporal. Se define X = Var PBI en t + d. El desfase d = +1 "
                   "(el bono se mueve antes que el PBI) se declaró antes de ver resultados; d = −3, −2, −1, +2 y +3 son "
                   "exploratorios y se comparan con α/5 = 0,01 para controlar las comparaciones múltiples."],
        "interpretacion": [r["veredictos"]["extension_d1"], texto_expl],
    }

    mult = r["regresion_multiple"]
    dm = r["diagnosticos"]["regresion_multiple"]
    coefs = mult["coeficientes"]
    modo_ccl = mult["modo"] == "ccl"
    control = "la variación del CCL implícito (AL30 en pesos / AL30C en dólares cable)" if modo_ccl else \
        "la variación del PBI del período siguiente"
    vifs = ", ".join(f"{NOMBRES.get(v['variable'], v['variable'])} {num(v['vif'], 2)}" for v in dm["vif"])
    corr = dm["correlaciones"][0][1]
    hac = mult["hac"]["coeficientes"][1]
    s["multiple"] = {
        "porque": [f"Agrega un control, {control}, para ver si la asociación con el PBI cambia cuando esa variable se "
                   "mantiene constante. "
                   + ("El control requiere aprobación docente, porque la consigna habla de variables dadas. Además, el "
                      "AL30D y el CCL implícito salen del mismo instrumento: si el dólar sube y el precio en pesos no, el "
                      "precio en dólares baja, así que parte de la relación entre ambos es mecánica."
                      if modo_ccl else "Como el PBI de meses vecinos está muy correlacionado, se espera multicolinealidad.")],
        "interpretacion": [
            "Ŷ = " + " ".join(
                (f"{num(c['coeficiente'])}" if i == 0 else f"{'+' if c['coeficiente'] >= 0 else '−'} "
                 f"{num(abs(c['coeficiente']))}·{NOMBRES.get(c['nombre'], c['nombre'])}") for i, c in enumerate(coefs))
            + f". R² = {num(mult['r2'])}, R² ajustado = {num(mult['r2_ajustado'])}, S = {num(mult['s'])} pp; "
              f"F = {num(mult['f'])} con ({mult['gl_f'][0]}; {mult['gl_f'][1]}) gl, {p_texto(mult['p_f'])} "
              f"({_rechaza(mult['p_f'], a)}: {'el modelo en conjunto se asocia con Y' if mult['p_f'] < a else 'no hay evidencia de que el modelo en conjunto se asocie con Y'}).",
            "; ".join(f"t de {NOMBRES.get(c['nombre'], c['nombre'])} = {num(c['t'])}, {p_texto(c['p_valor'])}"
                      for c in coefs[1:]) + ".",
            f"Supuestos de Gauss-Markov. Linealidad: ver residuos vs. ajustados. Homocedasticidad: Breusch-Pagan "
            f"{p_texto(dm['breusch_pagan']['p_valor'])} ({_rechaza(dm['breusch_pagan']['p_valor'], a)}). No autocorrelación: "
            f"Durbin-Watson = {num(dm['durbin_watson'], 4)} y Breusch-Godfrey ({dm['breusch_godfrey']['gl']} rezagos) "
            f"{p_texto(dm['breusch_godfrey']['p_valor'])} ({_rechaza(dm['breusch_godfrey']['p_valor'], a)}). "
            f"No multicolinealidad: correlación entre regresores {num(corr)} y VIF {vifs} (valores mayores a 5 o 10 "
            f"serían preocupantes). Normalidad de residuos: Shapiro-Wilk {p_texto(dm['normalidad_residuos']['shapiro']['p_valor'])}.",
            f"Sensibilidad con errores HAC (Newey-West, {mult['hac']['maxlags']} rezagos): el β de la Var PBI tiene "
            f"{p_texto(hac['p_valor'])}, frente a {p_texto(coefs[1]['p_valor'])} con errores clásicos.",
        ],
    }

    an = r["anova"]
    s["anova"] = {"porque": [
        "Es la herramienta a elección del grupo. Compara la variación media del bono entre tres niveles de la variación "
        "del PBI (terciles: bajo, medio y alto) sin imponer una relación lineal. Los terciles se arman con X, no con Y, "
        "y dejan grupos balanceados."]}
    if an["aplicable"]:
        sup = an["supuestos"]
        shapiros = "; ".join(f"{g['grupo']} {p_texto(g['p_valor'])}" for g in sup["shapiro_por_grupo"])
        medias = "; ".join(f"{g['grupo']} {num(g['media'])} % (n = {g['n']})" for g in an["grupos"])
        tukey = ("" if not an["tukey"] else " Tukey HSD: " + "; ".join(
            f"{t['par']} = {num(t['diferencia'])} pp, {p_texto(t['p_valor'])}" for t in an["tukey"]) + ".")
        anu = r["anova_umbral"]
        sens = (f"Sensibilidad con umbrales fijos de ±0,5 %: F = {num(anu['f'])}, {p_texto(anu['p_valor'])} "
                f"(n por grupo {'/'.join(str(g['n']) for g in anu['grupos'])})."
                + (f" Grupos con menos de 8 observaciones: {', '.join(anu['grupos_chicos'])}." if anu["grupos_chicos"] else "")
                if anu["aplicable"] else f"Sensibilidad con umbrales ±0,5 %: no aplicable ({anu['motivo']}).")
        s["anova"]["interpretacion"] = [
            f"F = {num(an['f'])} con ({an['gl_entre']}; {an['gl_dentro']}) gl, {p_texto(an['p_valor'])}: "
            f"{_rechaza(an['p_valor'], a)}. "
            + ("Las medias del bono difieren entre niveles del PBI." if an["p_valor"] < a else
               "No hay evidencia de que la variación media del bono difiera entre los niveles del PBI.")
            + f" η² = {num(an['eta2'])}." + tukey,
            f"Medias por tercil: {medias}.",
            f"Supuestos: Levene {p_texto(sup['levene']['p_valor'])} ({_rechaza(sup['levene']['p_valor'], a)}: "
            f"{'varianzas distintas' if sup['levene']['p_valor'] < a else 'varianzas homogéneas'}); normalidad por grupo "
            f"(Shapiro-Wilk): {shapiros}. La independencia no se puede garantizar en una serie de tiempo: meses "
            "consecutivos comparten contexto macroeconómico.",
            sens,
        ]
    else:
        s["anova"]["interpretacion"] = [f"No aplicable: {an['motivo']}"]

    comp = r["prueba_complementaria"]
    s["complementaria"] = {"porque": [
        "Es la hipótesis que el grupo envió a los docentes el 22/10 y sobre la que recibió devoluciones (no consta una "
        "aprobación formal). Invierte el planteo: Y = Var PBI y los grupos se forman por el signo de la variación del "
        "bono. Primero se contrasta la igualdad de varianzas con la F; si no se rechaza, t con varianza agrupada; si se "
        "rechaza, Welch."]}
    if comp["aplicable"]:
        dec, f = comp["decision"], comp["prueba_f"]
        dmd = comp["diferencia_minima_detectable"]
        s["complementaria"]["interpretacion"] = [
            r["veredictos"]["prueba_complementaria"],
            f"F de varianzas = {num(f['estadistico'])} con ({f['gl'][0]}; {f['gl'][1]}) gl, {p_texto(f['p_valor'])}: "
            f"{_rechaza(f['p_valor'], a)}, por eso decide la t {dec['tipo']} (t = {num(dec['estadistico'])}, "
            f"{num(dec['gl'], 2)} gl). Welch da {p_texto(comp['t_welch']['p_valor'])}.",
            f"Medias de la Var PBI: {num(comp['grupo_1']['media'])} % en {comp['grupo_1']['n']} períodos de suba y "
            f"{num(comp['grupo_2']['media'])} % en {comp['grupo_2']['n']} de baja. d de Cohen = {num(comp['d_cohen'])}. "
            f"Con estos tamaños, la diferencia mínima detectable con 80 % de potencia es {num(dmd['en_unidades'])} pp "
            f"(d = {num(dmd['d'])}).",
        ]
        if mensual:
            s["complementaria"]["interpretacion"].append(
                "Advertencia: la Var PBI mensual sale de un spline, así que las observaciones dentro de cada grupo están "
                f"autocorrelacionadas (orden 1: {num(comp['autocorrelacion_var_pbi'])}). El test supone independencia, "
                "de modo que su p-valor es optimista. La versión trimestral, sin interpolar, es el control.")
    else:
        s["complementaria"]["interpretacion"] = [f"No aplicable: {comp['motivo']}"]

    def _sc_texto(nombre: str, sc: dict) -> str:
        reg, err, tot = sc["filas"]
        return (f"{nombre}: SCR = {num(reg['sc'])} de SCT = {num(tot['sc'], 2)}, así que R² = SCR/SCT = {num(sc['r2'])}. "
                f"F = CMR/CME = {num(reg['cm'])}/{num(err['cm'], 2)} = {num(sc['f'])} con ({sc['gl_f'][0]}; {sc['gl_f'][1]}) gl, "
                f"frente a un valor crítico de {num(sc['valor_critico'], 2)}: {p_texto(sc['p_valor'])} ({_rechaza(sc['p_valor'], a)}).")

    sc = r["sumas_cuadrados"]
    s["sumas_cuadrados"] = {
        "porque": ["El método de las sumas de cuadrados descompone la variabilidad total del bono (SCT) en la parte que "
                   "explica la recta (SCR) y la que queda en el error (SCE). Si el PBI explicara algo, SCR sería grande "
                   "frente a SCE. El cociente de sus cuadrados medios es el estadístico F, y SCR/SCT es el coeficiente de "
                   "determinación R²."],
        "interpretacion": [
            _sc_texto("Regresión simple", sc["simple"]) + " En la regresión simple F = t², así que la decisión coincide "
            "con la del test t de β1.",
            _sc_texto("Regresión múltiple", sc["multiple"]),
        ],
    }

    pr = r["proyeccion"]
    esc = pr["escenarios"]
    fuera = [e["nombre"] for e in esc if not e["dentro_del_rango"]]
    y0s = [e["y0"] for e in esc]
    margen = sum(e["margen_valor"] for e in esc) / len(esc)
    s["proyeccion"] = {
        "porque": ["Con la recta de la hipótesis se proyecta la variación del bono para escenarios de variación del PBI. "
                   "Para cada escenario hay dos rangos al 95 %: el del valor esperado (IC de la media) y el de un período "
                   "concreto (intervalo de predicción), que suma la variabilidad propia del bono. Es la mirada actuarial de "
                   "la hipótesis: si el PBI sirviera para anticipar el bono, cambiaría la proyección y achicaría el rango."],
        "interpretacion": [
            (f"Entre los escenarios de {num(esc[0]['x0'], 1, signo=True)} % y {num(esc[-1]['x0'], 1, signo=True)} % de "
             f"variación {unidad} del PBI, la variación proyectada del bono va de {num(min(y0s), 2, signo=True)} % a "
             f"{num(max(y0s), 2, signo=True)} %, casi igual a su promedio ({num(p0['y_media'], 2, signo=True)} %), con un "
             f"intervalo de predicción de unos ±{num(margen, 0)} pp. Conocer el PBI no cambia la proyección ni reduce la "
             "incertidumbre sobre el bono."
             if p0["p_b1"] >= a else
             f"La proyección cambia con el escenario: de {num(esc[0]['y0'], 2, signo=True)} % a "
             f"{num(esc[-1]['y0'], 2, signo=True)} %, con un intervalo de predicción de unos ±{num(margen, 0)} pp."),
        ] + ([f"Fuera del rango observado del PBI ({num(pr['rango_observado'][0], 2)} % a "
              f"{num(pr['rango_observado'][1], 2)} %), y por lo tanto extrapolados: {', '.join(fuera)}."] if fuera else []),
    }

    coincide = (p0["p_b1"] < a) == (q0["p_b1"] < a)
    mismo_signo = (p0["b1"] >= 0) == (q0["b1"] >= 0)
    otra = resp["frecuencia"]
    s["robustez"] = {
        "porque": [f"La muestra {otra} usa la información sin interpolar, con su propio n "
                   f"({q0['n']}{', por debajo del mínimo de 50 de la consigna' if q0['n'] < 50 else ''}). Muestra si el "
                   "veredicto depende de la mensualización. Las sensibilidades cambian una decisión por vez."],
        "interpretacion": [
            (f"El veredicto de la hipótesis principal {'se mantiene' if coincide else 'cambia'} con la muestra {otra}: "
             f"β1 = {num(q0['b1'])} (IC 95 % {ic_texto(q0['ic_b1']['inferior'], q0['ic_b1']['superior'])}; "
             f"{p_texto(q0['p_b1'])}; R² = {num(q0['r2'])}), frente a β1 = {num(p0['b1'])} ({p_texto(p0['p_b1'])}) en la "
             f"{m['frecuencia']}. El signo {'coincide' if mismo_signo else 'es opuesto'}."),
            "Sensibilidades: " + "; ".join(
                f"{x['especificacion']}: {p_texto(x['p_valor'])} ({x['decision'][0].lower() + x['decision'][1:]})"
                for x in r["sensibilidades"] if x["id"] != "base" and x.get("p_valor") is not None) + ".",
        ],
    }
    inf = r["robustez_trimestral"]["influencia"]
    cambian, sg = inf["periodos_que_cambian_decision"], inf["signos"]
    s["robustez"]["influencia"] = (
        f"Influencia en la muestra {inf['frecuencia']} (diagnóstico posterior, no pre-registrado): al excluir un "
        f"período por vez, la decisión ({inf['decision'][0].lower() + inf['decision'][1:]}) "
        + (f"se mantiene en {inf['n'] - len(cambian)} de {inf['n']} casos y cambia al excluir "
           + ", ".join(f"{f['periodo']} ({p_texto(f['p_sin'])})" for f in inf["filas"] if f["periodo"] in cambian)
           if cambian else f"se mantiene en los {inf['n']} casos")
        + f"; el p-valor va de {pval(inf['p_sin_min'])} a {pval(inf['p_sin_max'])}. En los {sg['pbi_baja']} períodos "
        f"con caída del PBI el bono subió en {sg['pbi_baja_bono_sube']}; en los {sg['pbi_sube']} con suba del PBI, "
        f"subió en {sg['pbi_sube_bono_sube']}.")

    datos = r["datos"]
    s["limitaciones"] = [
        f"Mensualización: la información real del PBI en la ventana son {datos['trimestres_pbi_en_ventana']} "
        "trimestres; la forma dentro de cada trimestre la construye el spline. El n efectivo de X es menor al nominal "
        f"(autocorrelación de orden 1 de la Var PBI mensual: {num(datos['autocorrelacion_var_pbi_mensual'])}).",
        "Información hacia adelante: el spline usa los trimestres siguientes para fijar cada mes, y la STL es un filtro "
        "de dos lados. El valor de un mes incorpora datos que en ese momento no se conocían.",
        "Error de medición en X: la Var PBI mensual es una aproximación; ese error atenúa β1 hacia cero.",
        f"Durbin-Watson: {num(r['diagnosticos']['regresion_simple']['durbin_watson'], 4)} en la regresión simple. Era esperable "
        "un valor cercano a 2 porque la variación mensual del bono tiene poca autocorrelación; se calculó en lugar de "
        "suponerlo.",
        "Ajuste ex-pago: los días de pago de cupón y amortización llevan retorno 0. Sin el ajuste, esas caídas "
        "mecánicas (" + ", ".join(f"{num(x['variacion_pct'], 1)} %" for x in datos["ex_pago"]) + ") se leerían como "
        "pérdidas de precio.",
        "Período corto (2021-2026) con pocos ciclos completos de actividad, y observaciones no independientes: "
        "períodos consecutivos comparten contexto macroeconómico.",
        "Comparaciones múltiples: siete desfases y varias especificaciones. Por eso los exploratorios se juzgan con "
        "α/5 = 0,01 y cada resultado lleva su etiqueta.",
    ]
    if mult["modo"] == "ccl":
        sin_vol = datos["ccl"].get("al30c_share_sin_volumen_por_anio", {})
        s["limitaciones"].append(
            "CCL implícito: parte de su relación con el AL30D es mecánica (mismo instrumento) y el AL30C fue poco "
            f"líquido: no operó en el {num(sin_vol.get('2022', 0) * 100, 0)} % de las ruedas de 2022, así que varios "
            "cierres de mes repiten un precio viejo. La sensibilidad (g) usa solo cierres operados.")
    s["limitaciones"].append(
        f"Muestra {otra}: n = {q0['n']}"
        + (", por debajo del mínimo de 50 de la consigna; " if q0["n"] < 50 else "; ")
        + "se presenta como control de robustez, no como resultado principal.")
    return s


def tabla_p_valores_md(r: dict) -> str:
    filas = ["| Prueba | Etiqueta | Estadístico | gl | p-valor | Umbral | Decisión |", "|---|---|---|---|---|---|---|"]
    for f in r["p_valores"]:
        filas.append(f"| {f['prueba']} | {f['etiqueta']} | {num(f['estadistico'])} | {gl_texto(f['gl'])} | {pval(f['p_valor'])} | "
                     f"{num(f['umbral'], 2)} | {f['decision']} |")
    return "\n".join(filas)
