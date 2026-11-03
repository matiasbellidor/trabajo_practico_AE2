"""Lectura y validación de los archivos de entrada, y linaje de datos."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import pandas as pd

from .config import Config

log = logging.getLogger(__name__)

OBLIGATORIOS = ("al30d", "pbi")
OPCIONALES = ("al30", "al30c", "pbi_indec_desest")
# Descargas independientes de las mismas series: solo sirven para verificar los datasets ordenados.
VERIFICACION = ("verificacion_al30d", "verificacion_pbi")

# Cuadros del archivo largo de cuentas nacionales (data_sets_ordenados/01_...).
CUADRO_PBI = ("OD_C01", "Producto Interno Bruto")
CUADRO_PBI_DESEST = ("OD_DESEST_NIVEL", "PIB")
COLUMNAS_CSV_BONO = {"fecha": "date", "apertura": "o", "maximo": "h", "minimo": "l", "cierre": "c", "volumen": "v"}


def verificar_obligatorios(cfg: Config) -> None:
    faltan = [str(cfg.ruta(k)) for k in OBLIGATORIOS if not cfg.ruta(k).exists()]
    if faltan:
        raise FileNotFoundError("Faltan archivos obligatorios: " + ", ".join(faltan))


def leer_bono(ruta: Path) -> pd.DataFrame:
    """Cotizaciones diarias de Data912: JSON original (date, o, h, l, c, v) o CSV ordenado (fecha, cierre, ...)."""
    ruta = Path(ruta)
    if ruta.suffix == ".csv":
        df = pd.read_csv(ruta).rename(columns=COLUMNAS_CSV_BONO)
    else:
        df = pd.DataFrame(json.loads(ruta.read_text(encoding="utf-8")))
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    duplicadas = int(df["date"].duplicated().sum())
    if duplicadas:
        raise ValueError(f"{ruta}: {duplicadas} fechas duplicadas")
    if df["c"].isna().any() or (df["c"] <= 0).any():
        raise ValueError(f"{ruta}: cierres nulos o no positivos")
    return df.set_index("date")[["o", "h", "l", "c", "v"]]


def huecos(fechas: pd.DatetimeIndex, max_dias: int) -> pd.DataFrame:
    """Saltos entre ruedas consecutivas mayores a max_dias días corridos."""
    serie = pd.Series(fechas, index=fechas)
    salto = serie.diff().dt.days
    mask = salto > max_dias
    return pd.DataFrame({
        "desde": serie.shift(1)[mask].dt.strftime("%Y-%m-%d").to_numpy(),
        "hasta": serie[mask].dt.strftime("%Y-%m-%d").to_numpy(),
        "dias_corridos": salto[mask].astype(int).to_numpy(),
    })


def leer_pbi(ruta: Path) -> pd.Series:
    """PBI trimestral a precios de 2004 (serie original), indexado por trimestre.

    Acepta el archivo largo de cuentas nacionales del INDEC (cuadro OD_C01) o el CSV de datos.gob.ar
    (indice_tiempo, pib_precios_2004).
    """
    df = pd.read_csv(ruta)
    if "tabla_id" in df.columns:
        return leer_cuenta_nacional(ruta, *CUADRO_PBI, df=df)
    esperadas = {"indice_tiempo", "pib_precios_2004"}
    if not esperadas.issubset(df.columns):
        raise ValueError(f"{ruta}: se esperaban las columnas {sorted(esperadas)}")
    fechas = pd.to_datetime(df["indice_tiempo"])
    if not (fechas.dt.day.eq(1) & fechas.dt.month.isin([1, 4, 7, 10])).all():
        raise ValueError(f"{ruta}: indice_tiempo debe ser el primer día de cada trimestre")
    serie = pd.Series(df["pib_precios_2004"].to_numpy(float), index=pd.PeriodIndex(fechas, freq="Q"),
                      name="pib_precios_2004")
    return _validar_trimestral(serie.sort_index(), ruta)


def leer_cuenta_nacional(ruta: Path, tabla_id: str, concepto: str, df: pd.DataFrame | None = None) -> pd.Series:
    """Serie trimestral de un cuadro del archivo largo de cuentas nacionales del INDEC."""
    df = pd.read_csv(ruta) if df is None else df
    filas = df[(df["tabla_id"] == tabla_id) & (df["frecuencia"] == "trimestral") & (df["concepto"] == concepto)]
    if filas.empty:
        raise ValueError(f"{ruta}: no hay datos trimestrales de «{concepto}» en el cuadro {tabla_id}")
    indice = pd.PeriodIndex(pd.to_datetime(filas["fecha_fin_periodo"]), freq="Q")
    if indice.duplicated().any():
        raise ValueError(f"{ruta}: trimestres duplicados en {tabla_id} / {concepto}")
    serie = pd.Series(filas["valor"].to_numpy(float), index=indice, name=f"{tabla_id}:{concepto}")
    return _validar_trimestral(serie.sort_index(), ruta)


def _validar_trimestral(serie: pd.Series, ruta: Path) -> pd.Series:
    if serie.isna().any():
        raise ValueError(f"{ruta}: valores nulos en el PBI")
    esperado = pd.period_range(serie.index[0], serie.index[-1], freq="Q")
    if len(esperado) != len(serie):
        raise ValueError(f"{ruta}: faltan trimestres en la serie")
    return serie


def leer_pbi_desest_indec(ruta: Path) -> pd.Series:
    """PIB desestacionalizado publicado por el INDEC (millones de pesos de 2004)."""
    return leer_cuenta_nacional(ruta, *CUADRO_PBI_DESEST)


def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def linaje(cfg: Config) -> list[dict]:
    """Ruta, tamaño, SHA-256, filas y rango de fechas de cada archivo de entrada."""
    filas = []
    for clave in OBLIGATORIOS + OPCIONALES + VERIFICACION:
        if clave not in cfg["rutas"]:
            continue
        ruta = cfg.ruta(clave)
        meta = cfg["fuentes"].get(clave, {})
        registro = {
            "archivo": clave,
            "ruta": ruta.relative_to(cfg.raiz).as_posix(),
            "obligatorio": clave in OBLIGATORIOS,
            "uso": "verificación" if clave in VERIFICACION else "análisis",
            "existe": ruta.exists(),
            "fuente": meta.get("fuente"),
            "url": meta.get("url"),
            "obtencion": meta.get("obtencion"),
        }
        if ruta.exists():
            if clave in ("pbi", "verificacion_pbi", "pbi_indec_desest"):
                serie = leer_pbi_desest_indec(ruta) if clave == "pbi_indec_desest" else leer_pbi(ruta)
                n, inicio, fin = len(serie), serie.index[0].start_time, serie.index[-1].start_time
            else:
                df = leer_bono(ruta)
                n, inicio, fin = len(df), df.index[0], df.index[-1]
            registro.update({
                "bytes": ruta.stat().st_size,
                "sha256": _sha256(ruta),
                "filas": n,
                "fecha_min": inicio.strftime("%Y-%m-%d"),
                "fecha_max": fin.strftime("%Y-%m-%d"),
            })
        elif clave == "pbi_indec_desest":
            registro["nota"] = "No disponible: la sensibilidad con el PBI desestacionalizado del INDEC no se corrió."
        filas.append(registro)
    return filas
