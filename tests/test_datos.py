"""(2) Spline, (3) variación mensual del bono, (4) días ex-pago y (5) n mínimo."""

import numpy as np
import pandas as pd
import pytest

from tp_ae2 import analisis, transformaciones as T
from tp_ae2.config import con_cambios


def test_spline_pasa_por_los_niveles_y_no_extrapola(base, cfg):
    sa = T.desestacionalizar(base.pbi, "stl")["nivel"]
    mensual = T.mensualizar_spline(sa, cfg["pbi"]["spline_bc"], cfg["pbi"]["desplazamiento_mes_central"])
    centrales = sa.index.asfreq("M", how="start") + 1
    assert set(centrales.month) == {2, 5, 8, 11}
    np.testing.assert_allclose(mensual.loc[centrales].to_numpy(), sa.to_numpy(), rtol=1e-10)
    assert mensual.index[0] == centrales[0] and mensual.index[-1] == centrales[-1]
    assert str(mensual.index[-1]) == "2026-05"


def test_ventana_principal_termina_donde_termina_el_spline(cfg, base):
    panel = T.construir_panel(base, cfg, "mensual")
    assert str(panel.index[-1]) == "2026-05"
    assert panel["var_pbi_d+1"].isna().sum() == 1


def test_variacion_mensual_coincide_con_pct_change(base, cfg):
    cierres = base.bono["c"]
    mensual = cierres.groupby(cierres.index.to_period("M")).last()
    esperado = (mensual / mensual.shift(1) - 1) * 100
    resumen = T.resumen_bono(base.bono, base.retornos, "M", cfg["bono"]["dias_ex_pago"])
    sin_ex_pago = resumen[resumen["dias_ex_pago"] == ""]
    np.testing.assert_allclose(sin_ex_pago["var_bono"], esperado.loc[sin_ex_pago.index], rtol=1e-10)
    np.testing.assert_allclose(resumen["var_bono_bruto"], esperado.loc[resumen.index], rtol=1e-10)
    # Septiembre de 2021 es parcial: aparece en el resumen pero sin variación.
    assert np.isnan(resumen.loc["2021-09", "var_bono"])
    assert str(resumen["var_bono"].first_valid_index()) == "2021-10"


def test_dias_ex_pago_son_las_mayores_caidas(base, cfg):
    r = base.retornos["bruto"]
    enero_julio = r[r.index.month.isin([1, 7])]
    peores = set(enero_julio.nsmallest(5).index.strftime("%Y-%m-%d"))
    assert peores == set(cfg["bono"]["dias_ex_pago"])
    for dia in cfg["bono"]["dias_ex_pago"]:
        assert base.retornos.loc[dia, "ajustado"] == 0.0
        assert np.expm1(r.loc[dia]) < -0.06


def test_n_principal_cumple_minimo(corrida):
    resultados, _ = corrida
    assert resultados["muestra"]["principal"]["n"] == 56 >= 50
    assert resultados["muestra"]["respaldo"]["n"] == 19


def test_n_menor_a_50_falla_con_mensaje(cfg):
    corta = con_cambios(cfg, {"ventana_mensual": {"inicio": "2022-10", "fin": "2026-05"}})
    with pytest.raises(ValueError, match="n = 44 < 50"):
        analisis.ejecutar(corta)


def test_muestra_trimestral_como_principal(cfg):
    resultados, _ = analisis.ejecutar(con_cambios(cfg, {"muestra_principal": "trimestral"}))
    assert resultados["muestra"]["principal"]["n"] == 19
    assert resultados["muestra"]["principal"]["cumple_minimo_50"] is False
    assert not resultados["bondad_ajuste"]["var_bono"]["chi2"]["aplicable"]


def test_panel_trazable(base, cfg):
    panel = T.construir_panel(base, cfg, "mensual")
    for periodo, fila in panel.iterrows():
        assert pd.Timestamp(fila["fecha_ultimo_cierre"]).to_period("M") == periodo
        assert base.bono.loc[fila["fecha_ultimo_cierre"], "c"] == fila["cierre_al30d"]


def test_datasets_ordenados_coinciden_con_descargas_independientes(cfg):
    """data_sets_ordenados/ (lo que usa el análisis) contra data/raw/ (Data912 y datos.gob.ar)."""
    from tp_ae2 import io_datos

    bono, bono_raw = io_datos.leer_bono(cfg.ruta("al30d")), io_datos.leer_bono(cfg.ruta("verificacion_al30d"))
    pd.testing.assert_frame_equal(bono, bono_raw, check_dtype=False)
    pbi, pbi_raw = io_datos.leer_pbi(cfg.ruta("pbi")), io_datos.leer_pbi(cfg.ruta("verificacion_pbi"))
    assert pbi.index.equals(pbi_raw.index) and len(pbi) == 90
    np.testing.assert_allclose(pbi.to_numpy(), pbi_raw.to_numpy(), rtol=1e-12)


def test_pbi_desestacionalizado_indec_y_stl_dan_los_mismos_factores(base):
    sa = base.pbi_desest_indec
    assert sa is not None and sa.index.equals(base.pbi.index)
    implicitos = (base.pbi / sa).groupby(sa.index.quarter).mean()
    stl = T.desestacionalizar(base.pbi, "stl")["factor_estacional"]
    np.testing.assert_allclose(implicitos.to_numpy(), stl.groupby(stl.index.quarter).mean().to_numpy(), atol=0.005)


def test_influencia_respaldo(corrida):
    resultados, _ = corrida
    inf = resultados["robustez_trimestral"]["influencia"]
    assert inf["n"] == len(inf["filas"]) == resultados["muestra"]["respaldo"]["n"]
    assert inf["p_b1"] == resultados["robustez_trimestral"]["bateria_respaldo"]["hipotesis_principal"]["d0"]["p_b1"]
