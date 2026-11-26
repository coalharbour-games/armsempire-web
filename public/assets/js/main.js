(function () {
  'use strict';

  function initDecline() {
    var button = document.querySelector('[data-decline]');
    var message = document.querySelector('[data-decline-msg]');
    if (!button || !message) return;
    button.addEventListener('click', function () {
      message.textContent = 'In our regime, this is not an option.';
    });
  }

  function trapFocus(container, event) {
    var items = container.querySelectorAll('button, a[href], [tabindex]:not([tabindex="-1"])');
    var visible = Array.prototype.filter.call(items, function (el) { return el.offsetParent !== null; });
    if (!visible.length) return;
    var first = visible[0];
    var last = visible[visible.length - 1];
    if (event.shiftKey && document.activeElement === first) { last.focus(); event.preventDefault(); }
    else if (!event.shiftKey && document.activeElement === last) { first.focus(); event.preventDefault(); }
  }

  function initLightbox() {
    var groups = document.querySelectorAll('[data-gallery]');
    if (!groups.length) return;

    var box = document.createElement('div');
    box.className = 'lightbox';
    box.hidden = true;
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.setAttribute('aria-label', 'Screenshot');
    box.innerHTML =
      '<figure><img alt=""><figcaption class="m"></figcaption></figure>' +
      '<button type="button" class="lightbox__btn lightbox__prev" aria-label="Previous screenshot">\u2190</button>' +
      '<button type="button" class="lightbox__btn lightbox__next" aria-label="Next screenshot">\u2192</button>' +
      '<button type="button" class="lightbox__btn lightbox__close" aria-label="Close">\u00d7</button>';
    document.body.appendChild(box);

    var img = box.querySelector('img');
    var caption = box.querySelector('figcaption');
    var prev = box.querySelector('.lightbox__prev');
    var next = box.querySelector('.lightbox__next');
    var links = [];
    var index = 0;
    var opener = null;

    function show(i) {
      index = (i + links.length) % links.length;
      var link = links[index];
      img.src = link.getAttribute('href');
      img.alt = link.querySelector('img').alt;
      caption.textContent = link.getAttribute('data-caption') || '';
      prev.hidden = next.hidden = links.length < 2;
    }

    function open(group, link) {
      links = Array.prototype.slice.call(group.querySelectorAll('[data-lightbox]'));
      opener = link;
      show(links.indexOf(link));
      box.hidden = false;
      document.body.classList.add('scroll-lock');
      box.querySelector('.lightbox__close').focus();
    }

    function close() {
      box.hidden = true;
      img.removeAttribute('src');
      document.body.classList.remove('scroll-lock');
      if (opener) opener.focus();
    }

    Array.prototype.forEach.call(groups, function (group) {
      group.addEventListener('click', function (e) {
        var link = e.target.closest('[data-lightbox]');
        if (!link || e.ctrlKey || e.metaKey || e.shiftKey) return;
        e.preventDefault();
        open(group, link);
      });
    });
    prev.addEventListener('click', function () { show(index - 1); });
    next.addEventListener('click', function () { show(index + 1); });
    box.querySelector('.lightbox__close').addEventListener('click', close);
    box.addEventListener('click', function (e) { if (e.target === box) close(); });
    document.addEventListener('keydown', function (e) {
      if (box.hidden) return;
      if (e.key === 'Escape') close();
      else if (e.key === 'ArrowLeft') show(index - 1);
      else if (e.key === 'ArrowRight') show(index + 1);
      else if (e.key === 'Tab') trapFocus(box, e);
    });
  }

  function localDate() {
    var d = new Date();
    var pad = function (n) { return (n < 10 ? '0' : '') + n; };
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  }

  function seen(key, mark) {
    try {
      if (mark) sessionStorage.setItem(key, '1');
      return sessionStorage.getItem(key) === '1';
    } catch (e) {
      return false;
    }
  }

  function initOverlay() {
    var source = document.getElementById('overlay-data');
    if (!source) return;
    var items;
    try { items = JSON.parse(source.textContent); } catch (e) { return; }
    var today = localDate();
    var item = items.filter(function (i) { return i.from <= today && today <= i.to; })[0];
    if (!item) return;
    var key = 'overlay-' + item.id;
    if (seen(key)) return;
    seen(key, true);

    var overlay = document.createElement('div');
    overlay.className = 'overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-labelledby', 'overlay-title');
    var card = document.createElement('div');
    card.className = 'overlay__card';
    overlay.appendChild(card);

    if (item.image) {
      var img = document.createElement('img');
      img.className = 'overlay__img';
      img.src = item.image;
      img.alt = item.image_alt || '';
      img.width = 1200;
      img.height = 675;
      card.appendChild(img);
    }
    var body = document.createElement('div');
    body.className = 'overlay__body';
    card.appendChild(body);
    if (item.kicker) {
      var kicker = document.createElement('div');
      kicker.className = 'overlay__kicker';
      kicker.textContent = item.kicker;
      body.appendChild(kicker);
    }
    var title = document.createElement('h2');
    title.className = 'd overlay__title';
    title.id = 'overlay-title';
    title.textContent = item.title;
    body.appendChild(title);
    if (item.text) {
      var text = document.createElement('div');
      text.className = 'overlay__text';
      item.text.split(/\n\s*\n/).forEach(function (para) {
        var p = document.createElement('p');
        p.textContent = para.trim();
        text.appendChild(p);
      });
      body.appendChild(text);
    }
    if (item.button && item.link) {
      var cta = document.createElement('a');
      cta.className = 'btn btn--accent btn--sm overlay__cta';
      cta.href = item.link;
      cta.textContent = item.button;
      body.appendChild(cta);
    }
    var closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'overlay__close';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.textContent = '\u00d7';
    card.appendChild(closeBtn);

    var opener = document.activeElement;
    function close() {
      overlay.remove();
      document.body.classList.remove('scroll-lock');
      document.removeEventListener('keydown', onKey);
      if (opener && opener.focus) opener.focus();
    }
    function onKey(e) {
      if (e.key === 'Escape') close();
      else if (e.key === 'Tab') trapFocus(overlay, e);
    }
    closeBtn.addEventListener('click', close);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
    document.addEventListener('keydown', onKey);
    document.body.appendChild(overlay);
    document.body.classList.add('scroll-lock');
    closeBtn.focus();
  }

  initDecline();
  initLightbox();
  initOverlay();
})();
