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

  // Resolve the page's share thumbnail: the per-page og:image (article cover / hero)
  // set in <head>, falling back to the site logo. This is the "small icon" carried
  // into WeChat Moments / Chat shares.
  function shareImageUrl() {
    const og = document.querySelector('meta[property="og:image"]');
    if (og && og.content) return og.content;
    return new URL('assets/logo-192.png', location.href).href;
  }

  // Fetch the share image as a File so it can be attached to a system share.
  async function fetchShareImage() {
    const url = shareImageUrl();
    try {
      const res = await fetch(url, {mode: 'cors'});
      if (!res.ok) return null;
      const blob = await res.blob();
      const ext = (blob.type.split('/')[1] || 'png').replace('jpeg', 'jpg');
      const name = 'share-' + new Date().toISOString().slice(0,10) + '.' + ext;
      return new File([blob], name, {type: blob.type});
    } catch (error) {
      return null;
    }
  }

  // First content image on the page (article cover / hero), else logo — a local
  // fallback reader in case og:image is absent.
  function firstContentImage() {
    const imgs = document.querySelectorAll('main img, article img, .container img, .hero img');
    for (const img of imgs) {
      const src = img.getAttribute('src') || '';
      if (/logo|favicon|icon/i.test(src)) continue;
      if (img.getAttribute('alt') === 'AMC') continue;
      return new URL(src, location.href).href;
    }
    return new URL('assets/logo-192.png', location.href).href;
  }

  async function sharePage() {
    const url = new URL(location.href);
    // Avoid propagating inspection/cache query parameters in article shares.
    url.search = '';
    url.hash = '';
    const title = document.title;
    const text = (document.querySelector('meta[name="description"]')?.content || '').slice(0, 120);

    // Preferred path: system Web Share API with the thumbnail image attached.
    // This invokes the OS share sheet where the user can pick WeChat Moments/Chat,
    // and the shared content carries the small icon (the article image or logo).
    if (navigator.share) {
      const file = await fetchShareImage();
      const shareData = {title, text, url: url.href};
      if (file && (!navigator.canShare || navigator.canShare({files: [file]}))) {
        shareData.files = [file];
      }
      try {await navigator.share(shareData);return;}
      catch (error) {
        if (error.name === 'AbortError') return;
        if (shareData.files) {
          // Some targets reject the image; retry with plain text+url.
          delete shareData.files;
          try {await navigator.share(shareData);return;}
          catch (e2) {if (e2.name === 'AbortError') return;}
        }
      }
    }
    // Fallback: copy the share link.
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(url.href);
        notify('链接已复制，可粘贴到微信分享');
        return;
      } catch { /* Clipboard may be unavailable inside an in-app browser. */ }
    }
    window.prompt('复制此链接后分享', url.href);
  }
  document.querySelectorAll('[data-share]').forEach(button => button.addEventListener('click', sharePage));
})();
