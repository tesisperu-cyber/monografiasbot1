"""Clase base para todos los agentes."""

from groq import Groq
from utils.config import MODEL, MAX_TOKENS_PER_SECTION, INSTRUCCION_ACADEMICA, NIVELES


class AgenteBase:
    def __init__(self, client: Groq, nombre: str):
        self.client = client
        self.nombre = nombre

    def _llamar_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = MAX_TOKENS_PER_SECTION) -> str:
        """Llama al LLM y retorna el texto generado."""
        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[Error en {self.nombre}: {str(e)}]"

    def _nivel_descripcion(self, nivel: str) -> str:
        return NIVELES.get(nivel.upper(), nivel)

    def _fuentes_resumen(self, fuentes: list, max_fuentes: int = 15) -> str:
        """Convierte lista de fuentes en texto resumido para el prompt."""
        if not fuentes:
            return "No se encontraron fuentes externas."
        lines = []
        for i, f in enumerate(fuentes[:max_fuentes], 1):
            titulo  = f.get('titulo', 'Sin título')
            autores = f.get('autores', 'Autor desconocido')
            anio    = f.get('anio', 's.f.')
            fuente  = f.get('fuente', '')
            resumen = f.get('resumen', '')[:200]
            lines.append(f"{i}. {autores} ({anio}). {titulo}. [{fuente}] {resumen}")
        return "\n".join(lines)
