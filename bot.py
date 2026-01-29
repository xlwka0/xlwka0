import requests
from bs4 import BeautifulSoup
import json
import os

def get_stock():
    url = "https://fruityblox.com/stock"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # FruityBlox uses Next.js, so data is inside this script tag
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if not script_tag:
            return "❌ Error: Could not find stock data script."

        data = json.loads(script_tag.string)
        # Navigate to the stock data inside the JSON
        stock_info = data['props']['pageProps']['initialState']['stock']
        
        report = "🍎 **FRUITYBLOX LIVE STOCK** 🍎\n"
        
        for stock_type in ['normal', 'mirage']:
            title = stock_type.upper()
            reset_status = stock_info.get(f'{stock_type}Status', 'Unknown')
            fruits = stock_info.get(stock_type, [])
            
            report += f"\n**--- {title} STOCK ---**\n🕒 Reset: {reset_status}\n"
            
            if fruits:
                fruit_list = [f"• {f['name']} (${f['price']:,})" for f in fruits]
                report += "\n".join(fruit_list)
            else:
                report += "No fruits currently listed."
            report += "\n"

        return report
    except Exception as e:
        return f"⚠️ Script Error: {str(e)}"

def send_to_discord(content):
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    if webhook_url:
        requests.post(webhook_url, json={"content": content})
    else:
        print("Webhook URL missing from Secrets!")

if __name__ == "__main__":
    content = get_stock()
    send_to_discord(content)
