import pytest

from tp_ae2 import analisis, transformaciones
from tp_ae2.config import RAIZ_REPO, cargar_config


@pytest.fixture(scope="session")
def cfg():
    return cargar_config(RAIZ_REPO / "config.yaml")


@pytest.fixture(scope="session")
def base(cfg):
    return transformaciones.cargar_base(cfg)


@pytest.fixture(scope="session")
def corrida(cfg):
    return analisis.ejecutar(cfg)
