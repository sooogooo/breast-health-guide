/* Native menu enhancement and user-triggered sharing. No telemetry or storage. */
(() => {
  'use strict';
  document.documentElement.classList.add('js');
  const menu = document.querySelector('.mobile-menu');
  const summary = menu?.querySelector('summary');
  if (menu) {
    document.addEventListener('click', event => {
      if (menu.open && !menu.contains(event.target)) menu.open = false;
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && menu.open) {
        menu.open = false;
        summary.focus();
      }
    });
    menu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {menu.open = false;}));
    const desktop = matchMedia('(min-width: 701px)');
    desktop.addEventListener('change', event => {if (event.matches) menu.open = false;});
  }
  const status = document.querySelector('.share-status');
  let timer;
  function notify(message) {
    if (!status) return;
    clearTimeout(timer);
    status.textContent = message;
    timer = setTimeout(() => {status.textContent = '';}, 4000);
  }
  async function sharePage() {
    const url = new URL(location.href);
    // Avoid propagating inspection/cache query parameters in article shares.
    url.search = '';
    url.hash = '';
    if (navigator.share) {
      try {await navigator.share({title:document.title, url:url.href});return;}
      catch (error) {if (error.name === 'AbortError') return;}
    }
    if (navigator.clipboard?.writeText) {
      try {await navigator.clipboard.writeText(url.href);notify('链接已复制，可以粘贴分享');return;}
      catch { /* Clipboard may be unavailable inside an in-app browser. */ }
    }
    window.prompt('复制此链接后分享', url.href);
  }
  document.querySelectorAll('[data-share]').forEach(button => button.addEventListener('click', sharePage));
})();
