import os, discord, re
from discord.ext import commands
from flask import Flask, request
from threading import Thread
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
PORT = 21261  # Your specific host port

app = Flask('')

@app.route('/update', methods=['POST'])
def update():
    data = request.json
    # Tell the bot to process the new stock data
    bot.dispatch("stock_update", data)
    return {"status": "received"}, 200

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_stock_update(data):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        # Purge old bot messages to keep it clean
        try:
            def is_me(m): return m.author == bot.user
            await channel.purge(limit=5, check=is_me)
        print("Cleaned old messages.")

        # Convert the incoming JSON into Discord Embed objects
        embeds = [discord.Embed.from_dict(e) for e in data.get('embeds', [])]
        content = data.get('content', "")
        await channel.send(content=content, embeds=embeds)
        print("Posted new stock update.")

@bot.event
async def on_ready():
    print(f'🚀 Receiver Bot Online: {bot.user}')

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Host is listening on port 21261.")

# Run the web server in a background thread
def run_server():
    app.run(host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    t = Thread(target=run_server)
    t.daemon = True
    t.start()
    bot.run(TOKEN)
