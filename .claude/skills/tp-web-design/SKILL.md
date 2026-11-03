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
| Tests de la web | `tests/test_web_y_textos.py` |

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

- **Solo `transform` y `opacity`.** Animar `clip-path`, `width`, `height`, `top` o `visibility` saca la animación de la placa de video y traba el scroll en notebooks del aula. Para "dibujar" una línea, `stroke-dashoffset` con `pathLength="1"` vale porque se corre una sola vez.
- **El estilo base es el estado final.** Las animaciones viven dentro de `@media (prefers-reduced-motion: no-preference)` y detrás de la clase `.js`. Sin JS, con movimiento reducido o al imprimir, todo se ve completo y quieto.
- **Duraciones cortas.** Cambios de interfaz (etiqueta de sección, cursor, popover): de 160 a 300 ms. Entradas de contenido: de 500 a 700 ms. El trazo de portada, de una sola vez: alrededor de 1,8 s. Curva por defecto: `cubic-bezier(.2, .8, .2, 1)`.
- **Nada en loop.** Una animación infinita distrae mientras se explica un p-valor.
- **Lo invisible no recibe clics.** Toda capa que entra o sale con `opacity` lleva `pointer-events: none` cuando está oculta.
- **Impresión.** `html.modo-impresion` y `@media print` anulan toda animación (`opacity: 1; transform: none`) y ocultan barra, riel, índice y "Volver".

## Link al repositorio

Usar el componente `.repo` (logo de GitHub en SVG inline, título, una línea que dice qué hay: código, datos, tablas y tests) y el botón de la barra (`.boton--repo`). La URL sale de `r.meta.repositorio` (`config.yaml`); no escribirla a mano. Abre en otra pestaña, con `rel="noopener"` y un `aria-label` completo que lo avise.

## Verificación antes de dar algo por terminado

1. `pytest` (los tests de la web incluidos).
2. `python .claude/skills/tp-web-design/scripts/verificar_web.py docs/index.html <carpeta>`. Mide el desborde horizontal de 320 a 1920 px en los dos temas, comprueba que el riel, el índice y la barra marquen la sección correcta al saltar a cada una, que aparezca "Volver a…" después de un salto largo, que no haya errores de consola y que el modo de movimiento reducido no deje nada oculto. Además guarda capturas.
3. Mirar las capturas de cada sección que tocaste, en celular y en escritorio. Los tests no ven el diseño.

## Deploy

- **GitHub Pages:** rama `main`, carpeta `/docs`. Ya está activado.
- **Vercel:** `vercel.json` en la raíz con `framework: null` (preset "Other"), `installCommand: ""` y `buildCommand: ""` (sin instalar ni buildear: el repo tiene `pyproject.toml` y Vercel podría detectarlo como proyecto Python) y `outputDirectory: "docs"`. `docs/index.html` se commitea ya generado.
