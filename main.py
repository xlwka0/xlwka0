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
    """Converts '03:54:27' or '3h 54m' into a Discord timestamp."""
    try:
        nums = re.findall(r'\d+', relative_str)
        if len(nums) == 3: # HH:MM:SS
            h, m, s = map(int, nums)
            return int(time.time()) + (h * 3600) + (m * 60) + s
        elif len(nums) == 2: # MM:SS or HH:MM
            n1, n2 = map(int, nums)
            return int(time.time()) + (n1 * 60) + n2
    except: return None
    return None

def get_tab_data(driver, url):
    driver.get(url)
    wait = WebDriverWait(driver, 25) # Long wait for Gamersberg loading
    
    # CRITICAL: Wait for the specific text 'Rocket' or a fruit name to appear 
    # to ensure the "No data" skeleton is gone.
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.font-bold.mt-1")))
    except:
        print(f"Timeout waiting for fruits on {url}")

    # 1. Timer Logic (Targeting the mono/tabular font)
    try:
        timer_el = driver.find_element(By.CSS_SELECTOR, "span.font-mono, span.tabular-nums")
        unix_time = get_unix_timestamp(timer_el.text.strip())
        time_display = f"<t:{unix_time}:R>" if unix_time else "Unknown"
    except:
        time_display = "Unknown"

    # 2. Fruit Logic (Based on your HTML)
    stock_list = []
    high_value_alert = False
    
    # Find all fruit containers
    items = driver.find_elements(By.CSS_SELECTOR, "div.flex.flex-col.items-center")
    
    for item in items:
        try:
            name = item.find_element(By.CSS_SELECTOR, "p.font-bold.mt-1").text.strip()
            # Skip if name is empty (sometimes happens during load)
            if not name: continue 
            
            price_text = item.find_element(By.CSS_SELECTOR, "p.text-sm.font-bold").text.strip()
            
            # Numeric conversion for 1M+ check (Handles 1.20M, 500K, etc)
            clean_price = price_text.upper().replace('$', '')
            num_match = re.findall(r"[-+]?\d*\.\d+|\d+", clean_price)
            if num_match:
                val = float(num_match[0])
                if 'M' in clean_price: val *= 1_000_000
                elif 'K' in clean_price: val *= 1_000
                
                if val >= 1000000:
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
    # Gamersberg might block basic headless, so we add a User-Agent
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        normal = get_tab_data(driver, "https://www.gamersberg.com/blox-fruits/stock?tab=normal")
        mirage = get_tab_data(driver, "https://www.gamersberg.com/blox-fruits/stock?tab=mirage")

        embed = {
            "title": "🎮 Gamersberg Blox Fruits Stock",
            "url": "https://www.gamersberg.com/blox-fruits/stock",
            "color": 3447003, # Blue
            "fields": [
                {
                    "name": "📦 Normal Stock",
                    "value": f"Resets {normal['time']}\n" + ("\n".join(normal['items']) if normal['items'] else "_Loading failed_"),
                    "inline": True
                },
                {
                    "name": "🌌 Mirage Stock",
                    "value": f"Resets {mirage['time']}\n" + ("\n".join(mirage['items']) if mirage['items'] else "_Loading failed_"),
                    "inline": True
                }
            ],
            "footer": {"text": "Gamersberg Tracker"},
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
