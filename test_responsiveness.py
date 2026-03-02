from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_ui():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--window-size=400,800')
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get('http://127.0.0.1:5000/login')
        driver.find_element(By.NAME, 'username').send_keys('admin')
        driver.find_element(By.NAME, 'password').send_keys('admin_password')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Test Products Grid
        driver.get('http://127.0.0.1:5000/products')
        time.sleep(1)
        
        # Check if grid exists instead of table
        grid = driver.find_element(By.CLASS_NAME, 'product-grid')
        if grid: print("✅ product-grid found")
        else: print("❌ product-grid NOT found")
        
        # Check sticky search
        search_container = driver.find_element(By.CLASS_NAME, 'sticky-search-container')
        if "sticky" in search_container.value_of_css_property("position"):
            print("✅ search container is sticky")
        else:
            print("❌ search container is NOT sticky")
            
        print("UI Test Complete.")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_ui()
