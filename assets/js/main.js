/* ==========================================================================
   5G SERRALHERIA - MAIN JAVASCRIPT
   Vanilla JS - Leve, Rápido e Focado em Conversão
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const hamburgerBtn = document.getElementById('hamburgerBtn');
  const mobileMenu = document.getElementById('mobileMenu');

  if (hamburgerBtn && mobileMenu) {
    hamburgerBtn.addEventListener('click', () => {
      mobileMenu.classList.toggle('open');
      const isOpen = mobileMenu.classList.contains('open');
      hamburgerBtn.setAttribute('aria-expanded', isOpen);
    });

    // Fechar menu ao clicar em links
    mobileMenu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        mobileMenu.classList.remove('open');
        hamburgerBtn.setAttribute('aria-expanded', false);
      });
    });
  }

  // 2. FAQ Accordion
  const faqButtons = document.querySelectorAll('.faq-btn');
  faqButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const faqItem = btn.parentElement;
      const content = btn.nextElementSibling;
      const isOpen = faqItem.classList.contains('active');

      // Fechar outros itens
      document.querySelectorAll('.faq-item').forEach(item => {
        item.classList.remove('active');
        const c = item.querySelector('.faq-content');
        if (c) c.style.maxHeight = null;
      });

      if (!isOpen) {
        faqItem.classList.add('active');
        content.style.maxHeight = content.scrollHeight + 'px';
      }
    });
  });

  // 3. Rastreamento de Conversão (Google Ads + GA4)
  //
  // CONFIGURAÇÃO PENDENTE — dois valores precisam ser preenchidos:
  //
  //   GA4_ID       ID de medição da propriedade GA4 (formato 'G-XXXXXXXXXX').
  //                Hoje o site só carrega a tag do Google Ads, então nenhuma
  //                sessão, origem de tráfego ou página é registrada em lugar
  //                nenhum. Sem isso não há como medir o resultado do SEO/GEO.
  //
  //   ADS_LABEL    Rótulo da ação de conversão no Google Ads. O código antigo
  //                enviava send_to: 'AW-17926586201' sem rótulo — o Google Ads
  //                exige o formato 'AW-ID/RÓTULO' e descarta o evento sem ele,
  //                então os cliques de WhatsApp nunca chegaram a contar como
  //                conversão. Pegar em: Google Ads > Objetivos > Conversões >
  //                a ação desejada > Configurar tag > "rótulo da conversão".
  //
  const GA4_ID = '';      // ex: 'G-XXXXXXXXXX'
  const ADS_ID = 'AW-17926586201';
  const ADS_LABEL = '';   // ex: 'AbC-D_efGhIjKlM'

  const gtagReady = () => typeof window.gtag === 'function';

  if (GA4_ID && gtagReady()) {
    window.gtag('config', GA4_ID);
  }

  // De onde na página partiu o clique — separa o botão flutuante do CTA final,
  // do header etc., para saber qual ponto de contato realmente converte.
  const origemDoClique = (el) => {
    if (el.closest('.floating-whatsapp')) return 'flutuante';
    if (el.closest('.mobile-menu')) return 'menu-mobile';
    if (el.closest('.header')) return 'header';
    if (el.closest('.hero')) return 'hero';
    if (el.closest('.cta-banner')) return 'cta-final';
    if (el.closest('.footer')) return 'rodape';
    return 'conteudo';
  };

  // Delegação no document: pega também os links do menu mobile e qualquer
  // link de contato que venha a ser adicionado depois.
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href]');
    if (!link || !gtagReady()) return;

    const href = link.getAttribute('href') || '';
    let canal;
    if (href.includes('wa.me') || href.includes('whatsapp')) canal = 'whatsapp';
    else if (href.startsWith('tel:')) canal = 'telefone';
    else if (href.startsWith('mailto:')) canal = 'email';
    else return;

    const origem = origemDoClique(link);

    // GA4: evento padrão de geração de lead.
    window.gtag('event', 'generate_lead', {
      canal: canal,
      origem: origem,
      pagina: window.location.pathname
    });

    // Google Ads: só dispara com o rótulo configurado, senão o evento é
    // descartado silenciosamente pelo Ads e vira ruído.
    if (ADS_LABEL) {
      window.gtag('event', 'conversion', {
        send_to: ADS_ID + '/' + ADS_LABEL,
        event_category: 'Contato',
        event_label: canal + ' - ' + origem,
        value: 1.0
      });
    }
  });
});
