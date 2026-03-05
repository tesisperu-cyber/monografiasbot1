"""Ensambla todas las secciones en el documento final de la monografía."""

from datetime import date


def formatear_monografia(secciones: dict, contexto: dict) -> str:
    """
    Une todas las secciones generadas en un documento completo y bien formateado.
    """
    tema         = contexto['tema']
    curso        = contexto['curso']
    especialidad = contexto['especialidad']
    nivel        = contexto['nivel']
    paginas      = contexto['paginas']
    anio         = date.today().year

    separador = "\n" + "─" * 70 + "\n"

    doc = []

    # ── Portada ───────────────────────────────────────────────────────────────
    doc.append(f"""
{'='*70}
                    MONOGRAFÍA ACADÉMICA
{'='*70}

TÍTULO: {tema.upper()}

Curso       : {curso}
Especialidad: {especialidad}
Nivel       : {nivel}
Año         : {anio}
Páginas     : {paginas} páginas

{'='*70}
""")

    # ── Índice ────────────────────────────────────────────────────────────────
    doc.append("""
ÍNDICE DE CONTENIDOS
────────────────────

  I.    INTRODUCCIÓN ........................................................ 1
  II.   DESARROLLO
""")
    # Extraer títulos de capítulos del desarrollo
    desarrollo = secciones.get('desarrollo', '')
    caps = []
    for linea in desarrollo.split('\n'):
        if linea.strip().upper().startswith('CAPÍTULO') or \
           (linea.strip() and linea.strip()[0].isdigit() and 'CAPÍTULO' in linea.upper()):
            caps.append(linea.strip())
    for i, cap in enumerate(caps, 1):
        doc.append(f"        {cap} {'.'*(40-len(cap[:40]))} {i+1}\n")

    doc.append("""  III.  CONCLUSIONES Y RECOMENDACIONES ..................................... X
  IV.   REFERENCIAS BIBLIOGRÁFICAS ......................................... X

""")

    # ── Introducción ─────────────────────────────────────────────────────────
    doc.append(separador)
    doc.append("I. INTRODUCCIÓN\n")
    doc.append(separador)
    doc.append(secciones.get('introduccion', '[Sin contenido]'))

    # ── Desarrollo ───────────────────────────────────────────────────────────
    doc.append(separador)
    doc.append("II. DESARROLLO\n")
    doc.append(separador)
    doc.append(desarrollo)

    # ── Conclusiones ─────────────────────────────────────────────────────────
    doc.append(separador)
    doc.append("III. CONCLUSIONES Y RECOMENDACIONES\n")
    doc.append(separador)
    doc.append(secciones.get('conclusiones', '[Sin contenido]'))

    # ── Referencias ──────────────────────────────────────────────────────────
    doc.append(separador)
    doc.append("IV. REFERENCIAS BIBLIOGRÁFICAS\n")
    doc.append("    (Formato APA 7ma edición — Español, Inglés y Portugués)\n")
    doc.append(separador)
    doc.append(secciones.get('referencias', '[Sin contenido]'))

    doc.append(f"\n\n{'='*70}\n         Fin del documento — MonografiasBot1\n{'='*70}\n")

    return "\n".join(doc)
