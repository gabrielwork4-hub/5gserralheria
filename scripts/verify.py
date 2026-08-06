"""
Validação do site antes do deploy.

    python scripts/verify.py

Sai com código 1 se houver qualquer erro. Checa estrutura, caminhos, metadados,
schema e consistência entre as páginas.
"""
import json, os, re, sys, io, glob, html, hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
DOM = "https://5gserralheria.ayamdigital.com.br"
SKIP = ("5gserralheria-audit", "claude-seo", "claude SEO", "scripts")

# Tag do GA4. Enquanto for None o script so avisa; preenchido, passa a exigir
# a tag nas 13 paginas. Ver item 5.3 do ENTREGA-V1.md.
GA4 = None

erros, avisos = [], []
cascas = {}  # hash do header/footer por pagina, para detectar deriva de template


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

    # ---- indexacao: o noindex do preview NAO pode chegar em producao.
    # Toda pagina ja tem um <meta name="robots">, entao checar so o primeiro
    # deixaria passar um segundo meta injetado depois.
    robs = re.findall(r'name="robots"[^>]*content="([^"]*)"', s, re.I)
    if len(robs) > 1:
        e("%d metas robots (deve haver 1): %s" % (len(robs), robs))
    for r in robs:
        if "noindex" in r.lower():
            e("meta robots noindex — rode scripts/preview-noindex.py --off antes do deploy")

    # ---- casca comum
    if 'id="mobileMenu"' not in s:
        e("sem menu mobile")
    if "nav-dropdown" not in s:
        e("sem dropdown de serviços")
    if "M'Boi Mirim" not in s:
        e("rodapé sem NAP")
    if "fonts.googleapis" not in s:
        e("sem a fonte Inter")
    if "rel=\"preconnect\"" not in s:
        e("sem preconnect das fontes")
    if "AW-17926586201" not in s:
        e("sem a tag do Google Ads")
    if GA4 and GA4 not in s:
        e("sem a tag do GA4 (%s)" % GA4)

    # ---- casca identica entre paginas (header e footer vem do apply-shell.py).
    # Duas diferencas sao legitimas e precisam ser neutralizadas antes do hash:
    # os caminhos relativos mudam com a profundidade da pagina, e a classe
    # "active" marca o item de menu da pagina atual. O resto tem que ser igual.
    base = os.path.dirname(p)
    for tag in ("header", "footer"):
        m = re.search(r"<%s\b.*?</%s>" % (tag, tag), s, re.S)
        if not m:
            continue

        def resolve(mo):
            attr, v = mo.group(1), mo.group(2)
            if v.startswith(("http", "mailto:", "tel:", "data:", "//")):
                return mo.group(0)
            # Ancora pura ("#faq") aponta para a propria pagina; nas outras
            # paginas o mesmo item de menu vira "../#faq". Resolver os dois
            # contra a base faz as duas formas convergirem.
            alvo = os.path.normpath(os.path.join(base, v)).replace(os.sep, "/")
            return '%s="/%s"' % (attr, "" if alvo == "." else alvo)

        norm = re.sub(r'\b(href|src)="([^"]+)"', resolve, m.group(0))
        norm = re.sub(r'\s*\bactive\b', "", norm)
        norm = re.sub(r'\s*class=""', "", norm)  # residuo de tirar o "active"
        cascas.setdefault(tag, {}).setdefault(
            hashlib.md5(norm.encode()).hexdigest(), []).append(u)

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
    for m in re.findall(r"(?<![\w*])\*[^*\s][^*]{1,60}\*(?![\w*])", corpo):
        e("markdown vazado (itálico): %s" % m[:40])
    for m in re.findall(r"^#{1,6} \S", corpo, re.M):
        e("markdown vazado (heading): %s" % m[:40])

    # ---- FAQPage: o Google exige que pergunta e resposta do schema estejam
    # visiveis na pagina. Divergir e motivo de perder o rich result.
    if '"FAQPage"' in s:
        faq = next((json.loads(b) for b in
                    re.findall(r'application/ld\+json[^>]*>(.*?)</script>', s, re.S)
                    if '"FAQPage"' in b), None)
        sch = [(q["name"], q["acceptedAnswer"]["text"]) for q in faq["mainEntity"]]

        # O site tem dois markups de FAQ: acordeao (home) e h3+p (hubs).
        vq = re.findall(r'<button class="faq-btn">\s*<span>(.*?)</span>', s, re.S)
        va = re.findall(r'<div class="faq-content">\s*<p>(.*?)</p>', s, re.S)
        if not vq:
            pares = re.findall(r"<h3>(.*?)</h3>\s*<p>(.*?)</p>", s, re.S)
            perg = {q.strip() for q, _ in sch}
            vq = [q for q, _ in pares if html.unescape(q).strip() in perg]
            va = [a for q, a in pares if html.unescape(q).strip() in perg]

        limpa = lambda x: html.unescape(re.sub(r"<[^>]+>", "", x)).strip()
        vis = [(limpa(q), limpa(a)) for q, a in zip(vq, va)]
        if len(sch) != len(vis):
            e("FAQPage: %d no schema, %d visíveis" % (len(sch), len(vis)))
        for i, (a, b) in enumerate(zip(sch, vis), 1):
            if a[0] != b[0]:
                e("FAQPage #%d: pergunta do schema difere da visível" % i)
            elif a[1] != b[1]:
                e("FAQPage #%d: resposta do schema difere da visível" % i)

# ---- deriva de casca: todo header (e todo footer) tem que ter o mesmo hash
for tag, grupos in cascas.items():
    if len(grupos) > 1:
        maior = max(grupos.values(), key=len)
        for h, urls in grupos.items():
            if urls is not maior:
                erros.append("<%s> difere do resto em: %s  (rode scripts/apply-shell.py)"
                             % (tag, ", ".join(urls)))

# ---- sitemap
sm = open("sitemap.xml", encoding="utf-8").read()
locs = {l.replace(DOM, "") for l in re.findall(r"<loc>(.*?)</loc>", sm)}
arqs = {url_of(p) for p in P}
for x in sorted(arqs - locs):
    erros.append("sitemap — falta %s" % x)
for x in sorted(locs - arqs):
    erros.append("sitemap — %s não tem arquivo" % x)
if not GA4:
    avisos.append("GA4 ainda não instalado — preencher GA4 neste script e rodar apply-shell (item 5.3)")

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
