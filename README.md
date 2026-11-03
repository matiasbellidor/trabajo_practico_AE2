# ¿El bono argentino sigue al PBI?

**Variación del PBI real argentino y variación del bono AL30D.** Trabajo práctico de **Análisis Estadístico 2**, **Cátedra Tito Lasanta**, FCE-UBA, segundo cuatrimestre de 2026. Grupo 1.

**[Ver la presentación](https://matiasbellidor.github.io/trabajo_practico_AE2/)** · [Informe completo](reports/cuerpo_informe.md) · [Conclusión](conclusion/conclusion.md) · [Todos los resultados (JSON)](outputs/resultados.json)

<!-- RESUMEN:INICIO -->
> **En una frase.** Queríamos saber si cuando la economía argentina crece, el bono AL30D (deuda del Estado en dólares) también sube. Con 56 meses de datos (2021-10 a 2026-05), **no encontramos esa relación**: los movimientos del bono no acompañan a los del PBI (p = 0,9940, muy lejos del umbral de 0,05).
<!-- RESUMEN:FIN -->

**Contenido:** [1. De qué se trata](#1-de-qué-se-trata) · [2. Qué queríamos demostrar](#2-qué-queríamos-demostrar) · [3. Qué demostramos](#3-qué-demostramos) · [4. Cómo leer los números](#4-cómo-leer-los-números) · [5. Herramientas estadísticas](#5-herramientas-estadísticas) · [6. Controles](#6-controles-el-resultado-es-confiable) · [7. Tabla de contrastes](#7-todos-los-contrastes-principales-en-una-tabla) · [8. Cómo se hizo](#8-cómo-se-hizo) · [9. Datos](#9-datos) · [10. Limitaciones](#10-decisiones-y-limitaciones) · [11. Reproducirlo](#11-cómo-reproducirlo) · [12. Web y deploy](#12-presentación-web-y-deploy)

## 1. De qué se trata

- **El PBI** mide todo lo que produce la economía argentina. Usamos el PBI *real* (sin el efecto de la inflación) que publica el INDEC, cada tres meses.
- **El AL30D** es un bono de la deuda del Estado argentino que vence en 2030 y cotiza en dólares. Su precio sube cuando el mercado confía más en que el Estado va a pagar, y baja cuando confía menos.
- **La intuición que pusimos a prueba:** si la economía crece, el Estado recauda más y debería poder pagar su deuda con más facilidad, así que el bono podría subir. ¿Los datos muestran eso?
- **Asociación, no causalidad:** buscamos si las dos variables se mueven juntas. Aunque lo hicieran, eso solo no probaría que una mueve a la otra, porque los datos son observacionales.

## 2. Qué queríamos demostrar

| | Pregunta | Herramienta |
|---|---|---|
| **Hipótesis principal** | ¿La variación del PBI se asocia con la variación del AL30D? | Regresión lineal simple |
| **Extensión** | ¿El bono se anticipa a la economía (se mueve antes que el PBI del mes siguiente)? | Regresión con desfases |
| **Hipótesis enviada a los docentes** (22/10) | ¿La economía crece distinto en los meses en que el bono sube que en los meses en que baja? | Diferencia de medias |

La hipótesis principal, escrita como modelo:

```
Var AL30D = β0 + β1 · Var PBI + error
```

- **H0: β1 = 0.** No hay asociación: el PBI no ayuda a predecir el bono.
- **H1: β1 ≠ 0.** Hay asociación, positiva o negativa. Contraste bilateral con α = 0,05.

Todas las decisiones de método (qué bono, qué ventana de tiempo, cómo tratar el PBI, qué pruebas son principales y cuáles exploratorias) se fijaron en [`config.yaml`](config.yaml) **antes** de calcular cualquier p-valor. Así el resultado no se acomoda a lo que se quería encontrar.

<!-- RESULTADOS:INICIO -->
<!-- Bloque generado por `python -m tp_ae2.run_all` desde outputs/resultados.json. No editar a mano: los números y las interpretaciones se recalculan. -->

## 3. Qué demostramos

**No encontramos relación entre el crecimiento del PBI y la suba del bono.** Con 56 meses de datos (2021-10 a 2026-05), los meses en que la economía creció más no fueron meses en que el AL30D subiera (o bajara) más de lo que daría el azar.

- **Hipótesis principal (regresión simple).** β1 = 0,0154, IC 95 % [−4,0639 ; 4,0948], p = 0,9940: no se rechaza H0.
- **¿El bono se adelanta a la economía?** Con el PBI del mes siguiente, β1 = 1,8997 y p = 0,3573: no hay evidencia.
- **La hipótesis que enviamos a los docentes.** El crecimiento medio del PBI en los meses de suba del bono menos el de los meses de baja da −0,0112 pp (IC 95 % [−0,4692 ; 0,4467]; p = 0,9610): no hay diferencia significativa.
- **Qué tan chica tendría que ser la relación.** Aun en el extremo del intervalo de β1, un movimiento típico del PBI (un desvío estándar, 0,84 pp) se asociaría con unos 3,4 pp de variación del bono, cuando el bono se mueve típicamente 12,5 pp por mes. Si la relación existe, explica una parte chica de lo que hace el bono.
- **La única excepción no alcanza.** Con datos trimestrales sin interpolar (n = 19), β1 = −4,5407 y p = 0,0142: el resultado cambia y el signo es opuesto. No se toma como resultado porque son menos de las 50 observaciones que pide la consigna y depende de un solo período (sin 2024Q1, la decisión se invierte).
- **Lectura posible, que este trabajo no contrasta.** El precio del bono parece seguir más las expectativas sobre la capacidad de pago del Estado (situación fiscal, reservas, riesgo de default) que la actividad del período.

> No rechazar H0 no prueba que la relación sea cero: significa que los datos no alcanzan para afirmarla. Por eso los intervalos de confianza importan: dicen qué tamaños de relación quedan descartados.

## 4. Cómo leer los números

- **p-valor.** La probabilidad de ver un resultado igual o más extremo que el observado si en realidad no hubiera relación. Si es menor a 0,05, decimos que hay evidencia ("se rechaza H0"). Si es mayor, los datos no alcanzan para afirmarla.
- **IC 95 % (intervalo de confianza).** El rango de valores plausibles para el número verdadero, con 95 % de confianza. Si incluye el cero, no se puede descartar que no haya relación.
- **β1 (pendiente).** Cuántos puntos porcentuales se mueve el bono, en promedio, por cada punto porcentual que se mueve el PBI.
- **R².** Qué parte de la variación del bono explica el modelo: 0 es nada, 1 es todo.
- **pp.** Puntos porcentuales. **n**: cantidad de observaciones.

## 5. Herramientas estadísticas

Cada herramienta sigue el mismo esquema: **por qué la usamos**, **cómo la aplicamos** (paso a paso, con las fórmulas y los números intermedios), **qué dio** y **qué significa**. La consigna pide estimador, intervalo de confianza, bondad de ajuste y regresión lineal simple y múltiple, más una herramienta a elección: elegimos ANOVA. Todo se trabaja con 95 % de confianza (α = 0,05).

Las variables son las mismas en todas las herramientas:

- **Y = Var AL30D:** variación porcentual del precio del bono en cada mes.
- **X = Var PBI:** variación porcentual del PBI real desestacionalizado y mensualizado.
- **n = 56 meses**, de 2021-10 a 2026-05.

### 5.1 Regresión lineal simple (la herramienta principal)

**Por qué la usamos.** Es la forma directa de responder la pregunta del trabajo. Estima cuánto cambia, en promedio, la variación del bono cuando la variación del PBI sube un punto, y permite testear si ese número es distinto de cero. La hipótesis principal se formuló sobre esta herramienta.

**Cómo la aplicamos.**

*Paso 1. Modelo e hipótesis.*

$$\text{Var AL30D}_t = \beta_0 + \beta_1 \cdot \text{Var PBI}_t + \varepsilon_t \qquad H_0: \beta_1 = 0 \qquad H_1: \beta_1 \neq 0$$

*Paso 2. Estimación por mínimos cuadrados* (la recta que hace mínima la suma de los errores al cuadrado):

$$\hat\beta_1 = \frac{S_{xy}}{S_{xx}} = \frac{\sum (x_i - \bar x)(y_i - \bar y)}{\sum (x_i - \bar x)^2} \qquad \hat\beta_0 = \bar y - \hat\beta_1 \, \bar x$$

Con nuestros datos: media de X = 0,1326, media de Y = 2,5158, Sxy = 0,5967 y Sxx = 38,6396. Entonces β̂1 = 0,5967 / 38,6396 = **0,0154** y β̂0 = 2,5138.

*Paso 3. Test t sobre la pendiente*, con n − 2 = 54 grados de libertad:

$$s^2 = \frac{SCE}{n-2} \qquad EE(\hat\beta_1) = \sqrt{\frac{s^2}{S_{xx}}} \qquad t = \frac{\hat\beta_1}{EE(\hat\beta_1)}$$

SCE es la suma de los errores al cuadrado (8.638,37). Queda s² = 159,97, EE(β̂1) = 2,0347 y **t = 0,0076**. El valor crítico de la t de Student con 54 gl es ±2,0049: si |t| lo supera, se rechaza H0.

*Paso 4. Intervalo de confianza y R².*

$$IC_{95\%}(\beta_1) = \hat\beta_1 \pm t_{0{,}975;\,n-2} \cdot EE(\hat\beta_1) \qquad R^2 = 1 - \frac{SCE}{SCT}$$

*Paso 5. Extensión temporal.* Repetimos la regresión con el PBI del mes siguiente (d = +1, declarado antes de ver los datos) para ver si el bono se anticipa a la economía. Como exploración, también con desfases de −3 a +3, juzgados con un umbral más exigente (0,01) porque son varias pruebas.

**Qué dio.**

| | β̂1 | IC 95 % | t | p-valor | R² |
|---|---|---|---|---|---|
| Principal (d = 0) | 0,0154 | [−4,0639 ; 4,0948] | 0,0076 | 0,9940 | 0,0000 |
| Extensión (d = +1) | 1,8997 | [−2,2037 ; 6,0030] | 0,9286 | 0,3573 | 0,0160 |

De los 5 desfases exploratorios, pasa el umbral de 0,01 el desfase d = −2 (β̂1 = −5,8701, p = 0,0025).

**Qué significa.** La pendiente es prácticamente cero: |t| = 0,0076 está muy por debajo de 2,00, el intervalo incluye al cero y el PBI explica el 0,0 % de la variación del bono. **No se rechaza H0.** Con el PBI del mes siguiente tampoco aparece relación. El desfase exploratorio significativo queda como pista para otro trabajo y no como resultado: con 5 desfases probados alguno puede salir por azar, y el PBI mensualizado hace que meses vecinos estén muy correlacionados.

**Dónde está el cálculo.** [`src/tp_ae2/herramientas/regresion.py`](src/tp_ae2/herramientas/regresion.py), función `regresion_simple`, escrita desde estas fórmulas y comparada contra statsmodels en los tests. Para rehacerla con calculadora, `outputs/tablas/cuadro_a_mano.csv` tiene las sumas: Σx = 7,4229, Σy = 140,8852, Σx² = 39,6235, Σxy = 19,2712.

### 5.2 Regresión lineal múltiple

**Por qué la usamos.** El precio del AL30D en dólares también se mueve con el tipo de cambio. Si sumamos la variación del dólar CCL implícito como segunda variable, la regresión mide la relación con el PBI *manteniendo constante* el CCL. Si la relación con el PBI estuviera tapada por el tipo de cambio, aparecería acá. La consigna también la pide.

**Cómo la aplicamos.**

*Paso 1. Modelo e hipótesis.*

$$\text{Var AL30D}_t = \beta_0 + \beta_1 \cdot \text{Var PBI}_t + \beta_2 \cdot X_{2,t} + \varepsilon_t$$

con X₂ = Var CCL implícito. Se testea cada coeficiente (H0: βj = 0) y el modelo completo (H0: β1 = β2 = 0).

*Paso 2. Estimación por mínimos cuadrados en forma matricial*, con X la matriz que tiene una columna de unos y las dos variables:

$$\hat\beta = (X^\top X)^{-1} X^\top y$$

*Paso 3. Test t de cada coeficiente* con n − k − 1 = 53 grados de libertad (k = 2 variables), y **test F global**:

$$F = \frac{(SCT - SCE)/k}{SCE/(n-k-1)}$$

Con SCT = 8.638,37 y SCE = 8.342,79 queda F = 0,9389, con (2; 53) grados de libertad.

*Paso 4. R² ajustado*, que descuenta la cantidad de variables:

$$R^2_{aj} = 1 - (1 - R^2)\,\frac{n-1}{n-k-1}$$

*Paso 5. Multicolinealidad.* Si las dos variables explicativas estuvieran muy correlacionadas entre sí, los coeficientes serían inestables. Se mide con el VIF:

$$VIF_j = \frac{1}{1 - R_j^2}$$

donde R²j sale de explicar una variable con la otra. Valores mayores a 5 o 10 preocupan; acá dan 1,01 y 1,01.

**Qué dio.**

| Coeficiente | Estimación | Error estándar | t | p-valor | IC 95 % |
|---|---|---|---|---|---|
| Constante | 3,5270 | 1,8518 | 1,9046 | 0,0623 | [−0,1873 ; 7,2413] |
| Var PBI | −0,2222 | 2,0258 | −0,1097 | 0,9131 | [−4,2854 ; 3,8411] |
| Var CCL implícito | −0,2240 | 0,1634 | −1,3703 | 0,1764 | [−0,5518 ; 0,1039] |

Modelo completo: F = 0,9389, p = 0,3975, R² = 0,0342, R² ajustado = −0,0022.

**Qué significa.** Ni con el control aparece relación con el PBI (p = 0,9131). El modelo completo tampoco es significativo: explica el 3,4 % de la variación del bono, y su R² ajustado negativo indica que sumar variables no mejora la explicación.

**Dónde está el cálculo.** [`src/tp_ae2/herramientas/regresion.py`](src/tp_ae2/herramientas/regresion.py), función `regresion_multiple`.

### 5.3 ANOVA de un factor (herramienta a elección)

**Por qué la usamos.** La regresión busca una relación en línea recta. El ANOVA no necesita esa forma: divide los meses en tres grupos según cuánto creció el PBI y compara la variación media del bono entre los grupos. Si el bono reaccionara solo en los meses de mucho o de poco crecimiento, el ANOVA lo detectaría aunque la recta no.

**Cómo la aplicamos.**

*Paso 1. Grupos por terciles de la Var PBI* (un tercio de los meses en cada uno):

- **Bajo:** Var PBI de −1,85 % a 0,07 % (19 meses).
- **Medio:** Var PBI de 0,09 % a 0,27 % (18 meses).
- **Alto:** Var PBI de 0,30 % a 2,30 % (19 meses).

*Paso 2. Hipótesis.* H0: la variación media del bono es igual en los tres grupos. H1: al menos un grupo difiere.

*Paso 3. Descomponer la variabilidad total* en la que hay entre grupos y la que hay dentro de cada grupo:

$$SC_{total} = SC_{entre} + SC_{dentro}$$

Con nuestros datos: 8.638,37 = 83,32 + 8.555,05.

*Paso 4. Estadístico F*, que compara la variabilidad entre grupos con la de adentro:

$$F = \frac{SC_{entre}/(k-1)}{SC_{dentro}/(N-k)} = \frac{CM_{entre}}{CM_{dentro}}$$

F = 41,66 / 161,42 = **0,2581**, con (2; 53) grados de libertad. El valor crítico al 95 % es 3,1716.

*Paso 5. Tamaño del efecto y supuestos.* η² = SC entre / SC total = 0,0096. Igualdad de varianzas (Levene): p = 0,0518. Normalidad por grupo (Shapiro-Wilk): bajo p = 0,6217; medio p = 0,0088; alto p = 0,0407.

**Qué dio.** Variación media del bono: bajo +3,44 %; medio +3,34 %; alto +0,81 %. F = 0,2581, p = 0,7735.

**Qué significa.** Aunque las medias se ven distintas, la diferencia entre grupos es chica comparada con lo que varía el bono dentro de cada grupo: es la esperable por azar. No se rechaza H0. El grupo de crecimiento del PBI explica el 1,0 % de la variación del bono.

**Dónde está el cálculo.** [`src/tp_ae2/herramientas/anova.py`](src/tp_ae2/herramientas/anova.py).


### 5.4 Diferencia de medias (la hipótesis enviada a los docentes)

**Por qué la usamos.** Es la hipótesis original del grupo, enviada a los docentes el 22/10. Mira la relación desde el otro lado: separa los meses según lo que hizo el bono (subió o bajó) y compara cuánto creció el PBI en cada grupo.

**Cómo la aplicamos.**

*Paso 1. Grupos e hipótesis.* Suba del bono: 32 meses. Baja: 24 meses. H0: μ suba = μ baja. H1: son distintas.

*Paso 2. Prueba F de igualdad de varianzas.* La regla de la cátedra es usar el t con varianza agrupada si no se rechaza que las varianzas sean iguales, y el t de Welch si se rechaza.

$$F = \frac{S_1^2}{S_2^2}$$

F = 1,0401, con (31; 23) grados de libertad, p = 0,9357: no se rechaza la igualdad de varianzas, así que corresponde el t con varianza agrupada.

*Paso 3. Test t.*

$$S_p^2 = \frac{(n_1 - 1)S_1^2 + (n_2 - 1)S_2^2}{n_1 + n_2 - 2} \qquad t = \frac{\bar x_1 - \bar x_2}{S_p \sqrt{\frac{1}{n_1} + \frac{1}{n_2}}}$$

Con S1 = 0,8529 y S2 = 0,8363, el desvío agrupado es Sp = 0,8459. La diferencia de medias es 0,1277 − 0,1390 = −0,0112 pp, con error estándar 0,2284: **t = −0,0491**, con 54 grados de libertad.

*Paso 4. Intervalo de confianza y potencia.* El IC 95 % de la diferencia es diferencia ± t crítico × error estándar. Además calculamos la diferencia mínima que el test detectaría con 80 % de probabilidad (potencia), para saber qué tamaños quedan descartados si no se rechaza H0.

**Qué dio.** PBI medio con el bono en suba: +0,13 %; en baja: +0,14 %. Diferencia = −0,0112 pp, IC 95 % [−0,4692 ; 0,4467], p = 0,9610. Con Welch, como control, p = 0,9609. Diferencia mínima detectable: 0,65 pp.

**Qué significa.** La economía creció prácticamente lo mismo en los meses de suba y de baja del bono: no se rechaza H0. Una diferencia de 0,65 pp o más probablemente se habría detectado; una menor no se puede descartar.

**Dónde está el cálculo.** [`src/tp_ae2/herramientas/diferencia_medias.py`](src/tp_ae2/herramientas/diferencia_medias.py).

### 5.5 Estimador

**Por qué la usamos.** Antes de testear relaciones hay que describir cada serie: dónde está su centro, cuánto se dispersa y con qué frecuencia sube el bono. Los estimadores resumen la muestra en esos pocos números y son la base de todas las demás herramientas.

**Cómo la aplicamos.** Usamos los estimadores insesgados de la media, la varianza y la proporción:

$$\bar x = \frac{1}{n}\sum x_i \qquad S^2 = \frac{1}{n-1}\sum (x_i - \bar x)^2 \qquad \hat p = \frac{\text{períodos con suba del bono}}{n}$$

Se divide por n − 1 y no por n para que S² no subestime la varianza. El error estándar de la media es S / √n.

**Qué dio.**

| | Media | Desvío (S) | Error estándar | Mínimo | Máximo |
|---|---|---|---|---|---|
| Var AL30D (%) | 2,5158 | 12,5324 | 1,6747 | −19,53 | 39,48 |
| Var PBI (%) | 0,1326 | 0,8382 | 0,1120 | −1,85 | 2,30 |

Proporción de meses con suba del bono: p̂ = 32 / 56 = 0,5714.

**Qué significa.** El bono es unas 15 veces más volátil que el PBI: su desvío es 12,53 pp contra 0,84 pp. Con esa diferencia ya se intuye que la actividad sola difícilmente explique los movimientos del bono.

**Dónde está el cálculo.** [`src/tp_ae2/herramientas/estimadores.py`](src/tp_ae2/herramientas/estimadores.py).

### 5.6 Intervalo de confianza (95 %)

**Por qué la usamos.** Una media de la muestra es un solo número y no dice cuánto puede errarle al valor verdadero. El intervalo da un rango que, con 95 % de confianza, contiene la media o la proporción verdadera.

**Cómo la aplicamos.** Para las medias, con la t de Student (la varianza verdadera no se conoce); para la proporción, con la aproximación Normal:

$$IC_{95\%}(\mu) = \bar x \pm t_{0{,}975;\,n-1} \cdot \frac{S}{\sqrt n} \qquad IC_{95\%}(p) = \hat p \pm z_{0{,}975} \cdot \sqrt{\frac{\hat p (1 - \hat p)}{n}}$$

Con 55 grados de libertad, t = 2,0040; z = 1,96. Por ejemplo, para el bono: 2,5158 ± 2,0040 × 1,6747 = 2,5158 ± 3,3562.

**Qué dio.**

| | Estimación | IC 95 % |
|---|---|---|
| Media de Var AL30D (%) | 2,5158 | [−0,8404 ; 5,8720] |
| Media de Var PBI (%) | 0,1326 | [−0,0919 ; 0,3570] |
| Proporción de meses con suba | 0,5714 | [0,4418 ; 0,7010] |
| Pendiente β1 de la regresión | 0,0154 | [−4,0639 ; 4,0948] |

**Qué significa.** Los dos intervalos de medias incluyen el cero: con estos datos no se puede afirmar que el bono ni el PBI hayan crecido en promedio por mes. El de la proporción incluye 0,5: tampoco se puede afirmar que el bono haya subido más veces de las que bajó. El de β1 incluye el cero, que es la misma conclusión que el test t.

**Dónde está el cálculo.** [`src/tp_ae2/herramientas/intervalos.py`](src/tp_ae2/herramientas/intervalos.py).

### 5.7 Bondad de ajuste (χ² y Shapiro-Wilk)

**Por qué la usamos.** El test t y los intervalos suponen que los datos (o los errores de la regresión) siguen una distribución Normal. La bondad de ajuste verifica si eso se cumple, y la consigna la pide.

**Cómo la aplicamos.**

*Paso 1. Test χ² de bondad de ajuste.* Se divide el rango de valores en k = 8 clases que, si los datos fueran Normales (con la media y el desvío de la muestra), tendrían la misma probabilidad. Así se esperan n / k = 7,0 observaciones por clase, y se compara con las observadas:

$$\chi^2 = \sum_{j=1}^{k} \frac{(O_j - E_j)^2}{E_j}$$

Tiene k − 1 − 2 = 5 grados de libertad: se pierden dos por estimar la media y el desvío. El valor crítico al 95 % es 11,0705.

*Paso 2. Test de Shapiro-Wilk.* Compara los datos ordenados con los que daría una Normal; con muestras chicas detecta desvíos que el χ² pasa por alto. Su estadístico W vale 1 si el ajuste es perfecto.

**Qué dio.**

| Variable | χ² | p-valor (χ²) | W de Shapiro-Wilk | p-valor (SW) |
|---|---|---|---|---|
| Var AL30D | 6,8571 | 0,2315 | 0,9390 | 0,0070 |
| Var PBI | 19,4286 | 0,0016 | 0,9542 | 0,0327 |
| Residuos de la regresión principal | 6,8571 | 0,2315 | 0,9390 | 0,0070 |

**Qué significa.** Las series no son exactamente Normales: el bono tiene meses extremos, de −19,5 % a +39,5 %. Con n = 56, los tests sobre medias y coeficientes siguen siendo aproximadamente válidos por el teorema central del límite, y los errores robustos de la sección 6.1 llegan a la misma conclusión. Que el χ² y Shapiro-Wilk no coincidan para el bono es esperable: Shapiro-Wilk es más potente con este tamaño de muestra.

**Dónde está el cálculo.** [`src/tp_ae2/herramientas/bondad_ajuste.py`](src/tp_ae2/herramientas/bondad_ajuste.py).

## 6. Controles: ¿el resultado es confiable?

Las herramientas de la sección 5 dan un resultado. Estos controles revisan si ese resultado se sostiene.

### 6.1 Supuestos de la regresión

**Por qué.** Los p-valores de la regresión solo son confiables si se cumplen sus supuestos (Gauss-Markov): errores con varianza constante, sin correlación en el tiempo y regresores que no se pisen entre sí.

**Cómo.** Breusch-Pagan testea si la varianza de los errores cambia con X. Durbin-Watson y Breusch-Godfrey testean si el error de un período se parece al del anterior. El VIF mide la colinealidad (sección 5.2). Como respaldo, repetimos la regresión múltiple con errores robustos de Newey-West (HAC), que no suponen varianza constante ni ausencia de autocorrelación.

**Qué dio.** Breusch-Pagan p = 0,0586; Durbin-Watson = 1,94 (el ideal es cerca de 2); Breusch-Godfrey p = 0,8349; VIF 1,01 y 1,01. Con errores HAC, el coeficiente del PBI da p = 0,9455.

**Qué significa.** No aparecen heterocedasticidad ni autocorrelación (la homocedasticidad se cumple por poco). Los errores HAC llegan a la misma conclusión.

### 6.2 Robustez: datos sin interpolar e influencia de cada período

**Por qué.** El PBI se publica por trimestre. Para tener al menos 50 observaciones lo pasamos a mensual con un spline, una curva suave que pasa por cada dato trimestral. Hay que ver si el resultado depende de ese paso.

**Cómo.** Repetimos todas las herramientas con la muestra trimestral (19 trimestres). Además sacamos un período por vez y recalculamos la regresión (leave-one-out), y medimos la influencia de cada uno con la distancia de Cook. Esto último se agregó después de ver los resultados y se rotula como tal.

**Qué dio.** Con 19 trimestres: β̂1 = −4,5407, IC 95 % [−8,0455 ; −1,0359], p = 0,0142. Al sacar un período por vez, la decisión se mantiene en 18 de 19 casos; sin 2024Q1 cambia.

**Qué significa.** Con los datos sin interpolar aparece una relación, pero es una señal a mirar y no un resultado: son menos de las 50 observaciones que pide la consigna y depende de un solo período (sin 2024Q1, la decisión se invierte). En los 5 trimestres en que cayó el PBI el bono subió en 5; en los 14 en que creció, subió en 7.

### 6.3 Sensibilidades

**Por qué.** Varias decisiones de método podrían haberse tomado de otra forma. Cambiamos una por vez para ver si el veredicto se mueve.

**Qué dio.**

| Cambio | p-valor | Decisión |
|---|---|---|
| (a) Bono sin ajuste ex-pago (serie bruta) | 0,8915 | No se rechaza H0 |
| (b) PBI sin desestacionalizar | 0,5218 | No se rechaza H0 |
| (c) ANOVA con umbrales ±0,5 % (n por grupo 10/32/14) | 0,7404 | No se rechaza H0 |
| (d) Spline con condición de borde not-a-knot | 0,9943 | No se rechaza H0 |
| (f) Múltiple con errores HAC (Newey-West, 3 rezagos): β de Var PBI | 0,9455 | No se rechaza H0 |
| (g) Múltiple con CCL de cierres operados (AL30C con volumen > 0): β de Var PBI | 0,8499 | No se rechaza H0 |
| (g) Múltiple con CCL de cierres operados (AL30C con volumen > 0): β de Var CCL | 0,1544 | No se rechaza H0 |
| (h) PBI desestacionalizado por el INDEC (en lugar de STL) | 0,8208 | No se rechaza H0 |

**Qué significa.** Ninguna cambia la decisión: el resultado no depende de esas elecciones de método.

## 7. Todos los contrastes principales en una tabla

Muestra principal: mensual, 2021-10 a 2026-05 (n = 56). Los p-valores de todos los tests (diagnósticos y sensibilidades incluidos) están en el anexo de la presentación y en `outputs/tablas/p_valores.csv`.

| Contraste | Etiqueta | n | Estimación | p-valor | Decisión (α = 0,05) |
|---|---|---|---|---|---|
| Regresión simple, β1 (d = 0) | principal | 56 | 0,0154 | 0,9940 | No se rechaza H0 |
| Regresión simple, β1 (d = +1) | extensión | 55 | 1,8997 | 0,3573 | No se rechaza H0 |
| Diferencia de medias del PBI (suba − baja) | complementaria | 56 | −0,0112 pp | 0,9610 | No se rechaza H0 |
| ANOVA por terciles del PBI | herramienta | 56 | F = 0,2581 | 0,7735 | No se rechaza H0 |
| Regresión simple, β1 (muestra trimestral) | robustez | 19 | −4,5407 | 0,0142 | Se rechaza H0 |

<!-- RESULTADOS:FIN -->

## 8. Cómo se hizo

1. **Datos.** Precio diario del AL30D (Data912) y PBI trimestral a precios de 2004 (INDEC).
2. **Pagos del bono.** Los 5 días en que el bono pagó cupón y amortización, su precio cae de 7 a 13 % solo por el pago. A esos días se les asigna variación 0, para no confundir un pago con una pérdida.
3. **Variación mensual del bono.** Se acumulan las variaciones diarias de cada mes.
4. **PBI sin estacionalidad.** El PBI tiene un patrón que se repite todos los años (el segundo trimestre siempre es alto). Se lo saca con STL, un método que separa tendencia, estacionalidad y resto. Los factores coinciden con los del PIB desestacionalizado que publica el INDEC.
5. **PBI mensual.** El PBI es trimestral y la consigna pide al menos 50 observaciones. Se lo pasa a mensual con un spline cúbico, una curva suave que pasa por cada dato trimestral. Resultado: 56 meses, de octubre de 2021 a mayo de 2026.
6. **Herramientas.** Cada una está escrita desde su fórmula en [`src/tp_ae2/herramientas/`](src/tp_ae2/herramientas/) y los tests la comparan contra scipy y statsmodels.
7. **Control de calidad.** Supuestos de la regresión, la misma batería con los trimestres sin interpolar, sensibilidades de una decisión por vez y la influencia de cada período.

| Herramienta | Archivo |
|---|---|
| Estimador | [`herramientas/estimadores.py`](src/tp_ae2/herramientas/estimadores.py) |
| Intervalo de confianza | [`herramientas/intervalos.py`](src/tp_ae2/herramientas/intervalos.py) |
| Bondad de ajuste (χ² y Shapiro-Wilk) | [`herramientas/bondad_ajuste.py`](src/tp_ae2/herramientas/bondad_ajuste.py) |
| Regresión simple y múltiple, supuestos | [`herramientas/regresion.py`](src/tp_ae2/herramientas/regresion.py) |
| ANOVA | [`herramientas/anova.py`](src/tp_ae2/herramientas/anova.py) |
| Diferencia de medias | [`herramientas/diferencia_medias.py`](src/tp_ae2/herramientas/diferencia_medias.py) |
| Batería completa, robustez e influencia | [`analisis.py`](src/tp_ae2/analisis.py) |

## 9. Datos

El grupo ordenó los datos de origen en [`data_sets_ordenados/`](data_sets_ordenados/), en formato largo (una fila por observación).

| Archivo | Contenido | Uso |
|---|---|---|
| `01_indec_cuentas_nacionales_largo.csv` | Cuentas nacionales del INDEC: oferta y demanda (original y desestacionalizada), producción por sector y PBI 1980-2005. | PBI trimestral a precios de 2004 (cuadro `OD_C01`, 2004 a 2026) y PIB desestacionalizado del INDEC para una sensibilidad. |
| `02_al30d_diario.csv` | AL30D de Data912: apertura, máximo, mínimo, cierre y volumen. 1.243 ruedas, del 23/09/2021 al 27/10/2026. | Variación del bono. |
| `03_emisiones_deuda_publica_2006_2010.csv` y `04_deuda_tablas_resumen_2006_2010.csv` | Emisiones y tablas resumen de deuda pública de 2006 a 2010. | No entran en el análisis: no hay período común con el AL30D, que cotiza desde 2021. |

En [`data/raw/`](data/raw/) están el AL30 en pesos y el AL30C en dólares cable (con ellos se calcula el dólar CCL implícito, que es el control de la regresión múltiple) y dos descargas independientes de Data912 y datos.gob.ar. Un test verifica que coinciden valor por valor con los datasets ordenados. [`outputs/linaje_datos.json`](outputs/linaje_datos.json) registra el tamaño, la huella SHA-256 y el rango de fechas de cada archivo.

## 10. Decisiones y limitaciones

- **PBI mensualizado.** En la ventana hay unos 20 trimestres reales; la forma dentro de cada trimestre la pone el spline. El n efectivo es menor que 56, y por eso se repite todo con los datos trimestrales.
- **Información hacia adelante.** El spline y la desestacionalización usan trimestres posteriores para fijar cada mes.
- **Período corto.** De 2021 a 2026 hay pocos ciclos económicos completos, y meses consecutivos comparten contexto.
- **Muchas pruebas.** Hay siete desfases y varias especificaciones. Por eso cada resultado lleva su etiqueta (principal, extensión, exploratorio, sensibilidad) y los exploratorios se juzgan con un umbral más exigente (0,01).
- **CCL implícito.** Parte de su relación con el AL30D es mecánica (mismo bono) y el AL30C no operó en el 67 % de las ruedas de 2022. Una sensibilidad usa solo los días con operaciones.
- **Muestra mensual.** Usar el PBI mensualizado requiere la conformidad de los docentes. La muestra trimestral (19 datos) no llega al mínimo de 50 y queda como control.
- **Agregado después de ver resultados:** solo el diagnóstico de influencia de la muestra trimestral, rotulado como tal.

## 11. Cómo reproducirlo

Requiere Python 3.10 o superior.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; en Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m tp_ae2.run_all --config config.yaml
pytest
```

`run_all` regenera todo desde los datos: [`outputs/resultados.json`](outputs/resultados.json), las tablas (`outputs/tablas/*.csv` y `outputs/TP_AE2_tablas.xlsx`), las figuras, el informe ([`reports/cuerpo_informe.md`](reports/cuerpo_informe.md)), la presentación web y los bloques con números de este README. La conclusión ([`conclusion/conclusion.md`](conclusion/conclusion.md)) es el único texto escrito a mano, y un test falla si alguno de sus números deja de coincidir con los resultados.

`muestra_principal` en `config.yaml` acepta `mensual_spline` (por defecto) o `trimestral`: el mismo pipeline corre con cualquiera de las dos.

## 12. Presentación web y deploy

[`docs/index.html`](docs/index.html) es un único archivo que funciona sin conexión, con tema claro y oscuro, y se imprime en A4 apaisado. Para no perderse entre las 14 secciones tiene la sección actual en la barra (al tocarla abre el índice), un progreso por sección, un riel de puntos y un botón "Volver a…" si un scroll involuntario te saltea secciones. Las reglas de diseño y su verificación están en [`.claude/skills/tp-web-design/`](.claude/skills/tp-web-design/SKILL.md).

- **GitHub Pages:** https://matiasbellidor.github.io/trabajo_practico_AE2/ (rama `main`, carpeta `/docs`).
- **Vercel:** importar el repositorio. [`vercel.json`](vercel.json) ya lo configura: preset "Other", sin instalar ni compilar, y publica `docs/`.

<details>
<summary>Estructura del repositorio</summary>

```
trabajo_practico_AE2/
├── config.yaml                 # decisiones fijadas antes de ver resultados
├── data_sets_ordenados/        # datos ordenados por el grupo (INDEC, AL30D, deuda 2006-2010)
├── data/raw/                   # AL30 y AL30C (CCL) y descargas de verificación
├── conclusion/conclusion.md    # conclusión (sección 8 del informe)
├── src/tp_ae2/
│   ├── herramientas/           # una herramienta estadística por archivo, desde su fórmula
│   ├── analisis.py             # batería completa, robustez, sensibilidades e influencia
│   ├── transformaciones.py     # pagos del bono, desestacionalización, spline, CCL
│   ├── io_datos.py             # lectura, validación y linaje de los datos
│   ├── textos.py, veredicto.py # interpretaciones y formato de números
│   ├── graficos.py             # figuras
│   ├── reporte.py, plantillas/ # tablas, informe, resumen y bloques del README
│   ├── presentacion.py, web/   # presentación web
│   └── run_all.py              # pipeline completo
├── tests/                      # herramientas contra scipy/statsmodels, datos, web, conclusión
├── outputs/                    # resultados, tablas y figuras
├── reports/cuerpo_informe.md   # informe para imprimir
├── docs/                       # web publicada (GitHub Pages y Vercel)
├── vercel.json
└── .claude/skills/tp-web-design/
```
</details>

## Autoría y licencia

Grupo 1: Maria Acevedo, Matías Rodrigo Bellido, Melina Escalante, Luka Orpianesi y Manuel Rodriguez.

El código se publica bajo licencia MIT ([`LICENSE`](LICENSE)). Los datos pertenecen a sus fuentes: Data912 y el INDEC (vía datos.gob.ar).
