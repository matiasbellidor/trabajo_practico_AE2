"""El pitch publicado en docs/presentacion/ (lo arma `python -m tp_ae2.pitch`): deck con la capa de mejoras y sus
números atados a resultados.json, video, PDF, Recursos con el guion cifrado y el panel de la landing.

Los tests del guion corren solo donde está guion/guion.yaml (no está en el repo: es lo que protege el código)."""

import base64
import json
import re

import pytest

from tp_ae2.config import RAIZ_REPO
from tp_ae2.pitch import construir, deck, guion
from tp_ae2.veredicto import num

PITCH = RAIZ_REPO / "docs" / "presentacion"
GUION = RAIZ_REPO / "guion" / "guion.yaml"
ORDEN_ORADORES = ["todos", "luka", "mati", "manu", "maria", "manu", "meli"]

pytestmark = pytest.mark.skipif(not (PITCH / "index.html").exists(),
                                reason="falta docs/presentacion: correr python -m tp_ae2.pitch")


@pytest.fixture(scope="module")
def publicado():
    return (PITCH / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def resultados():
    return json.loads((RAIZ_REPO / "outputs" / "resultados.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def recursos():
    return (PITCH / "recursos" / "index.html").read_text(encoding="utf-8")


def test_deck_con_la_capa_de_mejoras_una_sola_vez(publicado):
    for parte in ("estilos", "script", "config", "fondo", "herramientas"):
        assert publicado.count(f'id="{deck.MARCA}-{parte}"') == 1, parte
    assert '<source src="media/horizonte.webm" type="video/webm">' in publicado
    assert "autoplay" not in publicado.split(f'id="{deck.MARCA}-fondo"')[1].split("</video>")[0], \
        "el video arranca por script (respeta reducir movimiento y ahorro de datos)"
    herramientas = publicado.split(f'id="{deck.MARCA}-herramientas"')[1].split("</div>")[0]
    assert re.search(r'<a class="pitch-boton" href="\.\./" data-pitch-inicio[^>]*>.*?<span>Volver al inicio</span></a>',
                     herramientas), "botón chico para volver a la web del trabajo"


def test_orden_de_la_exposicion(publicado):
    ids = [d.id for d in deck.diapositivas(publicado)]
    assert ids == deck.ORDEN
    config = json.loads(re.search(r"window\.__PITCH__ = (\{.*?\});</script>", publicado).group(1))
    assert [d["id"] for d in config["diapositivas"]] == ids, "la capa y la app tienen que contar igual las diapositivas"


def test_correcciones_de_contenido_y_velocidad_de_graficos(publicado):
    for viejo, nuevo, _ in deck.CORRECCIONES + deck.OPTIMIZACIONES:
        assert viejo not in publicado and publicado.count(nuevo) == 1


def test_volver_al_inicio_no_aparece_en_pantalla_completa(publicado):
    estilos = publicado.split(f'id="{deck.MARCA}-estilos"')[1].split("</style>")[0]
    for control in (".pitch-herramientas", ".nav", ".edge", ".hint", ".fab"):
        assert f":root:fullscreen {control}" in estilos, control
    assert "display: none !important" in estilos


def test_recursos_siempre_dice_volver_al_inicio(recursos):
    cab = re.search(r'<a class="cab__volver" href="([^"]*)"[^>]*>.*?<span>(.*?)</span></a>', recursos, re.S)
    assert cab and cab.group(1) == "../../" and cab.group(2) == "Volver al inicio", \
        "Recursos vuelve a la web del trabajo, no a la presentación"


def test_recursos_no_abre_otra_pestana(recursos):
    assert "data-proyectar" not in recursos and "window.open" not in recursos


def test_recursos_no_recuerda_el_codigo(recursos):
    assert "recursos-codigo" not in recursos and "CLAVE.codigo" not in recursos, "el código no se guarda en el navegador"


def test_numeros_del_deck_coinciden_con_resultados(publicado, resultados):
    """El deck se hizo aparte del pipeline: si cambian los resultados, este test avisa qué número quedó viejo."""
    hp, e = resultados["hipotesis_principal"]["d0"], resultados["estimadores"]
    rm, an = resultados["regresion_multiple"], resultados["anova"]
    pc = resultados["prueba_complementaria"]["decision"]
    coef = {c["nombre"]: c for c in rm["coeficientes"]}
    trim = resultados["robustez_trimestral"]["bateria_respaldo"]["hipotesis_principal"]["d0"]
    infl = resultados["robustez_trimestral"]["influencia"]
    n, n_trim = resultados["muestra"]["principal"]["n"], resultados["muestra"]["respaldo"]["n"]
    esperados = [
        f"{num(hp['b1'])}", f"p = {num(hp['p_b1'])} (ampliamente superior a 0,05)",
        f"R² = {num(hp['r2'])} con n = {n}",
        f"[{num(hp['ic_b1']['inferior'])} ; {num(hp['ic_b1']['superior'])}]",
        f"Media mensual: {num(e['var_bono']['media'])} %", f"Media mensual: {num(e['var_pbi']['media'])} %",
        f"Relación de desvíos estándar: {num(e['var_bono']['desvio'])} % frente a {num(e['var_pbi']['desvio'])} % mensual.",
        f"unas {round(e['var_bono']['desvio'] / e['var_pbi']['desvio'])} veces más volatilidad",
        f"R² = {num(rm['r2'])}", f"p = {num(rm['p_f'])}", f"p(PBI) = {num(coef['var_pbi']['p_valor'])}",
        f"F = {num(an['f'])}", f"p = {num(an['p_valor'])}",
        f"Dif = {num(pc['diferencia'])} pp", f"p = {num(pc['p_valor'])}",
        f" = {num(trim['b1'])} · p = {num(trim['p_b1'])} · R² = {num(trim['r2'])}",
        f"el p-valor sube a `,(0,$.jsx)(`b`,{{children:`{num(infl['p_sin_max'])}`",
        f"n = {n} observaciones", f"n = {n_trim}",
    ]
    faltan = [x for x in esperados if x not in publicado]
    assert not faltan, f"El deck no tiene estos valores de resultados.json: {faltan}"
    # Los dos desvíos grandes de la diapositiva de estadística descriptiva son contadores animados
    for x in (e["var_bono"]["desvio"], e["var_pbi"]["desvio"]):
        assert f"value:{round(x, 2):g}".replace("value:0.", "value:.") in publicado


def test_video_poster_y_miniaturas():
    webm = (PITCH / "media" / "horizonte.webm").read_bytes()
    assert webm[:4] == b"\x1a\x45\xdf\xa3" and len(webm) < 1_000_000, "WebM liviano (es un fondo)"
    assert (PITCH / "media" / "horizonte.webp").stat().st_size < 100_000
    for i in range(1, len(deck.ORDEN) + 1):
        assert (PITCH / "media" / f"diapo-{i:02d}.webp").exists()


def test_pdf_una_pagina_por_diapositiva():
    datos = (PITCH / construir.PDF_NOMBRE).read_bytes()
    assert datos.startswith(b"%PDF-") and datos.rstrip().endswith(b"%%EOF")
    assert len(re.findall(rb"/Type /Page\b(?!s)", datos)) == len(deck.ORDEN)


def test_recursos_pide_tres_casillas_y_no_muestra_el_guion(recursos):
    casillas = re.findall(r'<input class="codigo__casilla"[^>]*>', recursos)
    assert len(casillas) == 3, "tres casillas separadas, no un campo único"
    for c in casillas:
        assert 'inputmode="numeric"' in c and 'maxlength="1"' in c and 'autocomplete="off"' in c
    cifrado = json.loads(re.search(r'<script type="application/json" id="guion-cifrado">(.*?)</script>', recursos).group(1))
    assert cifrado["cifrado"] == "AES-GCM-256" and cifrado["iteraciones"] >= 100_000
    assert len(base64.b64decode(cifrado["datos"])) > 1000
    for frase in ("Somos el Grupo", "contales vos", "propuso Mati", "Luka Santino"):
        assert frase not in recursos, f"«{frase}» quedó en texto plano"
    assert 'name="robots" content="noindex' in recursos


def test_landing_tiene_el_boton_y_las_tres_acciones():
    landing = (RAIZ_REPO / "docs" / "index.html").read_text(encoding="utf-8")
    assert re.search(r'<button class="cta-pres[^"]*" type="button" popovertarget="menu-presentacion"', landing)
    menu = landing.split('id="menu-presentacion"')[1].split("</ul>")[0]
    hrefs = re.findall(r'<a class="accion[^"]*" href="([^"]+)"', menu)
    assert hrefs == ["presentacion/presentacion-tp-ae2.pdf", "presentacion/?presentar=1", "presentacion/recursos/"]
    assert re.search(r'href="presentacion/presentacion-tp-ae2\.pdf" download', menu)
    for accion in ("Descargar PDF", "Ver presentación", "Recursos"):
        assert f"<strong>{accion}</strong>" in menu


@pytest.fixture(scope="module")
def armado(publicado, resultados):
    diapos = deck.diapositivas(publicado)
    return guion.armar(guion.cargar(GUION), resultados, [d.id for d in diapos], {d.id: d.titulo for d in diapos})


@pytest.mark.skipif(not GUION.exists(), reason="guion/guion.yaml no está en el repo (se publica cifrado)")
class TestGuion:

    def test_orden_y_asignacion_de_oradores(self, armado):
        assert [b["orador"] for b in armado["bloques"]] == ORDEN_ORADORES
        etiquetas = [b["etiqueta"] for b in armado["bloques"]]
        assert etiquetas[3] == "Manu (1/2)" and etiquetas[5] == "Manu (2/2)", "las dos partes de Manu, rotuladas"
        temas = " | ".join(b["tema"].lower() for b in armado["bloques"])
        for tema in ("hipótesis", "metodología", "estimador", "intervalo de confianza", "bondad de ajuste",
                     "regresión lineal múltiple", "anova", "conclusiones"):
            assert tema in temas, tema

    def test_apertura_con_hola_y_pases_entre_oradores(self, armado):
        apertura = armado["pasos"][0]
        assert armado["bloques"][apertura["bloque"]]["orador"] == "todos" and "Hola" in " ".join(apertura["guion"])
        for b, siguiente in zip(armado["bloques"][1:], armado["bloques"][2:]):
            assert b["pase"] and b["pase"]["a"] == siguiente["orador"], f"{b['etiqueta']} tiene que pasarle a {siguiente['orador']}"

    def test_cada_orador_tiene_pausas_enfasis_y_tiempos(self, armado):
        for i, b in enumerate(armado["bloques"][1:], start=1):
            texto = " ".join(" ".join(p["guion"]) for p in armado["pasos"] if p["bloque"] == i)
            assert re.search(r"\[pausa \d+s\]", texto), f"{b['etiqueta']}: sin pausas"
            assert "**" in texto, f"{b['etiqueta']}: sin énfasis"
            assert b["segundos"] > 0
        assert armado["duracion"] == sum(p["segundos"] for p in armado["pasos"])

    def test_maria_explica_el_ccl_como_decision(self, armado):
        maria = " ".join(" ".join(p["guion"]) for p in armado["pasos"] if armado["bloques"][p["bloque"]]["orador"] == "maria")
        assert "CCL" in maria and "Mati" in maria and "antes de ver" in maria

    def test_numeros_del_guion_salen_de_resultados(self, armado, resultados):
        hp = resultados["hipotesis_principal"]["d0"]
        texto = json.dumps(armado, ensure_ascii=False)
        for valor in (num(hp["b1"]), num(hp["p_b1"]), num(resultados["anova"]["f"]),
                      num(resultados["prueba_complementaria"]["decision"]["p_valor"])):
            assert valor in texto
        assert not re.search(r"\{\{\s*\w+\s*\}\}", texto), "quedó una variable de Jinja sin reemplazar"

    def test_cada_diapositiva_tiene_puntos_clave_y_los_conceptos_estan_explicados(self, armado, publicado):
        ids = [d.id for d in deck.diapositivas(publicado)]
        assert list(armado["apoyo"]) == ids, "una entrada por diapositiva, en el orden del deck"
        for d, a in armado["apoyo"].items():
            assert a["claves"], f"{d}: sin puntos clave"
            for c in a["conceptos"]:
                assert c["nombre"] and len(c["texto"]) <= 190, f"{d}/{c['nombre']}: el concepto va en una o dos líneas"
        con_conceptos = {d for d, a in armado["apoyo"].items() if a["conceptos"]}
        assert {"hipotesis", "descriptiva", "mco", "sensibilidad"} <= con_conceptos

    def test_recursos_esta_al_dia_con_el_guion(self, armado, recursos):
        sal, iv = construir.sal_e_iv(construir.texto_del_guion(armado))
        cifrado = json.loads(re.search(r'id="guion-cifrado">(.*?)</script>', recursos).group(1))
        assert cifrado["sal"] == base64.b64encode(sal).decode() and cifrado["iv"] == base64.b64encode(iv).decode(), \
            "Recursos está desactualizado: correr python -m tp_ae2.pitch"
