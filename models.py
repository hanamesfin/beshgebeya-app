from datetime import datetime
from database import db

class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='branch', lazy=True)
    inventory = db.relationship('Inventory', backref='branch', lazy=True)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=True) # Nullable for social users
    name = db.Column(db.String(100))
    
    # User Preferences
    chart_style = db.Column(db.String(20), default='glass')
    landing_page = db.Column(db.String(20), default='dashboard')
    
    # Social Login IDs
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    apple_id = db.Column(db.String(100), unique=True, nullable=True)
    
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_denied = db.Column(db.Boolean, default=False)
    
    # Password Reset
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    products = db.relationship('Product', backref='category_rel', lazy=True)


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
    
    category = db.Column(db.String(100), nullable=True) # Keeping for legacy/migration
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id')) # Default/Primary location
    
    unit_price = db.Column(db.Float, default=0.0)
    quantity = db.Column(db.Float, default=0.0) # Overall stock tracking
    
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
    
    expiry_date = db.Column(db.DateTime)
    entry_date = db.Column(db.DateTime, default=datetime.utcnow)
    batch_number = db.Column(db.String(50))
    status = db.Column(db.String(20), default='AVAILABLE')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True)
    total_amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(20), default='CASH') # CASH, CARD, MOBILE
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('SaleItem', backref='sale', lazy=True)
    user = db.relationship('User', backref='sales', lazy=True)
    branch = db.relationship('Branch', backref='sales', lazy=True)


class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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


class ImportLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    import_type = db.Column(db.String(50)) # 'FILE' or 'GOOGLE_SHEET'
    added_count = db.Column(db.Integer, default=0)
    merged_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    log_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
