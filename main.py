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
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://fruityblox.com/stock")
        # Wait for the specific fruit card class from your snippet
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bg-card")))
        
        # Give JS a moment to populate text
        time.sleep(5) 
        
        headers = driver.find_elements(By.TAG_NAME, "h2")
        embeds_data = []
        high_value = False

        for header in headers:
            title = header.text.strip()
            if "Normal" not in title and "Mirage" not in title:
                continue
            
            print(f"✅ Found Section: {title}")
            
            # Find the Timer based on your Mirage snippet (font-mono tabular-nums)
            try:
                parent_div = header.find_element(By.XPATH, "./..")
                timer_text = parent_div.find_element(By.CLASS_NAME, "font-mono").text.strip()
                ts = f"<t:{get_unix_time(timer_text)}:R>"
            except:
                ts = "Unknown"

            lines = []
            # Move to the grid and find all fruit cards
            try:
                grid = header.find_element(By.XPATH, "./following-sibling::div")
                cards = grid.find_elements(By.CSS_SELECTOR, "a.bg-card")
                
                for card in cards:
                    # Target the H3 for name and text-green-400 for price as seen in your snippet
                    name = card.find_element(By.TAG_NAME, "h3").text.strip()
                    price_element = card.find_element(By.CLASS_NAME, "text-green-400")
                    price = price_element.text.strip()
                    
                    if not name or not price: continue
                    
                    # Clean price (e.g., "5,000" -> 5000)
                    val = int(re.sub(r'[^\d]', '', price))
                    line = f"**{name} | `${price}`**"
                    
                    if val >= 1000000:
                        line = "🔥 " + line
                        high_value = True
                    lines.append(line)
            except Exception as e:
                print(f"Error parsing fruits in {title}: {e}")

            if lines:
                embeds_data.append({
                    "description": f"**Current {title}**\n------------------\n" + "\n".join(lines) + "\n------------------\n" + f"-# **Stock Change** - {ts}",
                    "color": 2829617 
                })

        if embeds_data:
            payload = {"content": "🚨 @everyone **High Value!**" if high_value else "", "embeds": embeds_data}
            response = requests.post(TARGET_URL, json=payload, timeout=20)
            print(f"📡 Data sent to Host. Status: {response.status_code}")
        else:
            print("❌ Found headers but failed to extract fruit names/prices.")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape()
