"""
Validação do site antes do deploy.

    python scripts/verify.py

Sai com código 1 se houver qualquer erro. Checa estrutura, caminhos, metadados,
schema e consistência entre as páginas.
"""
import json, os, re, sys, io, glob
from urllib.parse import urljoin

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
DOM = "https://5gserralheria.ayamdigital.com.br"
SKIP = ("5gserralheria-audit", "claude-seo", "claude SEO", "scripts")
erros, avisos = [], []


def pages():
    f = glob.glob("index.html") + glob.glob("*/index.html") + glob.glob("*/*/index.html")
    return sorted(p for p in f if not p.replace(os.sep, "/").startswith(SKIP))


def url_of(p):
    return "/" + p.replace(os.sep, "/").replace("index.html", "")


P = pages()
print("PÁGINAS: %d\n" % len(P))

for p in P:
    s = open(p, encoding="utf-8").read()
    u = url_of(p)
    e = lambda m: erros.append("%s — %s" % (u, m))

    # ---- estrutura
    if len(re.findall(r"<div\b", s)) != len(re.findall(r"</div>", s)):
        e("div desbalanceado")
    if len(re.findall(r"<h1\b", s)) != 1:
        e("h1 = %d (esperado 1)" % len(re.findall(r"<h1\b", s)))
    for t in ("html", "head", "body", "header", "footer", "main"):
        if not re.search(r"<%s\b" % t, s):
            e("falta <%s>" % t)

    # ---- caminhos internos precisam ser RELATIVOS e resolver
    for attr, v in re.findall(r'\b(href|src)="([^"]+)"', s):
        if v.startswith(("http", "mailto:", "tel:", "data:", "//", "#")):
            continue
        if v.startswith("/"):
            e("caminho root-absoluto (quebra em subcaminho): %s" % v)
            continue
        alvo = os.path.normpath(os.path.join(os.path.dirname(p), v.split("#")[0]))
        if not v.split("#")[0]:
            continue
        ok = os.path.isfile(alvo) or os.path.isfile(os.path.join(alvo, "index.html"))
        if not ok:
            e("caminho quebrado: %s" % v)

    # ---- canonical / og precisam ser ABSOLUTOS e bater com o arquivo
    can = re.search(r'rel="canonical"[^>]*href="([^"]+)"', s)
    if not can:
        e("sem canonical")
    elif can.group(1) != DOM + u:
        e("canonical %s (esperado %s)" % (can.group(1), DOM + u))
    og = re.search(r'property="og:url"[^>]*content="([^"]+)"', s)
    if og and og.group(1) != DOM + u:
        e("og:url %s (esperado %s)" % (og.group(1), DOM + u))
    for tag in ("og:title", "og:description", "og:image"):
        if 'property="%s"' % tag not in s:
            e("falta %s" % tag)

    # ---- title / description
    t = re.search(r"<title>(.*?)</title>", s, re.S)
    if not t:
        e("sem <title>")
    elif not 40 <= len(t.group(1)) <= 75:
        avisos.append("%s — title com %d caracteres" % (u, len(t.group(1))))
    d = re.search(r'name="description"[^>]*content="([^"]*)"', s)
    if not d:
        e("sem meta description")
    elif not 120 <= len(d.group(1)) <= 170:
        avisos.append("%s — description com %d caracteres" % (u, len(d.group(1))))

    # ---- schema
    for sc in re.findall(r'application/ld\+json[^>]*>(.*?)</script>', s, re.S):
        try:
            json.loads(sc)
        except Exception as ex:
            e("JSON-LD inválido: %s" % str(ex)[:60])
    if u != "/" and "BreadcrumbList" not in s:
        e("sem BreadcrumbList")

    # ---- casca comum
    if 'id="mobileMenu"' not in s:
        e("sem menu mobile")
    if "nav-dropdown" not in s:
        e("sem dropdown de serviços")
    if "M'Boi Mirim" not in s:
        e("rodapé sem NAP")
    # A fonte passou a ser auto-hospedada (assets/fonts/inter-latin.woff2).
    # Cada página precisa do preload; o @font-face vive no main.css.
    if "assets/fonts/inter-latin.woff2" not in s:
        e("sem preload da fonte Inter auto-hospedada")
    if "fonts.googleapis" in s or "fonts.gstatic" in s:
        e("voltou a carregar a fonte do Google Fonts (deve ser auto-hospedada)")
    if "AW-17926586201" not in s:
        e("sem a tag do Google Ads")

    # ---- imagens
    for img in re.findall(r"<img\b[^>]*>", s):
        if not re.search(r'alt="[^"]+', img):
            e("img sem alt: %s" % img[:60])
        if not (re.search(r"width=", img) and re.search(r"height=", img)):
            e("img sem width/height: %s" % img[:60])

    # ---- markdown vazado
    corpo = re.sub(r"<(script|style|head)[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
    for m in re.findall(r"\*\*[^*]{2,60}\*\*", corpo):
        e("markdown vazado: %s" % m[:40])

# ---- sitemap
sm = open("sitemap.xml", encoding="utf-8").read()
locs = {l.replace(DOM, "") for l in re.findall(r"<loc>(.*?)</loc>", sm)}
arqs = {url_of(p) for p in P}
for x in sorted(arqs - locs):
    erros.append("sitemap — falta %s" % x)
for x in sorted(locs - arqs):
    erros.append("sitemap — %s não tem arquivo" % x)

# ---- resultado
print("=" * 64)
if avisos:
    print("AVISOS (%d):" % len(avisos))
    for a in avisos:
        print("  · %s" % a)
    print()
if erros:
    print("ERROS (%d):" % len(erros))
    for x in erros:
        print("  ✗ %s" % x)
    sys.exit(1)
print("TUDO OK — %d páginas validadas, 0 erros." % len(P))
