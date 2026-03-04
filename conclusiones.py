"""Agente especializado en Conclusiones y Recomendaciones."""

from agents.base import AgenteBase
from utils.config import INSTRUCCION_ACADEMICA


class AgenteConclusiones(AgenteBase):
    def __init__(self, client):
        super().__init__(client, "AgenteConclusiones")

    def generar(self, contexto: dict) -> str:
        tema              = contexto['tema']
        curso             = contexto['curso']
        especialidad      = contexto['especialidad']
        nivel             = self._nivel_descripcion(contexto['nivel'])
        palabras          = contexto['palabras_conclusiones']
        resumen_desarrollo = contexto.get('resumen_desarrollo', '')

        system_prompt = INSTRUCCION_ACADEMICA + f"""
Eres el Agente de Conclusiones y Recomendaciones. Redactas el cierre académico
de monografías de nivel {nivel}, sintetizando hallazgos y proponiendo líneas futuras.
"""

        user_prompt = f"""
Redacta las CONCLUSIONES Y RECOMENDACIONES de una monografía con estas características:

- Tema: {tema}
- Curso: {curso}
- Especialidad: {especialidad}
- Nivel: {nivel}
- Extensión aproximada: {palabras} palabras

Resumen del desarrollo de la monografía:
{resumen_desarrollo}

La sección debe incluir obligatoriamente:

CONCLUSIONES:
- Síntesis de los hallazgos principales de cada capítulo
- Respuesta a los objetivos planteados en la introducción
- Reflexión crítica sobre el tema investigado
- Contribución del estudio al campo de conocimiento

RECOMENDACIONES:
- Recomendaciones prácticas derivadas del análisis
- Sugerencias para futuras investigaciones
- Implicaciones para la práctica profesional en {especialidad}
- Limitaciones reconocidas y cómo superarlas en estudios futuros

Escribe en prosa académica formal y continua. No uses viñetas.
Inicia con el encabezado CONCLUSIONES, luego RECOMENDACIONES.
"""
        return self._llamar_llm(system_prompt, user_prompt)
