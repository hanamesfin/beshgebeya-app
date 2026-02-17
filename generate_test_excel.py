import openpyxl

def generate_test_excel():
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Products"
    
    # Common headers as supported by the updated import logic
    headers = ["Description", "Code", "Selling Price", "Cost Price", "Stock"]
    sheet.append(headers)
    
    data = [
        ["Dukem Oil 1Lit*12Pcs", "SO-001", "1200", "1000", "5"],
        ["Milk 500ml*24Pcs", "MK-002", "45", "35", "10"],
        ["Rice 5kg", "RC-003", "450", "400", "2"],
        ["Water 1.5Lit*6Pack", "WT-004", "180", "150", "20"]
    ]
    
    for row in data:
        sheet.append(row)
    
    wb.save("smart_test_products.xlsx")
    print("Created smart_test_products.xlsx")

if __name__ == "__main__":
    generate_test_excel()
