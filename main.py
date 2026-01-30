import os, re, time, requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Get Host Configuration from GitHub Secrets/Env
HOST_IP = os.getenv("HOST_IP")
PORT = "21261"
TARGET_URL = f"http://{HOST_IP}:{PORT}/update"

def get_unix_time(raw_str):
    """Converts the site's relative time string to a Discord Unix Timestamp."""
    try:
        p = raw_str.strip().split(':')
        # Calculates: Current Time + (Hours*3600 + Mins*60 + Secs)
        return int(time.time()) + (int(p[0])*3600 + int(p[1])*60 + int(p[2]))
    except:
        return int(time.time())

def scrape():
    print(f"🚀 Starting Scraper... Targeting Host: {TARGET_URL}")
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # GitHub Actions provides the browser, Selenium drives it
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://fruityblox.com/stock")
        
        # Wait up to 15 seconds for the fruit cards to actually load text
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h3")))
        
        headers = driver.find_elements(By.TAG_NAME, "h2")
        embeds_data = []
        high_value = False

        for header in headers:
            title = header.text.strip()
            if "Normal" not in title and "Mirage" not in title:
                continue
            
            # Extract the countdown timer
            try:
                t_el = driver.find_element(By.XPATH, f"//h2[contains(text(), '{title}')]/..//span[contains(@class, 'font-mono')]")
                ts = f"<t:{get_unix_time(t_el.text.strip())}:R>"
            except:
                ts = "Unknown"

            lines = []
            # Find the fruit grid associated with this header
            grid = header.find_element(By.XPATH, "./following-sibling::div[1]")
            cards = grid.find_elements(By.TAG_NAME, "a")
            
            for card in cards:
                try:
                    name = card.find_element(By.TAG_NAME, "h3").text.strip()
                    price = card.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                    if not name: continue
                    
                    # Alert if fruit price is 1M or higher
                    val = int(re.sub(r'[^\d]', '', price))
                    line = f"**{name} | `{price}`**"
                    if val >= 1000000:
                        line = "🔥 " + line
                        high_value = True
                    lines.append(line)
                except:
                    continue

            if lines:
                # Format data using standard characters to avoid host encoding errors
                embeds_data.append({
                    "description": f"**Current {title}**\n------------------\n" + "\n".join(lines) + "\n------------------\n" + f"-# **Stock Change** - {ts}",
                    "color": 2829617  # Decimal for 0x2b2d31
                })

        if embeds_data:
            payload = {
                "content": "🚨 @everyone **High Value Stock Alert!**" if high_value else "",
                "embeds": embeds_data
            }
            
            print("📦 Payload ready. Sending to host...")
            response = requests.post(TARGET_URL, json=payload, timeout=20)
            print(f"✅ Host Response: {response.status_code} - {response.text}")
        else:
            print("⚠️ Scraper finished but found no stock data.")

    except Exception as e:
        print(f"❌ Scraper Error: {e}")
    finally:
        driver.quit()
        print("Driver closed.")

if __name__ == "__main__":
    scrape()
