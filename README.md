# 📚 MonografiasBot1

Sistema multi-agente de redacción académica automatizada, construido con **Groq + LLaMA 3.3** y un orquestador que coordina agentes especializados para generar monografías completas en español.

---

## ✨ Características

- **Agente Orquestador** que coordina el pipeline completo
- **4 agentes especializados**:
  - 📝 Agente Introducción
  - 📚 Agente Desarrollo (capítulos)
  - 🎯 Agente Conclusiones y Recomendaciones
  - 📖 Agente Referencias APA 7
- **Búsqueda en 10 bases de datos** académicas abiertas
- **Referencias en 3 idiomas**: español, inglés y portugués
- Formato **APA 7ma edición** estricto
- Adaptado a 3 niveles: **Pregrado, Maestría, Doctorado**
- Extensión configurable por el usuario (páginas)

---

## 🗂️ Estructura del proyecto

```
monografias_bot/
│
├── main.py                  # Interfaz principal de usuario (CLI)
├── orchestrator.py          # Agente Orquestador
├── requirements.txt
├── README.md
│
├── agents/
│   ├── __init__.py
│   ├── base.py              # Clase base compartida por todos los agentes
│   ├── introduccion.py      # Agente Introducción
│   ├── desarrollo.py        # Agente Desarrollo (capítulos)
│   ├── conclusiones.py      # Agente Conclusiones y Recomendaciones
│   └── referencias.py       # Agente Referencias APA 7
│
├── research/
│   ├── __init__.py
│   └── buscador.py          # Motor de búsqueda multi-fuente
│
└── utils/
    ├── __init__.py
    ├── config.py             # Configuración global (modelo, tokens, etc.)
    └── formatter.py          # Ensamblado del documento final
```

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <tu-repo>
cd monografias_bot
```

### 2. Crear entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar API Key de Groq

Obtén tu clave gratis en [console.groq.com](https://console.groq.com).

**Opción A — Variable de entorno (recomendado):**
```bash
export GROQ_API_KEY="gsk_tu_clave_aqui"   # Linux/macOS
set GROQ_API_KEY=gsk_tu_clave_aqui        # Windows
```

**Opción B — Ingresar al ejecutar:** el programa te la pedirá si no está configurada.

---

## ▶️ Uso

```bash
python main.py
```

El programa solicitará de forma interactiva:

| Campo | Descripción |
|---|---|
| **Tema** | El tema completo de la monografía |
| **Curso** | Nombre del curso o asignatura |
| **Especialidad** | Carrera o especialidad académica |
| **Nivel** | Pregrado / Maestría / Doctorado |
| **Páginas** | Cantidad de páginas deseada (mín. 5, máx. 200) |

---

## 🏗️ Arquitectura

```
Usuario
   │
   ▼
main.py  ──►  Orchestrator
                    │
                    ├── BuscadorAcademico
                    │     ├── Semantic Scholar API
                    │     ├── OpenAlex API
                    │     ├── CrossRef API
                    │     ├── PubMed API (NCBI)
                    │     ├── Europe PMC API
                    │     ├── DOAJ API
                    │     ├── arXiv API
                    │     ├── SciELO (vía OpenAlex)
                    │     ├── monografias.com (scraping)
                    │     └── Open Library API
                    │
                    ├── AgenteIntroduccion  ──► Groq/LLaMA
                    ├── AgenteDesarrollo    ──► Groq/LLaMA (por capítulo)
                    ├── AgenteConclusiones  ──► Groq/LLaMA
                    └── AgenteReferencias   ──► Groq/LLaMA
                                │
                                ▼
                         formatter.py
                                │
                                ▼
                    monografia_TEMA_FECHA.txt
```

---

## 📊 Distribución de contenido

| Sección | % del total |
|---|---|
| Introducción | 15% |
| Desarrollo (capítulos) | 60% |
| Conclusiones y Recomendaciones | 15% |
| Referencias | 10% |

El número de capítulos se adapta automáticamente:
- 5–10 páginas → 2 capítulos
- 11–20 páginas → 3 capítulos
- 21–40 páginas → 4 capítulos
- 41+ páginas → 5 capítulos

---

## 🗄️ Bases de datos consultadas

| Base de datos | Tipo | Idiomas |
|---|---|---|
| Semantic Scholar | Artículos científicos | EN |
| OpenAlex | Artículos + libros | Múltiple |
| CrossRef | DOIs y metadatos | Múltiple |
| PubMed | Ciencias de la salud | EN |
| Europe PMC | Biomedicina | EN |
| DOAJ | Revistas open access | Múltiple |
| arXiv | Preprints ciencia/tecnología | EN |
| SciELO | Iberoamérica | ES/PT |
| monografias.com | Monografías en español | ES |
| Open Library | Libros gratuitos | Múltiple |

---

## 📋 Formato de salida

La monografía se guarda como `monografia_TEMA_FECHA.txt` con la estructura:

```
PORTADA
ÍNDICE DE CONTENIDOS
I.   INTRODUCCIÓN
II.  DESARROLLO
       CAPÍTULO 1: ...
       CAPÍTULO 2: ...
       CAPÍTULO N: ...
III. CONCLUSIONES Y RECOMENDACIONES
IV.  REFERENCIAS BIBLIOGRÁFICAS (APA 7 — ES, EN, PT)
```

---

## ⚙️ Configuración avanzada

Edita `utils/config.py` para cambiar:

```python
MODEL = "llama-3.3-70b-versatile"   # o "llama-3.1-8b-instant" para mayor velocidad
MAX_TOKENS_PER_SECTION = 8000        # tokens por sección
```

---

## 🐛 Solución de problemas

| Problema | Solución |
|---|---|
| `Error 401` | Verifica que tu GROQ_API_KEY sea válida |
| `RateLimitError` | Espera unos segundos y vuelve a ejecutar |
| Monografía muy corta | Aumenta la cantidad de páginas solicitadas |
| Fuentes no encontradas | Normal si el tema es muy específico; el agente genera referencias igualmente |

---

## 📄 Licencia

MIT — libre uso académico y personal.
