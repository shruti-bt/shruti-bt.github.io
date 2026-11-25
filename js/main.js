/* ==========================================================================
   Site interactions: BibTeX toggle, sticky nav, scroll spy
   ========================================================================== */

function updateNav() {
    var nav = document.querySelector('nav');
    var header = document.querySelector('header h1');
    if (nav) {
        // Show the name in the nav only once the big heading has scrolled away.
        var threshold = header ? header.offsetTop + header.offsetHeight : 8;
        nav.classList.toggle('is-scrolled', window.scrollY > threshold);
    }

    var current = null;
    ['news', 'publications'].forEach(function (id) {
        var el = document.getElementById(id);
        if (el && el.getBoundingClientRect().top <= 120) current = id;
    });
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

document.addEventListener('DOMContentLoaded', function () {
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
