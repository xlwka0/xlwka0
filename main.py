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
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h2"))) # Wait for section headers

        # Find all section containers (Normal and Mirage)
        # Usually, these are grouped by divs or follow a header
        sections = driver.find_elements(By.XPATH, "//div[contains(@class, 'space-y-6') or contains(@class, 'mb-8')]")
        
        final_message = "🛰️ **FruityBlox Live Stock Update**\n"
        
        # We'll try to find the two main grids
        # Normal is usually the first h2, Mirage is the second
        headers = driver.find_elements(By.TAG_NAME, "h2")
        grids = driver.find_elements(By.CLASS_NAME, "grid")

        for i, header in enumerate(headers):
            header_text = header.text.strip()
            if "Normal" in header_text or "Mirage" in header_text:
                final_message += f"\n**{header_text}**:\n"
                
                # Get the items specifically inside the grid following this header
                if i < len(grids):
                    cards = grids[i].find_elements(By.CSS_SELECTOR, "a.block.bg-card")
                    for card in cards:
                        try:
                            name = card.find_element(By.TAG_NAME, "h3").text.strip()
                            price = card.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                            final_message += f"• {name} | 💵 {price}\n"
                        except:
                            continue

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_message += f"\n*Last Checked: {timestamp}*"

        requests.post(WEBHOOK_URL, json={"content": final_message})

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_fruity_blox()
