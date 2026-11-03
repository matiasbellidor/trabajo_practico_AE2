"""Verificación de la presentación web en un navegador real (Playwright + Chromium).

Uso: python .claude/skills/tp-web-design/scripts/verificar_web.py docs/index.html <carpeta_de_capturas>

Comprueba:
  1. Sin desborde horizontal de página de 320 a 1920 px, en tema claro y oscuro (los contenedores con scroll
     propio, como tablas y figuras, quedan exceptuados).
  2. Navegación: al saltar a cada sección con el riel, la barra, el riel y el índice marcan esa sección.
  3. El índice abre, marca la sección actual y cierra con Esc.
  4. Un salto largo de scroll muestra "Volver a…" y el botón devuelve a la sección de origen; el hash se actualiza.
  5. Con movimiento reducido nada queda oculto (títulos con opacidad 1 y trazo de portada dibujado).
  6. Sin errores de consola.
Guarda capturas con barras de scroll visibles (Chromium headless las esconde por defecto) y las animaciones
terminadas, para mirarlas una por una.
Sale con código 1 si algún chequeo falla.
"""
import sys
from pathlib import Path

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


def main(html: Path, salida: Path) -> int:
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
        ocultos = pg.evaluate("""() => [...document.querySelectorAll('.diapo h1, .diapo h2, .revela')]
            .filter(e => getComputedStyle(e).opacity !== '1').length""")
        trazo = pg.evaluate("""() => [...document.querySelectorAll('.trazo__linea')]
            .map(e => getComputedStyle(e).strokeDashoffset)""")
        if ocultos:
            fallas.append(f"movimiento reducido: {ocultos} elementos con opacidad distinta de 1")
        if any(v not in ("0", "0px") for v in trazo):
            fallas.append(f"movimiento reducido: trazo sin dibujar {trazo}")
        pg.close()
        nav.close()

    if errores:
        fallas.append(f"errores de consola: {errores[:5]}")
    for f in fallas:
        print("FALLA:", f)
    print(f"{'OK' if not fallas else 'CON FALLAS'} · capturas en {salida}")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
