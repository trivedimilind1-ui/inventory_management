/**
 * SMARTSTOCK - Ultimate Supermarket POS Billing Terminal Engine
 */

class POSTerminal {
  constructor() {
    this.cart = []; // Array of { id, name, sku, price, maxStock, qty, unit }
    
    const taxInput = document.getElementById('taxRateInput');
    this.taxRate = taxInput ? (parseFloat(taxInput.value) || 5.0) : 5.0;
    
    this.discountType = 'fixed'; // 'fixed' or 'percent'
    this.discountVal = 0.0;
    this.discount = 0.0;
    
    this.paymentMethod = 'cash';
    this.cashReceived = 0.0;
    this.activeCatId = 'all';
    this.searchTerm = '';

    // Attach to window globally for inline handlers
    window.pos = this;

    this.initEventListeners();
    this.renderCart();
  }

  initEventListeners() {
    // 1. Search products in POS catalog
    const searchInput = document.getElementById('posSearchInput');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchTerm = e.target.value.trim().toLowerCase();
        this.applyCatalogFilters();
      });
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.quickAddFirstMatch();
        }
      });
    }

    // Clear search button
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    if (clearSearchBtn) {
      clearSearchBtn.addEventListener('click', () => {
        if (searchInput) {
          searchInput.value = '';
          this.searchTerm = '';
          this.applyCatalogFilters();
          searchInput.focus();
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
      pill.addEventListener('click', () => {
        catPills.forEach(p => {
          p.classList.remove('active', 'btn-primary');
          p.classList.add('btn-light');
          const b = p.querySelector('.badge');
          if (b) {
            b.classList.remove('bg-white', 'text-primary');
            b.classList.add('bg-secondary-subtle', 'text-dark');
          }
        });
        
        pill.classList.remove('btn-light');
        pill.classList.add('active', 'btn-primary');
        const activeBadge = pill.querySelector('.badge');
        if (activeBadge) {
          activeBadge.classList.remove('bg-secondary-subtle', 'text-dark');
          activeBadge.classList.add('bg-white', 'text-primary');
        }
        
        this.activeCatId = pill.getAttribute('data-cat-id');
        this.applyCatalogFilters();
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

    // 5. Discount preset buttons
    const discBtns = document.querySelectorAll('.pos-disc-btn');
    discBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        discBtns.forEach(b => b.classList.remove('active', 'btn-primary'));
        discBtns.forEach(b => b.classList.add('btn-outline-secondary'));
        btn.classList.remove('btn-outline-secondary');
        btn.classList.add('active', 'btn-primary');

        const val = btn.getAttribute('data-disc');
        if (val.endsWith('%')) {
          this.discountType = 'percent';
          this.discountVal = parseFloat(val) || 0;
        } else {
          this.discountType = 'fixed';
          this.discountVal = parseFloat(val) || 0;
        }
        this.renderCart();
      });
    });

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
        const cashSec = document.getElementById('cashCalcSection');
        const upiSec = document.getElementById('upiQRSection');

        if (this.paymentMethod === 'cash') {
          if (cashSec) cashSec.style.display = 'block';
          if (upiSec) upiSec.style.display = 'none';
        } else if (this.paymentMethod === 'upi') {
          if (cashSec) cashSec.style.display = 'none';
          if (upiSec) upiSec.style.display = 'block';
        } else {
          if (cashSec) cashSec.style.display = 'none';
          if (upiSec) upiSec.style.display = 'none';
        }
      });
    });

    // 8. Cash calculation & Denomination buttons
    const cashInput = document.getElementById('cashReceivedInput');
    if (cashInput) {
      cashInput.addEventListener('input', (e) => {
        this.cashReceived = parseFloat(e.target.value) || 0;
        this.updateCashChange();
      });
    }

    const denomBtns = document.querySelectorAll('.pos-denom-btn');
    denomBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const val = btn.getAttribute('data-val');
        const totals = this.calculateTotals();
        if (val === 'exact') {
          this.cashReceived = totals.total;
        } else {
          this.cashReceived = parseFloat(val) || 0;
        }
        if (cashInput) cashInput.value = this.cashReceived > 0 ? this.cashReceived.toFixed(2) : '';
        this.updateCashChange();
      });
    });

    // 9. Clear Cart button
    const clearBtn = document.getElementById('clearCartBtn');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => this.clearCart());
    }

    // 10. Checkout button
    const checkoutBtn = document.getElementById('checkoutSubmitBtn');
    if (checkoutBtn) {
      checkoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.processCheckout();
      });
    }

    // 11. Modal Next Sale Button
    const nextSaleBtn = document.getElementById('modalNextSaleBtn');
    if (nextSaleBtn) {
      nextSaleBtn.addEventListener('click', () => {
        const modalEl = document.getElementById('saleSuccessModal');
        if (modalEl) {
          const bsModal = bootstrap.Modal.getInstance(modalEl);
          if (bsModal) bsModal.hide();
        }
        this.resetTerminalForNextCustomer();
      });
    }

    // 12. Global Keyboard Shortcuts (F2: Search, F4: Checkout, Esc: Clear)
    window.addEventListener('keydown', (e) => {
      if (e.key === 'F2') {
        e.preventDefault();
        const inp = document.getElementById('barcodeScanInput') || document.getElementById('posSearchInput');
        if (inp) {
          inp.focus();
          inp.select();
        }
      } else if (e.key === 'F4') {
        e.preventDefault();
        const chk = document.getElementById('checkoutSubmitBtn');
        if (chk && !chk.disabled) {
          this.processCheckout();
        }
      } else if (e.key === 'Escape') {
        const sinp = document.getElementById('posSearchInput');
        if (sinp && document.activeElement === sinp) {
          sinp.value = '';
          this.searchTerm = '';
          this.applyCatalogFilters();
        }
      }
    });
  }

  applyCatalogFilters() {
    const cols = document.querySelectorAll('.pos-product-col');
    let visibleCount = 0;

    cols.forEach(col => {
      const card = col.querySelector('.pos-product-item');
      if (!card) return;

      const pCat = card.getAttribute('data-category-id');
      const name = (card.getAttribute('data-name') || '').toLowerCase();
      const sku = (card.getAttribute('data-sku') || '').toLowerCase();
      const barcode = (card.getAttribute('data-barcode') || '').toLowerCase();

      const matchesCat = (this.activeCatId === 'all' || pCat === this.activeCatId);
      const matchesSearch = (!this.searchTerm || name.includes(this.searchTerm) || sku.includes(this.searchTerm) || barcode.includes(this.searchTerm));

      if (matchesCat && matchesSearch) {
        col.style.display = 'block';
        visibleCount++;
      } else {
        col.style.display = 'none';
      }
    });
  }

  quickAddFirstMatch() {
    const cols = document.querySelectorAll('.pos-product-col');
    for (let col of cols) {
      if (col.style.display !== 'none') {
        const card = col.querySelector('.pos-product-item');
        if (card) {
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
  }

  handleBarcodeScan(code) {
    const cleanCode = code.trim().toLowerCase();
    const cards = document.querySelectorAll('.pos-product-item');
    let matchedCard = null;

    cards.forEach(card => {
      const sku = (card.getAttribute('data-sku') || '').toLowerCase();
      const barcode = (card.getAttribute('data-barcode') || '').toLowerCase();
      if (sku === cleanCode || barcode === cleanCode) {
        matchedCard = card;
      }
    });

    if (matchedCard) {
      const id = parseInt(matchedCard.getAttribute('data-id'));
      const name = matchedCard.getAttribute('data-name');
      const sku = matchedCard.getAttribute('data-sku');
      const price = parseFloat(matchedCard.getAttribute('data-price'));
      const maxStock = parseInt(matchedCard.getAttribute('data-stock'));
      const unit = matchedCard.getAttribute('data-unit') || 'pcs';
      this.addToCart(id, name, sku, price, maxStock, unit, matchedCard);
    } else {
      this.showToast(`No product found with Barcode/SKU: "${code}"`, 'danger');
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
        this.showToast(`Cannot add more. Max stock is ${maxStock} ${unit}.`, 'danger');
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

    this.playBeep();
    this.showToast(`Added: ${name} (₹${price.toFixed(2)})`);

    if (cardEl) {
      cardEl.style.transform = 'scale(0.97)';
      setTimeout(() => {
        cardEl.style.transform = '';
      }, 150);
    }

    this.renderCart();
  }

  setQuantity(id, val) {
    const item = this.cart.find(i => i.id === id);
    if (!item) return;

    let newQty = parseInt(val);
    if (isNaN(newQty) || newQty <= 0) {
      this.removeFromCart(id);
      return;
    }

    if (newQty > item.maxStock) {
      newQty = item.maxStock;
      this.showToast(`Stock limit reached (${item.maxStock} ${item.unit}).`, 'danger');
    }

    item.qty = newQty;
    this.renderCart();
  }

  updateQuantity(id, delta) {
    const item = this.cart.find(i => i.id === id);
    if (!item) return;

    const newQty = item.qty + delta;
    if (newQty <= 0) {
      this.removeFromCart(id);
    } else if (newQty > item.maxStock) {
      this.showToast(`Stock limit reached (${item.maxStock} ${item.unit}).`, 'danger');
    } else {
      item.qty = newQty;
      this.playBeep();
      this.renderCart();
    }
  }

  quickAddQty(id, extra) {
    this.updateQuantity(id, extra);
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
    if (this.cart.length > 0) {
      this.cart = [];
      this.showToast('Cart cleared', 'info');
      this.renderCart();
    }
  }

  calculateTotals() {
    const subtotal = this.cart.reduce((acc, item) => acc + (item.price * item.qty), 0);
    
    // Calculate discount
    if (this.discountType === 'percent') {
      this.discount = (subtotal * (this.discountVal / 100));
    } else {
      this.discount = this.discountVal;
    }
    this.discount = Math.min(subtotal, Math.max(0, this.discount));

    const taxableAmount = Math.max(0, subtotal - this.discount);
    const taxRate = parseFloat(this.taxRate) || 0;
    const taxAmount = (taxableAmount * (taxRate / 100));
    const total = Math.max(0, taxableAmount + taxAmount);

    return {
      subtotal,
      discount: this.discount,
      taxAmount,
      total,
      itemCount: this.cart.reduce((acc, item) => acc + item.qty, 0)
    };
  }

  updateCashChange() {
    const totals = this.calculateTotals();
    const change = Math.max(0, this.cashReceived - totals.total);
    const changeBox = document.getElementById('changeDueBox');
    const changeText = document.getElementById('changeDueText');

    if (changeText) {
      changeText.textContent = '₹' + change.toFixed(2);
    }
    if (changeBox) {
      if (this.cashReceived >= totals.total && totals.total > 0) {
        changeBox.className = 'd-flex justify-content-between align-items-center px-2 py-1 rounded bg-success text-white fw-bold small';
      } else {
        changeBox.className = 'd-flex justify-content-between align-items-center px-2 py-1 rounded bg-success-subtle text-success fw-bold small';
      }
    }
  }

  updateProductCardBadges() {
    // Sync active in-cart quantity badges on product catalog cards
    const badges = document.querySelectorAll('.pos-card-cart-pill');
    badges.forEach(b => b.style.display = 'none');

    this.cart.forEach(item => {
      const badge = document.getElementById(`cartBadgeProd_${item.id}`);
      if (badge) {
        const qtySpan = badge.querySelector('.badge-qty');
        if (qtySpan) qtySpan.textContent = item.qty;
        badge.style.display = 'block';
      }
    });
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
    this.updateProductCardBadges();

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
        <div class="pos-cart-item py-2 border-bottom">
          <div class="d-flex justify-content-between align-items-start mb-1">
            <div style="flex: 1; padding-right: 0.5rem;">
              <div class="fw-bold text-dark text-truncate" style="max-width: 200px;" title="${item.name}">${item.name}</div>
              <div class="text-muted small" style="font-size: 0.75rem;">₹${item.price.toFixed(2)} / ${item.unit} &bull; <span class="font-monospace">${item.sku}</span></div>
            </div>
            <div class="text-end ps-2">
              <span class="fw-bold text-primary fs-6">₹${lineTotal}</span>
              <button type="button" class="btn btn-sm text-danger p-0 ms-2" onclick="window.pos.removeFromCart(${item.id})" title="Remove">
                <i class="fa-solid fa-trash-can"></i>
              </button>
            </div>
          </div>

          <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center gap-1">
              <button type="button" class="btn btn-sm btn-light border px-2 py-0" onclick="window.pos.updateQuantity(${item.id}, -1)">
                <i class="fa-solid fa-minus" style="font-size: 0.7rem;"></i>
              </button>
              <input type="number" min="1" max="${item.maxStock}" value="${item.qty}" 
                     class="form-control form-control-sm text-center fw-bold px-1" 
                     style="width: 48px; height: 28px;"
                     onchange="window.pos.setQuantity(${item.id}, this.value)">
              <button type="button" class="btn btn-sm btn-light border px-2 py-0" onclick="window.pos.updateQuantity(${item.id}, 1)">
                <i class="fa-solid fa-plus" style="font-size: 0.7rem;"></i>
              </button>
            </div>
            
            <div class="d-flex gap-1">
              <button type="button" class="btn btn-xs btn-outline-secondary py-0 px-1" onclick="window.pos.quickAddQty(${item.id}, 5)">+5</button>
              <button type="button" class="btn btn-xs btn-outline-secondary py-0 px-1" onclick="window.pos.quickAddQty(${item.id}, 10)">+10</button>
            </div>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;

    // Update summary texts
    const subEl = document.getElementById('posSubtotalText');
    const taxEl = document.getElementById('posTaxText');
    const discEl = document.getElementById('posDiscountText');
    const grandEl = document.getElementById('posGrandTotalText');
    const btnTotEl = document.getElementById('checkoutTotalBtnText');
    const upiTotEl = document.getElementById('upiQRTotalText');

    if (subEl) subEl.textContent = '₹' + totals.subtotal.toFixed(2);
    if (taxEl) taxEl.textContent = '₹' + totals.taxAmount.toFixed(2);
    if (discEl) discEl.textContent = '- ₹' + totals.discount.toFixed(2);
    if (grandEl) grandEl.textContent = '₹' + totals.total.toFixed(2);
    if (btnTotEl) btnTotEl.textContent = '₹' + totals.total.toFixed(2);
    if (upiTotEl) upiTotEl.textContent = '₹' + totals.total.toFixed(2);

    this.updateCashChange();
  }

  processCheckout() {
    if (this.cart.length === 0) {
      this.showToast('Cart is empty. Please add items before checkout.', 'danger');
      return;
    }

    const totals = this.calculateTotals();
    const customerName = (document.getElementById('customerNameInput')?.value || 'Walk-in Customer').trim();
    const customerPhone = (document.getElementById('customerPhoneInput')?.value || '').trim();
    const checkoutBtn = document.getElementById('checkoutSubmitBtn');

    if (checkoutBtn) {
      checkoutBtn.disabled = true;
      checkoutBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Generating Invoice...';
    }

    const payload = {
      customer_name: customerName,
      customer_phone: customerPhone,
      payment_method: this.paymentMethod,
      tax_rate: this.taxRate,
      discount_amount: totals.discount,
      notes: `POS Terminal Sale - Mode: ${this.paymentMethod.toUpperCase()}`,
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
        if (checkoutBtn) {
          checkoutBtn.disabled = false;
          checkoutBtn.innerHTML = `<i class="fa-solid fa-circle-check me-2"></i> Pay & Generate Bill (<span id="checkoutTotalBtnText">₹${totals.total.toFixed(2)}</span>)`;
        }

        if (res.success) {
          // Play success chime
          this.playBeep();

          // Calculate change to show
          const changeGiven = Math.max(0, this.cashReceived - totals.total);

          // Populate and show the Success Modal!
          document.getElementById('modalInvoiceNo').textContent = res.invoice_no;
          document.getElementById('modalCustomerName').textContent = customerName;
          document.getElementById('modalTotalAmount').textContent = '₹' + totals.total.toFixed(2);
          document.getElementById('modalPaymentMethod').textContent = this.paymentMethod.toUpperCase();
          
          const changeRow = document.getElementById('modalChangeRow');
          if (changeRow) {
            if (this.paymentMethod === 'cash' && changeGiven > 0) {
              changeRow.style.display = 'flex';
              document.getElementById('modalChangeAmount').textContent = '₹' + changeGiven.toFixed(2);
            } else {
              changeRow.style.display = 'none';
            }
          }

          const printBtn = document.getElementById('modalPrintInvoiceBtn');
          if (printBtn) {
            printBtn.href = res.redirect_url;
          }

          // Show modal
          const modalEl = document.getElementById('saleSuccessModal');
          if (modalEl && window.bootstrap) {
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
          } else {
            // Fallback direct redirect
            window.location.href = res.redirect_url;
          }

          // Clear cart
          this.cart = [];
          this.renderCart();
        } else {
          this.showToast('Billing Error: ' + res.message, 'danger');
          alert('Billing Error: ' + res.message);
        }
      })
      .catch(err => {
        if (checkoutBtn) {
          checkoutBtn.disabled = false;
          checkoutBtn.innerHTML = `<i class="fa-solid fa-circle-check me-2"></i> Pay & Generate Bill (<span id="checkoutTotalBtnText">₹${totals.total.toFixed(2)}</span>)`;
        }
        this.showToast('Network error while processing sale.', 'danger');
        alert('Server network error while billing: ' + err.message);
      });
  }

  resetTerminalForNextCustomer() {
    this.cart = [];
    this.cashReceived = 0;
    this.discountVal = 0;
    this.discountType = 'fixed';
    
    const cashInput = document.getElementById('cashReceivedInput');
    if (cashInput) cashInput.value = '';

    const custName = document.getElementById('customerNameInput');
    if (custName) custName.value = 'Walk-in Customer';

    const custPhone = document.getElementById('customerPhoneInput');
    if (custPhone) custPhone.value = '';

    const discBtns = document.querySelectorAll('.pos-disc-btn');
    discBtns.forEach(b => {
      b.classList.remove('active', 'btn-primary');
      b.classList.add('btn-outline-secondary');
      if (b.getAttribute('data-disc') === '0') {
        b.classList.add('active', 'btn-primary');
        b.classList.remove('btn-outline-secondary');
      }
    });

    this.renderCart();

    const searchInput = document.getElementById('barcodeScanInput') || document.getElementById('posSearchInput');
    if (searchInput) {
      searchInput.focus();
    }
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
