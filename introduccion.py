"""Agente especializado en redactar la Introducción de la monografía."""

from agents.base import AgenteBase
from utils.config import INSTRUCCION_ACADEMICA


class AgenteIntroduccion(AgenteBase):
    def __init__(self, client):
        super().__init__(client, "AgenteIntroduccion")

    def generar(self, contexto: dict) -> str:
        tema         = contexto['tema']
        curso        = contexto['curso']
        especialidad = contexto['especialidad']
        nivel        = self._nivel_descripcion(contexto['nivel'])
        palabras     = contexto['palabras_intro']
        fuentes_txt  = self._fuentes_resumen(contexto.get('fuentes', []), max_fuentes=8)

        system_prompt = INSTRUCCION_ACADEMICA + f"""
Eres el Agente de Introducción. Tu tarea es redactar exclusivamente la sección
INTRODUCCIÓN de una monografía académica de nivel {nivel}.
"""

        user_prompt = f"""
Redacta la INTRODUCCIÓN completa de una monografía con las siguientes características:

- Tema: {tema}
- Curso: {curso}
- Especialidad: {especialidad}
- Nivel académico: {nivel}
- Extensión aproximada: {palabras} palabras

La introducción debe incluir obligatoriamente:
1. Presentación del tema y su relevancia actual
2. Justificación del estudio (por qué es importante investigar este tema)
3. Planteamiento del problema o pregunta de investigación
4. Objetivos de la monografía (objetivo general y objetivos específicos)
5. Descripción breve de la estructura de la monografía (capítulos)
6. Alcances y limitaciones del estudio

Usa citas académicas cuando corresponda basándote en estas fuentes disponibles:
{fuentes_txt}

Escribe en prosa académica formal y continua. No uses viñetas.
Inicia directamente con el texto de la introducción.
"""
        return self._llamar_llm(system_prompt, user_prompt)
