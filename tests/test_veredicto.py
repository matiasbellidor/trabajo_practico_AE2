"""(6) Textos de veredicto y formato numérico es-AR."""

from tp_ae2 import veredicto as V


def test_formato_es_ar():
    assert V.num(0.0146) == "0,0146"
    assert V.num(-1234.5, 1) == "−1.234,5"
    assert V.num(0, 0, signo=True) == "0"
    assert V.num(2, 0, signo=True) == "+2"
    assert V.pval(0.00004) == "< 0,0001"
    assert V.p_texto(0.0123) == "p = 0,0123"
    assert V.p_texto(0.00001) == "p < 0,0001"
    assert V.gl_texto([2, 53]) == "2; 53"
    assert V.gl_texto(54.0) == "54"
    assert V.gl_texto(50.2149) == "50,21"


def test_veredicto_rechaza():
    texto = V.veredicto_principal(1.0991, (0.57, 1.63), 0.000124, 0.253, 0.05)
    assert texto == ("SE AFIRMA la hipótesis principal: la variación mensual del PBI mensualizado se asocia de forma "
                     "estadísticamente significativa con la variación del AL30D (β1 = 1,0991; IC 95 % [0,5700 ; 1,6300]; "
                     "p = 0,0001; R² = 0,2530). Es una asociación estadística, no una relación causal.")


def test_veredicto_no_rechaza():
    texto = V.veredicto_principal(0.0154, (-4.0639, 4.0948), 0.994, 0.00000107, 0.05)
    assert texto == ("NO HAY EVIDENCIA SUFICIENTE para afirmar la hipótesis principal (β1 = 0,0154; IC 95 % "
                     "[−4,0639 ; 4,0948]; p = 0,9940; R² = 0,0000). No haber rechazado H0 no prueba que β1 sea cero.")


def test_umbral_exacto_no_rechaza():
    assert V.veredicto_principal(1, (0, 2), 0.05, 0.1, 0.05).startswith("NO HAY EVIDENCIA SUFICIENTE")
    assert V.veredicto_principal(1, (0, 2), 0.00001, 0.1, 0.05).count("p < 0,0001") == 1


def test_interpretacion_pendiente():
    assert "0,5000 pp menos" in V.interpretacion_pendiente(-0.5)
    assert "1,2000 pp más" in V.interpretacion_pendiente(1.2)
