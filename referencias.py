"""Agente especializado en Referencias Bibliográficas APA 7 (ES, EN, PT)."""

from agents.base import AgenteBase
from utils.config import INSTRUCCION_ACADEMICA


class AgenteReferencias(AgenteBase):
    def __init__(self, client):
        super().__init__(client, "AgenteReferencias")

    def generar(self, contexto: dict) -> str:
        tema     = contexto['tema']
        nivel    = self._nivel_descripcion(contexto['nivel'])
        fuentes  = contexto.get('fuentes', [])

        # Construir lista de fuentes reales encontradas
        fuentes_reales = []
        for f in fuentes[:40]:
            titulo  = f.get('titulo', '')
            autores = f.get('autores', '')
            anio    = f.get('anio', 's.f.')
            doi     = f.get('doi', '')
            url     = f.get('url', '')
            revista = f.get('revista', '')
            fuente  = f.get('fuente', '')
            idioma  = f.get('idioma', 'en')
            if titulo:
                fuentes_reales.append(
                    f"- Autores: {autores} | Año: {anio} | Título: {titulo} | "
                    f"Revista/Fuente: {revista or fuente} | DOI: {doi} | URL: {url} | Idioma: {idioma}"
                )

        fuentes_txt = "\n".join(fuentes_reales) if fuentes_reales else "No se encontraron fuentes externas."

        system_prompt = """
Eres el Agente de Referencias Bibliográficas. Eres experto en el formato APA 7ma edición.
Generas referencias perfectamente formateadas en español, inglés y portugués.
"""

        user_prompt = f"""
Genera la sección de REFERENCIAS BIBLIOGRÁFICAS en formato APA 7ma edición para una
monografía de nivel {nivel} sobre el tema: "{tema}"

INSTRUCCIONES IMPORTANTES:
1. Usa las fuentes reales encontradas a continuación cuando tengan información suficiente
2. Complementa con referencias académicas adicionales relevantes al tema
3. Incluye referencias en los TRES idiomas: español, inglés Y portugués
   - Mínimo 5 referencias en español
   - Mínimo 5 referencias en inglés
   - Mínimo 3 referencias en portugués
4. Ordena todas las referencias alfabéticamente por apellido del primer autor
5. Aplica sangría francesa (hanging indent) indicándolo con espacios
6. Formato APA 7 estricto para cada tipo:
   - Artículo: Apellido, I. (Año). Título del artículo. Nombre de la Revista, vol(núm), páginas. https://doi.org/...
   - Libro: Apellido, I. (Año). Título del libro. Editorial.
   - Capítulo: Apellido, I. (Año). Título del capítulo. En I. Editor (Ed.), Título del libro (pp. xx-xx). Editorial.
   - Web: Apellido, I. (Año). Título. Sitio Web. URL

FUENTES ENCONTRADAS EN BASES DE DATOS:
{fuentes_txt}

Genera la lista completa de referencias. Inicia directamente con la primera referencia.
"""
        return self._llamar_llm(system_prompt, user_prompt, max_tokens=4000)
