import os, re, time, discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Load secrets
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Custom Emojis
MONEY_EMOJI = "<:money:1456628926276173845>"
CLOCK_EMOJI = "<:clock:1182328726185312336>"

class FruityBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.scrape_loop.start()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

    def get_unix_time(self, raw_str):
        try:
            p = raw_str.strip().split(':')
            return int(time.time()) + (int(p[0])*3600 + int(p[1])*60 + int(p[2]))
        except: return None

    @tasks.loop(minutes=30)
    async def scrape_loop(self):
        channel = self.get_channel(CHANNEL_ID)
        if not channel: return

        # 1. Clean the channel (deletes last 5 messages to be safe)
        try:
            await channel.purge(limit=5, check=lambda m: m.author == self.user)
        except: pass

        # 2. Scrape Data
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        try:
            driver.get("https://fruityblox.com/stock")
            time.sleep(5)
            
            headers = driver.find_elements(By.TAG_NAME, "h2")
            embeds = []
            alert = False

            for header in headers:
                title = header.text.strip()
                if "Normal" not in title and "Mirage" not in title: continue
                
                # Timer logic
                try:
                    raw_t = driver.find_element(By.XPATH, f"//h2[contains(text(), '{title}')]/..//span[contains(@class, 'font-mono')]").text
                    ts = f"<t:{self.get_unix_time(raw_t)}:R>"
                except: ts = "Unknown"

                # Fruit lines
                lines = []
                grid = header.find_element(By.XPATH, "./following-sibling::div")
                for card in grid.find_elements(By.CSS_SELECTOR, "a.block.bg-card"):
                    name = card.find_element(By.TAG_NAME, "h3").text.strip()
                    price = card.find_element(By.CLASS_NAME, "text-green-400").text.strip()
                    val = int(re.sub(r'[^\d]', '', price))
                    
                    line = f"**{name} • {MONEY_EMOJI}`{price}`**"
                    if val >= 1000000:
                        line = "🔥 " + line
                        alert = True
                    lines.append(line)

                # Format like the Vulcan JSON
                desc = f"**Current {title}**\n" + "─" * 15 + "\n"
                desc += "\n".join(lines) + "\n" + "─" * 15 + "\n"
                desc += f"-# {CLOCK_EMOJI} **Stock Change in** - {ts}"
                
                embeds.append(discord.Embed(description=desc, color=0x2b2d31))

            # 3. Post New Stock
            content = "🚨 @everyone **High Value Stock!**" if alert else None
            await channel.send(content=content, embeds=embeds)

        finally:
            driver.quit()

bot = FruityBot()
bot.run(TOKEN)
