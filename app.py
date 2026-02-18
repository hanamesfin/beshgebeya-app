import os
import csv
import re
import requests
import xml.etree.ElementTree as ET
import openpyxl
import xlrd
from io import StringIO, BytesIO
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import click
# =====================
# CREATE APP
# =====================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "super-secret-key")

# =====================
# DATABASE CONFIG
# =====================
database_url = os.environ.get("DATABASE_URL")

if database_url:
    # Convert old-style postgres URI for SQLAlchemy
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
else:
    # Local fallback (SQLite)
    database_url = "sqlite:///local.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# =====================
# INITIALIZE DB
# =====================
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# =====================
# MODELS
# =====================
class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='branch', lazy=True)
    inventory = db.relationship('Inventory', backref='branch', lazy=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    local_name = db.Column(db.String(255))
    description = db.Column(db.Text)
    
    sku = db.Column(db.String(100), unique=True, index=True)
    local_code = db.Column(db.String(100), unique=True, index=True)
    internal_code = db.Column(db.String(100))
    barcode = db.Column(db.String(100), unique=True, index=True)
    
    # Size Info (e.g., 1 Lit)
    size_value = db.Column(db.Float)
    size_unit = db.Column(db.String(20))
    
    # Pack Info (e.g., 12 Pcs)
    pack_quantity = db.Column(db.Integer)
    pack_unit = db.Column(db.String(20))
    
    category = db.Column(db.String(100), nullable=True)
    brand = db.Column(db.String(100))
    supplier = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inventory = db.relationship('Inventory', backref='product', lazy=True)
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True)
    
    quantity_on_hand = db.Column(db.Float, nullable=True, default=0.0)
    unit_of_measure = db.Column(db.String(20)) # Pcs, Box, Carton
    
    threshold_min = db.Column(db.Integer, default=10)
    unit_size = db.Column(db.Float)
    unit_measure = db.Column(db.String(20))
    pack_qty = db.Column(db.Integer, default=1)
    pack_unit = db.Column(db.String(20), default='Pcs')
    extra_info = db.Column(db.String(255))
    
    cost_price = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, default=0.0)
    
    expiry_date = db.Column(db.DateTime)
    entry_date = db.Column(db.DateTime, default=datetime.utcnow)
    batch_number = db.Column(db.String(50))
    status = db.Column(db.String(20), default='AVAILABLE')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)


class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    product_id = db.Column(db.Integer)
    branch_id = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    days_until_expiry = db.Column(db.Integer)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# =====================
# DATABASE INITIALIZATION
# =====================
def initialize_database(app: Flask):
    """Insert default branch and admin user safely."""
    with app.app_context():
        # Ensure at least one branch exists
        if Branch.query.count() == 0:
            default_branch = Branch(
                name="Main Branch",
                location="Head Office",
                phone="0000000000"
            )
            db.session.add(default_branch)
            db.session.commit()
            print("[DB INIT] Default branch created")

        # Ensure admin exists
        if User.query.filter_by(username="admin").first() is None:
            branch = Branch.query.first()
            default_admin = User(
                username="admin",
                email="admin@example.com",
                name="Administrator",
                is_admin=True,
                branch_id=branch.id,
                password_hash=generate_password_hash("admin123")
            )
            db.session.add(default_admin)
            db.session.commit()
            print("[DB INIT] Default admin user created")

# =====================
# CALL DATABASE INITIALIZATION
# =====================
@app.cli.command("seed")
def seed():
    """Seed default branch and admin user."""
   # initialize_database(app)
    click.echo("Seed complete.")
# =====================
# AUTH DECORATORS
# =====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# =====================
# ROUTES (unchanged)
# =====================

# ROUTES
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check existing username
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('signup'))

        # Ensure at least one branch exists
        branch = Branch.query.first()
        if not branch:
            branch = Branch(
                name="Main Branch",
                location="Head Office",
                phone="0000000000"
            )
            db.session.add(branch)
            db.session.commit()

        is_first_user = User.query.count() == 0

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            name=username,
            is_admin=is_first_user,
            branch_id=branch.id
        )

        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'success')
    return redirect(url_for('login'))
@app.route('/')
@login_required
def dashboard():
    today = datetime.utcnow()

    # Expiry ranges
    expiring_0_90 = Inventory.query.filter(
        Inventory.expiry_date.between(today, today + timedelta(days=90)),
        Inventory.quantity_on_hand > 0
    ).order_by(Inventory.expiry_date).all()

    expiring_180 = Inventory.query.filter(
        Inventory.expiry_date.between(today + timedelta(days=90), today + timedelta(days=180)),
        Inventory.quantity_on_hand > 0
    ).order_by(Inventory.expiry_date).all()

    # Alerts
    alerts = Alert.query.filter_by(is_read=False).order_by(Alert.created_at.desc()).limit(10).all()

    # Sales summary (using SaleItem)
    sales_items = SaleItem.query.all()
    total_sales = sum(item.price for item in sales_items)

    product_sales = {}
    for item in sales_items:
        if item.product_id not in product_sales:
            product_sales[item.product_id] = {
                'name': item.product.name,
                'quantity': 0,
                'revenue': 0
            }
        product_sales[item.product_id]['quantity'] += item.quantity
        product_sales[item.product_id]['revenue'] += item.price

    top_products = sorted(product_sales.values(), key=lambda x: x['quantity'], reverse=True)[:5]

    return render_template(
        'dashboard.html',
        total_sales=total_sales,
        total_count=len(sales_items),
        alerts=alerts,
        top_products=top_products,
        expiring_0_90=expiring_0_90,
        expiring_180=expiring_180,
        now=today
    )

@app.route('/products', methods=['GET', 'POST'])
@login_required
def products():
    if request.method == 'POST':
        name = request.form['name']
        sku = sanitize_unique_field(request.form.get('sku'))
        barcode = sanitize_unique_field(request.form.get('barcode'))
        local_code = sanitize_unique_field(request.form.get('local_code'))
        
        # Resiliency: Check for existing product by SKU or Barcode
        product = None
        if sku:
            product = Product.query.filter_by(sku=sku).first()
        if not product and barcode:
            product = Product.query.filter_by(barcode=barcode).first()
            
        if product:
            # Update existing
            product.name = name
            product.local_name = request.form.get('local_name', product.local_name)
            product.description = request.form.get('description', product.description)
            if sku: product.sku = sku
            if barcode: product.barcode = barcode
            if local_code: product.local_code = local_code
            product.internal_code = request.form.get('internal_code', product.internal_code)
            product.size_value = request.form.get('size_value', type=float) or product.size_value
            product.size_unit = request.form.get('size_unit', product.size_unit)
            product.pack_quantity = request.form.get('pack_quantity', type=int) or product.pack_quantity
            product.pack_unit = request.form.get('pack_unit', product.pack_unit)
            product.category = request.form.get('category', product.category)
            product.brand = request.form.get('brand', product.brand)
            product.supplier = request.form.get('supplier', product.supplier)
            flash('Product updated (merged)!', 'success')
        else:
            # Create new
            product = Product(
                name=name,
                local_name=request.form.get('local_name', ''),
                description=request.form.get('description', ''),
                sku=sku,
                barcode=barcode,
                local_code=local_code,
                internal_code=request.form.get('internal_code'),
                size_value=request.form.get('size_value', type=float),
                size_unit=request.form.get('size_unit'),
                pack_quantity=request.form.get('pack_quantity', type=int),
                pack_unit=request.form.get('pack_unit'),
                category=request.form.get('category'),
                brand=request.form.get('brand', ''),
                supplier=request.form.get('supplier', '')
            )
            db.session.add(product)
            flash('Product created!', 'success')
            
        db.session.commit()
        return redirect(url_for('products'))
    
    products_list = Product.query.order_by(Product.name).all()
    return render_template('products.html', products=products_list)

@app.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST':
        # Check if searching by barcode/local_code
        search_code = request.form.get('search_code')
        if search_code:
            product = Product.query.filter(
                (Product.barcode == search_code) | (Product.local_code == search_code)
            ).first()
            if product:
                flash(f'Product found: {product.name}', 'success')
                return redirect(url_for('inventory') + f'?product_id={product.id}')
            else:
                flash('Product not found with that code', 'error')
                return redirect(url_for('inventory'))
        
        try:
            product_id = request.form.get('product_id', type=int)
            if not product_id:
                flash("Please select a product first", "error")
                return redirect(url_for('inventory'))
                
            branch_id = 1
            quantity_str = request.form.get('quantity_on_hand', '0')
            try:
                quantity = float(quantity_str)
            except ValueError:
                quantity = 0.0
            
            inv = Inventory.query.filter_by(product_id=product_id, branch_id=branch_id).first()
            
            if inv:
                inv.quantity_on_hand = quantity
                inv.unit_of_measure = request.form.get('unit_of_measure')
                inv.threshold_min = int(request.form.get('threshold_min', 10))
                if request.form.get('expiry_date'):
                    inv.expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d')
                inv.entry_date = datetime.utcnow()
                inv.batch_number = request.form.get('batch_number')
                inv.status = request.form.get('status', 'AVAILABLE')
            else:
                inv = Inventory(
                    product_id=product_id,
                    branch_id=branch_id,
                    quantity_on_hand=quantity,
                    unit_of_measure=request.form.get('unit_of_measure'),
                    threshold_min=int(request.form.get('threshold_min', 10)),
                    expiry_date=datetime.strptime(request.form['expiry_date'], '%Y-%m-%d') if request.form.get('expiry_date') else None,
                    entry_date=datetime.utcnow(),
                    batch_number=request.form.get('batch_number'),
                    status=request.form.get('status', 'AVAILABLE')
                )
                db.session.add(inv)
            
            db.session.commit()
            flash('Inventory updated!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating inventory: {str(e)}', 'error')
            
        return redirect(url_for('inventory'))
    
    # Sort by expiry date - closest to expiry first
    inventory_list = Inventory.query.join(Product).join(Branch).order_by(
        Inventory.expiry_date.asc().nullslast()
    ).all()
    products_list = Product.query.all()
    
    selected_product_id = request.args.get('product_id')
    
    return render_template('inventory.html', 
                         inventory=inventory_list, 
                         products=products_list,
                         selected_product_id=selected_product_id,
                         now=datetime.utcnow())

@app.route('/sales', methods=['POST'])
@login_required
def create_sale_items():
    data = request.get_json()
    total = 0
    for item in data['items']:
        product = Product.query.get(item['product_id'])
        quantity = int(item['quantity'])
        # Add this line to get the price from the request!
        price = float(item.get('price', 0)) 

        inv = Inventory.query.filter_by(product_id=product.id, branch_id=1).first()
        if inv and inv.quantity_on_hand >= quantity:
            inv.quantity_on_hand -= quantity
        else:
            db.session.rollback()
            return jsonify({'error': 'Insufficient stock'}), 400

        # Now 'price' is defined and won't crash
        sale_item = SaleItem(product_id=product.id, quantity=quantity, price=price)
       
        db.session.add(sale_item)
        total += price

    db.session.commit()
    return jsonify({'success': True, 'total': total})


@app.route('/search-product', methods=['POST'])
@login_required
def search_product():
    code = request.json.get('code')
    product = Product.query.filter(
        (Product.barcode == code) | (Product.local_code == code)
    ).first()
    
    if product:
        inv = Inventory.query.filter_by(product_id=product.id, branch_id=1).first()
        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'local_name': product.local_name,  
                'stock': inv.quantity_on_hand if inv else 0
            }
        })
    else:
        return jsonify({'success': False, 'error': 'Product not found'}), 404

@app.route('/generate-alerts')
@login_required
def generate_alerts():
    today = datetime.utcnow()
    seven_days = today + timedelta(days=7)
    
    # Clear old alerts
    Alert.query.delete()
    
    for item in Inventory.query.all():
        # Low stock alert
        if item.quantity_on_hand <= item.threshold_min and item.status == 'AVAILABLE':
            alert = Alert(
                type='LOW_STOCK',
                message=f'Low stock: {item.product.name}. Only {item.quantity_on_hand} left.',
                product_id=item.product_id,
                branch_id=item.branch_id,
                quantity=item.quantity_on_hand
            )
            db.session.add(alert)
        
        # Expiry alerts
        if item.expiry_date:
            if item.expiry_date <= seven_days and item.expiry_date > today:
                days_left = (item.expiry_date - today).days
                alert = Alert(
                    type='NEAR_EXPIRY',
                    message=f'{item.product.name} expires in {days_left} days ({item.quantity_on_hand} units)',
                    product_id=item.product_id,
                    branch_id=item.branch_id,
                    quantity=item.quantity_on_hand,
                    days_until_expiry=days_left
                )
                db.session.add(alert)
            elif item.expiry_date <= today:
                item.status = 'EXPIRED'
                alert = Alert(
                    type='EXPIRED',
                    message=f'{item.product.name} has EXPIRED! {item.quantity_on_hand} units need removal.',
                    product_id=item.product_id,
                    branch_id=item.branch_id,
                    quantity=item.quantity_on_hand,
                    days_until_expiry=0
                )
                db.session.add(alert)
    
    db.session.commit()
    flash('Alerts generated!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
def admin_panel():
    users = User.query.all()
    total_products = Product.query.count()
    total_inventory = db.session.query(db.func.sum(Inventory.quantity_on_hand)).scalar() or 0
    # We use SaleItem and the 'price' column since that's what you defined
    total_sales = db.session.query(db.func.sum(SaleItem.price)).scalar() or 0
    # Critical alerts for admin
    critical_alerts = Alert.query.filter_by(is_read=False).order_by(Alert.created_at.desc()).all()
    
    return render_template('admin.html',
                         users=users,
                         total_products=total_products,
                         total_inventory=total_inventory,
                         total_sales=total_sales,
                         critical_alerts=critical_alerts)

@app.errorhandler(500)
def internal_error(error):
    return "Internal Server Error: check logs!", 500


# =====================
# ERROR HANDLER
# =====================
@app.errorhandler(500)
def internal_error(error):
    return "Internal Server Error: check logs!", 500


# =====================
# HELPERS
# =====================
def sanitize_unique_field(value):
    """Convert empty strings to None for unique fields to avoid constraint violations"""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def detect_column(column_name):
    """
    Smart detection of column mapping based on common keywords.
    Priority is important to avoid overlaps (e.g., 'Bar Code' catching 'code' for SKU).
    """
    col = str(column_name).lower().strip()
    
    # 1. Barcode (Specific)
    if any(x in col for x in ["barcode", "bar code", "ean", "upc"]):
        return "barcode"
    
    # 2. SKU (Specific)
    if any(x in col for x in ["sku", "product code", "item code"]):
        return "sku"
    
    # 3. Local Code (Specific)
    if any(x in col for x in ["local code", "internal code", "local_code", "ref"]):
        return "local_code"
    
    # 4. Quantity (Specific)
    if any(x in col for x in ["qty", "quantity", "stock", "inventory", "count"]):
        return "quantity"
    
    # 5. Price (Specific)
    if any(x in col for x in ["price", "cost", "amount", "rate"]):
        return "price"
    
    # 6. Category (Specific)
    if any(x in col for x in ["category", "dept", "department", "group"]):
        return "category"
    
    # 7. Brand/Supplier
    if any(x in col for x in ["brand", "make", "manufacturer"]):
        return "brand"
    if any(x in col for x in ["supplier", "vendor", "distributor"]):
        return "supplier"
    
    # 8. Name (Catch-all for description)
    if any(x in col for x in ["name", "title", "product name", "item description", "description"]):
        return "name"
    
    # 9. Loose SKU match
    if "code" in col:
        return "sku"
    
    return None


def parse_product_details(text):
    """
    Production-ready safe parsing that never modifies the original name.
    """
    data = {
        "unit_size": None,
        "unit_measure": None,
        "pack_qty": 1,
        "pack_unit": "Pcs",
        "extra_info": None
    }

    if not text:
        return data

    # Extract bracket info (E), (G), etc.
    bracket = re.search(r"\((.*?)\)", text)
    if bracket:
        data["extra_info"] = bracket.group(1)

    # Extract size like 500ml, 1kg, 200gm, 2Lit
    size_match = re.search(r"(\d+(?:\.\d+)?)\s?(kg|gm|g|ml|cc|Lit|L|Pack)", text, re.IGNORECASE)
    if size_match:
        data["unit_size"] = float(size_match.group(1))
        data["unit_measure"] = size_match.group(2)

    # Extract pack like *12Pcs
    pack_match = re.search(r"\*(\d+)\s?(Pcs|pcs|Pack|Sheets|sack)", text, re.IGNORECASE)
    if pack_match:
        data["pack_qty"] = int(pack_match.group(1))
        data["pack_unit"] = pack_match.group(2)

    return data

# =====================
# RUN APP
# =====================
@app.route('/import-products', methods=['GET', 'POST'])
@login_required
def import_products():
    if request.method == 'POST':
        file = request.files.get('file')
        sheet_url = request.form.get('sheet_url')
        
        imported_data = []
        headers = []
        
        if file and file.filename:
            filename = file.filename.lower()
            file.seek(0)
            if filename.endswith('.csv'):
                try:
                    content = file.read().decode("UTF8")
                    stream = StringIO(content, newline=None)
                    reader = csv.DictReader(stream)
                    headers = [f.strip() for f in reader.fieldnames] if reader.fieldnames else []
                    imported_data = list(reader)
                except Exception as e:
                    flash(f"Error reading CSV: {str(e)}", "error")
            elif filename.endswith('.xlsx'):
                try:
                    wb = openpyxl.load_workbook(file)
                    sheet = wb.active
                    headers = [str(cell.value).strip() if cell.value is not None else "" for cell in sheet[1]]
                    for row in sheet.iter_rows(min_row=2, values_only=True):
                        if any(row):
                            imported_data.append(dict(zip(headers, row)))
                except Exception as e:
                    flash(f"Error parsing XLSX: {str(e)}", "error")
            elif filename.endswith('.xls'):
                try:
                    wb = xlrd.open_workbook(file_contents=file.read())
                    sheet = wb.sheet_by_index(0)
                    headers = [str(sheet.cell_value(0, col)).strip() for col in range(sheet.ncols)]
                    for row_idx in range(1, sheet.nrows):
                        row_data = [sheet.cell_value(row_idx, col) for col in range(sheet.ncols)]
                        if any(row_data):
                            imported_data.append(dict(zip(headers, row_data)))
                except Exception as e:
                    flash(f"Error parsing XLS: {str(e)}", "error")
        elif sheet_url:
            if "docs.google.com/spreadsheets" in sheet_url:
                if "/edit" in sheet_url:
                    sheet_url = sheet_url.split("/edit")[0] + "/export?format=csv"
                elif "/export" not in sheet_url:
                    sheet_url = sheet_url.rstrip("/") + "/export?format=csv"
                try:
                    response = requests.get(sheet_url)
                    response.raise_for_status()
                    stream = StringIO(response.text)
                    reader = csv.DictReader(stream)
                    headers = [f.strip() for f in reader.fieldnames] if reader.fieldnames else []
                    imported_data = list(reader)
                except Exception as e:
                    flash(f"Error fetching Google Sheet: {str(e)}", "error")
                    return redirect(url_for('import_products'))
        
        if not imported_data:
            flash("No data found to import", "error")
            return redirect(url_for('import_products'))
        
        # --- SMART COLUMN MAPPING ---
        column_mapping = {}
        for h in headers:
            field = detect_column(h)
            if field and field not in column_mapping:
                column_mapping[field] = h
        
        # Validation: check for minimum required fields (name or SKU)
        if not column_mapping.get("name") and not column_mapping.get("sku"):
            flash("Could not detect Name or SKU columns. Please ensure your file has identifiable headers.", "error")
            return redirect(url_for('import_products'))
            
        added_count = 0
        merged_count = 0
        failed_rows = []
        
        for i, row in enumerate(imported_data, 1):
            try:
                name_val = str(row.get(column_mapping.get("name")) or "").strip()
                sku = sanitize_unique_field(row.get(column_mapping.get("sku")))
                
                if not name_val:
                    failed_rows.append({"row": i, "reason": "Missing Name"})
                    continue
                if not sku:
                    failed_rows.append({"row": i, "reason": "Missing SKU"})
                    continue

                parsed = parse_product_details(name_val)
                
                stock_qty = 0
                try:
                    sq = row.get(column_mapping.get("quantity")) or row.get(column_mapping.get("stock"))
                    stock_qty = float(sq) if sq else 0.0
                except: stock_qty = 0.0

                price_val = 0
                try:
                    pv = row.get(column_mapping.get("price"))
                    price_val = float(pv) if pv else 0.0
                except: price_val = 0.0

                category = row.get(column_mapping.get("category"))
                brand = row.get(column_mapping.get("brand"))
                supplier = row.get(column_mapping.get("supplier"))
                barcode = sanitize_unique_field(row.get(column_mapping.get("barcode")))

                existing = Product.query.filter_by(sku=sku).first()

                if existing:
                    # Merge logic
                    existing.name = name_val
                    existing.description = name_val
                    if category: existing.category = category
                    if brand: existing.brand = brand
                    if supplier: existing.supplier = supplier
                    if barcode: existing.barcode = barcode
                    merged_count += 1
                    product = existing
                else:
                    product = Product(
                        name=name_val,
                        sku=sku,
                        local_code=sku,
                        description=name_val,
                        barcode=barcode,
                        category=category,
                        brand=brand,
                        supplier=supplier
                    )
                    db.session.add(product)
                    db.session.flush()
                    added_count += 1

                # Inventory Handling
                inv = Inventory.query.filter_by(product_id=product.id, branch_id=1).first()
                if inv:
                    inv.quantity_on_hand += stock_qty
                    inv.unit_size = parsed["unit_size"] or inv.unit_size
                    inv.unit_measure = parsed["unit_measure"] or inv.unit_measure
                    inv.pack_qty = parsed["pack_qty"] or inv.pack_qty
                    inv.pack_unit = parsed["pack_unit"] or inv.pack_unit
                    inv.extra_info = parsed["extra_info"] or inv.extra_info
                    if price_val > 0:
                        inv.selling_price = price_val
                else:
                    inv = Inventory(
                        product_id=product.id,
                        branch_id=1,
                        quantity_on_hand=stock_qty,
                        unit_size=parsed["unit_size"],
                        unit_measure=parsed["unit_measure"],
                        pack_qty=parsed["pack_qty"],
                        pack_unit=parsed["pack_unit"],
                        extra_info=parsed["extra_info"],
                        selling_price=price_val,
                        status='AVAILABLE'
                    )
                    db.session.add(inv)
                
            except Exception as e:
                db.session.rollback()
                failed_rows.append({"row": i, "reason": str(e)})
                continue
        
        db.session.commit()

        # Handle failed rows logging
        log_filename = None
        if failed_rows:
            log_filename = f"failed_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            log_path = os.path.join(app.root_path, 'temp', log_filename)
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "w") as f:
                for failure in failed_rows:
                    f.write(f"Row {failure['row']} - {failure['reason']}\n")
            
            session['last_import_log'] = log_filename

        return render_template('import_products.html', 
                             added=added_count, 
                             merged=merged_count, 
                             failed=len(failed_rows), 
                             log_file=log_filename)

    return render_template('import_products.html')

@app.route('/download-import-log/<filename>')
@login_required
def download_import_log(filename):
    log_path = os.path.join(app.root_path, 'temp', filename)
    if os.path.exists(log_path):
        return send_file(log_path, as_attachment=True)
    flash("Log file not found", "error")
    return redirect(url_for('import_products'))


@app.route('/api/inventory/<int:inventory_id>', methods=['GET'])
@login_required
def get_inventory(inventory_id):
    """Get a single inventory record details"""
    inv = Inventory.query.get_or_404(inventory_id)
    return jsonify({
        'success': True,
        'inventory': {
            'id': inv.id,
            'product_id': inv.product_id,
            'quantity_on_hand': inv.quantity_on_hand,
            'unit_size': inv.unit_size,
            'unit_measure': inv.unit_measure,
            'pack_qty': inv.pack_qty,
            'pack_unit': inv.pack_unit,
            'extra_info': inv.extra_info,
            'cost_price': inv.cost_price,
            'selling_price': inv.selling_price,
            'expiry_date': inv.expiry_date.strftime('%Y-%m-%d') if inv.expiry_date else None,
            'batch_number': inv.batch_number,
            'status': inv.status,
            'threshold_min': inv.threshold_min
        }
    })

@app.route('/api/inventory/<int:inventory_id>', methods=['PUT'])
@login_required
def update_inventory(inventory_id):
    """Update an inventory record via API"""
    try:
        inv = Inventory.query.get_or_404(inventory_id)
        data = request.get_json()
        
        inv.quantity_on_hand = data.get('quantity_on_hand', inv.quantity_on_hand)
        inv.unit_size = data.get('unit_size', inv.unit_size)
        inv.unit_measure = data.get('unit_measure', inv.unit_measure)
        inv.pack_qty = data.get('pack_qty', inv.pack_qty)
        inv.pack_unit = data.get('pack_unit', inv.pack_unit)
        inv.extra_info = data.get('extra_info', inv.extra_info)
        inv.threshold_min = data.get('threshold_min', inv.threshold_min)
        inv.batch_number = data.get('batch_number', inv.batch_number)
        inv.status = data.get('status', inv.status)
        
        if data.get('expiry_date'):
            inv.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d')
            
        db.session.commit()
        return jsonify({'success': True, 'message': 'Inventory updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/inventory/<int:inventory_id>', methods=['DELETE'])
@login_required
def delete_inventory(inventory_id):
    """Delete an inventory record via API"""
    try:
        inv = Inventory.query.get_or_404(inventory_id)
        db.session.delete(inv)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Inventory record deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# =====================
# PRODUCT API ENDPOINTS
# =====================
@app.route('/api/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    """Update a product via API"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        # Update fields
        product.name = data.get('name', product.name)
        product.local_name = data.get('local_name', product.local_name)
        product.description = data.get('description', product.description)
        product.sku = sanitize_unique_field(data.get('sku', product.sku))
        product.barcode = sanitize_unique_field(data.get('barcode', product.barcode))
        product.local_code = sanitize_unique_field(data.get('local_code', product.local_code))
        product.internal_code = data.get('internal_code', product.internal_code)
        product.category = data.get('category', product.category)
        product.brand = data.get('brand', product.brand)
        product.supplier = data.get('supplier', product.supplier)
        
        # Sync structured info if name changed
        parsed = parse_product_details(product.name)
        product.size_value = parsed["unit_size"]
        product.size_unit = parsed["unit_measure"]
        product.pack_quantity = parsed["pack_qty"]
        product.pack_unit = parsed["pack_unit"]
        
        # Sync with Inventory (default branch)
        inv = Inventory.query.filter_by(product_id=product.id, branch_id=1).first()
        if inv:
            inv.unit_size = parsed["unit_size"]
            inv.unit_measure = parsed["unit_measure"]
            inv.pack_qty = parsed["pack_qty"]
            inv.pack_unit = parsed["pack_unit"]
            inv.extra_info = parsed["extra_info"]
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product updated successfully',
            'product': {
                'id': product.id,
                'name': product.name,
                'local_name': product.local_name,
                'sku': product.sku,
                'category': product.category
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    """Delete a product via API"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # Check if product has inventory
        inventory_count = Inventory.query.filter_by(product_id=product_id).count()
        if inventory_count > 0:
            return jsonify({
                'success': False,
                'error': 'Cannot delete product with existing inventory records'
            }), 400
        
        # Remove associated alerts first
        Alert.query.filter_by(product_id=product_id).delete()
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/products/<int:product_id>', methods=['GET'])
@login_required
def get_product(product_id):
    """Get a single product details"""
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'local_name': product.local_name,
            'description': product.description,
            'sku': product.sku,
            'barcode': product.barcode,
            'local_code': product.local_code,
            'internal_code': product.internal_code,
            'size_value': product.size_value,
            'size_unit': product.size_unit,
            'pack_quantity': product.pack_quantity,
            'pack_unit': product.pack_unit,
            'category': product.category,
            'brand': product.brand,
            'supplier': product.supplier
        }
    })

@app.route('/api/admin/reset-database', methods=['POST'])
@login_required
def reset_database_api():
    """Destructive action: reset all products and inventory"""
    try:
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return jsonify({'success': False, 'error': 'Unauthorized. Admin access required.'}), 403
        db.session.query(Inventory).delete()
        db.session.query(Product).delete()
        db.session.query(Alert).delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'All product and inventory data has been reset.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == "__main__":
    with app.app_context():
        initialize_database(app)
    app.run(debug=True)


