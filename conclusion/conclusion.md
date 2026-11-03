# Conclusión

## Respuesta a la pregunta

Con los datos de octubre de 2021 a mayo de 2026 (n = 56 meses), **no hay evidencia suficiente para afirmar que la variación del PBI real argentino se asocie con la variación del bono AL30D**. La pendiente estimada es β1 = 0,0154, con IC 95 % [−4,0639 ; 4,0948] y p = 0,9940, y el modelo no explica variabilidad del bono (R² = 0,0000). No se rechaza H0: β1 = 0.

Las otras dos hipótesis llegan al mismo resultado:

- **Extensión temporal (d = +1).** El PBI del mes siguiente tampoco se asocia con el bono: β1 = 1,8997; p = 0,3573.
- **Hipótesis enviada a los docentes.** La variación media del PBI en los meses de suba del bono no difiere de la de los meses de baja: diferencia = −0,0112 pp, IC 95 % [−0,4692 ; 0,4467], p = 0,9610. La prueba F no rechazó la igualdad de varianzas (p = 0,9357), así que la decisión se tomó con el t de varianza agrupada, como indica la regla de la cátedra.

Las herramientas restantes son coherentes con eso. El ANOVA por terciles del PBI da F = 0,2581 (p = 0,7735). En la regresión múltiple con el CCL implícito como control, el F global da p = 0,3975 y el coeficiente del PBI, p = 0,9131.

## Qué permiten descartar los datos

No haber rechazado H0 no prueba que la relación sea nula, pero los intervalos acotan su tamaño:

- **Regresión.** Aun en el extremo del IC de β1, un desvío estándar de la variación mensual del PBI (0,8382 pp) se asociaría con unos 3,4 pp de variación del bono, mientras que el desvío del propio bono es 12,5324 pp. Si existe una relación lineal, explica una parte chica de lo que se mueve el AL30D en un mes.
- **Diferencia de medias.** Con 80 % de potencia, la diferencia mínima detectable es 0,6516 pp. Una diferencia de ese tamaño en el crecimiento mensual medio del PBI entre meses de suba y de baja del bono probablemente se habría detectado; una menor no se puede descartar.

## Qué tan sólido es el resultado

- **Sensibilidades.** Ninguna de las variantes sobre la muestra mensual cambia el veredicto. En la regresión simple: bono sin ajuste ex-pago (p = 0,8915), PBI sin desestacionalizar (p = 0,5218), spline not-a-knot (p = 0,9943) y PBI desestacionalizado por el INDEC en lugar de STL (p = 0,8208). En la múltiple, para el coeficiente del PBI: errores HAC (p = 0,9455) y CCL con cierres operados (p = 0,8499).
- **Supuestos.** Durbin-Watson (1,9399) y Breusch-Godfrey (p = 0,8349) no muestran autocorrelación de los residuos. Breusch-Pagan no rechaza la homocedasticidad, aunque queda cerca del umbral (p = 0,0586). Los residuos no son normales (Shapiro-Wilk p = 0,0070). Con n = 56 el t de β1 es aproximadamente válido, y los errores HAC, que no suponen homocedasticidad ni normalidad, llevan a la misma decisión.
- **La excepción: la muestra trimestral.** Sin interpolar el PBI (n = 19), β1 = −4,5407, con IC 95 % [−8,0455 ; −1,0359] y p = 0,0142: el signo es opuesto y se rechaza H0. No se toma como resultado principal por tres motivos. Primero, n = 19 está por debajo del mínimo de 50 que pide la consigna. Segundo, depende de un solo trimestre: sin 2024Q1, el p-valor sube a 0,0527. Tercero, el patrón viene de los trimestres con caída del PBI: en los 5, el bono subió, mientras que en los 14 trimestres con suba del PBI el bono subió en 7, la mitad. El desfase exploratorio d = −2 apunta al mismo signo (β1 = −5,8701; p = 0,0025, menor que el umbral de 0,01), pero es exploratorio y comparte la limitación del spline.

## Lectura de los resultados

En este período, el precio del AL30D se movió por razones que la actividad corriente no captura. Una lectura posible, que este trabajo no contrasta, es que el bono refleja sobre todo las expectativas sobre la capacidad de pago del Estado (situación fiscal, reservas, riesgo de default), y esas expectativas pueden ir en sentido contrario a la actividad del trimestre. Los cinco trimestres con caída del PBI y suba del bono están entre 2022Q4 y 2024Q1, un tramo que incluye la sequía de 2023, las elecciones presidenciales y el cambio de gobierno de diciembre de 2023 con el ajuste fiscal posterior. Los dos con mayor suba del bono son 2024Q1 (+42,88 % con el PBI en −3,33 %) y 2022Q4 (+32,58 % con −2,34 %). Es un patrón de pocos trimestres, no una relación establecida.

## Limitaciones y próximos pasos

Las limitaciones están detalladas en la sección 7. Las que más pesan son tres: la muestra mensual se apoya en solo 20 trimestres reales de PBI, el período es corto (2021-2026) y hay varias especificaciones y desfases, que obligan a separar lo confirmatorio de lo exploratorio.

Para seguir:

- Repetir el contraste con una serie de bonos soberanos en dólares más larga (por ejemplo, un índice de riesgo país), que dé más de 50 trimestres sin interpolar.
- Plantear de antemano la hipótesis que sugiere la muestra trimestral (β1 < 0: el bono sube cuando el PBI cae) y contrastarla con datos que no se usaron para formularla.
- Sumar a la regresión múltiple variables de solvencia, como el resultado fiscal o las reservas, para evaluar la lectura anterior.
