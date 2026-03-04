"""Configuración global del sistema MonografiasBot1."""

MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS_PER_SECTION = 8000

NIVELES = {
    "PREGRADO":  "pregrado universitario",
    "MAESTRIA":  "maestría (posgrado)",
    "DOCTORADO": "doctorado (posgrado avanzado)",
}

INSTRUCCION_ACADEMICA = """
Eres un redactor académico experto. Escribe en un registro formal y riguroso,
con lenguaje claro, párrafos bien desarrollados y coherencia argumentativa.
Usa terminología especializada apropiada al nivel indicado.
No uses viñetas ni listas en el cuerpo del texto — escribe en prosa académica continua.
"""
