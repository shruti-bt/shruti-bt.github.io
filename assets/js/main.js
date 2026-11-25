/* ==========================================================================
   Site interactions: BibTeX toggle, sticky nav, scroll spy
   ========================================================================== */

function updateNav() {
    // the Gallery page has its own fixed nav state
    if (document.body.classList.contains('page-gallery')) return;
    var nav = document.querySelector('nav');
    var header = document.querySelector('header h1');
    if (nav) {
        // Show the name in the nav only once the big heading has scrolled away.
        var threshold = header ? header.offsetTop + header.offsetHeight : 8;
        nav.classList.toggle('is-scrolled', window.scrollY > threshold);
    }

    var current = null;
    var ids = ['news', 'publications', 'gallery'].filter(function (id) {
        return document.getElementById(id);
    });
    ids.forEach(function (id) {
        if (document.getElementById(id).getBoundingClientRect().top <= 120) current = id;
    });
    // at the very bottom the last section can never reach the top: highlight it anyway
    if (ids.length && window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) {
        current = ids[ids.length - 1];
    }
    document.querySelectorAll('.nav-item').forEach(function (link) {
        link.classList.toggle('active', link.getAttribute('href') === '#' + current);
    });
}

// News & Highlights: show the first VISIBLE_NEWS items, the rest scroll inside the box.
var VISIBLE_NEWS = 7;

function sizeNewsBox() {
    var box = document.querySelector('.news-scroll');
    if (!box) return;
    var items = box.querySelectorAll('.news-item');
    if (items.length <= VISIBLE_NEWS) {
        box.style.maxHeight = 'none';
        box.classList.remove('has-more');
        return;
    }
    var boxTop = box.getBoundingClientRect().top - box.scrollTop;
    var nth = items[VISIBLE_NEWS - 1].getBoundingClientRect();
    // end just after item 7, with a peek of item 8 so it is clear the list continues
    box.style.maxHeight = Math.ceil(nth.bottom - boxTop + 36) + 'px';
    updateNewsFade();
}

function updateNewsFade() {
    var box = document.querySelector('.news-scroll');
    if (!box) return;
    var atEnd = box.scrollTop + box.clientHeight >= box.scrollHeight - 4;
    box.classList.toggle('has-more', box.scrollHeight > box.clientHeight + 4 && !atEnd);
}

// Light / dark button: flips the current look and remembers the choice
function setupThemeToggle() {
    var button = document.querySelector('.theme-toggle');
    if (!button) return;
    var root = document.documentElement;
    button.addEventListener('click', function () {
        var current = root.getAttribute('data-theme') || 'light';
        var next = current === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-theme', next);
        try { localStorage.setItem('theme', next); } catch (e) {}
    });
}

// Gallery: click a photo to see it full size; click outside or press Esc to close
function setupLightbox() {
    var box = document.querySelector('.lightbox');
    if (!box || typeof box.showModal !== 'function') return;
    var img = box.querySelector('img');
    var caption = box.querySelector('.lightbox-caption');
    document.querySelectorAll('.gallery-open').forEach(function (button) {
        button.addEventListener('click', function () {
            var thumb = button.querySelector('img');
            var figcap = button.parentElement.querySelector('figcaption');
            img.src = button.getAttribute('data-full');
            img.alt = thumb ? thumb.alt : '';
            caption.innerHTML = figcap ? figcap.innerHTML : '';
            box.showModal();
        });
    });
    box.addEventListener('close', function () { img.removeAttribute('src'); });
    box.addEventListener('click', function (e) {
        if (e.target === box || e.target.classList.contains('lightbox-close')) box.close();
    });
}

// Publications / Patents tabs: switch the list in place
function setupTabs() {
    var tabs = Array.prototype.slice.call(document.querySelectorAll('.section-tabs [role="tab"]'));
    if (!tabs.length) return;
    function select(tab, focus) {
        tabs.forEach(function (t) {
            var on = t === tab;
            t.setAttribute('aria-selected', String(on));
            t.tabIndex = on ? 0 : -1;
            document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
        });
        if (focus) tab.focus();
    }
    tabs.forEach(function (tab, i) {
        tab.addEventListener('click', function () { select(tab); });
        tab.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
                var next = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
                select(next, true);
            }
        });
    });
    // a link to #patents (from another page or the highlights line) opens the Patents tab
    function fromHash() {
        if (location.hash !== '#patents') return;
        select(document.getElementById('tab-patents') || tabs[0]);
        document.getElementById('publications').scrollIntoView();
    }
    select(tabs[0]);
    fromHash();
    window.addEventListener('hashchange', fromHash);
    document.querySelectorAll('a[href="#patents"]').forEach(function (a) {
        // clicking it twice should still work, even though the hash does not change
        a.addEventListener('click', function () { if (location.hash === '#patents') setTimeout(fromHash, 0); });
    });
    document.querySelectorAll('a[href="#publications"]').forEach(function (a) {
        a.addEventListener('click', function () { select(tabs[0]); });
    });
}

// Gallery page: filter the collage by event ("All photos" shows everything).
// A link like gallery.html#event-name opens with that event selected.
function setupGalleryFilters() {
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.gallery-filters button'));
    if (!buttons.length) return;
    var items = document.querySelectorAll('.gallery-item[data-event]');
    function show(filter) {
        if (!buttons.some(function (b) { return b.getAttribute('data-filter') === filter; })) filter = 'all';
        buttons.forEach(function (b) {
            b.setAttribute('aria-pressed', String(b.getAttribute('data-filter') === filter));
        });
        items.forEach(function (item) {
            item.hidden = filter !== 'all' && item.getAttribute('data-event') !== filter;
        });
    }
    buttons.forEach(function (b) {
        b.addEventListener('click', function () {
            var filter = b.getAttribute('data-filter');
            show(filter);
            history.replaceState(null, '', filter === 'all' ? location.pathname : '#' + filter);
        });
    });
    show(location.hash.slice(1) || 'all');
    window.addEventListener('hashchange', function () { show(location.hash.slice(1) || 'all'); });
}

document.addEventListener('DOMContentLoaded', function () {
    setupThemeToggle();
    setupGalleryFilters();
    setupTabs();
    setupLightbox();

    document.querySelectorAll('[data-bibtex]').forEach(function (button) {
        var bib = document.getElementById('bib_' + button.getAttribute('data-bibtex'));
        if (!bib) return;
        button.setAttribute('aria-expanded', 'false');
        button.addEventListener('click', function () {
            bib.hidden = !bib.hidden;
            button.setAttribute('aria-expanded', String(!bib.hidden));
        });
    });

    updateNav();
    window.addEventListener('scroll', updateNav, { passive: true });

    sizeNewsBox();
    var newsBox = document.querySelector('.news-scroll');
    if (newsBox) newsBox.addEventListener('scroll', updateNewsFade, { passive: true });
    window.addEventListener('resize', sizeNewsBox);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(sizeNewsBox);
});
