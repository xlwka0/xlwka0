import os
import requests
import datetime
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
        print("Missing Webhook URL")
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
        
        # We'll store strings to build the final message
        sections_data = {}

        for header in headers:
            title = header.text.strip()
            if "Normal" not in title and "Mirage" not in title:
                continue
                
            # 1. Get the Reset Time for this specific section
            # Logic: Look for the span with tabular-nums near this header
            try:
                # We look at the parent container of the header to find the timer inside it
                parent_section = header.find_element(By.XPATH, "./..")
                timer_element = parent_section.find_element(By.CLASS_NAME, "tabular-nums")
                reset_time = timer_element.text.strip()
            except:
                reset_time = "Unknown"

            # 2. Get the Fruits for this specific section
            stock_list = []
            try:
                grid = header.find_element(By.XPATH, "./following-sibling::div[contains(@class, 'grid')]")
                cards = grid.find_elements(By.CSS_SELECTOR, "a.block.bg-card")
                
                for card in cards:
                    name = card.find_element(By.TAG_NAME, "h3").text.strip()
                    price = card.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                    stock_list.append(f"• {name} | 💵 {price}")
            except:
                pass
            
            sections_data[title] = {"time": reset_time, "items": stock_list}

        # Construct the Discord Message
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = "🛰️ **FruityBlox Live Stock Update**\n"

        for section, data in sections_data.items():
            message += f"\n**{section}** (Resets in: `{data['time']}`)\n"
            if data['items']:
                message += "\n".join(data['items'])
            else:
                message += "_No stock found._"
            message += "\n"
        
        message += f"\n*Last Checked: {timestamp}*"

        requests.post(WEBHOOK_URL, json={"content": message})
        print("Successfully sent to Discord!")

    except Exception as e:
        print(f"Scraper Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_fruity_blox()
