"""
MonografiasBot1 — Interfaz Streamlit
=====================================
Ejecutar: streamlit run app.py
"""

import streamlit as st
import os
import tempfile
from datetime import date

st.set_page_config(
    page_title="MonografiasBot1",
    page_icon="📚",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&display=swap');
.stApp { background:#0a0a0f; }
header[data-testid="stHeader"] { background:transparent; }
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background:#12121a !important; color:#e8e8f0 !important;
    border:1px solid #2a2a3d !important;
}
.stButton > button {
    background:linear-gradient(135deg,#7c6aff,#ff6a9a);
    color:white; border:none; border-radius:10px;
    font-weight:700; font-size:16px; padding:12px 24px;
    width:100%;
}
.stButton > button:hover { opacity:0.85; }
.stDownloadButton > button {
    background:linear-gradient(135deg,#22c55e,#16a34a);
    color:white; border:none; border-radius:10px;
    font-weight:700; width:100%;
}
</style>
<div style="text-align:center;padding:20px 0 8px">
  <h1 style="font-family:'Syne',sans-serif;font-weight:800;color:#e8e8f0;
             font-size:36px;margin:0;letter-spacing:-1px;">📚 MonografiasBot1</h1>
  <p style="color:#7878a0;font-family:monospace;font-size:12px;margin-top:6px;">
    Multi-Agente IA · Groq + LLaMA · 10 Bases de Datos Académicas
  </p>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("resultado", None), ("generando", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Formulario ────────────────────────────────────────────────────────────────
with st.form("formulario"):

    st.markdown("### 🔑 API Key de Groq")
    st.caption("Obtén tu clave gratis en [groq.com](https://console.groq.com)")
    api_key = st.text_input("", type="password", placeholder="gsk_...",
                            label_visibility="collapsed")

    st.markdown("---")
    st.markdown("### 📝 Datos de la Monografía")

    tema = st.text_input("📌 Tema", placeholder="Ej: Impacto de la Inteligencia Artificial en la Educación Superior")

    col1, col2 = st.columns(2)
    with col1:
        curso = st.text_input("📖 Curso", placeholder="Ej: Metodología de la Investigación")
    with col2:
        especialidad = st.text_input("🎓 Especialidad", placeholder="Ej: Ciencias de la Educación")

    col3, col4 = st.columns(2)
    with col3:
        nivel = st.selectbox("📊 Nivel Académico", ["PREGRADO", "MAESTRIA", "DOCTORADO"])
    with col4:
        paginas = st.number_input("📄 Cantidad de Páginas", min_value=5, max_value=200, value=20, step=5)

    st.markdown("---")
    submitted = st.form_submit_button("🚀 Generar Monografía")

# ── Generación ────────────────────────────────────────────────────────────────
if submitted:
    # Validaciones
    if not api_key:
        st.error("⚠️ Ingresa tu API Key de Groq.")
        st.stop()
    if not tema:
        st.error("⚠️ Ingresa el tema de la monografía.")
        st.stop()
    if not curso:
        st.error("⚠️ Ingresa el nombre del curso.")
        st.stop()
    if not especialidad:
        st.error("⚠️ Ingresa la especialidad.")
        st.stop()

    datos = {
        'tema': tema,
        'curso': curso,
        'especialidad': especialidad,
        'nivel': nivel,
        'paginas': paginas,
    }

    st.markdown("---")
    st.markdown("### ⚙️ Agentes trabajando...")

    # Contenedor de progreso
    progreso = st.container()
    barra    = st.progress(0, text="Iniciando...")
    log_box  = st.empty()
    logs     = []

    def actualizar(msg):
        logs.append(msg)
        log_box.markdown(
            "<div style='background:#12121a;border:1px solid #2a2a3d;border-radius:8px;"
            "padding:12px;font-family:monospace;font-size:12px;color:#a0a0c0'>"
            + "<br>".join(logs) +
            "</div>",
            unsafe_allow_html=True
        )
        # Actualizar barra según etapa
        etapas = {
            "Buscando":       10,
            "encontradas":    20,
            "Introducción":   35,
            "Introducción completada": 50,
            "Desarrollo":     65,
            "Desarrollo completado":   75,
            "Conclusiones":   82,
            "Conclusiones completadas": 88,
            "Referencias":    92,
            "Referencias completadas":  96,
            "Ensamblando":    98,
        }
        for clave, pct in etapas.items():
            if clave.lower() in msg.lower():
                barra.progress(pct, text=msg)
                break

    try:
        from orchestrator import Orchestrator
        orquestador = Orchestrator(api_key=api_key)
        resultado   = orquestador.ejecutar(datos, callback=actualizar)

        barra.progress(100, text="✅ ¡Completado!")

        st.session_state.resultado = {
            'monografia': resultado['monografia'],
            'secciones':  resultado['secciones'],
            'contexto':   resultado['contexto'],
            'fuentes':    resultado['fuentes_encontradas'],
            'datos':      datos,
        }

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.stop()

# ── Resultados y descarga ─────────────────────────────────────────────────────
if st.session_state.resultado:
    r        = st.session_state.resultado
    monografia = r['monografia']
    fuentes    = r['fuentes']
    datos      = r['datos']
    secciones  = r['secciones']
    contexto   = r['contexto']

    st.markdown("---")
    st.success(f"✅ Monografía generada — {fuentes} fuentes académicas consultadas")

    fecha      = date.today().strftime("%Y%m%d")
    nombre_base = datos['tema'][:40].replace(' ', '_')
    nombre_base = "".join(c for c in nombre_base if c.isalnum() or c in ('_', '-'))

    col_a, col_b = st.columns(2)

    # ── Descarga TXT ──────────────────────────────────────────────────────────
    with col_a:
        st.download_button(
            label="📄 Descargar TXT",
            data=monografia.encode('utf-8'),
            file_name=f"monografia_{nombre_base}_{fecha}.txt",
            mime="text/plain",
        )

    # ── Descarga DOCX ─────────────────────────────────────────────────────────
    with col_b:
        try:
            from utils.docx_generator import generar_docx
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
                ruta_docx = f.name
            exito = generar_docx(secciones, contexto, ruta_docx)
            if exito and os.path.exists(ruta_docx):
                with open(ruta_docx, 'rb') as f:
                    docx_bytes = f.read()
                os.unlink(ruta_docx)
                st.download_button(
                    label="📝 Descargar Word (.docx)",
                    data=docx_bytes,
                    file_name=f"monografia_{nombre_base}_{fecha}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            else:
                st.warning("⚠️ Node.js requerido para .docx")
        except Exception as e:
            st.warning(f"⚠️ DOCX no disponible: {str(e)[:60]}")

    # ── Vista previa ──────────────────────────────────────────────────────────
    with st.expander("👁️ Vista previa de la monografía"):
        st.text_area("", monografia, height=500, label_visibility="collapsed")
