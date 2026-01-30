import os, requests, datetime, re, time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

# Custom Emojis from your JSON
MONEY_EMOJI = "<:money:1456628926276173845>"
CLOCK_EMOJI = "<:clock:1182328726185312336>"

def get_unix_time(relative_time_str):
    try:
        parts = relative_time_str.strip().split(':')
        if len(parts) != 3: return None
        seconds_to_add = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return int(time.time()) + seconds_to_add
    except: return None

def scrape_fruity_blox():
    if not WEBHOOK_URL: return
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://fruityblox.com/stock")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h2")))

        timers = {"Normal": "Unknown", "Mirage": "Unknown"}
        for stock_type in ["Normal", "Mirage"]:
            try:
                timer_xpath = f"//h2[contains(text(), '{stock_type}')]/..//span[contains(@class, 'font-mono')]"
                raw_time = driver.find_element(By.XPATH, timer_xpath).text.strip()
                unix_ts = get_unix_time(raw_time)
                if unix_ts:
                    timers[stock_type] = f"<t:{unix_ts}:R>"
            except: pass

        headers = driver.find_elements(By.TAG_NAME, "h2")
        embeds = []
        high_value_alert = False

        for header in headers:
            title_text = header.text.strip()
            if "Normal" not in title_text and "Mirage" not in title_text: continue
            
            stock_lines = []
            try:
                grid = header.find_element(By.XPATH, "./following-sibling::div[contains(@class, 'grid')]")
                cards = grid.find_elements(By.CSS_SELECTOR, "a.block.bg-card")
                for card in cards:
                    name = card.find_element(By.TAG_NAME, "h3").text.strip()
                    price = card.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                    
                    # Recreating the Vulcan JSON Line Style:
                    # **Name • <:money:ID>`Price`**
                    line = f"**{name} • {MONEY_EMOJI}`{price}`**"
                    
                    # Alert Logic
                    val = int(re.sub(r'[^\d]', '', price))
                    if val >= 1000000:
                        line = "🔥 " + line
                        high_value_alert = True
                    
                    stock_lines.append(line)
            except: pass

            stock_key = "Normal" if "Normal" in title_text else "Mirage"
            
            # Recreating the Vulcan "Section" look using Embed Description
            description = f"**Current {stock_key} Stock**\n"
            description += "─" * 15 + "\n"
            description += "\n".join(stock_lines) + "\n"
            description += "─" * 15 + "\n"
            description += f"-# {CLOCK_EMOJI} **Stock Change in** - {timers[stock_key]}"

            embeds.append({
                "description": description,
                "color": 2829617  # Matches the dark Vulcan theme
            })

        payload = {"embeds": embeds}
        if high_value_alert:
            payload["content"] = "🚨 **High Value Stock Alert!** @everyone"

        requests.post(WEBHOOK_URL, json=payload)
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_fruity_blox()
