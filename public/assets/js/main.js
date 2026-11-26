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

  initDecline();
})();
