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
  const UNAVAILABLE = 'Search is unavailable — the index list still filters';

  const ENTITIES = { amp: '&', lt: '<', gt: '>', quot: '"', '#39': "'", nbsp: ' ' };
  const plain = (html) => String(html || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/&(amp|lt|gt|quot|#39|nbsp);/g, (_, name) => ENTITIES[name])
    .replace(/\s+/g, ' ')
    .trim();
  // Names compare without the command prefix and by their words: "/neuroflow:data-analyze",
  // "/data-analyze" and "data analyze" are one name.
  const WORD = /[\p{L}\p{N}]+/gu;
  const wordsOf = (text) => String(text || '').toLowerCase().match(WORD) || [];
  const keyOf = (text) => wordsOf(String(text || '').trim().replace(/^(?:\/neuroflow:|\/|neuroflow:)/i, '')).join(' ');
  const termsOf = (query) => keyOf(query).split(' ').filter(Boolean);
  // A query word matches where a word starts: "search" finds "Search strategy" but not "research".
  const startsWord = (word) => new RegExp('(?:^|[^\\p{L}\\p{N}])' + word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'u');

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
    const status = document.querySelector('[data-nf-status]');
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
    // The name a page has in the index, without the phase note that follows it.
    const navKey = (link) => keyOf((link.querySelector('.md-ellipsis') || link).textContent);

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

    // The search index loads on first use. A failed load is forgotten, so the next keystroke tries
    // again; until then the field still filters the index.
    let pages = null;
    let loading = null;
    let failed = false;
    const load = () => {
      if (!loading) {
        loading = fetch(base + '/search/search_index.json')
          .then((response) => {
            if (!response.ok) throw new Error('search index: HTTP ' + response.status);
            return response.json();
          })
          .then((data) => {
            if (!data || !Array.isArray(data.docs)) throw new Error('search index: no documents');
            const docs = data.docs;
            const titles = new Map();
            docs.forEach((doc) => {
              if (!String(doc.location).includes('#')) titles.set(doc.location, plain(doc.title));
            });
            // Where each page sits in the index and the names it has there ("Overview" for a page
            // titled otherwise); both count for its rank.
            const root = new URL(base + '/', window.location.href);
            const inNav = new Map();
            pageLinks().forEach((link, order) => {
              const url = link.href.split('#')[0];
              const entry = inNav.get(url) || { order, names: [] };
              entry.names.push(navKey(link));
              inNav.set(url, entry);
            });
            pages = docs.map((doc) => {
              const location = String(doc.location || '');
              const page = location.split('#')[0];
              const pageUrl = new URL(page, root).href;
              const isPage = !location.includes('#');
              const title = plain(doc.title);
              const listed = (isPage && inNav.get(pageUrl)) || { names: [] };
              const names = [keyOf(title)].concat(listed.names);
              const text = plain(doc.text);
              return {
                location,
                title,
                page: titles.get(page) || '',
                pageUrl,
                isPage,
                names,
                words: names.join(' ').split(' ').filter(Boolean),
                order: (inNav.get(pageUrl) || { order: Infinity }).order,
                text,
                textKey: text.toLowerCase(),
              };
            });
            failed = false;
            return pages;
          })
          .catch(() => {
            loading = null;
            failed = true;
            return null;
          });
      }
      return loading;
    };

    // Screen readers hear the outcome of a search (a status line), not every result.
    let saying = 0;
    const announce = (text) => {
      clearTimeout(saying);
      if (!status) return;
      if (!text) status.textContent = '';
      else saying = setTimeout(() => { status.textContent = text; }, 400);
    };

    const filterNav = (words) => {
      const tests = words.map(startsWord);
      nav.classList.toggle('nf-filtering', words.length > 0);
      pageLinks().forEach((link) => {
        const item = link.closest('.md-nav__item');
        const text = link.textContent.toLowerCase();
        if (item) item.classList.toggle('nf-hidden', words.length > 0 && !tests.every((test) => test.test(text)));
      });
      nav.querySelectorAll('.md-nav__item--nested').forEach((group) => {
        const visible = Array.from(group.querySelectorAll('a.md-nav__link'))
          .some((link) => !link.closest('.md-nav--secondary') && !link.closest('.nf-hidden'));
        group.classList.toggle('nf-hidden', words.length > 0 && !visible);
      });
    };

    const snippet = (text, word) => {
      const found = startsWord(word).exec(text.toLowerCase());
      const at = found ? found.index + found[0].length - word.length : -1;
      if (at < 0) return text.slice(0, 110);
      const from = Math.max(0, at - 40);
      return (from > 0 ? '…' : '') + text.slice(from, from + 110) + (from + 110 < text.length ? '…' : '');
    };

    // Every query word must start a word of the title, an index name or the text. A page whose name is
    // the query comes first ("phase" -> /neuroflow:phase); then matches in the title before matches in
    // the text, pages before their sections, names that start with the query, and whole words before
    // word starts. Ties keep the order of the index.
    const rank = (key) => {
      const words = key.split(' ').filter(Boolean);
      const tests = words.map(startsWord);
      const seen = new Set();
      return pages
        .map((doc, index) => {
          let whole = 0;
          let inTitle = true;
          for (let i = 0; i < words.length; i += 1) {
            if (doc.words.includes(words[i])) whole += 1;
            else if (!doc.words.some((word) => word.startsWith(words[i]))) {
              inTitle = false;
              if (!tests[i].test(doc.textKey)) return null;
            }
          }
          const exact = doc.names.includes(key);
          const lead = doc.names.some((name) => name.startsWith(key));
          const score = (exact ? (doc.isPage ? 10000 : 300) : 0)
            + (inTitle ? (doc.isPage ? 2000 : 1000) : (doc.isPage ? 100 : 0))
            + (lead ? 500 : 0)
            + whole * 10;
          return { doc, score, inTitle, index };
        })
        .filter(Boolean)
        .sort((a, b) => b.score - a.score || a.doc.order - b.doc.order || a.index - b.index)
        .filter(({ doc }) => {
          // A page can repeat a heading (several "Installation" sections); it is listed once.
          const id = doc.pageUrl + '\n' + doc.names[0];
          if (seen.has(id)) return false;
          seen.add(id);
          return true;
        });
    };

    const note = (text) => {
      box.textContent = '';
      const line = document.createElement('p');
      line.className = 'nf-results__note';
      line.textContent = text;
      box.appendChild(line);
    };

    const render = (query) => {
      const key = keyOf(query);
      const words = key.split(' ').filter(Boolean);
      box.textContent = '';
      if (words.length === 0 || words.join('').length < 2) {
        box.hidden = true;
        announce('');
        return;
      }
      box.hidden = false;
      if (pages === null) {
        note(failed ? UNAVAILABLE : 'Searching…');
        load().then((ready) => {
          if (keyOf(input.value) !== key) return;
          if (ready) {
            render(input.value);
          } else {
            note(UNAVAILABLE);
            announce(UNAVAILABLE);
          }
        });
        return;
      }
      const found = rank(key);
      const hits = found.slice(0, MAX_RESULTS);
      note(hits.length === 0 ? 'Nothing matches. Try a phase or a command name.' : 'In the pages');
      announce(found.length === 0 ? 'No results' : found.length === 1 ? '1 result' : found.length + ' results' + (found.length > MAX_RESULTS ? ', the first ' + MAX_RESULTS + ' listed' : ''));
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

    // The results sit between the field and the index, which the theme scrolls to the current page
    // on load: typing brings them back into view under the field.
    const scrollers = [input.closest('.md-sidebar__scrollwrap'), input.closest('.md-sidebar__inner')].filter(Boolean);
    const update = () => {
      filterNav(termsOf(input.value));
      render(input.value);
      if (input.value.trim()) scrollers.forEach((el) => { el.scrollTop = 0; });
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
        // The page whose index name is the query, else the first match, else the first page left.
        const key = keyOf(input.value);
        const named = key ? pageLinks().find((link) => navKey(link) === key) : null;
        const first = named || box.querySelector('a') || pageLinks().find((link) => !link.closest('.nf-hidden'));
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
