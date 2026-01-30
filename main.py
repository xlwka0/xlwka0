import os
import requests
import datetime
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

def get_unix_timestamp(relative_str):
    """Parses time strings like '01h 05m 10s' or '01:05:10' into Discord Unix."""
    try:
        # Extract all numbers from the string
        nums = re.findall(r'\d+', relative_str)
        if len(nums) == 3:
            h, m, s = map(int, nums)
            total_seconds = (h * 3600) + (m * 60) + s
            return int(time.time()) + total_seconds
    except:
        return None
    return None

def get_tab_data(driver, url, label):
    driver.get(url)
    wait = WebDriverWait(driver, 15)
    
    # Wait for the stock items to load
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "img")))
    time.sleep(2) # Brief pause for animations

    # 1. Grab the Reset Timer
    # Gamersberg usually has the timer near the top or inside a specific badge
    try:
        timer_text = driver.find_element(By.XPATH, "//*[contains(text(), 'h') and contains(text(), 'm')]").text
        unix_time = get_unix_timestamp(timer_text)
        time_display = f"<t:{unix_time}:R>" if unix_time else "Unknown"
    except:
        time_display = "Unknown"

    # 2. Grab the Fruits
    stock_list = []
    high_value_found = False
    
    # Target common Gamersberg stock item containers
    items = driver.find_elements(By.CSS_SELECTOR, "div.flex.flex-col.items-center, div.bg-secondary")
    
    for item in items:
        try:
            name = item.find_element(By.TAG_NAME, "h3").text.strip()
            price_text = item.find_element(By.XPATH, ".//*[contains(text(), '$')]").text.strip()
            
            # Clean price to check for 1M+ alert
            numeric_price = int(re.sub(r'[^\d]', '', price_text))
            
            if numeric_price >= 1000000:
                stock_list.append(f"🔥 **{name}** | `{price_text}`")
                high_value_found = True
            else:
                stock_list.append(f"• {name} | `{price_text}`")
        except:
            continue

    return {"time": time_display, "items": stock_list, "alert": high_value_found}

def run_scraper():
    if not WEBHOOK_URL: return

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # Scrape both tabs
        normal = get_tab_data(driver, "https://www.gamersberg.com/blox-fruits/stock?tab=normal", "Normal")
        mirage = get_tab_data(driver, "https://www.gamersberg.com/blox-fruits/stock?tab=mirage", "Mirage")

        # Create Embed
        embed = {
            "title": "🎮 Gamersberg Blox Fruits Stock",
            "url": "https://www.gamersberg.com/blox-fruits/stock",
            "color": 3447003, # Blue
            "fields": [
                {
                    "name": "📦 Normal Stock",
                    "value": f"Resets {normal['time']}\n" + ("\n".join(normal['items'][:12]) or "No data"),
                    "inline": True
                },
                {
                    "name": "🌌 Mirage Stock",
                    "value": f"Resets {mirage['time']}\n" + ("\n".join(mirage['items'][:12]) or "No data"),
                    "inline": True
                }
            ],
            "footer": {"text": f"Last Checked: {datetime.datetime.now().strftime('%H:%M:%S')}"}
        }

        payload = {"embeds": [embed]}
        if normal['alert'] or mirage['alert']:
            payload["content"] = "🚨 **High Value Fruit Found!** @everyone"

        requests.post(WEBHOOK_URL, json=payload)

    finally:
        driver.quit()

if __name__ == "__main__":
    run_scraper()
