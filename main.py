import os, re, time, requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

HOST_IP = os.getenv("HOST_IP")
PORT = "21261"
TARGET_URL = f"http://{HOST_IP}:{PORT}/update"

def get_unix_time(raw_str):
    try:
        p = raw_str.strip().split(':')
        return int(time.time()) + (int(p[0])*3600 + int(p[1])*60 + int(p[2]))
    except: return int(time.time())

def scrape():
    print(f"🚀 Starting Scraper... Targeting Host: {TARGET_URL}")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080") # Help Selenium "see" more
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://fruityblox.com/stock")
        # Give the page extra time to finish all animations
        time.sleep(10) 
        
        # Look for headers that contain the words we need
        headers = driver.find_elements(By.TAG_NAME, "h2")
        print(f"Found {len(headers)} total headers. Checking for stock sections...")
        
        embeds_data = []
        high_value = False

        for header in headers:
            title = header.text.strip()
            # More flexible check for the section titles
            if "Normal" not in title and "Mirage" not in title:
                continue
            
            print(f"Processing section: {title}")
            
            try:
                # Find the timer span specifically inside this section
                parent = header.find_element(By.XPATH, "..")
                t_el = parent.find_element(By.CLASS_NAME, "font-mono")
                ts = f"<t:{get_unix_time(t_el.text.strip())}:R>"
            except:
                ts = "Unknown"

            lines = []
            # Find the fruit container nearby
            try:
                grid = header.find_element(By.XPATH, "./following-sibling::div")
                cards = grid.find_elements(By.TAG_NAME, "a")
                
                for card in cards:
                    name = card.find_element(By.TAG_NAME, "h3").text.strip()
                    price = card.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                    if not name: continue
                    
                    val = int(re.sub(r'[^\d]', '', price))
                    line = f"**{name} | `{price}`**"
                    if val >= 1000000:
                        line = "🔥 " + line
                        high_value = True
                    lines.append(line)
            except Exception as e:
                print(f"Error finding fruits in {title}: {e}")

            if lines:
                embeds_data.append({
                    "description": f"**Current {title}**\n------------------\n" + "\n".join(lines) + "\n------------------\n" + f"-# **Stock Change** - {ts}",
                    "color": 2829617 
                })

        if embeds_data:
            payload = {"content": "🚨 @everyone **High Value!**" if high_value else "", "embeds": embeds_data}
            response = requests.post(TARGET_URL, json=payload, timeout=20)
            print(f"✅ Sent! Host Status: {response.status_code}")
        else:
            print("❌ Still no stock found. The website structure might have changed.")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape()
