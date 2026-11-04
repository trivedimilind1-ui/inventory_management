import os
import random
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal

from models import (
    db, User, Category, Supplier, Product, Sale, SaleItem, 
    StockMovement, ActivityLog
)

def seed_database(app):
    with app.app_context():
        # Check if already seeded with products
        if Product.query.count() >= 30:
            print("Database already contains >= 30 products. Skipping duplicate seed.")
            return

        print("Seeding database with realistic supermarket data...")

        # 1. Users
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@smartstock.in',
                full_name='Vikram Sharma (Store Manager)',
                role='admin',
                phone='+91 98111 22334',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)

        staff = User.query.filter_by(username='staff').first()
        if not staff:
            staff = User(
                username='staff',
                email='staff@smartstock.in',
                full_name='Pooja Patel (Cashier)',
                role='staff',
                phone='+91 98222 33445',
                is_active=True
            )
            staff.set_password('staff123')
            db.session.add(staff)

        db.session.commit()

        # 2. Categories (10 Categories)
        categories_data = [
            ("Dairy Products", "Milk, butter, cheese, paneer, curd, and fresh dairy items", "bi-egg-fried"),
            ("Beverages", "Soft drinks, fruit juices, packaged water, tea, and coffee", "bi-cup-straw"),
            ("Snacks & Munchies", "Biscuits, chips, namkeen, instant noodles, and chocolates", "bi-basket"),
            ("Grocery & Staples", "Atta, rice, pulses, edible oils, spices, and grains", "bi-bag-check"),
            ("Personal Care", "Soaps, shampoos, toothpastes, skincare, and grooming", "bi-heart-pulse"),
            ("Household & Cleaning", "Detergents, dishwash, surface cleaners, and repellents", "bi-droplet"),
            ("Bakery & Bread", "Fresh bread, buns, cakes, cookies, and bakery essentials", "bi-shop"),
            ("Fruits & Vegetables", "Fresh seasonal fruits, vegetables, and farm produce", "bi-apple"),
            ("Frozen Foods", "Frozen peas, fries, frozen snacks, and ice creams", "bi-snow"),
            ("Stationery & Office", "Notebooks, pens, adhesives, and office supplies", "bi-pen")
        ]

        cat_map = {}
        for name, desc, icon in categories_data:
            cat = Category.query.filter_by(name=name).first()
            if not cat:
                cat = Category(name=name, description=desc, icon=icon, is_active=True)
                db.session.add(cat)
                db.session.flush()
            cat_map[name] = cat.id

        # 3. Suppliers (5 Major Supermarket Suppliers)
        suppliers_data = [
            ("Ramesh Patel", "Gujarat Co-op Milk Mktg Fed (Amul)", "+91 98791 00001", "sales@amul.coop", "Amul Dairy Road, Anand, Gujarat", "24AAAAG1234A1Z1"),
            ("Sunil Aggarwal", "Tata Consumer Products Ltd", "+91 98102 33333", "orders@tataconsumer.com", "1, Bishop Lefroy Road, Kolkata, WB", "19AAACT0001B1Z2"),
            ("Anand Mahindra", "ITC Foods Distribution", "+91 98300 44444", "distribution@itcportal.com", "Virginia House, 37 J.L. Nehru Road, Kolkata", "19AAACI1234C1Z3"),
            ("Meera Nair", "Hindustan Unilever Logistics", "+91 98210 55555", "support@hul.com", "B.D. Sawant Marg, Chakala, Andheri, Mumbai", "27AAACH1234D1Z4"),
            ("Devendra Singh", "Nestle India Supply Chain", "+91 98111 66666", "consumer@in.nestle.com", "100/101 World Trade Centre, Barakhamba, New Delhi", "07AAACN1234E1Z5")
        ]

        sup_map = {}
        for contact, comp, phone, email, addr, gstin in suppliers_data:
            sup = Supplier.query.filter_by(company_name=comp).first()
            if not sup:
                sup = Supplier(
                    name=contact,
                    company_name=comp,
                    phone=phone,
                    email=email,
                    address=addr,
                    gst_number=gstin,
                    is_active=True
                )
                db.session.add(sup)
                db.session.flush()
            sup_map[comp] = sup.id

        db.session.commit()

        # 4. Realistic Products (35 Products)
        # Columns: name, sku, category_name, supplier_comp, brand, purchase_price, selling_price, qty, min_stock, unit, expiry_days, desc
        products_data = [
            # Dairy
            ("Amul Taaza Homogenised Toned Milk 1L", "DAI-AMUL-001", "Dairy Products", "Gujarat Co-op Milk Mktg Fed (Amul)", "Amul", 62.00, 74.00, 45, 15, "ltr", 90, "Fresh toned milk, long shelf life tetra pack"),
            ("Amul Butter Pasteurised 500g", "DAI-AMUL-002", "Dairy Products", "Gujarat Co-op Milk Mktg Fed (Amul)", "Amul", 235.00, 275.00, 28, 10, "pack", 180, "Pure rich salted pasteurised butter"),
            ("Amul Malai Paneer 200g", "DAI-AMUL-003", "Dairy Products", "Gujarat Co-op Milk Mktg Fed (Amul)", "Amul", 82.00, 95.00, 18, 10, "pack", 45, "Soft, creamy fresh malai paneer cube"),
            ("Mother Dairy Classic Curd 400g", "DAI-MD-004", "Dairy Products", "Gujarat Co-op Milk Mktg Fed (Amul)", "Mother Dairy", 30.00, 35.00, 8, 12, "pack", 15, "Thick and natural classic dahi - Low stock alert!"),
            ("Britannia Cheese Slices 200g", "DAI-BRIT-005", "Dairy Products", "Gujarat Co-op Milk Mktg Fed (Amul)", "Britannia", 125.00, 150.00, 0, 8, "pack", 120, "Processed cheddar cheese slices (10 slices) - Out of stock!"),
            
            # Beverages
            ("Coca-Cola Original Taste 750ml", "BEV-COKE-001", "Beverages", "ITC Foods Distribution", "Coca-Cola", 36.00, 45.00, 60, 20, "bottle", 180, "Refreshing sparkling carbonated soft drink"),
            ("Real Fruit Power Mixed Fruit 1L", "BEV-REAL-002", "Beverages", "ITC Foods Distribution", "Dabur", 100.00, 130.00, 35, 15, "ltr", 240, "No added preservative mixed fruit juice"),
            ("Tata Tea Gold 500g", "BEV-TATA-003", "Beverages", "Tata Consumer Products Ltd", "Tata Tea", 270.00, 330.00, 40, 15, "pack", 365, "Rich aroma tea with gently rolled long leaves"),
            ("Nescafe Classic Instant Coffee 100g", "BEV-NES-004", "Beverages", "Nestle India Supply Chain", "Nescafe", 310.00, 385.00, 22, 10, "jar", 540, "100% pure instant coffee powder in glass jar"),
            ("Bisleri Packaged Drinking Water 1L", "BEV-BIS-005", "Beverages", "ITC Foods Distribution", "Bisleri", 14.00, 20.00, 120, 30, "bottle", 180, "Purified mineral water with added minerals"),

            # Snacks & Munchies
            ("Maggi 2-Minute Masala Noodles 280g", "SNK-MAG-001", "Snacks & Munchies", "Nestle India Supply Chain", "Maggi", 48.00, 60.00, 75, 25, "pack", 270, "Favourite masala instant noodles 4-pack"),
            ("Parle-G Original Gluco Biscuits 800g", "SNK-PAR-002", "Snacks & Munchies", "ITC Foods Distribution", "Parle", 68.00, 85.00, 50, 20, "pack", 180, "India's highest selling glucose biscuit family pack"),
            ("Lay's India's Magic Masala Chips 50g", "SNK-LAY-003", "Snacks & Munchies", "ITC Foods Distribution", "Lay's", 16.00, 20.00, 90, 25, "pack", 120, "Crispy potato chips seasoned with authentic spices"),
            ("Haldiram's Bhujia Sev 400g", "SNK-HAL-004", "Snacks & Munchies", "ITC Foods Distribution", "Haldiram's", 95.00, 120.00, 34, 15, "pack", 180, "Crispy fried moth bean flour spicy noodles"),
            ("Cadbury Dairy Milk Silk 150g", "SNK-CAD-005", "Snacks & Munchies", "Nestle India Supply Chain", "Cadbury", 145.00, 180.00, 42, 15, "pack", 240, "Smooth, velvety milk chocolate bar"),

            # Grocery & Staples
            ("Aashirvaad Shudh Chakki Atta 5kg", "GRO-AASH-001", "Grocery & Staples", "ITC Foods Distribution", "Aashirvaad", 230.00, 280.00, 40, 15, "pack", 180, "100% whole wheat chakki ground flour"),
            ("Tata Salt Vacuum Evaporated 1kg", "GRO-TATA-002", "Grocery & Staples", "Tata Consumer Products Ltd", "Tata Salt", 22.00, 28.00, 110, 30, "pack", 720, "Iodised salt for healthy family nutrition"),
            ("Fortune Sunlite Refined Sunflower Oil 1L", "GRO-FORT-003", "Grocery & Staples", "ITC Foods Distribution", "Fortune", 125.00, 155.00, 55, 20, "ltr", 270, "Light and healthy cooking oil enriched with vitamins"),
            ("India Gate Basmati Rice Feast Rozzana 5kg", "GRO-ING-004", "Grocery & Staples", "Tata Consumer Products Ltd", "India Gate", 380.00, 460.00, 25, 10, "pack", 540, "Aromatic long grain basmati rice for daily meals"),
            ("Tata Sampann Unpolished Toor Dal 1kg", "GRO-TATA-005", "Grocery & Staples", "Tata Consumer Products Ltd", "Tata Sampann", 145.00, 175.00, 32, 15, "kg", 365, "Naturally nutritious unpolished arhar dal"),

            # Personal Care
            ("Dettol Original Bathing Soap (3x125g)", "PC-DET-001", "Personal Care", "Hindustan Unilever Logistics", "Dettol", 130.00, 165.00, 38, 15, "pack", 720, "Antibacterial germ protection body soap"),
            ("Dove Intense Repair Shampoo 340ml", "PC-DOV-002", "Personal Care", "Hindustan Unilever Logistics", "Dove", 260.00, 335.00, 24, 10, "bottle", 720, "Deep nourishment shampoo for damaged hair"),
            ("Colgate Strong Teeth Dental Paste 300g", "PC-COL-003", "Personal Care", "Hindustan Unilever Logistics", "Colgate", 115.00, 145.00, 45, 15, "pack", 720, "Fluoride toothpaste for amino शक्ति and calcium"),
            ("Nivea Men Dark Spot Reduction Creme 75ml", "PC-NIV-004", "Personal Care", "Hindustan Unilever Logistics", "Nivea", 155.00, 199.00, 6, 10, "pack", 720, "Non-greasy face moisturiser - Low stock alert!"),

            # Household & Cleaning
            ("Surf Excel Easy Wash Detergent Powder 1kg", "HOU-SUR-001", "Household & Cleaning", "Hindustan Unilever Logistics", "Surf Excel", 120.00, 145.00, 50, 15, "kg", 720, "Tough stain removal powder with superior foam"),
            ("Vim Lemon Dishwash Gel Bottle 750ml", "HOU-VIM-002", "Household & Cleaning", "Hindustan Unilever Logistics", "Vim", 135.00, 168.00, 30, 12, "bottle", 720, "Concentrated dishwashing gel with natural lemons"),
            ("Harpic Power Plus Disinfectant Toilet Cleaner 1L", "HOU-HAR-003", "Household & Cleaning", "Hindustan Unilever Logistics", "Harpic", 160.00, 205.00, 35, 15, "bottle", 720, "10x better stain removal & 99.9% germ kill"),
            ("Good Knight Gold Flash Liquid Mosquito Refill", "HOU-GK-004", "Household & Cleaning", "ITC Foods Distribution", "Good Knight", 70.00, 89.00, 48, 15, "pack", 720, "Vapouriser refill for all-night mosquito protection"),

            # Bakery & Bread
            ("Britannia 100% Whole Wheat Bread 400g", "BAK-BRIT-001", "Bakery & Bread", "Gujarat Co-op Milk Mktg Fed (Amul)", "Britannia", 40.00, 50.00, 15, 10, "pack", 5, "Fresh sliced brown bread with zero trans fat"),
            ("English Oven Burger Buns (2 Pcs)", "BAK-ENG-002", "Bakery & Bread", "Gujarat Co-op Milk Mktg Fed (Amul)", "English Oven", 24.00, 32.00, 12, 10, "pack", 5, "Soft sesame seed topped classic burger buns"),

            # Fruits & Vegetables
            ("Fresh Farm Onions (Pyaz) 1kg", "FV-ONI-001", "Fruits & Vegetables", "Tata Consumer Products Ltd", "Farm Fresh", 28.00, 38.00, 65, 20, "kg", 14, "Dry graded red onions for daily cooking"),
            ("Fresh Potatoes (Aloo) 1kg", "FV-POT-002", "Fruits & Vegetables", "Tata Consumer Products Ltd", "Farm Fresh", 22.00, 30.00, 80, 25, "kg", 20, "Graded premium fresh local crop potatoes"),
            ("Shimla Premium Royal Delicious Apples 1kg", "FV-APP-003", "Fruits & Vegetables", "Tata Consumer Products Ltd", "Himachal Orchard", 140.00, 185.00, 25, 10, "kg", 10, "Sweet and crunchy handpicked red hill apples"),

            # Frozen Foods
            ("Safal Select Frozen Green Peas 1kg", "FRZ-SAF-001", "Frozen Foods", "Gujarat Co-op Milk Mktg Fed (Amul)", "Safal", 110.00, 140.00, 20, 10, "pack", 365, "Tender and naturally sweet frozen green peas"),
            ("McCain French Fries Crispy 420g", "FRZ-MCC-002", "Frozen Foods", "Nestle India Supply Chain", "McCain", 95.00, 125.00, 22, 10, "pack", 365, "Crispy golden ready-to-fry potato french fries"),

            # Stationery & Office
            ("Classmate Pulse Spiral Notebook 300 Pgs", "STN-CLS-001", "Stationery & Office", "ITC Foods Distribution", "Classmate", 125.00, 160.00, 30, 10, "pcs", None, "Single line ruled notebook with premium paper")
        ]

        created_products = []
        today = date.today()

        for name, sku, cat_name, sup_comp, brand, pp, sp, qty, min_stk, unit, exp_days, desc in products_data:
            prod = Product.query.filter_by(sku=sku).first()
            if not prod:
                exp_date = (today + timedelta(days=exp_days)) if exp_days else None
                prod = Product(
                    name=name,
                    sku=sku,
                    barcode=f"890{random.randint(100000000, 999999999)}",
                    category_id=cat_map[cat_name],
                    supplier_id=sup_map.get(sup_comp),
                    brand=brand,
                    purchase_price=Decimal(str(pp)),
                    selling_price=Decimal(str(sp)),
                    quantity=qty,
                    min_stock_level=min_stk,
                    unit=unit,
                    expiry_date=exp_date,
                    description=desc,
                    is_active=True
                )
                db.session.add(prod)
                db.session.flush()

                # Add initial stock movement
                if qty > 0:
                    movement = StockMovement(
                        product_id=prod.id,
                        movement_type='in',
                        quantity=qty,
                        previous_quantity=0,
                        new_quantity=qty,
                        reason='Initial stock onboarding',
                        reference_id='INIT-STOCK',
                        user_id=admin.id
                    )
                    db.session.add(movement)

            created_products.append(prod)

        db.session.commit()

        # 5. Realistic Historical Sales (Last 10 days)
        # Generate 15 realistic sales across the last 10 days
        sample_customers = [
            ("Rahul Sharma", "+91 98765 11111"),
            ("Ananya Verma", "+91 98111 22222"),
            ("Kavita Rao", "+91 98222 33333"),
            ("Amitabh Gupta", "+91 98333 44444"),
            ("Sunita Sen", "+91 98444 55555"),
            ("Walk-in Customer", None),
            ("Rajesh Malhotra", "+91 98555 66666"),
            ("Deepika Pillai", "+91 98666 77777"),
            ("Manoj Tiwari", "+91 98777 88888"),
            ("Priya Nair", "+91 98888 99999")
        ]

        payment_methods = ['cash', 'card', 'upi']
        now = datetime.now(timezone.utc)

        sales_count = Sale.query.count()
        if sales_count < 10:
            print("Generating realistic sales transactions...")
            for i in range(1, 16):
                # Spread sales over the past 9 days
                days_ago = (15 - i) % 8
                sale_time = now - timedelta(days=days_ago, hours=random.randint(1, 10), minutes=random.randint(5, 55))
                inv_no = f"INV-202611{i:04d}"

                cust_name, cust_phone = random.choice(sample_customers)
                cashier = random.choice([admin, staff])
                pay_method = random.choice(payment_methods)

                # Pick 2 to 4 distinct products
                picked_prods = random.sample(created_products[:25], k=random.randint(2, 4))
                
                subtotal = Decimal('0.00')
                total_profit = Decimal('0.00')
                sale_items_to_add = []

                for prod in picked_prods:
                    item_qty = random.randint(1, 3)
                    unit_price = Decimal(str(prod.selling_price))
                    unit_cost = Decimal(str(prod.purchase_price))
                    line_tot = unit_price * item_qty
                    line_prof = (unit_price - unit_cost) * item_qty
                    subtotal += line_tot
                    total_profit += line_prof

                    item = SaleItem(
                        product_id=prod.id,
                        product_name=prod.name,
                        sku=prod.sku,
                        unit_cost=unit_cost,
                        unit_price=unit_price,
                        quantity=item_qty,
                        line_total=line_tot,
                        line_profit=line_prof,
                        created_at=sale_time
                    )
                    sale_items_to_add.append((item, prod, item_qty))

                tax_rate = Decimal('5.00')
                tax_amt = round(subtotal * (tax_rate / Decimal('100.00')), 2)
                discount_amt = Decimal('0.00') if random.random() > 0.3 else Decimal(str(random.choice([10, 20, 50])))
                total_amt = subtotal + tax_amt - discount_amt

                sale = Sale(
                    invoice_no=inv_no,
                    user_id=cashier.id,
                    customer_name=cust_name,
                    customer_phone=cust_phone,
                    subtotal=subtotal,
                    tax_rate=tax_rate,
                    tax_amount=tax_amt,
                    discount_amount=discount_amt,
                    total_amount=total_amt,
                    payment_method=pay_method,
                    status='completed',
                    created_at=sale_time
                )
                db.session.add(sale)
                db.session.flush()

                for item, prod, qty in sale_items_to_add:
                    item.sale_id = sale.id
                    db.session.add(item)

            db.session.commit()

        # 6. Initial Activity Logs
        ActivityLog.log(
            action='SEED',
            entity_type='System',
            entity_id='1',
            details='Database initialized with supermarket catalog, categories, suppliers & sample sales',
            user_id=admin.id
        )
        db.session.commit()

        print(f"Successfully seeded database! Total products: {Product.query.count()}, Categories: {Category.query.count()}, Sales: {Sale.query.count()}")
