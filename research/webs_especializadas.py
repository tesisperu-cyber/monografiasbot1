"""
Webs Especializadas por Área Académica
========================================
Se activa automáticamente según la especialidad ingresada por el usuario.
Hace scraping de webs relevantes al área y extrae contenido real.
"""

import requests
import urllib.parse
import re
from bs4 import BeautifulSoup


# ── Mapa de especialidades → webs ─────────────────────────────────────────────
WEBS_POR_ESPECIALIDAD = {

    "derecho": [
        {"nombre": "LP Derecho (Perú)",          "url": "https://lpderecho.pe/?s={tema}",                        "tipo": "search"},
        {"nombre": "Derecho y Cambio Social",     "url": "https://derechoycambiosocial.com/?s={tema}",            "tipo": "search"},
        {"nombre": "Dialnet Derecho",             "url": "https://dialnet.unirioja.es/buscar/documentos?querysDismax.DOCUMENTAL_TODO={tema}&showMeta=true&filtros%5B0%5D.campo=TC&filtros%5B0%5D.clave=Derecho", "tipo": "dialnet"},
        {"nombre": "IUS ET VERITAS (PUCP)",       "url": "https://revistas.pucp.edu.pe/index.php/iusetveritas/search/search?query={tema}", "tipo": "search"},
        {"nombre": "THEMIS Revista de Derecho",   "url": "https://revistas.pucp.edu.pe/index.php/themis/search/search?query={tema}",       "tipo": "search"},
    ],

    "educacion": [
        {"nombre": "Redalyc Educación",           "url": "https://www.redalyc.org/busquedaArticuloFiltros.oa?q={tema}&area=5", "tipo": "search"},
        {"nombre": "SciELO Educación",            "url": "https://www.scielo.org/es/revistas/?status=current&subject_areas=HU", "tipo": "static"},
        {"nombre": "RIEOEI (OEI)",                "url": "https://rieoei.org/RIE/issue/search?query={tema}",      "tipo": "search"},
        {"nombre": "Perfiles Educativos (UNAM)",  "url": "https://www.iisue.unam.mx/perfiles/busqueda?q={tema}",  "tipo": "search"},
        {"nombre": "Educación XX1 (UNED)",        "url": "https://revistas.uned.es/index.php/educacionXX1/search/search?query={tema}", "tipo": "search"},
    ],

    "medicina": [
        {"nombre": "SciELO Salud",                "url": "https://search.scielo.org/?q={tema}&lang=es&filter%5Bin%5D%5B%5D=scl", "tipo": "scielo"},
        {"nombre": "Revista Peruana de Medicina", "url": "https://rpmesp.ins.gob.pe/rpmesp/buscar/busqueda?q={tema}", "tipo": "search"},
        {"nombre": "Revista Médica Herediana",    "url": "https://revistas.upch.edu.pe/index.php/RMH/search/search?query={tema}", "tipo": "search"},
        {"nombre": "ALAN Nutrición",              "url": "https://alanrevista.org/ediciones/index.php?q={tema}",  "tipo": "search"},
        {"nombre": "Medline Plus ES",             "url": "https://medlineplus.gov/spanish/search.html?q={tema}",  "tipo": "search"},
    ],

    "economia": [
        {"nombre": "CEPAL",                       "url": "https://repositorio.cepal.org/search?query={tema}&rpp=10", "tipo": "cepal"},
        {"nombre": "BCRP (Banco Central Perú)",   "url": "https://www.bcrp.gob.pe/publicaciones/buscador.html?q={tema}", "tipo": "search"},
        {"nombre": "BID (Banco Interamericano)",  "url": "https://publications.iadb.org/es/search?q={tema}",      "tipo": "search"},
        {"nombre": "Banco Mundial",               "url": "https://openknowledge.worldbank.org/discover?query={tema}&filtertype_0=subject&filter_0=Economics", "tipo": "search"},
        {"nombre": "ECLAC Papers",                "url": "https://repositorio.cepal.org/search?query={tema}",     "tipo": "cepal"},
    ],

    "psicologia": [
        {"nombre": "Redalyc Psicología",          "url": "https://www.redalyc.org/busquedaArticuloFiltros.oa?q={tema}&area=4", "tipo": "search"},
        {"nombre": "Revista Latinoam. Psicología","url": "https://www.redalyc.org/revista.oa?id=805",             "tipo": "static"},
        {"nombre": "Psicothema",                  "url": "https://www.psicothema.com/busqueda.asp?busqueda={tema}","tipo": "search"},
        {"nombre": "Interdisciplinaria",          "url": "https://www.redalyc.org/revista.oa?id=180",             "tipo": "static"},
    ],

    "ingenieria": [
        # ── Ingeniería General ────────────────────────────────────────────────
        {"nombre": "IEEE Xplore",                 "url": "https://ieeexplore.ieee.org/search/searchresult.jsp?queryText={tema}", "tipo": "search"},
        {"nombre": "arXiv CS/Eng",                "url": "https://arxiv.org/search/?query={tema}&searchtype=all",               "tipo": "search"},
        {"nombre": "SciELO Tecnología",           "url": "https://search.scielo.org/?q={tema}&lang=es",                         "tipo": "search"},
        {"nombre": "Dialnet Ingeniería",          "url": "https://dialnet.unirioja.es/buscar/documentos?querysDismax.DOCUMENTAL_TODO={tema}&filtros%5B0%5D.campo=TC&filtros%5B0%5D.clave=Ingenier%C3%ADa", "tipo": "search"},
        {"nombre": "Redalyc Ingeniería",          "url": "https://www.redalyc.org/busquedaArticuloFiltros.oa?q={tema}&area=7",  "tipo": "search"},
        # ── Ingeniería de Minas / Minería ─────────────────────────────────────
        {"nombre": "SME (Mining Engineering)",    "url": "https://www.smenet.org/publications-resources/mine-library?q={tema}", "tipo": "search"},
        {"nombre": "IIMP (Instituto Ing. Minas Perú)", "url": "https://iimp.org.pe/busqueda?q={tema}",                          "tipo": "search"},
        {"nombre": "Mining Technology Journal",   "url": "https://www.tandfonline.com/action/doSearch?query={tema}&searchField=all&target=journal&journalCode=ymte20", "tipo": "search"},
        {"nombre": "Journal of Mining Science",   "url": "https://link.springer.com/search?query={tema}&search-within=Journal&facet-journal-id=10913", "tipo": "search"},
        {"nombre": "MineLib (repositorio minero)","url": "https://minelib.readthedocs.io/",                                     "tipo": "static"},
        {"nombre": "MINEM Perú (publicaciones)",  "url": "https://www.minem.gob.pe/minem/archivos/publicaciones?s={tema}",     "tipo": "search"},
        # ── Estadística / Geoestadística ──────────────────────────────────────
        {"nombre": "Journal Mathematical Geology","url": "https://link.springer.com/search?query={tema}&search-within=Journal&facet-journal-id=11004", "tipo": "search"},
        {"nombre": "Computers & Geosciences",     "url": "https://www.sciencedirect.com/search?qs={tema}&pub=Computers+%26+Geosciences", "tipo": "search"},
        {"nombre": "Applied Geochemistry",        "url": "https://www.sciencedirect.com/search?qs={tema}&pub=Applied+Geochemistry",       "tipo": "search"},
        {"nombre": "arXiv Statistics",            "url": "https://arxiv.org/search/?query={tema}&searchtype=all&start=0&source=stat",     "tipo": "search"},
        {"nombre": "SciELO Geociencias",          "url": "https://search.scielo.org/?q={tema}&lang=es&filter%5Bin%5D%5B%5D=cub",         "tipo": "search"},
        # ── Geología / Geotecnia ──────────────────────────────────────────────
        {"nombre": "INGEMMET (Geología Perú)",    "url": "https://geocatmin.ingemmet.gob.pe/geocatmin/",                        "tipo": "static"},
        {"nombre": "Boletín INGEMMET",            "url": "https://repositorio.ingemmet.gob.pe/search?query={tema}",             "tipo": "search"},
        {"nombre": "SGP (Soc. Geológica Perú)",   "url": "https://sgp.org.pe/boletin/?s={tema}",                               "tipo": "search"},
        {"nombre": "Journal of Geochemical Expl.","url": "https://www.sciencedirect.com/search?qs={tema}&pub=Journal+of+Geochemical+Exploration", "tipo": "search"},
    ],

    "ingenieria_minas": [
        {"nombre": "SME Mining Engineering",      "url": "https://www.smenet.org/publications-resources/mine-library?q={tema}", "tipo": "search"},
        {"nombre": "IIMP Perú",                   "url": "https://iimp.org.pe/busqueda?q={tema}",                               "tipo": "search"},
        {"nombre": "Mining Technology Journal",   "url": "https://www.tandfonline.com/action/doSearch?query={tema}&searchField=all&target=journal&journalCode=ymte20", "tipo": "search"},
        {"nombre": "Journal of Mining Science",   "url": "https://link.springer.com/search?query={tema}&search-within=Journal&facet-journal-id=10913", "tipo": "search"},
        {"nombre": "MINEM Perú",                  "url": "https://www.minem.gob.pe/minem/archivos/publicaciones?s={tema}",     "tipo": "search"},
        {"nombre": "Boletín INGEMMET",            "url": "https://repositorio.ingemmet.gob.pe/search?query={tema}",             "tipo": "search"},
        {"nombre": "SGP Geología Perú",           "url": "https://sgp.org.pe/boletin/?s={tema}",                               "tipo": "search"},
        {"nombre": "Journal Geochemical Explor.", "url": "https://www.sciencedirect.com/search?qs={tema}&pub=Journal+of+Geochemical+Exploration", "tipo": "search"},
        {"nombre": "Computers & Geosciences",     "url": "https://www.sciencedirect.com/search?qs={tema}&pub=Computers+%26+Geosciences", "tipo": "search"},
        {"nombre": "Mathematical Geosciences",    "url": "https://link.springer.com/search?query={tema}&search-within=Journal&facet-journal-id=11004", "tipo": "search"},
        {"nombre": "SciELO Geociencias",          "url": "https://search.scielo.org/?q={tema}&lang=es",                        "tipo": "search"},
        {"nombre": "Redalyc Ingeniería",          "url": "https://www.redalyc.org/busquedaArticuloFiltros.oa?q={tema}&area=7", "tipo": "search"},
        {"nombre": "arXiv Statistics/Geo",        "url": "https://arxiv.org/search/?query={tema}&searchtype=all",              "tipo": "search"},
    ],

    "estadistica": [
        {"nombre": "arXiv Statistics",            "url": "https://arxiv.org/search/?query={tema}&searchtype=all&source=stat",  "tipo": "search"},
        {"nombre": "Journal of Statistics",       "url": "https://link.springer.com/search?query={tema}&search-within=Journal&facet-journal-id=10985", "tipo": "search"},
        {"nombre": "Redalyc Estadística",         "url": "https://www.redalyc.org/busquedaArticuloFiltros.oa?q={tema}",       "tipo": "search"},
        {"nombre": "SciELO Matemáticas",          "url": "https://search.scielo.org/?q={tema}&lang=es",                       "tipo": "search"},
        {"nombre": "Computers & Geosciences",     "url": "https://www.sciencedirect.com/search?qs={tema}&pub=Computers+%26+Geosciences", "tipo": "search"},
    ],

    "administracion": [
        {"nombre": "Redalyc Administración",      "url": "https://www.redalyc.org/busquedaArticuloFiltros.oa?q={tema}&area=5", "tipo": "search"},
        {"nombre": "ESAN (Perú)",                 "url": "https://www.esan.edu.pe/sala-de-prensa/publicaciones/?s={tema}", "tipo": "search"},
        {"nombre": "Harvard Business Review ES",  "url": "https://hbr.org/search?term={tema}",                    "tipo": "search"},
        {"nombre": "Cuadernos de Gestión",        "url": "https://www.ehu.eus/cuadernosdegestion/revista/es/buscar?q={tema}", "tipo": "search"},
    ],

    "ciencias_sociales": [
        {"nombre": "CLACSO",                      "url": "https://biblioteca.clacso.edu.ar/buscar/results.php?q={tema}", "tipo": "clacso"},
        {"nombre": "Redalyc CS",                  "url": "https://www.redalyc.org/busquedaArticuloFiltros.oa?q={tema}&area=6", "tipo": "search"},
        {"nombre": "FLACSO",                      "url": "https://www.flacso.org/publicaciones?search={tema}",    "tipo": "search"},
        {"nombre": "Dialnet CS",                  "url": "https://dialnet.unirioja.es/buscar/documentos?querysDismax.DOCUMENTAL_TODO={tema}", "tipo": "dialnet"},
    ],

    "medio_ambiente": [
        {"nombre": "SINIA (Perú)",                "url": "https://sinia.minam.gob.pe/notas/search?q={tema}",     "tipo": "search"},
        {"nombre": "PNUMA / UNEP ES",             "url": "https://www.unep.org/es/search?query={tema}",          "tipo": "search"},
        {"nombre": "Redalyc Ambiental",           "url": "https://www.redalyc.org/busquedaArticuloFiltros.oa?q={tema}&area=3", "tipo": "search"},
        {"nombre": "SciELO Ecología",             "url": "https://search.scielo.org/?q={tema}&lang=es",          "tipo": "scielo"},
    ],

    "enfermeria": [
        {"nombre": "Index Enfermería",            "url": "https://index-f.com/new/busqueda.php?texto={tema}",    "tipo": "search"},
        {"nombre": "SciELO Enfermería",           "url": "https://search.scielo.org/?q={tema}&lang=es",          "tipo": "scielo"},
        {"nombre": "Aquichan",                    "url": "https://aquichan.unisabana.edu.co/index.php/aquichan/search/search?query={tema}", "tipo": "search"},
    ],

    "contabilidad": [
        {"nombre": "Contaduría y Administración", "url": "https://www.cya.unam.mx/index.php/cya/search/search?query={tema}", "tipo": "search"},
        {"nombre": "Revista de Contabilidad",     "url": "https://www.elsevier.es/es-revista-revista-contabilidad-spanish-accounting-344-busqueda?q={tema}", "tipo": "search"},
        {"nombre": "BCRP Estadísticas",           "url": "https://www.bcrp.gob.pe/estadisticas.html",            "tipo": "static"},
    ],

    # Fallback genérico para cualquier especialidad no listada
    "general": [
        {"nombre": "Dialnet",                     "url": "https://dialnet.unirioja.es/buscar/documentos?querysDismax.DOCUMENTAL_TODO={tema}", "tipo": "dialnet"},
        {"nombre": "Redalyc General",             "url": "https://www.redalyc.org/busquedaArticuloFiltros.oa?q={tema}", "tipo": "search"},
        {"nombre": "CLACSO General",              "url": "https://biblioteca.clacso.edu.ar/buscar/results.php?q={tema}", "tipo": "clacso"},
    ],
}

# Alias para detectar especialidad del texto ingresado por el usuario
ALIAS_ESPECIALIDAD = {
    "derecho":           ["derecho", "jurídic", "legal", "ley", "leyes", "abogad", "jurisprudencia", "penal", "civil", "constitucional", "laboral"],
    "educacion":         ["educac", "pedagogía", "pedagog", "docente", "enseñanza", "aprendizaje", "escuela", "universidad", "didáctica"],
    "medicina":          ["medicina", "médic", "salud", "clínic", "hospital", "enfermedad", "farmac", "cirugía", "diagnóst"],
    "economia":          ["economía", "económic", "finanzas", "financier", "mercado", "macroeconom", "microeconom", "fiscal", "monetar"],
    "psicologia":        ["psicología", "psicológ", "psiquiatr", "mental", "conductual", "cognitiv", "terapia"],
    "ingenieria_minas":  ["minas", "minería", "minero", "mineral", "metalurg", "geoestadíst", "geología", "geotecn",
                          "yacimiento", "reserva mineral", "ley de mineral", "concentración", "flotación",
                          "lixiviación", "operación minera", "tajo", "socavón", "perforación", "voladura",
                          "geoestadística", "kriging", "variograma", "block model"],
    "estadistica":       ["estadístic", "estadistic", "probabilidad", "regresión", "correlación", "muestreo",
                          "análisis multivariado", "series temporales", "inferencia", "hipótesis"],
    "ingenieria":        ["ingeniería", "ingenier", "sistemas", "software", "hardware", "tecnología",
                          "informática", "computación", "electrónica", "civil", "mecánic", "químic",
                          "industrial", "ambiental ing", "telecomunicaciones"],
    "administracion":    ["administración", "administrat", "gestión", "gerencia", "management", "empresa", "organizacion", "negocios"],
    "ciencias_sociales": ["sociología", "sociolog", "político", "ciencias sociales", "antropolog", "historia", "geografía"],
    "medio_ambiente":    ["ambiente", "ambiental", "ecología", "ecológ", "sostenible", "sustentable", "clima", "biodiversidad"],
    "enfermeria":        ["enfermería", "enfermer", "cuidados", "nursing"],
    "contabilidad":      ["contabilidad", "contable", "contaduría", "auditoría", "tributar", "fiscal", "impuesto"],
}


def detectar_especialidad(especialidad_usuario: str, tema: str = "") -> str:
    """
    Detecta el área académica a partir de la especialidad Y el tema ingresados.
    El tema puede revelar sub-especialidades más específicas.
    """
    texto = (especialidad_usuario + " " + tema).lower()
    # Primero buscar sub-especialidades más específicas
    priority = ["ingenieria_minas", "estadistica", "enfermeria", "contabilidad"]
    for area in priority:
        for palabra in ALIAS_ESPECIALIDAD.get(area, []):
            if palabra in texto:
                return area
    # Luego especialidades generales
    for area, palabras_clave in ALIAS_ESPECIALIDAD.items():
        if area in priority:
            continue
        for palabra in palabras_clave:
            if palabra in texto:
                return area
    return "general"


def obtener_webs(especialidad_usuario: str, tema: str = "") -> list[dict]:
    """Retorna la lista de webs para la especialidad detectada."""
    area = detectar_especialidad(especialidad_usuario, tema)
    webs = WEBS_POR_ESPECIALIDAD.get(area, [])
    # Siempre agregar webs generales como complemento
    if area != "general":
        webs = webs + WEBS_POR_ESPECIALIDAD["general"]
    return webs


class BuscadorEspecializado:
    """Hace scraping de webs especializadas según la especialidad del usuario."""

    def __init__(self, timeout: int = 12):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'es-PE,es;q=0.9,en;q=0.8,pt;q=0.7',
        })

    def buscar(self, tema: str, especialidad: str, tema_extra: str = "", max_por_web: int = 3) -> list[dict]:
        """Busca en todas las webs de la especialidad detectada."""
        webs    = obtener_webs(especialidad, tema_extra or tema)
        area    = detectar_especialidad(especialidad, tema_extra or tema)
        results = []

        print(f"   🌐 Área detectada: {area.upper()} — consultando {len(webs)} webs especializadas")

        for web in webs:
            try:
                url_busqueda = web["url"].replace("{tema}", urllib.parse.quote(tema))
                tipo         = web.get("tipo", "search")
                nombre       = web["nombre"]

                res = self._scrape(url_busqueda, tema, tipo, nombre, max_por_web)
                results.extend(res)
                if res:
                    print(f"      ✓ {nombre}: {len(res)} resultados")
                import time; time.sleep(0.5)

            except Exception as e:
                print(f"      ⚠ {web['nombre']}: {str(e)[:50]}")

        return results

    def _scrape(self, url: str, tema: str, tipo: str, nombre: str, n: int) -> list[dict]:
        """Scraping genérico con BeautifulSoup."""
        try:
            r = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            if r.status_code not in (200, 301, 302):
                return []

            soup = BeautifulSoup(r.text, 'html.parser')

            # Eliminar scripts, estilos y navegación
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()

            results = []

            # ── Buscar artículos / entradas con patrones comunes ──────────────
            # Busca elementos que parezcan títulos de artículos
            candidatos = (
                soup.find_all('h2', limit=n*2) +
                soup.find_all('h3', limit=n*2) +
                soup.find_all(class_=re.compile(r'title|titulo|entry|article|result|item', re.I), limit=n*2)
            )

            vistos = set()
            for elem in candidatos:
                # Obtener texto del título
                titulo = elem.get_text(strip=True)
                if not titulo or len(titulo) < 15 or titulo.lower() in vistos:
                    continue
                vistos.add(titulo.lower()[:50])

                # Buscar enlace más cercano
                enlace = elem.find('a') or elem.find_parent('a')
                if not enlace:
                    enlace = elem.find_next('a')
                href = ''
                if enlace and enlace.get('href'):
                    href = enlace['href']
                    if href.startswith('/'):
                        base = '/'.join(url.split('/')[:3])
                        href = base + href

                # Buscar resumen cercano
                resumen = ''
                siguiente = elem.find_next_sibling()
                if siguiente:
                    resumen = siguiente.get_text(strip=True)[:300]
                if not resumen:
                    padre = elem.find_parent()
                    if padre:
                        resumen = padre.get_text(strip=True)[:300]

                # Filtrar si no tiene relación con el tema
                if tema.lower()[:10] not in titulo.lower() and \
                   tema.lower()[:10] not in resumen.lower():
                    # Igual lo incluyo si es de una web especializada
                    pass

                results.append({
                    'titulo':  titulo[:150],
                    'autores': 'Autor desconocido',
                    'anio':    _extraer_anio(titulo + ' ' + resumen),
                    'resumen': resumen[:400],
                    'doi':     '',
                    'url':     href,
                    'revista': nombre,
                    'fuente':  nombre,
                    'idioma':  'es',
                })

                if len(results) >= n:
                    break

            # Si no encontró nada con el método anterior, extraer párrafos relevantes
            if not results:
                parrafos = soup.find_all('p')
                for p in parrafos:
                    texto = p.get_text(strip=True)
                    if len(texto) > 100 and tema.lower()[:8] in texto.lower():
                        results.append({
                            'titulo':  texto[:80] + '...',
                            'autores': nombre,
                            'anio':    's.f.',
                            'resumen': texto[:400],
                            'doi':     '',
                            'url':     url,
                            'revista': nombre,
                            'fuente':  nombre,
                            'idioma':  'es',
                        })
                        if len(results) >= n:
                            break

            return results

        except Exception as e:
            return []


# ── Helpers ────────────────────────────────────────────────────────────────────
def _extraer_anio(texto: str) -> str:
    """Extrae año de publicación del texto si existe."""
    match = re.search(r'\b(19[8-9]\d|20[0-2]\d)\b', texto)
    return match.group(0) if match else 's.f.'
