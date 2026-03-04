"""
Generador de documentos Word (.docx) para MonografiasBot1
Llama a un script Node.js para crear el .docx con formato académico.
"""

import os
import json
import tempfile
import subprocess
import sys


def generar_docx(secciones: dict, contexto: dict, ruta_salida: str) -> bool:
    """
    Genera un archivo .docx académico con todas las secciones de la monografía.
    Retorna True si tuvo éxito.
    """
    # Preparar datos para pasar al script Node
    datos = {
        'tema':         contexto.get('tema', ''),
        'curso':        contexto.get('curso', ''),
        'especialidad': contexto.get('especialidad', ''),
        'nivel':        contexto.get('nivel', ''),
        'paginas':      contexto.get('paginas', 0),
        'introduccion': secciones.get('introduccion', ''),
        'desarrollo':   secciones.get('desarrollo', ''),
        'conclusiones': secciones.get('conclusiones', ''),
        'referencias':  secciones.get('referencias', ''),
        'salida':       ruta_salida,
    }

    # Escribir datos a archivo temporal JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                     delete=False, encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False)
        json_path = f.name

    # Ruta al script Node.js (mismo directorio que este archivo)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    node_script = os.path.join(script_dir, 'generar_docx.js')

    try:
        result = subprocess.run(
            ['node', node_script, json_path],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  ⚠ Error generando DOCX: {result.stderr[:200]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print("  ⚠ Timeout generando DOCX")
        return False
    except FileNotFoundError:
        print("  ⚠ Node.js no encontrado. Instala Node.js para generar .docx")
        return False
    finally:
        os.unlink(json_path)
