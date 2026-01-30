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

def get_unix_time(relative_time_str):
    try:
        parts = relative_time_str.split(':')
        if len(parts) != 3: return None
        seconds_to_add = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return int(time.time()) + seconds_to_add
    except: return None

def scrape_fruity_blox():
    if not WEBHOOK_URL: return

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://fruityblox.com/stock")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h2")))

        # --- 1. GET TIMERS ---
        try:
            n_timer = driver.find_element(By.XPATH, "//div[contains(@class, 'bg-blue-500')]//div[contains(@class, 'font-mono')]").text.strip()
            normal_ts = f"in <t:{get_unix_time(n_timer)}:R>"
        except: normal_ts = "Unknown"

        try:
            m_timer = driver.find_element(By.XPATH, "//div[contains(@class, 'bg-purple-500')]//div[contains(@class, 'font-mono')]").text.strip()
            mirage_ts = f"in <t:{get_unix_time(m_timer)}:R>"
        except: mirage_ts = "Unknown"

        # --- 2. GET FRUITS ---
        headers = driver.find_elements(By.TAG_NAME, "h2")
        embeds = []
        high_value_alert = False

        for header in headers:
            title = header.text.strip()
            if "Normal" not in title and "Mirage" not in title: continue
            
            stock_lines = []
            try:
                grid = header.find_element(By.XPATH, "./following-sibling::div[contains(@class, 'grid')]")
                cards = grid.find_elements(By.CSS_SELECTOR, "a.block.bg-card")
                for card in cards:
                    name = card.find_element(By.TAG_NAME, "h3").text.strip()
                    price = card.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                    val = int(re.sub(r'[^\d]', '', price))

                    if val >= 1000000:
                        stock_lines.append(f"🔥 **{name}** • 🟢 `${price}`")
                        high_value_alert = True
                    else:
                        stock_lines.append(f"▫️ {name} • `${price}`")
            except: pass

            # Formatting logic for the "Vulcan" look
            current_ts = normal_ts if "Normal" in title else mirage_ts
            description = "\n".join(stock_lines) + "\n" + "─" * 25
            
            embeds.append({
                "title": f"Current {title} Stock",
                "description": description,
                "color": 2829617,
                "footer": {"text": f"🕒 Stock Change in - {current_ts}"}
            })

        payload = {"embeds": embeds}
        if high_value_alert:
            payload["content"] = "🚨 **High Value Stock Alert!** @everyone"

        requests.post(WEBHOOK_URL, json=payload)

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_fruity_blox()
