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

  initDecline();
  initLightbox();
})();
