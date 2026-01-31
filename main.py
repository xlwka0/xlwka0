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
    print(f"🚀 Starting Stealth Scraper... Targeting Host: {TARGET_URL}")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # STEALTH SETTINGS: Make GitHub look like a real Chrome browser
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Further hide Selenium
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        driver.get("https://fruityblox.com/stock")
        
        # Give the page a massive 15-second cushion to load behind the bot-check
        time.sleep(15)
        
        # Check if we are stuck on a Cloudflare page
        if "Just a moment" in driver.title or "Verify you are human" in driver.page_source:
            print("❌ Stuck on Cloudflare verification. Retrying with different logic...")
            # Fallback: try to find any h2 even if cards aren't ready
        
        headers = driver.find_elements(By.TAG_NAME, "h2")
        print(f"--- Found {len(headers)} headers on page.")
        
        embeds_data = []
        high_value_alert = False

        for header in headers:
            title = header.text.strip()
            if "Normal" not in title and "Mirage" not in title:
                continue
            
            print(f"✅ Processing: {title}")
            
            # Timer
            try:
                parent = header.find_element(By.XPATH, "..")
                timer_text = parent.find_element(By.CLASS_NAME, "font-mono").text.strip()
                ts = f"<t:{get_unix_time(timer_text)}:R>"
            except: ts = "Unknown"

            lines = []
            # Find the fruit grid
            try:
                grid = header.find_element(By.XPATH, "./following-sibling::div")
                # Look for ANY link inside the grid
                cards = grid.find_elements(By.TAG_NAME, "a")
                
                for card in cards:
                    try:
                        name = card.find_element(By.TAG_NAME, "h3").text.strip()
                        # Extract price from the green text
                        price_el = card.find_element(By.CLASS_NAME, "text-green-400")
                        price = price_el.text.strip()
                        
                        if name and price:
                            val = int(re.sub(r'[^\d]', '', price))
                            line = f"**{name} | `${price}`**"
                            if val >= 1000000:
                                line = "🔥 " + line
                                high_value_alert = True
                            lines.append(line)
                            print(f"      > {name}: {price}")
                    except: continue
            except: continue

            if lines:
                embeds_data.append({
                    "description": f"**Current {title}**\n------------------\n" + "\n".join(lines) + "\n------------------\n" + f"-# **Stock Change** - {ts}",
                    "color": 2829617 
                })

        if embeds_data:
            payload = {"content": "🚨 @everyone **High Value!**" if high_value_alert else "", "embeds": embeds_data}
            res = requests.post(TARGET_URL, json=payload, timeout=20)
            print(f"📡 Data Sent! Response: {res.status_code}")
        else:
            print("❌ No fruit data extracted. Website might be blocking the automated script.")

    except Exception as e:
        print(f"❌ Scraper Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape()
