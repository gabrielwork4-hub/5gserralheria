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

  // 3. Rastreamento de Conversão de Cliques no WhatsApp (Google Ads / Analytics)
  const whatsappLinks = document.querySelectorAll('a[href*="wa.me"], a[href*="whatsapp"]');
  whatsappLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      if (typeof window.gtag === 'function') {
        window.gtag('event', 'conversion', {
          'send_to': 'AW-17926586201',
          'event_category': 'Engagement',
          'event_label': 'WhatsApp Click',
          'value': 1.0
        });
      }
    });
  });
});
