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
    """Converts HH:MM:SS to a 10-digit Unix timestamp."""
    try:
        parts = relative_time_str.strip().split(':')
        if len(parts) != 3: return None
        # Calculate total seconds until reset
        seconds_to_add = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        # Discord needs an integer for the timestamp
        return int(time.time()) + seconds_to_add
    except Exception as e:
        print(f"Timer error: {e}")
        return None

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
        timers = {"Normal": "Unknown", "Mirage": "Unknown"}
        for stock_type in ["Normal", "Mirage"]:
            try:
                # Find the h2 section and locate the font-mono time next to it
                timer_xpath = f"//h2[contains(text(), '{stock_type}')]/..//span[contains(@class, 'font-mono')]"
                raw_time = driver.find_element(By.XPATH, timer_xpath).text.strip()
                
                unix_ts = get_unix_time(raw_time)
                if unix_ts:
                    # THE FIX: Ensure it is a raw string <t:UNIX:R> for Discord to parse
                    timers[stock_type] = f"<t:{unix_ts}:R>"
            except: pass

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

                    # Formatting: Vulcan Dot • Price
                    if val >= 1000000:
                        stock_lines.append(f"🔥 **{name}** • 🟢 `${price}`")
                        high_value_alert = True
                    else:
                        stock_lines.append(f"▫️ {name} • `${price}`")
            except: pass

            # Formatting logic for the Vulcan look
            stock_key = "Normal" if "Normal" in title else "Mirage"
            current_relative_time = timers[stock_key]
            
            # Vulcan divider line
            description = "\n".join(stock_lines) + "\n" + "─" * 25
            
            embeds.append({
                "title": f"Current {title} Stock",
                "description": description,
                "color": 2829617,
                "footer": {"text": f"🕒 Stock Change {current_relative_time}"}
            })

        # Send both cards in ONE message
        payload = {"embeds": embeds}
        if high_value_alert:
            payload["content"] = "🚨 **High Value Stock Alert!** @everyone"

        requests.post(WEBHOOK_URL, json=payload)

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_fruity_blox()
