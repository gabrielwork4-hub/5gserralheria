/* ==========================================================================
   5G SERRALHERIA - BLOG JAVASCRIPT
   Controle de Filtros, Busca e Paginação do Blog
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('blogSearch');
  const searchForm = document.getElementById('searchForm');
  const categoryPills = document.querySelectorAll('.pill-btn');
  const postCards = document.querySelectorAll('.post-card');

  let activeCategory = 'Todos';

  // Filtro por Categoria
  categoryPills.forEach(pill => {
    pill.addEventListener('click', () => {
      categoryPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');

      activeCategory = pill.getAttribute('data-category');
      filterPosts();
    });
  });

  // Filtro por Busca em Tempo Real
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      filterPosts();
    });
  }

  if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      filterPosts();
    });
  }

  function filterPosts() {
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

    postCards.forEach(card => {
      const category = card.getAttribute('data-category');
      const title = card.querySelector('.post-card-title').textContent.toLowerCase();
      const excerpt = card.querySelector('.post-card-excerpt').textContent.toLowerCase();

      const matchesCategory = (activeCategory === 'Todos' || category === activeCategory);
      const matchesSearch = (!query || title.includes(query) || excerpt.includes(query));

      if (matchesCategory && matchesSearch) {
        card.style.display = 'flex';
      } else {
        card.style.display = 'none';
      }
    });
  }
});
