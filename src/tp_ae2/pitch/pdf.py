"""PDF mínimo con una imagen JPEG por página (sin re-codificar: el JPEG va tal cual, con DCTDecode)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def _texto_pdf(s: str) -> str:
    """Cadena PDF en UTF-16BE con BOM (acepta tildes y signos)."""
    return "<" + ("﻿" + s).encode("utf-16-be").hex().upper() + ">"


def escribir(jpegs: list[Path], destino: Path, titulo: str, autor: str, asunto: str,
             ancho_pt: float = 960, alto_pt: float = 540) -> None:
    objetos: list[bytes] = []

    def agregar(cuerpo: bytes) -> int:
        objetos.append(cuerpo)
        return len(objetos)

    catalogo = agregar(b"")  # se completa al final
    paginas = agregar(b"")
    hijos = []
    for i, ruta in enumerate(jpegs, start=1):
        datos = ruta.read_bytes()
        with Image.open(ruta) as im:
            ancho_px, alto_px = im.size
            componentes = 1 if im.mode == "L" else 3
        imagen = agregar(
            f"<< /Type /XObject /Subtype /Image /Width {ancho_px} /Height {alto_px} /ColorSpace "
            f"/{'DeviceGray' if componentes == 1 else 'DeviceRGB'} /BitsPerComponent 8 /Filter /DCTDecode "
            f"/Length {len(datos)} >>\nstream\n".encode() + datos + b"\nendstream")
        dibujo = f"q {ancho_pt:.2f} 0 0 {alto_pt:.2f} 0 0 cm /Im{i} Do Q".encode()
        contenido = agregar(b"<< /Length %d >>\nstream\n" % len(dibujo) + dibujo + b"\nendstream")
        hijos.append(agregar(
            f"<< /Type /Page /Parent {paginas} 0 R /MediaBox [0 0 {ancho_pt:.2f} {alto_pt:.2f}] "
            f"/Resources << /XObject << /Im{i} {imagen} 0 R >> >> /Contents {contenido} 0 R >>".encode()))
    objetos[paginas - 1] = (f"<< /Type /Pages /Count {len(hijos)} /Kids [" + " ".join(f"{h} 0 R" for h in hijos)
                            + "] >>").encode()
    objetos[catalogo - 1] = f"<< /Type /Catalog /Pages {paginas} 0 R /PageLayout /SinglePage >>".encode()
    # Sin fecha de creación: el mismo deck da el mismo PDF (el diff de git queda limpio si nada cambió)
    info = agregar(f"<< /Title {_texto_pdf(titulo)} /Author {_texto_pdf(autor)} /Subject {_texto_pdf(asunto)} "
                   f"/Creator (tp_ae2.pitch) >>".encode())

    salida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    desplazamientos = []
    for n, cuerpo in enumerate(objetos, start=1):
        desplazamientos.append(len(salida))
        salida += f"{n} 0 obj\n".encode() + cuerpo + b"\nendobj\n"
    xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    for d in desplazamientos:
        salida += f"{d:010d} 00000 n \n".encode()
    salida += (f"trailer\n<< /Size {len(objetos) + 1} /Root {catalogo} 0 R /Info {info} 0 R >>\n"
               f"startxref\n{xref}\n%%EOF\n").encode()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(bytes(salida))
