"""
Buscador Académico Multi-Fuente
================================
Consulta: Semantic Scholar, OpenAlex, CrossRef, PubMed, Europe PMC,
          DOAJ, arXiv, SciELO, Open Library,
          BASE (Bielefeld), CORE.ac.uk, búsqueda web general,
          Wikipedia ES/EN/PT (contenido + referencias reales).
"""

import requests
import urllib.parse
import time
import re


class BuscadorAcademico:
    def __init__(self, timeout: int = 12):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MonografiasBot/1.0 (academic research; mailto:research@monografiasbot.com)'
        })

    def buscar(self, tema: str, max_resultados: int = 50) -> list[dict]:
        """Busca en todas las fuentes y retorna lista unificada de resultados."""
        print(f"   🔍 Buscando: '{tema}'")
        todos = []

        fuentes = [
            ("Semantic Scholar", self._semantic_scholar),
            ("OpenAlex",         self._openalex),
            ("CrossRef",         self._crossref),
            ("PubMed",           self._pubmed),
            ("Europe PMC",       self._europe_pmc),
            ("DOAJ",             self._doaj),
            ("arXiv",            self._arxiv),
            ("SciELO",           self._scielo),
            ("Open Library",     self._open_library),
            ("CORE.ac.uk",       self._core),
            ("BASE",             self._base),
            ("Web General",      self._web_general),
            ("Wikipedia ES",     self._wikipedia_es),
            ("Wikipedia EN",     self._wikipedia_en),
            ("Wikipedia PT",     self._wikipedia_pt),
        ]

        por_fuente = max(3, max_resultados // len(fuentes))

        for nombre, fn in fuentes:
            try:
                resultados = fn(tema, por_fuente)
                todos.extend(resultados)
                print(f"      ✓ {nombre}: {len(resultados)} resultados")
                time.sleep(0.3)
            except Exception as e:
                print(f"      ⚠ {nombre}: {str(e)[:60]}")

        # Deduplicar por título
        vistos = set()
        unicos = []
        for r in todos:
            clave = r.get('titulo', '').lower()[:60]
            if clave and clave not in vistos:
                vistos.add(clave)
                unicos.append(r)

        return unicos[:max_resultados]

    # ── Semantic Scholar ───────────────────────────────────────────────────────
    def _semantic_scholar(self, tema: str, n: int) -> list[dict]:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            'query': tema,
            'limit': n,
            'fields': 'title,authors,year,abstract,externalIds,venue'
        }
        r = self.session.get(url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            return []
        items = r.json().get('data', [])
        results = []
        for item in items:
            autores = ", ".join([a.get('name','') for a in item.get('authors',[])][:3])
            doi = item.get('externalIds', {}).get('DOI', '')
            results.append({
                'titulo':  item.get('title',''),
                'autores': autores or 'Autor desconocido',
                'anio':    str(item.get('year', 's.f.')),
                'resumen': item.get('abstract','')[:400],
                'doi':     doi,
                'url':     f"https://doi.org/{doi}" if doi else '',
                'revista': item.get('venue',''),
                'fuente':  'Semantic Scholar',
                'idioma':  'en',
            })
        return results

    # ── OpenAlex ──────────────────────────────────────────────────────────────
    def _openalex(self, tema: str, n: int) -> list[dict]:
        url = "https://api.openalex.org/works"
        params = {
            'search': tema,
            'per-page': n,
            'select': 'title,authorships,publication_year,abstract_inverted_index,doi,primary_location,language'
        }
        r = self.session.get(url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            return []
        items = r.json().get('results', [])
        results = []
        for item in items:
            autores = ", ".join([
                a.get('author', {}).get('display_name','')
                for a in item.get('authorships', [])[:3]
            ])
            doi = item.get('doi','').replace('https://doi.org/','')
            aii = item.get('abstract_inverted_index') or {}
            abstract = _reconstruct_abstract(aii)
            loc = item.get('primary_location') or {}
            revista = (loc.get('source') or {}).get('display_name','')
            results.append({
                'titulo':  item.get('title',''),
                'autores': autores or 'Autor desconocido',
                'anio':    str(item.get('publication_year','s.f.')),
                'resumen': abstract[:400],
                'doi':     doi,
                'url':     item.get('doi',''),
                'revista': revista,
                'fuente':  'OpenAlex',
                'idioma':  item.get('language','en') or 'en',
            })
        return results

    # ── CrossRef ──────────────────────────────────────────────────────────────
    def _crossref(self, tema: str, n: int) -> list[dict]:
        url = "https://api.crossref.org/works"
        params = {'query': tema, 'rows': n, 'select': 'title,author,published,abstract,DOI,container-title'}
        r = self.session.get(url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            return []
        items = r.json().get('message', {}).get('items', [])
        results = []
        for item in items:
            titulo = (item.get('title') or [''])[0]
            autores_raw = item.get('author', [])
            autores = ", ".join([
                f"{a.get('family','')}, {a.get('given','')[0]}." if a.get('given') else a.get('family','')
                for a in autores_raw[:3]
            ])
            anio = ''
            pub = item.get('published', {})
            dp  = pub.get('date-parts', [['']])
            if dp and dp[0]:
                anio = str(dp[0][0])
            doi = item.get('DOI','')
            revista = (item.get('container-title') or [''])[0]
            results.append({
                'titulo':  titulo,
                'autores': autores or 'Autor desconocido',
                'anio':    anio or 's.f.',
                'resumen': _strip_html(item.get('abstract',''))[:400],
                'doi':     doi,
                'url':     f"https://doi.org/{doi}" if doi else '',
                'revista': revista,
                'fuente':  'CrossRef',
                'idioma':  'en',
            })
        return results

    # ── PubMed ────────────────────────────────────────────────────────────────
    def _pubmed(self, tema: str, n: int) -> list[dict]:
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {'db':'pubmed','term':tema,'retmax':n,'retmode':'json'}
        r = self.session.get(search_url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            return []
        ids = r.json().get('esearchresult',{}).get('idlist',[])
        if not ids:
            return []
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params2 = {'db':'pubmed','id':','.join(ids),'retmode':'json'}
        r2 = self.session.get(fetch_url, params=params2, timeout=self.timeout)
        if r2.status_code != 200:
            return []
        uids = r2.json().get('result',{})
        results = []
        for uid in ids:
            item = uids.get(uid, {})
            if not item or uid == 'uids':
                continue
            autores = ", ".join([a.get('name','') for a in item.get('authors',[])[:3]])
            results.append({
                'titulo':  item.get('title',''),
                'autores': autores or 'Autor desconocido',
                'anio':    item.get('pubdate','s.f.')[:4],
                'resumen': '',
                'doi':     item.get('elocationid','').replace('doi: ',''),
                'url':     f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                'revista': item.get('source',''),
                'fuente':  'PubMed',
                'idioma':  'en',
            })
        return results

    # ── Europe PMC ────────────────────────────────────────────────────────────
    def _europe_pmc(self, tema: str, n: int) -> list[dict]:
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        params = {'query': tema, 'pageSize': n, 'format': 'json', 'resultType': 'core'}
        r = self.session.get(url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            return []
        items = r.json().get('resultList',{}).get('result',[])
        results = []
        for item in items:
            results.append({
                'titulo':  item.get('title',''),
                'autores': item.get('authorString','') or 'Autor desconocido',
                'anio':    str(item.get('pubYear','s.f.')),
                'resumen': item.get('abstractText','')[:400],
                'doi':     item.get('doi',''),
                'url':     f"https://doi.org/{item.get('doi','')}" if item.get('doi') else '',
                'revista': item.get('journalTitle',''),
                'fuente':  'Europe PMC',
                'idioma':  'en',
            })
        return results

    # ── DOAJ ──────────────────────────────────────────────────────────────────
    def _doaj(self, tema: str, n: int) -> list[dict]:
        url = "https://doaj.org/api/search/articles/" + urllib.parse.quote(tema)
        params = {'pageSize': n}
        r = self.session.get(url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            return []
        items = r.json().get('results', [])
        results = []
        for item in items:
            bib = item.get('bibjson', {})
            doi_list = [i.get('id','') for i in bib.get('identifier',[]) if i.get('type')=='doi']
            doi = doi_list[0] if doi_list else ''
            lang = (bib.get('journal',{}).get('language') or ['en'])[0].lower()
            results.append({
                'titulo':  bib.get('title',''),
                'autores': ", ".join([a.get('name','') for a in bib.get('author',[])[:3]]) or 'Autor desconocido',
                'anio':    str(bib.get('year','s.f.')),
                'resumen': bib.get('abstract','')[:400],
                'doi':     doi,
                'url':     f"https://doi.org/{doi}" if doi else '',
                'revista': bib.get('journal',{}).get('title',''),
                'fuente':  'DOAJ',
                'idioma':  lang,
            })
        return results

    # ── arXiv ─────────────────────────────────────────────────────────────────
    def _arxiv(self, tema: str, n: int) -> list[dict]:
        url = "http://export.arxiv.org/api/query"
        params = {
            'search_query': f'all:{urllib.parse.quote(tema)}',
            'start': 0, 'max_results': n
        }
        r = self.session.get(url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            return []
        import xml.etree.ElementTree as ET
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        root = ET.fromstring(r.text)
        results = []
        for entry in root.findall('atom:entry', ns):
            titulo  = (entry.find('atom:title', ns) or ET.Element('')).text or ''
            resumen = (entry.find('atom:summary', ns) or ET.Element('')).text or ''
            pub = entry.find('atom:published', ns)
            anio = pub.text[:4] if pub is not None and pub.text else 's.f.'
            autores = ", ".join([
                (a.find('atom:name', ns) or ET.Element('')).text or ''
                for a in entry.findall('atom:author', ns)[:3]
            ])
            link = next((lnk.get('href','') for lnk in entry.findall('atom:link', ns)
                         if lnk.get('type') == 'text/html'), '')
            results.append({
                'titulo':  titulo.replace('\n',' ').strip(),
                'autores': autores or 'Autor desconocido',
                'anio':    anio,
                'resumen': resumen[:400],
                'doi':     '',
                'url':     link,
                'revista': f'arXiv:{link.split("/")[-1]}' if link else 'arXiv',
                'fuente':  'arXiv',
                'idioma':  'en',
            })
        return results

    # ── SciELO ────────────────────────────────────────────────────────────────
    def _scielo(self, tema: str, n: int) -> list[dict]:
        url = "https://api.openalex.org/works"
        params = {
            'search': tema,
            'filter': 'primary_location.source.host_organization:I4210139997',
            'per-page': n,
            'select': 'title,authorships,publication_year,doi,primary_location,language'
        }
        r = self.session.get(url, params=params, timeout=self.timeout)
        results = []
        if r.status_code == 200:
            for item in r.json().get('results', []):
                autores = ", ".join([
                    a.get('author',{}).get('display_name','')
                    for a in item.get('authorships',[])[:3]
                ])
                doi = item.get('doi','').replace('https://doi.org/','')
                loc = item.get('primary_location') or {}
                revista = (loc.get('source') or {}).get('display_name','')
                results.append({
                    'titulo':  item.get('title',''),
                    'autores': autores or 'Autor desconocido',
                    'anio':    str(item.get('publication_year','s.f.')),
                    'resumen': '',
                    'doi':     doi,
                    'url':     item.get('doi',''),
                    'revista': revista,
                    'fuente':  'SciELO',
                    'idioma':  item.get('language','es') or 'es',
                })
        return results

    # ── Open Library ──────────────────────────────────────────────────────────
    def _open_library(self, tema: str, n: int) -> list[dict]:
        url = "https://openlibrary.org/search.json"
        params = {'q': tema, 'limit': n, 'fields': 'title,author_name,first_publish_year,subject,first_sentence'}
        r = self.session.get(url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            return []
        results = []
        for item in r.json().get('docs', []):
            autores = ", ".join((item.get('author_name') or [])[:3])
            # Obtener primera oración como resumen si existe
            primera = item.get('first_sentence', {})
            resumen = primera.get('value', '') if isinstance(primera, dict) else str(primera)
            if not resumen:
                resumen = f"Libro sobre: {', '.join((item.get('subject') or [])[:4])}"
            results.append({
                'titulo':  item.get('title',''),
                'autores': autores or 'Autor desconocido',
                'anio':    str(item.get('first_publish_year','s.f.')),
                'resumen': resumen[:400],
                'doi':     '',
                'url':     f"https://openlibrary.org/search?q={urllib.parse.quote(item.get('title',''))}",
                'revista': '',
                'fuente':  'Open Library',
                'idioma':  'en',
            })
        return results

    # ── CORE.ac.uk ────────────────────────────────────────────────────────────
    def _core(self, tema: str, n: int) -> list[dict]:
        """
        CORE agrega millones de artículos open access con texto completo.
        API pública sin key para búsquedas básicas.
        """
        url = "https://api.core.ac.uk/v3/search/works"
        params = {
            'q':        tema,
            'limit':    n,
            'fields':   'title,authors,yearPublished,abstract,doi,downloadUrl,publisher,language',
        }
        try:
            r = self.session.get(url, params=params, timeout=self.timeout)
            if r.status_code != 200:
                return []
            items = r.json().get('results', [])
            results = []
            for item in items:
                autores_raw = item.get('authors') or []
                if autores_raw and isinstance(autores_raw[0], dict):
                    autores = ", ".join([a.get('name','') for a in autores_raw[:3]])
                else:
                    autores = ", ".join([str(a) for a in autores_raw[:3]])
                doi      = item.get('doi','') or ''
                url_pdf  = item.get('downloadUrl','') or ''
                idioma   = (item.get('language') or {}).get('code','en') if isinstance(item.get('language'), dict) else 'en'
                results.append({
                    'titulo':  item.get('title',''),
                    'autores': autores or 'Autor desconocido',
                    'anio':    str(item.get('yearPublished','s.f.')),
                    'resumen': (item.get('abstract') or '')[:400],
                    'doi':     doi,
                    'url':     url_pdf or (f"https://doi.org/{doi}" if doi else ''),
                    'revista': item.get('publisher',''),
                    'fuente':  'CORE.ac.uk',
                    'idioma':  idioma,
                })
            return results
        except Exception:
            return []

    # ── BASE (Bielefeld Academic Search Engine) ───────────────────────────────
    def _base(self, tema: str, n: int) -> list[dict]:
        """
        BASE indexa más de 350 millones de documentos académicos open access.
        Usa su API OAI-PMH / REST pública.
        """
        url = "https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi"
        params = {
            'func':    'PerformSearch',
            'query':   f'dcterms.subject:{tema} OR dcterms.title:{tema}',
            'hits':    n,
            'offset':  0,
            'format':  'json',
        }
        try:
            r = self.session.get(url, params=params, timeout=self.timeout)
            if r.status_code != 200:
                return []
            docs = r.json().get('response', {}).get('docs', [])
            results = []
            for doc in docs:
                titulo  = doc.get('dctitle','') or ''
                if isinstance(titulo, list):
                    titulo = titulo[0] if titulo else ''
                autores_raw = doc.get('dccreator','') or ''
                if isinstance(autores_raw, list):
                    autores = ", ".join(autores_raw[:3])
                else:
                    autores = str(autores_raw)
                anio_raw = doc.get('dcyear','') or doc.get('dcdateyear','') or 's.f.'
                if isinstance(anio_raw, list):
                    anio_raw = anio_raw[0] if anio_raw else 's.f.'
                resumen_raw = doc.get('dcdescription','') or ''
                if isinstance(resumen_raw, list):
                    resumen_raw = ' '.join(resumen_raw)
                url_doc = doc.get('dclink','') or ''
                if isinstance(url_doc, list):
                    url_doc = url_doc[0] if url_doc else ''
                idioma_raw = doc.get('dclanguage','en') or 'en'
                if isinstance(idioma_raw, list):
                    idioma_raw = idioma_raw[0] if idioma_raw else 'en'
                results.append({
                    'titulo':  titulo,
                    'autores': autores or 'Autor desconocido',
                    'anio':    str(anio_raw),
                    'resumen': _strip_html(resumen_raw)[:400],
                    'doi':     doc.get('dcidentifier','') or '',
                    'url':     url_doc,
                    'revista': doc.get('dcpublisher','') or '',
                    'fuente':  'BASE',
                    'idioma':  idioma_raw[:2].lower(),
                })
            return results
        except Exception:
            return []

    # ── Web General (DuckDuckGo instant answers + búsqueda libre) ────────────
    def _web_general(self, tema: str, n: int) -> list[dict]:
        """
        Búsqueda web general usando la API pública de DuckDuckGo
        para obtener contenido adicional relevante al tema.
        """
        url = "https://api.duckduckgo.com/"
        params = {
            'q':              tema + ' academic research',
            'format':         'json',
            'no_html':        1,
            'skip_disambig':  1,
        }
        try:
            r = self.session.get(url, params=params, timeout=self.timeout)
            if r.status_code != 200:
                return []
            data = r.json()
            results = []

            # Abstract principal
            abstract = data.get('Abstract','')
            abstract_url = data.get('AbstractURL','')
            abstract_src = data.get('AbstractSource','')
            if abstract and len(abstract) > 50:
                results.append({
                    'titulo':  data.get('Heading', tema),
                    'autores': abstract_src or 'Web',
                    'anio':    's.f.',
                    'resumen': abstract[:400],
                    'doi':     '',
                    'url':     abstract_url,
                    'revista': abstract_src,
                    'fuente':  'Web (DuckDuckGo)',
                    'idioma':  'en',
                })

            # Resultados relacionados
            for item in data.get('RelatedTopics', [])[:n]:
                if not isinstance(item, dict):
                    continue
                texto = item.get('Text','')
                link  = item.get('FirstURL','')
                if texto and len(texto) > 30:
                    results.append({
                        'titulo':  texto[:80],
                        'autores': 'Web',
                        'anio':    's.f.',
                        'resumen': texto[:400],
                        'doi':     '',
                        'url':     link,
                        'revista': 'Web',
                        'fuente':  'Web (DuckDuckGo)',
                        'idioma':  'en',
                    })
            return results[:n]
        except Exception:
            return []


    # ── Wikipedia (ES, EN, PT) ────────────────────────────────────────────────
    def _wikipedia(self, tema: str, n: int, lang: str) -> list[dict]:
        """
        Extrae de Wikipedia:
        1. Resumen y secciones del artículo principal
        2. Referencias externas reales (citables en APA 7)
        3. Enlaces externos como fuentes adicionales

        El contenido se usa como CONTEXTO para el LLM — no como referencia directa.
        Las referencias que extrae SÍ son citables académicamente.
        """
        base_url = f"https://{lang}.wikipedia.org/api/rest_v1"
        results  = []

        # ── Buscar artículo más relevante ─────────────────────────────────────
        search_url = f"https://{lang}.wikipedia.org/w/api.php"
        params_search = {
            'action':   'query',
            'list':     'search',
            'srsearch': tema,
            'srlimit':  3,
            'format':   'json',
        }
        try:
            rs = self.session.get(search_url, params=params_search, timeout=self.timeout)
            if rs.status_code != 200:
                return []
            hits = rs.json().get('query', {}).get('search', [])
            if not hits:
                return []
            titulo_wiki = hits[0].get('title', '')
        except Exception:
            return []

        # ── Obtener resumen y secciones ───────────────────────────────────────
        try:
            r_summary = self.session.get(
                f"{base_url}/page/summary/{urllib.parse.quote(titulo_wiki)}",
                timeout=self.timeout
            )
            if r_summary.status_code == 200:
                data = r_summary.json()
                resumen = data.get('extract', '')[:600]
                url_wiki = data.get('content_urls', {}).get('desktop', {}).get('page', '')
                results.append({
                    'titulo':  f"[Wikipedia {lang.upper()}] {titulo_wiki}",
                    'autores': f'Wikipedia {lang.upper()} contributors',
                    'anio':    's.f.',
                    'resumen': resumen,
                    'doi':     '',
                    'url':     url_wiki,
                    'revista': f'Wikipedia {lang.upper()}',
                    'fuente':  f'Wikipedia {lang.upper()}',
                    'idioma':  lang,
                    'es_wikipedia': True,   # marcador — no usar como ref directa
                    'contenido_completo': resumen,
                })
        except Exception:
            pass

        # ── Obtener secciones con contenido ───────────────────────────────────
        try:
            params_sections = {
                'action':  'parse',
                'page':    titulo_wiki,
                'prop':    'sections|text',
                'format':  'json',
            }
            r_sec = self.session.get(search_url, params=params_sections, timeout=self.timeout)
            if r_sec.status_code == 200:
                html = r_sec.json().get('parse', {}).get('text', {}).get('*', '')
                # Extraer texto limpio de las primeras secciones
                texto_limpio = _strip_html(html)
                # Tomar primeros 1500 caracteres de contenido útil
                parrafos = [p.strip() for p in texto_limpio.split('\n') if len(p.strip()) > 80]
                contenido = ' '.join(parrafos[:8])[:1500]
                if contenido and results:
                    results[0]['contenido_completo'] = contenido
        except Exception:
            pass

        # ── Extraer referencias reales de Wikipedia ───────────────────────────
        try:
            params_refs = {
                'action':   'query',
                'titles':   titulo_wiki,
                'prop':     'extlinks',
                'ellimit':  20,
                'format':   'json',
            }
            r_refs = self.session.get(search_url, params=params_refs, timeout=self.timeout)
            if r_refs.status_code == 200:
                pages = r_refs.json().get('query', {}).get('pages', {})
                for page in pages.values():
                    for link in (page.get('extlinks') or [])[:n]:
                        url_ext = link.get('*', '') or link.get('url', '')
                        if url_ext and _es_fuente_academica(url_ext):
                            results.append({
                                'titulo':  f"Referencia externa: {url_ext[:80]}",
                                'autores': 'Autor desconocido',
                                'anio':    's.f.',
                                'resumen': f'Fuente referenciada en Wikipedia ({lang}) para el tema: {tema}',
                                'doi':     '',
                                'url':     url_ext,
                                'revista': _dominio(url_ext),
                                'fuente':  f'Wikipedia {lang.upper()} (refs)',
                                'idioma':  lang,
                            })
        except Exception:
            pass

        return results[:n]

    def _wikipedia_es(self, tema: str, n: int) -> list[dict]:
        return self._wikipedia(tema, n, 'es')

    def _wikipedia_en(self, tema: str, n: int) -> list[dict]:
        return self._wikipedia(tema, n, 'en')

    def _wikipedia_pt(self, tema: str, n: int) -> list[dict]:
        return self._wikipedia(tema, n, 'pt')


# ── Helpers ────────────────────────────────────────────────────────────────────
def _reconstruct_abstract(aii: dict) -> str:
    if not aii:
        return ''
    try:
        max_pos = max(pos for positions in aii.values() for pos in positions)
        words = [''] * (max_pos + 1)
        for word, positions in aii.items():
            for pos in positions:
                words[pos] = word
        return ' '.join(words)
    except Exception:
        return ''

def _strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text or '')

def _es_fuente_academica(url: str) -> bool:
    """Filtra solo URLs de fuentes académicas y confiables."""
    dominios_validos = [
        'doi.org', 'pubmed', 'ncbi.nlm.nih.gov', 'scholar.google',
        'jstor.org', 'scielo', 'redalyc.org', 'dialnet.unirioja.es',
        'researchgate.net', 'academia.edu', 'springer.com', 'elsevier.com',
        'wiley.com', 'tandfonline.com', 'sagepub.com', 'nature.com',
        'science.org', 'plos.org', 'frontiersin.org', 'mdpi.com',
        'arxiv.org', 'ssrn.com', 'core.ac.uk', 'base-search.net',
        'openlibrary.org', 'worldcat.org', 'books.google', 'handle.net',
        '.edu', '.ac.', 'repository', 'repositorio', 'biblioteca',
    ]
    url_lower = url.lower()
    return any(d in url_lower for d in dominios_validos)

def _dominio(url: str) -> str:
    """Extrae el dominio limpio de una URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.replace('www.', '')
    except Exception:
        return url[:40]
