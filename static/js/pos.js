/**
 * SMARTSTOCK - Point of Sale (POS) Billing Terminal Engine
 */

class POSTerminal {
  constructor() {
    this.cart = []; // Array of { id, name, sku, price, maxStock, qty, unit }
    
    const taxInput = document.getElementById('taxRateInput');
    this.taxRate = taxInput ? (parseFloat(taxInput.value) || 5.0) : 5.0;
    
    const discountInput = document.getElementById('posDiscountInput');
    this.discount = discountInput ? (parseFloat(discountInput.value) || 0.0) : 0.0;
    
    this.paymentMethod = 'cash';
    this.cashTendered = 0.0;

    // Attach to window globally for inline handlers
    window.pos = this;

    this.initEventListeners();
    this.renderCart();
  }

  initEventListeners() {
    // 1. Search products in POS catalog
    const searchInput = document.getElementById('posSearchInput');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => this.filterCatalog(e.target.value.toLowerCase()));
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.quickAddFirstMatch(e.target.value.trim());
        }
      });
    }

    // 2. Barcode scanner listener
    const barcodeInput = document.getElementById('barcodeScanInput');
    if (barcodeInput) {
      barcodeInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const code = barcodeInput.value.trim();
          if (code) {
            this.handleBarcodeScan(code);
            barcodeInput.value = '';
          }
        }
      });
    }

    // 3. Category filter pills
    const catPills = document.querySelectorAll('.pos-cat-pill');
    catPills.forEach(pill => {
      pill.addEventListener('click', (e) => {
        catPills.forEach(p => p.classList.remove('active', 'btn-primary'));
        catPills.forEach(p => p.classList.add('btn-light'));
        
        pill.classList.remove('btn-light');
        pill.classList.add('active', 'btn-primary');
        
        const catId = pill.getAttribute('data-cat-id');
        this.filterByCategory(catId);
      });
    });

    // 4. Product card clicks via event delegation
    document.addEventListener('click', (e) => {
      const card = e.target.closest('.pos-product-item');
      if (card && document.getElementById('posContainer')?.contains(card)) {
        const id = parseInt(card.getAttribute('data-id') || card.dataset.id);
        const name = card.getAttribute('data-name') || card.dataset.name;
        const sku = card.getAttribute('data-sku') || card.dataset.sku;
        const price = parseFloat(card.getAttribute('data-price') || card.dataset.price);
        const maxStock = parseInt(card.getAttribute('data-stock') || card.dataset.stock);
        const unit = card.getAttribute('data-unit') || card.dataset.unit || 'pcs';
        
        if (id && !isNaN(price)) {
          this.addToCart(id, name, sku, price, maxStock, unit, card);
        }
      }
    });

    // 5. Discount input
    const discountInput = document.getElementById('posDiscountInput');
    if (discountInput) {
      discountInput.addEventListener('input', (e) => {
        this.discount = Math.max(0, parseFloat(e.target.value) || 0);
        this.renderCart();
      });
    }

    // 6. Tax Rate input
    const taxInput = document.getElementById('taxRateInput');
    if (taxInput) {
      taxInput.addEventListener('input', (e) => {
        this.taxRate = Math.max(0, parseFloat(e.target.value) || 0);
        this.renderCart();
      });
    }

    // 7. Payment method radio pills
    const paymentPills = document.querySelectorAll('input[name="payment_method"]');
    paymentPills.forEach(pill => {
      pill.addEventListener('change', (e) => {
        this.paymentMethod = e.target.value;
      });
    });

    // 8. Clear Cart button
    const clearBtn = document.getElementById('clearCartBtn');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => this.clearCart());
    }

    // 9. Checkout button
    const checkoutBtn = document.getElementById('checkoutSubmitBtn');
    if (checkoutBtn) {
      checkoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.processCheckout();
      });
    }
  }

  filterCatalog(term) {
    const cards = document.querySelectorAll('.pos-product-item');
    cards.forEach(card => {
      const name = (card.getAttribute('data-name') || '').toLowerCase();
      const sku = (card.getAttribute('data-sku') || '').toLowerCase();
      const barcode = (card.getAttribute('data-barcode') || '').toLowerCase();
      if (name.includes(term) || sku.includes(term) || barcode.includes(term)) {
        card.closest('.col-xl-4, .col-md-6').style.display = 'block';
      } else {
        card.closest('.col-xl-4, .col-md-6').style.display = 'none';
      }
    });
  }

  filterByCategory(catId) {
    const cards = document.querySelectorAll('.pos-product-item');
    cards.forEach(card => {
      const pCat = card.getAttribute('data-category-id');
      const col = card.closest('.col-xl-4, .col-md-6');
      if (catId === 'all' || pCat === catId) {
        if (col) col.style.display = 'block';
      } else {
        if (col) col.style.display = 'none';
      }
    });
  }

  quickAddFirstMatch(term) {
    const cards = document.querySelectorAll('.pos-product-item');
    for (let card of cards) {
      const col = card.closest('.col-xl-4, .col-md-6');
      if (col && col.style.display !== 'none') {
        const id = parseInt(card.getAttribute('data-id'));
        const name = card.getAttribute('data-name');
        const sku = card.getAttribute('data-sku');
        const price = parseFloat(card.getAttribute('data-price'));
        const maxStock = parseInt(card.getAttribute('data-stock'));
        const unit = card.getAttribute('data-unit') || 'pcs';
        this.addToCart(id, name, sku, price, maxStock, unit, card);
        break;
      }
    }
  }

  handleBarcodeScan(code) {
    const card = document.querySelector(`.pos-product-item[data-sku="${code}"], .pos-product-item[data-barcode="${code}"]`);
    if (card) {
      const id = parseInt(card.getAttribute('data-id'));
      const name = card.getAttribute('data-name');
      const sku = card.getAttribute('data-sku');
      const price = parseFloat(card.getAttribute('data-price'));
      const maxStock = parseInt(card.getAttribute('data-stock'));
      const unit = card.getAttribute('data-unit') || 'pcs';
      this.addToCart(id, name, sku, price, maxStock, unit, card);
    } else {
      this.showToast(`No product found with barcode / SKU: "${code}"`, 'danger');
    }
  }

  playBeep() {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.08);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.08);
    } catch (e) {}
  }

  showToast(message, type = 'success') {
    let toast = document.getElementById('posToast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'posToast';
      toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9999;
        padding: 12px 20px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.9rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        transition: all 0.25s ease;
        display: flex;
        align-items: center;
        gap: 8px;
      `;
      document.body.appendChild(toast);
    }

    if (type === 'success') {
      toast.style.background = '#10b981';
      toast.style.color = '#ffffff';
      toast.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${message}`;
    } else if (type === 'danger') {
      toast.style.background = '#ef4444';
      toast.style.color = '#ffffff';
      toast.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${message}`;
    } else {
      toast.style.background = '#4f46e5';
      toast.style.color = '#ffffff';
      toast.innerHTML = `<i class="fa-solid fa-info-circle"></i> ${message}`;
    }

    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';

    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
    }, 2200);
  }

  addToCart(id, name, sku, price, maxStock, unit, cardEl = null) {
    if (maxStock <= 0) {
      this.showToast(`"${name}" is currently out of stock.`, 'danger');
      return;
    }

    const existing = this.cart.find(item => item.id === id);

    if (existing) {
      if (existing.qty + 1 > maxStock) {
        this.showToast(`Cannot add more. Max available stock is ${maxStock} ${unit}.`, 'danger');
        return;
      }
      existing.qty += 1;
    } else {
      this.cart.push({
        id,
        name,
        sku,
        price,
        maxStock,
        qty: 1,
        unit
      });
    }

    // Play subtle beep sound & show visual cue
    this.playBeep();
    this.showToast(`Added: ${name} (₹${price.toFixed(2)})`);

    if (cardEl) {
      cardEl.style.transform = 'scale(0.97)';
      cardEl.style.borderColor = 'var(--primary)';
      setTimeout(() => {
        cardEl.style.transform = '';
      }, 150);
    }

    this.renderCart();
  }

  updateQuantity(id, delta) {
    const item = this.cart.find(i => i.id === id);
    if (!item) return;

    const newQty = item.qty + delta;
    if (newQty <= 0) {
      this.removeFromCart(id);
    } else if (newQty > item.maxStock) {
      this.showToast(`Available stock limit reached (${item.maxStock} ${item.unit}).`, 'danger');
    } else {
      item.qty = newQty;
      this.playBeep();
      this.renderCart();
    }
  }

  removeFromCart(id) {
    const item = this.cart.find(i => i.id === id);
    this.cart = this.cart.filter(i => i.id !== id);
    if (item) {
      this.showToast(`Removed "${item.name}" from cart`, 'info');
    }
    this.renderCart();
  }

  clearCart() {
    if (this.cart.length > 0 && confirm('Are you sure you want to clear the entire cart?')) {
      this.cart = [];
      this.showToast('Cart cleared', 'info');
      this.renderCart();
    }
  }

  calculateTotals() {
    const subtotal = this.cart.reduce((acc, item) => acc + (item.price * item.qty), 0);
    const taxRate = parseFloat(this.taxRate) || 0;
    const taxAmount = (subtotal * (taxRate / 100));
    const discount = parseFloat(this.discount) || 0;
    const total = Math.max(0, subtotal + taxAmount - discount);
    return {
      subtotal,
      taxAmount,
      total,
      itemCount: this.cart.reduce((acc, item) => acc + item.qty, 0)
    };
  }

  renderCart() {
    const container = document.getElementById('cartItemsContainer');
    const badge = document.getElementById('cartBadgeCount');
    const emptyState = document.getElementById('cartEmptyState');
    const summaryBlock = document.getElementById('cartSummaryBlock');
    const checkoutBtn = document.getElementById('checkoutSubmitBtn');

    if (!container) return;

    const totals = this.calculateTotals();

    if (badge) badge.textContent = totals.itemCount;

    if (this.cart.length === 0) {
      container.innerHTML = '';
      if (emptyState) emptyState.style.display = 'block';
      if (summaryBlock) summaryBlock.style.display = 'none';
      if (checkoutBtn) {
        checkoutBtn.disabled = true;
        document.getElementById('checkoutTotalBtnText').textContent = '₹0.00';
      }
      return;
    }

    if (emptyState) emptyState.style.display = 'none';
    if (summaryBlock) summaryBlock.style.display = 'block';
    if (checkoutBtn) checkoutBtn.disabled = false;

    let html = '';
    this.cart.forEach(item => {
      const lineTotal = (item.price * item.qty).toFixed(2);
      html += `
        <div class="pos-cart-item">
          <div style="flex: 1; padding-right: 0.5rem;">
            <div class="fw-bold text-dark text-truncate" style="max-width: 175px;" title="${item.name}">${item.name}</div>
            <div class="text-muted small">₹${item.price.toFixed(2)} / ${item.unit} &bull; <span class="font-monospace">${item.sku}</span></div>
          </div>
          <div class="d-flex align-items-center gap-1">
            <button type="button" class="btn btn-sm btn-light p-1 px-2 border" onclick="window.pos.updateQuantity(${item.id}, -1)">
              <i class="fa-solid fa-minus" style="font-size: 0.75rem;"></i>
            </button>
            <span class="fw-bold px-1" style="min-width: 26px; text-align: center;">${item.qty}</span>
            <button type="button" class="btn btn-sm btn-light p-1 px-2 border" onclick="window.pos.updateQuantity(${item.id}, 1)">
              <i class="fa-solid fa-plus" style="font-size: 0.75rem;"></i>
            </button>
          </div>
          <div class="text-end ps-2" style="min-width: 75px;">
            <div class="fw-bold text-primary">₹${lineTotal}</div>
            <a href="javascript:void(0)" class="text-danger small" onclick="window.pos.removeFromCart(${item.id})" title="Remove item">
              <i class="fa-solid fa-trash-can"></i>
            </a>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;

    // Update summary text
    const subEl = document.getElementById('posSubtotalText');
    const taxEl = document.getElementById('posTaxText');
    const discEl = document.getElementById('posDiscountText');
    const grandEl = document.getElementById('posGrandTotalText');
    const btnTotEl = document.getElementById('checkoutTotalBtnText');

    if (subEl) subEl.textContent = '₹' + totals.subtotal.toFixed(2);
    if (taxEl) taxEl.textContent = '₹' + totals.taxAmount.toFixed(2);
    if (discEl) discEl.textContent = '- ₹' + this.discount.toFixed(2);
    if (grandEl) grandEl.textContent = '₹' + totals.total.toFixed(2);
    if (btnTotEl) btnTotEl.textContent = '₹' + totals.total.toFixed(2);
  }

  processCheckout() {
    if (this.cart.length === 0) {
      this.showToast('Cart is empty. Please add items before billing.', 'danger');
      return;
    }

    const customerName = (document.getElementById('customerNameInput')?.value || 'Walk-in Customer').trim();
    const customerPhone = (document.getElementById('customerPhoneInput')?.value || '').trim();
    const notes = (document.getElementById('saleNotesInput')?.value || '').trim();
    const checkoutBtn = document.getElementById('checkoutSubmitBtn');

    if (checkoutBtn) {
      checkoutBtn.disabled = true;
      checkoutBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Finalizing Transaction...';
    }

    const payload = {
      customer_name: customerName,
      customer_phone: customerPhone,
      payment_method: this.paymentMethod,
      tax_rate: this.taxRate,
      discount_amount: this.discount,
      notes: notes,
      items: this.cart.map(item => ({
        product_id: item.id,
        quantity: item.qty
      }))
    };

    fetch('/sales/checkout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(res => {
        if (res.success) {
          this.cart = [];
          this.renderCart();
          // Instant redirect to printable invoice
          window.location.href = res.redirect_url;
        } else {
          if (checkoutBtn) {
            checkoutBtn.disabled = false;
            checkoutBtn.innerHTML = `<i class="fa-solid fa-circle-check me-1"></i> Pay & Print Invoice (<span id="checkoutTotalBtnText">₹${this.calculateTotals().total.toFixed(2)}</span>)`;
          }
          alert('Billing Error: ' + res.message);
        }
      })
      .catch(err => {
        if (checkoutBtn) {
          checkoutBtn.disabled = false;
          checkoutBtn.innerHTML = `<i class="fa-solid fa-circle-check me-1"></i> Pay & Print Invoice (<span id="checkoutTotalBtnText">₹${this.calculateTotals().total.toFixed(2)}</span>)`;
        }
        alert('Server network error while billing: ' + err.message);
      });
  }
}

// Robust auto-initialization that never misses DOM ready
function initPOSTerminal() {
  if (document.getElementById('posContainer')) {
    window.pos = new POSTerminal();
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPOSTerminal);
} else {
  initPOSTerminal();
}
