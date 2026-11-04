"""Verificación de la presentación web en un navegador real (Playwright + Chromium).

Uso: python .claude/skills/tp-web-design/scripts/verificar_web.py docs/index.html <carpeta> [--rendimiento] [--fotogramas]

Comprueba:
  1. Sin desborde horizontal de página de 320 a 1920 px, en tema claro y oscuro (los contenedores con scroll
     propio, como tablas y figuras, quedan exceptuados).
  2. Navegación: al saltar a cada sección con el riel, la barra, el riel y el índice marcan esa sección.
  3. El índice abre, marca la sección actual y cierra con Esc.
  4. Un salto largo de scroll muestra "Volver a…" y el botón devuelve a la sección de origen; el hash se actualiza.
  5. Con movimiento reducido nada queda oculto (títulos, palabras de la portada, elementos de las figuras con
     opacidad 1 y trazo de portada dibujado).
  6. Sin errores de consola.
Guarda capturas con barras de scroll visibles (Chromium headless las esconde por defecto) y las animaciones
terminadas, para mirarlas una por una.

--rendimiento (motion de las figuras), con la CPU 4 veces más lenta:
  7. Por figura, mientras se arma: ningún cuadro de más de 50 ms, p95 de cuadros <= 33 ms, como mucho 1 tarea larga.
  8. Con movimiento reducido, al emular impresión y en modo impresión: cada elemento .m (salvo los decorativos,
     cursor y anillos, que solo existen mientras se arma) con opacidad 1, sin dash y sin animaciones corriendo.
  9. La figura terminada es idéntica, píxel por píxel, a la figura quieta (movimiento reducido). Las dos capturas se
     toman con la página asentada: Chromium vuelve a rasterizar con más calidad un momento después del scroll.
--fotogramas: congela cada figura al 30, 60 y 100 % en claro y oscuro, a 390 y 1440 px, y arma una hoja de contacto
  por figura (fotogramas/hoja_<id>.png) para mirarla.
Sale con código 1 si algún chequeo falla.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import sync_playwright

TIEMPO_MAX = 15000  # ms por espera; ningún chequeo puede colgarse
ANCHOS = [(320, 640), (390, 844), (768, 1024), (1024, 720), (1280, 720), (1440, 900), (1920, 1080)]
CAPTURAS = {390: ("portada", "datos", "conclusion"), 1440: ("portada", "datos", "robustez", "conclusion")}

DESBORDE = """() => {
  const w = document.documentElement.clientWidth;
  const exceptuados = '.tabla-scroll, .figura__lienzo, .formula, .indice, .riel';
  const malos = [...document.querySelectorAll('body *')].filter(e => {
    if (e.closest(exceptuados)) return false;
    const r = e.getBoundingClientRect();
    return r.width > 0 && (r.right > w + 1 || r.left < -1);
  }).slice(0, 5).map(e => e.tagName + '.' + (e.className.baseVal ?? e.className));
  return {scroll: document.documentElement.scrollWidth - w, malos};
}"""

ESTADO = """() => ({
  num: document.querySelector('[data-seccion-num]').textContent,
  riel: [...document.querySelectorAll('.riel a')].findIndex(a => a.getAttribute('aria-current') === 'true'),
  indice: [...document.querySelectorAll('.indice a')].findIndex(a => a.getAttribute('aria-current') === 'true'),
  hash: location.hash,
  volver: !document.querySelector('[data-volver]').hidden,
  destino: document.querySelector('[data-volver-destino]').textContent,
})"""


def main(html: Path, salida: Path, rendimiento: bool = False, fotogramas: bool = False) -> int:
    salida.mkdir(parents=True, exist_ok=True)
    url = html.resolve().as_uri()
    fallas: list[str] = []
    errores: list[str] = []

    with sync_playwright() as p:
        nav = p.chromium.launch(ignore_default_args=["--hide-scrollbars"])

        def pagina(ancho, alto, tema="light", movimiento="no-preference"):
            pg = nav.new_page(viewport={"width": ancho, "height": alto}, color_scheme=tema, reduced_motion=movimiento)
            pg.set_default_timeout(TIEMPO_MAX)
            pg.on("console", lambda m: errores.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: errores.append(str(e)))
            pg.goto(url)
            pg.wait_for_load_state("load")
            return pg

        # 1. Desborde y capturas
        for ancho, alto in ANCHOS:
            for tema in ("light", "dark"):
                pg = pagina(ancho, alto, tema)
                d = pg.evaluate(DESBORDE)
                if d["scroll"] > 0 or d["malos"]:
                    fallas.append(f"desborde {ancho}px {tema}: {d}")
                if tema == "light" and ancho in CAPTURAS:
                    for sid in CAPTURAS[ancho]:
                        pg.evaluate(f"document.getElementById('{sid}').scrollIntoView({{behavior: 'instant'}})")
                        pg.wait_for_timeout(250)
                        pg.evaluate("document.getAnimations().forEach(a => { try { a.finish() } catch (e) {} })")
                        pg.screenshot(path=str(salida / f"{sid}_{ancho}.png"))
                pg.close()

        # 2 a 4. Navegación, índice, "Volver a…" y hash (escritorio)
        pg = pagina(1440, 900)
        enlaces = pg.locator(".riel a")
        for i in (1, 6, 12):
            enlaces.nth(i).click()
            pg.wait_for_function(f"document.querySelector('[data-seccion-num]').textContent === '{i + 1:02d}'")
            e = pg.evaluate(ESTADO)
            if (e["riel"], e["indice"]) != (i, i):
                fallas.append(f"riel/índice no marcan la sección {i}: {e}")
            if e["volver"]:
                fallas.append(f"'Volver' apareció en un salto intencional a {i}")
        pg.locator("[data-indice-boton]").click()
        if not pg.evaluate("document.getElementById('indice').matches(':popover-open')"):
            fallas.append("el índice no abre")
        pg.keyboard.press("Escape")
        if pg.evaluate("document.getElementById('indice').matches(':popover-open')"):
            fallas.append("el índice no cierra con Esc")

        pg.evaluate("document.getElementById('hipotesis').scrollIntoView({behavior: 'instant'})")
        pg.wait_for_function("location.hash === '#hipotesis'")  # se asentó (1,2 s) y escribió el hash
        pg.evaluate("document.getElementById('anova').scrollIntoView({behavior: 'instant'})")
        pg.wait_for_function("!document.querySelector('[data-volver]').hidden")
        e = pg.evaluate(ESTADO)
        if not e["destino"].startswith("02"):
            fallas.append(f"'Volver' apunta a otra sección: {e}")
        pg.evaluate("document.getAnimations().forEach(a => { try { a.finish() } catch (e) {} })")
        pg.screenshot(path=str(salida / "volver_1440.png"))
        pg.locator("[data-volver-ir]").click()
        pg.wait_for_function("document.querySelector('[data-seccion-num]').textContent === '02'")
        if pg.evaluate(ESTADO)["volver"]:
            fallas.append("'Volver' sigue visible después de usarlo")
        pg.close()

        # Índice abierto en celular, para mirarlo
        pg = pagina(390, 844)
        pg.locator("[data-indice-boton]").click()
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(salida / "indice_390.png"))
        pg.close()

        # 5. Movimiento reducido
        pg = pagina(1440, 900, movimiento="reduce")
        ocultos = pg.evaluate("""() => [...document.querySelectorAll('.diapo h1, .diapo h2, .revela, .pal, .figura .m:not(.m--deco)')]
            .filter(e => getComputedStyle(e).opacity !== '1').length""")
        trazo = pg.evaluate("""() => [...document.querySelectorAll('.trazo__linea')]
            .map(e => getComputedStyle(e).strokeDashoffset)""")
        if ocultos:
            fallas.append(f"movimiento reducido: {ocultos} elementos con opacidad distinta de 1")
        if any(v not in ("0", "0px") for v in trazo):
            fallas.append(f"movimiento reducido: trazo sin dibujar {trazo}")
        pg.close()

        if rendimiento:
            fallas += _rendimiento(nav, url, salida)
        if fotogramas:
            _fotogramas(nav, url, salida / "fotogramas")
        nav.close()

    if errores:
        fallas.append(f"errores de consola: {errores[:5]}")
    for f in fallas:
        print("FALLA:", f)
    print(f"{'OK' if not fallas else 'CON FALLAS'} · capturas en {salida}")
    return 1 if fallas else 0


# --- Motion de las figuras ----------------------------------------------------------------------
IDS = "() => [...document.querySelectorAll('.figura[data-anim]')].map(f => f.dataset.anim)"
TAREAS_LARGAS = """window.__largas = [];
try { new PerformanceObserver(l => l.getEntries().forEach(e => window.__largas.push([e.startTime, e.duration])))
  .observe({type: 'longtask', buffered: true}); } catch (e) {}"""
# Cuadros (deltas de requestAnimationFrame) y tareas largas desde que la figura se pone .anima hasta que termina.
MEDIR = """(fid) => new Promise(resolve => {
  const fig = document.getElementById('fig-' + fid);
  const deltas = []; let previo = null, inicio = null;
  const tope = setTimeout(() => resolve({error: 'la figura no terminó'}), 20000);
  function cuadro(t) {
    if (fig.classList.contains('anima')) {
      if (inicio === null) inicio = performance.now(); else deltas.push(t - previo);
      previo = t;
    } else if (inicio !== null) {
      clearTimeout(tope);
      const fin = performance.now();
      resolve({deltas, largas: window.__largas.filter(([s, d]) => s + d >= inicio && s <= fin).map(([s, d]) => d)});
      return;
    }
    requestAnimationFrame(cuadro);
  }
  requestAnimationFrame(cuadro);
  fig.scrollIntoView({block: 'center', behavior: 'instant'});
})"""
QUIETO = """() => {
  const els = [...document.querySelectorAll('.figura .m:not(.m--deco), .pal')];
  const vivas = [...document.querySelectorAll('.figura')].flatMap(f => f.getAnimations({subtree: true}))
    .filter(a => a.playState === 'running' && a.effect.target.matches('.m, .lectura')).length;
  return {ocultos: els.filter(e => getComputedStyle(e).opacity !== '1').length,
          dash: [...document.querySelectorAll('.figura .m--trazo')].filter(e => getComputedStyle(e).strokeDasharray !== 'none').length,
          vivas, total: els.length};
}"""
ASENTAR_MS = 2500


def _rendimiento(nav, url: str, salida: Path) -> list[str]:
    fallas: list[str] = []
    pg = nav.new_page(viewport={"width": 1440, "height": 900})
    pg.goto(url)
    ids = pg.evaluate(IDS)
    pg.close()

    # 7. Cuadros y tareas largas con la CPU 4× más lenta
    print(f"{'figura':<15}{'cuadros':>8}{'máx ms':>9}{'p95 ms':>9}{'tareas largas':>15}")
    for fid in ids:
        pg = nav.new_page(viewport={"width": 1440, "height": 900})
        pg.add_init_script(TAREAS_LARGAS)
        pg.goto(url)
        pg.wait_for_timeout(800)
        cdp = pg.context.new_cdp_session(pg)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
        pg.wait_for_timeout(300)
        r = pg.evaluate(MEDIR, fid)
        pg.close()
        if "error" in r:
            fallas.append(f"rendimiento {fid}: {r['error']}")
            continue
        d = sorted(r["deltas"])
        p95 = d[max(0, math.ceil(0.95 * len(d)) - 1)]
        print(f"{fid:<15}{len(d):>8}{d[-1]:>9.1f}{p95:>9.1f}{len(r['largas']):>15}")
        if d[-1] > 50 or p95 > 33 or len(r["largas"]) > 1:
            fallas.append(f"rendimiento {fid}: máx {d[-1]:.1f} ms, p95 {p95:.1f} ms, {len(r['largas'])} tareas largas")

    # 8. Quieto con movimiento reducido, al emular impresión y en modo impresión
    for caso in ("movimiento reducido", "impresión", "modo impresión"):
        pg = nav.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce" if caso == "movimiento reducido" else "no-preference")
        pg.goto(url)
        if caso == "impresión":
            pg.emulate_media(media="print")
        if caso == "modo impresión":
            pg.evaluate("window.tpPrepararImpresion()")
        pg.wait_for_timeout(300)
        q = pg.evaluate(QUIETO)
        if q["ocultos"] or q["dash"] or q["vivas"]:
            fallas.append(f"{caso}: {q}")
        pg.close()

    # 9. Terminada = quieta, píxel por píxel
    def captura(fid, movimiento):
        pg = nav.new_page(viewport={"width": 1440, "height": 900}, reduced_motion=movimiento)
        pg.goto(url)
        pg.evaluate(f"document.getElementById('fig-{fid}').scrollIntoView({{block: 'center', behavior: 'instant'}})")
        if movimiento == "no-preference":
            pg.wait_for_function(f"document.getElementById('fig-{fid}').classList.contains('lista')", timeout=15000)
        pg.wait_for_timeout(ASENTAR_MS)
        ruta = salida / f"pixel_{fid}_{movimiento}.png"
        pg.locator(f"#fig-{fid} .figura__lienzo > svg").screenshot(path=str(ruta))
        pg.close()
        return Image.open(ruta).convert("RGB")

    for fid in ids:
        quieta, terminada = captura(fid, "reduce"), captura(fid, "no-preference")
        caja = None if quieta.size != terminada.size else ImageChops.difference(quieta, terminada).getbbox()
        if quieta.size != terminada.size or caja:
            fallas.append(f"{fid}: la figura terminada no es idéntica a la quieta (zona {caja})")
    print(f"píxel por píxel: {len(ids)} figuras comparadas")
    return fallas


FRACCIONES = (0.3, 0.6, 1.0)
VISTAS = [(1440, 900, "light"), (1440, 900, "dark"), (390, 844, "light"), (390, 844, "dark")]
# Repite la figura y la congela en el instante t. Se usa con la página asentada, así el fotograma se ve como en vivo.
CONGELAR = """([fid, t, repetir]) => {
  const fig = document.getElementById('fig-' + fid);
  if (repetir) fig.querySelector('.figura__repetir').click();
  clearTimeout(fig._fin);
  fig.getAnimations({subtree: true}).forEach(a => { if (a.effect.target === fig) return; a.pause(); a.currentTime = t; });
}"""


def _fotogramas(nav, url: str, salida: Path) -> None:
    salida.mkdir(parents=True, exist_ok=True)
    ids = []
    for ancho, alto, tema in VISTAS:
        pg = nav.new_page(viewport={"width": ancho, "height": alto}, color_scheme=tema)
        pg.goto(url)
        ids = pg.evaluate(IDS)
        for fid in ids:
            pg.evaluate(f"document.getElementById('fig-{fid}').scrollIntoView({{block: 'center', behavior: 'instant'}})")
            pg.wait_for_function(f"document.getElementById('fig-{fid}').classList.contains('lista')", timeout=15000)
            pg.wait_for_timeout(ASENTAR_MS)
            dur = pg.evaluate(f"Number(document.getElementById('fig-{fid}').dataset.dur)")
            for k, fr in enumerate(FRACCIONES):
                pg.evaluate(CONGELAR, [fid, fr * dur, k == 0])
                pg.wait_for_timeout(150)
                pg.locator(f"#fig-{fid}").screenshot(path=str(salida / f"{fid}_{ancho}_{tema}_{int(fr * 100)}.png"))
        pg.close()
    col = 620
    for fid in ids:
        filas = [[Image.open(salida / f"{fid}_{a}_{t}_{int(fr * 100)}.png") for fr in FRACCIONES] for a, _, t in VISTAS]
        altos = [max(int(i.height * col / i.width) for i in fila) for fila in filas]
        hoja = Image.new("RGB", (col * 3 + 40, sum(altos) + 30 * len(filas)), "white")
        dibujo, y = ImageDraw.Draw(hoja), 0
        for fila, h, (ancho, _, tema) in zip(filas, altos, VISTAS):
            dibujo.text((6, y + 6), f"{fid} · {ancho}px {tema} · 30 % / 60 % / 100 %", fill="black")
            y += 22
            for c, img in enumerate(fila):
                hoja.paste(img.resize((col, int(img.height * col / img.width))), (10 + c * (col + 10), y))
            y += h + 8
        hoja.save(salida / f"hoja_{fid}.png")
    print(f"fotogramas: {len(ids)} hojas de contacto en {salida}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(main(Path(args[0]), Path(args[1]), "--rendimiento" in sys.argv, "--fotogramas" in sys.argv))
