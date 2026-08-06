#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Liga/desliga o noindex do preview.

O site final vive no Cloudflare, em 5gserralheria.ayamdigital.com.br. Enquanto
isso o GitHub Pages serve uma copia em gabrielwork4-hub.github.io/5gserralheria/
para o cliente ver. Duas copias do mesmo conteudo no ar sem protecao e risco de
o Google indexar o dominio errado.

O canonical ja aponta para o dominio final em todas as paginas, mas canonical e
uma dica, nao uma ordem. E robots.txt nao resolve aqui: em subcaminho o crawler
le gabrielwork4-hub.github.io/robots.txt, que nao e o arquivo deste projeto.
Sobra o meta robots por pagina — que e justamente o que este script controla.

    python scripts/preview-noindex.py --on     # antes de publicar no GitHub Pages
    python scripts/preview-noindex.py --off    # antes do deploy no Cloudflare

O verify.py falha se sobrar qualquer noindex, entao o --off nunca e esquecido
em silencio.
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
IGNORAR = ("5gserralheria-audit/", "claude-seo/", "claude SEO/", "scripts/")

PRODUCAO = "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"
PREVIEW = "noindex, nofollow"


def paginas():
    return sorted(p for p in RAIZ.rglob("index.html")
                  if not p.relative_to(RAIZ).as_posix().startswith(IGNORAR))


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("--on", "--off"):
        print(__doc__)
        return 2

    ligar = sys.argv[1] == "--on"
    alvo = PREVIEW if ligar else PRODUCAO
    mudadas = 0

    for p in paginas():
        s = p.read_text(encoding="utf-8")
        achou = re.findall(r'<meta name="robots"[^>]*>', s, re.I)
        if len(achou) != 1:
            print(f"ERRO: {p} tem {len(achou)} metas robots (esperado 1)", file=sys.stderr)
            return 1
        novo = f'<meta name="robots" content="{alvo}">'
        if achou[0] == novo:
            continue
        p.write_text(s.replace(achou[0], novo, 1), encoding="utf-8")
        mudadas += 1

    estado = "NOINDEX (preview)" if ligar else "INDEXAVEL (producao)"
    print(f"{estado} — {mudadas} de {len(paginas())} paginas alteradas")
    if ligar:
        print("Lembre: rode --off antes do deploy no Cloudflare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
