"""(9) La conclusión escrita a mano cita los mismos números que resultados.json y entra al informe y a la web."""

import pytest

from tp_ae2 import reporte, textos
from tp_ae2.config import RAIZ_REPO
from tp_ae2.veredicto import ic_texto, num, pval

from test_web_y_textos import CAUSAL, PROHIBIDO, _renderizar

RUTA = RAIZ_REPO / "conclusion" / "conclusion.md"


@pytest.fixture(scope="module")
def conclusion():
    if not RUTA.exists():
        pytest.skip("conclusion/conclusion.md todavía no se escribió")
    return RUTA.read_text(encoding="utf-8")


def _ic(d):
    return ic_texto(d["inferior"], d["superior"])


def test_conclusion_cita_los_numeros_vigentes(corrida, conclusion):
    r, _ = corrida
    d0, d1 = r["hipotesis_principal"]["d0"], r["hipotesis_principal"]["d1"]
    comp = r["prueba_complementaria"]
    trim = r["robustez_trimestral"]["bateria_respaldo"]["hipotesis_principal"]["d0"]
    inf = r["robustez_trimestral"]["influencia"]
    por_periodo = {f["periodo"]: f for f in inf["filas"]}
    sens = {s["id"]: s for s in r["sensibilidades"]}
    diag = r["diagnosticos"]["regresion_simple"]
    esperados = [
        f"β1 = {num(d0['b1'])}", _ic(d0["ic_b1"]), f"p = {pval(d0['p_b1'])}", f"R² = {num(d0['r2'])}",
        f"n = {r['muestra']['principal']['n']} meses",
        f"β1 = {num(d1['b1'])}; p = {pval(d1['p_b1'])}",
        f"diferencia = {num(comp['decision']['diferencia'])} pp", _ic(comp["decision"]["ic"]),
        f"p = {pval(comp['decision']['p_valor'])}", f"p = {pval(comp['prueba_f']['p_valor'])}",
        f"{num(comp['diferencia_minima_detectable']['en_unidades'])} pp",
        f"F = {num(r['anova']['f'])} (p = {pval(r['anova']['p_valor'])})",
        f"p = {pval(r['regresion_multiple']['p_f'])}", f"p = {pval(r['regresion_multiple']['coeficientes'][1]['p_valor'])}",
        f"({num(r['estimadores']['var_pbi']['desvio'])} pp)", f"{num(r['estimadores']['var_bono']['desvio'])} pp",
        # Extremo del IC de β1 por un desvío de la Var PBI.
        f"unos {num(max(abs(d0['ic_b1']['inferior']), abs(d0['ic_b1']['superior'])) * r['estimadores']['var_pbi']['desvio'], 1)} pp",
        *[f"p = {pval(sens[i]['p_valor'])}" for i in ("a", "b", "d", "f", "g1", "h")],
        f"Durbin-Watson ({num(diag['durbin_watson'])})", f"p = {pval(diag['breusch_godfrey']['p_valor'])}",
        f"p = {pval(diag['breusch_pagan']['p_valor'])}", f"p = {pval(diag['normalidad_residuos']['shapiro']['p_valor'])}",
        f"n = {trim['n']}", f"β1 = {num(trim['b1'])}", _ic(trim["ic_b1"]), f"p = {pval(trim['p_b1'])}",
        f"sin 2024Q1, el p-valor sube a {pval(por_periodo['2024Q1']['p_sin'])}",
        f"en los {inf['signos']['pbi_baja']}, el bono subió",
        f"en los {inf['signos']['pbi_sube']} trimestres con suba del PBI el bono subió en {inf['signos']['pbi_sube_bono_sube']}",
        f"2024Q1 (+{num(por_periodo['2024Q1']['var_bono'], 2)} % con el PBI en {num(por_periodo['2024Q1']['var_pbi'], 2)} %)",
        f"2022Q4 (+{num(por_periodo['2022Q4']['var_bono'], 2)} % con {num(por_periodo['2022Q4']['var_pbi'], 2)} %)",
        f"solo {r['datos']['trimestres_pbi_en_ventana']} trimestres reales",
    ]
    assert inf["periodos_que_cambian_decision"] == ["2024Q1"]
    assert inf["signos"]["pbi_baja"] == inf["signos"]["pbi_baja_bono_sube"] == 5
    d_menos2 = next(f for f in r["desfases"] if f["d"] == -2)
    esperados.append(f"β1 = {num(d_menos2['b1'])}; p = {pval(d_menos2['p_valor'])}")
    faltan = [e for e in esperados if e not in conclusion]
    assert not faltan, faltan


def test_conclusion_sin_lenguaje_causal(conclusion):
    assert not CAUSAL.search(conclusion), CAUSAL.search(conclusion)
    assert PROHIBIDO not in conclusion


def test_conclusion_entra_al_informe_y_a_la_web(corrida, conclusion):
    resultados, _ = corrida
    cuerpo = reporte.leer_conclusion(RUTA)
    assert not cuerpo.startswith("# ")
    informe = reporte.cuerpo_informe(resultados, textos.construir(resultados), cuerpo)
    assert "## 8. Conclusión\n" in informe and "### Respuesta a la pregunta" in informe
    assert "se redacta aparte" not in informe
    html = _renderizar(corrida, cuerpo)
    assert "<h3>Respuesta a la pregunta</h3>" in html and "Conclusión final pendiente" not in html
