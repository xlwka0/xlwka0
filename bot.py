import os, re, time, discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 1. Load your .env secrets
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# 2. Config & Emojis
MONEY_EMOJI = "<:money:1456628926276173845>"
CLOCK_EMOJI = "<:clock:1182328726185312336>"

# 3. Setup Intents (Crucial for Prefix Commands)
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)

# --- UTILITY FUNCTIONS ---

def get_unix_time(raw_str):
    try:
        p = raw_str.strip().split(':')
        return int(time.time()) + (int(p[0])*3600 + int(p[1])*60 + int(p[2]))
    except: return None

async def run_scrape_logic(channel):
    """The actual scraping brain used by both the loop and manual command."""
    # Clean old bot messages from the channel
    try:
        def is_me(m): return m.author == bot.user
        await channel.purge(limit=15, check=is_me)
    except Exception as e:
        print(f"Purge error: {e}")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://fruityblox.com/stock")
        time.sleep(5) # Allow dynamic content to load
        
        headers = driver.find_elements(By.TAG_NAME, "h2")
        embeds = []
        alert = False

        for header in headers:
            title = header.text.strip()
            if "Normal" not in title and "Mirage" not in title: continue
            
            # Timer logic
            try:
                timer_el = driver.find_element(By.XPATH, f"//h2[contains(text(), '{title}')]/..//span[contains(@class, 'font-mono')]")
                ts = f"<t:{get_unix_time(timer_el.text.strip())}:R>"
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

            desc = f"**Current {title}**\n" + "─" * 15 + "\n"
            desc += "\n".join(lines) + "\n" + "─" * 15 + "\n"
            desc += f"-# {CLOCK_EMOJI} **Stock Change in** - {ts}"
            
            embed_obj = discord.Embed(description=desc, color=0x2b2d31)
            embeds.append(embed_obj)

        content = "🚨 @everyone **High Value Stock Alert!**" if alert else None
        await channel.send(content=content, embeds=embeds)
        print("Scrape completed successfully.")

    except Exception as e:
        print(f"Scrape Logic Error: {e}")
        await channel.send(f"⚠️ **Scrape Failed:** `{e}`")
    finally:
        driver.quit()

# --- EVENTS ---

@bot.event
async def on_ready():
    print(f'🚀 Bot is online as {bot.user}')
    if not scrape_loop.is_running():
        scrape_loop.start()

@bot.event
async def on_message(message):
    # This prevents the bot from ignoring commands
    await bot.process_commands(message)

# --- COMMANDS ---

@bot.command()
async def ping(ctx):
    """Test if the bot is actually listening."""
    await ctx.send(f"🏓 **Pong!** Latency: {round(bot.latency * 1000)}ms")

@bot.command(name="force")
async def force(ctx):
    """Manually triggers a fresh scrape."""
    temp_msg = await ctx.send("🔄 **Manual update triggered. Working...**")
    
    target_channel = bot.get_channel(CHANNEL_ID)
    if target_channel:
        await run_scrape_logic(target_channel)
        await temp_msg.delete()
        try: await ctx.message.delete() # Clean up the !force command
        except: pass
    else:
        await ctx.send("❌ Could not find the target channel. Check your .env file.")

# --- AUTO LOOP ---

@tasks.loop(minutes=30)
async def scrape_loop():
    print("Running scheduled auto-scrape...")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await run_scrape_logic(channel)

# Start the bot
bot.run(TOKEN)
