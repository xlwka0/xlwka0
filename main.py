import os
import requests
import datetime
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

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
                
            # 1. Get Reset Time
            try:
                parent_section = header.find_element(By.XPATH, "./..")
                timer_element = parent_section.find_element(By.CLASS_NAME, "tabular-nums")
                reset_time = timer_element.text.strip()
            except:
                reset_time = "Unknown"

            # 2. Get Fruits
            stock_list = []
            try:
                grid = header.find_element(By.XPATH, "./following-sibling::div[contains(@class, 'grid')]")
                cards = grid.find_elements(By.CSS_SELECTOR, "a.block.bg-card")
                
                for card in cards:
                    name = card.find_element(By.TAG_NAME, "h3").text.strip()
                    price_text = card.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                    
                    # Check if value is over 1,000,000
                    # We remove '$' and ',' to turn "5,000,000" into 5000000
                    numeric_price = re.sub(r'[^\d]', '', price_text)
                    if numeric_price and int(numeric_price) >= 1000000:
                        name_display = f"🔥 **{name}**" # Highlight high value
                        high_value_found = True
                    else:
                        name_display = name

                    stock_list.append(f"• {name_display} | 💵 {price_text}")
            except:
                pass
            
            sections_data[title] = {"time": reset_time, "items": stock_list}

        # Construct Message
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # If a fruit >= 1M is found, add an @everyone ping at the top
        ping = "🔔 @everyone **HIGH VALUE STOCK DETECTED!** 🔔\n" if high_value_found else ""
        
        message = f"{ping}🛰️ **FruityBlox Live Stock Update**\n"

        for section, data in sections_data.items():
            message += f"\n**{section}** (Resets in: `{data['time']}`)\n"
            message += "\n".join(data['items']) if data['items'] else "_No stock found._"
            message += "\n"
        
        message += f"\n*Last Checked: {timestamp}*"

        requests.post(WEBHOOK_URL, json={"content": message})

    except Exception as e:
        print(f"Scraper Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_fruity_blox()
