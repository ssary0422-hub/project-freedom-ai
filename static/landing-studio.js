(() => {
  const toggle = document.querySelector('[data-nav-toggle]');
  const menu = document.querySelector('[data-nav-menu]');
  const setMenu = open => {
    if (!toggle || !menu) return;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.querySelector('.sr-only').textContent = open ? '메뉴 닫기' : '메뉴 열기';
    menu.classList.toggle('is-open', open);
  };
  if (toggle && menu) {
    toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
    menu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setMenu(false)));
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') { setMenu(false); toggle.focus(); }
    });
    document.addEventListener('click', event => { if (!menu.contains(event.target) && !toggle.contains(event.target)) setMenu(false); });
    matchMedia('(max-width: 700px)').addEventListener('change', () => setMenu(false));
  }
  const nav = document.querySelector('[data-studio-nav]');
  const updateNav = () => nav?.classList.toggle('is-scrolled', scrollY > 16);
  updateNav(); addEventListener('scroll', updateNav, {passive: true});
  const buttons = [...document.querySelectorAll('[data-filter]')];
  const cards = [...document.querySelectorAll('[data-category]')];
  const count = document.querySelector('[data-work-count]');
  buttons.forEach(button => button.addEventListener('click', () => {
    buttons.forEach(item => { const active = item === button; item.classList.toggle('is-active', active); item.setAttribute('aria-pressed', String(active)); });
    cards.forEach(card => { card.hidden = button.dataset.filter !== 'all' && card.dataset.category !== button.dataset.filter; });
    if (count) count.textContent = `${cards.filter(card => !card.hidden).length}개의 작업`;
  }));
})();
