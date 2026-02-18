import sys
import os

# Mocking Flask and SQLAlchemy for testing
class MockDB:
    class session:
        @staticmethod
        def begin_nested():
            return MockDB.session
        @staticmethod
        def __enter__():
            return MockDB.session
        @staticmethod
        def __exit__(*args):
            pass
        @staticmethod
        def rollback():
            pass
        @staticmethod
        def commit():
            pass

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

def test_mapping():
    test_cases = [
        ("Product Code", "sku"),
        ("Item SKU", "sku"),
        ("Description", "name"),
        ("Item Name", "name"),
        ("Cost Price", "price"),
        ("Rate", "price"),
        ("Stock Qty", "quantity"),
        ("Inventory", "quantity"),
        ("Bar Code", "barcode"),
        ("EAN", "barcode"),
        ("Ref #", "local_code"),
        ("Category Name", "category"),
        ("Brand", "brand"),
        ("Vendor", "supplier"),
        ("Unknown", None)
    ]
    
    print("Testing detect_column logic...")
    all_passed = True
    for header, expected in test_cases:
        result = detect_column(header)
        if result == expected:
            print(f"✅ '{header}' -> {result}")
        else:
            print(f"❌ '{header}' -> Expected {expected}, got {result}")
            all_passed = False
            
    if all_passed:
        print("\nAll header mapping tests PASSED! 🚀")
    else:
        print("\nSome tests FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    test_mapping()
