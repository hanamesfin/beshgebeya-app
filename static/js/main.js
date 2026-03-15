// Sticky & Shrinking Header (vanilla JS)
// Targets: #mainHeader
// Behavior: pins header to top, shrinks after scrollThreshold

// =====================
// GLOBAL THEME & LANG
// =====================
document.addEventListener('DOMContentLoaded', () => {
  // Dynamic Translation Applier
  function applyGlobalTranslations() {
    const lang = localStorage.getItem('lang') || 'en';
    document.documentElement.setAttribute('lang', lang);
    document.querySelectorAll('[data-en]').forEach(el => {
      const translation = el.getAttribute(`data-${lang}`);
      if (translation) {
        if (el.tagName === 'INPUT' && el.hasAttribute('placeholder')) {
          el.placeholder = translation;
        } else if (el.tagName === 'OPTION') {
          el.innerText = translation;
        } else {
          el.innerText = translation;
        }
      }
    });
  }

  applyGlobalTranslations();
  window.applyGlobalTranslations = applyGlobalTranslations; // Expose for HTMX usage

  // HTMX Global Hooks for GSAP & Translations
  document.addEventListener('htmx:afterSwap', (event) => {
    // 1. Re-apply translations to new content
    applyGlobalTranslations();

    // 2. Trigger GSAP Stagger Reveal for matching elements
    const newItems = event.detail.elt.querySelectorAll('.stagger-reveal');
    if (newItems.length > 0) {
      gsap.fromTo(newItems,
        {
          opacity: 0,
          y: 20,
          filter: 'blur(5px)'
        },
        {
          opacity: 1,
          y: 0,
          filter: 'blur(0px)',
          duration: 0.6,
          stagger: 0.05,
          ease: 'expo.out'
        }
      );
    }
  });

  // ChatGPT Style Scroll Down Arrow
  const scrollArrow = document.createElement('div');
  scrollArrow.className = 'scroll-bottom-btn';
  scrollArrow.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 13l5 5 5-5M7 6l5 5 5-5"/></svg>';
  document.body.appendChild(scrollArrow);

  const checkScroll = () => {
    // Show only on inventory, product, and admin pages
    const path = window.location.pathname;
    const allowed = ['/', '/inventory', '/products', '/admin-panel', '/reports', '/import-products', '/sales'].some(p => {
      if (p === '/') return path === '/';
      return path.includes(p);
    });

    if (!allowed) {
      scrollArrow.classList.remove('visible');
      return;
    }

    const scrollable = document.documentElement.scrollHeight - window.innerHeight > 400;
    const atBottom = window.innerHeight + window.pageYOffset >= document.documentElement.scrollHeight - 150;
    const nearTop = window.pageYOffset < 300;

    if (scrollable) {
      if (atBottom) {
        scrollArrow.classList.add('visible', 'up');
      } else if (nearTop) {
        scrollArrow.classList.add('visible');
        scrollArrow.classList.remove('up');
      } else {
        // Between top and bottom, keep visible but respect direction
        scrollArrow.classList.add('visible');
      }
    } else {
      scrollArrow.classList.remove('visible');
    }
  };

  window.addEventListener('scroll', checkScroll);
  window.addEventListener('resize', checkScroll);
  scrollArrow.addEventListener('click', () => {
    if (scrollArrow.classList.contains('up')) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }
  });

  // Footer Status Logic
  const footerLeft = document.querySelector('.footer-left');
  if (footerLeft) {
    const statusDiv = document.createElement('div');
    statusDiv.className = 'footer-status';
    statusDiv.style.marginTop = '4px';
    statusDiv.style.fontSize = '0.75rem';
    statusDiv.style.opacity = '0.7';
    statusDiv.style.display = 'flex';
    statusDiv.style.gap = '15px';

    statusDiv.innerHTML = `
      <span><span class="status-dot pulsing"></span> <span data-en="Live Connection" data-am="ቀጥታ መገናኛ">Live Connection</span></span>
      <span id="footer-time" style="font-family: monospace;"></span>
    `;
    footerLeft.appendChild(statusDiv);

    const updateTime = () => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const timeEl = document.getElementById('footer-time');
      if (timeEl) timeEl.innerText = 'Refreshed: ' + timeStr;
    };
    updateTime();
    setInterval(updateTime, 1000);
  }

  // Initial check
  setTimeout(checkScroll, 500);

  // Global staggered entrance for standard pages
  const entranceItems = document.querySelectorAll('.crystal-card, .data-table, .page-header h1, .section-header');
  if (entranceItems.length > 0) {
    gsap.from(entranceItems, {
      opacity: 0,
      y: 30,
      duration: 0.8,
      stagger: 0.1,
      ease: "expo.out",
      clearProps: "all"
    });
  }
});

// Dashboard Card Expansion logic
let expandedCards = [];
function focusCard(card) {
  const grid = document.getElementById('dashboardGrid');
  if (!grid) return;

  const cardId = card.getAttribute('data-card');
  const index = expandedCards.indexOf(cardId);
  const allCards = document.querySelectorAll('.crystal-card[data-card]');

  if (index > -1) {
    expandedCards.splice(index, 1);
    card.classList.remove('expanded');
  } else {
    expandedCards.push(cardId);
    card.classList.add('expanded');
  }

  // Reset all orders first
  allCards.forEach(c => c.style.order = "0");

  // Update grid stage and apply strict ordering
  grid.classList.remove('expand-stage-1', 'expand-stage-2');

  if (expandedCards.length === 1) {
    grid.classList.add('expand-stage-1');
    const active = document.querySelector(`[data-card="${expandedCards[0]}"]`);
    if (active) active.style.order = "-1";
  } else if (expandedCards.length >= 2) {
    grid.classList.add('expand-stage-2');
    expandedCards.forEach((id, i) => {
      const active = document.querySelector(`[data-card="${id}"]`);
      if (active) active.style.order = i;
    });
    allCards.forEach(c => {
      if (!expandedCards.includes(c.getAttribute('data-card'))) {
        c.style.order = "99";
      }
    });
  }

  // GSAP Smooth Transition for content visibility
  gsap.from(card.querySelector('.card-content'), {
    opacity: 0,
    height: 0,
    duration: 0.5,
    ease: "power2.out"
  });

  // Gentle scroll to keep the focused section in view
  setTimeout(() => {
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, 150);
}
window.focusCard = focusCard;

// =====================
// PRODUCT MANAGEMENT
// =====================
const ProductManager = {
  async edit(productId) {
    try {
      const response = await fetch(`/api/products/${productId}`);
      const data = await response.json();

      if (!data.success) {
        Toast.error('Failed to load product');
        return;
      }

      const product = data.product;
      const content = `
                <form id="edit-product-form">
                    <div class="form-group">
                        <label>Product Name (English) *</label>
                        <input type="text" id="edit-name" value="${product.name || ''}" required>
                    </div>
                    <div class="form-group">
                        <label>Local Name (Amharic)</label>
                        <input type="text" id="edit-local-name" value="${product.local_name || ''}">
                    </div>
                    <div class="form-grid" style="grid-template-columns: 1fr 1fr;">
                        <div class="form-group">
                            <label>SKU</label>
                            <input type="text" id="edit-sku" value="${product.sku || ''}">
                        </div>
                        <div class="form-group">
                            <label>Category *</label>
                            <input type="text" id="edit-category" value="${product.category || ''}" required>
                        </div>
                    </div>
                    <div class="form-grid" style="grid-template-columns: 1fr 1fr;">
                        <div class="form-group">
                            <label>Barcode</label>
                            <input type="text" id="edit-barcode" value="${product.barcode || ''}">
                        </div>
                        <div class="form-group">
                            <label>Local Code</label>
                            <input type="text" id="edit-local-code" value="${product.local_code || ''}">
                        </div>
                    </div>
                    <div class="form-grid" style="grid-template-columns: 1fr 1fr;">
                        <div class="form-group">
                            <label>Brand</label>
                            <input type="text" id="edit-brand" value="${product.brand || ''}">
                        </div>
                        <div class="form-group">
                            <label>Supplier</label>
                            <input type="text" id="edit-supplier" value="${product.supplier || ''}">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea id="edit-description" rows="3">${product.description || ''}</textarea>
                    </div>
                </form>
            `;

      const buttons = [
        { text: 'Cancel', class: 'btn-secondary', onclick: 'Modal.close()' },
        { text: 'Save Changes', class: 'btn-primary', onclick: `ProductManager.save(${productId})` }
      ];

      Modal.create('Edit Product', content, buttons);
    } catch (error) {
      console.error('Error:', error);
      Toast.error('Failed to load product details');
    }
  },

  async save(productId) {
    const formData = {
      name: document.getElementById('edit-name').value,
      local_name: document.getElementById('edit-local-name').value,
      sku: document.getElementById('edit-sku').value,
      category: document.getElementById('edit-category').value,
      barcode: document.getElementById('edit-barcode').value,
      local_code: document.getElementById('edit-local-code').value,
      brand: document.getElementById('edit-brand').value,
      supplier: document.getElementById('edit-supplier').value,
      description: document.getElementById('edit-description').value
    };

    try {
      const response = await fetch(`/api/products/${productId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (data.success) {
        showSuccessAnimation('📦', () => {
          window.location.reload();
        });
      } else {
        Toast.error(data.error || 'Failed to update product');
      }
    } catch (error) {
      console.error('Error:', error);
      Toast.error('Failed to update product');
    }
  },

  delete(productId) {
    Modal.confirm(
      'Delete Product',
      'Are you sure you want to delete this product? This action cannot be undone.',
      `ProductManager.confirmDelete(${productId})`
    );
  },

  async confirmDelete(productId) {
    try {
      const response = await fetch(`/api/products/${productId}`, {
        method: 'DELETE'
      });

      const data = await response.json();

      if (data.success) {
        showSuccessAnimation('🗑️', () => {
          window.location.reload();
        });
      } else {
        Toast.error(data.error || 'Failed to delete product');
      }
    } catch (error) {
      console.error('Error:', error);
      Toast.error('Failed to delete product');
    }
  }
};

(function () {
  'use strict';

  var header = null;
  var main = null;
  var flash = null;
  var scrollThreshold = 80; // px scrolled before shrinking
  var isShrunk = false;
  var rafScheduled = false;
  var footer = null;
  var footerVisible = false;
  var footerThreshold = 24; // px from bottom to trigger visibility
  var __footerDebounce = null;
  var __docResizeObserver = null;
  var __footerHideTimer = null;
  var footerHideDelay = 220; // ms delay before hiding to prevent flicker
  var footerHideThreshold = 80; // px away from bottom required to hide immediately

  function updatePlaceholder() {
    // Ensure the main content is pushed below fixed header
    if (!header || !main) return;
    var cs = window.getComputedStyle(header);
    var position = cs.getPropertyValue('position');
    // If header is fixed (removed from flow), we must add padding to main.
    if (position === 'fixed') {
      // Prefer getBoundingClientRect for accurate sub-pixel and transformed height
      var rect = header.getBoundingClientRect();
      var h = rect.height || header.offsetHeight || 0;
      // read CSS variable for small extra offset (defaults to 12px for more breathing room)
      var offsetVal = cs.getPropertyValue('--header-offset') || '12px';
      var offset = 12;
      try {
        offset = parseInt(offsetVal.trim(), 10) || 4;
      } catch (e) {
        offset = 4;
      }
      // Safety clamp: do not allow padding larger than 250px (accommodates taller mobile headers)
      var maxSafe = 250;
      var desired = h + (offset || 20); // Default to 20px offset
      if (desired > maxSafe) desired = maxSafe;
      // If there are flash messages, move the flash below the header. Otherwise pad main.
      var hasFlash = flash && flash.children && flash.children.length;
      if (hasFlash) {
        flash.style.marginTop = desired + 'px';
        main.style.paddingTop = '';
      } else {
        if (flash) flash.style.marginTop = '';
        main.style.paddingTop = desired + 'px';
      }
    } else {
      // Header is in-flow (sticky or static) -> clear any JS-added padding/margins
      main.style.paddingTop = '';
      if (flash) flash.style.marginTop = '';
    }
  }

  function onScroll() {
    if (rafScheduled) return;
    rafScheduled = true;
    window.requestAnimationFrame(function () {
      rafScheduled = false;
      var scrollY = window.scrollY || window.pageYOffset;
      var shouldShrink = scrollY > 100; // Increased threshold to match the taller header

      if (shouldShrink && !isShrunk) {
        header.classList.add('shrink');
        isShrunk = true;
      } else if (!shouldShrink && isShrunk) {
        header.classList.remove('shrink');
        isShrunk = false;
      }

      updatePlaceholder();
    });
  }

  // linear interpolation helper
  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function onResize() {
    // Recompute placeholder height on resize
    updatePlaceholder();
  }

  function getBaseDocHeight() {
    var docH = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);
    var paddingOffset = 0;
    if (footerVisible && footer) {
      paddingOffset = Math.ceil(footer.getBoundingClientRect().height);
    }
    return docH - paddingOffset;
  }

  function isAtBottom() {
    var scrollY = window.scrollY || window.pageYOffset;
    var baseDocH = getBaseDocHeight();
    var viewH = window.innerHeight || document.documentElement.clientHeight;
    return (scrollY + viewH) >= (baseDocH - footerThreshold);
  }

  function updateFooterVisibility() {
    if (!footer || !main) return;
    var docH = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);
    var baseDocH = getBaseDocHeight();
    var viewH = window.innerHeight || document.documentElement.clientHeight;

    var shouldShow = false;
    if (baseDocH <= viewH) {
      shouldShow = true; // page shorter than viewport
    } else if (isAtBottom()) {
      shouldShow = true; // scrolled to bottom
    }

    if (shouldShow && !footerVisible) {
      footerVisible = true;
      // set padding before showing so content doesn't get overlapped during transition
      var fh = Math.ceil(footer.getBoundingClientRect().height);
      main.style.paddingBottom = fh + 'px';
      // show footer
      footer.classList.remove('footer-hidden');
      footer.classList.add('footer-visible');
      // cancel pending hide
      clearTimeout(__footerHideTimer);
    } else if (!shouldShow && footerVisible) {
      var scrollY = window.scrollY || window.pageYOffset;
      var distanceFromBottom = baseDocH - (scrollY + viewH);
      // If we're far enough from bottom, hide immediately; otherwise debounce hide
      var doHide = function () {
        footerVisible = false;
        // start hide transition
        footer.classList.remove('footer-visible');
        footer.classList.add('footer-hidden');
        // clear padding after transition completes
        var clearAfter = 850; // match CSS transition (800ms) + buffer
        setTimeout(function () {
          if (!footerVisible) {
            main.style.paddingBottom = '';
          }
        }, clearAfter);
      };

      if (distanceFromBottom > footerHideThreshold) {
        doHide();
      } else {
        clearTimeout(__footerHideTimer);
        __footerHideTimer = setTimeout(function () {
          // re-evaluate before hiding
          var sY = window.scrollY || window.pageYOffset;
          var dfb = getBaseDocHeight() - (sY + viewH);
          if (dfb > footerHideThreshold) {
            doHide();
          }
        }, footerHideDelay);
      }
    }
  }

  function scheduleFooterUpdate(delay) {
    clearTimeout(__footerDebounce);
    __footerDebounce = setTimeout(function () {
      updateFooterVisibility();
    }, delay || 80);
  }

  function init() {
    header = document.getElementById('mainHeader');
    main = document.querySelector('main');
    flash = document.getElementById('flash-container');
    if (!header) return;

    // Apply fixed positioning class
    header.classList.add('is-fixed');

    // Cache numeric shrink variable values (in pixels) for fast interpolation
    function parseCSSVars() {
      var cs = window.getComputedStyle(header);
      var root = window.getComputedStyle(document.documentElement);
      var rem = parseFloat(root.fontSize) || 16;
      var getVal = function (name, fallback) {
        // prefer value computed on header (allows overrides), otherwise fall back to :root
        var raw = cs.getPropertyValue(name) || root.getPropertyValue(name) || fallback || '';
        raw = raw.trim();
        if (!raw) return null;
        if (raw.indexOf('px') > -1) return parseFloat(raw);
        if (raw.indexOf('rem') > -1) return parseFloat(raw) * rem;
        // plain number fallback
        var n = parseFloat(raw);
        return isNaN(n) ? null : n;
      };

      var paddingMax = getVal('--header-padding-max', '20px') || 20;
      var paddingMin = getVal('--header-padding-min', '8px') || 8;
      var logoHMax = getVal('--logo-height-max', '56px') || 56;
      var logoHMin = getVal('--logo-height-min', '36px') || 36;
      var logoFMax = getVal('--logo-font-max', '1.5rem') || (1.5 * rem);
      var logoFMin = getVal('--logo-font-min', '1rem') || (1.0 * rem);

      header._shrinkVars = {
        paddingMax: paddingMax,
        paddingMin: paddingMin,
        logoHMax: logoHMax,
        logoHMin: logoHMin,
        logoFMax: logoFMax,
        logoFMin: logoFMin
      };
      // initialize CSS variables to max
      header.style.setProperty('--header-padding', paddingMax + 'px');
      header.style.setProperty('--logo-height', logoHMax + 'px');
      header.style.setProperty('--logo-font', logoFMax + 'px');
    }

    parseCSSVars();
    // recompute when resizing (root font-size or CSS may change)
    window.addEventListener('resize', function () { parseCSSVars(); }, { passive: true });

    // no footer pinning: footer stays in normal document flow

    // Set initial placeholder height
    updatePlaceholder();

    // Footer setup: find footer and initialize visibility behavior
    footer = document.querySelector('footer');
    if (footer) {
      footer.classList.add('footer-hidden');
      // initial check on next frame (debounced)
      window.requestAnimationFrame(function () { scheduleFooterUpdate(40); });
      window.addEventListener('load', function () { scheduleFooterUpdate(40); });
      // Use debounced updates on scroll to avoid rapid toggles
      window.addEventListener('scroll', function () { scheduleFooterUpdate(40); }, { passive: true });
      window.addEventListener('resize', function () { scheduleFooterUpdate(60); });
      try {
        var fmo2 = new MutationObserver(function () {
          scheduleFooterUpdate(80);
        });
        fmo2.observe(footer, { childList: true, subtree: true, attributes: true });
      } catch (e) {
        // ignore
      }

      // Observe document size changes (scrollbar appearing/disappearing)
      try {
        if (window.ResizeObserver) {
          __docResizeObserver = new ResizeObserver(function () {
            scheduleFooterUpdate(40);
          });
          __docResizeObserver.observe(document.documentElement);
          __docResizeObserver.observe(document.body);
        } else {
          // Fallback: watch for body mutations to detect size changes
          try {
            var bodySizeObserver = new MutationObserver(function () {
              scheduleFooterUpdate(80);
            });
            bodySizeObserver.observe(document.body, { childList: true, subtree: true, attributes: true });
          } catch (e) { }
        }
      } catch (e) {
        // ignore
      }
    }

    // Attach listeners
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onResize);

    // Update when fonts/images load which can change header height
    window.addEventListener('load', updatePlaceholder);

    // Watch for DOM changes inside header (e.g. logo swap, menu expand)
    try {
      var mo = new MutationObserver(function () {
        // small debounce
        clearTimeout(window.__headerResizeTimer);
        window.__headerResizeTimer = setTimeout(updatePlaceholder, 80);
      });
      mo.observe(header, { childList: true, subtree: true, attributes: true });
    } catch (e) {
      // MutationObserver not available -> fallback to periodic checks
      setInterval(updatePlaceholder, 1000);
    }

    // Also watch for alert nodes being added anywhere in the document
    try {
      var bodyObserver = new MutationObserver(function (mutations) {
        var needsUpdate = false;
        for (var i = 0; i < mutations.length; i++) {
          var m = mutations[i];
          if (m.addedNodes && m.addedNodes.length) {
            for (var j = 0; j < m.addedNodes.length; j++) {
              var node = m.addedNodes[j];
              if (node.nodeType === 1) {
                if (node.classList && node.classList.contains('alert')) {
                  needsUpdate = true; break;
                }
                if (node.querySelector && node.querySelector('.alert')) {
                  needsUpdate = true; break;
                }
              }
            }
          }
          if (needsUpdate) break;
        }
        if (needsUpdate) {
          clearTimeout(window.__headerResizeTimer);
          window.__headerResizeTimer = setTimeout(updatePlaceholder, 40);
        }
      });
      bodyObserver.observe(document.body, { childList: true, subtree: true });
    } catch (e) {
      // ignore
    }

    // Also ensure images inside header trigger an update when they finish loading
    var imgs = header.querySelectorAll('img');
    imgs.forEach(function (img) {
      if (!img.complete) {
        img.addEventListener('load', updatePlaceholder);
      }
    });

    // footer not observed when not pinned
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
window.ProductManager = ProductManager;

// =====================
// ACTIVE NAV DETECTION
// =====================
(function () {
  var path = window.location.pathname;
  var links = document.querySelectorAll('.nav-links a[data-path]');
  links.forEach(function (link) {
    var linkPath = link.getAttribute('data-path');
    // Exact match or starts-with for nested routes
    if (path === linkPath || (linkPath !== '/' && path.startsWith(linkPath))) {
      link.classList.add('active');
    }
  });
})();

// =====================
// SUCCESS ANIMATION
// =====================
function playSuccessSound() {
  const sound = document.getElementById('successSound');
  if (sound) {
    sound.currentTime = 0;
    sound.play().catch(e => console.log('Sound play blocked:', e));
  }
}

function playDeleteSound() {
  const sound = document.getElementById('deleteSound');
  if (sound) {
    sound.currentTime = 0;
    sound.play().catch(e => console.log('Sound play blocked:', e));
  }
}

function showSuccessAnimation(emoji, callback) {
  const overlay = document.getElementById('successOverlay');
  const bagContainer = document.getElementById('bagContainer');
  const successEmoji = document.getElementById('successEmoji');
  const arcCircle = document.getElementById('arcCircle');
  const arcCheck = document.getElementById('arcCheck');

  if (!overlay || !bagContainer || !successEmoji || !arcCircle || !arcCheck) {
    playSuccessSound();
    if (callback) callback();
    return;
  }

  // 1. Reset states
  successEmoji.innerText = emoji || '📦';
  arcCircle.classList.remove('active');
  arcCheck.classList.remove('visible');
  bagContainer.style.transform = 'translate(-50vw, -50vh) rotate(-180deg) scale(0.1)';
  bagContainer.style.opacity = '0';
  bagContainer.style.position = 'absolute';
  bagContainer.style.top = '40%';
  bagContainer.style.left = '50%';

  // 2. Show overlay
  overlay.style.display = 'flex';
  setTimeout(() => overlay.style.opacity = '1', 10);

  // 3. Animate bag and emoji in from "the whole page"
  setTimeout(() => {
    bagContainer.style.transition = 'all 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
    bagContainer.style.transform = 'translate(-50%, -50%) rotate(0deg) scale(1)';
    bagContainer.style.opacity = '1';
  }, 100);

  // 4. Activate rotating arc circle
  setTimeout(() => {
    arcCircle.classList.add('active');
    playSuccessSound();
  }, 900);

  // 5. Show checkmark
  setTimeout(() => {
    arcCheck.classList.add('visible');
  }, 1600);

  // 6. Dismiss
  setTimeout(() => {
    overlay.style.opacity = '0';
    setTimeout(() => {
      overlay.style.display = 'none';
      if (callback) callback();
    }, 500);
  }, 3500);
}

// =====================
// IMPORT ANIMATION
// =====================
function showImportAnimation(callback) {
  const overlay = document.getElementById('importOverlay');
  const stage = document.getElementById('itemsStage');
  const arcCircle = document.getElementById('importArcCircle');
  const arcCheck = document.getElementById('importArcCheck');

  if (!overlay || !stage || !arcCircle || !arcCheck) {
    playSuccessSound();
    if (callback) callback();
    return;
  }

  // Reset
  stage.innerHTML = '';
  arcCircle.classList.remove('active');
  arcCheck.classList.remove('visible');

  overlay.style.display = 'flex';
  setTimeout(() => overlay.style.opacity = '1', 10);

  // Create falling products
  const emojis = ['📦', '📋', '🛒', '📦', '🎁', '📦'];
  for (let i = 0; i < 20; i++) {
    setTimeout(() => {
      const item = document.createElement('div');
      item.className = 'falling-item';
      item.innerText = emojis[Math.floor(Math.random() * emojis.length)];
      item.style.left = Math.random() * 100 + 'vw';
      item.style.animationDelay = Math.random() * 0.5 + 's';
      item.style.fontSize = (20 + Math.random() * 20) + 'px';
      stage.appendChild(item);
    }, i * 50);
  }

  // Activate arc and sound
  setTimeout(() => {
    arcCircle.classList.add('active');
    playSuccessSound();
  }, 1000);

  // Show checkmark
  setTimeout(() => {
    arcCheck.classList.add('visible');
  }, 2000);

  // Dismiss
  setTimeout(() => {
    overlay.style.opacity = '0';
    setTimeout(() => {
      overlay.style.display = 'none';
      if (callback) callback();
    }, 500);
  }, 4500);
}

// =====================
// DELETE ANIMATION
// =====================
function showDeleteAnimation(callback) {
  var overlay = document.getElementById('deleteOverlay');
  if (!overlay) {
    playDeleteSound();
    if (callback) callback();
    return;
  }

  overlay.classList.remove('active');
  void overlay.offsetWidth;
  overlay.classList.add('active');
  playDeleteSound();

  setTimeout(function () {
    overlay.classList.remove('active');
    if (callback) callback();
  }, 1500);
}

// =====================
// TOAST NOTIFICATIONS
// =====================
function showToast(message, type) {
  type = type || 'info';
  var container = document.getElementById('toast-container');
  if (!container) return;

  var icons = { success: '✓', error: '✕', info: 'ℹ' };
  var toast = document.createElement('div');
  toast.className = 'toast ' + type;
  toast.innerHTML = '<span style="font-size:1.25rem;font-weight:700;">' + (icons[type] || '•') + '</span>' +
    '<span>' + message + '</span>';
  container.appendChild(toast);

  // Auto-remove after 3.5s
  setTimeout(function () {
    toast.style.animation = 'slideOutRight 0.3s ease forwards';
    setTimeout(function () {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
  }, 3500);
}

// Add slideOutRight keyframe dynamically if not present
(function () {
  if (!document.getElementById('toast-keyframes')) {
    var style = document.createElement('style');
    style.id = 'toast-keyframes';
    style.textContent = '@keyframes slideOutRight { from { transform: translateX(0); opacity: 1; } to { transform: translateX(420px); opacity: 0; } }';
    document.head.appendChild(style);
  }
})();

