// Sticky & Shrinking Header (vanilla JS)
// Targets: #mainHeader
// Behavior: pins header to top, shrinks after scrollThreshold

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
        Toast.success('Product updated successfully!');
        setTimeout(() => window.location.reload(), 1000);
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
        Toast.success('Product deleted successfully!');
        setTimeout(() => window.location.reload(), 1000);
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
      // Prefer offsetHeight for integer pixel value
      var h = header.offsetHeight || Math.ceil(header.getBoundingClientRect().height) || 0;
      // read CSS variable for small extra offset (defaults to 4px)
      var offsetVal = cs.getPropertyValue('--header-offset') || '4px';
      var offset = 4;
      try {
        offset = parseInt(offsetVal.trim(), 10) || 4;
      } catch (e) {
        offset = 4;
      }
      // Safety clamp: do not allow padding larger than half the viewport or 150px
      var maxSafe = Math.min(150, Math.floor((window.innerHeight || 800) / 2));
      var desired = h + offset;
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
      // progressive shrink: compute progress 0..1 based on threshold
      var progress = 0;
      if (scrollThreshold > 0) progress = Math.min(1, scrollY / scrollThreshold);

      // interpolate CSS variables between max and min (with easing)
      try {
        if (header._shrinkVars) {
          var v = header._shrinkVars;
          // ease out cubic for a smooth start
          var eased = 1 - Math.pow(1 - progress, 3);
          var pad = Math.round(lerp(v.paddingMax, v.paddingMin, eased));
          var logoH = Math.round(lerp(v.logoHMax, v.logoHMin, eased));
          var logoF = lerp(v.logoFMax, v.logoFMin, eased);
          header.style.setProperty('--header-padding', pad + 'px');
          header.style.setProperty('--logo-height', logoH + 'px');
          // logo font uses px units after conversion
          header.style.setProperty('--logo-font', logoF + 'px');
        }
      } catch (e) {
        // ignore any parse errors and fall back to class toggle
      }

      // keep legacy shrink class (useful for CSS fallbacks)
      var shouldShrink = progress > 0.01; // start shrinking almost immediately
      if (shouldShrink && !isShrunk) {
        header.classList.add('shrink');
        isShrunk = true;
      } else if (!shouldShrink && isShrunk) {
        header.classList.remove('shrink');
        isShrunk = false;
      }

      // update placeholder so main padding follows header height changes
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

  function isAtBottom() {
    var scrollY = window.scrollY || window.pageYOffset;
    var docH = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);
    var viewH = window.innerHeight || document.documentElement.clientHeight;
    return (scrollY + viewH) >= (docH - footerThreshold);
  }

  function updateFooterVisibility() {
    if (!footer || !main) return;
    var docH = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);
    var viewH = window.innerHeight || document.documentElement.clientHeight;

    var shouldShow = false;
    if (docH <= viewH) {
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
      var distanceFromBottom = docH - (scrollY + viewH);
      // If we're far enough from bottom, hide immediately; otherwise debounce hide
      var doHide = function () {
        footerVisible = false;
        // start hide transition
        footer.classList.remove('footer-visible');
        footer.classList.add('footer-hidden');
        // clear padding after transition completes
        var clearAfter = 300; // match CSS transition (~260ms) + buffer
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
          var dfb = docH - (sY + viewH);
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
          } catch (e) {}
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
