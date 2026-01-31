import os, re, time, requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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
    print(f"🚀 Starting Categorized Scraper... Targeting Host: {TARGET_URL}")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://fruityblox.com/stock")
        time.sleep(15)

        script = """
        let results = { normal: [], mirage: [], normalTimer: "", mirageTimer: "" };
        
        document.querySelectorAll('h2').forEach(h2 => {
            let isMirage = h2.innerText.includes('Mirage');
            let isNormal = h2.innerText.includes('Normal');
            
            if (isNormal || isMirage) {
                // Get Timer
                let timer = h2.parentElement.querySelector('.font-mono')?.innerText || "00:00:00";
                if (isNormal) results.normalTimer = timer;
                else results.mirageTimer = timer;

                // Get Fruits in the grid immediately following this header
                let grid = h2.nextElementSibling;
                if (grid) {
                    grid.querySelectorAll('a').forEach(card => {
                        let name = card.querySelector('h3')?.innerText;
                        let price = card.querySelector('.text-green-400')?.innerText;
                        if (name && price) {
                            let item = { name: name.trim(), price: price.trim() };
                            if (isNormal) results.normal.push(item);
                            else results.mirage.push(item);
                        }
                    });
                }
            }
        });
        return results;
        """
        
        data = driver.execute_script(script)
        embeds_data = []
        high_value_alert = False

        for category in ['normal', 'mirage']:
            fruits = data[category]
            timer_text = data[f'{category}Timer']
            display_name = "Normal" if category == 'normal' else "Mirage"
            
            if not fruits:
                continue

            lines = []
            for f in fruits:
                name = f['name']
                price = f['price']
                val = int(re.sub(r'[^\d]', '', price))
                
                line = f"**{name} | `${price}`**"
                if val >= 1000000:
                    line = "🔥 " + line
                    high_value_alert = True
                lines.append(line)

            ts = f"<t:{get_unix_time(timer_text)}:R>"
            embeds_data.append({
                "description": f"**Current {display_name} Stock**\n------------------\n" + "\n".join(lines) + "\n------------------\n" + f"-# **Stock Change** - {ts}",
                "color": 2829617 if category == 'normal' else 10181046 # Mirage gets a purple-ish color
            })

        if embeds_data:
            payload = {"content": "🚨 @everyone **High Value!**" if high_value_alert else "", "embeds": embeds_data}
            requests.post(TARGET_URL, json=payload, timeout=20)
            print("📡 Sorted data sent successfully!")
        else:
            print("❌ Found headers but failed to find fruits in those specific grids.")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape()
