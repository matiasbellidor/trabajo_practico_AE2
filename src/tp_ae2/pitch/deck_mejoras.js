/* Capa de mejoras del pitch (la inyecta tp_ae2.pitch).
   1. Detecta la diapositiva actual sin tocar la app: la app escribe "#N" con history.replaceState (en el modo
      diapositivas y en el de lectura del celular), así que se envuelve replaceState y se escucha hashchange.
   2. Con cada cambio: atmósfera de esa diapositiva (data-diapo), paralaje del horizonte y un barrido de luz.
   3. Video de fondo: solo sin "reducir movimiento" ni ahorro de datos, en pausa con la pestaña oculta, con botón y
      tecla V para pausarlo (WCAG 2.2.2).
   4. Sincroniza ventanas: Recursos (y su vista previa en un iframe) maneja el deck por BroadcastChannel y postMessage.
   Corre antes que el módulo de la app (los módulos son diferidos): por eso alcanza a envolver replaceState. */
(function () {
  "use strict";
  var CFG = window.__PITCH__ || {};
  var DIAPOS = CFG.diapositivas || [];
  var raiz = document.documentElement;
  var fx = document.querySelector(".fx");
  var video = document.querySelector(".fx__video");
  var botonFondo = document.querySelector("[data-pitch-fondo]");
  var textoFondo = document.querySelector("[data-pitch-fondo-texto]");
  var aviso = document.querySelector("[data-pitch-aviso]");
  var reducido = window.matchMedia("(prefers-reduced-motion: reduce)");
  var params = new URLSearchParams(location.search);
  var embebido = params.get("modo") === "notas";
  var CLAVE_FONDO = "tp-ae2-pitch-fondo";
  var canal = null;
  var actual = 0;
  if (embebido) raiz.classList.add("pitch-embebido");
  if (params.get("captura") === "1") raiz.classList.add("pitch-captura");

  function numero(texto) {
    var m = String(texto || "").match(/#(\d+)/);
    var n = m ? parseInt(m[1], 10) : 1;
    return Math.max(1, Math.min(DIAPOS.length || 1, n));
  }

  function aplicar(n) {
    if (!fx || n === actual) return;
    var previo = actual;
    actual = n;
    var d = DIAPOS[n - 1] || {};
    fx.setAttribute("data-diapo", d.id || "");
    fx.style.setProperty("--i", String(n - 1));
    if (previo && !reducido.matches && !raiz.classList.contains("pitch-captura")) {
      fx.classList.remove("fx--barre", "fx--atras");
      void fx.offsetWidth; // reinicia la animación aunque se cambie de diapositiva a mitad del barrido
      fx.classList.add("fx--barre");
      if (n < previo) fx.classList.add("fx--atras");
    }
    raiz.setAttribute("data-pitch-diapo", String(n));
    var mensaje = { tipo: "pitch:diapo", n: n, id: d.id || "" };
    if (canal) { try { canal.postMessage(mensaje); } catch (e) { /* sin canal */ } }
    if (window.parent !== window) { try { window.parent.postMessage(mensaje, location.origin); } catch (e) { /* otro origen */ } }
  }

  if (fx) {
    fx.addEventListener("animationend", function (e) {
      if (e.animationName.indexOf("fx-barre") === 0) fx.classList.remove("fx--barre", "fx--atras");
    });
  }

  /* Gráficos más rápidos: la app precarga Plotly al arrancar y llama a esta función con él (deck.OPTIMIZACIONES). La
     primera figura que se dibuja en la página paga la puesta a punto de Plotly (módulos de barras y dispersión,
     medición de textos); se paga acá, con un gráfico mínimo fuera de pantalla, mientras se habla de la portada. */
  window.__pitchCalentar = function (Plotly) {
    try {
      var caja = document.createElement("div");
      caja.setAttribute("aria-hidden", "true");
      caja.style.cssText = "position:fixed;left:-10000px;top:0;width:480px;height:320px;pointer-events:none";
      document.body.appendChild(caja);
      Promise.resolve(Plotly.newPlot(caja, [
        { type: "scatter", mode: "markers+lines", x: [0, 1, 2], y: [0, 2, 1] },
        { type: "bar", x: [0, 1, 2], y: [1, -1, 2], xaxis: "x2", yaxis: "y2" },
      ], { grid: { rows: 2, columns: 1, pattern: "independent" }, showlegend: true }, { staticPlot: true }))
        .then(function () { Plotly.purge(caja); caja.remove(); }, function () { caja.remove(); });
    } catch (e) { /* si falla, la figura se dibuja igual al aparecer */ }
    return Plotly;
  };

  var replaceOriginal = history.replaceState;
  history.replaceState = function (estado, titulo, url) {
    var r = replaceOriginal.apply(this, arguments);
    if (url != null && /#\d+/.test(String(url))) aplicar(numero(String(url)));
    return r;
  };
  window.addEventListener("hashchange", function () { aplicar(numero(location.hash)); });
  aplicar(numero(location.hash || "#1"));

  /* Ir a una diapositiva desde afuera: la app escucha hashchange y navega (y en el celular hace scroll). */
  function ir(n) {
    n = Math.max(1, Math.min(DIAPOS.length || 1, n | 0));
    if (n !== actual) location.hash = "#" + n;
  }
  if ("BroadcastChannel" in window) {
    canal = new BroadcastChannel("tp-ae2-pitch");
    canal.onmessage = function (e) {
      var m = e.data || {};
      if (m.tipo === "pitch:ir" && !embebido) ir(m.n);
      if (m.tipo === "pitch:quien") canal.postMessage({ tipo: "pitch:diapo", n: actual, id: (DIAPOS[actual - 1] || {}).id || "" });
    };
  }
  window.addEventListener("message", function (e) {
    if (e.origin !== location.origin || !e.data) return;
    if (e.data.tipo === "pitch:ir") ir(e.data.n);
  });

  /* Video de fondo */
  var pausadoPorUsuario = false;
  try { pausadoPorUsuario = localStorage.getItem(CLAVE_FONDO) === "pausa"; } catch (e) { /* sin almacenamiento */ }
  function ahorroDeDatos() { return !!(navigator.connection && navigator.connection.saveData); }
  function puedeReproducir() {
    return !!video && !reducido.matches && !ahorroDeDatos() && !pausadoPorUsuario && document.visibilityState === "visible" &&
      !raiz.classList.contains("pitch-captura");
  }
  function actualizarVideo() {
    if (!video) return;
    if (puedeReproducir()) {
      if (video.preload !== "auto") video.preload = "auto";
      var p = video.play();
      if (p && p.catch) p.catch(function () { /* el navegador no dejó reproducir: queda el póster */ });
    } else {
      video.pause();
    }
    if (botonFondo) {
      var quieto = pausadoPorUsuario || reducido.matches || ahorroDeDatos();
      botonFondo.setAttribute("aria-pressed", quieto ? "true" : "false");
      botonFondo.setAttribute("aria-label", (quieto ? "Reanudar" : "Pausar") + " el video de fondo (V)");
      if (textoFondo) textoFondo.textContent = quieto ? "Fondo en pausa" : "Fondo";
    }
  }
  function alternarFondo() {
    pausadoPorUsuario = !pausadoPorUsuario;
    try { localStorage.setItem(CLAVE_FONDO, pausadoPorUsuario ? "pausa" : "on"); } catch (e) { /* sin almacenamiento */ }
    actualizarVideo();
  }
  if (botonFondo) botonFondo.addEventListener("click", alternarFondo);
  document.addEventListener("visibilitychange", actualizarVideo);
  if (reducido.addEventListener) reducido.addEventListener("change", actualizarVideo);
  actualizarVideo();

  /* Avisos breves (pantalla completa al entrar en modo presentación, estado del fondo con la tecla V) */
  var temporizador = 0;
  function avisar(html, ms) {
    if (!aviso || embebido) return;
    aviso.innerHTML = html;
    aviso.hidden = false;
    clearTimeout(temporizador);
    temporizador = setTimeout(function () { aviso.hidden = true; aviso.textContent = ""; }, ms || 3200);
  }
  window.addEventListener("keydown", function (e) {
    if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.target && e.target.closest && e.target.closest("input, textarea, select")) return;
    if (e.key === "v" || e.key === "V") {
      e.preventDefault();
      alternarFondo();
      avisar(pausadoPorUsuario ? "Fondo en pausa · <kbd>V</kbd> para reanudar" : "Fondo en movimiento", 1800);
    }
  });
  if (params.get("presentar") === "1") {
    setTimeout(function () { avisar("Pantalla completa: <kbd>F</kbd> · Avanzá con <kbd>→</kbd> o un clic", 4200); }, 600);
  }
})();
