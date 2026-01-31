import os, re, time, requests, datetime
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
    print(f"🚀 Starting Deep-Search Scraper... Targeting Host: {TARGET_URL}")
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
                let parent = h2.parentElement;
                let timer = parent.querySelector('.font-mono')?.innerText || "00:00:00";
                if (isNormal) results.normalTimer = timer;
                else results.mirageTimer = timer;

                // Search downwards for the next 'div' that contains fruit cards
                let current = h2.nextElementSibling;
                while (current) {
                    let cards = current.querySelectorAll('a[href*="/items/"]');
                    if (cards.length > 0) {
                        cards.forEach(card => {
                            let name = card.querySelector('h3')?.innerText;
                            let price = card.querySelector('.text-green-400')?.innerText;
                            if (name && price) {
                                let item = { name: name.trim(), price: price.trim() };
                                if (isNormal) results.normal.push(item);
                                else results.mirage.push(item);
                            }
                        });
                        break; // Stop searching once we found the grid
                    }
                    current = current.nextElementSibling;
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
                print(f"⚠️ No fruits found for {display_name}")
                continue

            print(f"✅ Found {len(fruits)} items for {display_name}")
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
            
            # Create the embed dictionary
            embed = {
                "title": f"Current {display_name} Stock",
                "description": "------------------\n" + "\n".join(lines) + "\n------------------\n" + f"-# **Stock Change** - {ts}",
                "color": 2829617 if category == 'normal' else 10181046
            }
            
            # Add timestamp footer to the last embed
            if category == 'mirage' or (category == 'normal' and not data['mirage']):
                now = datetime.datetime.now().strftime("%I:%M %p")
                embed["footer"] = {"text": f"Last Updated: {now} | Powered by GitHub"}
                
            embeds_data.append(embed)

        if embeds_data:
            payload = {"content": "🚨 @everyone **High Value!**" if high_value_alert else "", "embeds": embeds_data}
            requests.post(TARGET_URL, json=payload, timeout=20)
            print("📡 Sorted data sent successfully!")
        else:
            print("❌ Absolute failure: Headers found but grids were empty after deep search.")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape()
