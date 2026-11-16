/* Recursos: código de 3 casillas → descifra el guion (WebCrypto) → vista del presentador sincronizada con el deck.
   Sincronización: la vista previa es un iframe del deck (?modo=notas) que avisa por postMessage en qué diapositiva
   está; si el deck está abierto en otra pestaña del mismo navegador, se siguen por BroadcastChannel ("tp-ae2-pitch"). */
(() => {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const CLAVE = { vista: "tp-ae2-recursos-vista", reloj: "tp-ae2-recursos-reloj" };
  const publico = JSON.parse($("#guion-publico").textContent);
  const cifrado = JSON.parse($("#guion-cifrado").textContent);
  const total = publico.diapositivas.length;
  const form = $("[data-codigo]");
  const casillas = $$("[data-casilla]");
  const ayuda = $("[data-ayuda]");
  const error = $("[data-error]");
  const abrir = $("[data-abrir]");
  const puerta = $("[data-puerta]");
  const seccion = $("[data-guion]");
  const acciones = $("[data-acciones]");
  const anuncio = $("[data-anuncio]");
  const reducido = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const AYUDA = ayuda.textContent;

  const guardar = (clave, valor) => { try { valor == null ? sessionStorage.removeItem(clave) : sessionStorage.setItem(clave, valor); } catch (e) { /* sin almacenamiento */ } };
  const leer = (clave) => { try { return sessionStorage.getItem(clave); } catch (e) { return null; } };
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const reloj = (seg) => { seg = Math.max(0, Math.round(seg)); return `${Math.floor(seg / 60)}:${String(seg % 60).padStart(2, "0")}`; };

  /* ── Código de 3 casillas: un dígito por casilla, avanza solo, Backspace vuelve, se puede pegar ─────────── */
  const codigo = () => casillas.map((c) => c.value).join("");
  function limpiarError() {
    error.textContent = "";
    form.classList.remove("codigo--error");
    casillas.forEach((c) => c.removeAttribute("aria-invalid"));
  }
  function mostrarError(texto) {
    error.textContent = texto;
    form.classList.add("codigo--error");
    form.classList.remove("codigo--sacude");
    void form.offsetWidth;
    form.classList.add("codigo--sacude");
    casillas.forEach((c) => c.setAttribute("aria-invalid", "true"));
  }
  form.addEventListener("animationend", () => form.classList.remove("codigo--sacude"));
  function repartir(desde, digitos) {
    for (let i = 0; i < digitos.length && desde + i < casillas.length; i++) casillas[desde + i].value = digitos[i];
    casillas[Math.min(desde + digitos.length, casillas.length - 1)].focus();
    if (codigo().length === casillas.length) intentar();
  }
  casillas.forEach((c, i) => {
    c.addEventListener("focus", () => c.select());
    c.addEventListener("input", () => {
      const d = c.value.replace(/\D/g, "");
      limpiarError();
      if (!d) { c.value = ""; return; }
      c.value = d[0];
      if (d.length > 1) { repartir(i, d); return; } // autocompletado o teclados que mandan varios dígitos juntos
      if (i < casillas.length - 1) casillas[i + 1].focus();
      else if (codigo().length === casillas.length) intentar();
    });
    c.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !c.value && i > 0) { e.preventDefault(); casillas[i - 1].value = ""; casillas[i - 1].focus(); }
      else if (e.key === "ArrowLeft" && i > 0) { e.preventDefault(); casillas[i - 1].focus(); }
      else if (e.key === "ArrowRight" && i < casillas.length - 1) { e.preventDefault(); casillas[i + 1].focus(); }
      else if (e.key.length === 1 && /\D/.test(e.key) && !e.ctrlKey && !e.metaKey) e.preventDefault(); // solo números
    });
    c.addEventListener("paste", (e) => {
      const d = ((e.clipboardData || window.clipboardData).getData("text") || "").replace(/\D/g, "").slice(0, casillas.length);
      e.preventDefault();
      if (!d) return;
      limpiarError();
      casillas.forEach((x) => { x.value = ""; });
      repartir(0, d);
    });
  });
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    if (codigo().length < casillas.length) {
      mostrarError("Faltan números: el código tiene tres.");
      (casillas.find((c) => !c.value) || casillas[0]).focus();
      return;
    }
    intentar();
  });

  async function descifrar(cod) {
    const deB64 = (s) => Uint8Array.from(atob(s), (ch) => ch.charCodeAt(0));
    const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(cod), "PBKDF2", false, ["deriveKey"]);
    const clave = await crypto.subtle.deriveKey(
      { name: "PBKDF2", salt: deB64(cifrado.sal), iterations: cifrado.iteraciones, hash: "SHA-256" },
      base, { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
    const plano = await crypto.subtle.decrypt({ name: "AES-GCM", iv: deB64(cifrado.iv) }, clave, deB64(cifrado.datos));
    return JSON.parse(new TextDecoder().decode(plano));
  }

  let ocupado = false;
  async function intentar() {
    const cod = codigo();
    if (ocupado || !/^\d{3}$/.test(cod)) return;
    if (!window.crypto || !crypto.subtle) {
      mostrarError("Esta página se abre desde la web publicada o desde localhost, no como archivo.");
      return;
    }
    ocupado = true;
    casillas.forEach((c) => { c.disabled = true; });
    abrir.disabled = true;
    const espera = setTimeout(() => { ayuda.textContent = "Verificando…"; }, 600);
    try {
      const datos = await descifrar(cod);
      clearTimeout(espera);
      form.classList.add("codigo--ok");
      ayuda.textContent = "Código correcto.";
      setTimeout(() => abrirGuion(datos, true), reducido ? 0 : 280);
    } catch (err) {
      clearTimeout(espera);
      ayuda.textContent = AYUDA;
      casillas.forEach((c) => { c.disabled = false; c.value = ""; });
      abrir.disabled = false;
      mostrarError("Ese código no abre el guion. Revisalo con el grupo.");
      casillas[0].focus();
    } finally {
      ocupado = false;
    }
  }

  /* ── Guion ─────────────────────────────────────────────────────────────────────────────────────────────── */
  let G = null;
  let n = 1;
  let vista = leer(CLAVE.vista) || (matchMedia("(max-width: 760px)").matches ? "completo" : "presentador");
  let iframe = null;
  const canal = "BroadcastChannel" in window ? new BroadcastChannel("tp-ae2-pitch") : null;

  const pasosDe = (k) => G.pasos.filter((p) => p.n === k);
  const bloqueDe = (p) => G.bloques[p.bloque];
  const colorDe = (p) => G.oradores[bloqueDe(p).orador].color;
  function colorDePin(k, num) {
    const p = pasosDe(k).find((x) => x.marcas.some((m) => m.num === num));
    return p ? colorDe(p) : "var(--kick)";
  }
  function textoDePin(k, num) {
    for (const p of pasosDe(k)) { const m = p.marcas.find((x) => x.num === num); if (m) return m.texto; }
    return "";
  }

  function textoConMarcas(texto, paso) {
    let h = esc(texto);
    h = h.replace(/\*\*(.+?)\*\*/g, '<span class="cue cue--enfasis">énfasis</span><strong>$1</strong>');
    h = h.replace(/\[pausa (\d+(?:,\d+)?)s\]/g, '<span class="cue cue--pausa">pausa $1 s</span>');
    h = h.replace(/\[público\]/g, '<span class="cue cue--publico">al público</span>');
    h = h.replace(/\[lento\]/g, '<span class="cue cue--lento">más lento</span>');
    h = h.replace(/\[señalar (\d+)\]/g, (_, k) => {
      const m = paso.marcas[Number(k) - 1];
      if (!m) return "";
      return `<button type="button" class="cue cue--senal" data-pin="${m.num}" aria-label="Señalá la marca ${m.num}: ${esc(m.texto)}">` +
        `<span class="cue__num" aria-hidden="true">${m.num}</span>${esc(m.texto)}</button>`;
    });
    return h;
  }

  function pasoHTML(p) {
    const b = bloqueDe(p);
    const delBloque = G.pasos.filter((x) => x.bloque === p.bloque);
    let pase = "";
    if (b.pase && delBloque[delBloque.length - 1] === p) {
      const a = G.oradores[b.pase.a];
      pase = `<p class="pase" style="--pase-color:${esc(a.color)}"><span class="pase__a">Pase a <i>${esc(a.nombre)}</i></span>` +
        `<q>${esc(b.pase.frase)}</q></p>`;
    }
    return `<article class="paso" style="--color:${esc(colorDe(p))}" aria-label="${esc(b.etiqueta)}, ${esc(b.tema)}">` +
      `<header class="paso__cab"><span class="chip">${esc(b.etiqueta)}</span><span class="paso__tema">${esc(b.tema)}</span>` +
      `<span class="paso__tiempo">${reloj(p.inicio)} a ${reloj(p.inicio + p.segundos)} · ${p.segundos} s</span></header>` +
      (p.como ? `<p class="paso__como"><b>Cómo:</b> ${esc(p.como)}</p>` : "") +
      `<div class="paso__texto">${p.guion.map((l) => `<p>${textoConMarcas(l, p)}</p>`).join("")}</div>${pase}</article>`;
  }

  /* Debajo de la diapositiva: lo que sí o sí hay que tocar y los conceptos estadísticos, en una línea cada uno */
  function apoyoHTML(k) {
    const a = G.apoyo && G.apoyo[publico.diapositivas[k - 1].id];
    if (!a) return "";
    const conceptos = a.conceptos.length
      ? `<section class="apoyo__bloque" aria-labelledby="apoyo-con-${k}"><h4 class="apoyo__titulo" id="apoyo-con-${k}">Conceptos en esta diapositiva</h4>` +
        `<dl class="conceptos">${a.conceptos.map((c) => `<div class="concepto"><dt>${esc(c.nombre)}</dt><dd>${esc(c.texto)}</dd></div>`).join("")}</dl></section>`
      : "";
    return `<div class="apoyo"><section class="apoyo__bloque" aria-labelledby="apoyo-cla-${k}"><h4 class="apoyo__titulo" id="apoyo-cla-${k}">Puntos clave: hay que tocarlos sí o sí</h4>` +
      `<ol class="claves">${a.claves.map((c) => `<li>${esc(c)}</li>`).join("")}</ol></section>${conceptos}</div>`;
  }

  const pinHTML = (k, m) => `<span class="pin${m.centro ? "" : " pin--izq"}" data-pin="${m.num}" ` +
    `style="--x:${m.x};--y:${m.y};--color:${esc(colorDePin(k, m.num))}" title="${esc(textoDePin(k, m.num))}">${m.num}</span>`;

  function armar() {
    const ICONO = { ant: '<path d="M15 6l-6 6 6 6"/>', sig: '<path d="M9 6l6 6-6 6"/>' };
    const svg = (d) => `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">${d}</svg>`;
    seccion.innerHTML =
      `<h2 class="sr-only" tabindex="-1" data-foco>Guion de la exposición</h2>` +
      `<div class="guion__barra"><div class="segmentos" role="group" aria-label="Vista">` +
      `<button type="button" data-vista="presentador">Presentador</button><button type="button" data-vista="completo">Guion completo</button></div>` +
      `<p class="guion__total">${G.bloques.length} bloques · ${esc(G.duracion_texto)} en total · ${total} diapositivas</p></div>` +
      `<ol class="linea" aria-label="Orden de los oradores">` + G.bloques.map((b, i) =>
        `<li style="--peso:${b.segundos};--color:${esc(G.oradores[b.orador].color)}"><button type="button" data-bloque="${i}">` +
        `<span class="linea__nombre">${esc(b.etiqueta)}</span><span class="linea__tema">${esc(b.tema)}</span>` +
        `<span class="linea__tiempo">${reloj(b.inicio)} · dura ${reloj(b.segundos)}</span></button></li>`).join("") + `</ol>` +
      (G.leyenda && G.leyenda.length ? `<details class="leyenda" data-leyenda><summary>Cómo leer las marcas</summary><p class="leyenda__items">${G.leyenda.map((l) => {
        const [a, ...resto] = l.split(":");
        return `<span><b>${esc(a)}:</b>${esc(resto.join(":"))}</span>`;
      }).join("")}</p></details>` : "") +
      `<div class="presentador" data-panel="presentador"><div class="escenario">` +
      `<div class="escenario__marco"><iframe title="Vista previa de la diapositiva actual" src="${esc(publico.deck)}?modo=notas#${n}"></iframe>` +
      `<div class="pines" data-pines aria-hidden="true"></div></div>` +
      `<div class="escenario__controles"><button class="boton boton--icono" type="button" data-anterior aria-label="Diapositiva anterior">${svg(ICONO.ant)}</button>` +
      `<span class="contador" data-contador></span><button class="boton boton--icono" type="button" data-siguiente aria-label="Diapositiva siguiente">${svg(ICONO.sig)}</button>` +
      `<p class="escenario__sigue" data-sigue></p></div><div data-apoyo></div></div><div class="notas" data-notas></div></div>` +
      `<ol class="completo" data-panel="completo">` + publico.diapositivas.map((d, i) => {
        const k = i + 1;
        return `<li class="completo__item" id="g-${k}"><figure class="completo__diapo"><div class="completo__imagen">` +
          `<img src="${esc(d.imagen)}" alt="Diapositiva ${k}: ${esc(d.titulo)}" width="1280" height="720" loading="lazy" decoding="async">` +
          `${d.marcas.map((m) => pinHTML(k, m)).join("")}</div><figcaption class="completo__pie"><span><strong>${k}.</strong> ${esc(d.titulo)}</span>` +
          `<button class="boton" type="button" data-presentar-desde="${k}">Presentar desde acá</button></figcaption>${apoyoHTML(k)}</figure>` +
          `<div class="completo__notas">${pasosDe(k).map(pasoHTML).join("") || '<p class="paso__como">Esta diapositiva no tiene guion.</p>'}</div></li>`;
      }).join("") + `</ol>`;
    iframe = $("iframe", seccion);
    const leyenda = $("[data-leyenda]", seccion);
    if (leyenda && matchMedia("(min-width: 761px)").matches) leyenda.open = true;
    iframe.addEventListener("load", () => enviarAlIframe(n));
  }

  function pintarNotas() {
    const d = publico.diapositivas[n - 1];
    const pasos = pasosDe(n);
    $("[data-notas]").innerHTML =
      `<div class="notas__cabecera"><span class="notas__num">Diapositiva ${n} de ${total}</span><h3 class="notas__titulo">${esc(d.titulo)}</h3></div>` +
      (pasos.map(pasoHTML).join("") || '<p class="paso__como">Esta diapositiva no tiene guion.</p>');
    $("[data-apoyo]").innerHTML = apoyoHTML(n);
    $("[data-contador]").textContent = `${n} / ${total}`;
    $("[data-anterior]").disabled = n === 1;
    $("[data-siguiente]").disabled = n === total;
    const sig = pasosDe(n + 1)[0];
    $("[data-sigue]").innerHTML = n < total
      ? `Sigue: <strong>${esc(publico.diapositivas[n].titulo)}</strong>${sig ? ` · ${esc(bloqueDe(sig).etiqueta)}` : ""}`
      : "Es la última diapositiva.";
  }

  let temporizadorPines = 0;
  function pintarPines() {
    const caja = $("[data-pines]");
    caja.classList.remove("pines--listo");
    caja.innerHTML = publico.diapositivas[n - 1].marcas.map((m) => pinHTML(n, m)).join("");
    clearTimeout(temporizadorPines);
    // Las marcas aparecen cuando la diapositiva terminó de entrar en la vista previa
    temporizadorPines = setTimeout(() => caja.classList.add("pines--listo"), reducido ? 0 : 750);
  }

  function marcarLinea() {
    const actuales = new Set(pasosDe(n).map((p) => p.bloque));
    $$("[data-bloque]", seccion).forEach((b) => {
      if (actuales.has(Number(b.dataset.bloque))) b.setAttribute("aria-current", "step");
      else b.removeAttribute("aria-current");
    });
    const actual = $(`[data-bloque][aria-current="step"]`, seccion);
    if (actual && actual.scrollIntoView) actual.scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  function enviarAlIframe(k) {
    try { iframe.contentWindow.postMessage({ tipo: "pitch:ir", n: k }, location.origin); } catch (e) { /* todavía cargando */ }
  }

  function ir(k, origen) {
    k = Math.max(1, Math.min(total, Number(k) || 1));
    const cambio = k !== n;
    n = k;
    if (cambio || origen === "inicio") {
      pintarNotas();
      pintarPines();
      marcarLinea();
      pintarReloj();
      anuncio.textContent = `Diapositiva ${n} de ${total}: ${publico.diapositivas[n - 1].titulo}`;
      if (vista === "completo" && origen !== "inicio") {
        const item = document.getElementById(`g-${n}`);
        if (item) item.scrollIntoView({ behavior: reducido ? "auto" : "smooth", block: "start" });
      }
    }
    if (origen !== "iframe") enviarAlIframe(n);
    if (canal && origen !== "canal" && cambio) canal.postMessage({ tipo: "pitch:ir", n });
  }

  function cambiarVista(v) {
    vista = v;
    guardar(CLAVE.vista, v);
    $$("[data-vista]", seccion).forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.vista === v)));
    $$("[data-panel]", seccion).forEach((p) => { p.hidden = p.dataset.panel !== v; });
  }

  /* ── Reloj de la exposición (persiste si se recarga la página) ── */
  const R = { corriendo: false, inicio: 0, acumulado: 0, id: 0 };
  try { Object.assign(R, JSON.parse(leer(CLAVE.reloj) || "{}")); } catch (e) { /* reloj nuevo */ }
  const transcurrido = () => R.acumulado + (R.corriendo ? (Date.now() - R.inicio) / 1000 : 0);
  function pintarReloj() {
    if (!G) return;
    const t = transcurrido();
    $("[data-reloj]").textContent = reloj(t);
    const fin = Math.max(...pasosDe(n).map((p) => p.inicio + p.segundos), 0);
    $("[data-plan]").innerHTML = fin ? `plan ${reloj(fin)}<span class="reloj__total"> de ${esc(G.duracion_texto)}</span>` : "";
    const atraso = t - fin;
    $("[data-reloj-caja]").dataset.estado = (R.corriendo || t > 0) && fin ? (atraso > 30 ? "muy-tarde" : atraso > 0 ? "tarde" : "") : "";
    const boton = $("[data-reloj-boton]");
    boton.setAttribute("aria-pressed", String(R.corriendo));
    $("[data-reloj-texto]").textContent = R.corriendo ? "Pausar" : t > 0 ? "Seguir" : "Empezar";
    boton.querySelector("path").setAttribute("d", R.corriendo ? "M9 6v12M15 6v12" : "M8 5.5v13l10-6.5z");
  }
  function guardarReloj() { guardar(CLAVE.reloj, JSON.stringify({ corriendo: R.corriendo, inicio: R.inicio, acumulado: R.acumulado })); }
  function alternarReloj() {
    if (R.corriendo) { R.acumulado = transcurrido(); R.corriendo = false; } else { R.inicio = Date.now(); R.corriendo = true; }
    guardarReloj();
    pintarReloj();
  }
  setInterval(() => { if (R.corriendo) pintarReloj(); }, 500);

  function abrirGuion(datos, animar) {
    G = datos;
    armar();
    puerta.hidden = true;
    seccion.hidden = false;
    acciones.hidden = false;
    if (animar && !reducido) seccion.classList.add("guion--entra");
    cambiarVista(vista);
    ir(1, "inicio");
    $("[data-foco]", seccion).focus();
    if (canal) canal.postMessage({ tipo: "pitch:quien" }); // si el deck ya está abierto en otra pestaña, seguirlo

    seccion.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.dataset.vista) cambiarVista(b.dataset.vista);
      else if (b.dataset.bloque != null) ir(G.pasos.find((p) => p.bloque === Number(b.dataset.bloque)).n);
      else if (b.hasAttribute("data-anterior")) ir(n - 1);
      else if (b.hasAttribute("data-siguiente")) ir(n + 1);
      else if (b.dataset.presentarDesde) { cambiarVista("presentador"); ir(Number(b.dataset.presentarDesde)); window.scrollTo({ top: 0 }); }
      else if (b.dataset.pin) resaltar(b.dataset.pin, true);
    });
    const resaltar = (num, si) => $$(`.pines .pin[data-pin="${num}"]`, seccion).forEach((p) => p.classList.toggle("pin--activo", si));
    ["mouseover", "focusin"].forEach((ev) => seccion.addEventListener(ev, (e) => {
      const c = e.target.closest(".cue--senal");
      if (c) resaltar(c.dataset.pin, true);
    }));
    ["mouseout", "focusout"].forEach((ev) => seccion.addEventListener(ev, (e) => {
      const c = e.target.closest(".cue--senal");
      if (c) resaltar(c.dataset.pin, false);
    }));
  }

  /* Mensajes: la vista previa (postMessage) y otra pestaña con el deck, si la hay (BroadcastChannel) */
  window.addEventListener("message", (e) => {
    if (!G || e.origin !== location.origin || !e.data || e.data.tipo !== "pitch:diapo") return;
    if (iframe && e.source === iframe.contentWindow) ir(e.data.n, "iframe");
  });
  if (canal) canal.onmessage = (e) => {
    const m = e.data || {};
    if (G && m.tipo === "pitch:diapo") ir(m.n, "canal");
  };

  /* Teclado: ← → y Av/Re Pág cambian de diapositiva; T, reloj */
  document.addEventListener("keydown", (e) => {
    if (!G || e.altKey || e.ctrlKey || e.metaKey || e.defaultPrevented) return;
    if (e.target.closest("input, textarea, select")) return;
    const enControl = e.target.closest("button, a");
    const presentando = vista === "presentador";
    if (e.key === "ArrowRight" || (presentando && (e.key === "PageDown" || (e.key === " " && !enControl)))) { e.preventDefault(); ir(n + 1); }
    else if (e.key === "ArrowLeft" || (presentando && e.key === "PageUp")) { e.preventDefault(); ir(n - 1); }
    else if (presentando && e.key === "Home") { e.preventDefault(); ir(1); }
    else if (presentando && e.key === "End") { e.preventDefault(); ir(total); }
    else if (e.key === "t" || e.key === "T") { e.preventDefault(); alternarReloj(); }
  });

  $("[data-reloj-boton]").addEventListener("click", alternarReloj);
  $("[data-reloj-reiniciar]").addEventListener("click", () => {
    R.corriendo = false; R.acumulado = 0; R.inicio = 0;
    guardarReloj();
    pintarReloj();
  });
  // El código no se guarda en ningún lado: al refrescar la página hay que volver a ponerlo (pedido de Matías).
  $("[data-bloquear]").addEventListener("click", () => location.reload());
  if (matchMedia("(pointer: fine)").matches) casillas[0].focus();
})();
