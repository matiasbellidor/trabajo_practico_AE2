---
name: tp-web-design
description: Diseño, navegación y motion de la presentación web del TP de Análisis Estadístico 2 (docs/index.html, generada desde src/tp_ae2/web/ por tp_ae2.presentacion). Usala siempre que se toque la plantilla HTML, los estilos, navegacion.js, la portada, el riel de puntos, la barra superior, el índice, las animaciones o el deploy de la web (GitHub Pages o Vercel), aunque el pedido sea chico ("agregá un link", "que se vea más lindo", "me pierdo al scrollear", "animá esto").
---

# Diseño y motion de la web del TP

La web es la presentación que se proyecta en la exposición y que los docentes abren desde el link. Tiene que leerse como un trabajo académico serio: la estética acompaña a los números, no compite con ellos.

## Mapa de archivos

| Qué | Dónde |
|---|---|
| Plantilla (Jinja2) | `src/tp_ae2/web/plantilla.html.j2` |
| Estilos (tokens en `:root`, oscuro, impresión) | `src/tp_ae2/web/estilos.css` |
| Navegación, progreso, riel, índice, tema, impresión | `src/tp_ae2/web/navegacion.js` |
| Datos que recibe la plantilla (secciones, trazo de portada) | `src/tp_ae2/presentacion.py` |
| Salida publicada | `docs/index.html` (un solo archivo autocontenido) |
| Tests de la web | `tests/test_web_y_textos.py`, `tests/test_motion.py` (motion de figuras) |
| Coreografía de cada figura (marcas y tiempos) | `src/tp_ae2/graficos.py` (`_Motion`, `RECETAS`) |

Regenerar solo la web: `python -m tp_ae2.presentacion`. Regenerar todo: `python -m tp_ae2.run_all`. Nunca se edita `docs/index.html` a mano: se pisa en la próxima corrida.

## Restricciones que ya validan los tests

- Cero pedidos externos: nada de fuentes web, CDNs, `<img src="https:...">` ni `url(https:...)`. Íconos y logos van como SVG inline. Así la web funciona sin conexión en el aula.
- 14 secciones `<section class="diapo">` con ids únicos en todo el documento.
- Sin lenguaje causal ("impacto", "provoca", "causa") y sin el indicador mensual de actividad que la cátedra pidió no usar.
- `lang="es-AR"`, números con coma decimal y signo menos tipográfico (los da `veredicto.num`).

## Identidad

- Tipografía: serif del sistema para títulos (`--serif`), sans del sistema para texto (`--sans`). No agregar fuentes.
- Color: papel cálido (`--fondo`), tinta azul noche, un solo acento óxido (`--acento`). La portada usa el azul noche (`--noche`). Todo color nuevo es un token en `:root` y se redefine en los dos bloques de modo oscuro (sistema y `data-theme="dark"`) y en `@media print`.
- En las figuras, `--fig-s1` (azul) es la serie o muestra principal y `--fig-s2` (naranja) la de contraste. El trazo de la portada sigue la misma lógica: azul para el AL30D (la variable dependiente) y naranja para el PBI.
- Barras de scroll con la identidad: cursor óxido en cápsula, sin flechas, pista discreta, en la página y en cada contenedor con scroll (tablas, figuras, índice). Es una regla de Matías para todos sus proyectos. Chrome ignora `::-webkit-scrollbar` si ve `scrollbar-color`, así que las propiedades estándar solo van dentro de `@supports not selector(::-webkit-scrollbar)` (Firefox).
- Fechas en tablas: cada fecha en una sola pieza (`white-space: nowrap`), con el inicio arriba y "a fin" abajo si no entran en una línea. Nunca un `2021-` cortado.
- Lo "cool" sale del propio trabajo: líneas de las series reales, el número de sección, la ecuación. No sumar adornos genéricos (partículas, gradientes animados, glassmorphism, HUDs): ya se probaron en otros proyectos y se leen como plantilla.

## Orientación: que nadie se pierda

El riesgo de una web de 14 secciones largas es el scroll involuntario: un flick del trackpad y no sabés dónde estabas. Cada pieza resuelve una parte:

1. **Sección actual en la barra** (`.seccion-actual`): número `NN/14` y título, siempre visible, también en celular. Es un botón que abre el índice.
2. **Índice** (`#indice`, atributo `popover`): las 14 secciones con la actual marcada (`aria-current`). Cerrarlo con Esc o al elegir una sección.
3. **Progreso segmentado** (`.progreso`): un tramo por sección. Los anteriores llenos, el actual se llena según el avance dentro de la sección.
4. **Riel de puntos** (escritorio, más de 860 px): un cursor en forma de cápsula se desliza al punto activo y se llena con el avance de la sección. Al cambiar de sección muestra el título un momento.
5. **"Volver a…"** (`.volver`): si el scroll se detiene dos o más secciones lejos de la última donde te quedaste (más de 1,2 s), aparece un botón para volver. No aparece cuando el salto fue intencional (riel, índice o teclado).
6. **Hash en la URL**: al asentarse en una sección se hace `history.replaceState` con `#id`. Recargar o compartir el link vuelve a esa sección. Nunca `pushState`: llenaría el historial.

Si agregás una sección: sumala a `SECCIONES` en `presentacion.py` (el riel, el índice y el progreso salen de ahí) y actualizá el conteo de 14 en el test.

## Motion

Reglas, con su motivo:

- **Solo `transform` y `opacity`.** Animar `clip-path`, `width`, `height`, `top` o `visibility` saca la animación de la placa de video y traba el scroll en notebooks del aula. Para "dibujar" una línea, `stroke-dashoffset` con `pathLength="1"` vale porque se corre una sola vez. En la portada, además, `offset-distance` para el punto que recorre cada línea.
- **El estilo base es el estado final.** Las animaciones viven dentro de `@media (prefers-reduced-motion: no-preference)` y detrás de la clase `.js`. Sin JS, con movimiento reducido o al imprimir, todo se ve completo y quieto.
- **Duraciones cortas.** Cambios de interfaz (etiqueta de sección, cursor, popover): de 160 a 300 ms. Entradas de contenido: de 500 a 700 ms. El trazo de portada, de una sola vez: alrededor de 1,8 s. Curva por defecto: `cubic-bezier(.2, .8, .2, 1)`. **Excepción, solo para las figuras:** cada figura se arma una vez, en 2,4 s como mucho, y el movimiento tiene que mostrar cómo se construye el dato (barras que crecen, puntos que caen en orden, líneas que se trazan). Nada decorativo: ni partículas, ni brillos, ni gradientes animados.
- **Nada en loop.** Una animación infinita distrae mientras se explica un p-valor. Vale también para las figuras: todo es de una sola vez.
- **Lo invisible no recibe clics.** Toda capa que entra o sale con `opacity` lleva `pointer-events: none` cuando está oculta.
- **Impresión.** `html.modo-impresion` y `@media print` anulan toda animación (`opacity: 1; transform: none`) y ocultan barra, riel, índice y "Volver".

## Motion de figuras

Cada figura se arma con sus propios datos cuando queda a la vista. La lógica está repartida así:

1. **Python marca, JS no calcula.** Cada función de `graficos.py` pone `gid="m-<etiqueta>[-k][-sufijo]"` a sus artistas (barras con `-pos`/`-neg`, el anillo con `-anillo`). `_Motion` (en `graficos.py`) lee la geometría del SVG final (ejes, centros de barras, vértices de líneas) y deja en cada elemento `class="m m--<tipo> f<fase>"` y `style="--i:<orden>"`; las líneas llevan `pathLength="1"`. Cada receta (`RECETAS`) fija las fases: `t0`, `paso` (escalonado, como mucho `min(25 ms, 1200 ms / N)`) y `dur`. La figura recibe `--f<n>-t0/-paso/-dur`, `data-dur` (total, tope 2,4 s: si se pasa, `run_all` falla) y, la figura 1, `data-lecturas` con los textos del cursor formateados con `veredicto.num`.
2. **CSS reproduce.** Estado oculto: `.js .figura:not(.anima):not(.lista) .m`. Con `.anima`, cada elemento corre `var(--k)` con demora `t0 + i × paso`. Al terminar, `.lista` saca las animaciones: queda el estilo base, que es el final. Todo dentro de `@media screen and (prefers-reduced-motion: no-preference)`: al imprimir no aplica, y `tpPrepararImpresion` pone `.lista` en todas.
3. **JS decide cuándo.** Un IntersectionObserver: la figura tiene que quedar al menos un 35 % a la vista durante 120 ms (un flick del trackpad no la dispara); se arma una vez (`data-vista`). El fin llega con el último `animationend` (o `data-dur` + 800 ms). La lectura de la figura 1 cambia con el `animationstart` de cada barra: no hay trabajo por cuadro.
4. **Tipos** (`--k` en `estilos.css`): `barra` (scaleY desde la base: abajo si `m--pos`, arriba si `m--neg`), `ic`/`icx` (desde el centro), `punto` (escala con un rebote, `cubic-bezier(.34, 1.56, .64, 1)`), `cae`, `trazo` (dashoffset; con `m--sinc`, un `linear()` que hace que la punta quede bajo el cursor), `aparece`, `caja` (desde la mediana), `anillo` y `cursor` (decorativos, `m--deco`: invisibles en el estado base). Los keyframes que esperan con `fill-mode: both` arrancan invisibles (el anillo, desde opacidad 0): si no, se ven durante la demora.

| Figura | Coreografía |
|---|---|
| `series` | Cursor que barre los dos paneles en 2 s; cada barra crece cuando llega su mes; la línea del PBI se traza bajo el cursor; la lectura (mes · AL30D · PBI) va sobre el borde superior de la figura, así no tapa datos. |
| `pbi` | La serie original se traza y cada trimestre aparece al llegar la punta; después los puntos STL, el spline y la leyenda. |
| `histogramas` | Barras por panel (150 ms entre paneles); después la Normal ajustada de cada uno y la leyenda. |
| `dispersion` | Los 56 meses caen en orden cronológico (18 ms); después la recta de MCO y la banda del IC. |
| `desfases` | Referencias (cero, α); por desfase, el IC desde su centro, β1 y el p-valor que cae; anillo una vez sobre d = −2. |
| `residuos` | Puntos en orden, barras de la FAC por rezago, bandas ±1,96/√n. |
| `anova` | Por tercil: los meses, el IC desde el centro, la media y su rótulo. |
| `robustez` | Cero; fila por fila, el IC desde β1 (el IC t es simétrico) y el punto. |
| `complementaria` | Meses de suba, meses de baja; las cajas crecen desde su mediana. |

**Portada.** El título entra palabra por palabra (filtro `palabras` en `presentacion.py`: el texto del `<h1>` no cambia). Un punto recorre cada línea con `offset-path` (mismo camino, duración y curva que el trazo; sin soporte, se oculta) y al llegar abre una onda. Los números del pie cuentan desde 100 y terminan con el texto exacto del servidor.

**Repetir.** Botón «↻ Repetir» arriba a la derecha de cada figura: visible al pasar el mouse o con foco, siempre en táctil, oculto al imprimir y con movimiento reducido.

**Agregar una figura.** Poner los `gid` en su función, escribir su receta en `RECETAS`, sumar su conteo esperado (derivado de `resultados.json`) en `tests/test_motion.py` y mirar sus fotogramas.

**Lo que se aprendió midiendo** (no repetir):
- `will-change` en hijos de un SVG no ayuda (Chrome no los compone) y corre las líneas un subpíxel: al quitarlo, la figura salta. No usarlo.
- El costo de cada cuadro crece con la cantidad de elementos que tienen una animación vigente, **incluida la demora**: con CSS, los 56 puntos ya pesan desde el primer cuadro. Activarlos por tandas con JS no mejoró (más tareas largas). Medido con la CPU 4× más lenta: ~13 ms fijos más ~0,4 ms por elemento animado.
- Las capturas para comparar se toman con la página asentada (2,5 s): un momento después del scroll, Chromium vuelve a rasterizar con más calidad y los píxeles cambian.

## Link al repositorio

Usar el componente `.repo` (logo de GitHub en SVG inline, título, una línea que dice qué hay: código, datos, tablas y tests) y el botón de la barra (`.boton--repo`). La URL sale de `r.meta.repositorio` (`config.yaml`); no escribirla a mano. Abre en otra pestaña, con `rel="noopener"` y un `aria-label` completo que lo avise.

## Verificación antes de dar algo por terminado

1. `pytest` (los tests de la web incluidos).
2. `python .claude/skills/tp-web-design/scripts/verificar_web.py docs/index.html <carpeta>`. Mide el desborde horizontal de 320 a 1920 px en los dos temas, comprueba que el riel, el índice y la barra marquen la sección correcta al saltar a cada una, que aparezca "Volver a…" después de un salto largo, que no haya errores de consola y que el modo de movimiento reducido no deje nada oculto. Además guarda capturas.
   - `--rendimiento`: por figura, con la CPU 4× más lenta, cuadros (ningún cuadro de más de 50 ms, p95 ≤ 33 ms) y tareas largas (como mucho 1); figuras quietas con movimiento reducido, al imprimir y en modo impresión; y la figura terminada idéntica píxel por píxel a la quieta. Si falla, se arregla con menos elementos animados a la vez (agrupar, subir el paso, acortar), nunca aflojando los umbrales.
   - `--fotogramas`: congela cada figura al 30, 60 y 100 % en claro y oscuro, a 390 y 1440 px, y arma `fotogramas/hoja_<id>.png`. Mirar cada hoja: barras desde la base correcta, puntos que no saltan, cursor alineado, nada cortado.
3. Mirar las capturas de cada sección que tocaste, en celular y en escritorio. Los tests no ven el diseño.

## Deploy

- **GitHub Pages:** rama `main`, carpeta `/docs`. Ya está activado.
- **Vercel:** `vercel.json` en la raíz con `framework: null` (preset "Other"), `installCommand: ""` y `buildCommand: ""` (sin instalar ni buildear: el repo tiene `pyproject.toml` y Vercel podría detectarlo como proyecto Python) y `outputDirectory: "docs"`. `docs/index.html` se commitea ya generado.
