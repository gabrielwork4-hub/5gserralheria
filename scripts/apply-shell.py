"""
Aplica o header, o menu mobile e o rodapé canônicos em todas as páginas do site.

Este script é a ÚNICA fonte de verdade desses três componentes. Editar o markup
direto no HTML é errado — a próxima execução sobrescreve. Alterou o menu ou o
rodapé? Altere aqui e rode:

    python scripts/apply-shell.py

Foi criado porque os 17 arquivos originais tinham 3 variações de menu e 2 de
rodapé, e 10 de 11 páginas não tinham menu mobile nenhum.
"""
import re, os, sys, io, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

WA = ("https://wa.me/5511966408235?text=Ol%C3%A1!%20Gostaria%20de%20"
      "solicitar%20um%20or%C3%A7amento.")
TEL = "+5511966408235"
TEL_FMT = "(11) 96640-8235"

SERVICES = [
    ("escadas-de-ferro",        "Escadas de Ferro"),
    ("corrimao-e-guarda-corpo", "Corrimãos e Guarda-Corpos"),
    ("portoes-de-ferro",        "Portões Manuais e Automáticos"),
    ("mezaninos-metalicos",     "Mezaninos Metálicos"),
    ("coberturas-metalicas",    "Coberturas Metálicas"),
    ("grades-e-manutencao",     "Grades, Solda e Manutenção"),
]

SKIP = ("5gserralheria-audit", "claude-seo", "claude SEO", "scripts")


def pages():
    found = glob.glob("index.html") + glob.glob("*/index.html") + glob.glob("*/*/index.html")
    return sorted(p for p in found if not p.replace(os.sep, "/").startswith(SKIP))


def url_of(page):
    return "/" + page.replace(os.sep, "/").replace("index.html", "")


def prefixo(page):
    """'../' por nível de profundidade. Os caminhos precisam ser RELATIVOS: o
    site roda tanto na raiz de um domínio (Cloudflare Pages) quanto em
    subcaminho (GitHub Pages, /5gserralheria/), e '/assets/...' quebraria no
    segundo caso."""
    return "../" * page.replace(os.sep, "/").count("/")


def link(page, destino):
    """Converte um caminho absoluto do site ('/servicos/') em relativo à página."""
    p = prefixo(page)
    if destino == "/":
        return p if p else "./"
    if destino.startswith("/#"):
        return p + destino[1:]
    return p + destino.lstrip("/")


def header_html(page):
    u = url_of(page)
    serv_active = " active" if u.startswith("/servicos/") else ""
    blog_active = " active" if u.startswith("/blog/") else ""
    cont_active = " active" if u == "/contato/" else ""

    L = lambda d: link(page, d)
    items = []
    for slug, label in SERVICES:
        cls = ' class="active"' if u == "/servicos/%s/" % slug else ""
        items.append('            <a href="%s"%s>%s</a>'
                     % (L("/servicos/%s/" % slug), cls, label))
    drop = "\n".join(items)

    return """<header class="header">
    <div class="container header-container">
      <a href="{home}" class="logo" aria-label="Página inicial da 5G Serralheria">
        <img src="{logo}" alt="Logo Oficial 5G Serralheria" class="logo-img" width="52" height="52">
      </a>

      <nav class="nav-links" aria-label="Menu principal">
        <div class="nav-item-dropdown">
          <a href="{serv}" class="nav-link{sa}">Serviços<span class="nav-caret" aria-hidden="true"></span></a>
          <div class="nav-dropdown">
{drop}
            <a href="{serv}" class="nav-dropdown-all">Ver todos os serviços</a>
          </div>
        </div>
        <a href="{portf}" class="nav-link">Portfólio</a>
        <a href="{blog}" class="nav-link{ba}">Blog</a>
        <a href="{cont}" class="nav-link{ca}">Contato</a>
      </nav>

      <div class="header-cta">
        <a href="tel:{tel}" class="phone-link">{telf}</a>
        <a href="{wa}" class="btn btn-accent" target="_blank" rel="noopener">Falar no WhatsApp</a>
      </div>

      <button class="hamburger" id="hamburgerBtn" aria-label="Abrir menu de navegação" aria-expanded="false">
        <span></span>
        <span></span>
        <span></span>
      </button>
    </div>
  </header>""".format(sa=serv_active, ba=blog_active, ca=cont_active, drop=drop,
                      tel=TEL, telf=TEL_FMT, wa=WA,
                      home=L("/"), logo=L("/assets/img/logo-5g-serralheria.webp"),
                      serv=L("/servicos/"), portf=L("/#portfolio"),
                      blog=L("/blog/"), cont=L("/contato/"))


def mobile_html(page):
    u = url_of(page)
    L = lambda d: link(page, d)
    subs = []
    for slug, label in SERVICES:
        a = " active" if u == "/servicos/%s/" % slug else ""
        subs.append('    <a href="%s" class="nav-link sub%s">%s</a>'
                    % (L("/servicos/%s/" % slug), a, label))
    blog_active = " active" if u.startswith("/blog/") else ""
    cont_active = " active" if u == "/contato/" else ""

    return """<div class="mobile-menu" id="mobileMenu">
    <span class="mobile-menu-label">Serviços</span>
    <a href="{serv}" class="nav-link">Ver todos os serviços</a>
{subs}
    <span class="mobile-menu-label">Navegação</span>
    <a href="{portf}" class="nav-link">Portfólio</a>
    <a href="{blog}" class="nav-link{ba}">Blog</a>
    <a href="{cont}" class="nav-link{ca}">Contato</a>
    <a href="{wa}" class="btn btn-whatsapp" target="_blank" rel="noopener">Falar no WhatsApp</a>
    <a href="tel:{tel}" class="mobile-phone">{telf}</a>
  </div>""".format(subs="\n".join(subs), ba=blog_active, ca=cont_active,
                   wa=WA, tel=TEL, telf=TEL_FMT, serv=L("/servicos/"),
                   portf=L("/#portfolio"), blog=L("/blog/"), cont=L("/contato/"))


def footer_html(page):
    L = lambda d: link(page, d)
    links = "\n".join(
        '            <li><a href="%s">%s</a></li>' % (L("/servicos/%s/" % s), l)
        for s, l in SERVICES)
    return """<footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-col">
          <a href="{home}" class="logo" style="margin-bottom: 14px;">
            <img src="{logo}" alt="Logo Oficial 5G Serralheria" class="logo-img" width="52" height="52">
          </a>
          <p style="color: var(--text-muted); font-size: 0.88rem;">Mais de 10 anos de tradição e excelência em escadas de ferro e estruturas metálicas em São Paulo.</p>
        </div>

        <div class="footer-col">
          <h4>Serviços</h4>
          <ul>
{links}
          </ul>
        </div>

        <div class="footer-col">
          <h4>Empresa</h4>
          <ul>
            <li><a href="{difer}">Diferenciais</a></li>
            <li><a href="{portf}">Portfólio</a></li>
            <li><a href="{blog}">Blog</a></li>
            <li><a href="{cont}">Contato</a></li>
            <li><a href="{faq}">Perguntas Frequentes</a></li>
          </ul>
        </div>

        <div class="footer-col">
          <h4>Contato</h4>
          <ul>
            <li><a href="{wa}" target="_blank" rel="noopener">WhatsApp: {telf}</a></li>
            <li><a href="tel:{tel}">Telefone: {telf}</a></li>
            <li><a href="mailto:spg.vendas@hotmail.com">spg.vendas@hotmail.com</a></li>
            <li><span style="color: var(--text-muted);">Estrada M'Boi Mirim, 3355 — São Paulo/SP</span></li>
            <li><span style="color: var(--text-muted);">Seg a Sex, 08h às 18h</span></li>
          </ul>
        </div>
      </div>

      <div class="footer-bottom">
        <span>© 2026 5G Serralheria. Todos os direitos reservados.</span>
        <span>São Paulo - SP · Orçamento Gratuito</span>
      </div>
    </div>
  </footer>""".format(links=links, wa=WA, tel=TEL, telf=TEL_FMT,
                      home=L("/"), logo=L("/assets/img/logo-5g-serralheria.webp"),
                      difer=L("/#diferenciais"), portf=L("/#portfolio"),
                      blog=L("/blog/"), cont=L("/contato/"), faq=L("/#faq"))


def integridade(s):
    """Métricas estruturais usadas para comparar antes/depois da reescrita."""
    return {
        "div": (len(re.findall(r"<div\b", s)), len(re.findall(r"</div>", s))),
        "main": len(re.findall(r"<main\b", s)),
        "h1": len(re.findall(r"<h1\b", s)),
        "section": len(re.findall(r"<section\b", s)),
        "h2": len(re.findall(r"<h2\b", s)),
    }


def apply(page):
    s = open(page, encoding="utf-8").read()
    orig = s
    antes = integridade(orig)

    # Remove qualquer menu mobile existente (será reinserido após o header).
    # (?:(?!</?div\b).)* proíbe qualquer <div>/</div> dentro do trecho, garantindo
    # que o casamento pare no </div> do PRÓPRIO menu. A versão anterior usava
    # `.*?</div>` com lookahead e engoliu o hero inteiro da home.
    s = re.sub(r'\s*<div class="mobile-menu"[^>]*>(?:(?!</?div\b).)*</div>',
               "\n  ", s, flags=re.S)

    if not re.search(r"<header[^>]*>.*?</header>", s, re.S):
        return "SEM HEADER"
    s = re.sub(r"<header[^>]*>.*?</header>",
               lambda m: header_html(page) + "\n  " + mobile_html(page), s, count=1, flags=re.S)

    if not re.search(r"<footer[^>]*>.*?</footer>", s, re.S):
        return "SEM FOOTER"
    s = re.sub(r"<footer[^>]*>.*?</footer>", lambda m: footer_html(page), s, count=1, flags=re.S)

    # ---- trava de integridade -------------------------------------------
    # Uma regex de substituição mal ancorada já apagou o hero inteiro da home
    # sem erro nenhum. Nada é gravado se o conteúdo fora do header/rodapé
    # tiver mudado: <div> tem que fechar, e main/h1/section/h2 são preservados.
    depois = integridade(s)
    problemas = []
    if depois["div"][0] != depois["div"][1]:
        problemas.append("div desbalanceado (%d abre, %d fecha)" % depois["div"])
    for chave in ("main", "h1", "section", "h2"):
        if antes[chave] != depois[chave]:
            problemas.append("%s: %d -> %d" % (chave, antes[chave], depois[chave]))
    if problemas:
        return "ABORTADO — " + "; ".join(problemas)

    if s != orig:
        open(page, "w", encoding="utf-8", newline="").write(s)
        return "atualizado"
    return "sem mudança"


if __name__ == "__main__":
    falhas = 0
    for p in pages():
        r = apply(p)
        if r.startswith(("ABORTADO", "SEM ")):
            falhas += 1
        print("  %-56s %s" % (url_of(p), r))
    if falhas:
        print("\n%d página(s) NÃO foram gravadas — corrija antes de seguir." % falhas)
        sys.exit(1)
    print("\nOK — %d páginas com header, menu mobile e rodapé canônicos." % len(pages()))
