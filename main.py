"""
MonografiasBot1 — Interfaz principal de usuario
================================================
Ejecutar: python main.py
"""

import os
import sys
from datetime import date
from orchestrator import Orchestrator


def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')


def banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║            📚  M O N O G R A F I A S B O T 1               ║
║                                                              ║
║   Agente Orquestador con Multi-Agentes IA · Groq + LLaMA   ║
║                                                              ║
║   Bases de datos: Semantic Scholar · OpenAlex · CrossRef    ║
║   PubMed · Europe PMC · DOAJ · arXiv · SciELO              ║
║   monografias.com · Open Library                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def solicitar_datos() -> dict:
    print("─" * 60)
    print("  DATOS DE LA MONOGRAFÍA")
    print("─" * 60)

    tema = input("\n  📌 Tema de la monografía: ").strip()
    while not tema:
        tema = input("  ⚠  El tema no puede estar vacío. Ingresa el tema: ").strip()

    curso = input("\n  📖 Curso: ").strip() or "Investigación Académica"

    especialidad = input("\n  🎓 Especialidad: ").strip() or "Ciencias Generales"

    print("\n  📊 Nivel académico:")
    print("     1. PREGRADO")
    print("     2. MAESTRÍA")
    print("     3. DOCTORADO")
    opcion_nivel = input("  Selecciona (1/2/3) [1]: ").strip() or "1"
    niveles = {"1": "PREGRADO", "2": "MAESTRIA", "3": "DOCTORADO"}
    nivel = niveles.get(opcion_nivel, "PREGRADO")

    while True:
        try:
            paginas_str = input("\n  📄 Cantidad de páginas: ").strip()
            paginas = int(paginas_str)
            if paginas < 5:
                print("  ⚠  Mínimo 5 páginas.")
                continue
            if paginas > 200:
                print("  ⚠  Máximo 200 páginas.")
                continue
            break
        except ValueError:
            print("  ⚠  Ingresa un número válido.")

    print()
    print("─" * 60)
    print("  RESUMEN DE LA SOLICITUD")
    print("─" * 60)
    print(f"  Tema        : {tema}")
    print(f"  Curso       : {curso}")
    print(f"  Especialidad: {especialidad}")
    print(f"  Nivel       : {nivel}")
    print(f"  Páginas     : {paginas}")
    print("─" * 60)

    confirmar = input("\n  ¿Confirmar y generar monografía? (s/n) [s]: ").strip().lower()
    if confirmar == 'n':
        print("\n  Operación cancelada.")
        sys.exit(0)

    return {
        'tema': tema,
        'curso': curso,
        'especialidad': especialidad,
        'nivel': nivel,
        'paginas': paginas,
    }


def guardar_resultado(monografia: str, datos: dict) -> str:
    """Guarda la monografía en un archivo .txt"""
    fecha = date.today().strftime("%Y%m%d")
    nombre_base = datos['tema'][:40].replace(' ', '_').replace('/', '-')
    nombre_archivo = f"monografia_{nombre_base}_{fecha}.txt"
    nombre_archivo = "".join(c for c in nombre_archivo if c.isalnum() or c in ('_', '-', '.'))

    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        f.write(monografia)
    return nombre_archivo


def guardar_docx(secciones: dict, contexto: dict, datos: dict) -> str:
    """Guarda la monografía como .docx con formato académico."""
    from utils.docx_generator import generar_docx
    fecha = date.today().strftime("%Y%m%d")
    nombre_base = datos['tema'][:40].replace(' ', '_').replace('/', '-')
    nombre_archivo = f"monografia_{nombre_base}_{fecha}.docx"
    nombre_archivo = "".join(c for c in nombre_archivo if c.isalnum() or c in ('_', '-', '.'))

    exito = generar_docx(secciones, contexto, nombre_archivo)
    return nombre_archivo if exito else None


def main():
    limpiar_pantalla()
    banner()

    # ── API Key ────────────────────────────────────────────────────────────────
    api_key = os.environ.get('GROQ_API_KEY', '')
    if not api_key:
        print("  🔑 API Key de Groq")
        print("  (Obtén tu clave gratis en https://console.groq.com)\n")
        api_key = input("  Ingresa tu GROQ_API_KEY: ").strip()
        if not api_key:
            print("\n  ❌ Se requiere una API Key de Groq.")
            sys.exit(1)

    # ── Datos del usuario ──────────────────────────────────────────────────────
    datos = solicitar_datos()

    # ── Ejecutar orquestador ───────────────────────────────────────────────────
    print("\n")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          🤖 INICIANDO AGENTES — POR FAVOR ESPERA            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    def mostrar_progreso(msg):
        print(f"  {msg}")

    try:
        orquestador = Orchestrator(api_key=api_key)
        resultado = orquestador.ejecutar(datos, callback=mostrar_progreso)

        monografia = resultado['monografia']
        fuentes    = resultado['fuentes_encontradas']
        secciones  = resultado['secciones']
        contexto   = resultado['contexto']

        # ── Guardar .txt ───────────────────────────────────────────────────────
        archivo_txt = guardar_resultado(monografia, datos)

        # ── Guardar .docx ──────────────────────────────────────────────────────
        print("  📄 Generando archivo Word (.docx)...")
        archivo_docx = guardar_docx(secciones, contexto, datos)

        print()
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                  ✅ MONOGRAFÍA COMPLETADA                   ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print(f"\n  📚 Fuentes consultadas : {fuentes}")
        print(f"  📄 Archivo TXT        : {archivo_txt}")
        if archivo_docx:
            print(f"  📝 Archivo Word       : {archivo_docx}")
        else:
            print(f"  ⚠  Word no generado   : instala Node.js para .docx")
        print(f"  📏 Caracteres totales : {len(monografia):,}")
        print()

        # ── Vista previa ───────────────────────────────────────────────────────
        ver = input("  ¿Ver la monografía en pantalla? (s/n) [n]: ").strip().lower()
        if ver == 's':
            print("\n" + "="*70)
            print(monografia)
            print("="*70)

    except KeyboardInterrupt:
        print("\n\n  ⚠  Proceso interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n  ❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
