"""(1) Cada herramienta implementada a mano coincide con scipy/statsmodels (tolerancia relativa 1e-8)."""

import numpy as np
import pytest
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import acorr_breusch_godfrey, het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.proportion import proportion_confint
from statsmodels.stats.stattools import durbin_watson as dw_sm

from tp_ae2.herramientas import anova, bondad_ajuste, diferencia_medias, estimadores, intervalos, regresion

TOL = 1e-8


@pytest.fixture
def datos():
    rng = np.random.default_rng(2026)
    x = rng.normal(0.2, 0.9, 56)
    z = rng.normal(1.0, 6.0, 56)
    y = 2.0 + 1.5 * x - 0.3 * z + rng.standard_t(5, 56) * 8
    return x, y, z


def test_estimadores(datos):
    x, _, _ = datos
    e = estimadores.estimar(x)
    assert e["media"] == pytest.approx(np.mean(x), rel=TOL)
    assert e["varianza"] == pytest.approx(np.var(x, ddof=1), rel=TOL)
    assert e["error_estandar"] == pytest.approx(stats.sem(x), rel=TOL)
    assert e["asimetria"] == pytest.approx(stats.skew(x, bias=False), rel=TOL)
    assert e["curtosis_exceso"] == pytest.approx(stats.kurtosis(x, bias=False), rel=TOL)


def test_intervalos(datos):
    x, _, _ = datos
    ic = intervalos.ic_media(x, 0.95)
    esperado = stats.t.interval(0.95, len(x) - 1, loc=np.mean(x), scale=stats.sem(x))
    assert (ic["inferior"], ic["superior"]) == pytest.approx(esperado, rel=TOL)
    w = intervalos.ic_proporcion_wald(32, 56, 0.95)
    assert (w["inferior"], w["superior"]) == pytest.approx(proportion_confint(32, 56, 0.05, "normal"), rel=TOL)


def test_chi2_normal(datos):
    _, y, _ = datos
    r = bondad_ajuste.chi2_normal(y)
    obs = [c["observada"] for c in r["tabla"]]
    esp = [c["esperada"] for c in r["tabla"]]
    ref = stats.chisquare(obs, esp, ddof=2)
    assert r["k"] == 8 and r["gl"] == 5 and sum(obs) == 56
    assert r["estadistico"] == pytest.approx(ref.statistic, rel=TOL)
    assert r["p_valor"] == pytest.approx(ref.pvalue, rel=TOL)


def test_chi2_no_aplicable_con_n_chico():
    r = bondad_ajuste.chi2_normal(np.arange(19.0))
    assert not r["aplicable"] and r["gl"] < 1


def test_regresion_simple(datos):
    x, y, _ = datos
    r = regresion.regresion_simple(x, y)
    ref = sm.OLS(y, sm.add_constant(x)).fit()
    lin = stats.linregress(x, y)
    assert [r["b0"], r["b1"]] == pytest.approx(ref.params, rel=TOL)
    assert [r["ee_b0"], r["ee_b1"]] == pytest.approx(ref.bse, rel=TOL)
    assert [r["p_b0"], r["p_b1"]] == pytest.approx(ref.pvalues, rel=TOL)
    assert r["r2"] == pytest.approx(ref.rsquared, rel=TOL)
    assert r["f"] == pytest.approx(ref.fvalue, rel=TOL)
    assert r["p_b1"] == pytest.approx(lin.pvalue, rel=TOL)
    ic = ref.conf_int(0.05)[1]
    assert (r["ic_b1"]["inferior"], r["ic_b1"]["superior"]) == pytest.approx(tuple(ic), rel=TOL)
    # El p-valor de β1 coincide con el de r: invertir X e Y no lo cambia.
    assert regresion.regresion_simple(y, x)["p_b1"] == pytest.approx(r["p_b1"], rel=TOL)


@pytest.mark.filterwarnings("ignore:acorr_breusch_godfrey:FutureWarning")
def test_regresion_multiple_y_diagnosticos(datos):
    x, y, z = datos
    X = np.column_stack([x, z])
    r = regresion.regresion_multiple(X, y, ["x", "z"])
    ref = sm.OLS(y, sm.add_constant(X)).fit()
    assert [c["coeficiente"] for c in r["coeficientes"]] == pytest.approx(ref.params, rel=TOL)
    assert [c["error_estandar"] for c in r["coeficientes"]] == pytest.approx(ref.bse, rel=TOL)
    assert [c["p_valor"] for c in r["coeficientes"]] == pytest.approx(ref.pvalues, rel=TOL)
    assert r["r2_ajustado"] == pytest.approx(ref.rsquared_adj, rel=TOL)
    assert r["p_f"] == pytest.approx(ref.f_pvalue, rel=TOL)
    e, Xc = r["_residuos"], r["_X"]
    assert regresion.durbin_watson(e) == pytest.approx(dw_sm(ref.resid), rel=TOL)
    lm, p_lm, *_ = het_breuschpagan(ref.resid, ref.model.exog)
    bp = regresion.breusch_pagan(e, Xc)
    assert (bp["estadistico"], bp["p_valor"]) == pytest.approx((lm, p_lm), rel=TOL)
    lm, p_lm, *_ = acorr_breusch_godfrey(ref, nlags=3)
    bg = regresion.breusch_godfrey(e, Xc, 3)
    assert (bg["estadistico"], bg["p_valor"]) == pytest.approx((lm, p_lm), rel=TOL)
    vifs = regresion.vif(Xc, ["x", "z"])
    assert [v["vif"] for v in vifs] == pytest.approx([variance_inflation_factor(Xc, j) for j in (1, 2)], rel=TOL)


def test_anova(datos):
    _, y, _ = datos
    grupos = np.repeat(["bajo", "medio", "alto"], [19, 18, 19])
    r = anova.anova_un_factor(y, grupos, ["bajo", "medio", "alto"])
    ref = stats.f_oneway(*[y[grupos == g] for g in ("bajo", "medio", "alto")])
    assert r["f"] == pytest.approx(ref.statistic, rel=TOL)
    assert r["p_valor"] == pytest.approx(ref.pvalue, rel=TOL)
    assert r["sc_entre"] + r["sc_dentro"] == pytest.approx(r["sc_total"], rel=TOL)


def test_diferencia_medias(datos):
    x, y, _ = datos
    a, b = x[:30], x[30:] + 0.3
    agrupada = diferencia_medias.prueba_t(a, b, True)
    welch = diferencia_medias.prueba_t(a, b, False)
    ref_a, ref_w = stats.ttest_ind(a, b, equal_var=True), stats.ttest_ind(a, b, equal_var=False)
    assert (agrupada["estadistico"], agrupada["p_valor"]) == pytest.approx((ref_a.statistic, ref_a.pvalue), rel=TOL)
    assert (welch["estadistico"], welch["p_valor"]) == pytest.approx((ref_w.statistic, ref_w.pvalue), rel=TOL)
    ic = ref_a.confidence_interval(0.95)
    assert (agrupada["ic"]["inferior"], agrupada["ic"]["superior"]) == pytest.approx((ic.low, ic.high), rel=TOL)
    f = diferencia_medias.prueba_f_varianzas(a, b)
    v = np.var(a, ddof=1) / np.var(b, ddof=1)
    cola = min(stats.f.cdf(v, 29, 25), stats.f.sf(v, 29, 25))
    assert f["p_valor"] == pytest.approx(2 * cola, rel=TOL)


def test_influencia_coincide_con_statsmodels(datos, cfg):
    import pandas as pd

    from tp_ae2 import analisis

    x, y, _ = datos
    panel = pd.DataFrame({"var_pbi": x, "var_bono": y}, index=pd.period_range("2021-10", periods=len(x), freq="M"))
    inf = analisis.influencia(panel, cfg, "mensual")
    modelo = sm.OLS(y, sm.add_constant(x)).fit()
    cook_sm = modelo.get_influence().cooks_distance[0]
    np.testing.assert_allclose([f["cook"] for f in inf["filas"]], cook_sm, rtol=TOL)
    sin_primero = sm.OLS(y[1:], sm.add_constant(x[1:])).fit()
    assert inf["filas"][0]["b1_sin"] == pytest.approx(sin_primero.params[1], rel=TOL)
    assert inf["filas"][0]["p_sin"] == pytest.approx(sin_primero.pvalues[1], rel=TOL)
