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
    print(f"🚀 Starting JS-Injection Scraper... Targeting Host: {TARGET_URL}")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://fruityblox.com/stock")
        time.sleep(12) # Let JavaScript finish loading the fruits

        # THE "MAGIC" JAVASCRIPT: This finds all fruits regardless of nested HTML
        script = """
        let sections = [];
        document.querySelectorAll('h2').forEach(h2 => {
            let title = h2.innerText;
            if (title.includes('Normal') || title.includes('Mirage')) {
                let sectionData = { title: title, fruits: [], timer: "" };
                
                // Find Timer
                let parent = h2.parentElement;
                let timerEl = parent.querySelector('.font-mono');
                if (timerEl) sectionData.timer = timerEl.innerText;

                // Find Fruits in the sibling grid
                let grid = h2.nextElementSibling;
                if (grid) {
                    grid.querySelectorAll('a').forEach(card => {
                        let name = card.querySelector('h3')?.innerText;
                        let price = card.querySelector('.text-green-400')?.innerText;
                        if (name && price) {
                            sectionData.fruits.push({ name: name, price: price });
                        }
                    });
                }
                sections.push(sectionData);
            }
        });
        return sections;
        """
        
        results = driver.execute_script(script)
        print(f"--- JS found {len(results)} sections.")

        embeds_data = []
        high_value_alert = False

        for section in results:
            title = section['title']
            fruits = section['fruits']
            timer_text = section['timer']
            
            print(f"✅ Processing {title}: Found {len(fruits)} fruits.")
            
            lines = []
            for f in fruits:
                name = f['name'].strip()
                price = f['price'].strip()
                val = int(re.sub(r'[^\d]', '', price))
                
                line = f"**{name} | `${price}`**"
                if val >= 1000000:
                    line = "🔥 " + line
                    high_value_alert = True
                lines.append(line)

            if lines:
                ts = f"<t:{get_unix_time(timer_text)}:R>"
                embeds_data.append({
                    "description": f"**Current {title}**\n------------------\n" + "\n".join(lines) + "\n------------------\n" + f"-# **Stock Change** - {ts}",
                    "color": 2829617 
                })

        if embeds_data:
            payload = {"content": "🚨 @everyone **High Value!**" if high_value_alert else "", "embeds": embeds_data}
            res = requests.post(TARGET_URL, json=payload, timeout=20)
            print(f"📡 Sent to Host! Status: {res.status_code}")
        else:
            print("❌ Still no fruits found. Checking page source for errors...")
            print(driver.page_source[:500]) # Log start of HTML for debugging

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape()
