"""
Sobe o site localmente e abre no navegador.

    python scripts/preview.py            (porta 8000)
    python scripts/preview.py 8080       (porta escolhida)

Por que isto é necessário: o site usa caminhos root-absolutos (/assets/...),
que só resolvem quando servido a partir da raiz de um servidor. Abrir o .html
com duplo clique carrega via file:// e o CSS não é encontrado — a página
aparece sem layout. Não é bug: é como o site vai rodar no Cloudflare Pages.

Ctrl+C encerra.
"""
import http.server
import os
import socketserver
import sys
import threading
import webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTA = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

# Pastas de trabalho que não vão para o deploy — escondidas também aqui,
# para o preview refletir o que o cliente enxerga.
OCULTAS = ("/5gserralheria-audit", "/claude-seo", "/claude SEO", "/scripts")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        if any(self.path.startswith(p) for p in OCULTAS):
            self.send_error(404, "Nao faz parte do site")
            return
        super().do_GET()

    def end_headers(self):
        # sem cache: editou o CSS, F5 já mostra
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):
        code = str(args[1]) if len(args) > 1 else ""
        if code.startswith(("4", "5")):
            sys.stderr.write("  %s %s\n" % (code, args[0]))


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORTA), Handler) as srv:
        url = "http://127.0.0.1:%d/" % PORTA
        print("5G Serralheria rodando em %s" % url)
        print("Servindo: %s" % ROOT)
        print("Ctrl+C para encerrar.\n")
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nEncerrado.")
