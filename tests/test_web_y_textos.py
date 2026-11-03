"""(8) El HTML no hace pedidos externos; textos sin lenguaje causal; README y conclusión."""

import re

import pytest

from tp_ae2 import presentacion, reporte, textos
from tp_ae2.config import RAIZ_REPO

SVG_FALSO = '<svg viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>'
CAUSAL = re.compile(r"\bimpact\w*|\bprovoc\w*|se comprueba|comprueba que|\bcausa\b|\bcausó\b", re.I)
PROHIBIDO = "".join(("E", "M", "A", "E"))  # indicador que la cátedra pidió no usar


FIGURAS = [{"id": f, "titulo": f"Figura {f}", "alt": "texto alternativo", "svg": f"{f}.svg"}
           for f in ("series", "pbi", "histogramas", "dispersion", "desfases", "residuos", "anova", "robustez",
                     "complementaria")]


def _renderizar(corrida, conclusion=None):
    resultados, extras = corrida
    panel = extras["principal"]["panel"].reset_index().assign(periodo=lambda d: d["periodo"].astype(str))
    filas = panel[["periodo", "var_pbi", "var_bono", "grupo_bono", "tercil_pbi"]].to_dict(orient="records")
    return presentacion.renderizar(resultados, FIGURAS, {f["id"]: SVG_FALSO for f in FIGURAS}, filas, conclusion,
                                   "12/11/2026")


@pytest.fixture(scope="module")
def html_generado(corrida):
    return _renderizar(corrida)


def _sin_pedidos_externos(contenido: str) -> None:
    assert not re.search(r"<script[^>]+src=", contenido, re.I)
    assert not re.search(r"<link[^>]+href=[\"']https?:", contenido, re.I)
    assert not re.search(r"<(img|iframe|source|video|audio|embed)[^>]+src=[\"']https?:", contenido, re.I)
    assert not re.search(r"url\(\s*[\"']?https?:", contenido, re.I)
    assert "@import" not in contenido


def test_html_sin_pedidos_externos(html_generado):
    _sin_pedidos_externos(html_generado)
    assert '<html lang="es-AR">' in html_generado
    assert "Conclusión final pendiente" in html_generado


def test_html_publicado_sin_pedidos_externos():
    ruta = RAIZ_REPO / "docs" / "index.html"
    if not ruta.exists():
        pytest.skip("docs/index.html todavía no se generó")
    contenido = ruta.read_text(encoding="utf-8")
    _sin_pedidos_externos(contenido)
    assert len(re.findall(r'<section class="diapo', contenido)) == 14
    ids = re.findall(r'\sid="([^"]+)"', contenido)
    assert len(ids) == len(set(ids)), "IDs duplicados en el HTML"


def test_html_usa_conclusion_si_existe(corrida):
    con = _renderizar(corrida, "## Cierre\n\nTexto **final** de prueba.\n\n- punto uno")
    assert "<strong>final</strong>" in con and "<li>punto uno</li>" in con
    assert "Conclusión final pendiente" not in con


def test_textos_sin_lenguaje_causal(corrida, html_generado):
    resultados, extras = corrida
    t = textos.construir(resultados)
    generados = [html_generado, reporte.cuerpo_informe(resultados, t),
                 reporte.resumen_para_conclusion(resultados, t, extras), reporte.bloque_readme(resultados)]
    for contenido in generados:
        assert not CAUSAL.search(contenido), CAUSAL.search(contenido)
        assert PROHIBIDO not in contenido


def test_archivos_publicados_sin_dato_prohibido():
    carpetas = ["src", "outputs", "docs", "reports", "data"]
    archivos = [RAIZ_REPO / "README.md", RAIZ_REPO / "config.yaml"]
    for carpeta in carpetas:
        archivos += [p for p in (RAIZ_REPO / carpeta).rglob("*") if p.is_file() and p.suffix in
                     (".py", ".md", ".json", ".csv", ".html", ".j2", ".css", ".js", ".yaml", ".svg")]
    for archivo in archivos:
        assert PROHIBIDO not in archivo.read_text(encoding="utf-8", errors="ignore"), archivo


def test_readme_tiene_marcas_y_menciones():
    readme = (RAIZ_REPO / "README.md").read_text(encoding="utf-8")
    assert reporte.MARCA_INICIO in readme and reporte.MARCA_FIN in readme
    assert "Análisis Estadístico 2" in readme and "Tito Lasanta" in readme
    assert not CAUSAL.search(readme)


def test_informe_sin_conclusion_escrita(corrida):
    resultados, _ = corrida
    informe = reporte.cuerpo_informe(resultados, textos.construir(resultados))
    assert informe.rstrip().endswith("## 8. Conclusión (se redacta aparte)")
