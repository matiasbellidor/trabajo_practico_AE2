// Navegación por secciones, barra de progreso, riel de puntos, tema claro/oscuro e impresión.
(function () {
  "use strict";
  var raiz = document.documentElement;
  raiz.classList.add("js");

  var secciones = Array.prototype.slice.call(document.querySelectorAll(".diapo"));
  var puntos = Array.prototype.slice.call(document.querySelectorAll(".riel a"));
  var progreso = document.querySelector(".progreso");
  var botonTema = document.querySelector("[data-tema]");
  var movimientoReducido = window.matchMedia("(prefers-reduced-motion: reduce)");

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
    botonTema.setAttribute("aria-pressed", oscuro ? "true" : "false");
    botonTema.textContent = oscuro ? "Tema claro" : "Tema oscuro";
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

  var pendiente = false;
  function actualizarProgreso() {
    pendiente = false;
    var total = document.documentElement.scrollHeight - window.innerHeight;
    var fraccion = total > 0 ? Math.min(1, Math.max(0, window.scrollY / total)) : 0;
    if (progreso) progreso.style.transform = "scaleX(" + fraccion + ")";
  }
  window.addEventListener("scroll", function () {
    if (!pendiente) { pendiente = true; window.requestAnimationFrame(actualizarProgreso); }
  }, { passive: true });
  actualizarProgreso();

  function indiceActual() {
    var limite = window.innerHeight * 0.4;
    var actual = 0;
    secciones.forEach(function (s, i) { if (s.getBoundingClientRect().top <= limite) actual = i; });
    return actual;
  }
  function marcarPunto(i) {
    puntos.forEach(function (p, j) { p.setAttribute("aria-current", j === i ? "true" : "false"); });
  }
  function ir(i) {
    var destino = secciones[Math.max(0, Math.min(secciones.length - 1, i))];
    if (destino) destino.scrollIntoView({ behavior: movimientoReducido.matches ? "auto" : "smooth", block: "start" });
  }

  if ("IntersectionObserver" in window) {
    var observadorSecciones = new IntersectionObserver(function () { marcarPunto(indiceActual()); },
      { threshold: [0, 0.4, 1] });
    secciones.forEach(function (s) { observadorSecciones.observe(s); });
    var observadorRevela = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("visible"); observadorRevela.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    document.querySelectorAll(".revela").forEach(function (el) { observadorRevela.observe(el); });
  } else {
    document.querySelectorAll(".revela").forEach(function (el) { el.classList.add("visible"); });
  }
  marcarPunto(indiceActual());

  document.addEventListener("keydown", function (ev) {
    if (ev.altKey || ev.ctrlKey || ev.metaKey) return;
    var objetivo = ev.target;
    if (objetivo && (objetivo.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(objetivo.tagName))) return;
    if (ev.key === "ArrowRight" || ev.key === "PageDown") { ev.preventDefault(); ir(indiceActual() + 1); }
    else if (ev.key === "ArrowLeft" || ev.key === "PageUp") { ev.preventDefault(); ir(indiceActual() - 1); }
  });

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
