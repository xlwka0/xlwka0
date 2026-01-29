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

def get_discord_timestamp(relative_time_str):
    """Converts HH:MM:SS into a Discord Unix timestamp."""
    try:
        parts = relative_time_str.split(':')
        if len(parts) != 3:
            return "Unknown"
        
        # Calculate total seconds from now
        seconds_to_add = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        
        # Current Unix time + seconds from site
        future_unix = int(time.time()) + seconds_to_add
        
        # Return Discord formatted timestamp (Style 'R' is relative countdown)
        return f"<t:{future_unix}:R>"
    except:
        return "Unknown"

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

        headers = driver.find_elements(By.TAG_NAME, "h2")
        sections_data = {}
        high_value_found = False

        for header in headers:
            title = header.text.strip()
            if "Normal" not in title and "Mirage" not in title:
                continue
                
            # 1. Get Reset Time and Convert to Discord Timestamp
            try:
                parent_section = header.find_element(By.XPATH, "./..")
                timer_element = parent_section.find_element(By.CLASS_NAME, "tabular-nums")
                raw_time = timer_element.text.strip()
                discord_time = get_discord_timestamp(raw_time)
            except:
                discord_time = "Unknown"

            # 2. Get Fruits
            stock_list = []
            try:
                grid = header.find_element(By.XPATH, "./following-sibling::div[contains(@class, 'grid')]")
                cards = grid.find_elements(By.CSS_SELECTOR, "a.block.bg-card")
                
                for card in cards:
                    name = card.find_element(By.TAG_NAME, "h3").text.strip()
                    price_text = card.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                    
                    numeric_price = re.sub(r'[^\d]', '', price_text)
                    if numeric_price and int(numeric_price) >= 1000000:
                        name_display = f"🔥 **{name}**"
                        high_value_found = True
                    else:
                        name_display = name

                    stock_list.append(f"• {name_display} | 💵 {price_text}")
            except:
                pass
            
            sections_data[title] = {"time": discord_time, "items": stock_list}

        # Construct Message
        ping = "🔔 @everyone **HIGH VALUE STOCK!** 🔔\n" if high_value_found else ""
        message = f"{ping}🛰️ **FruityBlox Live Stock Update**\n"

        for section, data in sections_data.items():
            # Using the Discord timestamp here
            message += f"\n**{section}** (Resets {data['time']})\n"
            message += "\n".join(data['items']) if data['items'] else "_No stock found._"
            message += "\n"
        
        # Add a static timestamp for when the message was actually sent
        now_unix = int(time.time())
        message += f"\n*Checked at <t:{now_unix}:f>*"

        requests.post(WEBHOOK_URL, json={"content": message})

    except Exception as e:
        print(f"Scraper Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_fruity_blox()
