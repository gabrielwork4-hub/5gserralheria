/**
 * Modo de manutencao — Cloudflare Pages Functions.
 *
 * Por que aqui e nao num index.html trocado: status code e decisao do servidor.
 * Uma pagina estatica de manutencao sai com 200 OK e o Google indexa ela como
 * se fosse o conteudo real do site. Este middleware roda na borda, antes do
 * arquivo estatico, e devolve 503 de verdade.
 *
 * Liga/desliga: variavel de ambiente MAINTENANCE_MODE no painel do Cloudflare
 * Pages (Settings > Environment variables). Valores aceitos como "ligado":
 * 1, true, on, yes, enabled. Ausente ou qualquer outro valor = site normal.
 *
 * ATENCAO: no Cloudflare Pages, alterar uma variavel de ambiente so passa a
 * valer no deploy seguinte. Depois de mudar o valor, use "Retry deployment"
 * no ultimo deployment para aplicar sem precisar de commit.
 *
 * Nenhum arquivo do site e apagado ou alterado: quando o modo esta desligado
 * o middleware apenas repassa a requisicao com next().
 */

const RETRY_AFTER_SECONDS = 86400; // 24h

// Nunca interceptados, mesmo em manutencao: os crawlers precisam continuar
// lendo estes arquivos para nao perder a referencia do site.
const ALWAYS_AVAILABLE = new Set([
  '/robots.txt',
  '/sitemap.xml',
  '/llms.txt',
  '/favicon.ico',
]);

const TRUTHY = new Set(['1', 'true', 'on', 'yes', 'enabled']);

function maintenanceEnabled(env) {
  const raw = env && env.MAINTENANCE_MODE;
  if (typeof raw !== 'string') return false;
  return TRUTHY.has(raw.trim().toLowerCase());
}

/**
 * Rota HTML = termina em "/", termina em .html/.htm, ou nao tem extensao
 * (o Pages resolve /servicos/escadas-de-ferro para o index.html da pasta).
 * Qualquer coisa com outra extensao (.css, .js, .webp, .woff2) e asset e
 * passa direto — a pagina de manutencao nao depende de nenhum deles.
 */
function isHtmlRoute(pathname) {
  if (pathname.endsWith('/')) return true;
  const segment = pathname.slice(pathname.lastIndexOf('/') + 1);
  if (segment === '') return true;
  if (!segment.includes('.')) return true;
  return /\.html?$/i.test(segment);
}

export async function onRequest(context) {
  const { request, next, env } = context;

  if (!maintenanceEnabled(env)) return next();

  const pathname = new URL(request.url).pathname;

  if (ALWAYS_AVAILABLE.has(pathname)) return next();
  if (!isHtmlRoute(pathname)) return next();

  return maintenanceResponse();
}

function maintenanceResponse() {
  return new Response(MAINTENANCE_PAGE, {
    status: 503,
    statusText: 'Service Unavailable',
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      // Diz ao Google: volte depois, isto e temporario. Sem isto o 503
      // repetido comeca a ser tratado como erro permanente.
      'Retry-After': String(RETRY_AFTER_SECONDS),
      // O 503 nao pode ser cacheado: quando o modo for desligado, a pagina
      // real precisa voltar na hora, sem purge de cache.
      'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
      // O arquivo _headers so vale para assets estaticos; respostas geradas
      // por Function nao passam por ele. Repetimos o essencial aqui para o
      // 503 nao ser uma superficie mais fraca que o resto do site.
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
      'Referrer-Policy': 'strict-origin-when-cross-origin',
    },
  });
}

// Autocontida: CSS inline, sem fonte externa, sem imagem, sem JS.
const MAINTENANCE_PAGE = `<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Site em manutencao</title>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    background: #f4f4f5;
    color: #18181b;
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
  }
  main {
    max-width: 34rem;
    width: 100%;
    background: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 12px;
    padding: 40px 32px;
    text-align: center;
  }
  h1 { margin: 0 0 12px; font-size: 1.5rem; line-height: 1.3; font-weight: 600; }
  p { margin: 0 0 12px; color: #52525b; }
  p:last-child { margin-bottom: 0; }
  .sub { font-size: 0.875rem; color: #71717a; }
  @media (prefers-color-scheme: dark) {
    body { background: #18181b; color: #fafafa; }
    main { background: #27272a; border-color: #3f3f46; }
    p { color: #a1a1aa; }
    .sub { color: #8b8b93; }
  }
</style>
</head>
<body>
  <main>
    <h1>Site em manutencao</h1>
    <p>Estamos realizando uma manutencao programada. O site volta a ficar disponivel em breve.</p>
    <p class="sub">Obrigado pela compreensao.</p>
  </main>
</body>
</html>
`;
