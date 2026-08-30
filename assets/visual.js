(() => {
  'use strict';
  // Keep the selected column visible in the horizontally scrollable mobile menus.
  for (const nav of document.querySelectorAll('.nav,.collection-index')) {
    const current = nav.querySelector('.cur,[aria-current="page"]');
    if (current && nav.scrollWidth > nav.clientWidth) {
      nav.scrollLeft = current.getBoundingClientRect().left - nav.getBoundingClientRect().left - (nav.clientWidth - current.offsetWidth) / 2;
    }
  }
  const article = document.querySelector('.prose');
  const bar = document.querySelector('.read-progress span');
  if (!article || !bar) return;
  let queued = false;
  function paint() {
    const top = article.getBoundingClientRect().top + window.scrollY;
    const end = top + article.offsetHeight - window.innerHeight * .65;
    const start = Math.max(0, top - window.innerHeight * .25);
    const ratio = Math.max(0, Math.min(1, (window.scrollY - start) / Math.max(1, end - start)));
    bar.style.transform = `scaleX(${ratio})`;
    queued = false;
  }
  function schedule() { if (!queued) { queued = true; requestAnimationFrame(paint); } }
  window.addEventListener('scroll', schedule, {passive:true});
  window.addEventListener('resize', schedule);
  window.addEventListener('load', schedule);
  schedule();
})();
