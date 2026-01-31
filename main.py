import os, re, time, requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

HOST_IP = os.getenv("HOST_IP")
PORT = "21261"
TARGET_URL = f"http://{HOST_IP}:{PORT}/update"

def scrape():
    print(f"🚀 Sending Raw Data to: {TARGET_URL}")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://fruityblox.com/stock")
        time.sleep(15)

        script = """
        let results = { normal: [], mirage: [], normalTimer: "00:00:00", mirageTimer: "00:00:00" };
        document.querySelectorAll('h2').forEach(h2 => {
            let isMirage = h2.innerText.includes('Mirage');
            let parent = h2.parentElement;
            let timer = parent.querySelector('.font-mono')?.innerText || "00:00:00";
            
            if (isMirage) results.mirageTimer = timer;
            else results.normalTimer = timer;

            let current = h2.nextElementSibling;
            while (current) {
                let cards = current.querySelectorAll('a[href*="/items/"]');
                if (cards.length > 0) {
                    cards.forEach(card => {
                        let name = card.querySelector('h3')?.innerText;
                        let price = card.querySelector('.text-green-400')?.innerText;
                        if (name && price) {
                            if (isMirage) results.mirage.push({n: name.trim(), p: price.trim()});
                            else results.normal.push({n: name.trim(), p: price.trim()});
                        }
                    });
                    break;
                }
                current = current.nextElementSibling;
            }
        });
        return results;
        """
        raw_data = driver.execute_script(script)
        
        if raw_data['normal'] or raw_data['mirage']:
            requests.post(TARGET_URL, json=raw_data, timeout=20)
            print("✅ Raw data pushed.")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape()
