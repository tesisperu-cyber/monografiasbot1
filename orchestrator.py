"""
MonografiasBot1 — Agente Orquestador
=====================================
Coordina 4 sub-agentes:
  1. AgenteIntroduccion
  2. AgenteDesarrollo
  3. AgenteConclusiones
  4. AgenteReferencias
"""

from groq import Groq
from agents.introduccion   import AgenteIntroduccion
from agents.desarrollo     import AgenteDesarrollo
from agents.conclusiones   import AgenteConclusiones
from agents.referencias    import AgenteReferencias
from research.buscador          import BuscadorAcademico
from research.webs_especializadas import BuscadorEspecializado
from utils.formatter       import formatear_monografia
from utils.docx_generator  import generar_docx
from utils.config          import MODEL, MAX_TOKENS_PER_SECTION
import time


class Orchestrator:
    """Agente orquestador principal que coordina la generación de la monografía."""

    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.buscador            = BuscadorAcademico()
        self.buscador_especializado = BuscadorEspecializado()

        # Sub-agentes
        self.agente_intro       = AgenteIntroduccion(self.client)
        self.agente_desarrollo  = AgenteDesarrollo(self.client)
        self.agente_conclusiones = AgenteConclusiones(self.client)
        self.agente_referencias = AgenteReferencias(self.client)

    def ejecutar(self, datos_usuario: dict, callback=None) -> dict:
        """
        Ejecuta el pipeline completo de generación de monografía.

        datos_usuario = {
            'tema': str,
            'curso': str,
            'especialidad': str,
            'nivel': str,   # PREGRADO | MAESTRIA | DOCTORADO
            'paginas': int,
        }
        """
        tema        = datos_usuario['tema']
        curso       = datos_usuario['curso']
        especialidad = datos_usuario['especialidad']
        nivel       = datos_usuario['nivel']
        paginas     = int(datos_usuario['paginas'])

        # Palabras por página aprox (250 palabras/pág académica)
        palabras_total = paginas * 250
        # Distribución: 15% intro, 60% desarrollo, 15% conclusiones, 10% refs
        palabras_intro        = int(palabras_total * 0.15)
        palabras_desarrollo   = int(palabras_total * 0.60)
        palabras_conclusiones = int(palabras_total * 0.15)

        contexto = {
            'tema': tema,
            'curso': curso,
            'especialidad': especialidad,
            'nivel': nivel,
            'paginas': paginas,
            'palabras_intro': palabras_intro,
            'palabras_desarrollo': palabras_desarrollo,
            'palabras_conclusiones': palabras_conclusiones,
        }

        resultado = {}

        # ── FASE 1: Búsqueda académica ─────────────────────────────────────────
        if callback: callback("🔍 Buscando fuentes en bases de datos académicas...")
        fuentes = self.buscador.buscar(tema, max_resultados=50)
        if callback: callback(f"   ✓ {len(fuentes)} fuentes en bases de datos")

        # ── FASE 1b: Webs especializadas por área ──────────────────────────────
        if callback: callback(f"🌐 Buscando en webs especializadas ({especialidad})...")
        fuentes_web = self.buscador_especializado.buscar(tema, especialidad, tema_extra=tema, max_por_web=3)
        fuentes = fuentes + fuentes_web
        if callback: callback(f"   ✓ {len(fuentes_web)} resultados de webs especializadas")
        if callback: callback(f"   📚 Total fuentes: {len(fuentes)}")

        contexto['fuentes'] = fuentes

        # ── FASE 2: Introducción ───────────────────────────────────────────────
        if callback: callback("📝 Agente Introducción redactando...")
        resultado['introduccion'] = self.agente_intro.generar(contexto)
        if callback: callback("   ✓ Introducción completada")
        time.sleep(1)  # Respetar rate limits de Groq

        # ── FASE 3: Desarrollo (capítulos) ────────────────────────────────────
        if callback: callback("📚 Agente Desarrollo redactando capítulos...")
        resultado['desarrollo'] = self.agente_desarrollo.generar(contexto)
        if callback: callback("   ✓ Desarrollo completado")
        time.sleep(1)

        # ── FASE 4: Conclusiones y Recomendaciones ────────────────────────────
        if callback: callback("🎯 Agente Conclusiones redactando...")
        contexto['resumen_desarrollo'] = resultado['desarrollo'][:2000]
        resultado['conclusiones'] = self.agente_conclusiones.generar(contexto)
        if callback: callback("   ✓ Conclusiones completadas")
        time.sleep(1)

        # ── FASE 5: Referencias APA 7 ─────────────────────────────────────────
        if callback: callback("📖 Agente Referencias generando bibliografía APA 7...")
        resultado['referencias'] = self.agente_referencias.generar(contexto)
        if callback: callback("   ✓ Referencias completadas")

        # ── FASE 6: Ensamblar ─────────────────────────────────────────────────
        if callback: callback("🔧 Ensamblando monografía final...")
        monografia_final = formatear_monografia(resultado, contexto)

        return {
            'monografia': monografia_final,
            'fuentes_encontradas': len(fuentes),
            'secciones': resultado,
            'contexto': contexto,
        }
