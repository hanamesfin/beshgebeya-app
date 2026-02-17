from app import parse_description

def test_parsing():
    test_cases = [
        "Dukem Oil 1Lit*12Pcs",
        "Milk 500ml*24Pcs",
        "Rice 5kg",
        "Water 1.5Lit*6Pack",
        "Sugar 1kg x 10Pack",
        "Bread 400gm",
        "Invalid Description"
    ]
    print("-" * 50)
    print(f"{'Description':<30} | {'Name':<15} | {'Size':<10} | {'Pack'}")
    print("-" * 50)
    for tc in test_cases:
        p = parse_description(tc)
        size = f"{p['size_value']}{p['size_unit']}" if p['size_value'] else "-"
        pack = f"{p['pack_quantity']}{p['pack_unit']}" if p['pack_quantity'] else "-"
        name = p['name']
        print(f"{tc:<30} | {name:<15} | {size:<10} | {pack}")
    print("-" * 50)

if __name__ == "__main__":
    test_parsing()
