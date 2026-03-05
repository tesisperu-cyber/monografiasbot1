"""Agente especializado en redactar el Desarrollo (capítulos) de la monografía."""

from agents.base import AgenteBase
from utils.config import INSTRUCCION_ACADEMICA, MODEL
import time


class AgenteDesarrollo(AgenteBase):
    def __init__(self, client):
        super().__init__(client, "AgenteDesarrollo")

    def _planificar_capitulos(self, contexto: dict) -> list[str]:
        """Primero planifica los capítulos, luego los redacta uno a uno."""
        tema     = contexto['tema']
        nivel    = self._nivel_descripcion(contexto['nivel'])
        paginas  = contexto['paginas']

        # Número de capítulos según extensión
        if paginas <= 10:
            n_caps = 2
        elif paginas <= 20:
            n_caps = 3
        elif paginas <= 40:
            n_caps = 4
        else:
            n_caps = 5

        prompt = f"""
Para una monografía de nivel {nivel} sobre el tema: "{tema}"
que tiene aproximadamente {paginas} páginas en total,
propón exactamente {n_caps} títulos de capítulos para la sección DESARROLLO.

Los capítulos deben progresar lógicamente: de lo general a lo específico,
de lo teórico a lo aplicado.

Responde ÚNICAMENTE con los títulos, uno por línea, numerados así:
CAPÍTULO 1: [Título]
CAPÍTULO 2: [Título]
...
Sin explicaciones adicionales.
"""
        respuesta = self._llamar_llm(
            "Eres un planificador académico experto.",
            prompt,
            max_tokens=500
        )
        # Parsear títulos
        capitulos = []
        for linea in respuesta.strip().split('\n'):
            linea = linea.strip()
            if linea and ('CAPÍTULO' in linea.upper() or linea[0].isdigit()):
                capitulos.append(linea)
        return capitulos if capitulos else [
            "CAPÍTULO 1: Marco Teórico",
            "CAPÍTULO 2: Estado del Arte",
            "CAPÍTULO 3: Análisis y Discusión",
        ]

    def _redactar_capitulo(self, titulo: str, contexto: dict, fuentes_txt: str) -> str:
        tema         = contexto['tema']
        curso        = contexto['curso']
        especialidad = contexto['especialidad']
        nivel        = self._nivel_descripcion(contexto['nivel'])
        # Palabras por capítulo
        n_caps = contexto.get('n_capitulos', 3)
        palabras_cap = contexto['palabras_desarrollo'] // n_caps

        system_prompt = INSTRUCCION_ACADEMICA + f"""
Eres el Agente de Desarrollo. Redactas capítulos académicos de nivel {nivel}.
"""
        user_prompt = f"""
Redacta el contenido completo del siguiente capítulo de una monografía:

Título del capítulo: {titulo}
Tema de la monografía: {tema}
Curso: {curso}
Especialidad: {especialidad}
Nivel: {nivel}
Extensión aproximada: {palabras_cap} palabras

El capítulo debe:
- Desarrollar el tema con profundidad académica apropiada al nivel {nivel}
- Incluir subcapítulos (numerados: 1.1, 1.2, etc.)
- Integrar citas y referencias a autores cuando sea pertinente
- Presentar argumentos bien fundamentados con evidencia
- Conectar con el tema central de la monografía

Fuentes disponibles para citar:
{fuentes_txt}

Escribe en prosa académica formal. Inicia directamente con el contenido del capítulo.
"""
        return self._llamar_llm(system_prompt, user_prompt)

    def generar(self, contexto: dict) -> str:
        fuentes_txt = self._fuentes_resumen(contexto.get('fuentes', []), max_fuentes=20)

        # 1. Planificar capítulos
        capitulos = self._planificar_capitulos(contexto)
        contexto['n_capitulos'] = len(capitulos)

        # 2. Redactar cada capítulo
        secciones = []
        for i, titulo in enumerate(capitulos, 1):
            contenido = self._redactar_capitulo(titulo, contexto, fuentes_txt)
            secciones.append(f"\n{titulo}\n\n{contenido}")
            if i < len(capitulos):
                time.sleep(1)  # Respetar rate limits

        return "\n\n".join(secciones)
