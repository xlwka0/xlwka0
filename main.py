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
    """Calculates a future Unix timestamp from an HH:MM:SS string."""
    try:
        parts = relative_time_str.split(':')
        if len(parts) != 3: return None
        seconds_to_add = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return int(time.time()) + seconds_to_add
    except:
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

        headers = driver.find_elements(By.TAG_NAME, "h2")
        fields = []
        high_value_alert = False

        for header in headers:
            title = header.text.strip()
            if "Normal" not in title and "Mirage" not in title: continue
                
            # Timer Logic
            try:
                parent = header.find_element(By.XPATH, "./..")
                raw_time = parent.find_element(By.CLASS_NAME, "tabular-nums").text.strip()
                unix_reset = get_unix_time(raw_time)
                time_display = f"⌛ Resets <t:{unix_reset}:R>" if unix_reset else "⌛ Resets: Unknown"
            except:
                time_display = "⌛ Resets: Unknown"

            # Fruit Logic
            stock_lines = []
            try:
                grid = header.find_element(By.XPATH, "./following-sibling::div[contains(@class, 'grid')]")
                cards = grid.find_elements(By.CSS_SELECTOR, "a.block.bg-card")
                for card in cards:
                    name = card.find_element(By.TAG_NAME, "h3").text.strip()
                    price = card.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                    
                    val = int(re.sub(r'[^\d]', '', price))
                    if val >= 1000000:
                        stock_lines.append(f"🔥 **{name}** (`{price}`) ")
                        high_value_alert = True
                    else:
                        stock_lines.append(f"• {name} (`{price}`)")
            except:
                pass
            
            # Add section as an Embed Field
            fields.append({
                "name": f"━━━ {title} ━━━",
                "value": f"{time_display}\n" + ("\n".join(stock_lines) if stock_lines else "_No stock_"),
                "inline": True
            })

        # Final Embed Structure
        embed = {
            "title": "🍎 FruityBlox Stock Update",
            "color": 15548997, # Red-ish color
            "fields": fields,
            "footer": {"text": "FruityBlox Scraper Bot • GitHub Actions"},
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }

        payload = {"embeds": [embed]}
        if high_value_alert:
            payload["content"] = "🔔 @everyone **High Value Fruit in Stock!**"

        requests.post(WEBHOOK_URL, json=payload)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_fruity_blox()
