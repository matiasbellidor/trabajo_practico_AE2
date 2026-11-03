"""Pipeline completo: datos → análisis → tablas → figuras → informe → web → README.

Uso: python -m tp_ae2.run_all --config config.yaml
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import analisis, graficos, io_datos, presentacion, reporte, textos
from .config import Config, cargar_config

log = logging.getLogger("tp_ae2")


def ejecutar(cfg: Config) -> dict:
    salidas = cfg.ruta("salidas")
    log.info("Fase 0 · verificación de archivos y linaje")
    io_datos.verificar_obligatorios(cfg)
    linaje = io_datos.linaje(cfg)
    reporte.escribir_json(salidas / "linaje_datos.json", linaje)

    resultados, extras = analisis.ejecutar(cfg, linaje)
    reporte.escribir_json(salidas / "resultados.json", resultados)

    log.info("Fase 3 · tablas y figuras")
    reporte.escribir_tablas(reporte.construir_tablas(resultados, extras), salidas / "tablas",
                            salidas / "TP_AE2_tablas.xlsx")
    figuras = graficos.generar(resultados, extras, salidas / "figuras", salidas / "figuras" / "web")
    reporte.escribir_json(salidas / "figuras" / "figuras.json", figuras)

    log.info("Fase 4 · informe, resumen, web y README")
    t = textos.construir(resultados)
    conclusion = reporte.leer_conclusion(cfg.ruta("conclusion"))
    reporte.escribir_texto(cfg.ruta("informe"), reporte.cuerpo_informe(resultados, t, conclusion))
    reporte.escribir_texto(salidas / "resumen_para_conclusion.md", reporte.resumen_para_conclusion(resultados, t, extras))
    reporte.escribir_texto(salidas / "reconciliacion_borrador_previo.md", reporte.reconciliacion(resultados, extras))
    presentacion.generar(cfg)
    if cfg.ruta("readme").exists():
        reporte.inyectar_readme(cfg.ruta("readme"), reporte.bloque_resumen_readme(resultados),
                                (reporte.MARCA_RESUMEN_INICIO, reporte.MARCA_RESUMEN_FIN))
        reporte.inyectar_readme(cfg.ruta("readme"), reporte.bloque_readme(resultados))

    log.info("Listo. %s", resultados["veredictos"]["hipotesis_principal"])
    return resultados


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenera todo el TP de Análisis Estadístico 2")
    parser.add_argument("--config", default=None, help="Ruta a config.yaml (por defecto, la del repositorio)")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    ejecutar(cargar_config(args.config))


if __name__ == "__main__":
    main()
