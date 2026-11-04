/**
 * SMARTSTOCK - Point of Sale (POS) Billing Terminal
 */

class POSTerminal {
  constructor() {
    this.cart = []; // Array of { id, name, sku, price, max_stock, qty, unit }
    this.taxRate = parseFloat(document.getElementById('taxRateInput')?.value || 5.0);
    this.discount = 0.0;
    this.paymentMethod = 'cash';

    this.initEventListeners();
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

    // 2. Barcode scanner / fast-input listener
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
        catPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        const catId = pill.getAttribute('data-cat-id');
        this.filterByCategory(catId);
      });
    });

    // 4. Product card clicks
    const productCards = document.querySelectorAll('.pos-product-item');
    productCards.forEach(card => {
      card.addEventListener('click', () => {
        const id = parseInt(card.getAttribute('data-id'));
        const name = card.getAttribute('data-name');
        const sku = card.getAttribute('data-sku');
        const price = parseFloat(card.getAttribute('data-price'));
        const maxStock = parseInt(card.getAttribute('data-stock'));
        const unit = card.getAttribute('data-unit') || 'pcs';
        this.addToCart(id, name, sku, price, maxStock, unit);
      });
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
      clearBtn.addEventListener('click', () => {
        if (this.cart.length > 0 && confirm('Are you sure you want to clear the cart?')) {
          this.cart = [];
          this.renderCart();
        }
      });
    }

    // 9. Checkout form submission
    const checkoutBtn = document.getElementById('checkoutSubmitBtn');
    if (checkoutBtn) {
      checkoutBtn.addEventListener('click', () => this.processCheckout());
    }
  }

  filterCatalog(term) {
    const cards = document.querySelectorAll('.pos-product-item');
    cards.forEach(card => {
      const name = card.getAttribute('data-name').toLowerCase();
      const sku = card.getAttribute('data-sku').toLowerCase();
      const barcode = (card.getAttribute('data-barcode') || '').toLowerCase();
      if (name.includes(term) || sku.includes(term) || barcode.includes(term)) {
        card.parentElement.style.display = 'block';
      } else {
        card.parentElement.style.display = 'none';
      }
    });
  }

  filterByCategory(catId) {
    const cards = document.querySelectorAll('.pos-product-item');
    cards.forEach(card => {
      const pCat = card.getAttribute('data-category-id');
      if (catId === 'all' || pCat === catId) {
        card.parentElement.style.display = 'block';
      } else {
        card.parentElement.style.display = 'none';
      }
    });
  }

  quickAddFirstMatch(term) {
    const cards = document.querySelectorAll('.pos-product-item');
    for (let card of cards) {
      if (card.parentElement.style.display !== 'none') {
        const id = parseInt(card.getAttribute('data-id'));
        const name = card.getAttribute('data-name');
        const sku = card.getAttribute('data-sku');
        const price = parseFloat(card.getAttribute('data-price'));
        const maxStock = parseInt(card.getAttribute('data-stock'));
        const unit = card.getAttribute('data-unit') || 'pcs';
        this.addToCart(id, name, sku, price, maxStock, unit);
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
      this.addToCart(id, name, sku, price, maxStock, unit);
    } else {
      alert(`No product found with barcode / SKU: "${code}"`);
    }
  }

  addToCart(id, name, sku, price, maxStock, unit) {
    const existing = this.cart.find(item => item.id === id);

    if (existing) {
      if (existing.qty + 1 > maxStock) {
        alert(`Cannot add more. Available stock for "${name}" is ${maxStock} ${unit}.`);
        return;
      }
      existing.qty += 1;
    } else {
      if (maxStock <= 0) {
        alert(`Product "${name}" is currently out of stock.`);
        return;
      }
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

    this.renderCart();
  }

  updateQuantity(id, delta) {
    const item = this.cart.find(i => i.id === id);
    if (!item) return;

    const newQty = item.qty + delta;
    if (newQty <= 0) {
      this.removeFromCart(id);
    } else if (newQty > item.maxStock) {
      alert(`Cannot add more. Available stock for "${item.name}" is ${item.maxStock} ${item.unit}.`);
    } else {
      item.qty = newQty;
      this.renderCart();
    }
  }

  removeFromCart(id) {
    this.cart = this.cart.filter(i => i.id !== id);
    this.renderCart();
  }

  calculateTotals() {
    const subtotal = this.cart.reduce((acc, item) => acc + (item.price * item.qty), 0);
    const taxAmount = (subtotal * (this.taxRate / 100));
    const total = Math.max(0, subtotal + taxAmount - this.discount);
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
      if (checkoutBtn) checkoutBtn.disabled = true;
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
            <div class="fw-bold text-dark text-truncate" style="max-width: 170px;" title="${item.name}">${item.name}</div>
            <div class="text-muted small">₹${item.price.toFixed(2)} / ${item.unit} • SKU: ${item.sku}</div>
          </div>
          <div class="d-flex align-items-center gap-1">
            <button class="btn btn-sm btn-light p-1 px-2 border" onclick="pos.updateQuantity(${item.id}, -1)">
              <i class="bi bi-dash"></i>
            </button>
            <span class="fw-bold px-1" style="min-width: 24px; text-align: center;">${item.qty}</span>
            <button class="btn btn-sm btn-light p-1 px-2 border" onclick="pos.updateQuantity(${item.id}, 1)">
              <i class="bi bi-plus"></i>
            </button>
          </div>
          <div class="text-end ps-2" style="min-width: 75px;">
            <div class="fw-bold text-primary">₹${lineTotal}</div>
            <a href="javascript:void(0)" class="text-danger small" onclick="pos.removeFromCart(${item.id})">
              <i class="bi bi-trash"></i>
            </a>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;

    // Update summary text
    document.getElementById('posSubtotalText').textContent = '₹' + totals.subtotal.toFixed(2);
    document.getElementById('posTaxText').textContent = '₹' + totals.taxAmount.toFixed(2);
    document.getElementById('posDiscountText').textContent = '- ₹' + this.discount.toFixed(2);
    document.getElementById('posGrandTotalText').textContent = '₹' + totals.total.toFixed(2);
    document.getElementById('checkoutTotalBtnText').textContent = '₹' + totals.total.toFixed(2);
  }

  processCheckout() {
    if (this.cart.length === 0) {
      alert('Cart is empty.');
      return;
    }

    const customerName = document.getElementById('customerNameInput')?.value || 'Walk-in Customer';
    const customerPhone = document.getElementById('customerPhoneInput')?.value || '';
    const notes = document.getElementById('saleNotesInput')?.value || '';
    const checkoutBtn = document.getElementById('checkoutSubmitBtn');

    checkoutBtn.disabled = true;
    checkoutBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Processing...';

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
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(res => {
        checkoutBtn.disabled = false;
        checkoutBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i> Complete & Print Invoice';

        if (res.success) {
          // Success! Clear cart and redirect to invoice
          this.cart = [];
          this.renderCart();
          window.location.href = res.redirect_url;
        } else {
          alert('Checkout Failed: ' + res.message);
        }
      })
      .catch(err => {
        checkoutBtn.disabled = false;
        checkoutBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i> Complete & Print Invoice';
        alert('Server error processing transaction: ' + err.message);
      });
  }
}

let pos;
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('posContainer')) {
    pos = new POSTerminal();
  }
});
