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
    print(f"🚀 Starting Catch-All Scraper... Targeting Host: {TARGET_URL}")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://fruityblox.com/stock")
        # Massive wait to ensure the framework finishes rendering
        time.sleep(15)

        # This JS finds all fruit cards regardless of where they are in the HTML
        script = """
        let data = [];
        // Find all containers that look like fruit cards
        document.querySelectorAll('a').forEach(link => {
            let h3 = link.querySelector('h3');
            let priceEl = link.querySelector('.text-green-400');
            
            if (h3 && priceEl) {
                data.push({
                    name: h3.innerText.trim(),
                    price: priceEl.innerText.trim(),
                    // Check if it belongs to Mirage by looking at its parent's header
                    isMirage: link.closest('div').previousElementSibling?.innerText.includes('Mirage') || false
                });
            }
        });
        
        // Also grab the timers
        let timers = {};
        document.querySelectorAll('h2').forEach(h2 => {
            let t = h2.parentElement.querySelector('.font-mono')?.innerText;
            if (h2.innerText.includes('Normal')) timers.normal = t;
            if (h2.innerText.includes('Mirage')) timers.mirage = t;
        });
        
        return { fruits: data, timers: timers };
        """
        
        results = driver.execute_script(script)
        all_fruits = results.get('fruits', [])
        timers = results.get('timers', {})
        
        print(f"--- Found {len(all_fruits)} total fruits across all sections.")

        embeds_data = []
        high_value_alert = False

        # Group them manually
        for section_type in ['Normal', 'Mirage']:
            is_mirage_target = (section_type == 'Mirage')
            # Filter fruits for this section
            section_fruits = [f for f in all_fruits if f['isMirage'] == is_mirage_target]
            
            # If the logic above failed to group them, but we found fruits, 
            # let's just put the first few in Normal and others in Mirage as a fallback
            if not section_fruits and all_fruits:
                if section_type == 'Normal': section_fruits = all_fruits[:len(all_fruits)//2]
                else: section_fruits = all_fruits[len(all_fruits)//2:]

            lines = []
            for f in section_fruits:
                name = f['name']
                price = f['price']
                val = int(re.sub(r'[^\d]', '', price))
                
                line = f"**{name} | `${price}`**"
                if val >= 1000000:
                    line = "🔥 " + line
                    high_value_alert = True
                lines.append(line)

            if lines:
                t_key = 'normal' if section_type == 'Normal' else 'mirage'
                raw_t = timers.get(t_key, "00:00:00")
                ts = f"<t:{get_unix_time(raw_t)}:R>"
                
                embeds_data.append({
                    "description": f"**Current {section_type} Stock**\n------------------\n" + "\n".join(lines) + "\n------------------\n" + f"-# **Stock Change** - {ts}",
                    "color": 2829617 
                })

        if embeds_data:
            payload = {"content": "🚨 @everyone **High Value!**" if high_value_alert else "", "embeds": embeds_data}
            requests.post(TARGET_URL, json=payload, timeout=20)
            print("📡 Success! Data sent to host.")
        else:
            print("❌ Absolute failure: No items found in DOM.")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape()
