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
    """Calculates a future Unix timestamp from H:MM:SS or HH:MM:SS."""
    try:
        parts = relative_time_str.split(':')
        if len(parts) != 3: return None
        # Handles both 3:54:27 and 03:54:27
        seconds_to_add = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return int(time.time()) + seconds_to_add
    except:
        return None

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
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h2")))

        # --- 1. GET THE TIMERS FIRST ---
        # Normal timer is in the blue container, Mirage is in the purple one
        try:
            normal_timer_raw = driver.find_element(By.CSS_SELECTOR, "div.bg-blue-900\/50").text.strip()
            normal_unix = get_unix_time(normal_timer_raw)
            normal_time_display = f"⌛ Resets <t:{normal_unix}:R>" if normal_unix else "⌛ Resets: Unknown"
        except:
            normal_time_display = "⌛ Resets: Unknown"

        try:
            mirage_timer_raw = driver.find_element(By.CSS_SELECTOR, "div.bg-purple-900\/50").text.strip()
            mirage_unix = get_unix_time(mirage_timer_raw)
            mirage_time_display = f"⌛ Resets <t:{mirage_unix}:R>" if mirage_unix else "⌛ Resets: Unknown"
        except:
            mirage_time_display = "⌛ Resets: Unknown"

        # --- 2. GET THE FRUITS ---
        headers = driver.find_elements(By.TAG_NAME, "h2")
        fields = []
        high_value_alert = False

        for header in headers:
            title = header.text.strip()
            if "Normal" not in title and "Mirage" not in title:
                continue
                
            # Assign the correct timer based on the header title
            current_timer = normal_time_display if "Normal" in title else mirage_time_display

            stock_list = []
            try:
                grid = header.find_element(By.XPATH, "./following-sibling::div[contains(@class, 'grid')]")
                cards = grid.find_elements(By.CSS_SELECTOR, "a.block.bg-card")
                
                for card in cards:
                    name = card.find_element(By.TAG_NAME, "h3").text.strip()
                    price_text = card.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                    
                    # 1M+ Alert Logic
                    numeric_val = int(re.sub(r'[^\d]', '', price_text))
                    if numeric_val >= 1000000:
                        stock_list.append(f"🔥 **{name}** (`{price_text}`)")
                        high_value_alert = True
                    else:
                        stock_list.append(f"• {name} (`{price_text}`)")
            except:
                pass
            
            fields.append({
                "name": f"━━━ {title} ━━━",
                "value": f"{current_timer}\n" + ("\n".join(stock_list) if stock_list else "_No stock found_"),
                "inline": True
            })

        # --- 3. SEND EMBED ---
        embed = {
            "title": "🍎 FruityBlox Live Stock Update",
            "url": "https://fruityblox.com/stock",
            "color": 15548997,
            "fields": fields,
            "footer": {"text": "FruityBlox Scraper Bot • Fixed Timers"},
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }

        payload = {"embeds": [embed]}
        if high_value_alert:
            payload["content"] = "🔔 @everyone **HIGH VALUE FRUIT DETECTED!**"

        requests.post(WEBHOOK_URL, json=payload)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_fruity_blox()
