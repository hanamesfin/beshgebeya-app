from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-change-this"

# ======== DATABASE CONFIG ========
# Use DIRECT_URL for SQLAlchemy runtime (no ?pgbouncer)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DIRECT_URL")  
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_size": 5,
    "max_overflow": 0,
}

# Create DB instance
db = SQLAlchemy(app)

# ======== MIGRATIONS / CREATE TABLES ========
# Use NullPool to avoid conflicts with PgBouncer
def init_db():
    engine = create_engine(os.getenv("DIRECT_URL"), poolclass=NullPool)
    db.metadata.create_all(engine)
    print("✅ Database tables created.")

# ======== RUNTIME ENGINE OPTION IF USING PGBOUNCER ========
# Only enable PgBouncer at runtime if needed
# engine = create_engine(os.getenv("DATABASE_URL"), pool_size=5, max_overflow=0, pool_pre_ping=True)

# Call init_db() only when needed (not at every runtime)





# MODELS
class User(db.Model):
    __tablename__ = "users" 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    branch = db.relationship('Branch', backref='users')
  

class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    inventory = db.relationship('Inventory', backref='branch', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    local_name = db.Column(db.String(100))  # Amharic name
    description = db.Column(db.Text)
    barcode = db.Column(db.String(50), unique=True, index=True)
    local_code = db.Column(db.String(50), unique=True, index=True)  # Internal code
    sku = db.Column(db.String(50), unique=True)
    category = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(100))
  
    supplier = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    inventory = db.relationship('Inventory', backref='product', lazy=True)
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    quantity_on_hand = db.Column(db.Integer, nullable=False, default=0)
    threshold_min = db.Column(db.Integer, default=10)
    expiry_date = db.Column(db.DateTime)
    entry_date = db.Column(db.DateTime, default=datetime.utcnow)  # When stock was added
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
    quantity = db.Column(db.Integer)  # For tracking how many items
    days_until_expiry = db.Column(db.Integer)  # Days left until expiry
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# AUTH DECORATORS
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

# ROUTES
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('signup'))
        
        # First user becomes admin
        is_first_user = User.query.count() == 0
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            name=username,
            is_admin=is_first_user,
            branch_id=1
        )
        db.session.add(user)
        db.session.commit()
        
        if is_first_user:
            flash('Account created! You are the admin.', 'success')
        else:
            flash('Account created! Please login.', 'success')
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
        product = Product(
            name=request.form['name'],
            local_name=request.form.get('local_name', ''),
            description=request.form.get('description', ''),
            sku=request.form['sku'],
            barcode=request.form.get('barcode'),
            local_code=request.form.get('local_code'),
            category=request.form['category'],
            brand=request.form.get('brand', ''),
            supplier=request.form.get('supplier', '')
        )
        db.session.add(product)
        db.session.commit()
        flash('Product created!', 'success')
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
        
        product_id = request.form['product_id']
        branch_id = 1
        quantity = int(request.form['quantity_on_hand'])
        
        inv = Inventory.query.filter_by(product_id=product_id, branch_id=branch_id).first()
        
        if inv:
            inv.quantity_on_hand = quantity
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
                threshold_min=int(request.form.get('threshold_min', 10)),
                expiry_date=datetime.strptime(request.form['expiry_date'], '%Y-%m-%d') if request.form.get('expiry_date') else None,
                entry_date=datetime.utcnow(),
                batch_number=request.form.get('batch_number'),
                status=request.form.get('status', 'AVAILABLE')
            )
            db.session.add(inv)
        
        db.session.commit()
        flash('Inventory updated!', 'success')
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
@admin_required
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



      
if __name__ == "__main__":
    app.run()
