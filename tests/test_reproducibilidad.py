"""(7) Dos corridas dan el mismo resultados.json."""

import json

from tp_ae2 import analisis


def test_dos_corridas_identicas(cfg, corrida):
    primera, _ = corrida
    segunda, _ = analisis.ejecutar(cfg)
    assert json.dumps(primera, sort_keys=True, ensure_ascii=False) == json.dumps(segunda, sort_keys=True, ensure_ascii=False)


def test_cada_test_tiene_estadistico_p_y_decision(corrida):
    resultados, _ = corrida
    for fila in resultados["p_valores"]:
        assert fila["estadistico"] is not None and fila["p_valor"] is not None
        assert 0 <= fila["p_valor"] <= 1
        assert fila["decision"] in ("Se rechaza H0", "No se rechaza H0")
        assert fila["etiqueta"] in ("principal", "extensión", "exploratoria", "complementaria", "sensibilidad",
                                    "herramienta", "diagnóstico", "robustez")
    etiquetas = {f["etiqueta"] for f in resultados["p_valores"]}
    assert {"principal", "extensión", "exploratoria", "complementaria", "sensibilidad"} <= etiquetas


def test_claves_de_resultados(corrida):
    resultados, _ = corrida
    for clave in ("meta", "muestra", "estimadores", "intervalos", "bondad_ajuste", "hipotesis_principal", "desfases",
                  "regresion_multiple", "anova", "prueba_complementaria", "diagnosticos", "robustez_trimestral",
                  "sensibilidades", "veredictos"):
        assert clave in resultados
    assert set(resultados["hipotesis_principal"]) == {"d0", "d1"}
