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
        nums = re.findall(r'\d+', relative_str)
        if len(nums) == 3:
            h, m, s = map(int, nums)
            return int(time.time()) + (h * 3600) + (m * 60) + s
    except: return None
    return None

def get_tab_data(driver, url, stock_type):
    driver.get(url)
    wait = WebDriverWait(driver, 20)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.font-bold.mt-1")))
    except: pass

    # Timer Logic
    try:
        xpath_query = f"//span[contains(text(), 'Next {stock_type.lower()} stock')]/following-sibling::span"
        timer_el = driver.find_element(By.XPATH, xpath_query)
        unix_time = get_unix_timestamp(timer_el.text.strip())
        time_display = f"in <t:{unix_time}:R>" if unix_time else "Unknown"
    except:
        time_display = "Unknown"

    # Fruit Logic
    stock_lines = []
    high_value_alert = False
    items = driver.find_elements(By.CSS_SELECTOR, "div.flex.flex-col.items-center")
    
    for item in items:
        try:
            name = item.find_element(By.CSS_SELECTOR, "p.font-bold.mt-1").text.strip()
            price_text = item.find_element(By.CSS_SELECTOR, "p.text-sm.font-bold").text.strip()
            
            clean_price = price_text.upper().replace('$', '')
            num_match = re.findall(r"[-+]?\d*\.\d+|\d+", clean_price)
            if num_match:
                val = float(num_match[0])
                if 'M' in clean_price: val *= 1_000_000
                elif 'K' in clean_price: val *= 1_000
                
                # Using the specific bullet points and line style from your reference
                if val >= 1000000:
                    stock_lines.append(f"🔥 **{name}** • 🟢 `${price_text}`")
                    high_value_alert = True
                else:
                    stock_lines.append(f"▫️ {name} • `${price_text}`")
        except: continue

    # Create the horizontal line separator
    content = "\n".join(stock_lines) + "\n" + "─" * 25
    
    return {"time": time_display, "content": content, "alert": high_value_alert}

def run_scraper():
    if not WEBHOOK_URL: return

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        normal = get_tab_data(driver, "https://www.gamersberg.com/blox-fruits/stock?tab=normal", "normal")
        mirage = get_tab_data(driver, "https://www.gamersberg.com/blox-fruits/stock?tab=mirage", "mirage")

        # EMBED 1: Normal Stock
        embed_normal = {
            "title": "Current Normal Stock",
            "description": normal['content'],
            "color": 2829617,
            "footer": {"text": f"🕒 Stock Change in - {normal['time']}"}
        }

        # EMBED 2: Mirage Stock
        embed_mirage = {
            "title": "Current Mirage Stock",
            "description": mirage['content'],
            "color": 2829617,
            "footer": {"text": f"🕒 Stock Change in - {mirage['time']}"}
        }

        payload = {"embeds": [embed_normal, embed_mirage]}
        
        # Ping check
        if normal['alert'] or mirage['alert']:
            payload["content"] = "🚨 **High Value Stock Alert!** @everyone"

        requests.post(WEBHOOK_URL, json=payload)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_scraper()
