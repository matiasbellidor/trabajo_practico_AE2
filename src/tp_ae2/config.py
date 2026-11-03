"""Carga de config.yaml (decisiones pre-registradas) y resolución de rutas."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

RAIZ_REPO = Path(__file__).resolve().parents[2]
MUESTRAS_VALIDAS = ("mensual_spline", "trimestral")


@dataclass(frozen=True)
class Config:
    datos: dict[str, Any]
    raiz: Path

    def __getitem__(self, clave: str) -> Any:
        return self.datos[clave]

    def ruta(self, clave: str) -> Path:
        return self.raiz / self.datos["rutas"][clave]

    @property
    def alfa(self) -> float:
        return float(self.datos["alfa"])

    @property
    def confianza(self) -> float:
        return float(self.datos["confianza"])

    @property
    def principal_mensual(self) -> bool:
        return self.datos["muestra_principal"] == "mensual_spline"


def cargar_config(path: str | Path | None = None) -> Config:
    path = Path(path) if path else RAIZ_REPO / "config.yaml"
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    datos = yaml.safe_load(path.read_text(encoding="utf-8"))
    validar(datos)
    return Config(datos=datos, raiz=path.parent)


def validar(datos: dict[str, Any]) -> None:
    if datos["muestra_principal"] not in MUESTRAS_VALIDAS:
        raise ValueError(f"muestra_principal debe ser una de {MUESTRAS_VALIDAS}")
    if datos["pbi"]["desestacionalizar"] not in ("stl", "ninguna", "indec"):
        raise ValueError("pbi.desestacionalizar debe ser 'stl', 'ninguna' o 'indec'")
    if abs(datos["alfa"] + datos["confianza"] - 1) > 1e-12:
        raise ValueError("alfa y confianza deben sumar 1")


def con_cambios(cfg: Config, cambios: dict[str, Any]) -> Config:
    """Copia de la configuración con claves reemplazadas (para las sensibilidades)."""
    datos = copy.deepcopy(cfg.datos)
    _fusionar(datos, cambios)
    validar(datos)
    return Config(datos=datos, raiz=cfg.raiz)


def _fusionar(base: dict, cambios: dict) -> None:
    for clave, valor in cambios.items():
        if isinstance(valor, dict) and isinstance(base.get(clave), dict):
            _fusionar(base[clave], valor)
        else:
            base[clave] = valor
