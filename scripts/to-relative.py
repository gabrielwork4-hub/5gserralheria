"""
Converte os caminhos internos root-absolutos (/assets/...) em relativos (../assets/...).

Necessário porque o GitHub Pages serve o projeto em subcaminho
(gabrielwork4-hub.github.io/5gserralheria/), onde "/assets/..." resolveria para a
raiz do domínio e daria 404. Caminho relativo funciona nos três cenários:
raiz de domínio, subcaminho e file://.

NÃO toca em URLs absolutas https://5gserralheria.ayamdigital.com.br/... — essas
são canonical, og:url e schema, e devem continuar apontando para o domínio final.

    python scripts/to-relative.py
"""
import re, os, sys, io, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SKIP = ("5gserralheria-audit", "claude-seo", "claude SEO", "scripts")


def pages():
    found = glob.glob("index.html") + glob.glob("*/index.html") + glob.glob("*/*/index.html")
    return sorted(p for p in found if not p.replace(os.sep, "/").startswith(SKIP))


def converter(page):
    """Reescreve href/src que começam com / usando o prefixo do nível da página."""
    profundidade = page.replace(os.sep, "/").count("/")   # index.html=0, a/index.html=1
    prefixo = "../" * profundidade

    def troca(m):
        attr, valor = m.group(1), m.group(2)
        if valor == "/":                       # home
            destino = prefixo if prefixo else "./"
        elif valor.startswith("/#"):           # âncora da home
            destino = prefixo + valor[1:]
        else:
            destino = prefixo + valor.lstrip("/")
        return '%s="%s"' % (attr, destino)

    s = open(page, encoding="utf-8").read()
    novo = re.sub(r'\b(href|src)="(/(?!/)[^"]*)"', troca, s)
    if novo != s:
        open(page, "w", encoding="utf-8", newline="").write(novo)
        return len(re.findall(r'\b(?:href|src)="/(?!/)[^"]*"', s))
    return 0


if __name__ == "__main__":
    total = 0
    for p in pages():
        n = converter(p)
        total += n
        print("  %-56s %d caminho(s)" % ("/" + p.replace(os.sep, "/").replace("index.html", ""), n))
    print("\n%d caminhos convertidos para relativo." % total)
    print("Rode scripts/verify.py para conferir.")
