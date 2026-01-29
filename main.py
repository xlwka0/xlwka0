import os
import requests
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

def scrape_fruity_blox():
    if not WEBHOOK_URL:
        return

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://fruityblox.com/stock")
        wait = WebDriverWait(driver, 20)
        
        # Wait for the main content to load
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h2")))

        # We will find the parent containers for "Normal" and "Mirage"
        # Based on the site structure, we look for headers and their sibling grids
        headers = driver.find_elements(By.TAG_NAME, "h2")
        
        normal_stock = []
        mirage_stock = []

        for header in headers:
            title = header.text.strip()
            # Find the very next 'grid' element after this header
            try:
                # This XPath finds the first grid that comes after the specific header
                grid = header.find_element(By.XPATH, "./following-sibling::div[contains(@class, 'grid')]")
                cards = grid.find_elements(By.CSS_SELECTOR, "a.block.bg-card")
                
                for card in cards:
                    name = card.find_element(By.TAG_NAME, "h3").text.strip()
                    price = card.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                    item_str = f"• {name} | 💵 {price}"
                    
                    if "Normal" in title:
                        normal_stock.append(item_str)
                    elif "Mirage" in title:
                        mirage_stock.append(item_str)
            except:
                continue

        # Construct the Message
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_content = "🛰️ **FruityBlox Live Stock Update**\n"
        
        message_content += "\n**Normal:**\n"
        message_content += "\n".join(normal_stock) if normal_stock else "None found"
        
        message_content += "\n\n**Mirage:**\n"
        message_content += "\n".join(mirage_stock) if mirage_stock else "None found"
        
        message_content += f"\n\n*Last Checked: {timestamp}*"

        requests.post(WEBHOOK_URL, json={"content": message_content})

    except Exception as e:
        print(f"Scraper Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_fruity_blox()
