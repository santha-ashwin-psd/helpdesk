/**
 * Frappe Helpdesk — Breakdown Report Embed Widget
 *
 * Usage — drop this single <script> tag anywhere on the client's page:
 *
 *   <script
 *     src="https://your-frappe-site/assets/helpdesk/js/breakdown-widget.js"
 *     data-site="https://your-frappe-site"
 *     data-machine="Compressor-Unit-3"
 *     data-location="Plant A"
 *   ></script>
 *
 * OR render an inline iframe by placing a target div first:
 *
 *   <div id="hd-breakdown-form"></div>
 *   <script src="..." data-site="https://your-frappe-site" data-inline></script>
 *
 * Options (data-* attributes on the <script> tag):
 *   data-site      — Required. Base URL of your Frappe site.
 *   data-machine   — Optional. Pre-fill the Machine/Asset field.
 *   data-location  — Optional. Pre-fill the Location field.
 *   data-inline    — Optional. Render an inline iframe inside #hd-breakdown-form
 *                    instead of a floating button + modal.
 *   data-label     — Optional. Button label (default: "Report Breakdown").
 *   data-color     — Optional. Button accent colour (default: "#2563EB").
 *   data-target    — Optional. CSS selector for the inline container
 *                    (default: "#hd-breakdown-form").
 *   data-height    — Optional. iframe height in px for inline mode (default: 680).
 */
(function () {
  'use strict';

  // ── Read configuration from the <script> tag itself ─────────────────────
  var scripts  = document.querySelectorAll('script[data-site]');
  var scriptEl = scripts[scripts.length - 1]; // last matching tag wins

  if (!scriptEl) {
    console.warn('[HD Widget] Missing data-site attribute on script tag.');
    return;
  }

  var cfg = {
    site:    scriptEl.getAttribute('data-site').replace(/\/$/, ''),
    machine: scriptEl.getAttribute('data-machine')  || '',
    location:scriptEl.getAttribute('data-location') || '',
    label:   scriptEl.getAttribute('data-label')    || 'Report Breakdown',
    color:   scriptEl.getAttribute('data-color')    || '#2563EB',
    inline:  scriptEl.hasAttribute('data-inline'),
    target:  scriptEl.getAttribute('data-target')   || '#hd-breakdown-form',
    height:  parseInt(scriptEl.getAttribute('data-height') || '680', 10),
  };

  // Build the iframe src URL
  var params = new URLSearchParams();
  if (cfg.machine)  params.set('machine',  cfg.machine);
  if (cfg.location) params.set('location', cfg.location);
  var formURL = cfg.site + '/breakdown-report' + (params.toString() ? '?' + params.toString() : '');

  // ── Shared iframe factory ────────────────────────────────────────────────
  function createIframe(opts) {
    var iframe = document.createElement('iframe');
    iframe.src = formURL;
    iframe.title = 'Breakdown Report Form';
    iframe.setAttribute('frameborder', '0');
    iframe.setAttribute('allow', 'forms');
    iframe.setAttribute('loading', 'lazy');
    iframe.style.cssText = [
      'width:100%',
      'border:none',
      'border-radius:' + (opts.borderRadius || '0'),
      'height:' + (opts.height || cfg.height) + 'px',
      'display:block',
      'transition:opacity .25s',
      'opacity:0',
    ].join(';');
    iframe.onload = function () { iframe.style.opacity = '1'; };
    return iframe;
  }

  // ── Listen for success messages from the iframe ──────────────────────────
  window.addEventListener('message', function (evt) {
    if (!evt.data || evt.data.type !== 'hd-breakdown-submitted') return;
    // Close modal if one is open
    var modal = document.getElementById('hd-widget-modal');
    if (modal) {
      setTimeout(function () { closeModal(); }, 2000);
    }
  });

  // ── INLINE MODE — inject iframe into a container div ────────────────────
  if (cfg.inline) {
    document.addEventListener('DOMContentLoaded', function () {
      var container = document.querySelector(cfg.target);
      if (!container) {
        console.warn('[HD Widget] Inline target "' + cfg.target + '" not found.');
        return;
      }
      container.style.overflow = 'hidden';
      container.style.borderRadius = '16px';
      container.style.boxShadow = '0 4px 24px rgba(0,0,0,.1)';
      var iframe = createIframe({ borderRadius: '16px' });
      container.appendChild(iframe);
    });
    return; // skip floating button
  }

  // ── FLOATING MODE — fixed button + modal overlay ─────────────────────────
  // Inject styles
  var style = document.createElement('style');
  style.textContent = [
    /* Button */
    '#hd-widget-btn{',
      'position:fixed;',
      'bottom:28px;right:28px;',
      'z-index:2147483000;',
      'display:inline-flex;align-items:center;gap:8px;',
      'padding:12px 20px;',
      'background:' + cfg.color + ';',
      'color:#fff;',
      'border:none;border-radius:50px;',
      'font:600 14px/1 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;',
      'cursor:pointer;',
      'box-shadow:0 4px 16px rgba(0,0,0,.25);',
      'transition:transform .18s,box-shadow .18s,opacity .18s;',
    '}',
    '#hd-widget-btn:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.28);}',
    '#hd-widget-btn:active{transform:translateY(0);}',
    '#hd-widget-btn svg{width:16px;height:16px;flex-shrink:0;}',

    /* Overlay */
    '#hd-widget-overlay{',
      'display:none;',
      'position:fixed;inset:0;',
      'z-index:2147483001;',
      'background:rgba(0,0,0,.5);',
      'backdrop-filter:blur(3px);',
      'animation:hdFadeIn .2s ease;',
    '}',
    '#hd-widget-overlay.open{display:block;}',

    /* Modal */
    '#hd-widget-modal{',
      'position:fixed;',
      'z-index:2147483002;',
      'top:50%;left:50%;',
      'transform:translate(-50%,-50%) scale(.96);',
      'width:min(96vw, 620px);',
      'max-height:90vh;',
      'border-radius:16px;',
      'overflow:hidden;',
      'box-shadow:0 20px 60px rgba(0,0,0,.3);',
      'animation:hdSlideIn .22s cubic-bezier(.4,0,.2,1) forwards;',
    '}',
    '#hd-widget-modal iframe{',
      'width:100%;',
      'height:min(90vh, 700px);',
      'border:none;display:block;',
    '}',

    /* Close button */
    '#hd-widget-close{',
      'position:fixed;',
      'top:12px;right:12px;',
      'z-index:2147483003;',
      'width:34px;height:34px;',
      'background:rgba(255,255,255,.15);',
      'border:1px solid rgba(255,255,255,.25);',
      'border-radius:50%;',
      'color:#fff;',
      'font-size:18px;line-height:1;',
      'cursor:pointer;',
      'display:flex;align-items:center;justify-content:center;',
      'transition:background .15s;',
    '}',
    '#hd-widget-close:hover{background:rgba(255,255,255,.28);}',

    '@keyframes hdFadeIn{from{opacity:0}to{opacity:1}}',
    '@keyframes hdSlideIn{from{opacity:0;transform:translate(-50%,-50%) scale(.93)}to{opacity:1;transform:translate(-50%,-50%) scale(1)}}',
  ].join('');
  document.head.appendChild(style);

  // Trigger button
  var btn = document.createElement('button');
  btn.id = 'hd-widget-btn';
  btn.setAttribute('aria-label', cfg.label);
  btn.innerHTML = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"',
    'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">',
    '<path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>',
    '<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    '</svg>',
    cfg.label,
  ].join('');

  // Overlay
  var overlay = document.createElement('div');
  overlay.id = 'hd-widget-overlay';

  // Modal container
  var modal = document.createElement('div');
  modal.id = 'hd-widget-modal';

  // Close button
  var closeBtn = document.createElement('button');
  closeBtn.id = 'hd-widget-close';
  closeBtn.setAttribute('aria-label', 'Close');
  closeBtn.innerHTML = '&#x2715;';

  var iframeEl = null; // lazy-load

  function openModal() {
    if (!iframeEl) {
      iframeEl = createIframe({ borderRadius: '16px' });
      iframeEl.style.height = '100%';
      modal.appendChild(iframeEl);
    }
    overlay.classList.add('open');
    document.body.appendChild(overlay);
    document.body.appendChild(modal);
    document.body.appendChild(closeBtn);
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    overlay.classList.remove('open');
    if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
    if (modal.parentNode)   modal.parentNode.removeChild(modal);
    if (closeBtn.parentNode) closeBtn.parentNode.removeChild(closeBtn);
    document.body.style.overflow = '';
  }

  btn.addEventListener('click', openModal);
  overlay.addEventListener('click', closeModal);
  closeBtn.addEventListener('click', closeModal);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeModal();
  });

  document.addEventListener('DOMContentLoaded', function () {
    document.body.appendChild(btn);
  });
  // If DOM already loaded
  if (document.readyState !== 'loading') {
    document.body.appendChild(btn);
  }
})();
