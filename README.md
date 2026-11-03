# Variación del PBI real argentino y variación del bono AL30D

Trabajo práctico de **Análisis Estadístico 2** — **Cátedra Tito Lasanta** — FCE UBA, 2C 2026. Grupo 1.

El trabajo contrasta si la variación del PBI real argentino se asocia con la variación del precio del bono soberano AL30D. Usa estimadores, intervalos de confianza, bondad de ajuste, regresión lineal simple y múltiple, y ANOVA, todo en Python y reproducible desde los datos de origen.

## Hipótesis que se busca corroborar

Modelo de la hipótesis principal (regresión lineal simple):

```
Var AL30D_t = β0 + β1 · Var PBI_t + ε_t
```

- **H0: β1 = 0.** La variación del PBI mensualizado no se asocia de forma estadísticamente significativa con la variación de la cotización del AL30D.
- **H1: β1 ≠ 0.** Sí se asocia. Contraste bilateral con α = 0,05.

En palabras simples: si en los meses en que el PBI crece más el bono también tiende a subir (o a bajar) más de lo que explicaría el azar, β1 es distinto de cero. Es una **asociación estadística**: los datos son observacionales y no permiten afirmar que una variable mueva a la otra.

Además se contrastan:

- **Extensión temporal (declarada antes de ver resultados):** el PBI del mes siguiente (d = +1), para ver si el bono se mueve antes que la actividad. Los desfases d = −3, −2, −1, +2 y +3 son exploratorios y se juzgan con un umbral de 0,01.
- **Prueba complementaria:** la hipótesis que el grupo envió a los docentes el 22/10: la variación media del PBI difiere entre los meses en que el bono sube y aquellos en que baja (diferencia de medias).

## Resultado en una mirada

<!-- RESULTADOS:INICIO -->
<!-- Bloque generado por `python -m tp_ae2.run_all` desde outputs/resultados.json. No editar a mano. -->

> **Veredicto de la hipótesis principal.** NO HAY EVIDENCIA SUFICIENTE para afirmar la hipótesis principal (β1 = 0,0154; IC 95 % [−4,0639 ; 4,0948]; p = 0,9940; R² = 0,0000). No haber rechazado H0 no prueba que β1 sea cero.

Muestra principal: mensual, 2021-10 a 2026-05 (n = 56).

| Contraste | Etiqueta | n | Estimación | p-valor | Decisión (α = 0,05) |
|---|---|---|---|---|---|
| Regresión simple, β1 (d = 0) | principal | 56 | 0,0154 | 0,9940 | No se rechaza H0 |
| Regresión simple, β1 (d = +1) | extensión | 55 | 1,8997 | 0,3573 | No se rechaza H0 |
| Diferencia de medias del PBI (suba − baja) | complementaria | 56 | −0,0112 pp | 0,9610 | No se rechaza H0 |
| ANOVA por terciles del PBI | herramienta | 56 | F = 0,2581 | 0,7735 | No se rechaza H0 |
| Regresión simple, β1 (muestra trimestral) | robustez | 19 | −4,5407 | 0,0142 | Se rechaza H0 |

<!-- RESULTADOS:FIN -->

## Conclusión

Texto completo en [`conclusion/conclusion.md`](conclusion/conclusion.md), que también es la sección 8 del informe y la diapositiva 13 de la presentación.

- **Hipótesis principal.** Con 56 meses (oct-2021 a may-2026) no hay evidencia suficiente de que la variación del PBI real se asocie con la del AL30D (β1 = 0,0154; p = 0,9940). La extensión d = +1 (p = 0,3573), la hipótesis enviada a los docentes (p = 0,9610), el ANOVA (p = 0,7735) y la regresión múltiple con el CCL (p = 0,3975) tampoco rechazan H0.
- **Qué acotan los datos.** Aun en el extremo del IC de β1, un desvío de la Var PBI se asociaría con unos 3,4 pp de variación mensual del bono, frente a un desvío de 12,5 pp del propio bono. En la diferencia de medias, una brecha de 0,65 pp o más probablemente se habría detectado (potencia del 80 %).
- **Robustez.** Ninguna sensibilidad sobre la muestra mensual cambia el veredicto, incluida la que usa el PIB desestacionalizado del INDEC en lugar de la STL. La excepción es la muestra trimestral (n = 19, por debajo del mínimo de 50), que rechaza H0 con signo negativo (β1 = −4,5407; p = 0,0142). Ese rechazo depende de un solo trimestre: sin 2024Q1, p = 0,0527. Además, viene de los 5 trimestres con caída del PBI, en todos los cuales el bono subió.
- **Lectura.** En 2021-2026 el AL30D se movió por razones que la actividad corriente no captura. Que el bono siga las expectativas de solvencia más que el PBI del trimestre es una conjetura para contrastar con más datos, no un resultado de este trabajo.

`outputs/resumen_para_conclusion.md` tiene el detalle por herramienta, los diagnósticos y la robustez.

## Cómo se hizo

1. **Datos.** Cierres diarios del AL30D (Data912) y PBI trimestral a precios de 2004 (INDEC), leídos de `data_sets_ordenados/`.
2. **Ajuste ex-pago.** En los cinco días de pago de cupón y amortización (caídas de 7 a 13 % en una rueda) el retorno se fija en 0. La serie sin ajuste se usa como sensibilidad.
3. **Desestacionalización.** STL sobre el logaritmo del PBI (período 4, versión robusta).
4. **Mensualización.** Spline cúbico natural que pasa por cada nivel trimestral ubicado en el mes central del trimestre, sin extrapolar.
5. **Variaciones.** Variación mensual del bono, (e^(Σ log-retornos) − 1)·100, y del PBI mensualizado. Ventana oct-2021 a may-2026: n = 56.
6. **Herramientas.** Cada una se implementa desde su fórmula y se valida contra scipy/statsmodels en los tests.
7. **Diagnósticos.** Supuestos de Gauss-Markov: Breusch-Pagan, Durbin-Watson, Breusch-Godfrey, VIF y normalidad de residuos.
8. **Robustez.** Misma batería sobre la serie trimestral sin interpolar (n = 19), sensibilidades de una decisión por vez (entre ellas, el PIB desestacionalizado que publica el INDEC en lugar de la STL) y un diagnóstico de influencia por período (distancia de Cook y leave-one-out) sobre la muestra trimestral.

| Herramienta de la consigna | Módulo |
|---|---|
| Estimador | `src/tp_ae2/herramientas/estimadores.py` |
| Intervalo de confianza | `src/tp_ae2/herramientas/intervalos.py` |
| Bondad de ajuste (χ² y Shapiro-Wilk) | `src/tp_ae2/herramientas/bondad_ajuste.py` |
| Regresión lineal simple y múltiple, diagnósticos | `src/tp_ae2/herramientas/regresion.py` |
| ANOVA (herramienta a elección) | `src/tp_ae2/herramientas/anova.py` |
| Diferencia de medias (prueba complementaria) | `src/tp_ae2/herramientas/diferencia_medias.py` |
| Textos de veredicto y formato es-AR | `src/tp_ae2/veredicto.py` |

## Datos y fuentes

`data_sets_ordenados/` tiene los datasets que el grupo ordenó en formato largo (una fila por observación) a partir de los archivos originales.

| Archivo | Contenido | Uso |
|---|---|---|
| `data_sets_ordenados/01_indec_cuentas_nacionales_largo.csv` | Cuentas nacionales del INDEC: oferta y demanda globales (original y desestacionalizada), VBP y VAB por sector, PBI 1980-2005 a precios de 1993. 57.834 filas. | PBI trimestral a precios de 2004 (cuadro `OD_C01`, 2004T1 a 2026T2) y PIB desestacionalizado (`OD_DESEST_NIVEL`) para la sensibilidad (h). |
| `data_sets_ordenados/02_al30d_diario.csv` | AL30D de Data912: apertura, máximo, mínimo, cierre y volumen. 1.243 ruedas, 2021-09-23 a 2026-10-27. | Variación del bono. |
| `data_sets_ordenados/03_emisiones_deuda_publica_2006_2010.csv` | Emisiones de deuda pública de los archivos anuales 2006 a 2010: instrumento, fechas, monto, precio y rendimiento de cada colocación. | No entra en la inferencia (ver abajo). |
| `data_sets_ordenados/04_deuda_tablas_resumen_2006_2010.csv` | Tablas resumen de deuda 2006-2010: stock de letras intrasector y ratios de emisión. | No entra en la inferencia (ver abajo). |
| `data/raw/al30.json`, `data/raw/al30c.json` | Data912, `/historical/bonds/AL30` y `/AL30C`, descargados el 2026-11-01. | CCL implícito, control de la regresión múltiple. |
| `data/raw/al30d.json`, `data/raw/pbi_trimestral.csv` | Descargas independientes de Data912 y de la API de datos.gob.ar (serie `9.2_PP2_2004_T_16`), del 2026-11-01. | Verificación: según `tests/test_datos.py`, coinciden valor por valor con `01` y `02`. |

Los archivos `03` y `04` cubren 2006-2010 y el AL30D cotiza desde septiembre de 2021, así que no hay período común con la variable del bono. Además, registran colocaciones primarias de instrumentos distintos (Boden, Bonar, letras), no una serie continua de precios de un mismo bono, y 20 trimestres no alcanzan el mínimo de 50 muestras.

`outputs/linaje_datos.json` registra la ruta, el tamaño, la huella SHA-256, las filas y el rango de fechas de cada archivo que usa el pipeline.

## Decisiones a priori y limitaciones

Las decisiones están en `config.yaml` y se fijaron antes de calcular p-valores: bono, ajuste ex-pago, desestacionalización, spline, ventana, hipótesis principal (d = 0), extensión (d = +1), control de la regresión múltiple, factor del ANOVA y α. Cualquier especificación posterior se rotula exploratoria o sensibilidad. La única agregada después de mirar los datos, y antes de calcular p-valores, es la sensibilidad del CCL con cierres operados: el AL30C no tuvo operaciones en el 67 % de las ruedas de 2022. El diagnóstico de influencia de la muestra trimestral se agregó después de ver los resultados, para explicar el rechazo con n = 19, y se rotula como diagnóstico posterior. La sensibilidad con el PIB desestacionalizado del INDEC ya estaba prevista en `config.yaml` y se corrió cuando el archivo estuvo disponible.

Limitaciones:

- **Mensualización.** La información real del PBI en la ventana son unos 20 trimestres. La forma dentro de cada trimestre la construye el spline, así que el n efectivo de X es menor que el nominal.
- **Información hacia adelante.** El spline usa trimestres futuros para fijar cada mes, y la STL es un filtro de dos lados.
- **Error de medición en X.** Atenúa β1 hacia cero.
- **Durbin-Watson.** Con Y = variación del bono se esperaba un valor cercano a 2; se calcula en lugar de suponerlo.
- **Período y dependencia.** El período es corto (2021-2026), está dominado por pocos episodios y las observaciones no son independientes.
- **Comparaciones múltiples.** Hay siete desfases y varias especificaciones.
- **CCL implícito.** Parte de su relación con el AL30D es mecánica (mismo instrumento) y el AL30C fue poco líquido en 2022. Como variable de control requiere aprobación docente.
- **Muestra principal.** Mensual con PBI mensualizado; requiere conformidad docente. La serie trimestral (n = 19) no cumple el mínimo de 50 y funciona como control de robustez.

## Cómo reproducirlo

Requiere Python 3.10 o superior.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; en Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m tp_ae2.run_all --config config.yaml
pytest
```

`run_all` regenera todo desde `data_sets_ordenados/` y `data/raw/`:

- `outputs/resultados.json`: todos los resultados (estadístico, gl, p-valor y decisión de cada test).
- `outputs/resumen_para_conclusion.md`: resumen autocontenido para redactar la conclusión.
- `outputs/tablas/*.csv` y `outputs/TP_AE2_tablas.xlsx`: tablas, paneles y cuadro de cálculo a mano.
- `outputs/figuras/*.png`: figuras en 200 dpi para el documento impreso (las versiones SVG de la web están en `outputs/figuras/web/`).
- `outputs/linaje_datos.json` y `outputs/reconciliacion_borrador_previo.md`.
- `reports/cuerpo_informe.md`: informe completo para imprimir (secciones 1 a 8; la 8 es `conclusion/conclusion.md`).
- `docs/index.html`: presentación web.
- El bloque de resultados de este README.

Para regenerar solo la web desde las salidas existentes: `python -m tp_ae2.presentacion`. La conclusión es el único texto escrito a mano: `tests/test_conclusion.py` falla si alguno de sus números deja de coincidir con `outputs/resultados.json`.

`muestra_principal` en `config.yaml` admite `mensual_spline` (por defecto) o `trimestral`: el mismo pipeline corre la misma batería con cualquiera de las dos.

## Estructura del repositorio

```
trabajo_practico_AE2/
├── config.yaml                 # decisiones pre-registradas
├── data_sets_ordenados/        # datasets ordenados por el grupo (INDEC, AL30D, deuda 2006-2010)
├── data/raw/                   # AL30 y AL30C (CCL) y descargas de verificación
├── conclusion/conclusion.md    # conclusión (sección 8 del informe)
├── src/tp_ae2/
│   ├── config.py               # carga de config.yaml
│   ├── io_datos.py             # lectura, validación y linaje
│   ├── transformaciones.py     # ex-pago, STL, spline, CCL y paneles
│   ├── herramientas/           # una herramienta por módulo, desde su fórmula
│   ├── analisis.py             # batería completa, robustez y sensibilidades
│   ├── veredicto.py            # formato es-AR y textos de veredicto
│   ├── textos.py               # justificación e interpretación generadas desde los resultados
│   ├── graficos.py             # figuras PNG y SVG
│   ├── reporte.py              # tablas, JSON, informe, resumen y README
│   ├── presentacion.py         # docs/index.html
│   ├── run_all.py              # pipeline completo
│   ├── plantillas/             # plantillas Markdown del informe y el resumen
│   └── web/                    # plantilla HTML, estilos y navegación
├── tests/                      # pytest: herramientas contra scipy/statsmodels, datos, web, conclusión y reproducibilidad
├── outputs/                    # resultados, tablas, figuras y resumen
├── reports/cuerpo_informe.md
└── docs/                       # sitio estático (GitHub Pages)
```

## Presentación web

`docs/index.html` es un único archivo autocontenido: funciona sin conexión, no hace pedidos externos, tiene tema claro y oscuro, se navega con ← → y Re Pág / Av Pág, y se imprime en A4 apaisado con una sección por página.

Publicada con GitHub Pages en https://matiasbellidor.github.io/trabajo_practico_AE2/ (Settings → Pages → Deploy from a branch → rama `main`, carpeta `/docs`).

## Autoría y licencia

Grupo 1: Matías Rodrigo Bellido (GitHub: [matiasbellidor](https://github.com/matiasbellidor)), Luka Orpianesi, Manuel Rodriguez, Melina Escalante y Maria Acevedo.

El código se publica bajo licencia MIT (`LICENSE`). Los datos pertenecen a sus fuentes originales: Data912 y el INDEC (vía datos.gob.ar).
