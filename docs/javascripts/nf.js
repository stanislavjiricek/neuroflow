// The documentation index: the search field filters the index as you type and lists matches from
// the text of every page (MkDocs' search index). "/" focuses the field, Esc clears it, Enter opens
// the first match. Each section of the index shows how many pages it holds, and the phases carry a
// short note on what each one is for. On narrow screens the index is a drawer: its menu control
// works from the keyboard (Enter or Space), "/" opens the drawer, and Esc closes it.
(() => {
  const PHASE_NOTES = {
    ideation: 'question & literature',
    preregistration: 'hypotheses & plan',
    'grant-proposal': 'funding',
    finance: 'budget',
    experiment: 'paradigm design',
    'tool-build': 'build tools',
    'tool-validate': 'validate tools',
    data: 'acquisition & BIDS',
    'data-preprocess': 'preprocessing',
    'data-analyze': 'analysis',
    'brain-build': 'model building',
    'brain-optimize': 'model fitting',
    'brain-run': 'simulations',
    paper: 'manuscript',
    review: 'peer review',
    poster: 'poster',
    'write-report': 'reports',
    output: 'export & archive',
    notes: 'any time',
  };
  const MAX_RESULTS = 8;

  const ENTITIES = { amp: '&', lt: '<', gt: '>', quot: '"', '#39': "'", nbsp: ' ' };
  const plain = (html) => String(html || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/&(amp|lt|gt|quot|#39|nbsp);/g, (_, name) => ENTITIES[name])
    .replace(/\s+/g, ' ')
    .trim();
  const terms = (query) => query.toLowerCase().split(/\s+/).filter(Boolean);
  const hasAll = (text, words) => words.every((word) => text.includes(word));

  const start = () => {
    // The drawer is the theme's #__drawer checkbox. Clicking it, as the theme itself does, fires the
    // change event the theme listens to; the menu label becomes a button for the keyboard.
    const drawer = document.getElementById('__drawer');
    const menu = document.querySelector('.nf-menu');
    const narrow = window.matchMedia('(max-width: 76.234375em)');
    const drawerOpen = () => Boolean(drawer && drawer.checked && narrow.matches);
    const setDrawer = (open) => {
      if (drawer && drawer.checked !== open) drawer.click();
    };
    const closeDrawer = () => {
      setDrawer(false);
      if (menu) menu.focus();
    };
    if (drawer && menu) {
      menu.setAttribute('role', 'button');
      menu.tabIndex = 0;
      const sync = () => menu.setAttribute('aria-expanded', String(drawer.checked));
      sync();
      drawer.addEventListener('change', sync);
      menu.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        // The theme clicks a focused label on Enter too; stopping here toggles the drawer once.
        event.preventDefault();
        event.stopPropagation();
        setDrawer(!drawer.checked);
      });
    }

    const input = document.querySelector('[data-nf-search]');
    const box = document.querySelector('[data-nf-results]');
    const nav = document.querySelector('.md-sidebar--primary .md-nav--primary');
    if (!input || !box || !nav) return;
    let base = '.';
    try {
      base = JSON.parse(document.getElementById('__config').textContent).base || '.';
    } catch (error) {
      base = '.';
    }
    base = base.replace(/\/$/, '');

    const pageLinks = () => Array.from(nav.querySelectorAll('a.md-nav__link'))
      .filter((link) => !link.closest('.md-nav--secondary'));

    // Section counts and phase notes.
    nav.querySelectorAll(':scope > .md-nav__list > .md-nav__item--section').forEach((section) => {
      const label = section.querySelector(':scope > .md-nav__link');
      const count = Array.from(section.querySelectorAll('a.md-nav__link')).filter((link) => !link.closest('.md-nav--secondary')).length;
      if (label && count > 0 && !label.querySelector('.nf-count')) {
        const mark = document.createElement('i');
        mark.className = 'nf-count';
        mark.textContent = String(count);
        label.appendChild(mark);
      }
      const name = label ? label.textContent.trim().toLowerCase() : '';
      if (!name.startsWith('phases')) return;
      section.querySelectorAll('a.md-nav__link').forEach((link) => {
        const title = link.textContent.trim();
        if (!PHASE_NOTES[title] || link.querySelector('.nf-sub')) return;
        const note = document.createElement('small');
        note.className = 'nf-sub';
        note.textContent = PHASE_NOTES[title];
        link.appendChild(note);
      });
    });

    // The search index loads on first use.
    let pages = null;
    let loading = null;
    const load = () => {
      if (!loading) {
        loading = fetch(base + '/search/search_index.json')
          .then((response) => (response.ok ? response.json() : { docs: [] }))
          .then((data) => {
            const docs = Array.isArray(data.docs) ? data.docs : [];
            const titles = new Map();
            docs.forEach((doc) => {
              if (!String(doc.location).includes('#')) titles.set(doc.location, plain(doc.title));
            });
            pages = docs.map((doc) => {
              const location = String(doc.location || '');
              const page = location.split('#')[0];
              const title = plain(doc.title);
              return {
                location,
                title,
                page: titles.get(page) || '',
                isPage: !location.includes('#'),
                titleKey: title.toLowerCase(),
                text: plain(doc.text),
              };
            });
            return pages;
          })
          .catch(() => (pages = []));
      }
      return loading;
    };

    const filterNav = (words) => {
      nav.classList.toggle('nf-filtering', words.length > 0);
      pageLinks().forEach((link) => {
        const item = link.closest('.md-nav__item');
        if (item) item.classList.toggle('nf-hidden', words.length > 0 && !hasAll(link.textContent.toLowerCase(), words));
      });
      nav.querySelectorAll('.md-nav__item--nested').forEach((group) => {
        const visible = Array.from(group.querySelectorAll('a.md-nav__link'))
          .some((link) => !link.closest('.md-nav--secondary') && !link.closest('.nf-hidden'));
        group.classList.toggle('nf-hidden', words.length > 0 && !visible);
      });
    };

    const snippet = (text, word) => {
      const at = text.toLowerCase().indexOf(word);
      if (at < 0) return text.slice(0, 110);
      const from = Math.max(0, at - 40);
      return (from > 0 ? '…' : '') + text.slice(from, from + 110) + (from + 110 < text.length ? '…' : '');
    };

    const render = (words) => {
      box.textContent = '';
      if (words.length === 0 || words.join('').length < 2) {
        box.hidden = true;
        return;
      }
      box.hidden = false;
      if (pages === null) {
        const wait = document.createElement('p');
        wait.className = 'nf-results__note';
        wait.textContent = 'Searching…';
        box.appendChild(wait);
        load().then(() => {
          if (terms(input.value).join(' ') === words.join(' ')) render(words);
        });
        return;
      }
      const hits = pages
        .map((doc) => {
          const inTitle = hasAll(doc.titleKey, words);
          const inText = inTitle || hasAll(doc.text.toLowerCase(), words);
          if (!inText) return null;
          const score = (inTitle ? 4 : 0) + (doc.isPage ? 1 : 0) + (doc.titleKey.startsWith(words[0]) ? 1 : 0);
          return { doc, score, inTitle };
        })
        .filter(Boolean)
        .sort((a, b) => b.score - a.score)
        .slice(0, MAX_RESULTS);
      const head = document.createElement('p');
      head.className = 'nf-results__note';
      head.textContent = hits.length === 0 ? 'Nothing matches. Try a phase or a command name.' : 'In the pages';
      box.appendChild(head);
      hits.forEach(({ doc, inTitle }) => {
        const link = document.createElement('a');
        link.href = base + '/' + doc.location;
        const title = document.createElement('b');
        title.textContent = doc.title || doc.page || doc.location;
        link.appendChild(title);
        const where = document.createElement('small');
        where.textContent = !doc.isPage && doc.page ? doc.page : inTitle ? '' : snippet(doc.text, words[0]);
        if (where.textContent) link.appendChild(where);
        box.appendChild(link);
      });
    };

    const update = () => {
      const words = terms(input.value);
      filterNav(words);
      render(words);
    };
    input.addEventListener('input', update);
    input.addEventListener('focus', () => {
      load();
    });
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        // Esc clears the field; in an open drawer a second Esc closes the drawer.
        event.preventDefault();
        if (input.value) {
          input.value = '';
          update();
          if (!drawerOpen()) input.blur();
        } else if (drawerOpen()) {
          closeDrawer();
        } else {
          input.blur();
        }
      } else if (event.key === 'Enter') {
        const first = box.querySelector('a') || pageLinks().find((link) => !link.closest('.nf-hidden'));
        if (first) window.location.href = first.href;
      }
    });
    document.addEventListener('keydown', (event) => {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      if (event.key === 'Escape') {
        if (!event.defaultPrevented && drawerOpen()) closeDrawer();
        return;
      }
      if (event.key !== '/') return;
      const target = event.target;
      if (target && target.closest && target.closest('input, textarea, select, [contenteditable]')) return;
      event.preventDefault();
      // On a narrow screen the field lives in the drawer, so the drawer opens first.
      if (narrow.matches) setDrawer(true);
      input.focus();
    });
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
