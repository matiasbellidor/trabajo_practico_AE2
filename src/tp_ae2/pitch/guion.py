"""Guion de la exposición: se escribe en guion/guion.yaml (fuera del repo) con los números como variables de Jinja
({{ b1 }}, {{ p_b1 }}, …) que salen de outputs/resultados.json con el mismo formateador que el informe. Así ningún
número del guion se redondea a mano y, si cambian los resultados, el guion cambia solo.

Marcas que entiende la vista de Recursos dentro del texto:
  [pausa 2s]    pausa (la duración es parte del guion)
  **texto**     énfasis
  [señalar 2]   señalar en la diapositiva la marca 2 de ese paso (sale numerada sobre la diapositiva)
  [público]     levantar la vista y hablarle al público
  [lento]       bajar la velocidad (números, conclusiones)
"""

from __future__ import annotations

import re
from pathlib import Path

import jinja2
import yaml

from ..veredicto import num

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
_MARCA_SENALAR = re.compile(r"\[señalar (\d+)\]")
_MARCAS_VALIDAS = re.compile(r"\[(pausa \d+(?:,\d+)?s|señalar \d+|público|lento)\]")


class GuionInvalido(ValueError):
    pass


def _mes_largo(periodo: str) -> str:
    anio, mes = periodo.split("-")
    return f"{MESES[int(mes) - 1]} de {anio}"


def _trimestre_largo(q: str) -> str:
    anio, t = q.split("Q")
    return f"el {['primer', 'segundo', 'tercer', 'cuarto'][int(t) - 1]} trimestre de {anio}"


def contexto(r: dict) -> dict:
    """Los números que puede citar el guion, ya formateados (coma decimal, signo menos tipográfico)."""
    e, hp = r["estimadores"], r["hipotesis_principal"]["d0"]
    rm, an, pc = r["regresion_multiple"], r["anova"], r["prueba_complementaria"]["decision"]
    ba = r["bondad_ajuste"]["var_bono"]
    coef = {c["nombre"]: c for c in rm["coeficientes"]}
    grupos = {g["grupo"]: g for g in an["grupos"]}
    trim = r["robustez_trimestral"]["bateria_respaldo"]["hipotesis_principal"]["d0"]
    infl = r["robustez_trimestral"]["influencia"]
    vif = max(v["vif"] for v in r["diagnosticos"]["regresion_multiple"]["vif"])
    m = r["muestra"]
    return {
        "n": m["principal"]["n"], "n_minimo": m["n_minimo_consigna"], "n_trim": m["respaldo"]["n"],
        "inicio_largo": _mes_largo(m["principal"]["inicio"]), "fin_largo": _mes_largo(m["principal"]["fin"]),
        "media_bono": num(e["var_bono"]["media"], 2), "desvio_bono": num(e["var_bono"]["desvio"], 2),
        "desvio_bono_1": num(e["var_bono"]["desvio"], 1),
        "media_pbi": num(e["var_pbi"]["media"], 2), "desvio_pbi": num(e["var_pbi"]["desvio"], 2),
        "veces": round(e["var_bono"]["desvio"] / e["var_pbi"]["desvio"]),
        "min_bono": num(e["var_bono"]["minimo"], 1), "max_bono": num(e["var_bono"]["maximo"], 1, signo=True),
        "suba": e["proporcion_suba"]["exitos"],
        "ic_media_inf": num(r["intervalos"]["media_var_bono"]["inferior"], 2),
        "ic_media_sup": num(r["intervalos"]["media_var_bono"]["superior"], 2),
        "b1": num(hp["b1"], 4), "p_b1": num(hp["p_b1"], 4), "t_b1": num(hp["t_b1"], 4),
        "ic_inf": num(hp["ic_b1"]["inferior"], 2), "ic_sup": num(hp["ic_b1"]["superior"], 2),
        "r2": num(hp["r2"], 4),
        "chi2_p_bono": num(ba["chi2"]["p_valor"], 4), "sw_p_bono": num(ba["shapiro"]["p_valor"], 4),
        "tam_max": num(hp["ic_b1"]["superior"] * e["var_pbi"]["desvio"], 1),
        "rm_r2_pct": num(rm["r2"] * 100, 1), "rm_p": num(rm["p_f"], 4), "rm_p_pbi": num(coef["var_pbi"]["p_valor"], 4),
        "rm_vif": num(vif, 2),
        "anova_f": num(an["f"], 4), "anova_p": num(an["p_valor"], 4),
        "media_bajo": num(grupos["bajo"]["media"], 2), "media_medio": num(grupos["medio"]["media"], 2),
        "media_alto": num(grupos["alto"]["media"], 2),
        "dif": num(pc["diferencia"], 4), "dif_p": num(pc["p_valor"], 4),
        "trim_b1": num(trim["b1"], 2), "trim_p": num(trim["p_b1"], 4),
        "trim_clave": _trimestre_largo(infl["periodos_que_cambian_decision"][0]),
        "trim_p_sin": num(infl["p_sin_max"], 4),
    }


def _renderizar(valor, entorno: jinja2.Environment, ctx: dict):
    if isinstance(valor, str):
        return entorno.from_string(valor).render(ctx).strip()
    if isinstance(valor, list):
        return [_renderizar(v, entorno, ctx) for v in valor]
    if isinstance(valor, dict):
        return {k: _renderizar(v, entorno, ctx) for k, v in valor.items()}
    return valor


def _reloj(segundos: int) -> str:
    return f"{segundos // 60}:{segundos % 60:02d}"


def cargar(ruta: Path) -> dict:
    return yaml.safe_load(ruta.read_text(encoding="utf-8"))


def armar(fuente: dict, resultados: dict, ids_diapositivas: list[str], titulos: dict[str, str]) -> dict:
    """Guion listo para cifrar: números reemplazados, tiempos acumulados, marcas numeradas por diapositiva."""
    entorno = jinja2.Environment(undefined=jinja2.StrictUndefined, autoescape=False)
    try:
        g = _renderizar({k: v for k, v in fuente.items() if k != "codigo"}, entorno, contexto(resultados))
    except jinja2.UndefinedError as err:
        raise GuionInvalido(f"El guion usa una variable que no existe: {err}") from err

    oradores = g["oradores"]
    cuenta = {}
    for b in g["bloques"]:
        cuenta[b["orador"]] = cuenta.get(b["orador"], 0) + 1
    vistos: dict[str, int] = {}
    bloques, pasos, reloj, ultima = [], [], 0, 0
    marcas_por_diapo: dict[str, int] = {}
    for i, b in enumerate(g["bloques"]):
        quien = b["orador"]
        if quien not in oradores:
            raise GuionInvalido(f"Bloque {b['id']}: orador desconocido {quien!r}")
        vistos[quien] = vistos.get(quien, 0) + 1
        etiqueta = oradores[quien]["nombre"] + (f" ({vistos[quien]}/{cuenta[quien]})" if cuenta[quien] > 1 else "")
        inicio_bloque = reloj
        for p in b["pasos"]:
            d = p["diapositiva"]
            if d not in ids_diapositivas:
                raise GuionInvalido(f"Bloque {b['id']}: la diapositiva {d!r} no está en el deck")
            n = ids_diapositivas.index(d) + 1
            if n < ultima:
                raise GuionInvalido(f"Bloque {b['id']}: el guion vuelve a la diapositiva {n} después de la {ultima}")
            ultima = n
            texto = " ".join(p["guion"])
            for marca in re.findall(r"\[[^\]]+\]", texto):
                if not _MARCAS_VALIDAS.fullmatch(marca):
                    raise GuionInvalido(f"Marca desconocida {marca} en {b['id']}/{d}")
            marcas = p.get("marcas", [])
            for k in _MARCA_SENALAR.findall(texto):
                if not 1 <= int(k) <= len(marcas):
                    raise GuionInvalido(f"[señalar {k}] sin marca definida en {b['id']}/{d}")
            base = marcas_por_diapo.get(d, 0)
            marcas_por_diapo[d] = base + len(marcas)
            pasos.append({
                "bloque": i, "diapositiva": d, "n": n, "titulo": titulos[d], "segundos": int(p["segundos"]),
                "inicio": reloj, "como": p.get("como", ""), "guion": p["guion"],
                "marcas": [{"num": base + j + 1, **m} for j, m in enumerate(marcas)],
            })
            reloj += int(p["segundos"])
        bloques.append({"id": b["id"], "orador": quien, "etiqueta": etiqueta, "tema": b["tema"],
                        "inicio": inicio_bloque, "segundos": reloj - inicio_bloque, "pase": b.get("pase")})
    return {"titulo": g.get("titulo", "Guion de la exposición"), "duracion": reloj, "duracion_texto": _reloj(reloj),
            "oradores": oradores, "bloques": bloques, "pasos": pasos, "leyenda": g.get("leyenda", [])}
