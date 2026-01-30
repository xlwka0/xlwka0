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
    try:
        # Matches formats like "00:41:11" or "00h 41m 11s"
        nums = re.findall(r'\d+', relative_str)
        if len(nums) == 3:
            h, m, s = map(int, nums)
            return int(time.time()) + (h * 3600) + (m * 60) + s
    except: return None
    return None

def get_tab_data(driver, url):
    driver.get(url)
    wait = WebDriverWait(driver, 20)
    
    # Wait for the fruit container to load based on your HTML
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "grid")))
    time.sleep(3) # Give extra time for React/Next.js to render

    # 1. Timer Logic - Gamersberg uses specific text for the countdown
    try:
        # Search for any text containing 'h' and 'm' or the countdown pattern
        timer_el = driver.find_element(By.XPATH, "//*[contains(text(), ':') and (contains(@class, 'tabular-nums') or contains(@class, 'font-mono'))]")
        unix_time = get_unix_timestamp(timer_el.text)
        time_display = f"<t:{unix_time}:R>" if unix_time else "Unknown"
    except:
        time_display = "Unknown"

    # 2. Fruit Logic - Using the 'flex-col items-center' from your HTML
    stock_list = []
    high_value_alert = False
    
    items = driver.find_elements(By.CSS_SELECTOR, "div.flex.flex-col.items-center")
    
    for item in items:
        try:
            # Fruit Name is in the bold paragraph
            name = item.find_element(By.CSS_SELECTOR, "p.font-bold.mt-1").text.strip()
            # Price is in the paragraph with the dollar icon
            price_text = item.find_element(By.CSS_SELECTOR, "p.text-sm.font-bold").text.strip()
            
            # Convert values like 5.00K or 1.20M to numbers for the alert
            clean_price = price_text.upper()
            numeric_val = float(re.findall(r"[-+]?\d*\.\d+|\d+", clean_price.replace(',', ''))[0])
            
            if 'M' in clean_price:
                actual_value = numeric_val * 1_000_000
            elif 'K' in clean_price:
                actual_value = numeric_val * 1_000
            else:
                actual_value = numeric_val

            if actual_value >= 1000000:
                stock_list.append(f"🔥 **{name}** | `${price_text}`")
                high_value_alert = True
            else:
                stock_list.append(f"• {name} | `${price_text}`")
        except:
            continue

    return {"time": time_display, "items": stock_list, "alert": high_value_alert}

def run_scraper():
    if not WEBHOOK_URL: return

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        normal = get_tab_data(driver, "https://www.gamersberg.com/blox-fruits/stock?tab=normal")
        mirage = get_tab_data(driver, "https://www.gamersberg.com/blox-fruits/stock?tab=mirage")

        embed = {
            "title": "🎮 Gamersberg Blox Fruits Stock",
            "url": "https://www.gamersberg.com/blox-fruits/stock",
            "color": 3447003,
            "fields": [
                {
                    "name": "📦 Normal Stock",
                    "value": f"Resets {normal['time']}\n" + ("\n".join(normal['items']) if normal['items'] else "_Empty_"),
                    "inline": True
                },
                {
                    "name": "🌌 Mirage Stock",
                    "value": f"Resets {mirage['time']}\n" + ("\n".join(mirage['items']) if mirage['items'] else "_Empty_"),
                    "inline": True
                }
            ],
            "footer": {"text": "Bot by Gemini • Last Check"},
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }

        payload = {"embeds": [embed]}
        if normal['alert'] or mirage['alert']:
            payload["content"] = "🚨 **High Value Fruit Found!** @everyone"

        requests.post(WEBHOOK_URL, json=payload)

    finally:
        driver.quit()

if __name__ == "__main__":
    run_scraper()
