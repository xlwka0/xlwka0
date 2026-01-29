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

# Get Webhook from GitHub Secrets
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

def scrape_fruity_blox():
    if not WEBHOOK_URL:
        print("❌ Error: DISCORD_WEBHOOK secret is missing!")
        return

    # 1. Browser Configuration for GitHub (Linux/Headless)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        print("🔗 Connecting to FruityBlox...")
        driver.get("https://fruityblox.com/stock")
        
        wait = WebDriverWait(driver, 20)
        # Wait for the grid of fruits to appear
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h3")))

        # 2. Extract Data
        # Based on your HTML: Names are in <h3>, Prices in .text-green-400
        fruit_elements = driver.find_elements(By.CSS_SELECTOR, "a.block.bg-card")
        
        stock_lines = []
        for fruit in fruit_elements:
            try:
                name = fruit.find_element(By.TAG_NAME, "h3").text.strip()
                price = fruit.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                stock_lines.append(f"🍎 **{name}** | 💵 {price}")
            except:
                continue

        # 3. Prepare Discord Message
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if stock_lines:
            content = f"🛰️ **FruityBlox Live Stock Update**\n*Last Checked: {timestamp}*\n\n" + "\n".join(stock_lines[:15])
        else:
            content = f"⚠️ Checked at {timestamp}, but no stock was found. Layout might have changed!"

        # 4. Send to Discord
        response = requests.post(WEBHOOK_URL, json={"content": content})
        if response.status_code == 204:
            print("✅ Successfully sent to Discord!")
        else:
            print(f"❌ Discord Error: {response.status_code}")

    except Exception as e:
        print(f"💥 Scraper Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_fruity_blox()
