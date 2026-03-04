"""
Buscador Académico Multi-Fuente
================================
Consulta: Semantic Scholar, OpenAlex, CrossRef, PubMed, Europe PMC,
          DOAJ, arXiv, SciELO, monografias.com y libros PDF gratuitos.
"""

import requests
import urllib.parse
import time
import re
from typing import Optional


class BuscadorAcademico:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MonografiasBot/1.0 (academic research; mailto:research@monografiasbot.com)'
        })

    def buscar(self, tema: str, max_resultados: int = 30) -> list[dict]:
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
            ("monografias.com",  self._monografias_com),
            ("Open Library",     self._open_library),
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
                'resumen': item.get('abstract','')[:300],
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
            # Reconstruir abstract
            aii = item.get('abstract_inverted_index') or {}
            abstract = _reconstruct_abstract(aii)
            loc = item.get('primary_location') or {}
            revista = (loc.get('source') or {}).get('display_name','')
            results.append({
                'titulo':  item.get('title',''),
                'autores': autores or 'Autor desconocido',
                'anio':    str(item.get('publication_year','s.f.')),
                'resumen': abstract[:300],
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
                'resumen': _strip_html(item.get('abstract',''))[:300],
                'doi':     doi,
                'url':     f"https://doi.org/{doi}" if doi else '',
                'revista': revista,
                'fuente':  'CrossRef',
                'idioma':  'en',
            })
        return results

    # ── PubMed ────────────────────────────────────────────────────────────────
    def _pubmed(self, tema: str, n: int) -> list[dict]:
        # Paso 1: buscar IDs
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {'db':'pubmed','term':tema,'retmax':n,'retmode':'json'}
        r = self.session.get(search_url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            return []
        ids = r.json().get('esearchresult',{}).get('idlist',[])
        if not ids:
            return []
        # Paso 2: obtener detalles
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params2 = {'db':'pubmed','id':','.join(ids),'retmode':'json'}
        r2 = self.session.get(fetch_url, params2=params2, timeout=self.timeout)
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
            autores = item.get('authorString','')
            results.append({
                'titulo':  item.get('title',''),
                'autores': autores or 'Autor desconocido',
                'anio':    str(item.get('pubYear','s.f.')),
                'resumen': item.get('abstractText','')[:300],
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
            titulo = bib.get('title','')
            autores = ", ".join([
                f"{a.get('name','')}" for a in bib.get('author',[])[:3]
            ])
            anio = bib.get('year','s.f.')
            doi_list = [i.get('id','') for i in bib.get('identifier',[]) if i.get('type')=='doi']
            doi = doi_list[0] if doi_list else ''
            revista = bib.get('journal',{}).get('title','')
            lang = (bib.get('journal',{}).get('language') or ['en'])[0].lower()
            results.append({
                'titulo':  titulo,
                'autores': autores or 'Autor desconocido',
                'anio':    str(anio),
                'resumen': bib.get('abstract','')[:300],
                'doi':     doi,
                'url':     f"https://doi.org/{doi}" if doi else '',
                'revista': revista,
                'fuente':  'DOAJ',
                'idioma':  lang,
            })
        return results

    # ── arXiv ─────────────────────────────────────────────────────────────────
    def _arxiv(self, tema: str, n: int) -> list[dict]:
        url = "http://export.arxiv.org/api/query"
        params = {
            'search_query': f'all:{urllib.parse.quote(tema)}',
            'start': 0,
            'max_results': n
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
            anio    = ''
            pub = entry.find('atom:published', ns)
            if pub is not None and pub.text:
                anio = pub.text[:4]
            autores = ", ".join([
                (a.find('atom:name', ns) or ET.Element('')).text or ''
                for a in entry.findall('atom:author', ns)[:3]
            ])
            link = ''
            for lnk in entry.findall('atom:link', ns):
                if lnk.get('type') == 'text/html':
                    link = lnk.get('href','')
            arxiv_id = link.split('/')[-1] if link else ''
            results.append({
                'titulo':  titulo.replace('\n',' ').strip(),
                'autores': autores or 'Autor desconocido',
                'anio':    anio or 's.f.',
                'resumen': resumen[:300],
                'doi':     '',
                'url':     link,
                'revista': f'arXiv:{arxiv_id}',
                'fuente':  'arXiv',
                'idioma':  'en',
            })
        return results

    # ── SciELO ────────────────────────────────────────────────────────────────
    def _scielo(self, tema: str, n: int) -> list[dict]:
        # SciELO API via OpenAlex filter
        url = "https://api.openalex.org/works"
        params = {
            'search': tema,
            'filter': 'primary_location.source.host_organization:I4210139997',  # SciELO
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

    # ── monografias.com (scraping básico via requests) ─────────────────────────
    def _monografias_com(self, tema: str, n: int) -> list[dict]:
        query = urllib.parse.quote(tema)
        url   = f"https://www.monografias.com/buscar/docs/?q={query}"
        try:
            r = self.session.get(url, timeout=self.timeout)
            if r.status_code != 200:
                return []
            # Extraer títulos y URLs con regex simple
            titulos = re.findall(r'<a[^>]+href="(/trabajos[^"]+)"[^>]*>([^<]{10,})</a>', r.text)
            results = []
            for href, titulo in titulos[:n]:
                results.append({
                    'titulo':  titulo.strip(),
                    'autores': 'Autor desconocido',
                    'anio':    's.f.',
                    'resumen': f'Monografía disponible en monografias.com sobre {tema}',
                    'doi':     '',
                    'url':     f"https://www.monografias.com{href}",
                    'revista': 'monografias.com',
                    'fuente':  'monografias.com',
                    'idioma':  'es',
                })
            return results
        except Exception:
            return []

    # ── Open Library (libros PDF gratuitos) ───────────────────────────────────
    def _open_library(self, tema: str, n: int) -> list[dict]:
        url = "https://openlibrary.org/search.json"
        params = {'q': tema, 'limit': n, 'fields': 'title,author_name,first_publish_year,isbn,subject'}
        r = self.session.get(url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            return []
        items = r.json().get('docs', [])
        results = []
        for item in items:
            autores = ", ".join((item.get('author_name') or [])[:3])
            anio    = str(item.get('first_publish_year', 's.f.'))
            isbn    = (item.get('isbn') or [''])[0]
            url_ol  = f"https://openlibrary.org/search?q={urllib.parse.quote(item.get('title',''))}"
            results.append({
                'titulo':  item.get('title',''),
                'autores': autores or 'Autor desconocido',
                'anio':    anio,
                'resumen': f"Libro. Temas: {', '.join((item.get('subject') or [])[:3])}",
                'doi':     '',
                'url':     url_ol,
                'revista': '',
                'fuente':  'Open Library',
                'idioma':  'en',
            })
        return results


# ── Helpers ────────────────────────────────────────────────────────────────────
def _reconstruct_abstract(aii: dict) -> str:
    """Reconstruye el abstract desde el abstract_inverted_index de OpenAlex."""
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
    """Elimina etiquetas HTML simples."""
    return re.sub(r'<[^>]+>', '', text or '')
