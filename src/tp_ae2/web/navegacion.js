// Navegación por secciones: sección actual e índice en la barra, progreso por tramos, riel con cursor, aviso
// "Volver a…" después de un salto largo, hash en la URL, tema claro/oscuro e impresión.
(function () {
  "use strict";
  var raiz = document.documentElement;
  raiz.classList.add("js");

  function lista(nodos) { return Array.prototype.slice.call(nodos); }
  function dos(n) { return (n < 10 ? "0" : "") + n; }
  function acotar(x) { return Math.min(1, Math.max(0, x)); }

  var secciones = lista(document.querySelectorAll(".diapo"));
  var puntos = lista(document.querySelectorAll(".riel a"));
  var itemsIndice = lista(document.querySelectorAll(".indice a"));
  var tramos = lista(document.querySelectorAll(".progreso__tramo i"));
  var riel = document.querySelector(".riel");
  var cursor = document.querySelector(".riel__cursor");
  var relleno = document.querySelector(".riel__relleno");
  var indice = document.getElementById("indice");
  var botonIndice = document.querySelector("[data-indice-boton]");
  var numActual = document.querySelector("[data-seccion-num]");
  var tituloActual = document.querySelector("[data-seccion-titulo]");
  var volver = document.querySelector("[data-volver]");
  var volverDestino = document.querySelector("[data-volver-destino]");
  var anuncio = document.querySelector("[data-anuncio]");
  var botonTema = document.querySelector("[data-tema]");
  var textoTema = document.querySelector("[data-tema-texto]");
  var movimientoReducido = window.matchMedia("(prefers-reduced-motion: reduce)");
  var titulos = itemsIndice.map(function (a) { return a.getAttribute("data-titulo"); });
  var total = secciones.length;

  // --- Tema --------------------------------------------------------------------------------------
  function leerTema() {
    try { return localStorage.getItem("tp-ae2-tema"); } catch (e) { return null; }
  }
  function guardarTema(valor) {
    try { localStorage.setItem("tp-ae2-tema", valor); } catch (e) { /* almacenamiento bloqueado */ }
  }
  function temaEfectivo() {
    var fijado = raiz.getAttribute("data-theme");
    if (fijado) return fijado;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  function pintarBoton() {
    if (!botonTema) return;
    var oscuro = temaEfectivo() === "dark";
    var texto = oscuro ? "Tema claro" : "Tema oscuro";
    botonTema.setAttribute("aria-pressed", oscuro ? "true" : "false");
    botonTema.setAttribute("aria-label", texto);
    if (textoTema) textoTema.textContent = texto;
  }
  var guardado = leerTema();
  if (guardado === "light" || guardado === "dark") raiz.setAttribute("data-theme", guardado);
  pintarBoton();
  if (botonTema) {
    botonTema.addEventListener("click", function () {
      var nuevo = temaEfectivo() === "dark" ? "light" : "dark";
      raiz.setAttribute("data-theme", nuevo);
      guardarTema(nuevo);
      pintarBoton();
    });
  }

  // --- Sección actual ----------------------------------------------------------------------------
  var actual = -1;

  // La sección actual es la última cuyo borde superior pasó el 40 % de la ventana; al final de la página, la última.
  function medir() {
    var limite = window.innerHeight * 0.4;
    var i = 0;
    for (var k = 0; k < total; k++) { if (secciones[k].getBoundingClientRect().top <= limite) i = k; }
    var caja = secciones[i].getBoundingClientRect();
    var avance = caja.height > 0 ? (limite - caja.top) / caja.height : 0;
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) { i = total - 1; avance = 1; }
    return { i: i, avance: acotar(avance) };
  }

  function moverCursor(i) {
    var punto = puntos[i];
    if (cursor && punto) cursor.style.setProperty("--y", (punto.offsetTop + punto.offsetHeight / 2) + "px");
  }

  var turnoRotulo = 0;
  function rotular(i, anterior) {
    if (!numActual || !tituloActual) return;
    if (botonIndice) botonIndice.setAttribute("aria-label", "Abrir el índice. Sección " + (i + 1) + " de " + total + ": " + titulos[i]);
    var aplicar = function () { numActual.textContent = dos(i + 1); tituloActual.textContent = titulos[i]; };
    if (anterior === -1 || movimientoReducido.matches || typeof tituloActual.animate !== "function") { aplicar(); return; }
    var turno = ++turnoRotulo;
    var sentido = i > anterior ? 1 : -1;
    var piezas = [numActual, tituloActual];
    var salidas = piezas.map(function (el) {
      return el.animate([{ opacity: 1, transform: "none" }, { opacity: 0, transform: "translateY(" + (-45 * sentido) + "%)" }],
        { duration: 110, easing: "ease-in", fill: "forwards" });
    });
    salidas[1].onfinish = function () {
      if (turno !== turnoRotulo) return;
      aplicar();
      piezas.forEach(function (el) {
        el.getAnimations().forEach(function (a) { a.cancel(); });
        el.animate([{ opacity: 0, transform: "translateY(" + (45 * sentido) + "%)" }, { opacity: 1, transform: "none" }],
          { duration: 190, easing: "cubic-bezier(.2, .8, .2, 1)" });
      });
    };
  }

  var tAnuncia;
  function cambiarSeccion(i) {
    var anterior = actual;
    actual = i;
    secciones.forEach(function (s, k) { s.classList.toggle("activa", k === i); });
    puntos.forEach(function (p, k) {
      p.setAttribute("aria-current", k === i ? "true" : "false");
      p.setAttribute("data-estado", k < i ? "pasada" : k === i ? "actual" : "pendiente");
    });
    itemsIndice.forEach(function (a, k) { a.setAttribute("aria-current", k === i ? "true" : "false"); });
    moverCursor(i);
    rotular(i, anterior);
    if (anterior !== -1 && riel) {
      riel.classList.add("anuncia");
      clearTimeout(tAnuncia);
      tAnuncia = setTimeout(function () { riel.classList.remove("anuncia"); }, 1600);
    }
  }

  var pendiente = false;
  function actualizar() {
    pendiente = false;
    var m = medir();
    tramos.forEach(function (t, k) { t.style.transform = "scaleX(" + (k < m.i ? 1 : k === m.i ? m.avance.toFixed(3) : 0) + ")"; });
    if (cursor) cursor.style.setProperty("--avance", m.avance.toFixed(3));
    if (relleno && total > 1) relleno.style.transform = "scaleY(" + acotar((m.i + m.avance) / (total - 1)).toFixed(4) + ")";
    if (m.i !== actual) cambiarSeccion(m.i);
  }
  function pedirActualizacion() {
    if (!pendiente) { pendiente = true; window.requestAnimationFrame(actualizar); }
  }

  // --- Saltos intencionales, "Volver a…" y hash --------------------------------------------------
  // asentada: la última sección donde el lector se quedó al menos 1,2 s. Si el scroll se detiene dos o más
  // secciones lejos de ella y no fue un salto pedido (riel, índice, teclado), se ofrece volver.
  var asentada = -1, origen = -1, intencional = false;
  var tAsentar, tParada, tOcultar, tIntencional;

  function escribirHash(i) {
    var id = secciones[i] && secciones[i].id;
    if (!id) return;
    var hash = i === 0 ? "" : "#" + id;
    if (location.hash === hash) return;
    try { history.replaceState(null, "", hash || location.pathname + location.search); } catch (e) { /* sin historial */ }
  }
  function programarAsentar(i) {
    clearTimeout(tAsentar);
    tAsentar = setTimeout(function () {
      if (actual !== i) return;
      asentada = i;
      escribirHash(i);
    }, 1200);
  }
  function ocultarVolver() {
    if (volver) volver.hidden = true;
    origen = -1;
    clearTimeout(tOcultar);
  }
  function mostrarVolver(destino) {
    if (!volver || !volverDestino) return;
    origen = destino;
    var texto = dos(destino + 1) + " · " + titulos[destino];
    volverDestino.textContent = texto;
    volver.hidden = false;
    volver.classList.remove("entra");
    void volver.offsetWidth;  // reinicia la animación de entrada
    volver.classList.add("entra");
    if (anuncio) anuncio.textContent = "Saltaste varias secciones. Podés volver a " + texto + ".";
    clearTimeout(tOcultar);
    tOcultar = setTimeout(ocultarVolver, 15000);
  }
  function alPararScroll() {
    var i = actual;
    if (intencional) {
      intencional = false;
      clearTimeout(tIntencional);
      asentada = i;
      escribirHash(i);
      return;
    }
    if (origen !== -1 && i === origen) ocultarVolver();
    else if (origen === -1 && asentada !== -1 && Math.abs(i - asentada) >= 2) mostrarVolver(asentada);
    programarAsentar(i);
  }

  function ir(i) {
    i = Math.max(0, Math.min(total - 1, i));
    var destino = secciones[i];
    if (!destino) return;
    if (i !== actual) {
      intencional = true;
      clearTimeout(tIntencional);
      tIntencional = setTimeout(function () { intencional = false; }, 3000);
    }
    ocultarVolver();
    destino.scrollIntoView({ behavior: movimientoReducido.matches ? "auto" : "smooth", block: "start" });
    destino.setAttribute("tabindex", "-1");
    destino.focus({ preventScroll: true });
  }

  window.addEventListener("scroll", function () {
    pedirActualizacion();
    if (!("onscrollend" in window)) { clearTimeout(tParada); tParada = setTimeout(alPararScroll, 180); }
  }, { passive: true });
  if ("onscrollend" in window) window.addEventListener("scrollend", function () { actualizar(); alPararScroll(); });
  window.addEventListener("resize", function () { moverCursor(actual); pedirActualizacion(); });

  if (volver) {
    volver.querySelector("[data-volver-ir]").addEventListener("click", function () { var o = origen; if (o !== -1) ir(o); });
    volver.querySelector("[data-volver-cerrar]").addEventListener("click", ocultarVolver);
  }

  // --- Índice: popover nativo, con respaldo por clase si el navegador no lo soporta -------------------
  var conPopover = !!(indice && typeof indice.showPopover === "function");
  function indiceAbierto() {
    if (!indice) return false;
    if (conPopover) { try { return indice.matches(":popover-open"); } catch (e) { return false; } }
    return indice.classList.contains("abierta");
  }
  function cerrarIndice() {
    if (!indiceAbierto()) return;
    if (conPopover) indice.hidePopover();
    else { indice.classList.remove("abierta"); if (botonIndice) botonIndice.setAttribute("aria-expanded", "false"); }
  }
  function alAbrirIndice() {
    var item = itemsIndice[actual];
    if (item) { item.focus({ preventScroll: true }); item.scrollIntoView({ block: "nearest" }); }
  }
  if (indice && conPopover) {
    indice.addEventListener("toggle", function (ev) { if (ev.newState === "open") alAbrirIndice(); });
  } else if (indice && botonIndice) {
    botonIndice.removeAttribute("popovertarget");
    botonIndice.setAttribute("aria-expanded", "false");
    botonIndice.addEventListener("click", function (ev) {
      ev.stopPropagation();
      var abierta = indice.classList.toggle("abierta");
      botonIndice.setAttribute("aria-expanded", abierta ? "true" : "false");
      if (abierta) alAbrirIndice();
    });
    document.addEventListener("click", function (ev) { if (!indice.contains(ev.target)) cerrarIndice(); });
  }
  itemsIndice.concat(puntos).forEach(function (a) {
    a.addEventListener("click", function (ev) {
      var i = Number(a.getAttribute("data-ir"));
      if (isNaN(i)) return;
      ev.preventDefault();
      cerrarIndice();
      ir(i);
    });
  });

  // --- Entradas: cada sección marca .vista la primera vez que aparece; cada bloque .revela, idem ------
  if ("IntersectionObserver" in window) {
    var observadorVista = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("vista"); observadorVista.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -10% 0px" });
    secciones.forEach(function (s) { observadorVista.observe(s); });
    var observadorRevela = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("visible"); observadorRevela.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    document.querySelectorAll(".revela").forEach(function (el) { observadorRevela.observe(el); });
  } else {
    secciones.forEach(function (s) { s.classList.add("vista"); });
    document.querySelectorAll(".revela").forEach(function (el) { el.classList.add("visible"); });
  }

  actualizar();
  asentada = actual;

  // --- Teclado -----------------------------------------------------------------------------------
  document.addEventListener("keydown", function (ev) {
    if (ev.altKey || ev.ctrlKey || ev.metaKey) return;
    var objetivo = ev.target;
    if (objetivo && (objetivo.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(objetivo.tagName))) return;
    if (indice && indice.contains(objetivo)) return;
    if (ev.key === "Escape") { cerrarIndice(); return; }
    if (ev.key === "ArrowRight" || ev.key === "PageDown") { ev.preventDefault(); ir(actual + 1); }
    else if (ev.key === "ArrowLeft" || ev.key === "PageUp") { ev.preventDefault(); ir(actual - 1); }
  });

  // --- Impresión ---------------------------------------------------------------------------------
  // Al imprimir, cada sección se escala para entrar en una hoja A4 apaisada (188 mm de alto útil).
  var MM = 96 / 25.4;
  function prepararImpresion() {
    raiz.classList.add("modo-impresion");
    var alto = 182 * MM;
    secciones.forEach(function (s) {
      s.style.zoom = "";
      var h = s.getBoundingClientRect().height;
      if (h <= alto) return;
      // Con zoom menor a 0,6 la letra deja de leerse: la sección se reparte en dos hojas.
      var zoom = alto / h >= 0.6 ? alto / h : Math.min(1, (2 * alto) / h);
      s.style.zoom = zoom.toFixed(3);
    });
  }
  function restaurarImpresion() {
    raiz.classList.remove("modo-impresion");
    secciones.forEach(function (s) { s.style.zoom = ""; });
  }
  window.tpPrepararImpresion = prepararImpresion;
  window.addEventListener("beforeprint", prepararImpresion);
  window.addEventListener("afterprint", restaurarImpresion);
})();
