# Resumen para la conclusión

Análisis Estadístico 2 · Cátedra Tito Lasanta · 2C 2026 · Grupo 1
Fuente única: `outputs/resultados.json`. α = 0,05; IC al 95 %.

## Veredicto de la hipótesis principal

> NO HAY EVIDENCIA SUFICIENTE para afirmar la hipótesis principal (β1 = 0,0154; IC 95 % [−4,0639 ; 4,0948]; p = 0,9940; R² = 0,0000). No haber rechazado H0 no prueba que β1 sea cero.

- Pendiente positiva: en la muestra, cada 1 pp adicional de variación mensual del PBI se asocia, en promedio, con 0,0154 pp más de variación mensual del AL30D.
- Muestra principal: mensual, 2021-10 a 2026-05, n = 56 (PBI mensualizado por spline; requiere conformidad docente).
- Modelo: Var AL30D_t = β0 + β1 · Var PBI_t + ε_t; H0: β1 = 0; H1: β1 ≠ 0 (bilateral).

## Extensión temporal y prueba complementaria

- Extensión (d = +1, declarada a priori): NO HAY EVIDENCIA SUFICIENTE para afirmar la extensión temporal (d = +1) (β1 = 1,8997; IC 95 % [−2,2037 ; 6,0030]; p = 0,3573; R² = 0,0160). No haber rechazado H0 no prueba que β1 sea cero.
- Complementaria (hipótesis enviada a los docentes): NO HAY EVIDENCIA SUFICIENTE para afirmar la hipótesis complementaria (diferencia suba − baja = −0,0112 pp; IC 95 % [−0,4692 ; 0,4467]; p = 0,9610). No haber rechazado H0 no prueba que las medias sean iguales.

## Resultado por herramienta

| Herramienta | Resultado | p-valor |
|---|---|---|
| Estimador | x̄ Var AL30D = 2,5158 % (S = 12,5324); x̄ Var PBI = 0,1326 % (S = 0,8382); p̂ suba = 0,5714 | — |
| Intervalo de confianza | μ bono [−0,8404 ; 5,8720]; μ PBI [−0,0919 ; 0,3570]; β1 [−4,0639 ; 4,0948] | — |
| Bondad de ajuste: Var AL30D | χ² = 6,8571 (5 gl); Shapiro W = 0,9390 | χ²: 0,2315; SW: 0,0070 |
| Bondad de ajuste: Var PBI | χ² = 19,4286 (5 gl); Shapiro W = 0,9542 | χ²: 0,0016; SW: 0,0327 |
| Bondad de ajuste: residuos de la regresión principal | χ² = 6,8571 (5 gl); Shapiro W = 0,9390 | χ²: 0,2315; SW: 0,0070 |
| Regresión simple (d = 0) | β1 = 0,0154; R² = 0,0000; t = 0,0076 | 0,9940 |
| Regresión simple (d = +1) | β1 = 1,8997; R² = 0,0160 | 0,3573 |
| Regresión múltiple: Var PBI | β = −0,2222; t = −0,1097 | 0,9131 |
| Regresión múltiple: Var CCL implícito | β = −0,2240; t = −1,3703 | 0,1764 |
| Regresión múltiple: F global | F = 0,9389; R² = 0,0342; R² aj. = −0,0022 | 0,3975 |
| ANOVA (terciles del PBI) | F = 0,2581; η² = 0,0096; medias bajo 3,44 %, medio 3,34 %, alto 0,81 % | 0,7735 |
| Complementaria (varianza agrupada) | diferencia = −0,0112 pp; d de Cohen = −0,0133; DMD 80 % = 0,6516 pp | 0,9610 |


## Desfases (X = Var PBI en t + d)

| d | Etiqueta | n | β1 | p-valor | Umbral | ¿Significativo? |
|---|---|---|---|---|---|---|
| −3 | exploratoria | 56 | −4,3165 | 0,0292 | 0,01 | no |
| −2 | exploratoria | 56 | −5,8701 | 0,0025 | 0,01 | sí |
| −1 | exploratoria | 56 | −3,7515 | 0,0609 | 0,01 | no |
| 0 | principal | 56 | 0,0154 | 0,9940 | 0,05 | no |
| +1 | extensión | 55 | 1,8997 | 0,3573 | 0,05 | no |
| +2 | exploratoria | 54 | 0,3358 | 0,8727 | 0,01 | no |
| +3 | exploratoria | 53 | −2,3590 | 0,2621 | 0,01 | no |


Desfases exploratorios con p < 0,01: d = −2 (β1 = −5,8701, p = 0,0025). Al ser exploratorios no confirman nada por sí solos: señalan una relación a contrastar con datos nuevos, y comparten la limitación del spline (la Var PBI mensual de meses vecinos está muy correlacionada).


## Diagnóstico de supuestos

- Supuestos de Gauss-Markov. Linealidad: ver residuos vs. ajustados. Homocedasticidad: Breusch-Pagan p = 0,1870 (no se rechaza H0). No autocorrelación: Durbin-Watson = 1,9475 y Breusch-Godfrey (3 rezagos) p = 0,9030 (no se rechaza H0). No multicolinealidad: correlación entre regresores −0,0856 y VIF Var PBI 1,01, Var CCL implícito 1,01 (valores mayores a 5 o 10 serían preocupantes). Normalidad de residuos: Shapiro-Wilk p = 0,0077.
- Sensibilidad con errores HAC (Newey-West, 3 rezagos): el β de la Var PBI tiene p = 0,9455, frente a p = 0,9131 con errores clásicos.
- Regresión simple: Durbin-Watson = 1,9399; Breusch-Pagan p = 0,0586; Breusch-Godfrey p = 0,8349; Shapiro de residuos p = 0,0070.
- ANOVA: Levene p = 0,0518; Shapiro por grupo: bajo 0,6217; medio 0,0088; alto 0,0407.


## Robustez

- El veredicto de la hipótesis principal cambia con la muestra trimestral: β1 = −4,5407 (IC 95 % [−8,0455 ; −1,0359]; p = 0,0142; R² = 0,3053), frente a β1 = 0,0154 (p = 0,9940) en la mensual. El signo es opuesto.
- Sensibilidades: (a) Bono sin ajuste ex-pago (serie bruta): p = 0,8915 (no se rechaza H0); (b) PBI sin desestacionalizar: p = 0,5218 (no se rechaza H0); (c) ANOVA con umbrales ±0,5 % (n por grupo 10/32/14): p = 0,7404 (no se rechaza H0); (d) Spline con condición de borde not-a-knot: p = 0,9943 (no se rechaza H0); (e) Muestra trimestral (n = 19): p = 0,0142 (se rechaza H0); (f) Múltiple con errores HAC (Newey-West, 3 rezagos): β de Var PBI: p = 0,9455 (no se rechaza H0); (g) Múltiple con CCL de cierres operados (AL30C con volumen > 0): β de Var PBI: p = 0,8499 (no se rechaza H0); (g) Múltiple con CCL de cierres operados (AL30C con volumen > 0): β de Var CCL: p = 0,1544 (no se rechaza H0); (h) PBI desestacionalizado por el INDEC (en lugar de STL): p = 0,8208 (no se rechaza H0).

- Influencia en la muestra trimestral (diagnóstico posterior, no pre-registrado): al excluir un período por vez, la decisión (se rechaza H0) se mantiene en 18 de 19 casos y cambia al excluir 2024Q1 (p = 0,0527); el p-valor va de 0,0047 a 0,0527. En los 5 períodos con caída del PBI el bono subió en 5; en los 14 con suba del PBI, subió en 7.

| Especificación | Muestra | n | Coeficiente | p-valor | Decisión |
|---|---|---|---|---|---|
| Hipótesis principal: β1 (d = 0) | mensual | 56 | 0,0154 | 0,9940 | No se rechaza H0 |
| Hipótesis principal: β1 (d = 0) | trimestral | 19 | −4,5407 | 0,0142 | Se rechaza H0 |
| Extensión: β1 (d = +1) | mensual | 55 | 1,8997 | 0,3573 | No se rechaza H0 |
| Extensión: β1 (d = +1) | trimestral | 18 | −0,2123 | 0,9199 | No se rechaza H0 |
| Múltiple: β de Var PBI | mensual | 56 | −0,2222 | 0,9131 | No se rechaza H0 |
| Múltiple: β de Var PBI | trimestral | 19 | −4,5576 | 0,0141 | Se rechaza H0 |
| ANOVA por terciles del PBI | mensual | 56 | — | 0,7735 | No se rechaza H0 |
| ANOVA por terciles del PBI | trimestral | 19 | — | 0,0274 | Se rechaza H0 |
| Complementaria: μ suba − μ baja (Var PBI) | mensual | 56 | −0,0112 | 0,9610 | No se rechaza H0 |
| Complementaria: μ suba − μ baja (Var PBI) | trimestral | 19 | −2,2177 | 0,0484 | Se rechaza H0 |


**Datos de la muestra trimestral** (para leer la robustez período por período):

| Período | Var AL30D (%) | Var PBI (%) |
|---|---|---|
| 2021Q4 | −11,91 | 1,96 |
| 2022Q1 | −6,70 | 0,90 |
| 2022Q2 | −29,60 | 3,30 |
| 2022Q3 | −15,27 | 0,44 |
| 2022Q4 | 32,58 | −2,34 |
| 2023Q1 | 6,09 | −0,26 |
| 2023Q2 | 15,12 | −3,37 |
| 2023Q3 | −0,81 | 5,45 |
| 2023Q4 | 29,49 | −3,45 |
| 2024Q1 | 42,88 | −3,33 |
| 2024Q2 | 1,98 | 0,58 |
| 2024Q3 | 13,63 | 4,26 |
| 2024Q4 | 29,11 | 1,21 |
| 2025Q1 | −5,02 | 0,18 |
| 2025Q2 | 7,46 | 0,88 |
| 2025Q3 | −16,72 | 0,70 |
| 2025Q4 | 34,46 | 0,27 |
| 2026Q1 | 3,80 | 0,73 |
| 2026Q2 | 4,93 | 0,38 |


## Limitaciones

- Mensualización: la información real del PBI en la ventana son 20 trimestres; la forma dentro de cada trimestre la construye el spline. El n efectivo de X es menor al nominal (autocorrelación de orden 1 de la Var PBI mensual: 0,7827).
- Información hacia adelante: el spline usa los trimestres siguientes para fijar cada mes, y la STL es un filtro de dos lados. El valor de un mes incorpora datos que en ese momento no se conocían.
- Error de medición en X: la Var PBI mensual es una aproximación; ese error atenúa β1 hacia cero.
- Durbin-Watson: 1,9399 en la regresión simple. Era esperable un valor cercano a 2 porque la variación mensual del bono tiene poca autocorrelación; se calculó en lugar de suponerlo.
- Ajuste ex-pago: los días de pago de cupón y amortización llevan retorno 0. Sin el ajuste, esas caídas mecánicas (−7,0 %, −10,9 %, −11,9 %, −12,8 %, −13,1 %) se leerían como pérdidas de precio.
- Período corto (2021-2026) con pocos ciclos completos de actividad, y observaciones no independientes: períodos consecutivos comparten contexto macroeconómico.
- Comparaciones múltiples: siete desfases y varias especificaciones. Por eso los exploratorios se juzgan con α/5 = 0,01 y cada resultado lleva su etiqueta.
- CCL implícito: parte de su relación con el AL30D es mecánica (mismo instrumento) y el AL30C fue poco líquido: no operó en el 67 % de las ruedas de 2022, así que varios cierres de mes repiten un precio viejo. La sensibilidad (g) usa solo cierres operados.
- Muestra trimestral: n = 19, por debajo del mínimo de 50 de la consigna; se presenta como control de robustez, no como resultado principal.


## Tabla final de p-valores

| Prueba | Etiqueta | Estadístico | gl | p-valor | Umbral | Decisión |
|---|---|---|---|---|---|---|
| Regresión simple, β1 con d = −3 | exploratoria | −2,2409 | 54 | 0,0292 | 0,01 | No se rechaza H0 |
| Regresión simple, β1 con d = −2 | exploratoria | −3,1668 | 54 | 0,0025 | 0,01 | Se rechaza H0 |
| Regresión simple, β1 con d = −1 | exploratoria | −1,9143 | 54 | 0,0609 | 0,01 | No se rechaza H0 |
| Regresión simple, β1 con d = 0 | principal | 0,0076 | 54 | 0,9940 | 0,05 | No se rechaza H0 |
| Regresión simple, β1 con d = +1 | extensión | 0,9286 | 53 | 0,3573 | 0,05 | No se rechaza H0 |
| Regresión simple, β1 con d = +2 | exploratoria | 0,1610 | 52 | 0,8727 | 0,01 | No se rechaza H0 |
| Regresión simple, β1 con d = +3 | exploratoria | −1,1340 | 51 | 0,2621 | 0,01 | No se rechaza H0 |
| Regresión simple, F global (d = 0) | herramienta | 0,0001 | 1; 54 | 0,9940 | 0,05 | No se rechaza H0 |
| Bondad de ajuste χ² a la Normal: Var AL30D | herramienta | 6,8571 | 5 | 0,2315 | 0,05 | No se rechaza H0 |
| Shapiro-Wilk: Var AL30D | herramienta | 0,9390 | — | 0,0070 | 0,05 | Se rechaza H0 |
| Bondad de ajuste χ² a la Normal: Var PBI | herramienta | 19,4286 | 5 | 0,0016 | 0,05 | Se rechaza H0 |
| Shapiro-Wilk: Var PBI | herramienta | 0,9542 | — | 0,0327 | 0,05 | Se rechaza H0 |
| Bondad de ajuste χ² a la Normal: residuos de la regresión principal | herramienta | 6,8571 | 5 | 0,2315 | 0,05 | No se rechaza H0 |
| Shapiro-Wilk: residuos de la regresión principal | herramienta | 0,9390 | — | 0,0070 | 0,05 | Se rechaza H0 |
| Regresión múltiple, F global | herramienta | 0,9389 | 2; 53 | 0,3975 | 0,05 | No se rechaza H0 |
| Regresión múltiple, t de constante | herramienta | 1,9046 | 53 | 0,0623 | 0,05 | No se rechaza H0 |
| Regresión múltiple, t de Var PBI | herramienta | −0,1097 | 53 | 0,9131 | 0,05 | No se rechaza H0 |
| Regresión múltiple, t de Var CCL implícito | herramienta | −1,3703 | 53 | 0,1764 | 0,05 | No se rechaza H0 |
| Breusch-Pagan (regresión simple) | diagnóstico | 3,5757 | 1 | 0,0586 | 0,05 | No se rechaza H0 |
| Breusch-Godfrey (regresión simple) | diagnóstico | 0,8606 | 3 | 0,8349 | 0,05 | No se rechaza H0 |
| Shapiro-Wilk de residuos (regresión simple) | diagnóstico | 0,9390 | — | 0,0070 | 0,05 | Se rechaza H0 |
| Breusch-Pagan (regresión múltiple) | diagnóstico | 3,3528 | 2 | 0,1870 | 0,05 | No se rechaza H0 |
| Breusch-Godfrey (regresión múltiple) | diagnóstico | 0,5713 | 3 | 0,9030 | 0,05 | No se rechaza H0 |
| Shapiro-Wilk de residuos (regresión múltiple) | diagnóstico | 0,9399 | — | 0,0077 | 0,05 | Se rechaza H0 |
| ANOVA de un factor (terciles del PBI) | herramienta | 0,2581 | 2; 53 | 0,7735 | 0,05 | No se rechaza H0 |
| Levene (ANOVA) | diagnóstico | 3,1312 | 2; 53 | 0,0518 | 0,05 | No se rechaza H0 |
| Shapiro-Wilk grupo bajo (ANOVA) | diagnóstico | 0,9625 | — | 0,6217 | 0,05 | No se rechaza H0 |
| Shapiro-Wilk grupo medio (ANOVA) | diagnóstico | 0,8512 | — | 0,0088 | 0,05 | Se rechaza H0 |
| Shapiro-Wilk grupo alto (ANOVA) | diagnóstico | 0,8957 | — | 0,0407 | 0,05 | Se rechaza H0 |
| F de igualdad de varianzas (complementaria) | complementaria | 1,0401 | 31; 23 | 0,9357 | 0,05 | No se rechaza H0 |
| t varianza agrupada (complementaria) — decisión | complementaria | −0,0491 | 54 | 0,9610 | 0,05 | No se rechaza H0 |
| t Welch (complementaria) | complementaria | −0,0492 | 50,21 | 0,9609 | 0,05 | No se rechaza H0 |
| Hipótesis principal: β1 (d = 0) — muestra trimestral | robustez | −2,7334 | 17 | 0,0142 | 0,05 | Se rechaza H0 |
| Extensión: β1 (d = +1) — muestra trimestral | robustez | −0,1022 | 16 | 0,9199 | 0,05 | No se rechaza H0 |
| Múltiple: β de Var PBI — muestra trimestral | robustez | −2,7557 | 16 | 0,0141 | 0,05 | Se rechaza H0 |
| ANOVA por terciles del PBI — muestra trimestral | robustez | 4,5416 | 2; 16 | 0,0274 | 0,05 | Se rechaza H0 |
| Complementaria: μ suba − μ baja (Var PBI) — muestra trimestral | robustez | −2,1264 | 17 | 0,0484 | 0,05 | Se rechaza H0 |
| (a) Bono sin ajuste ex-pago (serie bruta) | sensibilidad | −0,1370 | 54 | 0,8915 | 0,05 | No se rechaza H0 |
| (b) PBI sin desestacionalizar | sensibilidad | −0,6448 | 54 | 0,5218 | 0,05 | No se rechaza H0 |
| (c) ANOVA con umbrales ±0,5 % (n por grupo 10/32/14) | sensibilidad | 0,3023 | 2; 53 | 0,7404 | 0,05 | No se rechaza H0 |
| (d) Spline con condición de borde not-a-knot | sensibilidad | 0,0072 | 54 | 0,9943 | 0,05 | No se rechaza H0 |
| (f) Múltiple con errores HAC (Newey-West, 3 rezagos): β de Var PBI | sensibilidad | −0,0687 | 53 | 0,9455 | 0,05 | No se rechaza H0 |
| (g) Múltiple con CCL de cierres operados (AL30C con volumen > 0): β de Var PBI | sensibilidad | −0,1902 | 49 | 0,8499 | 0,05 | No se rechaza H0 |
| (g) Múltiple con CCL de cierres operados (AL30C con volumen > 0): β de Var CCL | sensibilidad | −1,4465 | 49 | 0,1544 | 0,05 | No se rechaza H0 |
| (h) PBI desestacionalizado por el INDEC (en lugar de STL) | sensibilidad | 0,2276 | 54 | 0,8208 | 0,05 | No se rechaza H0 |
