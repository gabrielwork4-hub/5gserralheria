#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera sitemap.xml a partir dos arquivos que existem no site.

lastmod vem da data do ultimo commit que tocou o arquivo. Se o arquivo tem
alteracao nao commitada, usa a data de hoje - o commit ainda vai acontecer.
Assim o lastmod e sempre real, sem ninguem lembrar de atualizar a mao.

Uso:  python scripts/build-sitemap.py
"""

import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOMINIO = "https://5gserralheria.ayamdigital.com.br"

# priority/changefreq por secao. A ordem define a ordem no sitemap.
PRIORIDADE = [
    ("",                 "1.0", "monthly"),   # home
    ("servicos/",        "0.9", "monthly"),   # indice + os 6 hubs
    ("contato/",         "0.8", "yearly"),
    ("blog/",            "0.7", "weekly"),
]


def paginas():
    """Todo index.html do site, menos as pastas de trabalho do .gitignore."""
    encontradas = []
    for arq in RAIZ.rglob("index.html"):
        rel = arq.relative_to(RAIZ).as_posix()
        if rel.startswith(("5gserralheria-audit/", "claude-seo/", "claude SEO/")):
            continue
        encontradas.append(rel[: -len("index.html")])  # "servicos/x/index.html" -> "servicos/x/"
    return encontradas


def git(*args):
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def lastmod(url_path):
    arq = url_path + "index.html"
    if git("status", "--porcelain", "--", arq):
        return date.today().isoformat()          # mexido e ainda nao commitado
    d = git("log", "-1", "--format=%cs", "--", arq)
    return d or date.today().isoformat()         # sem historico = arquivo novo


def secao(url_path):
    """Indice da secao mais especifica que casa. O prefixo "" da home casa com
    tudo, entao a busca vai do mais especifico para o mais generico."""
    for i in range(len(PRIORIDADE) - 1, -1, -1):
        if url_path.startswith(PRIORIDADE[i][0]):
            return i
    return len(PRIORIDADE)


def classifica(url_path):
    i = secao(url_path)
    return PRIORIDADE[i][1:] if i < len(PRIORIDADE) else ("0.5", "monthly")


def ordena(url_path):
    return (secao(url_path), url_path.count("/"), url_path)


def main():
    urls = sorted(paginas(), key=ordena)
    if not urls:
        print("ERRO: nenhum index.html encontrado.", file=sys.stderr)
        return 1

    linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        pri, freq = classifica(u)
        linhas += ["  <url>",
                   f"    <loc>{DOMINIO}/{u}</loc>",
                   f"    <lastmod>{lastmod(u)}</lastmod>",
                   f"    <changefreq>{freq}</changefreq>",
                   f"    <priority>{pri}</priority>",
                   "  </url>"]
    linhas.append("</urlset>")

    destino = RAIZ / "sitemap.xml"
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"sitemap.xml gerado - {len(urls)} URLs")
    for u in urls:
        print(f"  {lastmod(u)}  /{u}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
