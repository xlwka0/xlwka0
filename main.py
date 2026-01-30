import os, re, time, requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Get Host IP from GitHub Secrets
HOST_IP = os.getenv("HOST_IP")
PORT = "21261"
TARGET_URL = f"http://{HOST_IP}:{PORT}/update"

def get_unix_time(raw_str):
    try:
        p = raw_str.strip().split(':')
        return int(time.time()) + (int(p[0])*3600 + int(p[1])*60 + int(p[2]))
    except: return int(time.time())

def scrape():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://fruityblox.com/stock")
        time.sleep(5)
        
        headers = driver.find_elements(By.TAG_NAME, "h2")
        embeds_data = []
        high_value = False

        for header in headers:
            title = header.text.strip()
            if "Normal" not in title and "Mirage" not in title: continue
            
            # Extract Timer
            try:
                t_str = driver.find_element(By.XPATH, f"//h2[contains(text(), '{title}')]/..//span[contains(@class, 'font-mono')]").text
                ts = f"<t:{get_unix_time(t_str)}:R>"
            except: ts = "Unknown"

            # Extract Fruits
            lines = []
            grid = header.find_element(By.XPATH, "./following-sibling::div")
            for card in grid.find_elements(By.CSS_SELECTOR, "a.block.bg-card"):
                name = card.find_element(By.TAG_NAME, "h3").text.strip()
                price = card.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                val = int(re.sub(r'[^\d]', '', price))
                
                line = f"**{name} • `{price}`**"
                if val >= 1000000:
                    line = "🔥 " + line
                    high_value = True
                lines.append(line)

            embeds_data.append({
                "description": f"**Current {title}**\n" + "─" * 15 + "\n" + "\n".join(lines) + "\n" + "─" * 15 + f"\n-# **Stock Change** - {ts}",
                "color": 2829617 
            })

        payload = {
            "content": "🚨 @everyone **High Value Stock Alert!**" if high_value else "",
            "embeds": embeds_data
        }
        
        response = requests.post(TARGET_URL, json=payload, timeout=15)
        print(f"Status: {response.status_code} - Data sent to host.")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape()
